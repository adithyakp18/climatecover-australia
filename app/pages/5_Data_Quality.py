from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.formatting import configure_page, display_data_warning
from src.dashboard.queries import (
    ensure_dashboard_data,
    load_data_lineage,
    load_data_manifest,
    load_data_quality_checks,
)


configure_page("Data Quality")

st.title("Data Quality")
st.caption("Source coverage, refresh status and validation checks for the regional risk intelligence layer.")

with st.spinner("Preparing regional risk database..."):
    data_ready, data_message = ensure_dashboard_data()

if not data_ready:
    display_data_warning()
    st.error(data_message)
    st.stop()

manifest = load_data_manifest()
summary = manifest.get("database_summary", {})

status_cols = st.columns(4)
status_cols[0].metric("Regional Coverage", f"{int(summary.get('total_regions', 0) or 0):,}")
status_cols[1].metric(
    "High or Severe Risk",
    f"{int(summary.get('high_or_severe_risk_regions', 0) or 0):,}",
)
status_cols[2].metric(
    "Severe Affordability",
    f"{int(summary.get('severe_affordability_regions', 0) or 0):,}",
)
status_cols[3].metric("Refresh Status", str(manifest.get("status", "Ready")).title())

st.markdown(
    f"""
    <div class="cc-status-strip">
      <div class="cc-status-item"><span>Last refresh</span><strong>{manifest.get("last_refresh_utc", "Not available")}</strong></div>
      <div class="cc-status-item"><span>Refresh mode</span><strong>{str(manifest.get("refresh_mode", "Local build")).replace("_", " ").title()}</strong></div>
      <div class="cc-status-item"><span>Automation</span><strong>Monthly GitHub Actions rebuild</strong></div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Source Coverage")
lineage = load_data_lineage()
if lineage.empty:
    st.info("Source catalog is not available yet.")
else:
    st.dataframe(
        lineage.rename(
            columns={
                "layer": "Layer",
                "field_group": "Fields",
                "source": "Source",
                "source_url": "Source URL",
                "data_status": "Data Status",
                "refresh_method": "Refresh Method",
                "business_use": "Business Use",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

st.subheader("Validation Checks")
quality = load_data_quality_checks()
st.dataframe(
    quality,
    hide_index=True,
    use_container_width=True,
)

with st.expander("How to read this page", expanded=False):
    st.markdown(
        """
        - **Real Public Data** means the field is loaded from an Australian public dataset.
        - **Modelled Indicator** means the field is generated from documented logic until a prepared public extract is connected.
        - **Calculated Metric** means the field is a transparent formula or score derived from source indicators.
        - **Pass** means the check is inside the expected dashboard operating range.
        - **Review** means the data is still usable for analysis, but the source or metric needs attention before production use.
        """
    )
