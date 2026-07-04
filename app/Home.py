from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.formatting import configure_page, display_data_warning
from src.dashboard.queries import ensure_dashboard_data


configure_page("Home")

st.markdown(
    """
    <div class="cc-hero">
      <span class="cc-pill">Australian climate risk</span>
      <span class="cc-pill">Insurance affordability</span>
      <span class="cc-pill">Executive intelligence</span>
      <h1>ClimateCover Australia</h1>
      <h3>Insurance Affordability & Property Risk Intelligence Platform</h3>
      <p>
        An operational analytics platform for identifying Australian regions where
        climate-related property risk intersects with household insurance affordability pressure.
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.spinner("Preparing regional risk database..."):
    data_ready, data_message = ensure_dashboard_data()

if not data_ready:
    display_data_warning()
    st.caption(data_message)

st.markdown("### Business Problem")
st.markdown(
    """
    Natural hazard exposure, rebuilding costs and household income pressure are creating
    a growing insurance affordability challenge. ClimateCover gives insurers, banks,
    governments and regulators a clear regional view of communities facing combined
    physical risk and financial stress.
    """
)

st.markdown("### Solution Overview")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(
        """
        <div class="cc-card">
        <h4>Risk Intelligence</h4>
        <p class="cc-small">Combines climate, hazard, SEIFA and household indicators to produce explainable regional risk scores.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col2:
    st.markdown(
        """
        <div class="cc-card">
        <h4>Affordability Analytics</h4>
        <p class="cc-small">Measures premium-to-income pressure and highlights areas requiring affordability and resilience attention.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col3:
    st.markdown(
        """
        <div class="cc-card">
        <h4>Executive Storytelling</h4>
        <p class="cc-small">Turns regional risk metrics into decision-ready views for insurers, banks and government stakeholders.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("### Data Sources")
st.markdown(
    """
    - ABS ASGS SA2 region reference data
    - ABS SEIFA 2021
    - ABS Census 2021 household indicators
    - Prepared BOM climate indicators
    - Prepared Geoscience Australia, data.gov.au or state open-data hazard indicators
    - Synthetic insurance estimates generated from documented assumptions
    """
)

st.markdown("### Architecture Overview")
st.markdown(
    """
    Public datasets are cleaned with Python and Pandas, persisted to DuckDB,
    joined into governed analytical tables, and consumed directly by this Streamlit
    application through a curated regional risk dataset.
    """
)

st.markdown("### Navigate")
nav1, nav2, nav3, nav4 = st.columns(4)
with nav1:
    st.page_link("pages/1_Executive_Overview.py", label="Executive Overview")
with nav2:
    st.page_link("pages/2_Risk_Explorer.py", label="Australia Risk Explorer")
with nav3:
    st.page_link("pages/3_Region_Profile.py", label="Region Profile")
with nav4:
    st.page_link("pages/4_Methodology.py", label="Methodology")
