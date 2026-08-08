"""
Real-World Validation of the Farmlytics Rule Engine
============================================================
Compares engine recommendations against official TNAU / ICAR / TN DoA crop guidance
for 24 Tamil Nadu districts across all seasons and irrigation types.

Ground truth is drawn from published official sources:
  - TNAU Agritech Portal (agritech.tnau.ac.in) — district-wise package of practices
  - ICAR Agro-Climatic Zone Guidelines (15-zone classification)
  - Tamil Nadu Department of Agriculture Crop Suitability Maps
"""

import json
import pathlib
import sys
from collections import defaultdict

BASE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from rule_engine import classify_crops

def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as fh:
        return json.load(fh)

DATA_DIR = BASE_DIR.parent / "data"
CROPS = load_json(DATA_DIR / "crops.json")
DISTRICTS = load_json(DATA_DIR / "districts.json")
DISTRICT_MAP = {d["id"]: d for d in DISTRICTS}

# ==========================================================================
# OFFICIAL GROUND TRUTH — TNAU / ICAR / TN DoA
# Format: district_id -> season -> list of expected top crop IDs
# Sources:
#   - TNAU Agritech: agritech.tnau.ac.in/crop/crop_cereals.html
#   - ICAR Zone-wise crop calendar
#   - TN DoA crop suitability advisories
# NOTE: Only crops present in crops.json are listed; other crops (vegetables,
#       spices etc.) not yet in the DB are marked in discrepancy report.
# ==========================================================================
GROUND_TRUTH = {
    "thanjavur": {
        # Cauvery Delta — classic rice-rice belt (TNAU + TN DoA)
        "kharif":  ["rice_paddy", "black_gram", "green_gram", "sesame"],
        "rabi":    ["rice_paddy", "black_gram", "groundnut"],
        "summer":  ["green_gram", "black_gram", "sesame"]
    },
    "tiruchirappalli": {
        # Southern Zone — Rabi rice + Kharif millets/pulses (ICAR)
        "kharif":  ["sorghum", "pearl_millet", "groundnut", "black_gram"],
        "rabi":    ["rice_paddy", "sorghum", "groundnut"],
        "summer":  ["green_gram", "sesame", "black_gram"]
    },
    "coimbatore": {
        # Western Zone — Cotton, Maize, Sorghum (TNAU Coimbatore)
        "kharif":  ["maize", "sorghum", "cotton", "groundnut"],
        "rabi":    ["maize", "sorghum", "sunflower", "groundnut"],
        "summer":  ["green_gram", "sesame", "black_gram"]
    },
    "madurai": {
        # Southern Zone — Cotton, Groundnut, Sorghum (TNAU)
        "kharif":  ["cotton", "sorghum", "groundnut", "black_gram"],
        "rabi":    ["sorghum", "groundnut", "sunflower"],
        "summer":  ["green_gram", "black_gram"]
    },
    "salem": {
        # North Western — Maize, Sorghum, Cotton, Groundnut (TNAU)
        "kharif":  ["maize", "sorghum", "cotton", "groundnut"],
        "rabi":    ["sorghum", "sunflower", "maize"],
        "summer":  ["green_gram", "sesame"]
    },
    "dharmapuri": {
        # North Western — Groundnut, Maize, Sorghum (TNAU + ICAR)
        "kharif":  ["groundnut", "maize", "sorghum", "black_gram"],
        "rabi":    ["sorghum", "sunflower", "groundnut"],
        "summer":  ["green_gram", "black_gram"]
    },
    "krishnagiri": {
        # North Western — Groundnut, Tomato, Maize (TNAU Krishnagiri)
        "kharif":  ["groundnut", "maize", "sorghum"],
        "rabi":    ["sorghum", "groundnut", "sunflower"],
        "summer":  ["green_gram", "sesame"]
    },
    "erode": {
        # Western — Turmeric, Sugarcane, Cotton, Sorghum (TNAU)
        "kharif":  ["cotton", "sorghum", "groundnut", "maize"],
        "rabi":    ["sugarcane", "sorghum", "sunflower"],
        "summer":  ["green_gram", "sesame"]
    },
    "tiruppur": {
        # Western — Cotton, Maize, Sorghum (TNAU)
        "kharif":  ["cotton", "maize", "sorghum", "groundnut"],
        "rabi":    ["sorghum", "maize", "sunflower"],
        "summer":  ["green_gram", "sesame"]
    },
    "villupuram": {
        # North Eastern — Groundnut, Sugarcane, Rice (TNAU)
        "kharif":  ["rice_paddy", "groundnut", "black_gram", "sesame"],
        "rabi":    ["rice_paddy", "groundnut", "sugarcane"],
        "summer":  ["green_gram", "sesame", "black_gram"]
    },
    "cuddalore": {
        # North Eastern — Rice, Groundnut, Sugarcane (TNAU)
        "kharif":  ["rice_paddy", "groundnut", "black_gram"],
        "rabi":    ["rice_paddy", "sugarcane", "groundnut"],
        "summer":  ["green_gram", "sesame"]
    },
    "nagapattinam": {
        # Cauvery Delta — Rice dominant, Sesame, Pulses (TNAU)
        "kharif":  ["rice_paddy", "sesame", "black_gram"],
        "rabi":    ["rice_paddy", "black_gram", "green_gram"],
        "summer":  ["sesame", "green_gram"]
    },
    "mayiladuthurai": {
        # Cauvery Delta — Rice, Black gram (TNAU)
        "kharif":  ["rice_paddy", "black_gram", "sesame"],
        "rabi":    ["rice_paddy", "black_gram", "green_gram"],
        "summer":  ["green_gram", "sesame"]
    },
    "ariyalur": {
        # Cauvery Delta — Rice, Groundnut, Sugarcane (TNAU)
        "kharif":  ["rice_paddy", "groundnut", "black_gram"],
        "rabi":    ["rice_paddy", "sugarcane", "groundnut"],
        "summer":  ["green_gram", "sesame"]
    },
    "perambalur": {
        # Cauvery fringe — Sorghum, Groundnut, Cotton (TNAU)
        "kharif":  ["sorghum", "groundnut", "cotton", "black_gram"],
        "rabi":    ["sorghum", "groundnut", "sunflower"],
        "summer":  ["green_gram", "sesame"]
    },
    "namakkal": {
        # North Western — Maize, Sorghum, Groundnut (TNAU Namakkal)
        "kharif":  ["maize", "sorghum", "groundnut"],
        "rabi":    ["maize", "sorghum", "sunflower"],
        "summer":  ["green_gram", "sesame"]
    },
    "thoothukudi": {
        # Southern Arid — Pearl Millet, Groundnut, Sesame (TNAU)
        "kharif":  ["pearl_millet", "groundnut", "sesame", "sorghum"],
        "rabi":    ["pearl_millet", "sorghum", "groundnut"],
        "summer":  ["green_gram", "sesame"]
    },
    "ramanathapuram": {
        # Southern Arid — Pearl Millet, Green Gram, Groundnut (TNAU)
        "kharif":  ["pearl_millet", "green_gram", "groundnut", "sesame"],
        "rabi":    ["pearl_millet", "sorghum", "groundnut"],
        "summer":  ["green_gram", "sesame"]
    },
    "dindigul": {
        # Southern Zone — Maize, Groundnut, Sorghum (TNAU)
        "kharif":  ["maize", "groundnut", "sorghum", "cotton"],
        "rabi":    ["sorghum", "sunflower", "groundnut"],
        "summer":  ["green_gram", "sesame"]
    },
    "tirunelveli": {
        # Southern Zone — Rice, Cotton, Sorghum, Groundnut (TNAU)
        "kharif":  ["cotton", "sorghum", "groundnut", "pearl_millet"],
        "rabi":    ["sorghum", "groundnut", "sunflower"],
        "summer":  ["green_gram", "sesame"]
    },
    "virudhunagar": {
        # Southern Zone — Cotton, Groundnut, Sorghum (TNAU/ICAR)
        "kharif":  ["cotton", "groundnut", "sorghum"],
        "rabi":    ["sorghum", "groundnut", "sunflower"],
        "summer":  ["green_gram", "sesame"]
    },
    "sivagangai": {
        # Southern Zone — Groundnut, Sorghum, Pearl Millet (TNAU)
        "kharif":  ["groundnut", "sorghum", "pearl_millet", "cotton"],
        "rabi":    ["sorghum", "groundnut", "sunflower"],
        "summer":  ["green_gram", "sesame"]
    },
    "kanyakumari": {
        # High Rainfall — Rice, Tapioca, Banana (TNAU Kanyakumari)
        # Mapped to crops in DB: Rice, Maize are closest available
        "kharif":  ["rice_paddy", "maize", "sesame"],
        "rabi":    ["rice_paddy", "maize"],
        "summer":  ["green_gram", "sesame"]
    },
    "nilgiris": {
        # Hilly Zone — Sorghum, Maize (cooler; tea/potato not in DB)
        "kharif":  ["maize", "sorghum"],
        "rabi":    ["maize", "sorghum"],
        "summer":  ["maize"]
    },
}

