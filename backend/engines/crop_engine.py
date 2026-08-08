"""
===============================================================================
Crop Risk Engine — Master Calculation Orchestrator
===============================================================================
This module evaluates crop risk by combining multiple individual domain engines:
1. Climate Engine (temperature, dry spell, flood)
2. Soil Engine (drainage, texture, PH)
3. Irrigation Engine (water availability vs crop requirement)
4. Rotation Engine (previous crop suitability)
5. Market Engine (market price volatility)
6. Confidence Engine (data accuracy confidence level)

Beginner Python Note:
- We combine individual risk scores into a overall suitability percentage.
- We build a detailed 'trace' dictionary for each crop, which is passed to 
  the explanation_engine to generate the 15-section narrative report.
"""
from __future__ import annotations

from .confidence_engine import calculate_confidence
from .climate_engine import compute_climate_risk
from .irrigation_engine import calculate_irrigation_support
from .market_engine import evaluate_market
from .models import CropModel, DistrictModel, round_js
from .rotation_engine import evaluate_rotation
from .soil_engine import compute_soil_health
from trace_builder import build_analysis_trace
from explanation_engine import render_explanation


def evaluate_crop_risk(
    crop: CropModel,
    district: DistrictModel,
    season: str,
    irrigation: str,
    prev_crop: CropModel | None,
    climate_res: dict,
    soil_res: dict,
    irrigation_res: dict,
) -> dict:
    """
    Evaluates risk metrics for a single crop under given district & seasonal conditions.
    
    Returns:
        dict: Fully evaluated crop result dictionary containing risk scores, reasons,
              trace data, and explanation narratives.
    """
    # Initialize an empty list to collect key decision reasons
    reasons: list[str] = []
    season_lower = season.lower()
    seasonal_temp = climate_res["details"]["seasonalTemp"]
    rain_score = climate_res["details"]["rainScore"]
    flood_score = climate_res["details"]["floodScore"]

    water_risk = irrigation_res["risk_score"]
    irrigation_details = irrigation_res["details"]
    is_infeasible = irrigation_res["isInfeasible"]

    if is_infeasible:
        reasons.extend(irrigation_res["reasons"])

    season_matched = season_lower in [s.lower() for s in crop.seasons]
    if not season_matched:
        reasons.append(f"Season Mismatch: Not typically grown in {season}.")

    if not is_infeasible and water_risk > 35:
        reasons.append(
            f"Water supply (~{irrigation_details['effSupply']}mm) below optimal demand (~{irrigation_details['wmid']}mm)."
        )

    temp_risk = 0
    heat_threshold = crop.stress_thresholds["heat"]
    cold_threshold = crop.stress_thresholds["cold"]
    if seasonal_temp > heat_threshold:
        temp_risk = min(100, (seasonal_temp - heat_threshold) * 15)
        reasons.append(
            f"Heat Stress: Avg temp ({seasonal_temp}C) exceeds {crop.name}'s limit ({heat_threshold}C)."
        )
    elif seasonal_temp < cold_threshold:
        temp_risk = min(100, (cold_threshold - seasonal_temp) * 15)
        reasons.append(
            f"Cold Stress: Avg temp ({seasonal_temp}C) below {crop.name}'s limit ({cold_threshold}C)."
        )

    climate_risk = max(temp_risk, rain_score)
    soil_risk = soil_res["risk_score"]
    if soil_res["risk_level"] != "safe":
        reasons.append(f"Soil Constraint: {soil_res['details']['waterlogDetail']}")

    rotation_res = evaluate_rotation(crop, prev_crop)
    reasons.extend(rotation_res["reasons"])

    critical_threshold = 65
    weighted_avg = round_js((climate_risk * 0.4) + (soil_risk * 0.3) + (water_risk * 0.3))
    limiting_factor_value = max(climate_risk, soil_risk, water_risk, flood_score)

    if is_infeasible:
        final_penalty = 100
    elif limiting_factor_value > critical_threshold:
        final_penalty = limiting_factor_value
    else:
        final_penalty = weighted_avg

    limiting_factor_name = "Climate"
    if soil_risk == limiting_factor_value:
        limiting_factor_name = "Soil"
    if water_risk == limiting_factor_value:
        limiting_factor_name = "Water"
    if flood_score == limiting_factor_value:
        limiting_factor_name = "Flood"
    if climate_risk == limiting_factor_value:
        limiting_factor_name = "Climate"

    selection_mode = (
        "Infeasible"
        if is_infeasible
        else ("Limiting Factor" if limiting_factor_value > critical_threshold else "Weighted Average")
    )

    market_res = evaluate_market(crop)
    volatility_penalty = market_res["volatilityPenalty"]
    if volatility_penalty:
        final_penalty = min(100, final_penalty + volatility_penalty)
        reasons.extend(market_res["reasons"])

    risk_level = "safe" if final_penalty <= 35 else ("moderate" if final_penalty <= 65 else "high")
    suitability = max(0, 100 - final_penalty)
    confidence_res = calculate_confidence(district, climate_res["confidence"])

    aggregation = {
        "climateRisk": climate_risk,
        "tempRisk": temp_risk,
        "rainScore": rain_score,
        "floodScore": flood_score,
        "soilRisk": soil_risk,
        "waterRisk": water_risk,
        "weightedAvg": weighted_avg,
        "limitingFactorValue": limiting_factor_value,
        "limitingFactorName": limiting_factor_name,
        "criticalThreshold": critical_threshold,
        "selectionMode": selection_mode,
        "volatilityPenalty": volatility_penalty,
        "finalPenalty": final_penalty,
        "suitability": suitability,
        "riskLevel": risk_level,
    }

    analysis_trace = build_analysis_trace(
        crop=crop,
        district=district,
        season=season,
        irrigation=irrigation,
        prev_crop=prev_crop,
        climate_res=climate_res,
        soil_res=soil_res,
        irrigation_res=irrigation_res,
        rotation_res=rotation_res,
        market_res=market_res,
        confidence_res=confidence_res,
        aggregation=aggregation,
    )
    explanation = render_explanation(analysis_trace)

    result = crop.to_frontend_dict()
    result.update(
        {
            "crop": crop.name,
            "crop_id": crop.id,
            "crop_name": crop.name,
            "rank": None,
            "overall_score": suitability,
            "scores": {
                "climate": climate_risk,
                "soil": soil_risk,
                "water": water_risk,
                "market": volatility_penalty,
                "overall": suitability,
            },
            "risk_score": final_penalty,
            "risk_level": risk_level,
            "suitability": suitability,
            "profit_level": market_res["profitLevel"],
            "profit_score": market_res["profitScore"],
            "confidence": climate_res["confidence"],
            "confidenceDetails": confidence_res,
            "reasons": reasons,
            "riskFactors": reasons,
            "improvementSuggestions": soil_res["details"]["recommendations"],
            "summary": {
                "selectionMode": selection_mode,
                "limitingFactor": limiting_factor_name,
                "finalPenalty": final_penalty,
                "suitability": suitability,
            },
            "explanation": explanation,
            "analysisTrace": analysis_trace,
            "isInfeasible": is_infeasible,
        }
    )
    return result


