from __future__ import annotations

import logging
import importlib.util
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
from src.data_ingestion.ingest_demographics import ingest_demographics  # noqa: E402
from src.data_ingestion.ingest_regions import ingest_regions  # noqa: E402
from src.data_ingestion.ingest_seifa import ingest_seifa  # noqa: E402
from src.transformation.build_foundation_model import build_foundation_model  # noqa: E402
from src.utils.validation import DataValidationError  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("run_sprint1")


SPRINT1_FILES = {
    "regions": "asgs_sa2_regions.csv",
    "seifa": "seifa_2021_sa2.xlsx",
    "demographics": "census_2021_sa2_demographics.csv",
}


def check_expected_files() -> None:
    missing = [
        filename
        for filename in SPRINT1_FILES.values()
        if not (RAW_DATA_DIR / filename).exists()
    ]
    if missing:
        expected = "\n".join(f"- data/raw/{filename}" for filename in SPRINT1_FILES.values())
        missing_text = "\n".join(f"- data/raw/{filename}" for filename in missing)
        raise FileNotFoundError(
            "Sprint 1 source files are missing.\n\n"
            f"Expected files:\n{expected}\n\n"
            f"Missing files:\n{missing_text}\n\n"
            "Download/prep the ABS files described in docs/data_sources.md and place them "
            "in data/raw/. If you use different filenames, update SPRINT1_FILES in "
            "scripts/run_sprint1.py."
        )


def main() -> int:
    ensure_directories()
    logger.info("Starting ClimateCover Australia Sprint 1 foundation build")
    logger.info("Raw data directory: %s", RAW_DATA_DIR)
    logger.info("DuckDB path: %s", DB_PATH)

    try:
        check_expected_files()
        ingest_regions(SPRINT1_FILES["regions"])
        ingest_seifa(SPRINT1_FILES["seifa"])
        ingest_demographics(SPRINT1_FILES["demographics"])
        build_foundation_model()
    except (FileNotFoundError, ValueError, DataValidationError) as exc:
        logger.error("%s", exc)
        return 1

    logger.info("Sprint 1 build completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
