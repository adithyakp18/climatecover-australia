# Data Dictionary

## `dim_region`

SA2 region dimension.

| Column | Type | Description |
|---|---|---|
| `sa2_code` | text | ABS Statistical Area Level 2 code |
| `sa2_name` | text | SA2 name |
| `state_name` | text | State or territory name |
| `gccsa_name` | text | Greater Capital City Statistical Area name, if available |
| `area_sq_km` | double | Area in square kilometres, if available |
| `source_file` | text | Raw source file used for ingestion |

## `fact_seifa`

SEIFA 2021 indicators at SA2 level.

| Column | Type | Description |
|---|---|---|
| `sa2_code` | text | ABS Statistical Area Level 2 code |
| `irsd_score` | double | Index of Relative Socio-economic Disadvantage score |
| `irsd_decile` | integer | IRSD decile, where lower values indicate greater disadvantage |
| `ier_score` | double | Index of Economic Resources score, if available |
| `ier_decile` | integer | IER decile, if available |
| `source_file` | text | Raw source file used for ingestion |

## `fact_demographics`

Core Census demographic and housing affordability fields at SA2 level.

| Column | Type | Description |
|---|---|---|
| `sa2_code` | text | ABS Statistical Area Level 2 code |
| `median_weekly_household_income` | double | Median weekly household income |
| `median_monthly_mortgage_repayment` | double | Median monthly mortgage repayment |
| `median_weekly_rent` | double | Median weekly rent |
| `household_count` | double | Household count |
| `source_file` | text | Raw source file used for ingestion |

## `foundation_region_profile`

Foundation analytical join used by later sprints.

| Column | Type | Description |
|---|---|---|
| `sa2_code` | text | ABS Statistical Area Level 2 code |
| `sa2_name` | text | SA2 name |
| `state_name` | text | State or territory name |
| `irsd_score` | double | IRSD score |
| `irsd_decile` | integer | IRSD decile |
| `median_weekly_household_income` | double | Median weekly household income |
| `median_monthly_mortgage_repayment` | double | Median monthly mortgage repayment |
| `median_weekly_rent` | double | Median weekly rent |
| `household_count` | double | Household count |

## `fact_climate`

BOM-derived climate indicators at SA2 level.

| Column | Type | Description |
|---|---|---|
| `sa2_code` | text | ABS Statistical Area Level 2 code |
| `annual_rainfall` | double | Annual rainfall in millimetres, or long-run annual average rainfall |
| `average_temperature` | double | Average temperature in degrees Celsius |
| `extreme_heat_days` | double | Count of days above the selected extreme heat threshold |
| `rainfall_anomaly` | double | Rainfall anomaly versus selected baseline |
| `source` | text | Dataset/source description |
| `source_file` | text | Raw source file used for ingestion |

## `fact_hazard`

Hazard exposure scores at SA2 level.

| Column | Type | Description |
|---|---|---|
| `sa2_code` | text | ABS Statistical Area Level 2 code |
| `flood_risk_score` | double | Flood exposure score from 0 to 100 |
| `bushfire_risk_score` | double | Bushfire exposure score from 0 to 100 |
| `cyclone_risk_score` | double | Cyclone exposure score from 0 to 100 |
| `storm_risk_score` | double | Storm exposure score from 0 to 100 |
| `overall_hazard_score` | double | Mean of available hazard component scores unless supplied |
| `source` | text | Dataset/source description |
| `source_file` | text | Raw source file used for ingestion |

## `foundation_region_climate`

Analytical table joining Sprint 1 foundation data to climate and hazard indicators.

| Column | Type | Description |
|---|---|---|
| `sa2_code` | text | ABS Statistical Area Level 2 code |
| `sa2_name` | text | SA2 name |
| `state_name` | text | State or territory name |
| `irsd_score` | double | IRSD score |
| `irsd_decile` | integer | IRSD decile |
| `median_weekly_household_income` | double | Median weekly household income |
| `median_monthly_mortgage_repayment` | double | Median monthly mortgage repayment |
| `median_weekly_rent` | double | Median weekly rent |
| `household_count` | double | Household count |
| `annual_rainfall` | double | Annual rainfall indicator |
| `average_temperature` | double | Average temperature indicator |
| `extreme_heat_days` | double | Extreme heat day count |
| `rainfall_anomaly` | double | Rainfall anomaly indicator |
| `flood_risk_score` | double | Flood exposure score |
| `bushfire_risk_score` | double | Bushfire exposure score |
| `cyclone_risk_score` | double | Cyclone exposure score |
| `storm_risk_score` | double | Storm exposure score |
| `overall_hazard_score` | double | Overall hazard score |

