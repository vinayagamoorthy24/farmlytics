/**
 * Climate Panel Component
 * Renders the climate risk advisory card.
 */
export function renderClimatePanel(climateRisk, district, season) {
    let drySpellColor = "var(--green-600)";
    if (climateRisk.drySpellPct >= 30) drySpellColor = "var(--red-600)";
    else if (climateRisk.drySpellPct >= 20) drySpellColor = "var(--risk-moderate-border)";

    let floodColor = "var(--green-600)";
    if (climateRisk.floodLevel === 'high') floodColor = "var(--red-600)";
    else if (climateRisk.floodLevel === 'medium') floodColor = "var(--risk-moderate-border)";

    // Derive temperature stress label from actual seasonal temperature
    const temp = climateRisk.seasonalTemp ?? 28;
    let tempLabel, tempColor;
    if (temp > 35) {
        tempLabel = `High (${temp}°C)`;
        tempColor = "var(--red-600)";
    } else if (temp > 30) {
        tempLabel = `Moderate (${temp}°C)`;
        tempColor = "var(--risk-moderate-border)";
    } else {
        tempLabel = `Low (${temp}°C)`;
        tempColor = "var(--green-600)";
    }

    return `
    <div class="advisory-card">
      <h3 class="advisory-card__title"><span aria-hidden="true">🌤️</span> Climate Risk – ${district.name ?? district.district} (${season.charAt(0).toUpperCase() + season.slice(1)})</h3>
      <div class="advisory-card__grid">
        <div class="advisory-item">
          <span class="advisory-item__label">Rainfall Available</span>
          <span class="advisory-item__value">${climateRisk.effectiveRainfall} mm</span>
        </div>
        <div class="advisory-item">
          <span class="advisory-item__label">Dry Spell Probability</span>
          <span class="advisory-item__value" style="color: ${drySpellColor}; font-weight: 600;">${climateRisk.drySpellPct}%</span>
        </div>
        <div class="advisory-item">
          <span class="advisory-item__label">Flood Risk</span>
          <span class="advisory-item__value" style="color: ${floodColor}; font-weight: 600; text-transform: capitalize;">${climateRisk.floodLevel}</span>
        </div>
        <div class="advisory-item">
          <span class="advisory-item__label">Temperature Stress</span>
          <span class="advisory-item__value" style="color: ${tempColor}; font-weight: 600;">${tempLabel}</span>
        </div>
      </div>
    </div>
  `;
}
