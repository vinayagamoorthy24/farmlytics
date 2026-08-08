import json
import random
import pathlib
import sys
from collections import defaultdict

BASE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from rule_engine import (
    _evaluate_water_rule,
    _evaluate_season_rule,
    _evaluate_rainfall_adequacy,
    _evaluate_soil_rule,
    _evaluate_rotation_rule,
    _evaluate_volatility_rule,
    RISK_THRESHOLDS
)

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as fh:
        return json.load(fh)

DATA_DIR = BASE_DIR.parent / "data"
CROPS = load_json(DATA_DIR / "crops.json")
DISTRICTS = load_json(DATA_DIR / "districts.json")

# Extract inputs
seasons = ["kharif", "rabi", "summer"]
irrigations = ["rainfed", "canal", "borewell"]
crop_ids = [c["id"] for c in CROPS]

random.seed(42)

# Generate 150 combinations
combinations = []
for _ in range(150):
    combinations.append({
        "district": random.choice(DISTRICTS),
        "season": random.choice(seasons),
        "irrigation": random.choice(irrigations),
        "previous_crop": random.choice([None] + crop_ids)
    })

results_log = []

score_distributions = {
    "water": [],
    "season": [],
    "rainfall_adequacy": [],
    "soil": [],
    "rotation": [],
    "volatility": [],
    "total": []
}

risk_level_counts = {"safe": 0, "moderate": 0, "high": 0}

for combo in combinations:
    dist = combo["district"]
    season = combo["season"]
    irrig = combo["irrigation"]
    prev_crop = combo["previous_crop"]
    
    district_rainfall = dist.get("avg_annual_rainfall_mm", 800)
    rainfall_var = dist.get("rainfall_variability", "medium")
    seasonal_shares = dist.get("seasonal_rainfall_share", {"kharif": 0.40, "rabi": 0.45, "summer": 0.15})
    season_share = seasonal_shares.get(season, 0.33)
    soil_texture = dist.get("soil_texture", "loam")
    
    combo_results = []
    
    for crop in CROPS:
        water_pen, water_reasons = _evaluate_water_rule(crop, irrig, district_rainfall, season_share, soil_texture)
        season_pen, season_reasons = _evaluate_season_rule(crop, season)
        rain_pen, rain_reasons = _evaluate_rainfall_adequacy(crop, district_rainfall, rainfall_var, season_share, soil_texture)
        soil_pen, soil_reasons = _evaluate_soil_rule(crop, soil_texture)
        rot_pen, rot_reasons = _evaluate_rotation_rule(crop, prev_crop)
        vol_pen, vol_reasons = _evaluate_volatility_rule(crop)
        
        total = water_pen + season_pen + rain_pen + soil_pen + rot_pen + vol_pen
        total = max(total, 0)
        
        score_distributions["water"].append(water_pen)
        score_distributions["season"].append(season_pen)
        score_distributions["rainfall_adequacy"].append(rain_pen)
        score_distributions["soil"].append(soil_pen)
        score_distributions["rotation"].append(rot_pen)
        score_distributions["volatility"].append(vol_pen)
        score_distributions["total"].append(total)
        
        if total <= RISK_THRESHOLDS["safe"]:
            risk = "safe"
        elif total <= RISK_THRESHOLDS["moderate"]:
            risk = "moderate"
        else:
            risk = "high"
            
        risk_level_counts[risk] += 1
            
        combo_results.append({
            "crop": crop["name"],
            "total": total,
            "risk": risk,
            "breakdown": {
                "water": water_pen,
                "season": season_pen,
                "rain": rain_pen,
                "soil": soil_pen,
                "rotation": rot_pen,
                "market": vol_pen
            },
            "reasons": water_reasons + season_reasons + rain_reasons + soil_reasons + rot_reasons + vol_reasons
        })
        
    combo_results.sort(key=lambda x: x["total"])
    
    results_log.append({
        "combo": combo,
        "top_5": combo_results[:5],
        "bottom_5": combo_results[-5:]
    })

# Write rule_engine_analysis.md
def avg(lst): return sum(lst) / max(len(lst), 1)

