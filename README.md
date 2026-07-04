# ClimateCover Australia

Insurance Affordability & Property Risk Intelligence Platform

ClimateCover Australia is an insurance affordability and property risk intelligence platform. It combines Australian public data and explainable analytics to identify communities where climate-related property risk intersects with household affordability pressure.

Sprint 1 builds the real-data foundation at SA2 level:

- `dim_region`
- `fact_seifa`
- `fact_demographics`
- `foundation_region_profile`

Sprint 2 adds the climate and hazard layer:

- `fact_climate`
- `fact_hazard`
- `foundation_region_climate`

Sprint 3 adds insurance affordability and property risk analytics:

- `synthetic_insurance`
- `fact_affordability`
- `fact_property_risk`
- `foundation_region_risk`

The project uses Python, Pandas and DuckDB. No Databricks dependency is required.

## Sprint 1 Data Status

Sprint 1 expects user-downloaded ABS files in `data/raw/`.

Real public data:

- ABS ASGS SA2 region reference or boundary export
- ABS SEIFA 2021 SA2 indexes
- ABS Census 2021 General Community Profile or equivalent SA2 demographic proxy

Synthetic data:

- None in Sprint 1

Synthetic premium, claims and mitigation scenario data will be introduced in later sprints and clearly labelled.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\run_sprint1.py
python scripts\run_sprint2.py
python scripts\run_sprint3.py
streamlit run app/Home.py
```

The runners will fail if the required raw files are not present. That is expected. Place the files listed in `docs/data_sources.md` into `data/raw/`, update the column mappings in the ingestion scripts if needed, then rerun the command.

## Expected Output

After a successful Sprint 1 run:

- DuckDB database: `db/climatecover.duckdb`
- Tables:
  - `dim_region`
  - `fact_seifa`
  - `fact_demographics`
  - `foundation_region_profile`
  - `fact_climate`
  - `fact_hazard`
  - `foundation_region_climate`
  - `synthetic_insurance`
  - `fact_affordability`
  - `fact_property_risk`
  - `foundation_region_risk`

## Dashboard

Launch the Streamlit dashboard:

```powershell
streamlit run app/Home.py
```

The dashboard reads directly from:

```text
db/climatecover.duckdb
```

Primary dashboard table:

```text
foundation_region_risk
```

### Local Sample Mode

If you want to preview the dashboard before downloading the real ABS/BOM/hazard files, create a clearly labelled local sample database:

```powershell
python scripts\create_demo_database.py
streamlit run app/Home.py
```

Local sample mode is only for UI testing.

### ABS-Backed Production Seed

To create a national SA2 database seeded from the official ABS SEIFA workbook:

```powershell
python scripts\prepare_real_abs_data.py
python scripts\create_abs_backed_database.py
streamlit run app/Home.py
```

This mode uses official ABS SEIFA SA2 records for region names, population and SEIFA indexes. Add prepared Census, BOM, Geoscience Australia and state hazard extracts to move from production seed data to full production data coverage.

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
- Make the local prototype easy to migrate later to a lakehouse architecture.