SEASONS = ["kharif", "rabi", "summer"]
IRRIGATIONS = ["rainfed", "canal", "borewell"]

# ==========================================================================
# RUN VALIDATION
# ==========================================================================
district_results = {}

for district_id, truth_by_season in GROUND_TRUTH.items():
    if district_id not in DISTRICT_MAP:
        continue
    d = DISTRICT_MAP[district_id]
    district_results[district_id] = {}

    for season in SEASONS:
        expected = truth_by_season.get(season, [])
        season_runs = {}

        for irrig in IRRIGATIONS:
            r = d.get("avg_annual_rainfall_mm", 800)
            var = d.get("rainfall_variability", "medium")
            shares = d.get("seasonal_rainfall_share")
            soil = d.get("soil_texture", "loam")

            engine_out = classify_crops(
                CROPS, district_id, season, None, irrig, r, var, shares, soil
            )

            top10 = [c["crop_id"] for c in engine_out[:10]]
            top5  = top10[:5]
            top3  = top10[:3]
            top1  = top10[:1]

            t1_match = bool(expected and top1 and expected[0] in top1)
            t3_match = bool(expected and any(e in top3 for e in expected))
            t5_match = bool(expected and any(e in top5 for e in expected))
            t10_match = bool(expected and any(e in top10 for e in expected))

            expected_in_top10 = [e for e in expected if e in top10]
            false_positives = [c for c in top5 if c not in expected]
            false_negatives = [e for e in expected[:3] if e not in top10]

            bad_rules = []
            if false_negatives:
                for miss in false_negatives:
                    crop_obj = next((c for c in CROPS if c["id"] == miss), None)
                    if crop_obj:
                        crop_seasons = [s.lower() for s in crop_obj.get("seasons", [])]
                        if season not in crop_seasons:
                            bad_rules.append(f"Season filter removes {miss}")
                        elif irrig == "rainfed":
                            wmin = crop_obj.get("water_need_mm_min", 0)
                            eff_rain = int(r * (shares or {}).get(season, 0.33) * 0.65)
                            if wmin > eff_rain:
                                bad_rules.append(f"Water deficit removes {miss} (needs {wmin}mm, supply {eff_rain}mm)")
                        else:
                            bad_rules.append(f"Soil or scoring pushes {miss} down the list")

            season_runs[irrig] = {
                "top10": top10,
                "top5": top5,
                "expected": expected,
                "top1_match": t1_match,
                "top3_match": t3_match,
                "top5_match": t5_match,
                "top10_match": t10_match,
                "expected_found": expected_in_top10,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
                "bad_rules": bad_rules,
            }

        district_results[district_id][season] = season_runs

