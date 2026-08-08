"""
===============================================================================
Explanation Engine — Agricultural Decision Narrative Generator
===============================================================================
This module acts as the "Agricultural Scientist Narrative Writer".

How it works:
1. Takes the raw calculation data (trace) produced by our python calculation engines.
2. Converts raw numerical metrics (e.g. soil drainage, rainfall mm, temperature)
   into human-readable, professional agricultural reports.
3. Does NOT show raw engine scores or internal math variables to the user.
   Instead, it answers: "Why is this crop suitable or unsuitable for this land?"

Beginner Python Note:
- Dictionaries ({key: value}) are used to hold each section of the report.
- Helper functions starting with an underscore (like _overall) are private helper
  functions used inside this file to build specific parts of the report.
"""
from __future__ import annotations


def render_explanation(trace: dict) -> dict:
    """
    Main function called by crop_engine.py.
    
    Parameters:
        trace (dict): A detailed Python dictionary containing all parameters,
                      environmental data, and evaluation results for one crop.
                      
    Returns:
        dict: A dictionary containing 15 formatted narrative sections plus a summary.
    """
    # Build a dictionary where each key represents a report section
    sections = {
        "overallRecommendation": _overall(trace),
        "climateSuitability": _climate(trace),
        "rainfallAnalysis": _rainfall(trace),
        "temperatureSuitability": _temperature(trace),
        "soilCompatibility": _soil(trace),
        "waterAvailability": _water(trace),
        "irrigationEffect": _irrigation(trace),
        "seasonCompatibility": _season(trace),
        "cropRotationEffect": _rotation(trace),
        "diseaseStressRisks": _disease(trace),
        "marketInformation": _market(trace),
        "profitability": _profit(trace),
        "confidenceAnalysis": _confidence(trace),
        "riskAnalysis": _risk_narrative(trace),
        "finalRecommendation": _final(trace),
        "farmerSummary": _farmer_summary(trace),
    }
    return sections


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _suit_word(s: int) -> str:
    if s >= 75: return "highly suitable"
    if s >= 60: return "suitable"
    if s >= 40: return "marginally suitable"
    return "not recommended"


def _risk_word(level: str) -> str:
    return {"safe": "low", "moderate": "moderate", "high": "significant"}.get(level, level)


def _season_label(s: str) -> str:
    return {"kharif": "Kharif (monsoon)", "rabi": "Rabi (winter)", "summer": "Summer"}.get(s, s.title())


def _join_list(items: list[str]) -> str:
    if not items: return ""
    if len(items) == 1: return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


# ---------------------------------------------------------------------------
# Section renderers — each returns {"title": str, "text": str}
# ---------------------------------------------------------------------------

def _overall(t: dict) -> dict:
    agg, crop = t["aggregation"], t["crop"]
    s = agg["suitability"]
    name = crop["name"]

    if s >= 75:
        verdict = f"{name} is a **strong choice** for this district under the selected conditions."
        detail = "The soil, water supply, and climate are closely aligned with what this crop needs to thrive."
    elif s >= 60:
        verdict = f"{name} is a **suitable crop** for this district, though some conditions are not ideal."
        detail = "Overall growing conditions support this crop, but attention should be paid to the factors highlighted below."
    elif s >= 40:
        verdict = f"{name} can be grown in this district, but it **carries notable risks**."
        detail = "One or more growing conditions fall short of what this crop ideally requires. Active management will be needed."
    else:
        verdict = f"{name} is **not recommended** for this district under these conditions."
        detail = "The growing conditions do not meet this crop's fundamental biological requirements."

    # Identify the main reason
    reason = _primary_reason(t)
    text = f"{verdict} {detail} {reason}"
    return {"title": "Overall Recommendation", "text": text}


