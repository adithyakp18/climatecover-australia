# ClimateCover Australia - Project Summary

## Product Description

ClimateCover Australia is an insurance affordability and property risk intelligence platform for Australian regions. It helps identify where climate-related property exposure overlaps with household affordability pressure, so insurers, banks, governments and resilience planners can prioritise intervention.

The application reads from a local DuckDB analytical database and presents results through a Streamlit dashboard.

## Current Application Status

- Application: Streamlit multi-page dashboard
- Database: DuckDB
- Primary analytical table: `foundation_region_risk`
- Current regional coverage: 2,353 SA2 regions
- Current app URL on this machine: `http://localhost:8505`
- Deployment command: `streamlit run app/Home.py`

## Current Dashboard Metrics

| Metric | Value |
|---|---:|
| Total SA2 regions | 2,353 |
| Average property risk score | 29.88 |
| Average premium-to-income percentage | 4.69% |
| Severe affordability regions | 71 |
| High or severe property risk regions | 18 |

## Highest Priority Regions In Current Build

| Region | State | Property Risk | Risk Band | Premium / Income | Affordability Band | Priority Score |
|---|---|---:|---|---:|---|---:|
| Victoria River | Northern Territory | 59.50 | High | 12.31% | Severe | 75.70 |
| Driver | Northern Territory | 57.50 | High | 9.33% | Severe | 74.50 |
| Riverview | Queensland | 56.17 | High | 11.74% | Severe | 73.70 |
| Lakes Creek | Queensland | 55.17 | High | 10.07% | Severe | 73.10 |
| Tiwi Islands | Northern Territory | 54.63 | High | 11.71% | Severe | 72.78 |
| Southern Moreton Bay Islands | Queensland | 51.29 | High | 10.73% | Severe | 70.78 |
| Deception Bay | Queensland | 51.29 | High | 8.97% | Severe | 70.78 |
| Torres Strait Islands | Queensland | 51.29 | High | 11.53% | Severe | 70.78 |
| Palm Island | Queensland | 51.29 | High | 11.56% | Severe | 70.78 |
| Southport - North | Queensland | 50.29 | High | 11.07% | Severe | 70.18 |

## What Was Built

### 1. Data Foundation Layer

Tables:

- `dim_region`
- `fact_seifa`
- `fact_demographics`
- `foundation_region_profile`

Purpose:

- Create a standard SA2-level regional spine.
- Store region names, state names, SEIFA scores and household indicators.

### 2. Climate And Hazard Layer

Tables:

- `fact_climate`
- `fact_hazard`
- `foundation_region_climate`

Purpose:

- Add climate and hazard indicators to each SA2 region.
- Standardise rainfall, temperature, heat, flood, bushfire, cyclone and storm features.

### 3. Insurance Affordability And Property Risk Layer

Tables:

- `synthetic_insurance`
- `fact_affordability`
- `fact_property_risk`
- `foundation_region_risk`

Purpose:

- Estimate annual home insurance burden.
- Calculate affordability bands.
- Calculate property risk scores.
- Build the final table consumed by the dashboard.

### 4. Dashboard Layer

Streamlit pages:

- Home
- Executive Overview
- Australia Risk Explorer
- Region Profile
- Methodology

Supporting modules:

- `src/dashboard/queries.py`
- `src/dashboard/charts.py`
- `src/dashboard/formatting.py`

## Datasets Used

### Real Public Data Currently Used

| Dataset | Source | Use |
|---|---|---|
| ABS SEIFA 2021 SA2 workbook | Australian Bureau of Statistics | SA2 codes, SA2 names, SEIFA scores, SEIFA deciles, usual resident population |
| ABS Census DataPacks page | Australian Bureau of Statistics | Documented target source for full Census household fields |

Downloaded file:

- `data/raw/seifa_2021_sa2.xlsx`

Generated raw extracts:

- `data/raw/asgs_sa2_regions.csv`
- `data/raw/census_2021_sa2_demographics.csv`

### Target Real Datasets For Full Production Coverage

These are the intended source categories for replacing current derived fields:

- ABS Census 2021 SA2 General Community Profile
- BOM climate observations or prepared SA2 climate indicators
- Geoscience Australia hazard/exposure datasets
- State open data flood, bushfire and planning layers
- APRA, ICA and Actuaries Institute publications for insurance benchmark context

## Backend Data Model

The dashboard reads from:

```text
db/climatecover.duckdb
```

Current database tables:

```text
dim_region
fact_seifa
fact_demographics
foundation_region_profile
fact_climate
fact_hazard
foundation_region_climate
synthetic_insurance
fact_affordability
fact_property_risk
foundation_region_risk
```

Primary dashboard table:

```text
foundation_region_risk
```

## How The App Works

