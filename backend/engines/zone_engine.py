from __future__ import annotations

from .models import DistrictModel


def evaluate_zone(district: DistrictModel) -> dict:
    return {
        "districtZone": district.zone,
        "penalty": 0,
        "bonus": 0,
        "reasons": [],
    }