def _primary_reason(t: dict) -> str:
    agg = t["aggregation"]
    season = t["season"]
    water = t["water"]

    if water["isInfeasible"]:
        return "The available water supply is critically insufficient for this crop to survive."
    if not season["matched"]:
        crop_seasons = _join_list([_season_label(s) for s in season["cropSeasons"]])
        return f"Note that this crop is traditionally grown during {crop_seasons}, and the selected season differs from its natural cycle."
    if agg["limitingFactorName"] == "Water" and agg["waterRisk"] > 30:
        return "Water availability is the primary concern — the crop's water needs are not fully met."
    if agg["limitingFactorName"] == "Climate" and agg["climateRisk"] > 30:
        return "Climate conditions — particularly rainfall distribution — are the main limiting factor."
    if agg["soilRisk"] > 30:
        return "Soil conditions present challenges that may reduce the crop's performance."
    return ""


def _climate(t: dict) -> dict:
    cl, crop, agg = t["climate"], t["crop"], t["aggregation"]
    name = crop["name"]
    zone = t["zone"]["districtZone"]
    annual = cl["annualRainfall"]
    cv = cl["rainfallCV"]

    parts = [f"This district falls within the **{zone}** agro-climatic zone and receives an average annual rainfall of approximately **{annual} mm**."]

    if cv < 20:
        parts.append("Rainfall patterns are consistent across years, which makes water planning more reliable.")
    elif cv <= 30:
        parts.append("Rainfall variability across years is moderate, meaning seasonal water availability is reasonably predictable.")
    else:
        parts.append("Rainfall is highly variable from year to year, which introduces uncertainty in water planning.")

    cr = agg["climateRisk"]
    if cr < 15:
        parts.append(f"Overall, the climate conditions are well suited for {name} cultivation.")
    elif cr < 35:
        parts.append(f"Climate conditions are acceptable for {name}, though not ideal — the crop can be successfully grown with proper management.")
    elif cr < 60:
        parts.append(f"The climate presents moderate challenges for {name}. Growers should monitor weather conditions closely.")
    else:
        parts.append(f"The climate poses serious difficulties for {name}. This crop is not well-adapted to these conditions.")

    return {"title": "Climate Analysis", "text": " ".join(parts)}


def _rainfall(t: dict) -> dict:
    cl = t["climate"]
    season = cl["season"]
    raw_rain = cl["rawSeasonalRainfall"]
    share_pct = round(cl["seasonalRainfallShare"] * 100)
    eff = cl["effectiveRainfall"]
    texture = cl["soilTexture"]
    dry_pct = cl["drySpellPct"]

    parts = [
        f"{_season_label(season)} accounts for approximately **{share_pct}%** of the district's total annual rainfall, which translates to roughly **{raw_rain} mm** of seasonal rain.",
        f"After accounting for runoff and evaporation losses on {texture}-textured soil, the effective rainfall available to the crop is approximately **{eff} mm**.",
    ]

    if dry_pct < 10:
        parts.append("The probability of prolonged dry spells during this season is low, which is favourable for consistent crop growth.")
    elif dry_pct < 25:
        parts.append(f"There is a moderate chance ({dry_pct}%) of dry spells occurring during the growing period, which could temporarily stress the crop.")
    else:
        parts.append(f"There is a significant chance ({dry_pct}%) of prolonged dry spells, which increases the risk of crop water stress.")

    flood = cl["floodLevel"]
    if flood == "low":
        parts.append("Flood risk during this season is low.")
    elif flood == "medium":
        parts.append("There is a moderate flood risk, which could cause temporary waterlogging.")
    else:
        parts.append("Flood risk is high — heavy rains could submerge fields and damage the crop.")

    return {"title": "Rainfall Analysis", "text": " ".join(parts)}


def _temperature(t: dict) -> dict:
    cl, crop, agg = t["climate"], t["crop"], t["aggregation"]
    temp = cl["seasonalTemp"]
    name = crop["name"]
    heat = crop["heatThreshold"]
    cold = crop["coldThreshold"]

    parts = [f"The average temperature during the growing season is **{temp}°C**."]

    if agg["tempRisk"] == 0:
        parts.append(f"{name} grows comfortably between {cold}°C and {heat}°C. At {temp}°C, temperatures are well within the preferred range, and no heat or cold stress is expected.")
        parts.append("Temperature is not a limiting factor for this crop in this district.")
    elif temp > heat:
        diff = round(temp - heat, 1)
        parts.append(f"{name} begins to experience heat stress above {heat}°C. The local temperature exceeds this threshold by {diff}°C, which can reduce flowering, pollination, and overall yields.")
        parts.append("Heat management strategies such as mulching or adjusted planting dates may help mitigate this.")
    else:
        diff = round(cold - temp, 1)
        parts.append(f"{name} is sensitive to cold below {cold}°C. The local temperature falls {diff}°C below this threshold, which may slow growth, delay maturation, or damage the crop.")

    return {"title": "Temperature Analysis", "text": " ".join(parts)}


