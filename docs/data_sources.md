# Data Sources

Sprint 1 uses real Australian public data where possible. Download the files manually and place them in `data/raw/`.

The ingestion scripts are intentionally robust but conservative. If ABS column names differ from the examples below, update the `COLUMN_MAPPING` section near the top of the relevant ingestion script.

## 1. ABS ASGS SA2 Region Reference

Purpose: Build `dim_region`.

Preferred sources:

- ABS Australian Statistical Geography Standard (ASGS) Edition 3 correspondences and digital boundaries
- ABS Data by Region / ASGS structure files

Useful URL:

- https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3

Place one of these in `data/raw/`:

- CSV or XLSX containing SA2 code, SA2 name and state name
- Shapefile/GeoPackage is not required for Sprint 1 unless exported to CSV first

Suggested filename:

- `asgs_sa2_regions.csv`
- or `asgs_sa2_regions.xlsx`

Required fields, with flexible names:

- SA2 code
- SA2 name
- State name

Optional fields:

- GCCSA name
- Area square kilometres

## 2. ABS SEIFA 2021 SA2 Indexes

Purpose: Build `fact_seifa`.

Useful URL:

- https://www.abs.gov.au/statistics/people/people-and-communities/socio-economic-indexes-areas-seifa-australia/latest-release

Download:

- `Statistical Area Level 2, Indexes, SEIFA 2021.xlsx`

Place in `data/raw/`.

Suggested filename:

- `seifa_2021_sa2.xlsx`

Required fields:

- SA2 code
- IRSD score
- IRSD decile

Optional fields:

- IER score
- IER decile

## 3. ABS Census 2021 Demographic Proxy

Purpose: Build `fact_demographics`.

Useful URL:

- https://www.abs.gov.au/census/find-census-data/datapacks
- Direct SA2 General Community Profile DataPack endpoint used by the automated refresh:
  https://www.abs.gov.au/census/find-census-data/datapacks/download/2021_GCP_SA2_for_AUS_short-header.zip

Download one of:

- 2021 General Community Profile DataPack for Australia
- 2021 General Community Profile DataPack for your selected state
- A smaller exported ABS table containing SA2-level income, rent, mortgage and household count fields

Place a prepared CSV/XLSX extract in `data/raw/`.

Suggested filename:

- `census_2021_sa2_demographics.csv`
- or `census_2021_sa2_demographics.xlsx`

Required fields:

- SA2 code
- Median weekly household income
- Median monthly mortgage repayment
- Median weekly rent
- Household count

If using the full Census DataPack, create a small extract first with these fields. Sprint 1 deliberately avoids guessing across hundreds of Census columns because silent mis-mapping would damage trust in the project.

The automated ABS-backed refresh first attempts to download the official SA2 General Community Profile DataPack and extract the required household fields. If the public ABS page or DataPack structure changes, the pipeline falls back to a clearly tagged modelled household indicator layer so the deployed dashboard remains available.

## Source Transparency

Each table stores `source_file` so downstream dashboards can show lineage and distinguish real from synthetic data in later sprints.

## 4. BOM Climate Indicators by SA2

Purpose: Build `fact_climate`.

Primary source:

- Bureau of Meteorology Climate Data Online: https://www.bom.gov.au/climate/data/

Recommended source preparation:

1. Download rainfall and temperature observations from BOM Climate Data Online.
2. Aggregate observations to annual or long-run climate indicators.
3. Assign each station or gridded extract to the nearest SA2, or prepare a state/region extract and map it to SA2 using ABS boundaries.
4. Save a prepared SA2-level file in `data/raw/`.

Suggested filename:

- `bom_sa2_climate.csv`

Required fields:

- SA2 code
- Annual rainfall
- Average temperature
- Extreme heat days
- Rainfall anomaly

Accepted file types:

- CSV
- XLSX
- Parquet

Licence:

- BOM data is Australian Government public data. Check the specific dataset page for licence and attribution requirements before publication.

Update frequency:

- BOM observations update frequently. For this portfolio project, annual or long-run aggregates are recommended.

Assumptions and limitations:

- Sprint 2 expects a prepared SA2-level extract.
- Station-to-SA2 assignment can introduce approximation error, especially in large regional SA2s.
- Rainfall anomaly methodology must be documented in the prepared extract notes.

## 5. Hazard Risk Indicators by SA2

Purpose: Build `fact_hazard`.

Primary sources:

- Geoscience Australia Data Discovery Portal: https://portal.ga.gov.au/
- data.gov.au: https://www.data.gov.au/
- Australian Flood Risk Information Portal: https://www.ga.gov.au/scientific-topics/community-safety/flood/afrip
- State open data portals, such as:
  - Queensland Open Data: https://www.data.qld.gov.au/
  - NSW Spatial Services / SEED: https://datasets.seed.nsw.gov.au/
  - Data Victoria: https://www.data.vic.gov.au/

Recommended source preparation:

1. Download relevant flood, bushfire, cyclone and storm layers.
2. Convert spatial exposure to SA2-level scores from 0 to 100.
3. Save a prepared SA2-level file in `data/raw/`.

Suggested filename:

- `hazard_sa2_scores.csv`

Required fields:

- SA2 code
- Flood risk score
- Bushfire risk score
- Cyclone risk score
- Storm risk score

Optional fields:

- Overall hazard score
- Source

Accepted file types:

- CSV
- XLSX
- Parquet

Licence:

