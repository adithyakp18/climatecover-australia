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


SOURCE_FILENAME = "census_2021_sa2_demographics.csv"
SHEET_NAME: str | int | None = None

COLUMN_MAPPING = {
    "sa2_code": [
        "sa2_code",
        "sa2_code_2021",
        "sa2_code21",
        "region_code",
    ],
    "median_weekly_household_income": [
        "median_weekly_household_income",
        "median_tot_hhd_inc_weekly",
        "median_household_income_weekly",
        "median_weekly_hhd_income",
    ],
    "median_monthly_mortgage_repayment": [
        "median_monthly_mortgage_repayment",
        "median_mortgage_repay_monthly",
        "median_mortgage_repayment_monthly",
        "median_monthly_mortgage",
    ],
    "median_weekly_rent": [
        "median_weekly_rent",
        "median_rent_weekly",
        "median_weekly_rental",
    ],
    "household_count": [
        "household_count",
        "total_households",
        "occupied_private_dwellings",
        "tot_hhd",
        "total_hhd",
    ],
}

OUTPUT_COLUMNS = [
    "sa2_code",
    "median_weekly_household_income",
    "median_monthly_mortgage_repayment",
    "median_weekly_rent",
    "household_count",
    "source_file",
]


def prepare_demographics(path: Path) -> pd.DataFrame:
    raw = read_tabular_file(path, sheet_name=SHEET_NAME)
    df = normalise_columns(raw)
    rename_map = build_rename_map(df, COLUMN_MAPPING)
    df = df.rename(columns=rename_map)

    require_columns(
        df,
        [
            "sa2_code",
            "median_weekly_household_income",
            "median_monthly_mortgage_repayment",
            "median_weekly_rent",
            "household_count",
        ],
        "ABS Census demographic extract",
    )

    output = df[
        [
            "sa2_code",
            "median_weekly_household_income",
            "median_monthly_mortgage_repayment",
            "median_weekly_rent",
            "household_count",
        ]
    ].copy()
    output["sa2_code"] = clean_sa2_code(output["sa2_code"])
    for column in [
        "median_weekly_household_income",
        "median_monthly_mortgage_repayment",
        "median_weekly_rent",
        "household_count",
    ]:
        output[column] = to_numeric(output[column])
    output["source_file"] = path.name
    output = output.dropna(subset=["sa2_code"])
    output = output[output["sa2_code"].str.len() > 0]
    output = output.drop_duplicates(subset=["sa2_code"], keep="first")
    return output[OUTPUT_COLUMNS]


def ingest_demographics(filename: str | Path = SOURCE_FILENAME) -> pd.DataFrame:
    path = resolve_raw_file(filename)
    df = prepare_demographics(path)
    conn = get_connection()
    try:
        write_df(conn, df, "fact_demographics")
    finally:
        conn.close()
    logger.info("Ingested fact_demographics from %s", path)
    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
    ingest_demographics()
