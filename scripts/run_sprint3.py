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

from src.config import DB_PATH, ensure_directories  # noqa: E402
from src.data_ingestion.create_synthetic_insurance import create_synthetic_insurance  # noqa: E402
from src.transformation.build_risk_model import build_risk_model  # noqa: E402
from src.utils.db import get_connection, table_exists, table_row_count  # noqa: E402
from src.utils.validation import DataValidationError  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("run_sprint3")


def check_sprint2_foundation() -> None:
    conn = get_connection()
    try:
        if not table_exists(conn, "foundation_region_climate"):
            raise RuntimeError(
                "Sprint 2 table foundation_region_climate was not found.\n\n"
                "Run Sprint 2 first:\n"
                "  python scripts\\run_sprint2.py"
            )
        row_count = table_row_count(conn, "foundation_region_climate")
        if row_count == 0:
            raise RuntimeError(
                "Sprint 2 table foundation_region_climate exists but has no records.\n\n"
                "Re-run Sprint 2 after checking climate and hazard source files."
            )
        logger.info("Found foundation_region_climate with %s rows", row_count)
    finally:
        conn.close()


def log_insurance_dataset_decision() -> None:
    logger.info(
        "Insurance data decision: no complete public SA2-level home premium dataset "
        "is bundled for Sprint 3. Generating documented synthetic premiums from "
        "available regional, SEIFA, climate and hazard inputs."
    )


def print_completion_summary() -> None:
    conn = get_connection()
    try:
        tables = [
            "synthetic_insurance",
            "fact_affordability",
            "fact_property_risk",
            "foundation_region_risk",
        ]
        logger.info("Sprint 3 completion summary")
        for table in tables:
            logger.info("%s rows: %s", table, table_row_count(conn, table))

        top_regions = conn.execute(
            """
            SELECT
                sa2_name,
                state_name,
                ROUND(estimated_annual_premium, 2) AS estimated_annual_premium,
                ROUND(premium_to_income_percent, 2) AS premium_to_income_percent,
                affordability_band,
                ROUND(property_risk_score, 2) AS property_risk_score,
                risk_band,
                ROUND(intervention_priority_score, 2) AS intervention_priority_score
            FROM foundation_region_risk
            ORDER BY intervention_priority_score DESC
            LIMIT 10
            """
        ).fetchdf()
        logger.info("Top 10 intervention priority regions:\n%s", top_regions.to_string(index=False))
    finally:
        conn.close()


def main() -> int:
    ensure_directories()
    logger.info("Starting ClimateCover Australia Sprint 3 insurance affordability and risk build")
    logger.info("DuckDB path: %s", DB_PATH)

    try:
        check_sprint2_foundation()
        log_insurance_dataset_decision()
        create_synthetic_insurance()
        build_risk_model()
        print_completion_summary()
    except (ValueError, RuntimeError, DataValidationError) as exc:
        logger.error("%s", exc)
        return 1

    logger.info("Sprint 3 build completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
