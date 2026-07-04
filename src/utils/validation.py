from __future__ import annotations

import logging

import duckdb
import pandas as pd

from src.utils.db import table_exists, table_row_count

logger = logging.getLogger(__name__)


class DataValidationError(RuntimeError):
    """Raised when a data quality check fails."""


def require_columns(df: pd.DataFrame, required: list[str], dataset_name: str) -> None:
    missing = [column for column in required if column not in df.columns]
    if missing:
        available = "\n".join(f"- {column}" for column in df.columns)
        raise DataValidationError(
            f"{dataset_name} is missing required columns: {missing}\n\n"
            f"Available columns are:\n{available}\n\n"
            "Update the COLUMN_MAPPING dictionary near the top of the ingestion script "
            "or prepare a source extract with the required fields."
        )


def require_non_empty_table(conn: duckdb.DuckDBPyConnection, table_name: str) -> None:
    if not table_exists(conn, table_name):
        raise DataValidationError(f"Required table does not exist: {table_name}")
    count = table_row_count(conn, table_name)
    if count == 0:
        raise DataValidationError(f"Required table has no records: {table_name}")
    logger.info("Validation passed: %s has %s rows", table_name, count)


def require_no_duplicate_key(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    key_column: str,
) -> None:
    duplicates = conn.execute(
        f"""
        SELECT {key_column}, COUNT(*) AS record_count
        FROM {table_name}
        GROUP BY {key_column}
        HAVING COUNT(*) > 1
        LIMIT 10
        """
    ).fetchdf()

    if not duplicates.empty:
        raise DataValidationError(
            f"{table_name} contains duplicate {key_column} values. Sample:\n"
            f"{duplicates.to_string(index=False)}"
        )

    logger.info("Validation passed: %s has no duplicate %s", table_name, key_column)


def report_missing_join_rate(
    conn: duckdb.DuckDBPyConnection,
    left_table: str,
    right_table: str,
    key_column: str,
) -> float:
    result = conn.execute(
        f"""
        SELECT
            COUNT(*) AS total_rows,
            SUM(CASE WHEN r.{key_column} IS NULL THEN 1 ELSE 0 END) AS missing_rows
        FROM {left_table} l
        LEFT JOIN {right_table} r
            ON l.{key_column} = r.{key_column}
        """
    ).fetchone()
    total_rows = int(result[0] or 0)
    missing_rows = int(result[1] or 0)
    rate = missing_rows / total_rows if total_rows else 0.0
    logger.info(
        "Join quality %s -> %s on %s: %s/%s missing (%.2f%%)",
        left_table,
        right_table,
        key_column,
        missing_rows,
        total_rows,
        rate * 100,
    )
    return rate


def require_no_duplicate_dataframe_key(
    df: pd.DataFrame,
    key_column: str,
    dataset_name: str,
) -> None:
    duplicates = (
        df[df[key_column].notna()]
        .groupby(key_column)
        .size()
        .reset_index(name="record_count")
    )
    duplicates = duplicates[duplicates["record_count"] > 1]
    if not duplicates.empty:
        raise DataValidationError(
            f"{dataset_name} contains duplicate {key_column} values. Sample:\n"
            f"{duplicates.head(10).to_string(index=False)}"
        )


def log_null_percentages(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    if columns is None:
        info = conn.execute(f"DESCRIBE {table_name}").fetchdf()
        columns = info["column_name"].tolist()

    expressions = [
        f"""
        SELECT
            '{column}' AS column_name,
            COUNT(*) AS row_count,
            SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) AS null_count,
            ROUND(
                100.0 * SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0),
                2
            ) AS null_pct
        FROM {table_name}
        """
        for column in columns
    ]
    result = conn.execute(" UNION ALL ".join(expressions)).fetchdf()
    logger.info("Null percentage summary for %s:\n%s", table_name, result.to_string(index=False))
    return result


def log_numeric_summary(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    columns: list[str],
) -> pd.DataFrame:
    expressions = [
        f"""
        SELECT
            '{column}' AS column_name,
            MIN({column}) AS min_value,
            AVG({column}) AS avg_value,
            MAX({column}) AS max_value
        FROM {table_name}
        """
        for column in columns
    ]
    result = conn.execute(" UNION ALL ".join(expressions)).fetchdf()
    logger.info("Numeric summary for %s:\n%s", table_name, result.to_string(index=False))
    return result
