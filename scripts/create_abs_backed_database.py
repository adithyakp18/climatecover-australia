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


def make_demographics(seifa_raw: pd.DataFrame) -> pd.DataFrame:
    prepared_path = RAW_DATA_DIR / "census_2021_sa2_demographics.csv"
    required_columns = [
        "sa2_code",
        "median_weekly_household_income",
        "median_monthly_mortgage_repayment",
        "median_weekly_rent",
        "household_count",
    ]
    if prepared_path.exists():
        prepared = pd.read_csv(prepared_path, dtype={"sa2_code": str})
        missing = [column for column in required_columns if column not in prepared.columns]
        if missing:
            logger.warning(
                "Prepared Census file is missing columns %s. Falling back to SEIFA-derived estimates.",
                ", ".join(missing),
            )
        else:
            prepared["sa2_code"] = prepared["sa2_code"].astype(str).str.extract(r"(\d{9})", expand=False)
            for column in required_columns[1:]:
                prepared[column] = pd.to_numeric(prepared[column], errors="coerce")
            prepared = prepared.dropna(subset=["sa2_code"])
            output = seifa_raw[["sa2_code"]].merge(prepared, on="sa2_code", how="left")
            if "source_file" not in output.columns:
                output["source_file"] = "ABS Census 2021 General Community Profile SA2 DataPack"
            if "source_type" not in output.columns:
                output["source_type"] = "Real Public Data"
            output["source_file"] = output["source_file"].fillna(
                "ABS Census 2021 General Community Profile SA2 DataPack"
            )
            output["source_type"] = output["source_type"].fillna("Real Public Data")
            missing_income_rate = output["median_weekly_household_income"].isna().mean()
            if missing_income_rate < 0.25:
                logger.info("Using prepared Census demographics extract: %s", prepared_path)
                return output[
                    [
                        *required_columns,
                        "source_file",
                        "source_type",
                    ]
                ]
            logger.warning(
                "Prepared Census extract has %.1f%% missing income values after SA2 join. "
                "Falling back to SEIFA-derived estimates.",
                missing_income_rate * 100,
            )

    income_percentile = seifa_raw["ier_score"].rank(pct=True).fillna(0.5)
    population = seifa_raw["usual_resident_population"].fillna(0)
    demographics = pd.DataFrame()
    demographics["sa2_code"] = seifa_raw["sa2_code"]
    demographics["median_weekly_household_income"] = (850 + income_percentile * 1550).round(0)
    demographics["median_monthly_mortgage_repayment"] = (1150 + income_percentile * 1850).round(0)
    demographics["median_weekly_rent"] = (260 + income_percentile * 430).round(0)
    demographics["household_count"] = (population / 2.55).round(0)
    demographics["source_file"] = "ABS SEIFA 2021 population plus SEIFA-derived household estimates"
    demographics["source_type"] = "Modelled Indicator"
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
                "BOM-informed state climate estimates pending SA2 climate extract",
                "ABS-backed climate estimate",
                "Modelled Indicator",
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
            "source_type",
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
    hazard["source"] = "GA/state hazard-informed estimates pending SA2 hazard extract"
    hazard["source_file"] = "ABS-backed hazard estimate"
    hazard["source_type"] = "Modelled Indicator"
    return hazard


def make_data_lineage(demographics: pd.DataFrame) -> pd.DataFrame:
    household_status = (
        "Real Public Data"
        if "source_type" in demographics.columns
        and demographics["source_type"].eq("Real Public Data").any()
        else "Modelled Indicator"
    )
    household_source = (
        "ABS Census 2021 General Community Profile SA2 DataPack"
        if household_status == "Real Public Data"
        else "ABS SEIFA 2021 population plus SEIFA-derived household indicators"
    )
    rows = [
        {
            "layer": "Regional Reference",
            "field_group": "SA2 code, SA2 name, state, population",
            "source": "ABS SEIFA 2021 SA2 workbook",
            "source_url": "https://www.abs.gov.au/statistics/people/people-and-communities/socio-economic-indexes-areas-seifa-australia/latest-release",
            "data_status": "Real Public Data",
            "refresh_method": "Automated ABS workbook download when source is available",
            "business_use": "Regional coverage and joins",
        },
        {
            "layer": "Socio-economic Indicators",
            "field_group": "IRSD and IER scores and deciles",
            "source": "ABS SEIFA 2021 SA2 workbook",
            "source_url": "https://www.abs.gov.au/statistics/people/people-and-communities/socio-economic-indexes-areas-seifa-australia/latest-release",
            "data_status": "Real Public Data",
            "refresh_method": "Automated ABS workbook download when source is available",
            "business_use": "Community vulnerability and affordability context",
        },
        {
            "layer": "Household Indicators",
            "field_group": "Income, rent, mortgage, household count",
            "source": household_source,
            "source_url": "https://www.abs.gov.au/census/find-census-data/datapacks",
            "data_status": household_status,
            "refresh_method": "Automated ABS DataPack download with governed fallback",
            "business_use": "Insurance affordability denominator and household scale",
        },
        {
            "layer": "Climate Indicators",
            "field_group": "Rainfall, temperature, heat days, rainfall anomaly",
            "source": "BOM-style prepared indicators",
            "source_url": "https://www.bom.gov.au/climate/data/",
            "data_status": "Modelled Indicator",
            "refresh_method": "Ready for scheduled prepared-source ingestion",
            "business_use": "Climate pressure signal",
        },
        {
            "layer": "Hazard Indicators",
            "field_group": "Flood, bushfire, cyclone, storm scores",
            "source": "Geoscience Australia, data.gov.au and state open-data hazard layers",
            "source_url": "https://portal.ga.gov.au/",
            "data_status": "Modelled Indicator",
            "refresh_method": "Ready for scheduled prepared-source ingestion",
            "business_use": "Physical property risk exposure",
        },
        {
            "layer": "Insurance Affordability",
            "field_group": "Estimated annual premium and premium-to-income ratio",
            "source": "Explainable affordability model",
            "source_url": "docs/methodology.md",
            "data_status": "Calculated Metric",
            "refresh_method": "Recalculated whenever input data is rebuilt",
            "business_use": "Affordability stress screening",
        },
        {
            "layer": "Property Risk",
            "field_group": "Property risk score, risk band, intervention priority",
            "source": "Explainable weighted scoring model",
            "source_url": "docs/methodology.md",
            "data_status": "Calculated Metric",
            "refresh_method": "Recalculated whenever input data is rebuilt",
            "business_use": "Prioritisation and executive decision support",
        },
    ]
    return pd.DataFrame(rows)


def main() -> int:
    ensure_directories()
    seifa_raw = load_official_seifa()
    logger.info("Loaded %s official ABS SA2 SEIFA records", len(seifa_raw))

    region = make_region(seifa_raw)
    seifa = make_seifa(seifa_raw)
    demographics = make_demographics(seifa_raw)
    climate = make_climate_proxy(seifa_raw)
    hazard = make_hazard_proxy(seifa_raw)
    data_lineage = make_data_lineage(demographics)

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
        write_df(conn, data_lineage, "data_lineage")
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
