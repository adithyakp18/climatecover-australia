from __future__ import annotations

import pandas as pd
import streamlit as st


RISK_COLORS = {
    "Low": "#2f855a",
    "Moderate": "#b7791f",
    "High": "#c05621",
    "Severe": "#c53030",
}

AFFORDABILITY_COLORS = {
    "Low": "#2b6cb0",
    "Moderate": "#6b46c1",
    "High": "#c05621",
    "Severe": "#c53030",
}

NEUTRAL_COLOR = "#4a5568"


def configure_page(title: str) -> None:
    st.set_page_config(
        page_title=f"{title} | ClimateCover Australia",
        layout="wide",
    )
    st.markdown(
        """
        <style>
        :root {
            --cc-ink: #172033;
            --cc-muted: #526071;
            --cc-line: #d8e0ea;
            --cc-panel: #ffffff;
            --cc-soft: #f6f8fb;
            --cc-blue: #1f5f99;
            --cc-navy: #10243f;
        }
        html, body, [data-testid="stAppViewContainer"] {
            background: linear-gradient(180deg, #eef4f9 0%, #f8fafc 34%, #ffffff 100%);
            color: var(--cc-ink);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
            max-width: 1280px;
        }
        h1, h2, h3, h4, h5, h6, p, li, label, span {
            color: var(--cc-ink);
        }
        [data-testid="stSidebar"] {
            background: #f7fafc;
            border-right: 1px solid var(--cc-line);
        }
        div[data-testid="stMetric"] {
            background: var(--cc-panel);
            border: 1px solid var(--cc-line);
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.07);
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
            color: var(--cc-muted) !important;
            font-weight: 700;
        }
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: var(--cc-navy) !important;
            font-weight: 800;
        }
        .cc-card {
            border: 1px solid var(--cc-line);
            border-radius: 8px;
            padding: 1rem;
            background: var(--cc-panel);
            height: 100%;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            color: var(--cc-ink);
        }
        .cc-card h4 {
            color: var(--cc-navy);
            margin-top: 0;
            margin-bottom: 0.35rem;
        }
        .cc-summary {
            border-left: 4px solid var(--cc-blue);
            background: #edf5fc;
            padding: 1rem 1.25rem;
            border-radius: 6px;
            color: var(--cc-ink);
            box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
        }
        .cc-hero {
            background: linear-gradient(135deg, #10243f 0%, #1f5f99 58%, #2b8a7e 100%);
            color: #ffffff;
            border-radius: 8px;
            padding: 1.5rem 1.75rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 14px 34px rgba(15, 23, 42, 0.18);
        }
        .cc-hero h1, .cc-hero h2, .cc-hero h3, .cc-hero p {
            color: #ffffff;
        }
        .cc-pill {
            display: inline-block;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            background: #e6f0fa;
            color: #17466f;
            font-weight: 700;
            font-size: 0.78rem;
            margin-right: 0.35rem;
        }
        .cc-small {
            color: var(--cc-muted);
            font-size: 0.92rem;
        }
        .stDataFrame {
            border: 1px solid var(--cc-line);
            border-radius: 8px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_currency(value: float | int | None) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"${value:,.0f}"


def format_number(value: float | int | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value:,.{decimals}f}"


def format_percent(value: float | int | None, decimals: int = 2) -> str:
    if value is None or pd.isna(value):
        return "n/a"
    return f"{value:,.{decimals}f}%"


def band_order() -> list[str]:
    return ["Low", "Moderate", "High", "Severe"]


def display_data_warning() -> None:
    st.warning(
        "The regional risk database is not ready yet. "
        "Run the data preparation pipeline before launching the dashboard."
    )
