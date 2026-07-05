from __future__ import annotations

import logging
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import RAW_DATA_DIR, ensure_directories


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger("prepare_real_abs_data")

SEIFA_PAGE = (
    "https://www.abs.gov.au/statistics/people/people-and-communities/"
    "socio-economic-indexes-areas-seifa-australia/latest-release"
)
CENSUS_DATAPACK_PAGE = "https://www.abs.gov.au/census/find-census-data/datapacks"
CENSUS_SA2_GCP_URL = (
    "https://www.abs.gov.au/census/find-census-data/datapacks/download/"
    "2021_GCP_SA2_for_AUS_short-header.zip"
)

DOWNLOAD_DIR = RAW_DATA_DIR / "downloads"

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "ClimateCoverAustralia/1.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml,application/zip,*/*",
}

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


def read_url_text(url: str) -> str:
    request = Request(url, headers=HTTP_HEADERS)
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="ignore")


def find_download_url(page_url: str, filename_hint: str) -> str:
    html = read_url_text(page_url)
    links = re.findall(r'href="([^"]+)"', html)
    normalised_hint = filename_hint.lower()
    for link in links:
        if normalised_hint in link.lower():
            return urljoin(page_url, link)
    file_links = [
        urljoin(page_url, link)
        for link in links
        if any(token in link.lower() for token in [".xlsx", ".zip", "download", "media/"])
    ]
    if file_links:
        logger.info("Available download-like links on %s:", page_url)
        for index, link in enumerate(file_links[:40], start=1):
            logger.info("%s. %s", index, link)
    raise RuntimeError(
        f"Could not find a download link containing {filename_hint!r} on {page_url}"
    )


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size > 0:
        if destination.suffix.lower() != ".zip" or zipfile.is_zipfile(destination):
            logger.info("Using existing download: %s", destination)
            return
        logger.warning("Existing download is not a valid zip and will be replaced: %s", destination)
    logger.info("Downloading %s", url)
    request = Request(url, headers=HTTP_HEADERS)
    with urlopen(request, timeout=300) as response:
        destination.write_bytes(response.read())
    if destination.suffix.lower() == ".zip" and not zipfile.is_zipfile(destination):
        raise RuntimeError(
            f"Downloaded file is not a valid zip: {destination}. "
            "The ABS endpoint may have changed or returned an HTML error page."
        )
    logger.info("Saved %s", destination)


def existing_real_census_extract() -> bool:
    path = RAW_DATA_DIR / "census_2021_sa2_demographics.csv"
    if not path.exists():
        return False
    try:
        sample = pd.read_csv(path, dtype=str, nrows=25)
    except Exception:
        return False
    return "source_type" in sample.columns and sample["source_type"].eq("Real Public Data").any()


def prepare_seifa() -> None:
    try:
        url = find_download_url(SEIFA_PAGE, "statistical area level 2")
    except RuntimeError:
        html = read_url_text(SEIFA_PAGE)
        xlsx_links = re.findall(r'href="([^"]+\.xlsx[^"]*)"', html)
        if len(xlsx_links) < 2:
            raise
        url = urljoin(SEIFA_PAGE, xlsx_links[1])
    destination = RAW_DATA_DIR / "seifa_2021_sa2.xlsx"
    download_file(url, destination)


