# Assumptions and Limitations

## Real Public Data

The project uses real public data for:

- ABS SA2 regions
- ABS SEIFA
- ABS Census demographic and household indicators
- Prepared BOM climate indicators
- Prepared Geoscience Australia, data.gov.au or state hazard indicators

## Synthetic Data

Sprint 3 generates synthetic insurance premiums because no complete public SA2-level home insurance premium dataset was selected.

Synthetic tables:

- `synthetic_insurance`

Synthetic fields:

- Estimated annual premium
- Base premium
- Hazard loadings
- Rebuild loading
- Mitigation discount

## Calculated Metrics

Calculated tables:

- `fact_affordability`
- `fact_property_risk`
- `foundation_region_risk`

Calculated metrics:

- Affordability ratio
- Premium-to-income percentage
- Affordability band
- Property risk score
- Risk band
- Intervention priority score

## Key Assumptions

- SA2 is a suitable analytical grain for portfolio-level consulting analysis.
- Median weekly household income is a reasonable public proxy for household ability to pay.
- Hazard scores are scaled from 0 to 100.
- Public affordability reporting supports using one month of income, or 8.33% of annual income, as a severe stress threshold.
- Synthetic premium loadings are scenario assumptions, not market quotes.
- Mitigation discount is zero until a dedicated mitigation scenario layer is added.

## Limitations

- Synthetic premiums must not be used for underwriting, pricing, financial advice or household purchasing decisions.
- Public hazard datasets vary by state, licence, update frequency and spatial precision.
- Prepared SA2-level climate and hazard extracts may hide local variation within large SA2s.
- Census income fields are from 2021 and may not reflect current household income.
- Property replacement cost is approximated; a real rebuild-cost dataset should be added in a future sprint.
- Historical hazard is proxied by `overall_hazard_score` until a dedicated disaster event history table is added.

## Intended Use

ClimateCover Australia is a decision-support analytics application for:

- Regional risk prioritisation
- Insurance affordability analytics
- Climate resilience planning
- Executive dashboards
- AI-generated briefing summaries

It is not an actuarial pricing model.
