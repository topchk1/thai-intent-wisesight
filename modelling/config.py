"""Repository paths and the config.yaml loader."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONFIG = ROOT / "config.yaml"
RESULTS = ROOT / "results"
CHECKPOINTS = DATA / "checkpoints"


def load_config(path: Path = CONFIG) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
