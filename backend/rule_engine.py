"""
AgroRisk Advisor — Rule Engine (v9.0 - Multi-Soil Dominance Edition)
Applies agricultural risk rules to classify crops based on:
  1. Water requirement vs irrigation type + district rainfall
  2. Season suitability
  3. Rainfall adequacy for the district
  4. Soil-site suitability with multi-soil dominance scoring
  5. Crop rotation (previous crop penalty / bonus)
  6. Market volatility risk signal

Sources embedded in crops.json / districts.json / district_soils_v2.json:
  • FAO Irrigation & Drainage Paper 56, Table 5 (crop water needs)
  • IRRI (rice paddy total field water)
  • IMD District Rainfall Monitoring Scheme (avg annual rainfall)
  • ICAR 15-zone agro-climatic classification & crop calendars
  • NBSS-LUP Pub 46 + TNAU Agritech (soil dominance classification)
  • Agmarknet / PIB 2023-24 (market volatility patterns)
"""

import json
import pathlib
from typing import Any
from explanation_generator import generate_full_report

# ---------------------------------------------------------------------------
# Load district soils v2 (multi-soil dominance model)
# ---------------------------------------------------------------------------
_DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
_SOILS_PATH = _DATA_DIR / "district_soils_v2.json"
_AFFINITY_PATH = _DATA_DIR / "zone_crop_affinity.json"
_DISTRICTS_PATH = _DATA_DIR / "districts.json"

DISTRICT_SOILS: dict[str, list[dict]] = {}
if _SOILS_PATH.exists():
    with open(_SOILS_PATH, "r", encoding="utf-8") as _f:
        for _entry in json.load(_f):
            DISTRICT_SOILS[_entry["district_id"]] = _entry["soil_types"]

ZONE_AFFINITY: dict[str, dict[str, str]] = {}
if _AFFINITY_PATH.exists():
    with open(_AFFINITY_PATH, "r", encoding="utf-8") as _f:
        for _entry in json.load(_f):
            ZONE_AFFINITY[_entry["agro_climatic_zone"]] = _entry["affinity_map"]

DISTRICT_ZONES: dict[str, str] = {}
if _DISTRICTS_PATH.exists():
    with open(_DISTRICTS_PATH, "r", encoding="utf-8") as _f:
        for _entry in json.load(_f):
            DISTRICT_ZONES[_entry["id"]] = _entry.get("agro_climatic_zone", "Unknown")

# Dominance weights — reflects probability that a farmer's field matches
# this soil type within the district.
DOMINANCE_WEIGHTS: dict[str, int] = {
    "primary":   100,
    "secondary":  70,
    "minor":      40,
}

AFFINITY_BONUS: dict[str, int] = {
    "high": 20,
    "medium": 12,
    "low": 5,
    "unknown": 0
}


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
IRRIGATION_WATER_CAPACITY: dict[str, int] = {
    "rainfed":  0,      # purely rainfall-dependent
    "canal":    800,    # mm – moderate, seasonal availability
    "borewell": 1400,   # mm – reliable, year-round
}

RISK_THRESHOLDS = {
    "safe":     30,     # total penalty  <=  30  → safe
    "moderate": 60,     # total penalty  <=  60  → moderate
    #                   # total penalty  >   60  → high risk
}

# FAO Efficiency Coefficients by Soil Texture (Infiltration/Runoff)
SOIL_TEXTURE_EFFICIENCY: dict[str, float] = {
    "sand":  0.50,  # high runoff, low retention
    "loam":  0.65,  # balanced infiltration
    "clay":  0.75,  # high retention, low deep percolation
}

