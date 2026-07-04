from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.formatting import configure_page


configure_page("Methodology")

st.title("Methodology")
st.caption("How ClimateCover Australia prepares data, calculates risk and supports regional decision-making.")

with st.expander("Public Data Foundation", expanded=True):
    st.markdown(
        """
        ClimateCover uses Australian public data as the foundation for regional decision intelligence.

        - ABS ASGS regional reference data for Australian statistical geography.
        - ABS SEIFA 2021 for socio-economic advantage, disadvantage and vulnerability signals.
        - ABS Census household indicators for income, housing and household scale.
        - Prepared climate indicators aligned to Bureau of Meteorology style measures.
        - Prepared hazard indicators aligned to Geoscience Australia, data.gov.au and state open-data sources.

        The application rebuilds its DuckDB analytical layer from these inputs so dashboards,
        rankings and regional profiles refresh from the governed data layer.
        """
    )

with st.expander("Insurance Affordability Model", expanded=True):
    st.markdown(
        """
        ClimateCover estimates household insurance affordability pressure by combining
        regional hazard exposure, socio-economic vulnerability and housing cost pressure.

        The annual premium estimate is a transparent modelled indicator. It is designed
        for portfolio screening, policy discussion and resilience prioritisation.

        It considers:

        - A regional baseline insurance cost.
        - Flood, bushfire, cyclone and storm exposure.
        - Rebuild-cost pressure informed by household and housing indicators.
        - Future mitigation adjustments once resilience scenarios are added.

        Public region-level insurer quote and claims datasets are not openly available
        at national SA2 coverage. For that reason, this application presents an explainable
        affordability estimate rather than an insurer quote or actuarial price.
        """
    )

with st.expander("Risk Scoring Methodology", expanded=True):
    st.markdown(
        """
        Property risk score is a weighted, explainable 0-100 score.

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
        """
    )

with st.expander("Affordability Methodology", expanded=True):
    st.markdown(
        """
        Annual household income is calculated by converting weekly household income
        into a yearly value.

        The affordability ratio compares the estimated annual insurance premium with
        estimated annual household income.

        Bands:

        - Low: < 2%
        - Moderate: 2% to < 4%
        - High: 4% to < 8.33%
        - Severe: >= 8.33%

        The severe threshold approximates one month of annual household income.
        """
    )

with st.expander("Data Preparation Workflow"):
    st.markdown(
        """
        1. Public regional files are loaded into `data/raw`.
        2. Python ingestion scripts standardise field names, types and regional keys.
        3. Processed files are written to `data/processed`.
        4. DuckDB tables are rebuilt for regions, demographics, SEIFA, climate, hazards,
           affordability and property risk.
        5. The dashboard reads directly from the analytical DuckDB layer.
        6. A scheduled GitHub Actions workflow can rebuild the data layer monthly and redeploy the app.
        """
    )

with st.expander("Model Governance"):
    st.markdown(
        """
        ClimateCover is a decision-support analytics platform. It is intended to help
        executives, analysts and policy teams identify where deeper investigation,
        resilience investment or community support may be required.

        Important governance notes:

        - Premium estimates are not insurer quotes and must not be used for underwriting,
          pricing, financial advice or household purchase decisions.
        - Public hazard datasets vary by state, licence, update frequency and spatial precision.
        - Census income fields are from 2021 and may not reflect current household income.
        - Regional results can hide local street-level hazard variation.
        - The platform should be connected to live insurer, claims and parcel-level hazard
          data before operational pricing or portfolio action.
        """
    )
