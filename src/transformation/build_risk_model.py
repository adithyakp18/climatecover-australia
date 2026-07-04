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


def build_risk_model() -> None:
    conn = get_connection()
    try:
        require_non_empty_table(conn, "foundation_region_climate")
        require_non_empty_table(conn, "synthetic_insurance")
        require_no_duplicate_key(conn, "synthetic_insurance", "sa2_code")

        report_missing_join_rate(conn, "foundation_region_climate", "synthetic_insurance", "sa2_code")

        conn.execute(
            """
            CREATE OR REPLACE TABLE fact_affordability AS
            SELECT
                c.sa2_code,
                c.median_weekly_household_income * 52 AS median_household_income,
                i.estimated_annual_premium,
                CASE
                    WHEN c.median_weekly_household_income IS NULL
                        OR c.median_weekly_household_income <= 0
                        THEN NULL
                    ELSE i.estimated_annual_premium / (c.median_weekly_household_income * 52)
                END AS affordability_ratio,
                CASE
                    WHEN c.median_weekly_household_income IS NULL
                        OR c.median_weekly_household_income <= 0
                        THEN NULL
                    ELSE 100 * i.estimated_annual_premium / (c.median_weekly_household_income * 52)
                END AS premium_to_income_percent,
                CASE
                    WHEN c.median_weekly_household_income IS NULL
                        OR c.median_weekly_household_income <= 0
                        THEN NULL
                    WHEN 100 * i.estimated_annual_premium / (c.median_weekly_household_income * 52) < 2
                        THEN 'Low'
                    WHEN 100 * i.estimated_annual_premium / (c.median_weekly_household_income * 52) < 4
                        THEN 'Moderate'
                    WHEN 100 * i.estimated_annual_premium / (c.median_weekly_household_income * 52) < 8.33
                        THEN 'High'
                    ELSE 'Severe'
                END AS affordability_band
            FROM foundation_region_climate c
            LEFT JOIN synthetic_insurance i
                ON c.sa2_code = i.sa2_code
            """
        )

        conn.execute(
            """
            CREATE OR REPLACE TABLE fact_property_risk AS
            WITH base AS (
                SELECT
                    sa2_code,
                    COALESCE(flood_risk_score, 0) AS flood_risk_score,
                    COALESCE(bushfire_risk_score, 0) AS bushfire_risk_score,
                    COALESCE(cyclone_risk_score, 0) AS cyclone_risk_score,
                    COALESCE(storm_risk_score, 0) AS storm_risk_score,
                    COALESCE(overall_hazard_score, 0) AS overall_hazard_score,
                    COALESCE(extreme_heat_days, 0) AS extreme_heat_days,
                    COALESCE(ABS(rainfall_anomaly), 0) AS rainfall_anomaly_abs,
                    CASE
                        WHEN irsd_decile BETWEEN 1 AND 10 THEN (11 - irsd_decile) * 10
                        ELSE 50
                    END AS vulnerability_score
                FROM foundation_region_climate
            ),
            climate_norm AS (
                SELECT
                    *,
                    CASE
                        WHEN MAX(extreme_heat_days) OVER () = MIN(extreme_heat_days) OVER () THEN 0
                        ELSE 100 * (extreme_heat_days - MIN(extreme_heat_days) OVER ())
                            / NULLIF(MAX(extreme_heat_days) OVER () - MIN(extreme_heat_days) OVER (), 0)
                    END AS heat_score,
                    CASE
                        WHEN MAX(rainfall_anomaly_abs) OVER () = MIN(rainfall_anomaly_abs) OVER () THEN 0
                        ELSE 100 * (rainfall_anomaly_abs - MIN(rainfall_anomaly_abs) OVER ())
                            / NULLIF(MAX(rainfall_anomaly_abs) OVER () - MIN(rainfall_anomaly_abs) OVER (), 0)
                    END AS rainfall_anomaly_score
                FROM base
            ),
            scored AS (
                SELECT
                    sa2_code,
                    flood_risk_score * 0.30 AS flood_component,
                    bushfire_risk_score * 0.25 AS bushfire_component,
                    ((cyclone_risk_score + storm_risk_score) / 2) * 0.15 AS cyclone_component,
                    overall_hazard_score * 0.10 AS storm_component,
                    ((heat_score + rainfall_anomaly_score) / 2) * 0.10 AS climate_component,
                    vulnerability_score * 0.10 AS vulnerability_component
                FROM climate_norm
            )
            SELECT
                sa2_code,
                LEAST(
                    100,
                    GREATEST(
                        0,
                        flood_component
                        + bushfire_component
                        + cyclone_component
                        + storm_component
                        + climate_component
                        + vulnerability_component
                    )
                ) AS property_risk_score,
                flood_component,
                bushfire_component,
                cyclone_component,
                storm_component,
                climate_component,
                vulnerability_component,
                CASE
                    WHEN flood_component
                        + bushfire_component
                        + cyclone_component
                        + storm_component
                        + climate_component
                        + vulnerability_component < 25 THEN 'Low'
                    WHEN flood_component
                        + bushfire_component
                        + cyclone_component
                        + storm_component
                        + climate_component
                        + vulnerability_component < 50 THEN 'Moderate'
                    WHEN flood_component
                        + bushfire_component
                        + cyclone_component
                        + storm_component
                        + climate_component
                        + vulnerability_component < 75 THEN 'High'
                    ELSE 'Severe'
                END AS risk_band
            FROM scored
            """
        )

        conn.execute(
            """
            CREATE OR REPLACE TABLE foundation_region_risk AS
            SELECT
                c.sa2_code,
                c.sa2_name,
                c.state_name,
                c.irsd_score,
                c.irsd_decile,
                c.median_weekly_household_income,
                c.median_weekly_household_income * 52 AS median_annual_household_income,
                c.median_monthly_mortgage_repayment,
                c.median_weekly_rent,
                c.household_count,
                c.annual_rainfall,
                c.average_temperature,
                c.extreme_heat_days,
                c.rainfall_anomaly,
                c.flood_risk_score,
                c.bushfire_risk_score,
                c.cyclone_risk_score,
                c.storm_risk_score,
                c.overall_hazard_score,
                i.estimated_annual_premium,
                i.base_premium,
                i.flood_loading,
                i.bushfire_loading,
                i.cyclone_loading,
                i.storm_loading,
                i.rebuild_loading,
                i.mitigation_discount,
                i.premium_source,
                i.data_type,
                a.affordability_ratio,
                a.premium_to_income_percent,
                a.affordability_band,
                r.property_risk_score,
                r.flood_component,
                r.bushfire_component,
                r.cyclone_component,
                r.storm_component,
                r.climate_component,
                r.vulnerability_component,
                r.risk_band,
                (
                    COALESCE(r.property_risk_score, 0) * 0.6
                    + LEAST(COALESCE(a.premium_to_income_percent, 0) / 8.33 * 100, 100) * 0.4
                ) AS intervention_priority_score
            FROM foundation_region_climate c
            LEFT JOIN synthetic_insurance i
                ON c.sa2_code = i.sa2_code
            LEFT JOIN fact_affordability a
                ON c.sa2_code = a.sa2_code
            LEFT JOIN fact_property_risk r
                ON c.sa2_code = r.sa2_code
            """
        )

        for table in [
            "fact_affordability",
            "fact_property_risk",
            "foundation_region_risk",
        ]:
            require_non_empty_table(conn, table)
            require_no_duplicate_key(conn, table, "sa2_code")
            logger.info("%s rows: %s", table, table_row_count(conn, table))

        log_null_percentages(
            conn,
            "foundation_region_risk",
            [
                "sa2_code",
                "estimated_annual_premium",
                "affordability_ratio",
                "premium_to_income_percent",
                "property_risk_score",
                "intervention_priority_score",
            ],
        )
        log_numeric_summary(
            conn,
            "foundation_region_risk",
            [
                "estimated_annual_premium",
                "affordability_ratio",
                "premium_to_income_percent",
                "property_risk_score",
                "intervention_priority_score",
            ],
        )

        premium_range_issues = conn.execute(
            """
            SELECT COUNT(*)
            FROM synthetic_insurance
            WHERE estimated_annual_premium < 500
                OR estimated_annual_premium > 20000
            """
        ).fetchone()[0]
        if premium_range_issues:
            raise ValueError(
                f"Premium validation failed: {premium_range_issues} records outside expected range."
            )

        risk_range_issues = conn.execute(
            """
            SELECT COUNT(*)
            FROM fact_property_risk
            WHERE property_risk_score < 0
                OR property_risk_score > 100
            """
        ).fetchone()[0]
        if risk_range_issues:
            raise ValueError(
                f"Risk score validation failed: {risk_range_issues} records outside 0-100."
            )

        affordability_range_issues = conn.execute(
            """
            SELECT COUNT(*)
            FROM fact_affordability
            WHERE affordability_ratio < 0
                OR affordability_ratio > 1
            """
        ).fetchone()[0]
        if affordability_range_issues:
            raise ValueError(
                "Affordability validation failed: "
                f"{affordability_range_issues} records outside expected 0-1 ratio range."
            )

        band_distribution = conn.execute(
            """
            SELECT
                affordability_band,
                risk_band,
                COUNT(*) AS region_count
            FROM foundation_region_risk
            GROUP BY affordability_band, risk_band
            ORDER BY region_count DESC
            """
        ).fetchdf()
        logger.info("Risk and affordability band distribution:\n%s", band_distribution.to_string(index=False))
    finally:
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s - %(message)s")
    build_risk_model()
