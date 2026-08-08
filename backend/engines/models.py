from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CropModel:
    raw: dict[str, Any]

    @property
    def id(self) -> str:
        return self.raw.get("id", "")

    @property
    def name(self) -> str:
        return self.raw.get("name", "")

    @property
    def family(self) -> str:
        return self.raw.get("family", "")

    @property
    def category(self) -> str:
        return self.raw.get("category", "")

    @property
    def description(self) -> str:
        return self.raw.get("description", "")

    @property
    def seasons(self) -> list[str]:
        return self.raw.get("seasons") or []

    @property
    def water_needs(self) -> dict[str, float]:
        wmin = self.raw.get("water_need_mm_min") or 0
        wmax = self.raw.get("water_need_mm_max") or 0
        return {"min": wmin, "max": wmax, "mid": (wmin + wmax) / 2}

    @property
    def stress_thresholds(self) -> dict[str, float]:
        return {
            "heat": self.raw.get("heat_stress") or 35,
            "cold": self.raw.get("cold_stress") or 15,
        }

    @property
    def duration(self) -> dict[str, int]:
        return {
            "min": self.raw.get("growth_duration_days_min") or 90,
            "max": self.raw.get("growth_duration_days_max") or 120,
        }

    @property
    def rotation(self) -> dict[str, list[str]]:
        return {
            "goodPredecessors": self.raw.get("good_predecessor_families") or [],
            "badPredecessors": self.raw.get("bad_predecessor_families") or [],
        }

    @property
    def economics(self) -> dict[str, Any]:
        return {
            "marketVolatility": self.raw.get("market_volatility") or "medium",
            "yieldPotential": self.raw.get("yield_potential") or 7,
            "marketPrice": self.raw.get("market_price") or 7,
            "inputCost": self.raw.get("input_cost") or 6,
            "mspCovered": self.raw.get("msp_covered") or False,
            "mspPricePerQtl": self.raw.get("msp_price_per_qtl"),
            "mspYear": self.raw.get("msp_year"),
        }

    def to_frontend_dict(self) -> dict[str, Any]:
        return {
            **self.raw,
            "id": self.id,
            "name": self.name,
            "family": self.family,
            "category": self.category,
            "description": self.description,
            "seasons": self.seasons,
            "waterNeeds": self.water_needs,
            "stressThresholds": self.stress_thresholds,
            "duration": self.duration,
            "rotation": self.rotation,
            "economics": self.economics,
        }


@dataclass
class DistrictModel:
    raw: dict[str, Any]

    @property
    def id(self) -> str:
        return self.raw.get("id", "")

    @property
    def name(self) -> str:
        return self.raw.get("district", "")

    @property
    def state(self) -> str:
        return self.raw.get("state", "")

    @property
    def zone(self) -> str:
        return self.raw.get("agro_climatic_zone", "")

    @property
    def annual_rainfall(self) -> int:
        return self.raw.get("avg_annual_rainfall_mm") or 0

    @property
    def rainfall_shares(self) -> dict[str, float]:
        return self.raw.get("seasonal_rainfall_share") or {}

    @property
    def temp_avg(self) -> dict[str, float]:
        return self.raw.get("seasonal_temp_avg") or {}

    @property
    def rainfall_cv(self) -> float:
        return self.raw.get("rainfall_cv_percent") or 25

    @property
    def soil(self) -> dict[str, str]:
        return {
            "type": self.raw.get("soil_type"),
            "drainage": self.raw.get("soil_drainage"),
            "texture": self.raw.get("soil_texture") or "loam",
        }

    @property
    def data_quality(self) -> float:
        return self.raw.get("data_quality_index") or 1.0

    def get_confidence_score(self) -> str:
        completeness = self.data_quality
        stability_factor = 1.0
        if self.rainfall_cv >= 40:
            stability_factor = 0.6
        elif self.rainfall_cv >= 30:
            stability_factor = 0.8
        elif self.rainfall_cv >= 20:
            stability_factor = 0.95
        model_factor = 0.85
        total_confidence = (completeness * stability_factor * model_factor) ** (1 / 3)
        if total_confidence >= 0.85:
            return "High"
        if total_confidence >= 0.70:
            return "Moderate"
        return "Low"

    def get_seasonal_rainfall(self, season: str) -> int:
        share = self.rainfall_shares.get(season.lower()) or 0
        return round_js(self.annual_rainfall * share)

    def get_effective_seasonal_rainfall(self, season: str) -> int:
        raw_rain = self.get_seasonal_rainfall(season)
        efficiency = {"sand": 0.50, "loam": 0.65, "clay": 0.75}
        texture = (self.soil.get("texture") or "loam").lower()
        factor = efficiency.get(texture, 0.65)
        return round_js(raw_rain * factor)

    def get_seasonal_temp(self, season: str) -> float:
        return self.temp_avg.get(season.lower()) or 28

    def to_frontend_dict(self) -> dict[str, Any]:
        return {
            **self.raw,
            "id": self.id,
            "name": self.name,
            "state": self.state,
            "zone": self.zone,
            "annualRainfall": self.annual_rainfall,
            "rainfallShares": self.rainfall_shares,
            "tempAvg": self.temp_avg,
            "tempVariability": self.raw.get("temp_variability_index") or "medium",
            "rainfallCV": self.rainfall_cv,
            "soil": self.soil,
            "source": self.raw.get("source"),
            "dataQuality": self.data_quality,
        }


def round_js(value: float) -> int:
    return int(value + 0.5)