- Varies by source. Check each state or Australian Government open-data page. Most public-sector sources use Creative Commons-style licences, but this must be confirmed per dataset.

Update frequency:

- Varies by dataset. State planning layers may update periodically; disaster and climate layers may update annually or after major events.

Assumptions and limitations:

- Sprint 2 expects a prepared SA2-level scoring extract.
- Scores must be explainable and reproducible from public source layers.
- If `overall_hazard_score` is not supplied, the pipeline calculates it as the mean of available hazard component scores.

## 6. Insurance Affordability and Claims Benchmarks

Purpose: Inform `synthetic_insurance`, `fact_affordability`, `fact_property_risk`, and `foundation_region_risk`.

Dataset scan outcome:

- No suitable public SA2-level or address-level Australian home insurance premium dataset was identified for Sprint 3.
- APRA, Insurance Council of Australia and Actuaries Institute publications provide useful aggregate benchmarks and methodology context, but do not provide complete SA2-level premium or claims data suitable for direct ingestion into this local prototype.
- Sprint 3 therefore generates a transparent synthetic SA2-level insurance premium table using real demographic, SEIFA, climate and hazard inputs from previous sprints.

Public sources reviewed:

| Dataset / Source | Source URL | Coverage | Licence | Update Frequency | Limitations | Why Selected |
|---|---|---|---|---|---|---|
| APRA general insurance statistics | https://www.apra.gov.au/general-insurance-statistics | Australian general insurance industry statistics | APRA website terms and Australian Government information policy apply; confirm before reuse | Quarterly and annual statistical releases | Not SA2-level household premium data | Authoritative prudential and industry benchmark source |
| Insurance Council of Australia catastrophe reporting and industry data | https://insurancecouncil.com.au/ | Australian insurance industry catastrophe and event commentary | Check ICA publication terms for each report | Event-driven and periodic reports | Does not provide a complete SA2-level household premium table | Useful for explaining catastrophe-driven premium pressure |
| Actuaries Institute home insurance affordability reporting | https://www.actuaries.asn.au/ | National affordability stress findings and methodology commentary | Check report licence/terms before reuse | Periodic research reports | Public reporting is not a full regional premium dataset | Supports affordability stress threshold design |
| Government disaster recovery datasets | https://www.data.gov.au/ and state disaster portals | Disaster declarations, recovery grants, event impacts | Varies by dataset, often Creative Commons-style public-sector licences | Event-driven | Not direct insurance premium or claims data | Candidate future enhancement for historical hazard and recovery-cost features |
| Public property valuation/building cost datasets | State land/property portals and construction cost reports | Fragmented property and rebuilding proxies | Varies by source | Varies | No nationally consistent SA2-level replacement cost table selected for Sprint 3 | Candidate future enhancement for replacing synthetic rebuild loading |

Primary affordability benchmark:

- A household is considered severely stressed when basic insurance costs approach or exceed one month of gross household income, equivalent to 8.33% of annual income. This threshold is aligned with public reporting on Actuaries Institute affordability stress methodology.

Synthetic dataset generated:

- `synthetic_insurance`

Fields:

- SA2 code
- Estimated annual premium
- Base premium
- Flood loading
- Bushfire loading
- Cyclone loading
- Storm loading
- Rebuild loading
- Mitigation discount
- Premium source
- Data type

Licence:

- Synthetic output generated by this project. Underlying inputs retain their original source licences.

Update frequency:

- Re-run whenever the foundation climate/hazard data is updated.

Assumptions and limitations:

- Premiums are not real insurer quotes.
- Estimates are designed for regional analytics, scenario testing and intervention prioritisation.
- Do not use the synthetic premiums for underwriting, pricing, financial advice or household decision-making.

## 7. ABS-Backed Production Seed Dataset

Purpose: Create a national SA2-level operating dataset seeded from official ABS SEIFA records.

Command:

```powershell
python scripts\prepare_real_abs_data.py
python scripts\create_abs_backed_database.py
```

Real public data used:

- ABS SEIFA 2021 Statistical Area Level 2 workbook
- Real SA2 codes
- Real SA2 names
- Real usual resident population from SEIFA workbook
- Real IRSD and IER scores/deciles

Derived fields requiring source replacement for production deployment:

- Median weekly household income
- Median monthly mortgage repayment
- Median weekly rent
- Climate indicators
- Hazard scores
- Insurance premiums

Why this exists:

- It gives the dashboard a national real ABS SA2 foundation immediately.
- It creates a working national operating table while prepared Census/BOM/hazard extracts are connected.
- It clearly separates official ABS fields from derived and estimated fields.

Limitations:

- Full deployment should replace derived fields with prepared Census, BOM, Geoscience Australia and state hazard extracts.

## 8. Automated Refresh Workflow

The repository includes a scheduled GitHub Actions workflow:

```text
.github/workflows/refresh-public-data.yml
```

It runs:

```text
python scripts/refresh_public_data.py
```

Current automated refresh scope:

- Refresh ABS SEIFA workbook when the public ABS page exposes a matching download.
- Recreate SA2 region and household seed extracts.
- Rebuild the DuckDB analytics database for validation.
- Write `docs/data_refresh_manifest.json`.
- Commit changed public-data seed files and manifest outputs.

Current non-automated layers:

- Direct ABS Census GCP SA2 ingestion
- BOM climate API/download ingestion
- Geoscience Australia/state geospatial hazard joins
- Real SA2-level insurer premium data

These are structured as future hardening steps because their source formats, licensing, update cadence and spatial joins need source-specific handling.
