from __future__ import annotations

import logging
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import RAW_DATA_DIR, ensure_directories
from src.data_ingestion.create_synthetic_insurance import create_synthetic_insurance
from src.transformation.build_risk_model import build_risk_model
from src.utils.db import get_connection, write_df


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("create_abs_backed_database")


STATE_BY_FIRST_DIGIT = {
    "1": "New South Wales",
    "2": "Victoria",
    "3": "Queensland",
    "4": "South Australia",
    "5": "Western Australia",
    "6": "Tasmania",
    "7": "Northern Territory",
    "8": "Australian Capital Territory",
    "9": "Other Territories",
}

STATE_CLIMATE_DEFAULTS = {
    "New South Wales": (760, 18.5, 18, 40),
    "Victoria": (650, 15.2, 12, 20),
    "Queensland": (1050, 23.8, 42, 95),
    "South Australia": (430, 17.8, 26, -35),
    "Western Australia": (620, 22.0, 34, 10),
    "Tasmania": (790, 12.1, 3, 30),
    "Northern Territory": (1180, 27.8, 75, 120),
    "Australian Capital Territory": (630, 13.6, 15, 0),
    "Other Territories": (800, 22.0, 30, 0),
}

COASTAL_TERMS = [
    "bay",
    "beach",
    "coast",
    "harbour",
    "heads",
    "island",
    "lake",
    "lakes",
    "port",
    "river",
    "waters",
]

BUSHFIRE_TERMS = [
    "mount",
    "mountain",
    "forest",
    "ranges",
    "valley",
    "hills",
    "bush",
    "rural",
]


def load_official_seifa() -> pd.DataFrame:
    path = RAW_DATA_DIR / "seifa_2021_sa2.xlsx"
    if not path.exists():
        raise FileNotFoundError(
            "Official ABS SEIFA workbook not found at data/raw/seifa_2021_sa2.xlsx.\n"
            "Run: python scripts\\prepare_real_abs_data.py"
        )
    raw = pd.read_excel(path, sheet_name="Table 1", header=5, dtype=str)
    raw.columns = [
        "sa2_code",
        "sa2_name",
        "irsd_score",
        "irsd_decile",
        "irsad_score",
        "irsad_decile",
        "ier_score",
        "ier_decile",
        "ieo_score",
        "ieo_decile",
        "usual_resident_population",
    ]
    for column in [
        "irsd_score",
        "irsd_decile",
        "ier_score",
        "ier_decile",
        "usual_resident_population",
    ]:
        raw[column] = pd.to_numeric(raw[column], errors="coerce")
    raw["sa2_code"] = raw["sa2_code"].astype(str).str.extract(r"(\d{9})", expand=False)
    raw = raw.dropna(subset=["sa2_code", "sa2_name", "irsd_score", "irsd_decile"])
    raw["state_name"] = raw["sa2_code"].str[0].map(STATE_BY_FIRST_DIGIT).fillna("Other Territories")
    return raw


def make_region(seifa_raw: pd.DataFrame) -> pd.DataFrame:
    region = seifa_raw[["sa2_code", "sa2_name", "state_name"]].copy()
    region["gccsa_name"] = pd.NA
    region["area_sq_km"] = pd.NA
    region["source_file"] = "ABS SEIFA 2021 SA2 workbook"
    return region


def make_seifa(seifa_raw: pd.DataFrame) -> pd.DataFrame:
    seifa = seifa_raw[["sa2_code", "irsd_score", "irsd_decile", "ier_score", "ier_decile"]].copy()
    seifa["source_file"] = "ABS SEIFA 2021 SA2 workbook"
    return seifa


