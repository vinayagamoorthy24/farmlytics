/**
 * Crop Cards Components — v3.0
 * Pure renderer: renders card UI only.
 * Explanation content is injected into the shared modal by app.js on click.
 */

export function renderCropCard(crop, index) {
    const cropName = crop.name || crop.crop_name || crop.crop || 'Crop';
    const level = crop.risk_level || 'safe';
    const badgeLabel = level === 'high' ? 'High Risk' : level === 'moderate' ? 'Moderate' : 'Safe';

    // Safely resolve duration and water values
    const durMin = crop.duration?.min ?? crop.growth_duration_days_min ?? '–';
    const durMax = crop.duration?.max ?? crop.growth_duration_days_max ?? '–';
    const wMin = crop.waterNeeds?.min ?? crop.water_need_mm_min ?? '–';
    const wMax = crop.waterNeeds?.max ?? crop.water_need_mm_max ?? '–';
    const volatility = crop.economics?.marketVolatility ?? crop.market_volatility ?? 'medium';

    const volBadge = volatility === 'high'
        ? '<span class="crop-card__stat crop-card__stat--warn" aria-label="Market: Volatile"><span aria-hidden="true">📈</span> Volatile</span>'
        : volatility === 'low'
            ? '<span class="crop-card__stat crop-card__stat--ok" aria-label="Market: Stable"><span aria-hidden="true">📊</span> Stable</span>'
            : '<span class="crop-card__stat" aria-label="Market: Moderate volatility"><span aria-hidden="true">📊</span> Moderate vol</span>';

    const profitClass = crop.profit_level === 'High' ? 'crop-card__stat--ok'
                      : crop.profit_level === 'Low' ? 'crop-card__stat--warn' : '';
    const profitBadge = `<span class="crop-card__stat ${profitClass}" title="Profit outlook: ${crop.profit_level}"><span aria-hidden="true">💰</span> Profit: ${crop.profit_level}</span>`;

    // MSP Badge
    const mspData = crop.economics || {};
    let mspBadge = '';
    if (mspData.mspCovered && mspData.mspPricePerQtl) {
        mspBadge = `<span class="crop-card__stat crop-card__stat--msp" title="Govt. MSP backed (${mspData.mspYear})"><span aria-hidden="true">🏛️</span> MSP ₹${mspData.mspPricePerQtl.toLocaleString('en-IN')}/qtl</span>`;
    } else {
        mspBadge = `<span class="crop-card__stat crop-card__stat--warn" title="No MSP coverage"><span aria-hidden="true">⚠</span> No MSP</span>`;
    }

    return `
    <article
      class="crop-card crop-card--${level}"
      data-risk="${level}"
      style="animation-delay: ${index * 40}ms"
    >
      <span class="crop-card__badge crop-card__badge--${level}">${badgeLabel}</span>

      <div class="crop-card__header">
        <h3 class="crop-card__name">${cropName}</h3>
        <span class="crop-card__score" title="Overall Suitability Rating">Suitability ${crop.suitability}%</span>
      </div>

      <p class="crop-card__category">${crop.category || ''} &middot; Family: ${crop.family || ''}</p>
      <p class="crop-card__desc">${crop.description || ''}</p>

      <div class="crop-card__stats">
        <span class="crop-card__stat" title="Duration" aria-label="Growth duration: ${durMin} to ${durMax} days">
          <span aria-hidden="true">📅</span> ${durMin}–${durMax} d
        </span>
        <span class="crop-card__stat" title="Water Needs" aria-label="Water requirement: ${wMin} to ${wMax} mm">
          <span aria-hidden="true">💧</span> ${wMin}–${wMax} mm
        </span>
        ${volBadge}
        ${profitBadge}
        ${mspBadge}
      </div>

      <div class="crop-card__actions" style="display: flex; gap: var(--s-1); margin-top: var(--s-2);">
        <button
          type="button"
          class="btn-explain"
          data-crop-index="${index}"
          aria-haspopup="dialog"
          aria-controls="explanation-modal"
          style="flex: 1; margin-top: 0;"
        >
          <span aria-hidden="true">📋</span> Decision Report
        </button>
        <button
          type="button"
          class="btn-compare-toggle"
          data-crop-index="${index}"
          aria-label="Add ${cropName} to comparison"
        >
          <span aria-hidden="true">⚖️</span> Compare
        </button>
      </div>
    </article>`;
}

export function renderResultsGrid(results) {
    if (!results || !results.length) {
        return `<p style="color: var(--text-secondary); text-align: center; grid-column: 1/-1;">No crops matched the analysis criteria.</p>`;
    }
    return results.map((r, idx) => renderCropCard(r, idx)).join('');
}
