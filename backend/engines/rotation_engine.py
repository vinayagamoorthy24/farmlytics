from __future__ import annotations

from .models import CropModel


def evaluate_rotation(crop: CropModel, prev_crop: CropModel | None) -> dict:
    conflict = False
    beneficial = False
    reasons: list[str] = []

    if prev_crop:
        prev_family = prev_crop.family
        if prev_family in crop.rotation["badPredecessors"]:
            conflict = True
            reasons.append(f"Rotation Conflict: Planting {crop.family} after {prev_family}.")
        if prev_family in crop.rotation["goodPredecessors"]:
            beneficial = True

    return {
        "conflict": conflict,
        "beneficial": beneficial,
        "reasons": reasons,
        "penalty": 0,
    }
