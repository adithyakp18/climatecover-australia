from __future__ import annotations


def risk_band(score: float | None) -> str | None:
    if score is None:
        return None
    if score < 25:
        return "Low"
    if score < 50:
        return "Moderate"
    if score < 75:
        return "High"
    return "Severe"


def affordability_band(premium_to_income_percent: float | None) -> str | None:
    if premium_to_income_percent is None:
        return None
    if premium_to_income_percent < 2:
        return "Low"
    if premium_to_income_percent < 4:
        return "Moderate"
    if premium_to_income_percent < 8.33:
        return "High"
    return "Severe"
