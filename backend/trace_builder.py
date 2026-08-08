from __future__ import annotations

from engines.models import CropModel, DistrictModel, round_js


def build_analysis_trace(
    crop: CropModel,
    district: DistrictModel,
    season: str,
    irrigation: str,
    prev_crop: CropModel | None,
    climate_res: dict,
    soil_res: dict,
    irrigation_res: dict,
    rotation_res: dict,
    market_res: dict,
    confidence_res: dict,
    aggregation: dict,
) -> dict:
    climate_details = climate_res["details"]
    soil_details = soil_res["details"]
    irrigation_details = irrigation_res["details"]
    soil_trace = soil_res.get("trace") or {}
    irrigation_trace = irrigation_res.get("trace") or {}
    irrigation_calcs = irrigation_trace.get("calculations") or {}
    crop_water = crop.water_needs
    economics = crop.economics

    operations = {
        "climate": _operations_from_climate(climate_res, aggregation),
        "soil": _operations_from_soil(soil_res),
        "water": _operations_from_water(irrigation_res),
        "aggregation": _operations_from_aggregation(aggregation),
        "confidence": _operations_from_confidence(confidence_res),
    }

    return {
        "crop": {
            "name": crop.name,
            "id": crop.id,
            "family": crop.family,
            "category": crop.category,
            "seasons": crop.seasons,
            "heatThreshold": crop.stress_thresholds["heat"],
            "coldThreshold": crop.stress_thresholds["cold"],
            "waterMin": crop_water["min"],
            "waterMid": crop_water["mid"],
            "waterMax": crop_water["max"],
        },
        "climate": {
            "annualRainfall": district.annual_rainfall,
            "season": season,
            "irrigation": irrigation,
            "soilTexture": district.soil["texture"],
            "soilDrainage": district.soil["drainage"],
            "rainfallCV": district.rainfall_cv,
            "seasonalRainfallShare": district.rainfall_shares.get(season.lower()) or 0,
            "rawSeasonalRainfall": district.get_seasonal_rainfall(season),
            "effectiveRainfall": climate_details["effectiveRainfall"],
            "seasonalTemp": climate_details["seasonalTemp"],
            "drySpellPct": climate_details["drySpellPct"],
            "rainScore": climate_details["rainScore"],
            "floodLevel": climate_details["floodLevel"],
            "floodScore": climate_details["floodScore"],
            "irrigationReduction": irrigation != "rainfed",
            "drainageEscalation": district.soil["drainage"] == "Poor" and district.annual_rainfall > 900,
        },
        "soil": {
            "soilType": district.soil["type"],
            "soilTexture": district.soil["texture"],
            "soilDrainage": district.soil["drainage"],
            "previousCrop": prev_crop.name if prev_crop else "None",
            "previousCropFamily": prev_crop.family if prev_crop else "None",
            "hasResidue": soil_trace.get("inputs", {}).get("hasResidue", False),
            "hasFertilizer": soil_trace.get("inputs", {}).get("hasFertilizer", False),
            "feederLevel": soil_trace.get("calculations", {}).get("feederLevel", "none"),
            "nitrogenRisk": soil_details["nitrogenRisk"],
            "nitrogenScore": soil_details["nScore"],
            "waterlogRisk": soil_details["waterlogRisk"],
            "waterlogScore": soil_details["wScore"],
            "seasonalRainfall": soil_trace.get("inputs", {}).get("seasonalRainfall", 0),
            "poorDrainageHighRain": soil_trace.get("ruleEvaluations", [{}, {}])[1].get("poorDrainageHighRain", False),
            "clayHighRain": soil_trace.get("ruleEvaluations", [{}, {}])[1].get("clayHighRain", False),
            "poorDrainageModRain": soil_trace.get("ruleEvaluations", [{}, {}])[1].get("poorDrainageModRain", False),
            "weightedFormula": soil_trace.get("calculations", {}).get("weightedFormula", ""),
            "floorCheck": soil_trace.get("calculations", {}).get("floorCheck", ""),
            "finalRiskScore": soil_res["risk_score"],
            "recommendations": soil_details["recommendations"],
        },
        "water": {
            "cropName": crop.name,
            "irrigationType": irrigation,
            "irrigationBase": irrigation_calcs.get("irrigationBase", 0),
            "effectiveRainfall": irrigation_calcs.get("effectiveRainfall", 0),
            "rainfedMode": irrigation == "rainfed",
            "rainfallContribution": irrigation_calcs.get("rainfallContribution", 0),
            "totalEffectiveSupply": irrigation_details["effSupply"],
            "cropWaterMin": irrigation_details["wmin"],
            "cropWaterMid": irrigation_details["wmid"],
            "cropWaterMax": crop_water["max"],
            "deficit": irrigation_calcs.get("deficit", 0),
            "surplus": irrigation_calcs.get("surplus", 0),
            "deficitRatio": irrigation_details["defRatio"],
            "deficitRatioPercent": round_js(irrigation_details["defRatio"] * 100),
            "biologicalMinimum": irrigation_details["wmin"],
            "biologicalThreshold": round_js(irrigation_details["wmin"] * 0.95),
            "isInfeasible": irrigation_res["isInfeasible"],
            "riskScore": irrigation_res["risk_score"],
            "severeDeficit": irrigation_details["defRatio"] > 0.35,
        },
        "season": {
            "selectedSeason": season,
            "cropName": crop.name,
            "cropSeasons": crop.seasons,
            "matched": season.lower() in [s.lower() for s in crop.seasons],
        },
        "zone": {"districtZone": district.zone},
        "market": {
            "cropName": crop.name,
            "volatility": economics["marketVolatility"],
            "penalty": market_res["volatilityPenalty"],
            "mspCovered": economics["mspCovered"],
            "mspPrice": economics["mspPricePerQtl"],
            "mspYear": economics["mspYear"],
            "yieldPotential": economics["yieldPotential"],
            "marketPrice": economics["marketPrice"],
            "inputCost": economics["inputCost"],
            "profitScore": market_res["profitScore"],
            "profitLevel": market_res["profitLevel"],
        },
        "rotation": {
            "previousCrop": prev_crop.name if prev_crop else "None",
            "previousCropFamily": prev_crop.family if prev_crop else "None",
            "currentCrop": crop.name,
            "currentCropFamily": crop.family,
            "conflict": rotation_res["conflict"],
            "beneficial": rotation_res["beneficial"],
            "badPredecessors": crop.rotation["badPredecessors"],
            "goodPredecessors": crop.rotation["goodPredecessors"],
        },
        "confidence": confidence_res,
        "aggregation": aggregation,
        "operations": operations,
    }