def _soil(t: dict) -> dict:
    soil = t["soil"]
    soil_type = soil["soilType"]
    drainage = soil["soilDrainage"]
    texture = soil["soilTexture"]
    n_risk = soil["nitrogenRisk"]
    wl_risk = soil["waterlogRisk"]
    prev = soil["previousCrop"]
    recs = soil.get("recommendations", [])

    parts = [f"The predominant soil type in this district is **{soil_type}** with **{drainage.lower()} drainage** and a {texture} texture."]

    if wl_risk == "low":
        parts.append("The soil drains well, which reduces the risk of waterlogging and root diseases.")
    elif wl_risk == "medium":
        parts.append("Drainage is moderate — during periods of heavy rainfall or irrigation, temporary waterlogging is possible.")
    else:
        parts.append("Poor drainage increases the risk of waterlogging, which can suffocate roots and promote fungal diseases.")

    if n_risk == "low":
        parts.append("Nitrogen levels in the soil are stable, and no significant nutrient depletion concerns were identified.")
    elif n_risk == "moderate":
        if prev and prev != "None":
            parts.append(f"Because the previous crop ({prev}) was a heavy nitrogen feeder, there is a moderate risk of nitrogen depletion. Supplemental fertilisation is recommended.")
        else:
            parts.append("There is a moderate risk of nitrogen depletion. Supplemental fertilisation may be beneficial.")

    if recs:
        rec_text = " ".join(recs)
        parts.append(f"**Soil management recommendation:** {rec_text}")

    return {"title": "Soil Analysis", "text": " ".join(parts)}


def _water(t: dict) -> dict:
    w = t["water"]
    name = w["cropName"]
    wmin, wmid, wmax = w["cropWaterMin"], w["cropWaterMid"], w["cropWaterMax"]
    supply = w["totalEffectiveSupply"]

    parts = [f"{name} requires between **{wmin} mm and {wmax} mm** of water across its growing period, with an optimal requirement around **{round(wmid)} mm**."]

    if w["isInfeasible"]:
        parts.append(f"The total available water supply is only **{supply} mm**, which falls critically below the minimum biological requirement of **{wmin} mm**. {name} cannot survive under these conditions — it is biologically infeasible.")
    elif w["deficit"] > 0:
        deficit = w["deficit"]
        parts.append(f"The total available water supply is approximately **{supply} mm**, which creates a shortfall of about **{deficit} mm** compared to the optimal requirement.")
        if w.get("severeDeficit"):
            parts.append("This is a severe water deficit that will significantly impact yields.")
        else:
            parts.append("This deficit can be partially managed through efficient irrigation scheduling and water conservation practices.")
    else:
        surplus = round(w["surplus"])
        parts.append(f"The total available water supply is approximately **{supply} mm**, providing a comfortable surplus of over **{surplus} mm** above the optimal requirement. Water supply is more than adequate — {name} will not face water stress under these conditions.")

    return {"title": "Water Availability", "text": " ".join(parts)}


