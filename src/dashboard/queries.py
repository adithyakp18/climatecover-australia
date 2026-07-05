from __future__ import annotations

from pathlib import Path
import json

import duckdb
import pandas as pd
import streamlit as st

from src.config import DB_PATH


REQUIRED_TABLE = "foundation_region_risk"
MANIFEST_PATH = Path(__file__).resolve().parents[2] / "docs" / "data_refresh_manifest.json"
SOURCE_CATALOG_PATH = Path(__file__).resolve().parents[2] / "docs" / "data_source_catalog.json"


def database_exists(db_path: Path = DB_PATH) -> bool:
    return db_path.exists()


@st.cache_resource(show_spinner=False)
def get_connection(db_path: str = str(DB_PATH)) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(db_path, read_only=True)


def table_exists(table_name: str, db_path: Path = DB_PATH) -> bool:
    if not database_exists(db_path):
        return False
    conn = duckdb.connect(str(db_path), read_only=True)
    try:
        result = conn.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name = ?
            """,
            [table_name],
        ).fetchone()
        return bool(result[0])
    finally:
        conn.close()


def risk_table_available() -> bool:
    return table_exists(REQUIRED_TABLE)


def ensure_dashboard_data() -> tuple[bool, str]:
    if risk_table_available():
        return True, "Dashboard database is ready."

    try:
        from scripts.prepare_real_abs_data import main as prepare_real_abs_data
        from scripts.create_abs_backed_database import main as create_abs_backed_database

        prepare_real_abs_data()
        create_abs_backed_database()
    except Exception as exc:
        return False, str(exc)

    if hasattr(get_connection, "clear"):
        get_connection.clear()
    for cached_function in [
        load_foundation_risk,
        load_kpis,
        load_band_distribution,
        load_top_regions,
        load_region_names,
        load_data_lineage,
        load_data_quality_checks,
    ]:
        if hasattr(cached_function, "clear"):
            cached_function.clear()

    if risk_table_available():
        return True, "Dashboard database was prepared successfully."
    return False, "Dashboard database build finished, but the required table was not found."


@st.cache_data(show_spinner=False)
def load_data_manifest() -> dict[str, object]:
    if not MANIFEST_PATH.exists():
        return {}
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


@st.cache_data(show_spinner=False)
def load_source_catalog() -> pd.DataFrame:
    if not SOURCE_CATALOG_PATH.exists():
        return pd.DataFrame(
            columns=[
                "layer",
                "field_group",
                "source",
                "source_url",
                "data_status",
                "refresh_method",
                "business_use",
            ]
        )
    try:
        return pd.DataFrame(json.loads(SOURCE_CATALOG_PATH.read_text(encoding="utf-8")))
    except json.JSONDecodeError:
        return pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_data_lineage() -> pd.DataFrame:
    if table_exists("data_lineage"):
        conn = get_connection()
        return conn.execute(
            """
            SELECT
                layer,
                field_group,
                source,
                source_url,
                data_status,
                refresh_method,
                business_use
            FROM data_lineage
            ORDER BY
                CASE data_status
                    WHEN 'Real Public Data' THEN 1
                    WHEN 'Calculated Metric' THEN 2
                    ELSE 3
                END,
                layer
            """
        ).fetchdf()
    return load_source_catalog()


@st.cache_data(show_spinner=False)
def load_data_quality_checks() -> pd.DataFrame:
    conn = get_connection()
    rows = []

    def add_check(check_name: str, result: str, value: object, detail: str) -> None:
        rows.append(
            {
                "Check": check_name,
                "Result": result,
                "Value": value,
                "Detail": detail,
            }
        )

    total_regions = conn.execute("SELECT COUNT(*) FROM foundation_region_risk").fetchone()[0]
    duplicate_regions = conn.execute(
        """
        SELECT COUNT(*)
        FROM (
            SELECT sa2_code
            FROM foundation_region_risk
            GROUP BY sa2_code
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]
    add_check(
        "Regional coverage",
        "Pass" if total_regions > 0 else "Fail",
        f"{total_regions:,}",
        "Number of regional records available to the dashboard.",
    )
    add_check(
        "Duplicate region keys",
        "Pass" if duplicate_regions == 0 else "Review",
        f"{duplicate_regions:,}",
        "SA2 code should be unique in the regional risk layer.",
    )

    lineage_available = table_exists("data_lineage")
    add_check(
        "Source lineage available",
        "Pass" if lineage_available else "Review",
        "Available" if lineage_available else "Catalog fallback",
        "Shows which field groups are real public data, modelled indicators or calculated metrics.",
    )

    if table_exists("fact_demographics"):
        demographic_sources = conn.execute(
            """
            SELECT
                source_type,
                COUNT(*) AS records
            FROM fact_demographics
            GROUP BY source_type
            ORDER BY records DESC
            """
        ).fetchall()
        source_summary = ", ".join(
            f"{source_type or 'Unknown'}: {records:,}" for source_type, records in demographic_sources
        )
        real_household_records = sum(
            records for source_type, records in demographic_sources if source_type == "Real Public Data"
        )
        add_check(
            "Household indicator source",
            "Pass" if real_household_records > 0 else "Review",
            source_summary or "Unavailable",
            "Confirms whether household affordability fields are loaded from ABS Census or modelled fallback indicators.",
        )

    for column, label in [
        ("irsd_score", "SEIFA IRSD score completeness"),
        ("median_weekly_household_income", "Household income completeness"),
        ("property_risk_score", "Property risk score completeness"),
        ("estimated_annual_premium", "Insurance affordability estimate completeness"),
    ]:
        null_rate = conn.execute(
            f"""
            SELECT
                100.0 * SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) / COUNT(*)
            FROM foundation_region_risk
            """
        ).fetchone()[0]
        add_check(
            label,
            "Pass" if null_rate < 5 else "Review",
            f"{null_rate:.2f}%",
            f"Null percentage for {label.lower()}.",
        )

    min_risk, max_risk = conn.execute(
        """
        SELECT MIN(property_risk_score), MAX(property_risk_score)
        FROM foundation_region_risk
        """
    ).fetchone()
    risk_range_ok = (min_risk is not None and max_risk is not None and 0 <= min_risk <= max_risk <= 100)
    add_check(
        "Risk score range",
        "Pass" if risk_range_ok else "Review",
        f"{min_risk:.1f} to {max_risk:.1f}" if min_risk is not None else "n/a",
        "Property risk scores should sit between 0 and 100.",
    )

    min_premium, max_premium = conn.execute(
        """
        SELECT MIN(estimated_annual_premium), MAX(estimated_annual_premium)
        FROM foundation_region_risk
        """
    ).fetchone()
    premium_range_ok = (
        min_premium is not None
        and max_premium is not None
        and 500 <= min_premium <= max_premium <= 20000
    )
    add_check(
        "Premium estimate range",
        "Pass" if premium_range_ok else "Review",
        f"${min_premium:,.0f} to ${max_premium:,.0f}" if min_premium is not None else "n/a",
        "Estimated annual premium should remain within the governed screening range.",
    )

    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False)