1. ABS SEIFA data is downloaded and read from Excel.
2. SA2 records are standardised into region and SEIFA tables.
3. Household indicators are prepared at SA2 level.
4. Climate and hazard indicators are attached to each SA2.
5. Insurance premium estimates are generated from hazard, state and rebuilding pressure assumptions.
6. Affordability is calculated as annual premium divided by annual household income.
7. Property risk is calculated using an explainable weighted score.
8. The final dataset is stored in DuckDB.
9. Streamlit queries DuckDB directly and renders KPIs, charts, filters and region profiles.

## Risk Scoring Methodology

Property risk score is calculated on a 0-100 scale.

| Component | Weight |
|---|---:|
| Flood risk | 30% |
| Bushfire risk | 25% |
| Cyclone and storm risk | 15% |
| Climate indicators | 10% |
| Historical hazard indicator | 10% |
| Socio-economic vulnerability | 10% |

Risk bands:

- Low: 0 to < 25
- Moderate: 25 to < 50
- High: 50 to < 75
- Severe: 75 to 100

## Affordability Methodology

Annual household income:

```text
median_weekly_household_income * 52
```

Affordability ratio:

```text
estimated_annual_premium / median_annual_household_income
```

Affordability bands:

- Low: < 2%
- Moderate: 2% to < 4%
- High: 4% to < 8.33%
- Severe: >= 8.33%

The severe threshold approximates one month of annual household income.

## Hardcoding And Estimates Used

The current build contains several deliberate assumptions so the product can run end-to-end before every government source is fully integrated.

### State Base Premiums

The insurance model uses state-level base premiums in `src/data_ingestion/create_synthetic_insurance.py`.

Examples:

- NSW: 1,900
- VIC: 1,750
- QLD: 2,350
- NT: 2,400

These are not insurer quotes. They are estimated baseline values used for regional analytics.

### Hazard Loadings

Maximum loading assumptions:

- Flood loading: 1,800
- Bushfire loading: 1,400
- Cyclone loading: 1,700
- Storm loading: 900
- Rebuild loading: 750

The formula is:

```text
loading = risk_score / 100 * maximum_loading
```

### Rebuild Loading

Rebuild loading is calculated from income and mortgage repayment ranks. This is a replacement-cost pressure indicator until a more direct construction/rebuild-cost dataset is added.

### Climate And Hazard Seed Values

The ABS-backed production seed uses state-level climate defaults and name-based hazard indicators. This gives every SA2 a complete operating record while final BOM/Geoscience/state hazard extracts are being connected.

Examples:

- Northern Territory and Queensland receive higher cyclone baseline exposure.
- Coastal terms such as bay, beach, island, river and port increase flood/storm exposure.
- Terms such as mountain, forest, ranges, valley and hills increase bushfire exposure.

These rules are transparent and replaceable.

## Production Readiness Notes

The app has been made deployment-ready in the following ways:

- Streamlit multipage app structure is complete.
- Dashboard reads from DuckDB through reusable query functions.
- App can bootstrap the database if `foundation_region_risk` is missing.
- Data processing scripts are reusable and documented.
- Key tables and metrics are validated during pipeline runs.
- Product-facing language has been changed from project/prototype wording to operational platform wording.

For a production-grade deployment, the next data-hardening steps are:

1. Replace derived household indicators with full ABS Census GCP SA2 fields.
2. Replace state climate defaults with prepared BOM SA2 climate features.
3. Replace name-based hazard indicators with Geoscience Australia and state spatial hazard layers.
4. Add source lineage columns to every feature table.
5. Add automated tests for all scoring functions.
6. Deploy through Streamlit Community Cloud, Render, Azure App Service, or similar.

## Local Run Commands

```powershell
cd C:\Users\Adith\Documents\Codex\2026-07-04\use-github-to-review-recent-notebook
pip install -r requirements.txt
python scripts\prepare_real_abs_data.py
python scripts\create_abs_backed_database.py
streamlit run app/Home.py
```

## LinkedIn Positioning

Suggested LinkedIn post:

```text
I built ClimateCover Australia, an insurance affordability and property risk intelligence platform for Australian regions.

The application combines ABS regional data, SEIFA socio-economic indicators, climate and hazard features, insurance burden estimation, and explainable risk scoring to identify where climate-related property risk intersects with household affordability pressure.

Current build:
- 2,353 Australian SA2 regions
- DuckDB analytical backend
- Streamlit executive dashboard
- Risk and affordability scoring
- Regional explorer and SA2 profile views
- Reproducible Python data pipeline

The platform is designed for use cases across insurance, banking, government resilience planning and climate risk analytics.
```

## Screenshot Status

Dashboard screenshot files were attempted through browser automation. Headless capture returned Streamlit loading screens rather than the rendered dashboard. A full visible-screen capture requires explicit approval because it can include unrelated on-screen content.

Recommended LinkedIn approach:

- Use the deployed public app link.
- Add screenshots manually from the browser after opening only the dashboard window.
