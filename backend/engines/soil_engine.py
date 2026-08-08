from __future__ import annotations

from .models import CropModel, DistrictModel, round_js


def compute_soil_health(
    district: DistrictModel,
    prev_crop: CropModel | None,
    seasonal_rainfall: int,
    has_residue: bool,
    has_fertilizer: bool,
    soil_rules: dict,
) -> dict:
    soil = district.soil
    soil_type = soil["type"]
    drainage = soil["drainage"]
    texture = soil["texture"]

    nitrogen_risk = "low"
    nitrogen_detail = "Nitrogen levels stable."
    feeder_level = "none"
    if prev_crop:
        feeder_level = soil_rules["nutrient_feeders"].get(prev_crop.family, "normal")
        if feeder_level == "heavy":
            if has_residue and has_fertilizer:
                nitrogen_detail = f"{prev_crop.name} is a heavy feeder, but managed."
            else:
                nitrogen_risk = "moderate"
                nitrogen_detail = f"{prev_crop.name} depletes soil nitrogen."
        elif feeder_level == "fixer":
            nitrogen_detail = f"{prev_crop.name} improved soil fertility."

    waterlog_risk = "low"
    waterlog_detail = "Good drainage."
    if drainage == "Poor" and seasonal_rainfall > 1000:
        waterlog_risk = "high"
        waterlog_detail = f"Poor drainage + high rainfall ({seasonal_rainfall}mm)."
    elif texture == "clay" and seasonal_rainfall > 800:
        waterlog_risk = "medium"
        waterlog_detail = "Heavy clay + high rainfall."
    elif drainage == "Poor" and seasonal_rainfall > 500:
        waterlog_risk = "medium"
        waterlog_detail = "Poor drainage with moderate rain."

    recommendations = list(soil_rules["soil_type_advice"].get(soil_type, []))
    if nitrogen_risk == "moderate":
        recommendations.append("Rotate with pulses to restore nitrogen.")
    if waterlog_risk in ("high", "medium"):
        recommendations.append("Construct raised beds or furrows.")

    n_score = 50 if nitrogen_risk == "moderate" else 0
    w_score = 100 if waterlog_risk == "high" else (60 if waterlog_risk == "medium" else 0)
    weighted_avg = round_js((n_score * 0.3) + (w_score * 0.7))
    risk_score = max(weighted_avg, round_js(w_score * 0.9))

    return {
        "risk_score": risk_score,
        "risk_level": "high" if risk_score > 65 else ("moderate" if risk_score > 35 else "safe"),
        "confidence": "high",
        "reasons": [],
        "details": {
            "soilType": soil_type,
            "drainage": drainage,
            "nitrogenRisk": nitrogen_risk,
            "nitrogenDetail": nitrogen_detail,
            "waterlogRisk": waterlog_risk,
            "waterlogDetail": waterlog_detail,
            "recommendations": recommendations,
            "nScore": n_score,
            "wScore": w_score,
        },
        "trace": {
            "inputs": {
                "soilType": soil_type,
                "soilDrainage": drainage,
                "soilTexture": texture,
                "previousCrop": prev_crop.name if prev_crop else "None",
                "previousCropFamily": prev_crop.family if prev_crop else "None",
                "seasonalRainfall": seasonal_rainfall,
                "hasResidue": has_residue,
                "hasFertilizer": has_fertilizer,
            },
            "calculations": {
                "nitrogenRisk": nitrogen_risk,
                "nitrogenDetail": nitrogen_detail,
                "nitrogenScore": n_score,
                "feederLevel": feeder_level,
                "waterlogRisk": waterlog_risk,
                "waterlogDetail": waterlog_detail,
                "waterlogScore": w_score,
                "weightedAverage": weighted_avg,
                "weightedFormula": f"({n_score} x 0.3) + ({w_score} x 0.7) = {weighted_avg}",
                "floorCheck": f"max({weighted_avg}, {round_js(w_score * 0.9)}) = {risk_score}",
                "finalRiskScore": risk_score,
            },
            "ruleEvaluations": [
                {
                    "rule": "Nitrogen Depletion",
                    "previousCrop": prev_crop.name if prev_crop else "None",
                    "feederType": feeder_level,
                    "residueManaged": has_residue,
                    "fertilizerApplied": has_fertilizer,
                    "result": nitrogen_risk,
                    "penalty": n_score,
                },
                {
                    "rule": "Waterlogging Risk",
                    "drainage": drainage,
                    "texture": texture,
                    "seasonalRainfall": seasonal_rainfall,
                    "poorDrainageHighRain": drainage == "Poor" and seasonal_rainfall > 1000,
                    "clayHighRain": texture == "clay" and seasonal_rainfall > 800,
                    "poorDrainageModRain": drainage == "Poor" and seasonal_rainfall > 500,
                    "result": waterlog_risk,
                    "penalty": w_score,
                },
            ],
            "recommendations": recommendations,
        },
    }
