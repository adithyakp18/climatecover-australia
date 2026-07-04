from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.config import PROCESSED_DATA_DIR, SYNTHETIC_DATA_DIR
from src.utils.db import get_connection, write_df
from src.utils.validation import require_no_duplicate_dataframe_key, require_non_empty_table

logger = logging.getLogger(__name__)


PROCESSED_FILENAME = "synthetic_insurance.csv"

STATE_BASE_PREMIUMS = {
    "New South Wales": 1900.0,
    "Victoria": 1750.0,
    "Queensland": 2350.0,
    "South Australia": 1650.0,
    "Western Australia": 1850.0,
    "Tasmania": 1600.0,
    "Northern Territory": 2400.0,
    "Australian Capital Territory": 1550.0,
    "Other Territories": 1800.0,
}

DEFAULT_BASE_PREMIUM = 1850.0

MAX_LOADINGS = {
    "flood_loading": 1800.0,
    "bushfire_loading": 1400.0,
    "cyclone_loading": 1700.0,
    "storm_loading": 900.0,
    "rebuild_loading": 750.0,
}


def _normalise_state_name(value: object) -> str:
    text = str(value).strip()
    aliases = {
        "NSW": "New South Wales",
        "VIC": "Victoria",
        "QLD": "Queensland",
        "SA": "South Australia",
        "WA": "Western Australia",
        "TAS": "Tasmania",
        "NT": "Northern Territory",
        "ACT": "Australian Capital Territory",
    }
    return aliases.get(text, text)


def _score_to_loading(score: pd.Series, max_loading: float) -> pd.Series:
    return score.fillna(0).clip(lower=0, upper=100) / 100 * max_loading


def build_synthetic_insurance() -> pd.DataFrame:
    conn = get_connection()
    try:
        require_non_empty_table(conn, "foundation_region_climate")
        source = conn.execute(
            """
            SELECT
                sa2_code,
                state_name,
                median_weekly_household_income,
                median_monthly_mortgage_repayment,
                flood_risk_score,
                bushfire_risk_score,
                cyclone_risk_score,
                storm_risk_score
            FROM foundation_region_climate
            """
        ).fetchdf()
    finally:
        conn.close()

    if source.empty:
        raise ValueError("foundation_region_climate has no records; cannot build synthetic insurance.")

    output = pd.DataFrame()
    output["sa2_code"] = source["sa2_code"].astype(str)
    normalised_states = source["state_name"].map(_normalise_state_name)
    output["base_premium"] = normalised_states.map(STATE_BASE_PREMIUMS).fillna(DEFAULT_BASE_PREMIUM)

    output["flood_loading"] = _score_to_loading(
        source["flood_risk_score"],
        MAX_LOADINGS["flood_loading"],
    )
    output["bushfire_loading"] = _score_to_loading(
        source["bushfire_risk_score"],
        MAX_LOADINGS["bushfire_loading"],
    )
    output["cyclone_loading"] = _score_to_loading(
        source["cyclone_risk_score"],
        MAX_LOADINGS["cyclone_loading"],
    )
    output["storm_loading"] = _score_to_loading(
        source["storm_risk_score"],
        MAX_LOADINGS["storm_loading"],
    )

    income_rank = source["median_weekly_household_income"].rank(pct=True).fillna(0.5)
    mortgage_rank = source["median_monthly_mortgage_repayment"].rank(pct=True).fillna(0.5)
    rebuild_pressure = ((income_rank * 0.4) + (mortgage_rank * 0.6)).clip(lower=0, upper=1)
    output["rebuild_loading"] = rebuild_pressure * MAX_LOADINGS["rebuild_loading"]

    output["mitigation_discount"] = 0.0
    output["estimated_annual_premium"] = (
        output["base_premium"]
        + output["flood_loading"]
        + output["bushfire_loading"]
        + output["cyclone_loading"]
        + output["storm_loading"]
        + output["rebuild_loading"]
        - output["mitigation_discount"]
    ).round(2)

    for column in [
        "base_premium",
        "flood_loading",
        "bushfire_loading",
        "cyclone_loading",
        "storm_loading",
        "rebuild_loading",
        "mitigation_discount",
    ]:
        output[column] = output[column].round(2)

    output["premium_source"] = (
        "Synthetic estimate informed by public APRA, ICA and Actuaries Institute "
        "reporting; generated from SA2 hazard and demographic inputs"
    )
    output["data_type"] = "Synthetic"

    output = output[
        [
            "sa2_code",
            "estimated_annual_premium",
            "base_premium",
            "flood_loading",
            "bushfire_loading",
            "cyclone_loading",
            "storm_loading",
            "rebuild_loading",
            "mitigation_discount",
            "premium_source",
            "data_type",
        ]
    ]
    require_no_duplicate_dataframe_key(output, "sa2_code", "synthetic_insurance")
    return output


def create_synthetic_insurance() -> pd.DataFrame:
    df = build_synthetic_insurance()

    SYNTHETIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    synthetic_path = SYNTHETIC_DATA_DIR / PROCESSED_FILENAME
    processed_path = PROCESSED_DATA_DIR / PROCESSED_FILENAME
    df.to_csv(synthetic_path, index=False)
    df.to_csv(processed_path, index=False)
    logger.info("Wrote synthetic insurance data to %s", synthetic_path)
    logger.info("Wrote processed insurance data to %s", processed_path)

    conn = get_connection()
    try:
        write_df(conn, df, "synthetic_insurance")
    finally:
        conn.close()

    return df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
    create_synthetic_insurance()
