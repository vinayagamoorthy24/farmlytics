/**
 * Analysis Summary Component (v7.2)
 * Displays the top-tier recommendation and confidence meta.
 */
export function renderAnalysisSummary(results, district) {
   const top = results.crops[0];
   if (!top) return "";

   const topName = top.name || top.crop_name || top.crop || 'Primary Crop';
   const badgeClass = `crop-card__badge--${top.risk_level}`;
   const confidenceLabel = `${top.confidence} Confidence`;
   const confidenceClass = top.confidence === 'High' ? 'stat--ok' : (top.confidence === 'Moderate' ? 'stat--info' : 'stat--warn');
   
   const farmerSummary = top.explanation ? top.explanation.farmerSummary.text : "No detailed summary available.";

   return `
    <div class="top-rec-card">
       <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-2);">
          <h3 class="top-rec-title">Primary Recommendation</h3>
          <span class="crop-card__stat ${confidenceClass}" style="font-size: 0.75rem; font-weight: 600; padding: 0.125rem 0.5rem; border-radius: var(--radius-sm);">
             🛡️ ${confidenceLabel}
          </span>
       </div>
       <div class="top-rec-content">
          <div class="top-rec-header">
             <span class="crop-card__badge ${badgeClass}">${(top.risk_level || '').toUpperCase()}</span>
             <h4 class="top-rec-name">${topName}</h4>
             <span class="crop-card__stat">Suitability: ${top.suitability}%</span>
             <span class="crop-card__stat" style="margin-left:auto;">💰 Profit: ${top.profit_level}</span>
          </div>
          <div class="top-rec-reasons" style="margin-top: var(--space-3); padding-top: var(--space-3); border-top: 1px solid var(--border-subtle);">
             <p style="margin: 0; color: var(--text-secondary); line-height: 1.6; font-size: 1rem;">${farmerSummary}</p>
          </div>
       </div>
    </div>
  `;
}

export function renderDataStatus(version) {
   return `
    <div class="telemetry-text" style="display: flex; justify-content: center; gap: var(--space-4); margin-top: var(--space-2);">
      <span>📦 Dataset: ${version} (Validated)</span>
      <span>🌐 Mode: Live API (Python Backend)</span>
      <span>🏛️ Source: IMD / ICAR / FAO</span>
    </div>
  `;
}
