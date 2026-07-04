from __future__ import annotations

import logging
from pathlib import Path

import duckdb
import pandas as pd

from src.config import DB_PATH, ensure_directories

logger = logging.getLogger(__name__)


def get_connection(db_path: Path = DB_PATH) -> duckdb.DuckDBPyConnection:
    ensure_directories()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Opening DuckDB database at %s", db_path)
    return duckdb.connect(str(db_path))


def write_df(
    conn: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    table_name: str,
    replace: bool = True,
) -> None:
    if df.empty:
        raise ValueError(f"Refusing to write empty DataFrame to {table_name}.")

    temp_name = f"tmp_{table_name}"
    conn.register(temp_name, df)
    mode = "CREATE OR REPLACE" if replace else "CREATE"
    conn.execute(f"{mode} TABLE {table_name} AS SELECT * FROM {temp_name}")
    conn.unregister(temp_name)
    row_count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    logger.info("Wrote %s rows to %s", row_count, table_name)


def table_row_count(conn: duckdb.DuckDBPyConnection, table_name: str) -> int:
    result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    return int(result[0])


def table_exists(conn: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    result = conn.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = ?
        """,
        [table_name],
    ).fetchone()
    return bool(result[0])
