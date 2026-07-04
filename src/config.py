from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
REFERENCE_DATA_DIR = DATA_DIR / "reference"
SYNTHETIC_DATA_DIR = DATA_DIR / "synthetic"
DB_DIR = PROJECT_ROOT / "db"

DEFAULT_DB_PATH = DB_DIR / "climatecover.duckdb"
DB_PATH = Path(os.getenv("CLIMATECOVER_DB_PATH", DEFAULT_DB_PATH))


REQUIRED_DIRECTORIES = [
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    REFERENCE_DATA_DIR,
    SYNTHETIC_DATA_DIR,
    DB_DIR,
]


def ensure_directories() -> None:
    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)


def resolve_raw_file(filename: str | Path) -> Path:
    path = Path(filename)
    if path.is_absolute():
        return path
    return RAW_DATA_DIR / path