def make_demographics_proxy(seifa_raw: pd.DataFrame) -> pd.DataFrame:
    income_percentile = seifa_raw["ier_score"].rank(pct=True).fillna(0.5)
    population = seifa_raw["usual_resident_population"].fillna(0)
    demographics = pd.DataFrame()
    demographics["sa2_code"] = seifa_raw["sa2_code"]
    demographics["median_weekly_household_income"] = (850 + income_percentile * 1550).round(0)
    demographics["median_monthly_mortgage_repayment"] = (1150 + income_percentile * 1850).round(0)
    demographics["median_weekly_rent"] = (260 + income_percentile * 430).round(0)
    demographics["household_count"] = (population / 2.55).round(0)
    demographics["source_file"] = "ABS SEIFA 2021 population plus SEIFA-derived affordability proxy"
    return demographics


def make_climate_proxy(seifa_raw: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in seifa_raw.iterrows():
        rainfall, temperature, heat_days, anomaly = STATE_CLIMATE_DEFAULTS[row["state_name"]]
        rows.append(
            [
                row["sa2_code"],
                rainfall,
                temperature,
                heat_days,
                anomaly,
                "BOM-informed state climate proxy pending SA2 climate extract",
                "ABS-backed proxy",
            ]
        )
    return pd.DataFrame(
        rows,
        columns=[
            "sa2_code",
            "annual_rainfall",
            "average_temperature",
            "extreme_heat_days",
            "rainfall_anomaly",
            "source",
            "source_file",
        ],
    )


def make_hazard_proxy(seifa_raw: pd.DataFrame) -> pd.DataFrame:
    output = []
    for _, row in seifa_raw.iterrows():
        name = str(row["sa2_name"]).lower()
        state = row["state_name"]
        coastal = any(term in name for term in COASTAL_TERMS)
        bush = any(term in name for term in BUSHFIRE_TERMS)
        flood = 25 + (25 if coastal else 0) + (15 if "river" in name or "lakes" in name else 0)
        bushfire = 25 + (35 if bush else 0)
        cyclone = 0
        if state in {"Queensland", "Northern Territory"}:
            cyclone = 35 + (30 if coastal else 0)
        elif state == "Western Australia":
            cyclone = 18 + (20 if coastal else 0)
        storm = 35 + (15 if coastal else 0)
        if state == "Tasmania":
            storm += 10
        scores = [min(flood, 100), min(bushfire, 100), min(cyclone, 100), min(storm, 100)]
        output.append([row["sa2_code"], *scores, sum(scores) / len(scores)])

    hazard = pd.DataFrame(
        output,
        columns=[
            "sa2_code",
            "flood_risk_score",
            "bushfire_risk_score",
            "cyclone_risk_score",
            "storm_risk_score",
            "overall_hazard_score",
        ],
    )
    hazard["source"] = "GA/state hazard-informed proxy pending SA2 hazard extract"
    hazard["source_file"] = "ABS-backed proxy"
    return hazard


def main() -> int:
    ensure_directories()
    seifa_raw = load_official_seifa()
    logger.info("Loaded %s official ABS SA2 SEIFA records", len(seifa_raw))

    region = make_region(seifa_raw)
    seifa = make_seifa(seifa_raw)
    demographics = make_demographics_proxy(seifa_raw)
    climate = make_climate_proxy(seifa_raw)
    hazard = make_hazard_proxy(seifa_raw)

    foundation_region_profile = (
        region[["sa2_code", "sa2_name", "state_name"]]
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
            climate[
                [
                    "sa2_code",
                    "annual_rainfall",
                    "average_temperature",
                    "extreme_heat_days",
                    "rainfall_anomaly",
                ]
            ],
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

    conn = get_connection()
    try:
        write_df(conn, region, "dim_region")
        write_df(conn, seifa, "fact_seifa")
        write_df(conn, demographics, "fact_demographics")
        write_df(conn, foundation_region_profile, "foundation_region_profile")
        write_df(conn, climate, "fact_climate")
        write_df(conn, hazard, "fact_hazard")
        write_df(conn, foundation_region_climate, "foundation_region_climate")
    finally:
        conn.close()

    create_synthetic_insurance()
    build_risk_model()
    logger.info("ABS-backed database created successfully.")
    logger.info("Created a national SA2 database seeded from official ABS SEIFA records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
