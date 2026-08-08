"""
===============================================================================
AgroRisk Advisor — Main FastAPI Backend Application
===============================================================================
This file serves as the web server and entry point for the Python backend.

How it works:
1. Loads agricultural datasets (crops, districts, climate, soil) from JSON files.
2. Sets up a FastAPI web server with CORS enabled so the frontend can talk to it.
3. Defines API endpoints (/api/meta and /api/analyze).
4. Routes incoming user requests to the crop analysis engine and returns responses.

Beginner Python Note:
- FastAPI is a modern, fast Python web framework used to create Web APIs.
- Pydantic BaseModel defines the expected structure and types for data coming into or out of our API.
"""

import json
import pathlib
import sys

# ---------------------------------------------------------------------------
# Step 1: Set up module search paths so imports work smoothly
# ---------------------------------------------------------------------------
# BASE_DIR is the folder containing main.py (the 'backend' directory).
BASE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Import FastAPI web framework tools
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import our custom Python analysis engine function
from engines.crop_engine import analyze_crops

# ---------------------------------------------------------------------------
# Step 2: Define file paths for datasets and frontend files
# ---------------------------------------------------------------------------
# DATA_DIR points to project_root/data
DATA_DIR = BASE_DIR.parent / "data"
# FRONTEND_DIR points to project_root/frontend
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# ---------------------------------------------------------------------------
# Step 3: Helper function to load JSON dataset files safely
# ---------------------------------------------------------------------------
def _load_json(filename: str) -> list[dict]:
    """
    Reads a JSON data file from the 'data' directory and converts it to a Python list/dict.
    
    Parameters:
        filename (str): Name of the JSON file (e.g., 'crops.json')
        
    Returns:
        list[dict]: Parsed JSON content as native Python objects.
    """
    filepath = DATA_DIR / filename
    if not filepath.exists():
        raise RuntimeError(f"Data file not found: {filepath}")
    
    # Open and parse the JSON file with UTF-8 encoding
    with open(filepath, "r", encoding="utf-8") as fh:
        return json.load(fh)

# Load core datasets into memory when the server starts
CROPS: list[dict] = _load_json("crops.json")
DISTRICTS: list[dict] = _load_json("districts.json")
CLIMATE_CONSTANTS: dict = _load_json("climate_constants.json")
SOIL_RULES: dict = _load_json("soil_rules.json")

# Create quick dictionary lookups for fast access by ID
# Example: DISTRICT_MAP["coimbatore"] gives the Coimbatore district dictionary.
DISTRICT_MAP = {d["id"]: d for d in DISTRICTS}
CROP_MAP = {c["id"]: c for c in CROPS}

# ---------------------------------------------------------------------------
# Step 4: Initialize the FastAPI Web Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AgroRisk Advisor Engine",
    version="2.0.0",
    description=(
        "Rule-based agricultural risk advisory API. "
        "Evaluates crop suitability based on climate, soil, water, and market data."
    ),
)

# Enable CORS (Cross-Origin Resource Sharing) so our frontend browser app can make API requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Step 5: Define Data Validation Schemas (Pydantic Models)
# ---------------------------------------------------------------------------
# These classes ensure incoming HTTP requests have the correct data structure and types.

class AnalyzeRequest(BaseModel):
    """Defines the input parameters submitted by the user in the frontend form."""
    district: str          # Name/ID of the district selected (e.g. 'coimbatore')
    season: str            # Season selected: 'kharif', 'rabi', or 'summer'
    previous_crop: str | None = None  # Optional previous crop grown on the land
    irrigation: str        # Irrigation mode: 'rainfed', 'canal', or 'borewell'
    has_residue: bool = False      # Farming practice: Crop residue incorporated
    has_fertilizer: bool = False   # Farming practice: Optimal fertilizer applied


class CropResult(BaseModel):
    """Structure of a single evaluated crop result returned to the client."""
    crop_id: str
    crop_name: str
    category: str
    description: str
    growth_days: str
    water_requirement: str
    water_need_mm: str
    market_volatility: str
    rotation_sensitive: bool
    risk_level: str
    risk_score: int
    reasons: list[str]
    explanation: dict | None = None


class DistrictInfo(BaseModel):
    """District overview metadata included in response."""
    id: str
    district: str
    state: str
    avg_annual_rainfall_mm: int
    rainfall_variability: str
    agro_climatic_zone: str


class AnalyzeResponse(BaseModel):
    """The overall structure returned by the POST /api/analyze endpoint."""
    district: str
    district_info: DistrictInfo | None
    season: str
    irrigation: str
    previous_crop: str | None
    total_crops_evaluated: int
    results: list[CropResult]

# ---------------------------------------------------------------------------
# Step 6: API Endpoints (Routes)
# ---------------------------------------------------------------------------

@app.get("/api/meta")
def get_meta():
    """
    GET Endpoint: Returns metadata options for population of frontend select dropdowns.
    Returns: List of available districts, seasons, irrigation types, and crops.
    """
    return {
        "districts": [
            {
                "id": d["id"],
                "name": f"{d['district']} ({d['state']})",
                "state": d["state"],
                "rainfall": d["avg_annual_rainfall_mm"],
                "zone": d["agro_climatic_zone"],
            }
            for d in DISTRICTS
        ],
        "seasons": ["kharif", "rabi", "summer"],
        "irrigation_types": ["rainfed", "canal", "borewell"],
        "crops": [{"id": c["id"], "name": c["name"]} for c in CROPS],
    }


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    """
    POST Endpoint: Performs full crop risk analysis.
    
    Input: AnalyzeRequest object with user choices.
    Process:
    1. Looks up target district data from memory.
    2. Calls the rule-based python calculation engine (analyze_crops).
    3. Formats and returns the result list along with structured decision explanations.
    """
    # Normalize input district ID (e.g. "Coimbatore" -> "coimbatore")
    district_id = req.district.lower().replace(" ", "_")

    # Fetch district data dictionary
    district_info = DISTRICT_MAP.get(district_id)
    if not district_info:
        raise HTTPException(status_code=404, detail=f"District not found in dataset: {req.district}")

    # Pass all input parameters into the Python calculation engine
    analysis = analyze_crops(
        crops=CROPS,
        district=district_info,
        season=req.season.lower(),
        irrigation=req.irrigation.lower(),
        previous_crop=req.previous_crop,
        has_residue=req.has_residue,
        has_fertilizer=req.has_fertilizer,
        climate_constants=CLIMATE_CONSTANTS,
        soil_rules=SOIL_RULES,
    )

    # Return structured API response to frontend
    return {
        "district": district_id,
        "district_info": {
            "id": district_info["id"],
            "district": district_info["district"],
            "state": district_info["state"],
            "avg_annual_rainfall_mm": district_info["avg_annual_rainfall_mm"],
            "rainfall_variability": district_info["rainfall_variability"],
            "agro_climatic_zone": district_info["agro_climatic_zone"],
        },
        "season": req.season.lower(),
        "irrigation": req.irrigation.lower(),
        "previous_crop": req.previous_crop,
        "total_crops_evaluated": len(analysis["crops"]),
        "results": analysis["crops"],
        **analysis,
    }

# ---------------------------------------------------------------------------
# Step 7: Static File Serving (Web Server setup)
# ---------------------------------------------------------------------------
# Serves static files so the frontend UI can be loaded directly from localhost:8000
app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")
app.mount("/services", StaticFiles(directory=str(BASE_DIR.parent / "services")), name="services")

# Mount frontend root last to serve HTML, CSS, and JS static assets
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

