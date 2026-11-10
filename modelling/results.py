"""Output files of a training run."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support)

from modelling.clean import has_hashtag

def scores(y, p, k: int = 7) -> dict:
    """Accuracy and macro precision / recall / F1 over all k classes."""
    prec, rec, f1, _ = precision_recall_fscore_support(y, p, labels=range(k), average="macro",
                                                       zero_division=0)
    return {"accuracy": accuracy_score(y, p), "macro_precision": prec, "macro_recall": rec,
            "macro_f1": f1}

def class_report(y, p, classes: list[str]) -> str:
    """Per-class precision / recall / F1 and the confusion matrix, as text."""
    labels = range(len(classes))
    return (f"{classification_report(y, p, labels=labels, target_names=classes, digits=4, zero_division=0)}"
            f"confusion (rows = gold, cols = predicted, order = {classes}):\n"
            f"{confusion_matrix(y, p, labels=labels)}\n")

def predictions(frame: pd.DataFrame, split: str, pred, classes: list[str]) -> pd.DataFrame:
    return pd.DataFrame({"id": frame["id"], "split": split, "gold": frame["label"],
                         "pred": [classes[i] for i in pred],
                         "has_hashtag": [has_hashtag(t) for t in frame["text"]]})

def save_run(results: Path, row: dict, preds: pd.DataFrame | None, report: str,
             logits: dict[str, np.ndarray]) -> None:
    """Write the output files of one run; the json is written last."""
    name = row["name"]
    subs = ("runs", "reports", "logits") + (("predictions",) if preds is not None else ())
    for sub in subs:
        (results / sub).mkdir(parents=True, exist_ok=True)
    if preds is not None:
        preds.to_csv(results / "predictions" / f"{name}.csv", index=False)
    np.savez_compressed(results / "logits" / f"{name}.npz", **logits)
    (results / "reports" / f"{name}.txt").write_text(f"{name}\n\n{report}", encoding="utf-8")
    (results / "runs" / f"{name}.json").write_text(json.dumps(row, indent=2, default=float),
                                                   encoding="utf-8")
