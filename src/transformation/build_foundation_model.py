from __future__ import annotations

import logging

from src.utils.db import get_connection, table_row_count
from src.utils.validation import (
    require_no_duplicate_key,
    require_non_empty_table,
    report_missing_join_rate,
)

logger = logging.getLogger(__name__)


def build_foundation_model() -> None:
    conn = get_connection()
    try:
        require_non_empty_table(conn, "dim_region")
        require_non_empty_table(conn, "fact_seifa")
        require_non_empty_table(conn, "fact_demographics")
        require_no_duplicate_key(conn, "dim_region", "sa2_code")

        report_missing_join_rate(conn, "dim_region", "fact_seifa", "sa2_code")
        report_missing_join_rate(conn, "dim_region", "fact_demographics", "sa2_code")

        conn.execute(
            """
            CREATE OR REPLACE TABLE foundation_region_profile AS
            SELECT
                r.sa2_code,
                r.sa2_name,
                r.state_name,
                s.irsd_score,
                s.irsd_decile,
                d.median_weekly_household_income,
                d.median_monthly_mortgage_repayment,
                d.median_weekly_rent,
                d.household_count
            FROM dim_region r
            LEFT JOIN fact_seifa s
                ON r.sa2_code = s.sa2_code
            LEFT JOIN fact_demographics d
                ON r.sa2_code = d.sa2_code
            """
        )

        require_non_empty_table(conn, "foundation_region_profile")
        row_count = table_row_count(conn, "foundation_region_profile")
        logger.info("Built foundation_region_profile with %s rows", row_count)

        missing_summary = conn.execute(
            """
            SELECT
                COUNT(*) AS total_regions,
                SUM(CASE WHEN irsd_score IS NULL THEN 1 ELSE 0 END) AS regions_missing_seifa,
                SUM(CASE WHEN median_weekly_household_income IS NULL THEN 1 ELSE 0 END)
                    AS regions_missing_demographics
            FROM foundation_region_profile
            """
        ).fetchdf()
        logger.info("Foundation missing-data summary:\n%s", missing_summary.to_string(index=False))
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
    build_foundation_model()
