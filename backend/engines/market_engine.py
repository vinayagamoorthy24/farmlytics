from __future__ import annotations

from .models import CropModel, round_js


def evaluate_market(crop: CropModel) -> dict:
    economics = crop.economics
    volatility_penalty = 0
    reasons: list[str] = []
    if economics["marketVolatility"] == "high":
        volatility_penalty = 5
        reasons.append("High market price volatility.")

    raw_profit_ratio = (
        economics["yieldPotential"] * economics["marketPrice"]
    ) / max(economics["inputCost"], 1)
    profit_pct = round_js(min(100, raw_profit_ratio * 8.5))
    profit_level = "High" if profit_pct > 75 else ("Low" if profit_pct < 45 else "Medium")

    return {
        "volatilityPenalty": volatility_penalty,
        "profitScore": profit_pct,
        "profitLevel": profit_level,
        "reasons": reasons,
    }
