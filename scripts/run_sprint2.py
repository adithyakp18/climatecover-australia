from __future__ import annotations

import importlib.util
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

REQUIRED_PACKAGES = ["pandas", "duckdb", "openpyxl"]


def check_dependencies() -> None:
    missing = [
        package
        for package in REQUIRED_PACKAGES
        if importlib.util.find_spec(package) is None
    ]
    if missing:
        message = (
            "Missing required Python packages: "
            f"{', '.join(missing)}\n\n"
            "Install dependencies first:\n"
            "  pip install -r requirements.txt"
        )
        print(message, file=sys.stderr)
        raise SystemExit(1)


check_dependencies()

from src.config import DB_PATH, RAW_DATA_DIR, ensure_directories  # noqa: E402
from src.data_ingestion.ingest_climate import ingest_climate  # noqa: E402
from src.data_ingestion.ingest_hazard import ingest_hazard  # noqa: E402
from src.transformation.build_climate_model import build_climate_model  # noqa: E402
from src.utils.db import get_connection, table_exists, table_row_count  # noqa: E402
from src.utils.validation import DataValidationError  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("run_sprint2")


SPRINT2_FILES = {
    "climate": "bom_sa2_climate.csv",
    "hazard": "hazard_sa2_scores.csv",
}


def check_sprint1_foundation() -> None:
    conn = get_connection()
    try:
        if not table_exists(conn, "foundation_region_profile"):
            raise RuntimeError(
                "Sprint 1 table foundation_region_profile was not found.\n\n"
                "Run Sprint 1 first:\n"
                "  python scripts\\run_sprint1.py"
            )
        row_count = table_row_count(conn, "foundation_region_profile")
        if row_count == 0:
            raise RuntimeError(
                "Sprint 1 table foundation_region_profile exists but has no records.\n\n"
                "Re-run Sprint 1 after checking the ABS source files."
            )
        logger.info("Found foundation_region_profile with %s rows", row_count)
    finally:
        conn.close()


def check_expected_files() -> None:
    missing = [
        filename
        for filename in SPRINT2_FILES.values()
        if not (RAW_DATA_DIR / filename).exists()
    ]
    if missing:
        expected = "\n".join(f"- data/raw/{filename}" for filename in SPRINT2_FILES.values())
        missing_text = "\n".join(f"- data/raw/{filename}" for filename in missing)
        raise FileNotFoundError(
            "Sprint 2 source files are missing.\n\n"
            f"Expected files:\n{expected}\n\n"
            f"Missing files:\n{missing_text}\n\n"
            "Prepare the SA2-level climate and hazard files described in docs/data_sources.md "
            "and place them in data/raw/. If you use different filenames, update "
            "SPRINT2_FILES in scripts/run_sprint2.py."
        )


def print_completion_summary() -> None:
    conn = get_connection()
    try:
        tables = [
            "fact_climate",
            "fact_hazard",
            "foundation_region_climate",
        ]
        logger.info("Sprint 2 completion summary")
        for table in tables:
            logger.info("%s rows: %s", table, table_row_count(conn, table))
    finally:
        conn.close()


def main() -> int:
    ensure_directories()
    logger.info("Starting ClimateCover Australia Sprint 2 climate and hazard build")
    logger.info("Raw data directory: %s", RAW_DATA_DIR)
    logger.info("DuckDB path: %s", DB_PATH)

    try:
        check_sprint1_foundation()
        check_expected_files()
        ingest_climate(SPRINT2_FILES["climate"])
        ingest_hazard(SPRINT2_FILES["hazard"])
        build_climate_model()
        print_completion_summary()
    except (FileNotFoundError, ValueError, RuntimeError, DataValidationError) as exc:
        logger.error("%s", exc)
        return 1

    logger.info("Sprint 2 build completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