def _irrigation(t: dict) -> dict:
    w = t["water"]
    irr_type = w["irrigationType"]
    eff_rain = w["effectiveRainfall"]

    if w["rainfedMode"]:
        parts = [
            f"Under **rainfed** conditions, the crop relies entirely on natural rainfall.",
            f"The effective seasonal rainfall available is approximately **{eff_rain} mm**.",
            "No supplemental irrigation water is provided. The crop's success depends entirely on the timing and quantity of rainfall during the growing season.",
        ]
    else:
        irr_base = w["irrigationBase"]
        rain_contrib = w["rainfallContribution"]
        supply = w["totalEffectiveSupply"]
        parts = [
            f"With **{irr_type} irrigation**, the system provides an estimated base water supply of **{irr_base} mm**, supplemented by approximately **{rain_contrib} mm** from captured rainfall.",
            f"This brings the total available water to approximately **{supply} mm**.",
        ]
        if w["deficit"] > 0:
            parts.append(f"Despite irrigation support, there remains a water shortfall. Farmers should ensure consistent {irr_type} operation during peak growth stages and consider water-saving techniques.")
        else:
            parts.append(f"The {irr_type} supply comfortably meets the crop's water requirements. Farmers should maintain consistent operation during peak growth stages.")

    return {"title": "Irrigation Impact", "text": " ".join(parts)}


def _season(t: dict) -> dict:
    s = t["season"]
    selected = _season_label(s["selectedSeason"])
    name = s["cropName"]
    natural = _join_list([_season_label(ss) for ss in s["cropSeasons"]])

    if s["matched"]:
        text = (
            f"{name} is naturally adapted to the **{selected}** season, which matches the selected planting period. "
            f"The crop's growth cycle, water needs, and temperature preferences align well with the conditions during this season."
        )
    else:
        text = (
            f"{name} is traditionally grown during **{natural}**. "
            f"The selected season ({selected}) does not match the crop's natural growing cycle. "
            f"While the agronomic conditions may still permit cultivation with adequate irrigation and management, "
            f"growers should be aware that the crop may face challenges not present during its natural season — "
            f"including potentially different pest pressure cycles and market timing."
        )

    return {"title": "Season Compatibility", "text": text}


def _rotation(t: dict) -> dict:
    rot = t["rotation"]
    current = rot["currentCrop"]
    family = rot["currentCropFamily"]
    good_pred = rot.get("goodPredecessors", [])

    if rot["previousCrop"] == "None":
        ideal = ""
        if good_pred:
            ideal_families = _join_list(good_pred)
            ideal = f" Ideally, {current} should follow a crop from the {ideal_families} family, which would naturally replenish soil nutrients and break pest cycles."
        text = f"No previous crop was specified for this analysis. {current} belongs to the **{family}** family.{ideal}"
    elif rot["conflict"]:
        text = (
            f"The previous crop ({rot['previousCrop']}, {rot['previousCropFamily']} family) is a poor predecessor for {current} ({family} family). "
            f"Growing crops from the same or related families in succession depletes specific soil nutrients and increases the risk of pest and disease carry-over. "
            f"This rotation choice may reduce soil health and yields over time."
        )
    elif rot["beneficial"]:
        text = (
            f"The previous crop ({rot['previousCrop']}, {rot['previousCropFamily']} family) is an excellent predecessor for {current}. "
            f"This rotation naturally improves soil fertility — particularly nitrogen levels — and helps break pest cycles, creating favourable conditions for the current crop."
        )
    else:
        text = (
            f"The previous crop ({rot['previousCrop']}, {rot['previousCropFamily']} family) has a neutral relationship with {current} ({family} family). "
            f"No negative rotation effects are expected."
        )

    return {"title": "Crop Rotation", "text": text}


def _disease(t: dict) -> dict:
    rot, soil, cl = t["rotation"], t["soil"], t["climate"]
    concerns = []

    if rot["conflict"]:
        concerns.append(
            f"Because {rot['currentCrop']} follows a related crop ({rot['previousCrop']}), there is an increased risk of soil-borne diseases and pest carry-over."
        )
    if soil["waterlogRisk"] != "low":
        concerns.append(
            f"The soil's {soil['soilDrainage'].lower()} drainage increases the chance of waterlogging during heavy rain or irrigation, which promotes root rot and fungal infections."
        )
    if cl["floodLevel"] != "low":
        level = "moderate" if cl["floodLevel"] == "medium" else "significant"
        concerns.append(f"There is a {level} flood risk during this season, which could submerge fields and create conditions for disease outbreaks.")

    if not t["season"]["matched"]:
        concerns.append(
            f"Growing {t['season']['cropName']} outside its natural season may expose it to different pest populations. Consult local Krishi Vigyan Kendra (KVK) advisories for current pest forecasts."
        )

    if not concerns:
        text = (
            "Based on the current conditions — good soil drainage, low flood risk, and no rotation conflicts — "
            "the risk of disease and environmental stress is minimal. Standard crop protection practices should be sufficient."
        )
    else:
        text = " ".join(concerns)

    return {"title": "Disease & Environmental Risks", "text": text}


