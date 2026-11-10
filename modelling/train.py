"""Train BiLSTM / mBERT / WangchanBERTa."""
from __future__ import annotations

import argparse
import itertools
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import transformers
from sklearn.utils.class_weight import compute_class_weight
from torch import nn
from transformers import AutoTokenizer, EarlyStoppingCallback, Trainer, TrainingArguments

from modelling.clean import PreprocOpts, hashtag_modes, preprocess
from modelling.config import CHECKPOINTS, RESULTS, ROOT, load_config
from modelling.data import SPLITS, load_gold, split_frames
from modelling.models import build_model, build_vocab, encode, thai_tokenizer
from modelling.results import class_report, predictions, save_run, scores

STAGES = ("main", "tune", "tuned")
BEST_METRICS = {"loss": ("eval_loss", False), "macro_f1": ("eval_macro_f1", True)}
SHORT = {"class_weight_power": "cw"}


def run_name(model: str, mode: str, seed: int, candidate: str | None = None) -> str:
    return f"{model}_{mode}_seed{seed}" + (f"__{candidate}" if candidate else "")


def hparams(cfg: dict, model: str) -> dict:
    m = cfg["modelling"]
    return {**m["train"], **(m.get("train_overrides", {}).get(model) or {})}


def class_weights(label_ids, k: int, power: float = 1.0) -> torch.Tensor:
    w = compute_class_weight("balanced", classes=np.arange(k), y=np.asarray(label_ids))
    return torch.tensor(w ** float(power), dtype=torch.float32)


def provenance() -> dict:
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                                text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    return {"torch_version": torch.__version__, "transformers_version": transformers.__version__,
            "numpy_version": np.__version__, "git_commit": commit}


class TextDataset(torch.utils.data.Dataset):
    def __init__(self, ids: list[list[int]], labels: list[int]):
        self.ids, self.labels = ids, labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, i):
        return {"input_ids": self.ids[i], "labels": self.labels[i]}


def pad_batch(pad_id: int):
    """Pad each batch to its longest post; attention mask 1 = real token."""
    def collate(batch: list[dict]) -> dict:
        n = max(1, max(len(b["input_ids"]) for b in batch))
        ids = torch.full((len(batch), n), pad_id, dtype=torch.long)
        mask = torch.zeros((len(batch), n), dtype=torch.long)
        for i, b in enumerate(batch):
            ids[i, :len(b["input_ids"])] = torch.tensor(b["input_ids"], dtype=torch.long)
            mask[i, :len(b["input_ids"])] = 1
        return {"input_ids": ids, "attention_mask": mask,
                "labels": torch.tensor([b["labels"] for b in batch])}
    return collate


def make_encoder(model_cfg: dict, train_texts: list[str], max_len: int):
    if model_cfg["kind"] == "bilstm":
        tok = thai_tokenizer()
        vocab = build_vocab((tok(t) for t in train_texts), int(model_cfg["min_freq"]))
        return (lambda texts: [encode(tok(t), vocab, max_len) for t in texts]), vocab, None

    tok = AutoTokenizer.from_pretrained(model_cfg["pretrained"])

    def enc(texts):
        texts = list(texts)
        if model_cfg.get("lowercase"):
            texts = [t.lower() for t in texts]
        if model_cfg.get("space_token"):
            texts = [t.replace(" ", model_cfg["space_token"]) for t in texts]
        return tok(texts, max_length=max_len, truncation=True)["input_ids"]
    return enc, None, tok


