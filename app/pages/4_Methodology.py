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

with st.expander("Real Datasets", expanded=True):
    st.markdown(
        """
        - ABS ASGS SA2 region reference data
        - ABS SEIFA 2021
        - ABS Census 2021 household indicators
        - Prepared BOM climate indicators
        - Prepared Geoscience Australia, data.gov.au or state government hazard indicators
        """
    )

with st.expander("Insurance Premium Estimation"):
    st.markdown(
        """
        Annual insurance premium estimates are generated because complete SA2-level
        Australian home insurance premium data is not publicly released at the level
        required for this application.

        The estimates are reproducible, explainable and based on:

        - State-level synthetic base premium assumptions
        - Flood, bushfire, cyclone and storm hazard scores
        - Rebuild-cost pressure derived from income and mortgage repayment ranks
        - Zero mitigation discount until the scenario simulator sprint
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

with st.expander("Assumptions"):
    st.markdown(
        """
        - SA2 is the primary analytical grain.
        - Climate and hazard inputs are assumed to be prepared at SA2 level before ingestion.
        - Synthetic premiums are scenario estimates, not insurer quotes.
        - Mitigation discount is currently zero.
        - The combined hazard indicator is used as the historical hazard signal until a dedicated disaster event table is added.
        """
    )

with st.expander("Limitations"):
    st.markdown(
        """
        - Synthetic premiums must not be used for underwriting, pricing, financial advice or household decisions.
        - Public hazard datasets vary by state, licence, update frequency and spatial precision.
        - Census income fields are from 2021 and may not reflect current household income.
        - SA2-level aggregation can hide local street-level hazard variation.
        - This is a decision-support analytics application, not an actuarial pricing model.
        """
    )