def analyze_crops(
    crops: list[dict],
    district: dict,
    season: str,
    irrigation: str,
    previous_crop: str | None,
    has_residue: bool,
    has_fertilizer: bool,
    climate_constants: dict,
    soil_rules: dict,
) -> dict:
    district_model = DistrictModel(district)
    crop_models = [CropModel(c) for c in crops]
    crop_lookup = {crop.id: crop for crop in crop_models}
    prev_crop = crop_lookup.get(previous_crop) if previous_crop else None

    climate_res = compute_climate_risk(district_model, season, irrigation, climate_constants)
    soil_res = compute_soil_health(
        district_model,
        prev_crop,
        district_model.get_effective_seasonal_rainfall(season),
        has_residue,
        has_fertilizer,
        soil_rules,
    )

    results = [
        evaluate_crop_risk(
            crop,
            district_model,
            season,
            irrigation,
            prev_crop,
            climate_res,
            soil_res,
            calculate_irrigation_support(
                crop, irrigation, district_model, season, climate_constants
            ),
        )
        for crop in crop_models
    ]

    results.sort(key=lambda item: item["suitability"], reverse=True)
    for index, result in enumerate(results, start=1):
        result["rank"] = index

    return {
        "climate": climate_res,
        "soil": soil_res,
        "crops": results,
        "district": district_model.to_frontend_dict(),
        "summary": {
            "totalCropsEvaluated": len(results),
            "topCrop": results[0]["name"] if results else None,
        },
    }
