from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import DB_PATH, ensure_directories
from src.utils.db import get_connection, write_df


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("create_demo_database")


def band_from_score(score: float) -> str:
    if score < 25:
        return "Low"
    if score < 50:
        return "Moderate"
    if score < 75:
        return "High"
    return "Severe"


def affordability_band(percent: float) -> str:
    if percent < 2:
        return "Low"
    if percent < 4:
        return "Moderate"
    if percent < 8.33:
        return "High"
    return "Severe"


def main() -> int:
    ensure_directories()
    logger.info("Creating demo DuckDB database at %s", DB_PATH)

    regions = pd.DataFrame(
        [
            ["101021007", "Batemans Bay", "New South Wales", "Rest of NSW", 39.5],
            ["112011247", "Lismore", "New South Wales", "Rest of NSW", 28.1],
            ["206041122", "Melton", "Victoria", "Greater Melbourne", 135.2],
            ["212031455", "Mallacoota", "Victoria", "Rest of Vic.", 620.4],
            ["302011028", "Cairns City", "Queensland", "Rest of Qld", 11.7],
            ["315011396", "Toowoomba", "Queensland", "Rest of Qld", 105.6],
            ["401011001", "Adelaide City", "South Australia", "Greater Adelaide", 15.6],
            ["505011096", "Bunbury", "Western Australia", "Rest of WA", 65.0],
            ["601011001", "Hobart", "Tasmania", "Greater Hobart", 29.2],
            ["701011002", "Darwin City", "Northern Territory", "Greater Darwin", 21.3],
        ],
        columns=["sa2_code", "sa2_name", "state_name", "gccsa_name", "area_sq_km"],
    )
    regions["source_file"] = "demo_seed_data"

    seifa = pd.DataFrame(
        [
            ["101021007", 930, 3, 910, 3],
            ["112011247", 870, 2, 850, 2],
            ["206041122", 960, 4, 950, 4],
            ["212031455", 900, 3, 890, 3],
            ["302011028", 920, 3, 900, 3],
            ["315011396", 980, 5, 970, 5],
            ["401011001", 1010, 6, 1000, 6],
            ["505011096", 990, 5, 985, 5],
            ["601011001", 1020, 6, 1010, 6],
            ["701011002", 970, 4, 960, 4],
        ],
        columns=["sa2_code", "irsd_score", "irsd_decile", "ier_score", "ier_decile"],
    )
    seifa["source_file"] = "demo_seed_data"

    demographics = pd.DataFrame(
        [
            ["101021007", 1450, 1900, 430, 5200],
            ["112011247", 1200, 1700, 390, 9300],
            ["206041122", 1650, 2250, 460, 28400],
            ["212031455", 1150, 1500, 360, 1600],
            ["302011028", 1350, 2050, 470, 7600],
            ["315011396", 1500, 1950, 410, 18800],
            ["401011001", 1700, 2100, 500, 11200],
            ["505011096", 1550, 2000, 430, 14200],
            ["601011001", 1600, 1900, 450, 9700],
            ["701011002", 1750, 2300, 520, 6800],
        ],
        columns=[
            "sa2_code",
            "median_weekly_household_income",
            "median_monthly_mortgage_repayment",
            "median_weekly_rent",
            "household_count",
        ],
    )
    demographics["source_file"] = "demo_seed_data"

    climate = pd.DataFrame(
        [
            ["101021007", 910, 17.5, 8, 120],
            ["112011247", 1340, 20.2, 14, 310],
            ["206041122", 540, 15.6, 12, -80],
            ["212031455", 760, 14.8, 5, 95],
            ["302011028", 1980, 25.2, 38, 420],
            ["315011396", 720, 19.4, 28, -40],
            ["401011001", 530, 17.1, 18, -60],
            ["505011096", 730, 18.5, 15, 40],
            ["601011001", 620, 13.2, 2, 30],
            ["701011002", 1700, 27.6, 72, 260],
        ],
        columns=["sa2_code", "annual_rainfall", "average_temperature", "extreme_heat_days", "rainfall_anomaly"],
    )
    climate["source"] = "Demo climate indicators for local dashboard testing"
    climate["source_file"] = "demo_seed_data"

    hazard = pd.DataFrame(
        [
            ["101021007", 45, 65, 5, 45],
            ["112011247", 92, 35, 8, 60],
            ["206041122", 20, 35, 0, 30],
            ["212031455", 25, 88, 0, 55],
            ["302011028", 70, 25, 78, 75],
            ["315011396", 48, 35, 15, 55],
            ["401011001", 18, 42, 0, 35],
            ["505011096", 22, 38, 15, 48],
            ["601011001", 20, 45, 0, 50],
            ["701011002", 55, 30, 86, 82],
        ],
        columns=["sa2_code", "flood_risk_score", "bushfire_risk_score", "cyclone_risk_score", "storm_risk_score"],
    )
    hazard["overall_hazard_score"] = hazard[
        ["flood_risk_score", "bushfire_risk_score", "cyclone_risk_score", "storm_risk_score"]
    ].mean(axis=1)
    hazard["source"] = "Demo hazard scores for local dashboard testing"
    hazard["source_file"] = "demo_seed_data"

    foundation_region_profile = (
        regions[["sa2_code", "sa2_name", "state_name"]]
        .merge(seifa[["sa2_code", "irsd_score", "irsd_decile"]], on="sa2_code")
        .merge(
            demographics[
                [
                    "sa2_code",
                    "median_weekly_household_income",
                    "median_monthly_mortgage_repayment",
                    "median_weekly_rent",
                    "household_count",
                ]
            ],
            on="sa2_code",
        )
    )
    foundation_region_climate = (
        foundation_region_profile.merge(
            climate[["sa2_code", "annual_rainfall", "average_temperature", "extreme_heat_days", "rainfall_anomaly"]],
            on="sa2_code",
        )
        .merge(
            hazard[
                [
                    "sa2_code",
                    "flood_risk_score",
                    "bushfire_risk_score",
                    "cyclone_risk_score",
                    "storm_risk_score",
                    "overall_hazard_score",
                ]
            ],
            on="sa2_code",
        )
    )

    insurance = pd.DataFrame()
    insurance["sa2_code"] = foundation_region_climate["sa2_code"]
    insurance["base_premium"] = foundation_region_climate["state_name"].map(
        {
            "New South Wales": 1900,
            "Victoria": 1750,
            "Queensland": 2350,
            "South Australia": 1650,
            "Western Australia": 1850,
            "Tasmania": 1600,
            "Northern Territory": 2400,
        }
    )
    insurance["flood_loading"] = foundation_region_climate["flood_risk_score"] / 100 * 1800
    insurance["bushfire_loading"] = foundation_region_climate["bushfire_risk_score"] / 100 * 1400
    insurance["cyclone_loading"] = foundation_region_climate["cyclone_risk_score"] / 100 * 1700
    insurance["storm_loading"] = foundation_region_climate["storm_risk_score"] / 100 * 900
    insurance["rebuild_loading"] = foundation_region_climate["median_monthly_mortgage_repayment"].rank(pct=True) * 750
    insurance["mitigation_discount"] = 0.0
    insurance["estimated_annual_premium"] = (
        insurance["base_premium"]
        + insurance["flood_loading"]
        + insurance["bushfire_loading"]
        + insurance["cyclone_loading"]
        + insurance["storm_loading"]
        + insurance["rebuild_loading"]
        - insurance["mitigation_discount"]
    ).round(2)
    insurance["premium_source"] = "Demo synthetic estimate for local dashboard testing"
    insurance["data_type"] = "Demo Synthetic"
    insurance = insurance[
        [
            "sa2_code",
            "estimated_annual_premium",
            "base_premium",
            "flood_loading",
            "bushfire_loading",
            "cyclone_loading",
            "storm_loading",
            "rebuild_loading",
            "mitigation_discount",
            "premium_source",
            "data_type",
        ]
    ]

    affordability = foundation_region_climate[["sa2_code", "median_weekly_household_income"]].merge(
        insurance[["sa2_code", "estimated_annual_premium"]],
        on="sa2_code",
    )
    affordability["median_household_income"] = affordability["median_weekly_household_income"] * 52
    affordability["affordability_ratio"] = affordability["estimated_annual_premium"] / affordability["median_household_income"]
    affordability["premium_to_income_percent"] = affordability["affordability_ratio"] * 100
    affordability["affordability_band"] = affordability["premium_to_income_percent"].map(affordability_band)
    affordability = affordability[
        [
            "sa2_code",
            "median_household_income",
            "estimated_annual_premium",
            "affordability_ratio",
            "premium_to_income_percent",
            "affordability_band",
        ]
    ]

    property_risk = foundation_region_climate[["sa2_code"]].copy()
    property_risk["flood_component"] = foundation_region_climate["flood_risk_score"] * 0.30
    property_risk["bushfire_component"] = foundation_region_climate["bushfire_risk_score"] * 0.25
    property_risk["cyclone_component"] = (
        (foundation_region_climate["cyclone_risk_score"] + foundation_region_climate["storm_risk_score"]) / 2 * 0.15
    )
    property_risk["storm_component"] = foundation_region_climate["overall_hazard_score"] * 0.10
    property_risk["climate_component"] = foundation_region_climate["extreme_heat_days"].rank(pct=True) * 100 * 0.10
    property_risk["vulnerability_component"] = (11 - foundation_region_climate["irsd_decile"]) * 10 * 0.10
    property_risk["property_risk_score"] = property_risk[
        [
            "flood_component",
            "bushfire_component",
            "cyclone_component",
            "storm_component",
            "climate_component",
            "vulnerability_component",
        ]
    ].sum(axis=1)
    property_risk["risk_band"] = property_risk["property_risk_score"].map(band_from_score)
    property_risk = property_risk[
        [
            "sa2_code",
            "property_risk_score",
            "flood_component",
            "bushfire_component",
            "cyclone_component",
            "storm_component",
            "climate_component",
            "vulnerability_component",
            "risk_band",
        ]
    ]

    foundation_region_risk = (
        foundation_region_climate.merge(insurance, on="sa2_code")
        .merge(affordability[["sa2_code", "affordability_ratio", "premium_to_income_percent", "affordability_band"]], on="sa2_code")
        .merge(property_risk, on="sa2_code")
    )
    foundation_region_risk["median_annual_household_income"] = foundation_region_risk["median_weekly_household_income"] * 52
    foundation_region_risk["intervention_priority_score"] = (
        foundation_region_risk["property_risk_score"] * 0.6
        + (foundation_region_risk["premium_to_income_percent"] / 8.33 * 100).clip(upper=100) * 0.4
    )

    tables = {
        "dim_region": regions,
        "fact_seifa": seifa,
        "fact_demographics": demographics,
        "foundation_region_profile": foundation_region_profile,
        "fact_climate": climate,
        "fact_hazard": hazard,
        "foundation_region_climate": foundation_region_climate,
        "synthetic_insurance": insurance,
        "fact_affordability": affordability,
        "fact_property_risk": property_risk,
        "foundation_region_risk": foundation_region_risk,
    }

    conn = get_connection()
    try:
        for table_name, df in tables.items():
            write_df(conn, df, table_name)
    finally:
        conn.close()

    logger.info("Demo database created successfully.")
    logger.info("Open the dashboard with: streamlit run app/Home.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