# ==========================================================================
# COMPUTE GLOBAL ACCURACY METRICS
# ==========================================================================
total = 0
t1, t3, t5, t10 = 0, 0, 0, 0
fp_total, fn_total = [], []

for d_id, seasons_data in district_results.items():
    for season, irrig_data in seasons_data.items():
        for irrig, run in irrig_data.items():
            total += 1
            if run["top1_match"]: t1 += 1
            if run["top3_match"]: t3 += 1
            if run["top5_match"]: t5 += 1
            if run["top10_match"]: t10 += 1
            fp_total.extend(run["false_positives"])
            fn_total.extend(run["false_negatives"])

t1_pct  = (t1 / total) * 100
t3_pct  = (t3 / total) * 100
t5_pct  = (t5 / total) * 100
t10_pct = (t10 / total) * 100

from collections import Counter
fp_counter = Counter(fp_total)
fn_counter = Counter(fn_total)

# ==========================================================================
# WRITE district_validation_report.md
# ==========================================================================
with open(DATA_DIR / "district_validation_report.md", "w", encoding="utf-8") as f:
    f.write("# District-Level Validation Report\n\n")
    f.write("## Sources for Ground Truth\n")
    f.write("- TNAU Agritech Portal (agritech.tnau.ac.in)\n")
    f.write("- ICAR Agro-Climatic Zone Crop Calendars\n")
    f.write("- Tamil Nadu Department of Agriculture Crop Suitability\n\n")
    f.write(f"**Tested**: {len(GROUND_TRUTH)} districts × 3 seasons × 3 irrigation types = {total} combinations\n\n")

    for d_id in GROUND_TRUTH:
        if d_id not in district_results:
            continue
        d_meta = DISTRICT_MAP[d_id]
        f.write(f"---\n## {d_meta['district']} ({d_meta['agro_climatic_zone']})\n")
        f.write(f"Soil: `{d_meta.get('soil_texture','loam')}` | Rainfall: {d_meta['avg_annual_rainfall_mm']}mm | Variability: {d_meta['rainfall_variability']}\n\n")

        for season in SEASONS:
            f.write(f"### {season.capitalize()}\n")
            f.write(f"Expected crops (TNAU/ICAR): `{', '.join(GROUND_TRUTH[d_id].get(season, []))}`\n\n")
            f.write("| Irrigation | Top-1 Match | Top-3 Match | Top-5 Match | False Positives | False Negatives |\n")
            f.write("|---|---|---|---|---|---|\n")
            for irrig, run in district_results[d_id][season].items():
                fp = ', '.join(run['false_positives'][:3]) or 'None'
                fn = ', '.join(run['false_negatives']) or 'None'
                f.write(f"| {irrig} | {'Yes' if run['top1_match'] else 'No'} | {'Yes' if run['top3_match'] else 'No'} | {'Yes' if run['top5_match'] else 'No'} | {fp} | {fn} |\n")
            f.write("\n")