def _operations_from_climate(climate_res: dict, aggregation: dict) -> list[dict]:
    details = climate_res["details"]
    return [
        {
            "factor": "Rain distribution score",
            "input": details["drySpellPct"],
            "expectedValue": "0 to 50 dry-spell probability scale",
            "actualValue": details["drySpellPct"],
            "formula": "min(100, (drySpellPct / 50) x 100)",
            "penaltyOrBonus": details["rainScore"],
            "scoreBefore": 0,
            "scoreAfter": details["rainScore"],
        },
        {
            "factor": "Temperature stress",
            "input": details["seasonalTemp"],
            "expectedValue": "Crop cold/heat thresholds",
            "actualValue": details["seasonalTemp"],
            "formula": "temperature delta x 15, capped at 100",
            "penaltyOrBonus": aggregation["tempRisk"],
            "scoreBefore": 0,
            "scoreAfter": aggregation["tempRisk"],
        },
        {
            "factor": "Climate risk",
            "input": [aggregation["tempRisk"], details["rainScore"]],
            "expectedValue": "Higher stress determines climate risk",
            "actualValue": aggregation["climateRisk"],
            "formula": "max(tempRisk, rainScore)",
            "penaltyOrBonus": aggregation["climateRisk"],
            "scoreBefore": 0,
            "scoreAfter": aggregation["climateRisk"],
        },
    ]