# Soil-site suitability matrix – ICAR agro-climatic zone guidelines
# Maps crop categories to their preferred and unsuitable soil textures.
SOIL_SUITABILITY: dict[str, dict] = {
    "rice_paddy":    {"preferred": ["clay"], "unsuitable": ["sand"]},
    "wheat":         {"preferred": ["loam", "clay"], "unsuitable": ["sand"]},
    "maize":         {"preferred": ["loam"], "unsuitable": []},
    "sorghum":       {"preferred": ["loam", "clay"], "unsuitable": []},
    "pearl_millet":  {"preferred": ["sand", "loam"], "unsuitable": ["clay"]},
    "finger_millet": {"preferred": ["loam"], "unsuitable": []},
    "groundnut":     {"preferred": ["loam", "sand"], "unsuitable": ["clay"]},
    "sesame":        {"preferred": ["loam"], "unsuitable": ["clay"]},
    "sunflower":     {"preferred": ["loam", "clay"], "unsuitable": []},
    "cotton":        {"preferred": ["clay", "loam"], "unsuitable": ["sand"]},
    "sugarcane":     {"preferred": ["loam", "clay"], "unsuitable": ["sand"]},
    "black_gram":    {"preferred": ["loam"], "unsuitable": []},
    "green_gram":    {"preferred": ["loam", "sand"], "unsuitable": ["clay"]},
    "red_gram":      {"preferred": ["loam"], "unsuitable": ["clay"]},
    "soybean":       {"preferred": ["loam", "clay"], "unsuitable": ["sand"]},
    "tomato":        {"preferred": ["loam"], "unsuitable": []},
    "onion":         {"preferred": ["loam"], "unsuitable": ["clay"]},
    "chilli":        {"preferred": ["loam"], "unsuitable": []},
    "banana":        {"preferred": ["loam", "clay"], "unsuitable": ["sand"]},
    "potato":        {"preferred": ["loam", "sand"], "unsuitable": ["clay"]},
    "turmeric":      {"preferred": ["loam", "clay"], "unsuitable": ["sand"]},
    "coconut":       {"preferred": ["loam", "sand"], "unsuitable": []},
}


# ---------------------------------------------------------------------------
# Individual rule evaluators
# ---------------------------------------------------------------------------
def _get_effective_seasonal_rainfall(
    district_rainfall: int,
    seasonal_share: float,
    soil_texture: str,
) -> int:
    """
    Calculate effective seasonal rainfall accounting for:
    1. Seasonal share of annual rainfall (IMD seasonal distribution)
    2. Soil texture infiltration efficiency (FAO coefficients)
    """
    raw_seasonal = district_rainfall * seasonal_share
    efficiency = SOIL_TEXTURE_EFFICIENCY.get(soil_texture, 0.65)
    return int(raw_seasonal * efficiency)


def _evaluate_water_rule(
    crop: dict[str, Any],
    irrigation: str,
    district_rainfall: int,
    seasonal_share: float = 0.33,
    soil_texture: str = "loam",
) -> tuple[int, list[str]]:
    """
    Compare crop water need against the effective SEASONAL water supply.

    Critical Fix (v8.0): Uses seasonal rainfall share instead of annual
    average to prevent overestimation of water availability.

    For rainfed: supply = effective seasonal rainfall (IMD × season share × FAO soil factor).
    For canal/borewell: supply = irrigation capacity + fraction of effective seasonal rainfall.
    Crop water need is the midpoint of the FAO min-max range.
    """

    # --- Resolve crop water need (FAO Table 5 midpoint) ---
    wmin = crop.get("water_need_mm_min", 0)
    wmax = crop.get("water_need_mm_max", 0)
    water_need = (wmin + wmax) // 2 if (wmin and wmax) else 500

    # --- Resolve effective seasonal supply ---
    effective_rain = _get_effective_seasonal_rainfall(
        district_rainfall, seasonal_share, soil_texture
    )
    irrig_cap = IRRIGATION_WATER_CAPACITY.get(irrigation, 0)

    if irrigation == "rainfed":
        effective_supply = effective_rain
    else:
        # Irrigation capacity + 80% of effective seasonal rainfall
        effective_supply = irrig_cap + int(effective_rain * 0.8)

    reasons: list[str] = []
    deficit_ratio = (water_need - effective_supply) / max(water_need, 1)

    if deficit_ratio > 0.5:
        penalty = 40
        reasons.append(
            f"⚠ Severe water deficit: crop needs ~{water_need} mm (FAO range "
            f"{wmin}–{wmax} mm) but seasonal {irrigation} supply ≈ {effective_supply} mm"
        )
    elif deficit_ratio > 0.2:
        penalty = 20
        reasons.append(
            f"⚠ Moderate water gap: crop needs ~{water_need} mm; "
            f"seasonal {irrigation} supply ≈ {effective_supply} mm"
        )
    elif deficit_ratio <= 0:
        penalty = 0
        reasons.append(
            f"✅ Water supply adequate: seasonal {irrigation} provides "
            f"≈ {effective_supply} mm for a {water_need} mm requirement"
        )
    else:
        penalty = 10
        reasons.append(
            f"✅ Slight water gap but manageable: needs ~{water_need} mm, "
            f"seasonal supply ≈ {effective_supply} mm"
        )

    return penalty, reasons


