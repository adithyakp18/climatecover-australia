from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DATA_DIR, resolve_raw_file
from src.data_ingestion.common import (
    build_rename_map,
    clean_sa2_code,
    first_existing_column,
    normalise_columns,
    read_tabular_file,
    to_numeric,
)
from src.utils.db import get_connection, write_df
from src.utils.validation import require_columns, require_no_duplicate_dataframe_key

logger = logging.getLogger(__name__)


SOURCE_FILENAME = "hazard_sa2_scores.csv"
SHEET_NAME: str | int | None = None
PROCESSED_FILENAME = "fact_hazard.csv"

COLUMN_MAPPING = {
    "sa2_code": [
        "sa2_code",
        "sa2_code_2021",
        "sa2_code21",
        "region_code",
    ],
    "flood_risk_score": [
        "flood_risk_score",
        "flood_score",
        "flood_exposure_score",
        "flood_hazard_score",
    ],
    "bushfire_risk_score": [
        "bushfire_risk_score",
        "bushfire_score",
        "bushfire_exposure_score",
        "fire_risk_score",
    ],
    "cyclone_risk_score": [
        "cyclone_risk_score",
        "cyclone_score",
        "cyclone_exposure_score",
        "tropical_cyclone_risk_score",
    ],
    "storm_risk_score": [
        "storm_risk_score",
        "storm_score",
        "storm_exposure_score",
        "severe_storm_risk_score",
    ],
}

OPTIONAL_OVERALL_COLUMNS = [
    "overall_hazard_score",
    "hazard_score",
    "total_hazard_score",
]

OPTIONAL_SOURCE_COLUMNS = [
    "source",
    "dataset_source",
    "data_source",
    "source_url",
]

RISK_COLUMNS = [
    "flood_risk_score",
    "bushfire_risk_score",
    "cyclone_risk_score",
    "storm_risk_score",
]

OUTPUT_COLUMNS = [
    "sa2_code",
    "flood_risk_score",
    "bushfire_risk_score",
    "cyclone_risk_score",
    "storm_risk_score",
    "overall_hazard_score",
    "source",
    "source_file",
]


def _clip_score(series: pd.Series, column_name: str) -> pd.Series:
    below_zero = int((series < 0).sum())
    above_hundred = int((series > 100).sum())
    if below_zero or above_hundred:
        logger.warning(
            "%s contains %s values below 0 and %s values above 100; clipping to 0-100",
            column_name,
            below_zero,
            above_hundred,
        )
    return series.clip(lower=0, upper=100)


def prepare_hazard(path: Path) -> pd.DataFrame:
    raw = read_tabular_file(path, sheet_name=SHEET_NAME)
    df = normalise_columns(raw)
    rename_map = build_rename_map(df, COLUMN_MAPPING)
    df = df.rename(columns=rename_map)

    overall_column = first_existing_column(df, OPTIONAL_OVERALL_COLUMNS)
    if overall_column:
        df = df.rename(columns={overall_column: "overall_hazard_score"})

    source_column = first_existing_column(df, OPTIONAL_SOURCE_COLUMNS)
    if source_column:
        df = df.rename(columns={source_column: "source"})
    else:
        df["source"] = "Prepared SA2 hazard extract from GA/data.gov.au/state open data"

    require_columns(df, ["sa2_code", *RISK_COLUMNS], "SA2 hazard score extract")

    output_columns = ["sa2_code", *RISK_COLUMNS, "source"]
    if "overall_hazard_score" in df.columns:
        output_columns.insert(-1, "overall_hazard_score")

    output = df[output_columns].copy()
    output["sa2_code"] = clean_sa2_code(output["sa2_code"])
    for column in RISK_COLUMNS:
        output[column] = _clip_score(to_numeric(output[column]), column)

    if "overall_hazard_score" in output.columns:
        output["overall_hazard_score"] = _clip_score(
            to_numeric(output["overall_hazard_score"]),
            "overall_hazard_score",
        )
        missing_overall = output["overall_hazard_score"].isna()
        if missing_overall.any():
            output.loc[missing_overall, "overall_hazard_score"] = output.loc[
                missing_overall,
                RISK_COLUMNS,
            ].mean(axis=1, skipna=True)
    else:
        output["overall_hazard_score"] = output[RISK_COLUMNS].mean(axis=1, skipna=True)

    output["overall_hazard_score"] = _clip_score(
        output["overall_hazard_score"],
        "overall_hazard_score",
    )
    output["source"] = output["source"].fillna(
        "Prepared SA2 hazard extract from GA/data.gov.au/state open data"
    )
    output["source_file"] = path.name
    output = output.dropna(subset=["sa2_code"])
    output = output[output["sa2_code"].str.len() > 0]
    require_no_duplicate_dataframe_key(output, "sa2_code", "SA2 hazard score extract")
    return output[OUTPUT_COLUMNS]


def ingest_hazard(filename: str | Path = SOURCE_FILENAME) -> pd.DataFrame:
    path = resolve_raw_file(filename)
    df = prepare_hazard(path)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    processed_path = PROCESSED_DATA_DIR / PROCESSED_FILENAME
    df.to_csv(processed_path, index=False)
    logger.info("Wrote cleaned hazard data to %s", processed_path)

    conn = get_connection()
    try:
        write_df(conn, df, "fact_hazard")
    finally:
        conn.close()
    logger.info("Ingested fact_hazard from %s", path)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
    ingest_hazard()