def _market(t: dict) -> dict:
    m = t["market"]
    name = m["cropName"]
    vol = m["volatility"]

    if vol == "low":
        parts = [f"{name} has **stable market prices**, meaning price fluctuations are relatively small and predictable."]
    elif vol == "medium":
        parts = [f"{name} has **moderate price volatility** — prices can fluctuate based on seasonal supply and demand."]
    else:
        parts = [f"{name} has **high price volatility**, meaning market prices can swing significantly. This introduces financial uncertainty."]

    if m["mspCovered"]:
        parts.append(
            f"The Government of India provides a **Minimum Support Price (MSP) of ₹{m['mspPrice']:,} per quintal** ({m['mspYear']}), "
            f"which guarantees a price floor and significantly reduces the financial risk of cultivation."
        )
    else:
        parts.append("This crop is **not covered by Government MSP**, meaning returns depend entirely on open market prices. Growers should monitor market conditions and consider forward contracts where available.")

    return {"title": "Market Analysis", "text": " ".join(parts)}


def _profit(t: dict) -> dict:
    m = t["market"]
    name = m["cropName"]
    level = m["profitLevel"]

    if level == "High":
        text = (
            f"Based on {name}'s yield potential, current market prices, and input costs, the estimated profit outlook is **High**. "
            f"This crop offers a strong return on investment under current market conditions."
        )
    elif level == "Medium":
        text = (
            f"Based on {name}'s yield potential, current market prices, and input costs, the estimated profit outlook is **Medium**. "
            f"Returns are expected to be moderate and stable. Growers aiming for above-average profits should focus on quality production and timely harvesting."
        )
    else:
        text = (
            f"Based on {name}'s yield potential, current market prices, and input costs, the estimated profit outlook is **Low**. "
            f"High input costs or lower market prices may squeeze margins. Careful cost management is essential."
        )

    if m["mspCovered"]:
        text += f" The MSP guarantee of ₹{m['mspPrice']:,}/qtl provides a safety net against adverse price movements."

    return {"title": "Profit Expectations", "text": text}


def _confidence(t: dict) -> dict:
    conf = t["confidence"]
    level = conf["level"]
    cv = conf["rainfallCV"]

    if level == "High":
        text = (
            f"This recommendation carries **High confidence**. "
            f"The district has comprehensive and reliable agricultural data. "
        )
    elif level == "Moderate":
        text = (
            f"This recommendation carries **Moderate confidence**. "
            f"The available data is adequate but some uncertainty remains. "
        )
    else:
        text = (
            f"This recommendation carries **Low confidence**. "
            f"Data availability or quality for this district is limited, and predictions should be treated with caution. "
        )

    if cv < 20:
        text += f"Rainfall variability is low (CV {cv}%), which means weather patterns are consistent and the analysis is reliable."
    elif cv <= 30:
        text += f"Rainfall variability is moderate (CV {cv}%), meaning weather patterns used in this analysis are reasonably consistent across years."
    else:
        text += f"Rainfall variability is high (CV {cv}%), which means significant year-to-year weather differences can affect actual outcomes."

    return {"title": "Confidence in This Assessment", "text": text}


