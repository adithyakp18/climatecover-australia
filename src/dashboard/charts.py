from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.dashboard.formatting import AFFORDABILITY_COLORS, RISK_COLORS, band_order


def donut_chart(df: pd.DataFrame, title: str, color_map: dict[str, str]) -> go.Figure:
    order = band_order()
    ordered = (
        df.set_index("band")
        .reindex(order, fill_value=0)
        .reset_index()
        .rename(columns={"index": "band"})
    )
    ordered["region_count"] = ordered["region_count"].fillna(0).astype(int)
    total = int(ordered["region_count"].sum())

    fig = go.Figure(
        data=[
            go.Pie(
                labels=ordered["band"],
                values=ordered["region_count"],
                hole=0.62,
                sort=False,
                marker=dict(
                    colors=[color_map.get(band, "#718096") for band in ordered["band"]],
                    line=dict(color="#ffffff", width=2),
                ),
                texttemplate="%{label}<br>%{percent}",
                textposition="inside",
                hovertemplate="<b>%{label}</b><br>%{value:,} regions<br>%{percent}<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title=title,
        template="plotly_white",
        margin=dict(l=12, r=12, t=58, b=18),
        legend_title_text="Band",
        height=410,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#172033", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=-0.08, xanchor="center", x=0.5),
        annotations=[
            dict(
                text=f"{total:,}<br>regions",
                x=0.5,
                y=0.5,
                font=dict(size=18, color="#10243f"),
                showarrow=False,
            )
        ],
    )
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
        template="plotly_white",
        margin=dict(l=10, r=22, t=58, b=20),
        height=450,
        yaxis_title="",
        xaxis_title=label,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(color="#172033", size=12),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#e6edf5")
    fig.update_yaxes(showgrid=False, automargin=True)
    fig.update_traces(
        texttemplate="%{text:.1f}",
        textposition="outside",
        cliponaxis=False,
        marker_line_color="#ffffff",
        marker_line_width=1,
    )
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
        template="plotly_white",
        margin=dict(l=10, r=10, t=58, b=18),
        height=380,
        showlegend=False,
        yaxis_title="Weighted contribution",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(color="#172033", size=12),
    )
    fig.update_yaxes(showgrid=True, gridcolor="#e6edf5")
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
        template="plotly_white",
        margin=dict(l=10, r=10, t=58, b=18),
        height=380,
        showlegend=False,
        yaxis_title="Estimated annual amount ($)",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(color="#172033", size=12),
    )
    fig.update_yaxes(showgrid=True, gridcolor="#e6edf5")
    return fig