def _evaluate_season_rule(
    crop: dict[str, Any],
    season: str,
) -> tuple[int, list[str]]:
    """Check if the crop is suitable for the selected season (ICAR calendar)."""

    suitable_seasons = [s.lower() for s in crop.get("seasons", [])]
    reasons: list[str] = []

    if season.lower() in suitable_seasons:
        reasons.append(
            f"✅ {crop['name']} is recommended for {season} season (ICAR calendar)"
        )
        return 0, reasons
    else:
        reasons.append(
            f"⚠ {crop['name']} is not recommended for {season} season "
            f"(suited for: {', '.join(suitable_seasons)})"
        )
        return 35, reasons


def _evaluate_rainfall_adequacy(
    crop: dict[str, Any],
    district_rainfall: int,
    rainfall_variability: str,
    seasonal_share: float = 0.33,
    soil_texture: str = "loam",
) -> tuple[int, list[str]]:
    """
    Assess whether the district's SEASONAL rainfall (IMD) is adequate
    for the crop and factor in rainfall variability.

    Critical Fix (v8.0): Uses seasonal rainfall share for accurate
    season-specific adequacy assessment.
    """

    wmin = crop.get("water_need_mm_min", 0)
    water_req_label = crop.get("water_requirement", "medium")
    seasonal_rainfall = _get_effective_seasonal_rainfall(
        district_rainfall, seasonal_share, soil_texture
    )
    reasons: list[str] = []
    penalty = 0

    # High-variability districts get extra penalty for water-intensive crops
    variability_penalty = 0
    if rainfall_variability == "high" and water_req_label == "high":
        variability_penalty = 10
        reasons.append(
            f"⚠ District has high rainfall variability (IMD) — risky for "
            f"high-water crops"
        )
    elif rainfall_variability == "high" and water_req_label == "medium":
        variability_penalty = 5
        reasons.append(
            f"ℹ District has high rainfall variability — moderate concern "
            f"for {crop['name']}"
        )

    # Check if seasonal effective rainfall meets minimum crop needs
    if seasonal_rainfall >= wmin:
        reasons.append(
            f"✅ Seasonal effective rainfall ({seasonal_rainfall} mm, IMD) "
            f"meets crop's minimum water need ({wmin} mm)"
        )
    else:
        shortfall_pct = ((wmin - seasonal_rainfall) / max(wmin, 1)) * 100
        if shortfall_pct > 50:
            penalty = 15
            reasons.append(
                f"⚠ Seasonal effective rainfall ({seasonal_rainfall} mm) is "
                f"well below crop's minimum need ({wmin} mm) — "
                f"irrigation strongly recommended"
            )
        else:
            penalty = 5
            reasons.append(
                f"ℹ Seasonal effective rainfall ({seasonal_rainfall} mm) is "
                f"below crop minimum ({wmin} mm) — supplemental "
                f"irrigation advisable"
            )

    return penalty + variability_penalty, reasons