def _risk_narrative(t: dict) -> dict:
    agg = t["aggregation"]
    factors = []

    if agg["climateRisk"] > 20:
        factors.append("climate conditions (particularly rainfall distribution)")
    if agg["soilRisk"] > 20:
        factors.append("soil health concerns")
    if agg["waterRisk"] > 20:
        factors.append("insufficient water supply")
    if agg["volatilityPenalty"] > 0:
        factors.append("market price instability")
    if not t["season"]["matched"]:
        factors.append("seasonal mismatch")

    if not factors:
        text = "No significant risk factors were identified. The growing conditions across all dimensions — climate, soil, water, and market — are supportive of this crop."
    elif len(factors) == 1:
        text = f"The primary risk factor is **{factors[0]}**. All other growing conditions are favourable. Focused attention on this area should be sufficient to achieve good results."
    else:
        text = f"The main risk factors are: **{_join_list(factors)}**. Growers should develop a management plan that addresses these specific challenges."

    if agg["selectionMode"] == "Limiting Factor":
        lf = agg["limitingFactorName"]
        text += f" In this case, {lf.lower()} conditions are severe enough to be the single dominant constraint on the crop's viability, regardless of how favourable other conditions may be."
    elif agg["selectionMode"] == "Infeasible":
        text += " The water deficit is so severe that the crop cannot biologically survive — this is not a matter of reduced yields but of crop failure."

    return {"title": "Risk Assessment", "text": text}


def _final(t: dict) -> dict:
    agg, crop = t["aggregation"], t["crop"]
    name = crop["name"]
    s = agg["suitability"]
    season = t["season"]
    water = t["water"]
    soil = t["soil"]
    recs = soil.get("recommendations", [])

    if s >= 75:
        text = f"{name} is a **safe and strong choice** for this district. Water supply is adequate, soil conditions are supportive, and temperatures are within the crop's preferred range."
    elif s >= 60:
        text = f"{name} is a **viable choice** for this district. Growing conditions are generally supportive, though some factors require attention."
    elif s >= 40:
        text = f"{name} can be grown with **careful management**, but growers should be prepared to address the challenges identified in this report."
    else:
        text = f"{name} is **not advisable** under these conditions. The fundamental growing requirements are not met, and attempting cultivation carries a high risk of crop failure or financial loss."

    # Build actionable recommendations
    actions = []
    if not water["rainfedMode"] and water["irrigationType"] != "rainfed":
        actions.append(f"Ensure consistent {water['irrigationType']} operation throughout the growth period.")
    if recs:
        actions.extend(recs)
    if not season["matched"]:
        actions.append("Consult local KVK for off-season pest and disease advisories.")
    if t["rotation"]["conflict"]:
        good = t["rotation"].get("goodPredecessors", [])
        if good:
            actions.append(f"Consider rotating with a {_join_list(good)} family crop in the next cycle.")
    actions.append("Plan harvest timing to align with favourable market windows.")

    if actions:
        text += "\n\n**Recommended actions:**\n" + "\n".join(f"• {a}" for a in actions)

    return {"title": "Final Recommendation", "text": text}


def _farmer_summary(t: dict) -> dict:
    agg, crop = t["aggregation"], t["crop"]
    name = crop["name"]
    s = agg["suitability"]
    conf = t["confidence"]["level"]
    season = t["season"]
    water = t["water"]

    # Build a concise 2-3 sentence summary
    if s >= 75:
        verdict = f"{name} is well suited to this district"
    elif s >= 60:
        verdict = f"{name} can be successfully grown in this district"
    elif s >= 40:
        verdict = f"{name} is possible but challenging in this district"
    else:
        verdict = f"{name} is not recommended for this district"

    # Identify key positives and concerns
    positives = []
    concerns = []

    if agg["climateRisk"] < 25:
        positives.append("climate conditions")
    elif agg["climateRisk"] > 40:
        concerns.append("challenging climate")

    if agg["soilRisk"] < 15:
        positives.append("soil conditions")
    elif agg["soilRisk"] > 30:
        concerns.append("soil health")

    if water["deficit"] == 0:
        positives.append("adequate water supply")
    elif water["isInfeasible"]:
        concerns.append("critically insufficient water")
    else:
        concerns.append("water shortfall")

    if not season["matched"]:
        concerns.append("seasonal mismatch")

    text = verdict
    if positives:
        text += f" — {_join_list(positives)} {'is' if len(positives) == 1 else 'are'} favourable"
    text += "."

    if concerns:
        text += f" The main {'concern is' if len(concerns) == 1 else 'concerns are'} {_join_list(concerns)}."

    text += f" Confidence in this assessment is {conf.lower()}."

    return {"title": "Farmer Summary", "text": text}
