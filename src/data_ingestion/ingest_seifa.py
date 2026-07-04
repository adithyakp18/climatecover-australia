from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.config import resolve_raw_file
from src.data_ingestion.common import (
    build_rename_map,
    clean_sa2_code,
    first_existing_column,
    normalise_columns,
    read_tabular_file,
    to_numeric,
)
from src.utils.db import get_connection, write_df
from src.utils.validation import require_columns

logger = logging.getLogger(__name__)


SOURCE_FILENAME = "seifa_2021_sa2.xlsx"
SHEET_NAME: str | int | None = None

COLUMN_MAPPING = {
    "sa2_code": [
        "sa2_code",
        "sa2_code_2021",
        "sa2_code21",
        "2021_statistical_area_level_2_sa2_9_digit_code",
    ],
    "irsd_score": [
        "irsd_score",
        "index_of_relative_socio_economic_disadvantage_score",
        "score_irsd",
        "irsd",
        "score",
    ],
    "irsd_decile": [
        "irsd_decile",
        "index_of_relative_socio_economic_disadvantage_decile",
        "decile_irsd",
        "decile",
    ],
}

OPTIONAL_COLUMN_MAPPING = {
    "ier_score": [
        "ier_score",
        "index_of_economic_resources_score",
        "score_ier",
        "ier",
        "score_2",
    ],
    "ier_decile": [
        "ier_decile",
        "index_of_economic_resources_decile",
        "decile_ier",
        "decile_2",
    ],
}

OUTPUT_COLUMNS = [
    "sa2_code",
    "irsd_score",
    "irsd_decile",
    "ier_score",
    "ier_decile",
    "source_file",
]


def prepare_seifa(path: Path) -> pd.DataFrame:
    raw = read_tabular_file(path, sheet_name=SHEET_NAME)
    df = normalise_columns(raw)
    if "sa2_code" not in df.columns and path.suffix.lower() in {".xlsx", ".xls"}:
        raw = pd.read_excel(path, sheet_name="Table 1", header=5, dtype=str)
        df = normalise_columns(raw)
    rename_map = build_rename_map(df, COLUMN_MAPPING)
    df = df.rename(columns=rename_map)

    for target_column, candidates in OPTIONAL_COLUMN_MAPPING.items():
        source_column = first_existing_column(df, candidates)
        if source_column:
            df = df.rename(columns={source_column: target_column})
        else:
            df[target_column] = pd.NA

    require_columns(df, ["sa2_code", "irsd_score", "irsd_decile"], "SEIFA SA2")

    output = df[["sa2_code", "irsd_score", "irsd_decile", "ier_score", "ier_decile"]].copy()
    output["sa2_code"] = clean_sa2_code(output["sa2_code"])
    for column in ["irsd_score", "irsd_decile", "ier_score", "ier_decile"]:
        output[column] = to_numeric(output[column])
    output["irsd_decile"] = output["irsd_decile"].astype("Int64")
    output["ier_decile"] = output["ier_decile"].astype("Int64")
    output["source_file"] = path.name
    output = output.dropna(subset=["sa2_code", "irsd_score", "irsd_decile"])
    output = output[output["sa2_code"].str.len() > 0]
    output = output.drop_duplicates(subset=["sa2_code"], keep="first")
    return output[OUTPUT_COLUMNS]


def ingest_seifa(filename: str | Path = SOURCE_FILENAME) -> pd.DataFrame:
    path = resolve_raw_file(filename)
    df = prepare_seifa(path)
    conn = get_connection()
    try:
        write_df(conn, df, "fact_seifa")
    finally:
        conn.close()
    logger.info("Ingested fact_seifa from %s", path)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
    ingest_seifa()
