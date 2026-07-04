# ClimateCover Australia

Insurance Affordability & Property Risk Intelligence Platform

ClimateCover Australia is an insurance affordability and property risk intelligence platform. It combines Australian public data and explainable analytics to identify communities where climate-related property risk intersects with household affordability pressure.

## What It Does

ClimateCover helps insurers, banks, governments and resilience teams answer:

- Which Australian regions combine high property risk with affordability pressure?
- Where should resilience investment, mitigation funding or community support be prioritised?
- Which regional markets require deeper underwriting, lending or policy analysis?
- How can executives explain climate-related insurance pressure using a transparent data model?

## Current Data Foundation

The deployed dataset is built from an ABS-backed national regional foundation:

- Official ABS SEIFA 2021 SA2 records
- Real SA2 codes, names, states and regional population
- Real ABS IRSD and IER scores and deciles
- Modelled household, climate, hazard and insurance affordability indicators used to create a national decision-support layer

The insurance affordability layer is an explainable estimate for regional screening. It is not an insurer quote, actuarial price or financial advice.

The project uses Python, Pandas, DuckDB, Streamlit and Plotly. No Databricks dependency is required.

## Automated Data Refresh

The project includes an automated public-data refresh workflow.

Manual local refresh:

```powershell
python scripts\refresh_public_data.py
```

Stop any running local Streamlit app before running the local refresh, because DuckDB allows only one writer at a time.

GitHub Actions workflow:

```text
.github/workflows/refresh-public-data.yml
```

Schedule:

```text
Monthly, on the first day of the month
```

The workflow refreshes public source files, rebuilds the analytics database for validation, writes `docs/data_refresh_manifest.json`, and commits refreshed source/manifest files back to GitHub when changes exist.

## Data Status

The repository includes a national ABS-backed seed dataset so the Streamlit app can run locally and in Streamlit Community Cloud without manual file downloads.

Real public data:

- ABS SEIFA 2021 SA2 indexes
- ABS statistical geography fields derived from official SA2 records

Prepared Census, BOM, Geoscience Australia and state hazard extracts can be added to replace or enrich the current modelled indicators.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\create_abs_backed_database.py
streamlit run app/Home.py
```

The app also prepares the ABS-backed database automatically on startup when the DuckDB database is missing.

## Expected Output

After a successful build:

- DuckDB database: `db/climatecover.duckdb`
- Streamlit dashboard: `app/Home.py`
- Automated refresh manifest: `docs/data_refresh_manifest.json`
- Regional risk intelligence layer used by the dashboard

## Dashboard

Launch the Streamlit dashboard:

```powershell
streamlit run app/Home.py
```

The dashboard reads directly from:

```text
db/climatecover.duckdb
```

### ABS-Backed Data Build

To create a national SA2 database seeded from the official ABS SEIFA workbook:

```powershell
python scripts\prepare_real_abs_data.py
python scripts\create_abs_backed_database.py
streamlit run app/Home.py
```

This mode uses official ABS SEIFA SA2 records for region names, population and SEIFA indexes. Prepared Census, BOM, Geoscience Australia and state hazard extracts can be connected as source-specific production hardening steps.

Pages:

- Home
- Executive Overview
- Australia Risk Explorer
- Region Profile
- Methodology

## Dashboard Screenshots

Screenshots will be added after the Streamlit app is run with populated Sprint 1-3 data.

Suggested screenshots:

- `docs/images/home.png`
- `docs/images/executive_overview.png`
- `docs/images/risk_explorer.png`
- `docs/images/region_profile.png`

## Design Principles

- Prefer real Australian public data.
- Fail loudly when column mappings are ambiguous.
- Report join quality and missing SA2 rates.
- Keep methodology explainable for business stakeholders.
- Keep the local analytics layer easy to migrate later to a lakehouse architecture.
