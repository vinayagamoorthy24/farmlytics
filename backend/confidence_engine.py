def calculate_confidence(crop, rules_fired):
    """
    Calculate confidence score (0-100) based on data completeness,
    source quality, and conflicting evidence.
    """
    score = 100
    reasons = []

    # Check for missing values
    critical_fields = ['water_need_mm_min', 'seasons', 'growth_duration_days_min']
    missing = [f for f in critical_fields if not crop.get(f)]
    if missing:
        score -= len(missing) * 15
        reasons.append(f"Missing critical data: {', '.join(missing)}")

    # Check source quality
    sources = crop.get('sources', {})
    verified_sources = [s for s in sources.values() if "TNAU" in s or "ICAR" in s or "FAO" in s or "NBSS-LUP" in s or "IMD" in s]
    if len(verified_sources) < 2:
        score -= 20
        reasons.append("Limited official sources verifying crop parameters.")
    else:
        reasons.append(f"Parameters verified by {len(verified_sources)} official sources (TNAU/ICAR/FAO).")

    # Conflicting evidence or manual assumptions
    if "assumption" in str(sources).lower():
        score -= 10
        reasons.append("Contains manual assumptions.")

    score = max(0, min(100, score))
    
    if score >= 90:
        level = "Very High"
    elif score >= 75:
        level = "High"
    elif score >= 50:
        level = "Medium"
    elif score >= 30:
        level = "Low"
    else:
        level = "Very Low"

    return {
        "score": score,
        "level": level,
        "reasons": reasons
    }
