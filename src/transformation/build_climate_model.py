from __future__ import annotations

import logging

from src.utils.db import get_connection, table_row_count
from src.utils.validation import (
    log_null_percentages,
    log_numeric_summary,
    require_no_duplicate_key,
    require_non_empty_table,
    report_missing_join_rate,
)

logger = logging.getLogger(__name__)


CLIMATE_NUMERIC_COLUMNS = [
    "annual_rainfall",
    "average_temperature",
    "extreme_heat_days",
    "rainfall_anomaly",
]

HAZARD_NUMERIC_COLUMNS = [
    "flood_risk_score",
    "bushfire_risk_score",
    "cyclone_risk_score",
    "storm_risk_score",
    "overall_hazard_score",
]


def build_climate_model() -> None:
    conn = get_connection()
    try:
        require_non_empty_table(conn, "foundation_region_profile")
        require_non_empty_table(conn, "fact_climate")
        require_non_empty_table(conn, "fact_hazard")
        require_no_duplicate_key(conn, "fact_climate", "sa2_code")
        require_no_duplicate_key(conn, "fact_hazard", "sa2_code")
        log_null_percentages(conn, "fact_climate", ["sa2_code", *CLIMATE_NUMERIC_COLUMNS])
        log_null_percentages(conn, "fact_hazard", ["sa2_code", *HAZARD_NUMERIC_COLUMNS])
        log_numeric_summary(conn, "fact_climate", CLIMATE_NUMERIC_COLUMNS)
        log_numeric_summary(conn, "fact_hazard", HAZARD_NUMERIC_COLUMNS)

        climate_missing_rate = report_missing_join_rate(
            conn,
            "foundation_region_profile",
            "fact_climate",
            "sa2_code",
        )
        hazard_missing_rate = report_missing_join_rate(
            conn,
            "foundation_region_profile",
            "fact_hazard",
            "sa2_code",
        )

        conn.execute(
            """
            CREATE OR REPLACE TABLE foundation_region_climate AS
            SELECT
                p.sa2_code,
                p.sa2_name,
                p.state_name,
                p.irsd_score,
                p.irsd_decile,
                p.median_weekly_household_income,
                p.median_monthly_mortgage_repayment,
                p.median_weekly_rent,
                p.household_count,
                c.annual_rainfall,
                c.average_temperature,
                c.extreme_heat_days,
                c.rainfall_anomaly,
                h.flood_risk_score,
                h.bushfire_risk_score,
                h.cyclone_risk_score,
                h.storm_risk_score,
                h.overall_hazard_score
            FROM foundation_region_profile p
            LEFT JOIN fact_climate c
                ON p.sa2_code = c.sa2_code
            LEFT JOIN fact_hazard h
                ON p.sa2_code = h.sa2_code
            """
        )

        require_non_empty_table(conn, "foundation_region_climate")
        row_count = table_row_count(conn, "foundation_region_climate")
        logger.info("Built foundation_region_climate with %s rows", row_count)
        logger.info(
            "Sprint 2 join summary: climate missing %.2f%%, hazard missing %.2f%%",
            climate_missing_rate * 100,
            hazard_missing_rate * 100,
        )

        log_null_percentages(
            conn,
            "foundation_region_climate",
            [
                "sa2_code",
                "irsd_score",
                "median_weekly_household_income",
                *CLIMATE_NUMERIC_COLUMNS,
                *HAZARD_NUMERIC_COLUMNS,
            ],
        )
        log_numeric_summary(
            conn,
            "foundation_region_climate",
            [
                "irsd_score",
                "median_weekly_household_income",
                *CLIMATE_NUMERIC_COLUMNS,
                *HAZARD_NUMERIC_COLUMNS,
            ],
        )
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
    build_climate_model()
