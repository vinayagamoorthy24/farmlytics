from __future__ import annotations

from .models import DistrictModel


def compute_climate_risk(
    district: DistrictModel,
    season: str,
    irrigation: str,
    constants: dict,
) -> dict:
    rainfall_cv_thresholds = constants["rainfall_cv_thresholds"]
    dry_spell_base_rates = constants["dry_spell_base_rates"]
    evapotranspiration_penalty = constants["evapotranspiration_penalty"]

    effective_rainfall = district.get_effective_seasonal_rainfall(season)
    seasonal_temp = district.get_seasonal_temp(season)
    cv = district.rainfall_cv

    if cv < rainfall_cv_thresholds["low"]:
        dry_spell_pct = dry_spell_base_rates["low"]
    elif cv < rainfall_cv_thresholds["medium"]:
        dry_spell_pct = dry_spell_base_rates["medium"]
    else:
        dry_spell_pct = dry_spell_base_rates["high"]

    if cv > 35:
        dry_spell_pct += 10

    if irrigation != "rainfed":
        dry_spell_pct = round(dry_spell_pct * 0.4)

    if effective_rainfall < 400 and seasonal_temp > 32:
        dry_spell_pct += evapotranspiration_penalty

    flood_level = "low"
    if district.annual_rainfall > 1600:
        flood_level = "high"
    elif district.annual_rainfall > 1200:
        flood_level = "medium"

    if district.soil["drainage"] == "Poor" and district.annual_rainfall > 900:
        if flood_level == "low":
            flood_level = "medium"
        elif flood_level == "medium":
            flood_level = "high"

    rain_score = min(100, (dry_spell_pct / 50) * 100)
    flood_score = 80 if flood_level == "high" else (40 if flood_level == "medium" else 0)

    return {
        "confidence": district.get_confidence_score(),
        "details": {
            "effectiveRainfall": effective_rainfall,
            "drySpellPct": dry_spell_pct,
            "floodLevel": flood_level,
            "rangeCV": cv,
            "seasonalTemp": seasonal_temp,
            "rainScore": rain_score,
            "floodScore": flood_score,
        },
        "trace": {
            "inputs": {
                "districtName": district.name,
                "annualRainfall": district.annual_rainfall,
                "season": season,
                "irrigation": irrigation,
                "soilTexture": district.soil["texture"],
                "soilDrainage": district.soil["drainage"],
                "rainfallCV": cv,
            },
            "calculations": {
                "seasonalRainfallShare": district.rainfall_shares.get(season.lower()) or 0,
                "rawSeasonalRainfall": district.get_seasonal_rainfall(season),
                "effectiveRainfall": effective_rainfall,
                "seasonalTemp": seasonal_temp,
                "drySpellPct": dry_spell_pct,
                "rainScore": rain_score,
                "floodScore": flood_score,
                "floodLevel": flood_level,
            },
            "ruleEvaluations": [
                {
                    "rule": "Dry Spell Probability",
                    "input": f"Rainfall CV = {cv}%",
                    "thresholds": f"Low < {rainfall_cv_thresholds['low']}, Medium < {rainfall_cv_thresholds['medium']}",
                    "baseDrySpell": dry_spell_base_rates["low"] if cv < rainfall_cv_thresholds["low"] else (dry_spell_base_rates["medium"] if cv < rainfall_cv_thresholds["medium"] else dry_spell_base_rates["high"]),
                    "cvBonusApplied": cv > 35,
                    "irrigationReduction": irrigation != "rainfed",
                    "evapPenaltyApplied": effective_rainfall < 400 and seasonal_temp > 32,
                    "finalDrySpellPct": dry_spell_pct,
                },
                {
                    "rule": "Flood Risk",
                    "input": f"Annual Rainfall = {district.annual_rainfall} mm, Drainage = {district.soil['drainage']}",
                    "thresholdHigh": 1600,
                    "thresholdMedium": 1200,
                    "drainageEscalation": district.soil["drainage"] == "Poor" and district.annual_rainfall > 900,
                    "result": flood_level,
                    "floodScore": flood_score,
                },
                {
                    "rule": "Rain Distribution Score",
                    "formula": f"min(100, ({dry_spell_pct} / 50) x 100)",
                    "result": rain_score,
                },
            ],
        },
    }