with open(DATA_DIR / "rule_engine_analysis.md", "w", encoding="utf-8") as f:
    f.write("# Rule Engine Analysis\n\n")
    f.write("## Experiment Setup\n")
    f.write("- 150 combinations of District, Season, Irrigation, and Previous Crop.\n")
    f.write(f"- Total evaluations: {150 * len(CROPS)}\n\n")
    
    f.write("## Score Distributions (Average Penalty)\n")
    f.write(f"- Water/Irrigation: {avg(score_distributions['water']):.2f}\n")
    f.write(f"- Season mismatch: {avg(score_distributions['season']):.2f}\n")
    f.write(f"- Rainfall Adequacy: {avg(score_distributions['rainfall_adequacy']):.2f}\n")
    f.write(f"- Soil Mismatch: {avg(score_distributions['soil']):.2f}\n")
    f.write(f"- Rotation: {avg(score_distributions['rotation']):.2f}\n")
    f.write(f"- Market Volatility: {avg(score_distributions['volatility']):.2f}\n")
    f.write(f"- Total Average Penalty: {avg(score_distributions['total']):.2f}\n\n")
    
    f.write("## Risk Classification Spread\n")
    f.write(f"- Safe (<=30): {risk_level_counts['safe']}\n")
    f.write(f"- Moderate (<=60): {risk_level_counts['moderate']}\n")
    f.write(f"- High (>60): {risk_level_counts['high']}\n\n")
    
    f.write("## Identified Problems\n")
    f.write("1. **Irrigation Dominance**: If irrigation is 'canal' or 'borewell', water penalty is 0, which makes high-water crops seem entirely 'safe' even if climate is very dry. The water rule dominates.\n")
    f.write("2. **Season Penalty Too Rigid**: A mismatch in season adds 35 points, which single-handedly forces a crop near 'moderate' or 'high' risk, overriding soil or rotation benefits.\n")
    f.write("3. **Rotation Benefits Minimal**: Rotation gives a -10 bonus, which is easily erased by a slight water gap (+10).\n")
    f.write("4. **Unrealistic Safe Designations**: A crop can be planted out of season (+35) but if water (+0), soil (-5) and rotation (-10) are good, total is 20 (Safe). This is biologically unrealistic since out-of-season crops often fail entirely.\n")

with open(DATA_DIR / "recommendation_quality_report.md", "w", encoding="utf-8") as f:
    f.write("# Recommendation Quality Report\n\n")
    f.write("## Overview of Top Recommendations\n")
    for idx, log in enumerate(results_log[:10]):
        f.write(f"### Test {idx+1}: {log['combo']['district']['district']}, {log['combo']['season']}, {log['combo']['irrigation']}\n")
        for rank, crop in enumerate(log['top_5']):
            f.write(f"{rank+1}. **{crop['crop']}** (Score: {crop['total']}, {crop['risk']})\n")
            f.write(f"   - Breakdown: Water:{crop['breakdown']['water']}, Season:{crop['breakdown']['season']}, Rain:{crop['breakdown']['rain']}, Soil:{crop['breakdown']['soil']}, Rot:{crop['breakdown']['rotation']}, Mkt:{crop['breakdown']['market']}\n")
            f.write(f"   - Ex: {crop['reasons'][0]}\n")
        f.write("\n")

with open(DATA_DIR / "suggested_weight_improvements.md", "w", encoding="utf-8") as f:
    f.write("# Suggested Weight Improvements\n\n")
    f.write("## Current vs Proposed Weights\n\n")
    f.write("| Factor | Current Penalty | Proposed Penalty/Action |\n")
    f.write("|--------|-----------------|-------------------------|\n")
    f.write("| Season Mismatch | +35 | **Veto** (Skip recommendation or +80 to force High Risk) |\n")
    f.write("| Soil Mismatch | +20 | +30 (Poor soil severely impacts yield) |\n")
    f.write("| Water Deficit (>50%) | +40 | +60 (Water deficit is lethal) |\n")
    f.write("| Good Rotation | -10 | -15 (Encourage sustainable practices) |\n")
    f.write("| Bad Rotation | +25 | +25 (Keep as is) |\n")
    f.write("| Market Volatility | +5 | +10 (Economic risk should be more visible) |\n")
    f.write("\n")
    f.write("## Rationale\n")
    f.write("- **Biological constraints (Season/Soil/Water)** should act as hard filters or severe penalties. A crop cannot be 'Safe' if it's planted in the wrong season, no matter how much water is pumped.\n")
    f.write("- **Irrigation offset** should be capped. Just because a farmer has a borewell doesn't mean they should grow water-guzzling crops in an arid region. The rainfall adequacy penalty should be increased for borewell usage in arid zones to reflect groundwater depletion risks.\n")

with open(DATA_DIR / "explanation_improvement_plan.md", "w", encoding="utf-8") as f:
    f.write("# Explanation Improvement Plan\n\n")
    f.write("## Current Issues\n")
    f.write("1. **Repetitive Formatting**: Every reason starts with an emoji (✅, ⚠, ℹ) and uses identical sentence structures.\n")
    f.write("2. **Lack of Synthesized Insights**: The engine outputs 6 disconnected sentences instead of a cohesive paragraph (e.g., 'Despite good soil, severe water scarcity makes this risky').\n")
    f.write("3. **Numeric Clutter**: Excessive display of raw numbers ('needs ~500 mm, supply ≈ 800 mm') can confuse users who just want actionable advice.\n\n")
    f.write("## Proposed Plan\n")
    f.write("1. **Categorized Feedback**: Group reasons into 'Strengths' and 'Risks' rather than a flat list.\n")
    f.write("2. **Dynamic Natural Language Generation**: Use template blending. For example, if both water and soil are poor, combine them: *'This crop is highly vulnerable due to incompatible sandy soils and a 50% water deficit.'*\n")
    f.write("3. **Actionable Mitigations**: Instead of just saying 'Poor rotation', add a mitigation: *'Poor rotation risk: Consider applying neem cake to manage soil-borne pests.'*\n")

print("Analysis complete. Reports generated.")
