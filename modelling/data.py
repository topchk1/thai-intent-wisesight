"""Load the reference labels and split them into train / validation / test."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from modelling.config import ROOT

SPLITS = ("train", "validation", "test")


def prepare(df: pd.DataFrame, classes: list[str]) -> pd.DataFrame:
    unknown = sorted(set(df["label"]) - set(classes))
    if unknown:
        raise ValueError(f"labels not in config intent_classes: {unknown}")
    bad = sorted(set(df["split"]) - set(SPLITS))
    if bad:
        raise ValueError(f"unknown split values: {bad}")
    df = df.copy()
    df["label_id"] = df["label"].map({c: i for i, c in enumerate(classes)}).astype(int)
    return df.reset_index(drop=True)


def load_gold(cfg: dict, path: Path | None = None) -> pd.DataFrame:
    path = path or ROOT / cfg["data"]["labels_path"]
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df["id"] = df["id"].astype(int)
    return prepare(df, cfg["intent_classes"])


def split_frames(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    out = {s: df[df["split"] == s].reset_index(drop=True) for s in SPLITS}
    empty = [s for s, f in out.items() if f.empty]
    if empty:
        raise ValueError(f"no rows for split(s) {empty}")
    return out
