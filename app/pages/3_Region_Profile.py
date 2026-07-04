from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.charts import premium_loading_bar, region_component_bar
from src.dashboard.formatting import (
    configure_page,
    display_data_warning,
    format_currency,
    format_number,
    format_percent,
)
from src.dashboard.insights import build_region_briefing
from src.dashboard.queries import ensure_dashboard_data, load_foundation_risk, load_region_names


configure_page("Region Profile")

st.title("Region Profile")
st.caption("Detailed regional view for executive discussion and intervention planning.")

with st.spinner("Preparing regional risk database..."):
    data_ready, data_message = ensure_dashboard_data()

if not data_ready:
    display_data_warning()
    st.error(data_message)
    st.stop()

regions = load_region_names()
labels = (
    regions["sa2_name"]
    + " | "
    + regions["state_name"]
    + " | "
    + regions["sa2_code"].astype(str)
)
selected_label = st.selectbox("Select region", labels)
selected_code = selected_label.split("|")[-1].strip()

df = load_foundation_risk()
region = df[df["sa2_code"].astype(str) == selected_code].iloc[0]

st.subheader(f"{region['sa2_name']}, {region['state_name']}")

briefing_items = build_region_briefing(region)
briefing_html = "".join(f"<li>{item}</li>" for item in briefing_items)
st.markdown(
    f"""
    <div class="cc-insight">
      <h4>Generated Regional Briefing</h4>
      <ul>{briefing_html}</ul>
    </div>
    """,
    unsafe_allow_html=True,
)

st.divider()

kpi_cols = st.columns(4)
kpi_cols[0].metric("Property Risk", format_number(region["property_risk_score"], 1), region["risk_band"])
kpi_cols[1].metric("Estimated Premium", format_currency(region["estimated_annual_premium"]))
kpi_cols[2].metric("Premium to Income", format_percent(region["premium_to_income_percent"]))
kpi_cols[3].metric(
    "Intervention Priority",
    format_number(region["intervention_priority_score"], 1),
)

st.subheader("Regional Profile")
dem_col, climate_col, hazard_col = st.columns(3)

with dem_col:
    st.markdown("#### Demographics & SEIFA")
    st.write(f"SA2 code: `{region['sa2_code']}`")
    st.write(f"IRSD score: {format_number(region['irsd_score'], 1)}")
    st.write(f"IRSD decile: {format_number(region['irsd_decile'], 0)}")
    st.write(f"Median weekly household income: {format_currency(region['median_weekly_household_income'])}")
    st.write(f"Estimated annual household income: {format_currency(region['median_annual_household_income'])}")
    st.write(f"Households: {format_number(region['household_count'], 0)}")

with climate_col:
    st.markdown("#### Climate")
    st.write(f"Annual rainfall: {format_number(region['annual_rainfall'], 1)}")
    st.write(f"Average temperature: {format_number(region['average_temperature'], 1)}")
    st.write(f"Extreme heat days: {format_number(region['extreme_heat_days'], 1)}")
    st.write(f"Rainfall anomaly: {format_number(region['rainfall_anomaly'], 1)}")

with hazard_col:
    st.markdown("#### Hazard Scores")
    st.write(f"Flood: {format_number(region['flood_risk_score'], 1)}")
    st.write(f"Bushfire: {format_number(region['bushfire_risk_score'], 1)}")
    st.write(f"Cyclone: {format_number(region['cyclone_risk_score'], 1)}")
    st.write(f"Storm: {format_number(region['storm_risk_score'], 1)}")
    st.write(f"Combined hazard indicator: {format_number(region['overall_hazard_score'], 1)}")

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    st.plotly_chart(
        region_component_bar(region),
        use_container_width=True,
        config={"displayModeBar": False},
    )
with chart_col2:
    st.plotly_chart(
        premium_loading_bar(region),
        use_container_width=True,
        config={"displayModeBar": False},
    )