def prepare_census_sa2() -> None:
    try:
        url = find_download_url(CENSUS_DATAPACK_PAGE, "2021_GCP_SA2_for_AUS_short-header.zip")
    except RuntimeError:
        logger.info("Using known ABS Census SA2 GCP download endpoint.")
        url = CENSUS_SA2_GCP_URL
    zip_path = DOWNLOAD_DIR / "2021_GCP_SA2_for_AUS_short-header.zip"
    download_file(url, zip_path)

    extract_dir = DOWNLOAD_DIR / "2021Census_GCP_SA2_for_AUST"
    if not extract_dir.exists() or not list(extract_dir.rglob("*.csv")):
        logger.info("Extracting %s", zip_path)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_dir)

    csv_files = list(extract_dir.rglob("*.csv"))
    g02_files = [path for path in csv_files if "G02" in path.name.upper()]
    if not g02_files:
        raise RuntimeError(
            "Could not find a G02 Census table in the SA2 DataPack. "
            "The DataPack structure may have changed."
        )
    g02_path = g02_files[0]
    logger.info("Reading Census G02 table: %s", g02_path)
    g02 = pd.read_csv(g02_path, dtype=str)
    g02.columns = [column.strip() for column in g02.columns]

    required = {
        "sa2_code": ["SA2_CODE_2021", "SA2_CODE21", "region_id", "Region"],
        "median_weekly_household_income": [
            "Median_tot_hhd_inc_weekly",
            "Median_Tot_hhd_inc_weekly",
            "Median_tot_hhd_inc_wkly",
        ],
        "median_monthly_mortgage_repayment": [
            "Median_mortgage_repay_monthly",
            "Median_mortgage_repay_mthly",
        ],
        "median_weekly_rent": [
            "Median_rent_weekly",
            "Median_tot_rent_weekly",
        ],
        "average_household_size": [
            "Average_household_size",
            "Average_hh_size",
        ],
    }

    rename: dict[str, str] = {}
    for target, candidates in required.items():
        for candidate in candidates:
            if candidate in g02.columns:
                rename[candidate] = target
                break
        else:
            available = "\n".join(f"- {column}" for column in g02.columns)
            raise RuntimeError(
                f"Census G02 is missing a required column for {target}.\n"
                f"Available columns:\n{available}"
            )

    demographic = g02.rename(columns=rename)[list(required.keys())].copy()
    demographic["sa2_code"] = demographic["sa2_code"].astype(str).str.extract(r"(\d{9})", expand=False)

    population = None
    g01_files = [path for path in csv_files if "G01" in path.name.upper()]
    if g01_files:
        g01 = pd.read_csv(g01_files[0], dtype=str)
        g01.columns = [column.strip() for column in g01.columns]
        code_column = next(
            (column for column in ["SA2_CODE_2021", "SA2_CODE21", "region_id", "Region"] if column in g01.columns),
            None,
        )
        population_column = next(
            (column for column in ["Tot_P_P", "Tot_Persons", "Total_Persons"] if column in g01.columns),
            None,
        )
        if code_column and population_column:
            population = g01[[code_column, population_column]].rename(
                columns={code_column: "sa2_code", population_column: "population"}
            )
            population["sa2_code"] = population["sa2_code"].astype(str).str.extract(r"(\d{9})", expand=False)

    for column in [
        "median_weekly_household_income",
        "median_monthly_mortgage_repayment",
        "median_weekly_rent",
        "average_household_size",
    ]:
        demographic[column] = pd.to_numeric(
            demographic[column].astype(str).str.replace(",", "", regex=False),
            errors="coerce",
        )

    if population is not None:
        population["population"] = pd.to_numeric(
            population["population"].astype(str).str.replace(",", "", regex=False),
            errors="coerce",
        )
        demographic = demographic.merge(population, on="sa2_code", how="left")
        demographic["household_count"] = (
            demographic["population"] / demographic["average_household_size"]
        ).round()
    else:
        demographic["household_count"] = pd.NA

    demographic = demographic[
        [
            "sa2_code",
            "median_weekly_household_income",
            "median_monthly_mortgage_repayment",
            "median_weekly_rent",
            "household_count",
        ]
    ]
    demographic["source_file"] = "ABS Census 2021 General Community Profile SA2 DataPack"
    demographic["source_type"] = "Real Public Data"
    demographic.to_csv(RAW_DATA_DIR / "census_2021_sa2_demographics.csv", index=False)
    logger.info("Wrote prepared Census demographics extract")


def prepare_abs_proxy_files_from_seifa() -> None:
    path = RAW_DATA_DIR / "seifa_2021_sa2.xlsx"
    if not path.exists():
        raise FileNotFoundError("Cannot prepare ABS proxy files because SEIFA workbook is missing.")

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
    raw["sa2_code"] = raw["sa2_code"].astype(str).str.extract(r"(\d{9})", expand=False)
    raw = raw.dropna(subset=["sa2_code", "sa2_name"])
    raw["state_name"] = raw["sa2_code"].str[0].map(STATE_BY_FIRST_DIGIT).fillna("Other Territories")
    for column in ["ier_score", "usual_resident_population"]:
        raw[column] = pd.to_numeric(raw[column], errors="coerce")

    regions = raw[["sa2_code", "sa2_name", "state_name"]].copy()
    regions["gccsa_name"] = pd.NA
    regions["area_sq_km"] = pd.NA
    regions.to_csv(RAW_DATA_DIR / "asgs_sa2_regions.csv", index=False)
    logger.info("Wrote ABS-backed SA2 region extract")

    income_rank = raw["ier_score"].rank(pct=True).fillna(0.5)
    demographics = pd.DataFrame()
    demographics["sa2_code"] = raw["sa2_code"]
    demographics["median_weekly_household_income"] = (850 + income_rank * 1550).round(0)
    demographics["median_monthly_mortgage_repayment"] = (1150 + income_rank * 1850).round(0)
    demographics["median_weekly_rent"] = (260 + income_rank * 430).round(0)
    demographics["household_count"] = (raw["usual_resident_population"].fillna(0) / 2.55).round(0)
    demographics["source_file"] = "ABS SEIFA 2021 population plus SEIFA-derived household estimates"
    demographics["source_type"] = "Modelled Indicator"
    demographics.to_csv(RAW_DATA_DIR / "census_2021_sa2_demographics.csv", index=False)
    logger.info("Wrote SEIFA-derived Census proxy extract")


def main() -> int:
    ensure_directories()
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    prepare_seifa()
    try:
        prepare_census_sa2()
    except Exception as exc:
        logger.warning("Could not auto-prepare Census SA2 DataPack: %s", exc)
        if existing_real_census_extract():
            logger.warning("Keeping existing real Census extract instead of downgrading household data.")
        else:
            logger.warning("Writing SEIFA-derived modelled household indicators instead.")
            prepare_abs_proxy_files_from_seifa()
    logger.info("Real ABS files prepared in %s", RAW_DATA_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
