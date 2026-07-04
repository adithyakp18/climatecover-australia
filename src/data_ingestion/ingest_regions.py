from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.config import resolve_raw_file
from src.data_ingestion.common import (
    build_rename_map,
    clean_sa2_code,
    normalise_columns,
    read_tabular_file,
    to_numeric,
)
from src.utils.db import get_connection, write_df
from src.utils.validation import require_columns

logger = logging.getLogger(__name__)


SOURCE_FILENAME = "asgs_sa2_regions.csv"
SHEET_NAME: str | int | None = None

COLUMN_MAPPING = {
    "sa2_code": [
        "sa2_code",
        "sa2_code_2021",
        "sa2_code21",
        "sa2_maincode_2021",
        "sa2_maincode21",
        "sa2_maincode",
    ],
    "sa2_name": [
        "sa2_name",
        "sa2_name_2021",
        "sa2_name21",
    ],
    "state_name": [
        "state_name",
        "state_name_2021",
        "state",
        "ste_name_2021",
        "ste_name21",
        "ste_name",
    ],
}

OPTIONAL_COLUMN_MAPPING = {
    "gccsa_name": [
        "gccsa_name",
        "gccsa_name_2021",
        "gccsa_name21",
    ],
    "area_sq_km": [
        "area_sq_km",
        "areasqkm",
        "area_albers_sqkm",
        "area_km2",
    ],
}

OUTPUT_COLUMNS = [
    "sa2_code",
    "sa2_name",
    "state_name",
    "gccsa_name",
    "area_sq_km",
    "source_file",
]


def prepare_regions(path: Path) -> pd.DataFrame:
    raw = read_tabular_file(path, sheet_name=SHEET_NAME)
    df = normalise_columns(raw)
    rename_map = build_rename_map(df, COLUMN_MAPPING)
    df = df.rename(columns=rename_map)

    for target_column, candidates in OPTIONAL_COLUMN_MAPPING.items():
        for candidate in candidates:
            candidate_norm = candidate.lower()
            if candidate_norm in df.columns:
                df = df.rename(columns={candidate_norm: target_column})
                break
        if target_column not in df.columns:
            df[target_column] = pd.NA

    require_columns(df, ["sa2_code", "sa2_name", "state_name"], "ASGS SA2 regions")

    output = df[["sa2_code", "sa2_name", "state_name", "gccsa_name", "area_sq_km"]].copy()
    output["sa2_code"] = clean_sa2_code(output["sa2_code"])
    output["sa2_name"] = output["sa2_name"].astype(str).str.strip()
    output["state_name"] = output["state_name"].astype(str).str.strip()
    output["gccsa_name"] = output["gccsa_name"].astype(str).str.strip().replace({"<NA>": pd.NA})
    output["area_sq_km"] = to_numeric(output["area_sq_km"])
    output["source_file"] = path.name
    output = output.dropna(subset=["sa2_code"])
    output = output[output["sa2_code"].str.len() > 0]
    output = output.drop_duplicates(subset=["sa2_code"], keep="first")
    return output[OUTPUT_COLUMNS]


def ingest_regions(filename: str | Path = SOURCE_FILENAME) -> pd.DataFrame:
    path = resolve_raw_file(filename)
    df = prepare_regions(path)
    conn = get_connection()
    try:
        write_df(conn, df, "dim_region")
    finally:
        conn.close()
    logger.info("Ingested dim_region from %s", path)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
    ingest_regions()