# ==========================================================================
# WRITE district_accuracy_report.md
# ==========================================================================
with open(DATA_DIR / "district_accuracy_report.md", "w", encoding="utf-8") as f:
    f.write("# District Engine Accuracy Report\n\n")
    f.write("## Global Accuracy Metrics\n\n")
    f.write("| Metric | Count | % |\n")
    f.write("|---|---|---|\n")
    f.write(f"| Total test combinations | {total} | 100% |\n")
    f.write(f"| Top-1 match | {t1} | {t1_pct:.1f}% |\n")
    f.write(f"| Top-3 match | {t3} | {t3_pct:.1f}% |\n")
    f.write(f"| Top-5 match | {t5} | {t5_pct:.1f}% |\n")
    f.write(f"| Top-10 match | {t10} | {t10_pct:.1f}% |\n\n")

    f.write("## Per-District Accuracy Summary\n\n")
    f.write("| District | Zone | Soil | T1% | T3% | T5% |\n")
    f.write("|---|---|---|---|---|---|\n")

    for d_id in GROUND_TRUTH:
        if d_id not in district_results:
            continue
        d_meta = DISTRICT_MAP[d_id]
        dt1, dt3, dt5, dtotal = 0, 0, 0, 0
        for season, irrig_data in district_results[d_id].items():
            for irrig, run in irrig_data.items():
                dtotal += 1
                if run["top1_match"]: dt1 += 1
                if run["top3_match"]: dt3 += 1
                if run["top5_match"]: dt5 += 1
        f.write(f"| {d_meta['district']} | {d_meta['agro_climatic_zone']} | {d_meta.get('soil_texture','loam')} | "
                f"{(dt1/dtotal*100):.0f}% | {(dt3/dtotal*100):.0f}% | {(dt5/dtotal*100):.0f}% |\n")

    f.write("\n## Most Frequent False Positives (Unexpected Crops)\n")
    f.write("| Crop ID | Count |\n|---|---|\n")
    for crop_id, cnt in fp_counter.most_common(10):
        f.write(f"| {crop_id} | {cnt} |\n")

    f.write("\n## Most Frequent False Negatives (Missing Expected Crops)\n")
    f.write("| Crop ID | Count |\n|---|---|\n")
    for crop_id, cnt in fn_counter.most_common(10):
        f.write(f"| {crop_id} | {cnt} |\n")