def _evaluate_soil_rule(
    crop: dict[str, Any],
    soil_texture: str,
    district_soils: list[dict] | None = None,
) -> tuple[int, list[str]]:
    """
    Evaluate soil-site suitability using the multi-soil dominance model.

    If district_soils (from district_soils_v2.json) is available, evaluates
    the crop against ALL soil types in the district, weighted by dominance:
        Primary   = 100 (most likely farmer soil)
        Secondary =  70
        Minor     =  40

    The best-matching soil (highest weighted suitability) determines the
    final penalty. This prevents a single collapsed texture from hiding
    suitable sub-regions within a district.

    Falls back to legacy single-texture evaluation if district_soils
    is not available.
    """
    crop_id = crop.get("id", "")
    soil_prefs = SOIL_SUITABILITY.get(crop_id, {})
    preferred = soil_prefs.get("preferred", [])
    unsuitable = soil_prefs.get("unsuitable", [])
    reasons: list[str] = []

    # --- Multi-soil dominance evaluation ---
    if district_soils:
        best_score = -999
        best_soil = None
        best_dominance = "unknown"

        for soil_entry in district_soils:
            texture = soil_entry.get("texture", "loam").lower()
            dominance = soil_entry.get("dominance", "unknown")
            weight = DOMINANCE_WEIGHTS.get(dominance, 0)

            if texture in unsuitable:
                raw_score = -20
            elif texture in preferred:
                raw_score = 5
            else:
                raw_score = 0

            # Weighted score: higher dominance amplifies good/bad match
            weighted = raw_score * (weight / 100)

            if weighted > best_score:
                best_score = weighted
                best_soil = soil_entry
                best_dominance = dominance

        if best_soil:
            soil_name = best_soil.get("type", "Unknown")
            soil_tex = best_soil.get("texture", "loam")

            if best_score > 0:
                penalty = -5
                reasons.append(
                    f"✅ Optimal soil match: {soil_name} ({best_dominance} soil) "
                    f"is well-suited for {crop['name']} (ICAR + NBSS-LUP)"
                )
            elif best_score < -10:
                penalty = 20
                reasons.append(
                    f"⚠ Soil mismatch: {crop['name']} performs poorly in "
                    f"{soil_name} ({best_dominance} soil, {soil_tex} texture)"
                )
            elif best_score < 0:
                penalty = 10
                reasons.append(
                    f"⚠ Partial soil concern: {crop['name']} has limited "
                    f"suitability in {soil_name} ({best_dominance}, {soil_tex})"
                )
            else:
                penalty = 0
                reasons.append(
                    f"ℹ Soil ({soil_name}, {best_dominance}) is acceptable "
                    f"for {crop['name']}"
                )
            return penalty, reasons

    # --- Fallback: legacy single-texture evaluation ---
    texture_lower = soil_texture.lower()

    if texture_lower in unsuitable:
        reasons.append(
            f"⚠ Soil mismatch: {crop['name']} performs poorly in "
            f"{soil_texture} soil (ICAR soil-site suitability criteria)"
        )
        return 20, reasons
    elif texture_lower in preferred:
        reasons.append(
            f"✅ Optimal soil: {soil_texture} soil is well-suited for "
            f"{crop['name']} (ICAR criteria)"
        )
        return -5, reasons
    else:
        reasons.append(
            f"ℹ Soil type ({soil_texture}) is acceptable but not optimal "
            f"for {crop['name']}"
        )
        return 0, reasons


