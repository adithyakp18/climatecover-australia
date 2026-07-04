from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.charts import (
    affordability_donut,
    risk_donut,
    top_affordability_bar,
    top_risk_bar,
)
from src.dashboard.formatting import (
    configure_page,
    display_data_warning,
    format_number,
    format_percent,
)
from src.dashboard.queries import (
    ensure_dashboard_data,
    load_band_distribution,
    load_kpis,
    load_top_regions,
)


configure_page("Executive Overview")

st.title("Executive Overview")
st.caption("National view of climate property risk and insurance affordability pressure.")

with st.spinner("Preparing regional risk database..."):
    data_ready, data_message = ensure_dashboard_data()

if not data_ready:
    display_data_warning()
    st.error(data_message)
    st.stop()

kpis = load_kpis()

metric_cols = st.columns(5)
metric_cols[0].metric("Total Regions", f"{int(kpis['total_regions']):,}")
metric_cols[1].metric("High Risk Regions", f"{int(kpis['high_risk_regions']):,}")
metric_cols[2].metric(
    "Severe Affordability",
    f"{int(kpis['severe_affordability_regions']):,}",
)
metric_cols[3].metric(
    "Avg Property Risk",
    format_number(kpis["avg_property_risk_score"], 1),
)
metric_cols[4].metric(
    "Avg Affordability Ratio",
    format_percent(kpis["avg_affordability_ratio"] * 100, 2),
)

st.divider()

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.plotly_chart(risk_donut(load_band_distribution("risk_band")), use_container_width=True)
with chart_col2:
    st.plotly_chart(
        affordability_donut(load_band_distribution("affordability_band")),
        use_container_width=True,
    )

bar_col1, bar_col2 = st.columns(2)
with bar_col1:
    top_risk = load_top_regions("property_risk_score", 10)
    st.plotly_chart(top_risk_bar(top_risk), use_container_width=True)
with bar_col2:
    top_stress = load_top_regions("premium_to_income_percent", 10)
    st.plotly_chart(top_affordability_bar(top_stress), use_container_width=True)

st.subheader("Executive Signal")
priority = load_top_regions("intervention_priority_score", 5)
priority_table = priority[
    [
        "sa2_name",
        "state_name",
        "property_risk_score",
        "premium_to_income_percent",
        "risk_band",
        "affordability_band",
        "intervention_priority_score",
    ]
].rename(
    columns={
        "sa2_name": "Region",
        "state_name": "State",
        "property_risk_score": "Property Risk Score",
        "premium_to_income_percent": "Premium to Income %",
        "risk_band": "Risk Band",
        "affordability_band": "Affordability Band",
        "intervention_priority_score": "Intervention Priority Score",
    }
)
st.dataframe(
    priority_table,
    hide_index=True,
    use_container_width=True,
)