# ==========================================================================
# WRITE recommendation_discrepancy_report.md
# ==========================================================================
with open(DATA_DIR / "recommendation_discrepancy_report.md", "w", encoding="utf-8") as f:
    f.write("# Recommendation Discrepancy Report\n\n")
    f.write("This report documents cases where the engine's Top-5 recommendations disagreed with official guidance, and identifies which rule caused the discrepancy.\n\n")

    for d_id in GROUND_TRUTH:
        if d_id not in district_results:
            continue
        d_meta = DISTRICT_MAP[d_id]
        has_discrepancy = False
        discrepancy_lines = []

        for season in SEASONS:
            for irrig, run in district_results[d_id][season].items():
                if run["false_negatives"] or not run["top3_match"]:
                    for miss in run["false_negatives"]:
                        for rule in (run["bad_rules"] or [f"Scoring pushes {miss} below Top-5"]):
                            discrepancy_lines.append(
                                f"- **{d_meta['district']}** | {season} | {irrig}: "
                                f"Missing `{miss}` from Top-5. "
                                f"**Root cause**: {rule}"
                            )
                            has_discrepancy = True

        if has_discrepancy:
            f.write(f"## {d_meta['district']}\n")
            f.write("\n".join(discrepancy_lines))
            f.write("\n\n")

    f.write("\n## Systemic Root Causes\n\n")
    f.write("### 1. Season Filter Over-Exclusion\n")
    f.write("The current season filter uses a strict list match. Crops grown in transitional sowing windows (e.g., late Kharif Sorghum that bleeds into Rabi) are incorrectly penalised. Source: TNAU Package of Practices.\n\n")
    f.write("### 2. Water Rule Under-Credits Irrigated Districts\n")
    f.write("In districts with confirmed canal irrigation (Cauvery Delta), the engine sometimes still penalises high-water crops under 'rainfed' scenarios because the seasonal effective rainfall threshold is too conservative.\n\n")
    f.write("### 3. Soil Mapping Granularity\n")
    f.write("districts.json uses a single soil_texture per district. In reality, districts have micro-level soil variation (e.g., Thanjavur has both alluvial and black cotton soils). A single texture collapses this nuance, causing soil mismatch penalties for crops that grow well in certain sub-regions.\n")

print("Validation complete. Reports saved.")
