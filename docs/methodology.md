# Methodology

## Sprint 3 Overview

Sprint 3 identifies regions where climate hazard exposure overlaps with household financial vulnerability.

The layer creates:

- `synthetic_insurance`
- `fact_affordability`
- `fact_property_risk`
- `foundation_region_risk`

## Public Insurance Data Assessment

Public Australian insurance sources were reviewed before creating synthetic premiums.

Selected sources for benchmark context:

- APRA general insurance statistics
- Insurance Council of Australia catastrophe reporting
- Actuaries Institute home insurance affordability reporting
- Government disaster recovery and resilience datasets

Finding:

- Public sources provide strong aggregate evidence that premiums, reinsurance costs, natural hazard losses and affordability stress are increasing.
- No complete public SA2-level household home insurance premium dataset was selected for Sprint 3.

Decision:

- Generate a reproducible synthetic SA2-level insurance premium table using real SA2 demographic, SEIFA, climate and hazard data.

## Synthetic Premium Estimation

Estimated annual premium:

```text
estimated_annual_premium =
  base_premium
  + flood_loading
  + bushfire_loading
  + cyclone_loading
  + storm_loading
  + rebuild_loading
  - mitigation_discount
```

### Base Premium

State-based base premiums are synthetic benchmark values. They are not insurer quotes.

They reflect a simple assumption that northern and disaster-exposed jurisdictions may have higher baseline home insurance costs than lower-risk jurisdictions.

### Hazard Loadings

Hazard loadings use Sprint 2 hazard scores:

- Flood loading increases with `flood_risk_score`
- Bushfire loading increases with `bushfire_risk_score`
- Cyclone loading increases with `cyclone_risk_score`
- Storm loading increases with `storm_risk_score`

Each score is scaled from 0 to 100 and multiplied by a fixed maximum loading.

### Rebuild Loading

Rebuild loading is a synthetic proxy for construction and replacement-cost pressure.

It uses:

- Income percentile within the dataset
- Mortgage repayment percentile within the dataset

This is intentionally simple and explainable until a suitable public building replacement cost dataset is added.

### Mitigation Discount

Sprint 3 sets mitigation discount to zero by default.

Later sprints can add mitigation scenarios and resilience investment datasets.

## Affordability Methodology

Annual household income:

```text
median_annual_household_income = median_weekly_household_income * 52
```

Affordability ratio:

```text
affordability_ratio = estimated_annual_premium / median_annual_household_income
```

Premium-to-income percentage:

```text
premium_to_income_percent = affordability_ratio * 100
```

Affordability bands:

| Band | Premium-to-Income % |
|---|---:|
| Low | < 2% |
| Moderate | 2% to < 4% |
| High | 4% to < 8.33% |
| Severe | >= 8.33% |

The severe threshold approximates one month of annual household income.

## Property Risk Methodology

Property risk is scored from 0 to 100 using a transparent weighted model.

Weights:

| Component | Weight |
|---|---:|
| Flood risk | 30% |
| Bushfire risk | 25% |
| Cyclone and storm risk | 15% |
| Climate indicators | 10% |
| Historical hazard proxy | 10% |
| Socio-economic vulnerability | 10% |

Sprint 3 uses `overall_hazard_score` as the historical hazard proxy until a dedicated historical event table is introduced.

Socio-economic vulnerability is derived from SEIFA IRSD decile:

```text
vulnerability_score = (11 - irsd_decile) * 10
```

Risk bands:

| Band | Score |
|---|---:|
| Low | 0 to < 25 |
| Moderate | 25 to < 50 |
| High | 50 to < 75 |
| Severe | 75 to 100 |

## Intervention Priority

The `foundation_region_risk` table includes:

```text
intervention_priority_score =
  property_risk_score * 0.6
  + min(premium_to_income_percent / 8.33 * 100, 100) * 0.4
```

This prioritises areas with both high physical risk and high affordability stress.
