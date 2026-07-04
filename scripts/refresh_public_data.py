from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DB_PATH, ensure_directories
from scripts.prepare_real_abs_data import main as prepare_real_abs_data
from scripts.create_abs_backed_database import main as create_abs_backed_database


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("refresh_public_data")

MANIFEST_PATH = PROJECT_ROOT / "docs" / "data_refresh_manifest.json"


def database_summary() -> dict[str, object]:
    conn = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        risk_summary = conn.execute(
            """
            SELECT
                COUNT(*) AS total_regions,
                ROUND(AVG(property_risk_score), 2) AS avg_property_risk_score,
                ROUND(AVG(premium_to_income_percent), 2) AS avg_premium_to_income_percent,
                SUM(CASE WHEN affordability_band = 'Severe' THEN 1 ELSE 0 END)
                    AS severe_affordability_regions,
                SUM(CASE WHEN risk_band IN ('High', 'Severe') THEN 1 ELSE 0 END)
                    AS high_or_severe_risk_regions
            FROM foundation_region_risk
            """
        ).fetchone()
    finally:
        conn.close()

    return {
        "analytics_layers": [
            "Regional reference",
            "Socio-economic indicators",
            "Household affordability indicators",
            "Climate and hazard indicators",
            "Insurance affordability estimates",
            "Property risk and intervention priority",
        ],
        "total_regions": int(risk_summary[0] or 0),
        "avg_property_risk_score": float(risk_summary[1] or 0),
        "avg_premium_to_income_percent": float(risk_summary[2] or 0),
        "severe_affordability_regions": int(risk_summary[3] or 0),
        "high_or_severe_risk_regions": int(risk_summary[4] or 0),
    }


def write_manifest() -> dict[str, object]:
    summary = database_summary()
    manifest = {
        "last_refresh_utc": datetime.now(timezone.utc).isoformat(),
        "refresh_mode": "automated_public_data_refresh",
        "status": "success",
        "primary_table": "foundation_region_risk",
        "real_public_sources": [
            {
                "name": "ABS SEIFA 2021 SA2 workbook",
                "provider": "Australian Bureau of Statistics",
                "coverage": "National SA2",
                "fields_used": [
                    "SA2 code",
                    "SA2 name",
                    "usual resident population",
                    "IRSD score and decile",
                    "IER score and decile",
                ],
                "update_pattern": "ABS release cycle",
            }
        ],
        "derived_or_modelled_layers": [
            "Household income/rent/mortgage indicators until direct Census GCP integration is completed",
            "Climate indicators until prepared BOM SA2 climate extracts are connected",
            "Hazard indicators until Geoscience/state spatial layers are connected",
            "Insurance premium estimates because public SA2-level insurer premium data is not available",
        ],
        "database_summary": summary,
        "next_data_hardening_steps": [
            "Connect direct ABS Census GCP SA2 ingestion",
            "Connect BOM climate data ingestion",
            "Connect Geoscience Australia and state hazard layers",
            "Add commercial or partner insurance premium data if available",
        ],
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info("Wrote data refresh manifest to %s", MANIFEST_PATH)
    return manifest


def main() -> int:
    ensure_directories()
    logger.info("Starting automated public data refresh")
    prepare_real_abs_data()
    create_abs_backed_database()
    manifest = write_manifest()
    logger.info(
        "Refresh complete: %s regions, avg risk score %.2f",
        manifest["database_summary"]["total_regions"],
        manifest["database_summary"]["avg_property_risk_score"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
