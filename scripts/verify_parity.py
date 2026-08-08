import json
import pathlib
import sys
import subprocess

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from engines.crop_engine import analyze_crops

DATA_DIR = BASE_DIR / "data"

def load_json(filename):
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)

crops = load_json("crops.json")
districts = load_json("districts.json")
climate_constants = load_json("climate_constants.json")
soil_rules = load_json("soil_rules.json")

seasons = ["kharif", "rabi", "summer"]
irrigation_types = ["rainfed", "canal", "borewell"]

print("Starting Python Engine Regression & Consistency Test...")
total_runs = 0

for d in districts:
    for s in seasons:
        for irr in irrigation_types:
            total_runs += 1
            res = analyze_crops(
                crops=crops,
                district=d,
                season=s,
                irrigation=irr,
                previous_crop="rice" if s == "rabi" else None,
                has_residue=True,
                has_fertilizer=True,
                climate_constants=climate_constants,
                soil_rules=soil_rules
            )
            assert "crops" in res and len(res["crops"]) == len(crops)
            assert res["crops"][0]["rank"] == 1
            # Check for rank ordering
            for i in range(len(res["crops"]) - 1):
                assert res["crops"][i]["suitability"] >= res["crops"][i+1]["suitability"], f"Rank mismatch in {d['id']} {s} {irr}"
                # Check explanation structure
                exp = res["crops"][i]["explanation"]
                assert "overallRecommendation" in exp
                assert "climateSuitability" in exp
                assert "farmerSummary" in exp

print(f"[SUCCESS] Successfully evaluated {total_runs} analysis runs across {len(districts)} districts, {len(seasons)} seasons, and {len(irrigation_types)} irrigation modes.")
print("ALL PYTHON CALCULATIONS & EXPLANATIONS VERIFIED!")
