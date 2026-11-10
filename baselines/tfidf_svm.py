"""TF-IDF + linear SVM baseline."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from pythainlp.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import FeatureUnion
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from modelling.clean import preprocess                       # noqa: E402
from modelling.config import load_config                     # noqa: E402
from modelling.data import load_gold, split_frames           # noqa: E402

C_GRID = [0.01, 0.03, 0.1, 0.3, 1, 3, 10]
CLASS_WEIGHTS = [None, "balanced"]
OUT = ROOT / "baselines" / "out"


def tokenize(text: str) -> list[str]:
    return word_tokenize(text, engine="newmm", keep_whitespace=False)


def main() -> None:
    frames = split_frames(load_gold(load_config()))
    X = {s: [preprocess(t, "keep") for t in f["text"]] for s, f in frames.items()}
    y = {s: f["label_id"].to_numpy() for s, f in frames.items()}
    features = FeatureUnion([
        ("word", TfidfVectorizer(tokenizer=tokenize, token_pattern=None, ngram_range=(1, 2),
                                 min_df=2, sublinear_tf=True)),
        ("char", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), min_df=2,
                                 sublinear_tf=True)),
    ])
    Xtr = features.fit_transform(X["train"])
    Xva, Xte = features.transform(X["validation"]), features.transform(X["test"])

    grid = []
    for c in C_GRID:
        for cw in CLASS_WEIGHTS:
            clf = LinearSVC(C=c, class_weight=cw).fit(Xtr, y["train"])
            f1 = f1_score(y["validation"], clf.predict(Xva), average="macro")
            grid.append({"C": c, "class_weight": cw, "val_macro_f1": f1, "clf": clf})
    best = max(grid, key=lambda r: r["val_macro_f1"])
    scores = best["clf"].decision_function(Xte)
    pred = scores.argmax(1)
    result = {"C": best["C"], "class_weight": best["class_weight"],
              "val_macro_f1": best["val_macro_f1"],
              "test_accuracy": accuracy_score(y["test"], pred),
              "test_macro_f1": f1_score(y["test"], pred, average="macro"),
              "grid": [{k: v for k, v in r.items() if k != "clf"} for r in grid]}
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "tfidf_svm_test_scores.npz", test_scores=scores,
                        test_ids=frames["test"]["id"].to_numpy())
    (OUT / "tfidf_svm.json").write_text(json.dumps(result, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
