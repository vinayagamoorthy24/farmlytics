from __future__ import annotations

from .models import DistrictModel


def calculate_confidence(district: DistrictModel, level: str) -> dict:
    completeness = district.data_quality
    stability_factor = 1.0
    if district.rainfall_cv >= 40:
        stability_factor = 0.6
    elif district.rainfall_cv >= 30:
        stability_factor = 0.8
    elif district.rainfall_cv >= 20:
        stability_factor = 0.95

    model_factor = 0.85
    geometric_mean = (completeness * stability_factor * model_factor) ** (1 / 3)

    return {
        "completeness": completeness,
        "stabilityFactor": stability_factor,
        "modelFactor": model_factor,
        "geometricMean": geometric_mean,
        "level": level,
        "rainfallCV": district.rainfall_cv,
    }
