from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.formatting import configure_page, display_data_warning
from src.dashboard.queries import ensure_dashboard_data, filter_risk_data, load_foundation_risk


configure_page("Risk Explorer")

st.title("Australia Risk Explorer")
st.caption("Filter, search and compare SA2 regions by risk, affordability and premium burden.")

with st.spinner("Preparing regional risk database..."):
    data_ready, data_message = ensure_dashboard_data()

if not data_ready:
    display_data_warning()
    st.error(data_message)
    st.stop()

df = load_foundation_risk()

with st.sidebar:
    st.header("Filters")
    states = sorted(df["state_name"].dropna().unique().tolist())
    risk_bands = ["Low", "Moderate", "High", "Severe"]
    affordability_bands = ["Low", "Moderate", "High", "Severe"]
    selected_states = st.multiselect("State", states)
    selected_risk = st.multiselect("Risk Band", risk_bands)
    selected_affordability = st.multiselect("Affordability Band", affordability_bands)
    search_text = st.text_input("Search SA2")

filtered = filter_risk_data(
    df,
    selected_states,
    selected_risk,
    selected_affordability,
    search_text,
)

st.metric("Matching Regions", f"{len(filtered):,}")

display_columns = [
    "sa2_name",
    "state_name",
    "property_risk_score",
    "estimated_annual_premium",
    "affordability_ratio",
    "premium_to_income_percent",
    "risk_band",
    "affordability_band",
    "intervention_priority_score",
]

table = filtered[display_columns].copy()
table = table.rename(
    columns={
        "sa2_name": "Region",
        "state_name": "State",
        "property_risk_score": "Property Risk",
        "estimated_annual_premium": "Estimated Premium",
        "affordability_ratio": "Premium / Income Ratio",
        "premium_to_income_percent": "Premium to Income %",
        "risk_band": "Risk Band",
        "affordability_band": "Affordability Band",
        "intervention_priority_score": "Intervention Priority",
    }
)

st.dataframe(
    table.sort_values("Intervention Priority", ascending=False),
    hide_index=True,
    use_container_width=True,
    column_config={
        "Property Risk": st.column_config.ProgressColumn(
            "Property Risk",
            min_value=0,
            max_value=100,
            format="%.1f",
        ),
        "Estimated Premium": st.column_config.NumberColumn(
            "Estimated Premium",
            format="$%.0f",
        ),
        "Premium / Income Ratio": st.column_config.NumberColumn(
            "Premium / Income Ratio",
            format="%.4f",
            help="Annual insurance premium divided by annual household income.",
        ),
        "Premium to Income %": st.column_config.NumberColumn(
            "Premium to Income %",
            format="%.2f%%",
            help="Estimated annual insurance premium as a percentage of annual household income.",
        ),
        "Intervention Priority": st.column_config.ProgressColumn(
            "Intervention Priority",
            min_value=0,
            max_value=100,
            format="%.1f",
        ),
    },
)

csv = table.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered results",
    data=csv,
    file_name="climatecover_risk_explorer.csv",
    mime="text/csv",
)