class WeightedTrainer(Trainer):
    """Trainer with class-weighted cross-entropy."""

    def __init__(self, *args, class_weights, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        loss = nn.functional.cross_entropy(outputs.logits, labels,
                                           weight=self.class_weights.to(outputs.logits.device))
        return (loss, outputs) if return_outputs else loss


def run(model: str, mode: str, seed: int, cfg: dict, frames: dict[str, pd.DataFrame], *,
        results: Path = RESULTS, checkpoints: Path = CHECKPOINTS, hp: dict | None = None,
        stage: str = "main", candidate: str | None = None) -> dict:
    classes, k = cfg["intent_classes"], len(cfg["intent_classes"])
    hp = dict(hp) if hp is not None else hparams(cfg, model)
    model_cfg = cfg["modelling"]["models"][model]
    tuning = stage == "tune"
    name = run_name(model, mode, seed, candidate if tuning else None)
    out = results if stage == "main" else results / stage
    ck = checkpoints / stage / name
    metric, higher = BEST_METRICS[hp.get("best_metric", "loss")]
    transformers.set_seed(seed)

    splits = ("train", "validation") if tuning else SPLITS
    opts = PreprocOpts.from_config(cfg)
    texts = {s: [preprocess(t, mode, opts) for t in frames[s]["text"]] for s in splits}
    enc, vocab, tok = make_encoder(model_cfg, texts["train"], int(hp["max_len"]))
    ds = {s: TextDataset(enc(texts[s]), frames[s]["label_id"].tolist()) for s in splits}

    bs = int(hp["batch_size"])
    trainer = WeightedTrainer(
        model=build_model(model_cfg, k, len(vocab) if vocab else None),
        args=TrainingArguments(
            output_dir=str(ck), seed=seed, num_train_epochs=int(hp["max_epochs"]),
            learning_rate=float(hp["lr"]), weight_decay=float(hp["weight_decay"]),
            warmup_steps=float(hp["warmup_ratio"]),
            per_device_train_batch_size=bs, per_device_eval_batch_size=bs,
            eval_strategy="epoch", save_strategy="epoch", logging_strategy="epoch",
            load_best_model_at_end=True, save_total_limit=1,
            metric_for_best_model=metric, greater_is_better=higher),
        train_dataset=ds["train"], eval_dataset=ds["validation"],
        data_collator=pad_batch(0 if tok is None else tok.pad_token_id),
        class_weights=class_weights(frames["train"]["label_id"], k,
                                    hp.get("class_weight_power", 1.0)),
        compute_metrics=lambda p: {m: v for m, v in scores(p.label_ids, p.predictions.argmax(-1), k)
                                   .items() if m in ("accuracy", "macro_f1")},
        callbacks=[EarlyStoppingCallback(early_stopping_patience=int(hp["early_stopping_patience"]))])
    train_out = trainer.train()

    val_out = trainer.predict(ds["validation"], metric_key_prefix="val")
    val_pred, val_gold = val_out.predictions.argmax(-1), frames["validation"]["label_id"].to_numpy()
    row = {"name": name, "stage": stage, "model": model, "hashtag_mode": mode, "seed": seed,
           "candidate": candidate, "n_train": len(ds["train"]),
           **{f"hp_{key}": v for key, v in hp.items()},
           "epochs_run": trainer.state.epoch,
           "best_epoch": next((h["epoch"] for h in trainer.state.log_history
                               if h.get(metric) == trainer.state.best_metric), None),
           **{f"val_{key}": v for key, v in scores(val_gold, val_pred, k).items()},
           "train_seconds": train_out.metrics["train_runtime"],
           "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
           **provenance()}
    report = "validation\n" + class_report(val_gold, val_pred, classes)
    logits = {"val_logits": val_out.predictions, "val_ids": frames["validation"]["id"].to_numpy()}
    preds = None
    if not tuning:
        test_out = trainer.predict(ds["test"])
        pred, gold = test_out.predictions.argmax(-1), frames["test"]["label_id"].to_numpy()
        row.update({f"test_{key}": v for key, v in scores(gold, pred, k).items()})
        row["test_infer_seconds"] = test_out.metrics["test_runtime"]
        report = "test\n" + class_report(gold, pred, classes)
        preds = predictions(frames["test"], "test", pred, classes)
        logits.update(test_logits=test_out.predictions, test_ids=frames["test"]["id"].to_numpy())
    shutil.rmtree(ck, ignore_errors=True)
    save_run(out, row, preds, report, logits)
    return row


def candidates(cfg: dict, model: str) -> list[tuple[str, dict]]:
    t, base = cfg["modelling"]["tune"], hparams(cfg, model)
    axes = {key: (v[model] if isinstance(v, dict) else v) for key, v in t["grid"].items()}
    out = [("base", base)]
    for combo in itertools.product(*axes.values()):
        cid = "_".join(f"{SHORT.get(key, key)}{float(v):g}" for key, v in zip(axes, combo))
        out.append((cid, {**base, **(t.get("fixed") or {}), **dict(zip(axes, combo))}))
    return out


def tune_table(cfg: dict, model: str, results: Path = RESULTS) -> pd.DataFrame:
    """Mean validation scores per candidate."""
    t = cfg["modelling"]["tune"]
    rows = []
    for cid, hp in candidates(cfg, model):
        files = [results / "tune" / "runs" / f"{run_name(model, t['hashtag_mode'], s, cid)}.json"
                 for s in t["seeds"]]
        runs = pd.DataFrame([json.loads(f.read_text(encoding="utf-8")) for f in files if f.exists()])
        mean = lambda col: runs[col].mean() if col in runs else float("nan")   # noqa: E731
        sd = runs["val_macro_f1"].std(ddof=1) if len(runs) > 1 else float("nan")
        rows.append({"model": model, "candidate": cid, "lr": hp["lr"],
                     "class_weight_power": hp.get("class_weight_power", 1.0),
                     "best_metric": hp.get("best_metric", "loss"), "seeds_done": len(runs),
                     "val_macro_f1": mean("val_macro_f1"), "val_macro_f1_sd": sd,
                     "val_accuracy": mean("val_accuracy"),
                     "kept_epoch": mean("best_epoch"), "train_minutes": mean("train_seconds") / 60})
    return pd.DataFrame(rows)


def select_best(cfg: dict, model: str, results: Path = RESULTS) -> dict:
    col, tab = "val_macro_f1", tune_table(cfg, model, results)
    if (tab["seeds_done"] < len(cfg["modelling"]["tune"]["seeds"])).any():
        raise SystemExit(f"the search for {model} is not finished, run `--stage tune` first")
    win, base = tab.loc[tab[col].idxmax()], tab.loc[tab["candidate"] == "base"].iloc[0]
    best = {"model": model, "candidate": win["candidate"],
            "hp": dict(candidates(cfg, model))[win["candidate"]],
            "val_macro_f1": float(win[col]), "val_macro_f1_sd": float(win["val_macro_f1_sd"]),
            "base_val_macro_f1": float(base[col])}
    (results / "tune" / f"best_{model}.json").write_text(json.dumps(best, indent=2, default=float),
                                                        encoding="utf-8")
    return best


def plan(stage: str, models: list[str], cfg: dict, results: Path = RESULTS) -> list[dict]:
    """Every run of a stage as run() keyword arguments."""
    m = cfg["modelling"]
    if stage == "tune":
        n = {mod: len(candidates(cfg, mod)) for mod in m["models"]}
        if len(set(n.values())) != 1:
            raise ValueError(f"every model must get the same number of candidates; got {n}")
        return [dict(model=mod, mode=m["tune"]["hashtag_mode"], seed=s, hp=hp, candidate=cid)
                for mod in models for cid, hp in candidates(cfg, mod) for s in m["tune"]["seeds"]]
    best = {mod: select_best(cfg, mod, results) for mod in models} if stage == "tuned" else {}
    return [dict(model=mod, mode=h, seed=s,
                 hp=best[mod]["hp"] if best else hparams(cfg, mod),
                 candidate=best[mod]["candidate"] if best else None)
            for mod in models for h in hashtag_modes(cfg) for s in m["grid"]["seeds"]]


def is_done(p: dict, stage: str, results: Path) -> bool:
    name = run_name(p["model"], p["mode"], p["seed"], p["candidate"] if stage == "tune" else None)
    f = (results if stage == "main" else results / stage) / "runs" / f"{name}.json"
    return f.exists() and (stage != "tuned" or
                           json.loads(f.read_text(encoding="utf-8")).get("candidate") == p["candidate"])


def run_stage(stage: str, models: list[str], cfg: dict, frames: dict[str, pd.DataFrame], *,
              results: Path = RESULTS, checkpoints: Path = CHECKPOINTS, force: bool = False) -> list[dict]:
    """Run what is left of a stage (everything with force=True)."""
    todo = [p for p in plan(stage, models, cfg, results) if force or not is_done(p, stage, results)]
    return [run(**p, cfg=cfg, frames=frames, results=results, checkpoints=checkpoints, stage=stage)
            for p in todo]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stage", choices=STAGES, default="main")
    ap.add_argument("--models", default=None, help="comma list; default = all in config.yaml")
    ap.add_argument("--force", action="store_true", help="re-train runs that already have results")
    a = ap.parse_args()
    cfg = load_config()
    models = a.models.split(",") if a.models else list(cfg["modelling"]["models"])
    run_stage(a.stage, models, cfg, split_frames(load_gold(cfg)), force=a.force)
    if a.stage == "tune":
        for mod in models:
            select_best(cfg, mod)


if __name__ == "__main__":
    main()