def _operations_from_soil(soil_res: dict) -> list[dict]:
    calcs = soil_res["trace"]["calculations"]
    return [
        {
            "factor": "Nitrogen depletion",
            "input": calcs["feederLevel"],
            "expectedValue": "Managed or non-heavy feeder",
            "actualValue": calcs["nitrogenRisk"],
            "formula": "moderate nitrogen risk => 50, otherwise 0",
            "penaltyOrBonus": calcs["nitrogenScore"],
            "scoreBefore": 0,
            "scoreAfter": calcs["nitrogenScore"],
        },
        {
            "factor": "Waterlogging",
            "input": calcs["waterlogRisk"],
            "expectedValue": "low",
            "actualValue": calcs["waterlogRisk"],
            "formula": "high => 100, medium => 60, low => 0",
            "penaltyOrBonus": calcs["waterlogScore"],
            "scoreBefore": 0,
            "scoreAfter": calcs["waterlogScore"],
        },
        {
            "factor": "Final soil risk",
            "input": [calcs["nitrogenScore"], calcs["waterlogScore"]],
            "expectedValue": "weighted average with waterlog floor",
            "actualValue": soil_res["risk_score"],
            "formula": calcs["weightedFormula"] + "; " + calcs["floorCheck"],
            "penaltyOrBonus": soil_res["risk_score"],
            "scoreBefore": 0,
            "scoreAfter": soil_res["risk_score"],
        },
    ]


def _operations_from_water(irrigation_res: dict) -> list[dict]:
    c = irrigation_res["trace"]["calculations"]
    return [
        {
            "factor": "Total effective water supply",
            "input": [c["irrigationBase"], c["rainfallContribution"]],
            "expectedValue": c["optimalDemand"],
            "actualValue": c["totalEffectiveSupply"],
            "formula": "irrigation base + rainfall contribution",
            "penaltyOrBonus": 0,
            "scoreBefore": 0,
            "scoreAfter": c["totalEffectiveSupply"],
        },
        {
            "factor": "Biological feasibility",
            "input": c["totalEffectiveSupply"],
            "expectedValue": c["biologicalThreshold"],
            "actualValue": c["totalEffectiveSupply"],
            "formula": "supply < waterMin x 0.95 => 100 penalty",
            "penaltyOrBonus": 100 if c["isInfeasible"] else 0,
            "scoreBefore": 0,
            "scoreAfter": 100 if c["isInfeasible"] else 0,
        },
        {
            "factor": "Water deficit risk",
            "input": c["deficitRatio"],
            "expectedValue": "0 or lower",
            "actualValue": c["deficitRatio"],
            "formula": "min(100, deficitRatio^1.5 x 200), floor 75 if ratio > 0.35",
            "penaltyOrBonus": c["riskScore"],
            "scoreBefore": 0,
            "scoreAfter": c["riskScore"],
        },
    ]


def _operations_from_aggregation(aggregation: dict) -> list[dict]:
    return [
        {
            "factor": "Weighted risk average",
            "input": [aggregation["climateRisk"], aggregation["soilRisk"], aggregation["waterRisk"]],
            "expectedValue": "Climate 40%, soil 30%, water 30%",
            "actualValue": aggregation["weightedAvg"],
            "formula": "(climateRisk x 0.4) + (soilRisk x 0.3) + (waterRisk x 0.3)",
            "penaltyOrBonus": aggregation["weightedAvg"],
            "scoreBefore": 0,
            "scoreAfter": aggregation["weightedAvg"],
        },
        {
            "factor": "Final penalty",
            "input": aggregation["selectionMode"],
            "expectedValue": "Use infeasible, limiting factor, or weighted average rule",
            "actualValue": aggregation["finalPenalty"],
            "formula": "infeasible => 100; if limiting > 65 use limiting factor; else weighted average; then market penalty",
            "penaltyOrBonus": aggregation["finalPenalty"],
            "scoreBefore": 100,
            "scoreAfter": aggregation["suitability"],
        },
    ]


def _operations_from_confidence(confidence: dict) -> list[dict]:
    return [
        {
            "factor": "Confidence",
            "input": [confidence["completeness"], confidence["stabilityFactor"], confidence["modelFactor"]],
            "expectedValue": "Higher geometric mean is better",
            "actualValue": confidence["geometricMean"],
            "formula": "(completeness x stabilityFactor x modelFactor)^(1/3)",
            "penaltyOrBonus": 0,
            "scoreBefore": None,
            "scoreAfter": confidence["level"],
        }
    ]
