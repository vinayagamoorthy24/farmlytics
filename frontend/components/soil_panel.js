/**
 * Soil Panel Component
 * Renders the soil health advisory card.
 */
export function renderSoilPanel(soilHealth) {
    let nitrogenColor = "var(--green-600)";
    if (soilHealth.nitrogenRisk === 'moderate') nitrogenColor = "var(--risk-moderate-border)";
    else if (soilHealth.nitrogenRisk === 'high') nitrogenColor = "var(--red-600)";

    let waterlogColor = "var(--green-600)";
    if (soilHealth.waterlogRisk === 'high') waterlogColor = "var(--red-600)";
    else if (soilHealth.waterlogRisk === 'medium') waterlogColor = "var(--risk-moderate-border)";

    const recsHtml = soilHealth.recommendations.map(r => `<li>${r}</li>`).join("");

    return `
    <div class="advisory-card">
      <h3 class="advisory-card__title">🌱 Soil Health Advisory</h3>
      <div class="advisory-card__content">
        <p><strong>Soil Type:</strong> ${soilHealth.soilType}</p>
        <div class="advisory-risks" style="margin-top: 0.5rem;">
           <p><strong>Risks:</strong></p>
           <ul style="margin: 0.25rem 0 0.5rem 1.5rem; color: var(--text-secondary);">
              <li><span style="color: ${nitrogenColor}; font-weight: 500;">Nitrogen: ${soilHealth.nitrogenDetail}</span></li>
              <li><span style="color: ${waterlogColor}; font-weight: 500;">Drainage: ${soilHealth.waterlogDetail}</span></li>
           </ul>
        </div>
        <div class="advisory-recs">
          <p><strong>Recommendations:</strong></p>
          <ul style="margin: 0.25rem 0 0 1.5rem; color: var(--text-secondary);">
            ${recsHtml}
          </ul>
        </div>
      </div>
    </div>
  `;
}
