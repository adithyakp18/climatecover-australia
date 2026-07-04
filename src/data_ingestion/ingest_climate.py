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


SOURCE_FILENAME = "bom_sa2_climate.csv"
SHEET_NAME: str | int | None = None
PROCESSED_FILENAME = "fact_climate.csv"

COLUMN_MAPPING = {
    "sa2_code": [
        "sa2_code",
        "sa2_code_2021",
        "sa2_code21",
        "region_code",
    ],
    "annual_rainfall": [
        "annual_rainfall",
        "annual_rainfall_mm",
        "rainfall_annual_mm",
        "mean_annual_rainfall",
    ],
    "average_temperature": [
        "average_temperature",
        "average_temperature_c",
        "mean_temperature",
        "mean_temperature_c",
        "avg_temp",
    ],
    "extreme_heat_days": [
        "extreme_heat_days",
        "days_above_35c",
        "days_over_35c",
        "hot_days",
        "heat_days",
    ],
    "rainfall_anomaly": [
        "rainfall_anomaly",
        "rainfall_anomaly_mm",
        "rainfall_departure",
        "rainfall_variance_from_baseline",
    ],
}

OPTIONAL_SOURCE_COLUMNS = [
    "source",
    "dataset_source",
    "data_source",
    "source_url",
]

OUTPUT_COLUMNS = [
    "sa2_code",
    "annual_rainfall",
    "average_temperature",
    "extreme_heat_days",
    "rainfall_anomaly",
    "source",
    "source_file",
]


def prepare_climate(path: Path) -> pd.DataFrame:
    raw = read_tabular_file(path, sheet_name=SHEET_NAME)
    df = normalise_columns(raw)
    rename_map = build_rename_map(df, COLUMN_MAPPING)
    df = df.rename(columns=rename_map)

    source_column = first_existing_column(df, OPTIONAL_SOURCE_COLUMNS)
    if source_column:
        df = df.rename(columns={source_column: "source"})
    else:
        df["source"] = "Bureau of Meteorology prepared SA2 climate extract"

    require_columns(df, list(COLUMN_MAPPING.keys()), "BOM SA2 climate extract")

    output = df[
        [
            "sa2_code",
            "annual_rainfall",
            "average_temperature",
            "extreme_heat_days",
            "rainfall_anomaly",
            "source",
        ]
    ].copy()
    output["sa2_code"] = clean_sa2_code(output["sa2_code"])
    for column in [
        "annual_rainfall",
        "average_temperature",
        "extreme_heat_days",
        "rainfall_anomaly",
    ]:
        output[column] = to_numeric(output[column])

    output["source"] = output["source"].fillna(
        "Bureau of Meteorology prepared SA2 climate extract"
    )
    output["source_file"] = path.name
    output = output.dropna(subset=["sa2_code"])
    output = output[output["sa2_code"].str.len() > 0]
    require_no_duplicate_dataframe_key(output, "sa2_code", "BOM SA2 climate extract")
    return output[OUTPUT_COLUMNS]


def ingest_climate(filename: str | Path = SOURCE_FILENAME) -> pd.DataFrame:
    path = resolve_raw_file(filename)
    df = prepare_climate(path)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    processed_path = PROCESSED_DATA_DIR / PROCESSED_FILENAME
    df.to_csv(processed_path, index=False)
    logger.info("Wrote cleaned climate data to %s", processed_path)

    conn = get_connection()
    try:
        write_df(conn, df, "fact_climate")
    finally:
        conn.close()
    logger.info("Ingested fact_climate from %s", path)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
    ingest_climate()