def load_foundation_risk() -> pd.DataFrame:
    conn = get_connection()
    return conn.execute(
        """
        SELECT *
        FROM foundation_region_risk
        """
    ).fetchdf()


@st.cache_data(show_spinner=False)
def load_kpis() -> dict[str, float]:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS total_regions,
            SUM(CASE WHEN risk_band IN ('High', 'Severe') THEN 1 ELSE 0 END) AS high_risk_regions,
            SUM(CASE WHEN affordability_band = 'Severe' THEN 1 ELSE 0 END)
                AS severe_affordability_regions,
            AVG(property_risk_score) AS avg_property_risk_score,
            AVG(affordability_ratio) AS avg_affordability_ratio
        FROM foundation_region_risk
        """
    ).fetchone()
    return {
        "total_regions": row[0] or 0,
        "high_risk_regions": row[1] or 0,
        "severe_affordability_regions": row[2] or 0,
        "avg_property_risk_score": row[3] or 0,
        "avg_affordability_ratio": row[4] or 0,
    }


@st.cache_data(show_spinner=False)
def load_band_distribution(column_name: str) -> pd.DataFrame:
    if column_name not in {"risk_band", "affordability_band"}:
        raise ValueError(f"Unsupported band distribution column: {column_name}")
    conn = get_connection()
    return conn.execute(
        f"""
        SELECT
            {column_name} AS band,
            COUNT(*) AS region_count
        FROM foundation_region_risk
        GROUP BY {column_name}
        ORDER BY region_count DESC
        """
    ).fetchdf()


@st.cache_data(show_spinner=False)
def load_top_regions(metric: str, limit: int = 10) -> pd.DataFrame:
    allowed_metrics = {
        "property_risk_score",
        "premium_to_income_percent",
        "estimated_annual_premium",
        "intervention_priority_score",
    }
    if metric not in allowed_metrics:
        raise ValueError(f"Unsupported metric: {metric}")
    conn = get_connection()
    return conn.execute(
        f"""
        SELECT
            sa2_name,
            state_name,
            estimated_annual_premium,
            premium_to_income_percent,
            affordability_band,
            property_risk_score,
            risk_band,
            intervention_priority_score
        FROM foundation_region_risk
        ORDER BY {metric} DESC NULLS LAST
        LIMIT ?
        """,
        [limit],
    ).fetchdf()


@st.cache_data(show_spinner=False)
def load_region_names() -> pd.DataFrame:
    conn = get_connection()
    return conn.execute(
        """
        SELECT
            sa2_code,
            sa2_name,
            state_name
        FROM foundation_region_risk
        ORDER BY state_name, sa2_name
        """
    ).fetchdf()


def filter_risk_data(
    df: pd.DataFrame,
    states: list[str],
    risk_bands: list[str],
    affordability_bands: list[str],
    search_text: str,
) -> pd.DataFrame:
    filtered = df.copy()
    if states:
        filtered = filtered[filtered["state_name"].isin(states)]
    if risk_bands:
        filtered = filtered[filtered["risk_band"].isin(risk_bands)]
    if affordability_bands:
        filtered = filtered[filtered["affordability_band"].isin(affordability_bands)]
    if search_text:
        term = search_text.strip().lower()
        filtered = filtered[
            filtered["sa2_name"].str.lower().str.contains(term, na=False)
            | filtered["sa2_code"].astype(str).str.lower().str.contains(term, na=False)
        ]
    return filtered
