from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def normalise_column_name(column: object) -> str:
    value = str(column).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def normalise_columns(df: pd.DataFrame) -> pd.DataFrame:
    output = df.copy()
    output.columns = [normalise_column_name(column) for column in output.columns]
    return output


def read_tabular_file(path: Path, sheet_name: str | int | None = None) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find source file: {path}\n"
            "Place the required ABS file in data/raw/ or update the filename in scripts/run_sprint1.py."
        )

    suffix = path.suffix.lower()
    logger.info("Reading source file %s", path)

    if suffix == ".csv":
        return pd.read_csv(path, dtype=str)
    if suffix in {".xlsx", ".xls"}:
        kwargs: dict[str, object] = {"dtype": str}
        if sheet_name is not None:
            kwargs["sheet_name"] = sheet_name
        else:
            kwargs["sheet_name"] = 0
        return pd.read_excel(path, **kwargs)
    if suffix == ".parquet":
        return pd.read_parquet(path)

    raise ValueError(
        f"Unsupported file type for {path}. Supported formats: CSV, XLSX, XLS, Parquet."
    )


def first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    normalised_candidates = [normalise_column_name(candidate) for candidate in candidates]
    for candidate in normalised_candidates:
        if candidate in df.columns:
            return candidate
    return None


def build_rename_map(df: pd.DataFrame, column_mapping: dict[str, list[str]]) -> dict[str, str]:
    rename_map: dict[str, str] = {}
    missing: dict[str, list[str]] = {}

    for target_column, candidates in column_mapping.items():
        source_column = first_existing_column(df, candidates)
        if source_column is None:
            missing[target_column] = candidates
        else:
            rename_map[source_column] = target_column

    if missing:
        available = "\n".join(f"- {column}" for column in df.columns)
        expected = "\n".join(
            f"- {target}: {', '.join(candidates)}"
            for target, candidates in missing.items()
        )
        raise ValueError(
            "Could not map all required source columns.\n\n"
            f"Missing target mappings:\n{expected}\n\n"
            f"Available columns after normalisation:\n{available}\n\n"
            "Update COLUMN_MAPPING near the top of the relevant ingestion script."
        )

    return rename_map


def clean_sa2_code(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.extract(r"(\d{9})", expand=False)
        .fillna(series.astype(str).str.strip())
    )


def to_numeric(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("not applicable", "", case=False, regex=False)
        .str.replace("n/a", "", case=False, regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")
