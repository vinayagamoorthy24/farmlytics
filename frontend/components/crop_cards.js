/**
 * Crop Cards Component — Farmlytics v9.0
 * Renders recommended crop cards with verified legally safe crop images,
 * rank badges, suitability gauges, and action controls.
 */

export function renderCropCard(crop, index) {
    const cropName = crop.name || crop.crop_name || crop.crop || 'Crop';
    const rank = crop.rank || (index + 1);
    const suitability = Math.round(crop.suitability ?? crop.overall_score ?? 0);

    // Resolve Suitability text and color scheme matching design spec
    let suitabilityText = 'Less Suitable';
    let labelClass = 'label--less';
    let donutClass = 'donut--less';
    let strokeColor = '#dc2626'; // Red

    if (suitability >= 80) {
        suitabilityText = 'Highly Suitable';
        labelClass = 'label--high';
        donutClass = 'donut--high';
        strokeColor = '#15803d'; // Green
    } else if (suitability >= 65) {
        suitabilityText = 'Suitable';
        labelClass = 'label--suitable';
        donutClass = 'donut--suitable';
        strokeColor = '#16a34a'; // Light Green
    } else if (suitability >= 50) {
        suitabilityText = 'Moderately Suitable';
        labelClass = 'label--moderate';
        donutClass = 'donut--moderate';
        strokeColor = '#d97706'; // Amber / Orange
    }

    // Resolve verified image path with reliable default fallback
    const imageSrc = crop.image || `assets/crops/${crop.id || 'default'}.png`;

    // Concise description string
    let descText = crop.description || 'Good match for selected soil, climate, and irrigation parameters.';
    if (descText.length > 90) {
        descText = descText.substring(0, 87) + '...';
    }

    const isBestMatch = rank === 1;

    return `
    <article
      class="crop-card"
      data-crop-id="${crop.id}"
      data-crop-index="${index}"
      style="animation-delay: ${index * 40}ms"
    >
      <div class="crop-card__image-container">
        <img 
          src="${imageSrc}" 
          alt="${cropName}" 
          class="crop-card__img"
          onerror="this.onerror=null; this.src='assets/crops/default.png';" 
        />
        <div class="crop-card__rank-badge ${isBestMatch ? 'crop-card__rank-badge--best' : ''}">
          <span class="rank-num">${rank}</span>
          ${isBestMatch ? '<span class="rank-text">Best Match</span>' : ''}
        </div>
      </div>

      <div class="crop-card__body">
        <h3 class="crop-card__title">${cropName}</h3>

        <div class="crop-card__score-row">
          <div class="crop-card__donut ${donutClass}">
            <svg viewBox="0 0 36 36" class="donut-svg">
              <path class="donut-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
              <path class="donut-fill" stroke="${strokeColor}" stroke-dasharray="${suitability}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
            </svg>
            <span class="donut-text">${suitability}%</span>
          </div>
          <span class="crop-card__suitability-label ${labelClass}">${suitabilityText}</span>
        </div>

        <p class="crop-card__desc">${descText}</p>

        <div class="crop-card__actions">
          <button
            type="button"
            class="btn-explain"
            data-crop-index="${index}"
            aria-haspopup="dialog"
            aria-controls="explanation-modal"
          >
            Only Explain &rarr;
          </button>
          <button
            type="button"
            class="btn-compare-toggle"
            data-crop-index="${index}"
            aria-label="Add ${cropName} to comparison"
          >
            <span aria-hidden="true">&#9878;</span> Compare
          </button>
        </div>
      </div>
    </article>`;
}

export function renderResultsGrid(results) {
    if (!results || !results.length) {
        return `<p style="color: var(--slate-500); text-align: center; grid-column: 1/-1; padding: 3rem;">No crops matched the analysis criteria.</p>`;
    }
    return results.map((r, idx) => renderCropCard(r, idx)).join('');
}
