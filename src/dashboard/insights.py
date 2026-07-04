from __future__ import annotations

from typing import Any

import pandas as pd

from src.dashboard.formatting import format_currency, format_number, format_percent


def _value(row: pd.Series | dict[str, Any], key: str, default: Any = None) -> Any:
    if isinstance(row, pd.Series):
        return row.get(key, default)
    return row.get(key, default)


def _top_region_label(df: pd.DataFrame, metric: str) -> str:
    if df.empty:
        return "No region available"
    row = df.sort_values(metric, ascending=False).iloc[0]
    return f"{row['sa2_name']}, {row['state_name']}"


def build_national_briefing(
    kpis: dict[str, float],
    top_risk: pd.DataFrame,
    top_stress: pd.DataFrame,
    priority: pd.DataFrame,
    manifest: dict[str, object],
) -> list[str]:
    total_regions = int(kpis.get("total_regions", 0) or 0)
    high_risk = int(kpis.get("high_risk_regions", 0) or 0)
    severe_stress = int(kpis.get("severe_affordability_regions", 0) or 0)
    high_risk_share = (high_risk / total_regions * 100) if total_regions else 0
    severe_share = (severe_stress / total_regions * 100) if total_regions else 0
    last_refresh = manifest.get("last_refresh_utc") or "the latest available refresh"

    highest_risk_region = _top_region_label(top_risk, "property_risk_score")
    highest_stress_region = _top_region_label(top_stress, "premium_to_income_percent")
    priority_region = _top_region_label(priority, "intervention_priority_score")

    return [
        (
            f"ClimateCover is monitoring {total_regions:,} Australian regional markets. "
            f"{high_risk:,} regions ({high_risk_share:.1f}%) are currently classified as high "
            f"or severe property risk."
        ),
        (
            f"Insurance affordability pressure is most acute in {severe_stress:,} regions "
            f"({severe_share:.1f}%), where estimated annual premiums consume a severe share "
            f"of median household income."
        ),
        (
            f"The highest risk signal is currently concentrated in {highest_risk_region}, "
            f"while the strongest affordability stress signal is in {highest_stress_region}."
        ),
        (
            f"The leading intervention priority is {priority_region}, where physical hazard exposure "
            f"and household affordability pressure overlap."
        ),
        f"Dataset refresh status: {last_refresh}.",
    ]


def build_region_briefing(region: pd.Series) -> list[str]:
    risk_band = _value(region, "risk_band", "Unclassified")
    affordability_band = _value(region, "affordability_band", "Unclassified")
    risk_score = _value(region, "property_risk_score")
    premium = _value(region, "estimated_annual_premium")
    premium_share = _value(region, "premium_to_income_percent")
    income = _value(region, "median_annual_household_income")
    priority = _value(region, "intervention_priority_score")
    top_hazard = _dominant_hazard(region)

    return [
        (
            f"{_value(region, 'sa2_name')} is classified as {risk_band} property risk, "
            f"with a score of {format_number(risk_score, 1)} out of 100."
        ),
        (
            f"The modelled annual insurance cost is {format_currency(premium)}, equivalent to "
            f"{format_percent(premium_share)} of estimated annual household income "
            f"({format_currency(income)})."
        ),
        (
            f"The leading hazard driver is {top_hazard}, supported by SEIFA and household "
            f"affordability indicators."
        ),
        (
            f"Decision signal: {affordability_band} affordability pressure and an intervention "
            f"priority score of {format_number(priority, 1)}."
        ),
    ]


def _dominant_hazard(region: pd.Series) -> str:
    hazards = {
        "flood exposure": _value(region, "flood_risk_score", 0) or 0,
        "bushfire exposure": _value(region, "bushfire_risk_score", 0) or 0,
        "cyclone exposure": _value(region, "cyclone_risk_score", 0) or 0,
        "storm exposure": _value(region, "storm_risk_score", 0) or 0,
    }
    return max(hazards, key=hazards.get)