def _evaluate_rotation_rule(
    crop: dict[str, Any],
    previous_crop_id: str | None,
) -> tuple[int, list[str]]:
    """Reward good predecessors and penalise bad ones (ICAR rotation advisories)."""

    if not previous_crop_id:
        return 0, ["ℹ No previous crop specified — rotation rule skipped"]

    reasons: list[str] = []
    penalty = 0

    bad = [c.lower() for c in crop.get("bad_predecessors", [])]
    good = [c.lower() for c in crop.get("good_predecessors", [])]

    prev_label = previous_crop_id.replace("_", " ").title()

    if previous_crop_id.lower() in bad:
        penalty = 25
        reasons.append(
            f"⚠ Poor rotation: planting {crop['name']} after "
            f"{prev_label} increases pest/disease risk (ICAR advisory)"
        )
    elif previous_crop_id.lower() in good:
        penalty = -10  # bonus
        reasons.append(
            f"✅ Excellent rotation: {prev_label} is a recommended "
            f"predecessor for {crop['name']} (ICAR advisory)"
        )
    else:
        reasons.append(
            f"ℹ Neutral rotation: {prev_label} has no specific "
            f"interaction with {crop['name']}"
        )

    return penalty, reasons


def _evaluate_volatility_rule(
    crop: dict[str, Any],
) -> tuple[int, list[str]]:
    """
    Signal market risk based on Agmarknet volatility classification.
    This is an informational flag, not a hard penalty.
    """

    volatility = crop.get("market_volatility", "medium")
    reasons: list[str] = []
    penalty = 0

    if volatility == "high":
        penalty = 5
        reasons.append(
            f"⚠ High market price volatility (Agmarknet 2023-24) — "
            f"consider contract farming or storage"
        )
    elif volatility == "low":
        penalty = 0
        reasons.append(
            f"✅ Stable market prices (Agmarknet) — low financial risk"
        )
    else:
        penalty = 0
        reasons.append(
            f"ℹ Moderate market price variability (Agmarknet)"
        )

    return penalty, reasons


def _evaluate_zone_affinity(
    crop: dict[str, Any],
    district: str,
) -> tuple[int, list[str]]:
    """
    Reward crops officially recommended by TNAU/ICAR for the district's zone.
    """
    crop_id = crop.get("id", "")
    zone = DISTRICT_ZONES.get(district, "Unknown")
    affinity_map = ZONE_AFFINITY.get(zone, {})
    affinity = affinity_map.get(crop_id, "unknown")
    bonus = AFFINITY_BONUS.get(affinity, 0)
    
    reasons: list[str] = []
    
    if bonus > 0:
        reasons.append(
            f"⭐ Zone Affinity: {crop['name']} is a {affinity} affinity crop "
            f"for the {zone} (TNAU/ICAR recommendation, +{bonus} bonus)"
        )
    return -bonus, reasons


