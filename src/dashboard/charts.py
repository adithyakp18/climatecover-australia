from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.formatting import AFFORDABILITY_COLORS, RISK_COLORS, band_order


def donut_chart(df: pd.DataFrame, title: str, color_map: dict[str, str]) -> go.Figure:
    ordered = df.copy()
    ordered["band"] = pd.Categorical(ordered["band"], categories=band_order(), ordered=True)
    ordered = ordered.sort_values("band")
    fig = px.pie(
        ordered,
        names="band",
        values="region_count",
        hole=0.58,
        color="band",
        color_discrete_map=color_map,
    )
    fig.update_layout(
        title=title,
        margin=dict(l=10, r=10, t=48, b=10),
        legend_title_text="Band",
        height=360,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    return fig


def risk_donut(df: pd.DataFrame) -> go.Figure:
    return donut_chart(df, "Risk Band Distribution", RISK_COLORS)


def affordability_donut(df: pd.DataFrame) -> go.Figure:
    return donut_chart(df, "Affordability Band Distribution", AFFORDABILITY_COLORS)


def horizontal_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str,
    label: str,
) -> go.Figure:
    chart_data = df.sort_values(x, ascending=True).copy()
    fig = px.bar(
        chart_data,
        x=x,
        y=y,
        orientation="h",
        text=x,
        color_discrete_sequence=[color],
        labels={x: label, y: "Region"},
    )
    fig.update_layout(
        title=title,
        margin=dict(l=10, r=10, t=48, b=10),
        height=420,
        yaxis_title="",
        xaxis_title=label,
        showlegend=False,
    )
    fig.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
    return fig


def top_risk_bar(df: pd.DataFrame) -> go.Figure:
    return horizontal_bar(
        df,
        x="property_risk_score",
        y="sa2_name",
        title="Top 10 Highest Risk Regions",
        color="#c53030",
        label="Property Risk Score",
    )


def top_affordability_bar(df: pd.DataFrame) -> go.Figure:
    return horizontal_bar(
        df,
        x="premium_to_income_percent",
        y="sa2_name",
        title="Top 10 Highest Affordability Stress Regions",
        color="#6b46c1",
        label="Premium to Income %",
    )


def region_component_bar(region: pd.Series) -> go.Figure:
    components = pd.DataFrame(
        {
            "component": [
                "Flood",
                "Bushfire",
                "Cyclone/Storm",
                "Historical Indicator",
                "Climate",
                "Vulnerability",
            ],
            "value": [
                region.get("flood_component"),
                region.get("bushfire_component"),
                region.get("cyclone_component"),
                region.get("storm_component"),
                region.get("climate_component"),
                region.get("vulnerability_component"),
            ],
        }
    )
    fig = px.bar(
        components,
        x="component",
        y="value",
        color="component",
        color_discrete_sequence=[
            "#2b6cb0",
            "#c05621",
            "#805ad5",
            "#718096",
            "#2f855a",
            "#b7791f",
        ],
        labels={"component": "Component", "value": "Weighted contribution"},
    )
    fig.update_layout(
        title="Property Risk Score Components",
        margin=dict(l=10, r=10, t=48, b=10),
        height=360,
        showlegend=False,
        yaxis_title="Weighted contribution",
    )
    return fig


def premium_loading_bar(region: pd.Series) -> go.Figure:
    loadings = pd.DataFrame(
        {
            "loading": [
                "Base",
                "Flood",
                "Bushfire",
                "Cyclone",
                "Storm",
                "Rebuild",
                "Mitigation Discount",
            ],
            "amount": [
                region.get("base_premium"),
                region.get("flood_loading"),
                region.get("bushfire_loading"),
                region.get("cyclone_loading"),
                region.get("storm_loading"),
                region.get("rebuild_loading"),
                -1 * (region.get("mitigation_discount") or 0),
            ],
        }
    )
    fig = px.bar(
        loadings,
        x="loading",
        y="amount",
        color="loading",
        color_discrete_sequence=[
            "#2d3748",
            "#2b6cb0",
            "#c05621",
            "#805ad5",
            "#718096",
            "#b7791f",
            "#2f855a",
        ],
        labels={"loading": "Premium component", "amount": "Estimated annual amount ($)"},
    )
    fig.update_layout(
        title="Estimated Premium Components",
        margin=dict(l=10, r=10, t=48, b=10),
        height=360,
        showlegend=False,
        yaxis_title="Estimated annual amount ($)",
    )
    return fig
