from __future__ import annotations

import math

from .models import CropModel, DistrictModel, round_js


def calculate_irrigation_support(
    crop: CropModel,
    irrigation: str,
    district: DistrictModel,
    season: str,
    constants: dict,
) -> dict:
    irrigation_capacity = constants["irrigation_capacity"]
    eff_rain = district.get_effective_seasonal_rainfall(season)
    water_needs = crop.water_needs
    wmin = water_needs["min"]
    wmid = water_needs["mid"]
    eff_supply = irrigation_capacity.get(irrigation, 0)

    if irrigation == "rainfed":
        eff_supply = eff_rain
    else:
        eff_supply += round_js(eff_rain * 0.8)

    is_infeasible = eff_supply < (wmin * 0.95)
    def_ratio = (wmid - eff_supply) / max(wmid, 1)
    risk_score = 0

    if is_infeasible:
        risk_score = 100
    elif def_ratio > 0:
        risk_score = min(100, round_js(math.pow(def_ratio, 1.5) * 200))
        if def_ratio > 0.35:
            risk_score = max(risk_score, 75)

    deficit = max(0, wmid - eff_supply)
    surplus = max(0, eff_supply - wmid)

    return {
        "risk_score": risk_score,
        "risk_level": "high" if is_infeasible else ("high" if risk_score > 65 else ("moderate" if risk_score > 35 else "safe")),
        "confidence": "high",
        "isInfeasible": is_infeasible,
        "reasons": [f"Infeasible: Effective water supply ({eff_supply}mm) is below minimum biological requirement ({wmin}mm)."] if is_infeasible else [],
        "details": {
            "effSupply": eff_supply,
            "defRatio": def_ratio,
            "wmin": wmin,
            "wmid": wmid,
        },
        "trace": {
            "inputs": {
                "cropName": crop.name,
                "irrigationType": irrigation,
                "irrigationCapacity": irrigation_capacity.get(irrigation, 0),
                "cropWaterMin": wmin,
                "cropWaterMid": wmid,
                "cropWaterMax": water_needs["max"],
                "districtName": district.name,
                "season": season,
            },
            "calculations": {
                "effectiveRainfall": eff_rain,
                "irrigationBase": irrigation_capacity.get(irrigation, 0),
                "rainfedMode": irrigation == "rainfed",
                "rainfallContribution": eff_rain if irrigation == "rainfed" else round_js(eff_rain * 0.8),
                "totalEffectiveSupply": eff_supply,
                "optimalDemand": wmid,
                "deficit": deficit,
                "surplus": surplus,
                "deficitRatio": def_ratio,
                "deficitRatioPercent": round_js(def_ratio * 100),
                "biologicalMinimum": wmin,
                "biologicalThreshold": round_js(wmin * 0.95),
                "isInfeasible": is_infeasible,
                "riskScore": risk_score,
            },
            "ruleEvaluations": [
                {
                    "rule": "Biological Feasibility (FAO 56)",
                    "supply": eff_supply,
                    "minimumRequired": wmin,
                    "threshold": round_js(wmin * 0.95),
                    "passed": not is_infeasible,
                    "penalty": 100 if is_infeasible else 0,
                },
                {
                    "rule": "Water Deficit Penalty (Power Law)",
                    "deficitRatio": def_ratio,
                    "formula": f"min(100, ({def_ratio:.3f}^1.5) x 200) = {min(100, round_js(math.pow(max(0, def_ratio), 1.5) * 200))}" if def_ratio > 0 else "No deficit",
                    "severeDeficit": def_ratio > 0.35,
                    "penalty": risk_score,
                },
            ],
        },
    }