# ---------------------------------------------------------------------------
# Main classifier
# ---------------------------------------------------------------------------
def classify_crops(
    crops: list[dict[str, Any]],
    district: str,
    season: str,
    previous_crop: str | None,
    irrigation: str,
    district_rainfall: int = 800,
    rainfall_variability: str = "medium",
    seasonal_rainfall_share: dict[str, float] | None = None,
    soil_texture: str = "loam",
    district_soils: list[dict] | None = None,
) -> list[dict[str, Any]]:
    """
    Run every crop through the rule engine and return a sorted list of
    risk-classified results.

    Parameters
    ----------
    crops : list of crop dicts (from crops.json)
    district : district id
    season : kharif | rabi | summer
    previous_crop : id of the previous crop or None
    irrigation : rainfed | canal | borewell
    district_rainfall : avg annual rainfall in mm (from IMD via districts.json)
    rainfall_variability : low | medium | high (from districts.json)
    seasonal_rainfall_share : dict mapping season → fraction of annual rain
    soil_texture : sand | loam | clay (from districts.json via NBSS-LUP)

    Returns
    -------
    list of dicts sorted by risk level then risk score.
    """

    # Resolve seasonal share for the selected season
    if seasonal_rainfall_share is None:
        seasonal_rainfall_share = {"kharif": 0.40, "rabi": 0.45, "summer": 0.15}
    season_share = seasonal_rainfall_share.get(season.lower(), 0.33)

    results: list[dict[str, Any]] = []

    for crop in crops:
        total_penalty = 0
        all_reasons: list[str] = []

        resolved_district_soils = district_soils or DISTRICT_SOILS.get(district)
        
        water_pen, water_res = _evaluate_water_rule(crop, irrigation, district_rainfall, season_share, soil_texture)
        season_pen, season_res = _evaluate_season_rule(crop, season)
        rain_pen, rain_res = _evaluate_rainfall_adequacy(crop, district_rainfall, rainfall_variability, season_share, soil_texture)
        soil_pen, soil_res = _evaluate_soil_rule(crop, soil_texture, resolved_district_soils)
        rot_pen, rot_res = _evaluate_rotation_rule(crop, previous_crop)
        vol_pen, vol_res = _evaluate_volatility_rule(crop)
        zone_pen, zone_res = _evaluate_zone_affinity(crop, district)
        
        total_penalty = water_pen + season_pen + rain_pen + soil_pen + rot_pen + vol_pen + zone_pen
        all_reasons = water_res + season_res + rain_res + soil_res + rot_res + vol_res + zone_res
        
        penalties = {
            "water": water_pen,
            "season": season_pen,
            "rainfall": rain_pen,
            "soil": soil_pen,
            "rotation": rot_pen,
            "volatility": vol_pen,
            "zone": zone_pen
        }
        
        eff_rain = _get_effective_seasonal_rainfall(district_rainfall, season_share, soil_texture)
        
        # Determine the best soil for explanation (matching the logic in _evaluate_soil_rule)
        best_soil = None
        if resolved_district_soils:
            best_score = -999
            crop_id = crop.get("id", "")
            soil_prefs = SOIL_SUITABILITY.get(crop_id, {})
            preferred = soil_prefs.get("preferred", [])
            unsuitable = soil_prefs.get("unsuitable", [])
            
            for soil_entry in resolved_district_soils:
                texture = soil_entry.get("texture", "loam").lower()
                dominance = soil_entry.get("dominance", "unknown")
                weight = DOMINANCE_WEIGHTS.get(dominance, 0)
                if texture in unsuitable:
                    raw_score = -20
                elif texture in preferred:
                    raw_score = 5
                else:
                    raw_score = 0
                weighted = raw_score * (weight / 100)
                if weighted > best_score:
                    best_score = weighted
                    best_soil = soil_entry
                    
        zone_name = DISTRICT_ZONES.get(district, "Unknown")
        report = generate_full_report(
            crop, district, season, previous_crop, irrigation, 
            district_rainfall, season_share, soil_texture, 
            resolved_district_soils, zone_name, penalties, 
            total_penalty, eff_rain, best_soil
        )

        # Clamp to zero
        total_penalty = max(total_penalty, 0)

        # Determine risk level
        if total_penalty <= RISK_THRESHOLDS["safe"]:
            risk_level = "safe"
        elif total_penalty <= RISK_THRESHOLDS["moderate"]:
            risk_level = "moderate"
        else:
            risk_level = "high"

        # Build growth duration display
        gmin = crop.get("growth_duration_days_min", 0)
        gmax = crop.get("growth_duration_days_max", 0)
        growth_display = f"{gmin}–{gmax}" if gmin != gmax else str(gmin)

        results.append(
            {
                "crop_id":           crop["id"],
                "crop_name":         crop["name"],
                "category":          crop.get("category", ""),
                "description":       crop.get("description", ""),
                "growth_days":       growth_display,
                "water_requirement": crop.get("water_requirement", ""),
                "water_need_mm":     f"{crop.get('water_need_mm_min', 0)}–{crop.get('water_need_mm_max', 0)}",
                "market_volatility": crop.get("market_volatility", ""),
                "rotation_sensitive": crop.get("rotation_sensitive", False),
                "risk_level":        risk_level,
                "risk_score":        total_penalty,
                "reasons":           all_reasons,
                "explanation":       report,
            }
        )

    # Sort: safe first, then moderate, then high; within same level by score
    level_order = {"safe": 0, "moderate": 1, "high": 2}
    results.sort(key=lambda r: (level_order.get(r["risk_level"], 3), r["risk_score"]))

    return results