## `synthetic_insurance`

Synthetic SA2-level insurance premium estimate. This table is generated because no suitable public SA2-level Australian home premium dataset was selected for Sprint 3.

| Column | Type | Description |
|---|---|---|
| `sa2_code` | text | ABS Statistical Area Level 2 code |
| `estimated_annual_premium` | double | Estimated annual home insurance premium |
| `base_premium` | double | State-based synthetic base premium |
| `flood_loading` | double | Premium loading derived from flood risk score |
| `bushfire_loading` | double | Premium loading derived from bushfire risk score |
| `cyclone_loading` | double | Premium loading derived from cyclone risk score |
| `storm_loading` | double | Premium loading derived from storm risk score |
| `rebuild_loading` | double | Synthetic loading for rebuilding-cost pressure |
| `mitigation_discount` | double | Synthetic resilience or mitigation discount |
| `premium_source` | text | Description of source/method |
| `data_type` | text | `Synthetic` for generated estimates, `Real` only if a future public dataset is ingested |

## `fact_affordability`

Calculated insurance affordability metrics.

| Column | Type | Description |
|---|---|---|
| `sa2_code` | text | ABS Statistical Area Level 2 code |
| `median_household_income` | double | Annualised median household income |
| `estimated_annual_premium` | double | Estimated annual home insurance premium |
| `affordability_ratio` | double | Estimated annual premium divided by annual household income |
| `premium_to_income_percent` | double | Affordability ratio expressed as a percentage |
| `affordability_band` | text | Low, Moderate, High or Severe |

## `fact_property_risk`

Calculated property risk score.

| Column | Type | Description |
|---|---|---|
| `sa2_code` | text | ABS Statistical Area Level 2 code |
| `property_risk_score` | double | Weighted risk score from 0 to 100 |
| `flood_component` | double | Flood contribution to score |
| `bushfire_component` | double | Bushfire contribution to score |
| `cyclone_component` | double | Cyclone and storm contribution to score |
| `storm_component` | double | Historical hazard proxy contribution to score |
| `climate_component` | double | Climate indicator contribution to score |
| `vulnerability_component` | double | Socio-economic vulnerability contribution to score |
| `risk_band` | text | Low, Moderate, High or Severe |

## `foundation_region_risk`

Primary analytical dataset for dashboards and AI briefing components.

| Column | Type | Description |
|---|---|---|
| `sa2_code` | text | ABS Statistical Area Level 2 code |
| `sa2_name` | text | SA2 name |
| `state_name` | text | State or territory name |
| `irsd_score` | double | IRSD score |
| `irsd_decile` | integer | IRSD decile |
| `median_weekly_household_income` | double | Median weekly household income |
| `median_annual_household_income` | double | Median weekly household income annualised |
| `median_monthly_mortgage_repayment` | double | Median monthly mortgage repayment |
| `median_weekly_rent` | double | Median weekly rent |
| `household_count` | double | Household count |
| `annual_rainfall` | double | Annual rainfall indicator |
| `average_temperature` | double | Average temperature indicator |
| `extreme_heat_days` | double | Extreme heat day count |
| `rainfall_anomaly` | double | Rainfall anomaly indicator |
| `flood_risk_score` | double | Flood exposure score |
| `bushfire_risk_score` | double | Bushfire exposure score |
| `cyclone_risk_score` | double | Cyclone exposure score |
| `storm_risk_score` | double | Storm exposure score |
| `overall_hazard_score` | double | Overall hazard score |
| `estimated_annual_premium` | double | Estimated annual insurance premium |
| `affordability_ratio` | double | Premium divided by annual household income |
| `premium_to_income_percent` | double | Premium-to-income percentage |
| `affordability_band` | text | Low, Moderate, High or Severe |
| `property_risk_score` | double | Weighted property risk score |
| `risk_band` | text | Low, Moderate, High or Severe |
| `intervention_priority_score` | double | Combined property risk and affordability stress score |
