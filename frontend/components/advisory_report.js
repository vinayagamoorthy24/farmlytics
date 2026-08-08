/**
 * Advisory Report Component (v1.0)
 * Generates a farmer-friendly, government-style printable advisory report.
 * Consumes analysis_service output and renders a structured document
 * suitable for print and PDF export.
 */

/**
 * Formats a date in Indian government-style: DD/MM/YYYY
 * @param {Date} date
 * @returns {string}
 */
function formatDate(date) {
  const dd = String(date.getDate()).padStart(2, '0');
  const mm = String(date.getMonth() + 1).padStart(2, '0');
  const yyyy = date.getFullYear();
  return `${dd}/${mm}/${yyyy}`;
}

/**
 * Capitalises the first letter of a string.
 * @param {string} str
 * @returns {string}
 */
function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Returns a risk-level CSS modifier class token.
 * @param {string} level – 'safe' | 'moderate' | 'high'
 * @returns {string}
 */
function riskModifier(level) {
  if (level === 'safe') return 'report-risk--safe';
  if (level === 'moderate') return 'report-risk--moderate';
  return 'report-risk--high';
}

/**
 * Builds the full advisory report HTML string.
 *
 * @param {object} results      – output from runAnalysis()
 * @param {string} season       – selected season identifier
 * @param {string} irrigation   – selected irrigation type
 * @returns {string}            – complete HTML for the report container
 */
export function renderAdvisoryReport(results, season, irrigation) {
  const { climate, soil, crops, district } = results;
  const cd = climate.details;
  const sd = soil.details;
  const top = crops[0] ?? null;
  const today = formatDate(new Date());

  /* ----------------------------------------------------------------
     Section 1 — Recommended Crop
     ---------------------------------------------------------------- */
      const topName = top ? (top.name || top.crop_name || top.crop || 'Crop') : '';
      const recommendedCropSection = top ? `
    <section class="report__section" aria-labelledby="report-heading-crop">
      <h3 class="report__section-title" id="report-heading-crop">
        <span class="report__section-number" aria-hidden="true">1</span>
        Recommended Crop
      </h3>
      <div class="report__kv-grid">
        <div class="report__kv">
          <span class="report__kv-label">Crop Name</span>
          <span class="report__kv-value report__kv-value--highlight">${topName}</span>
        </div>
        <div class="report__kv">
          <span class="report__kv-label">Risk Level</span>
          <span class="report__kv-value ${riskModifier(top.risk_level)}">${capitalize(top.risk_level)}</span>
        </div>
        <div class="report__kv">
          <span class="report__kv-label">Confidence</span>
          <span class="report__kv-value">${top.confidence}</span>
        </div>
        <div class="report__kv">
          <span class="report__kv-label">Suitability Index</span>
          <span class="report__kv-value">${top.suitability}%</span>
        </div>
        <div class="report__kv">
          <span class="report__kv-label">Profit Potential</span>
          <span class="report__kv-value">${top.profit_level}</span>
        </div>
      </div>
    </section>
  ` : `
    <section class="report__section" aria-labelledby="report-heading-crop">
      <h3 class="report__section-title" id="report-heading-crop">
        <span class="report__section-number" aria-hidden="true">1</span>
        Recommended Crop
      </h3>
      <p class="report__empty">No viable crop recommendation could be generated for the given parameters.</p>
    </section>
  `;

  /* ----------------------------------------------------------------
     Section 2 — Climate Summary
     ---------------------------------------------------------------- */
  const tempValue = cd.seasonalTemp ?? 'N/A';
  let tempStressLabel;
  if (cd.seasonalTemp > 35) tempStressLabel = 'High';
  else if (cd.seasonalTemp > 30) tempStressLabel = 'Moderate';
  else tempStressLabel = 'Low';

  const climateSummarySection = `
    <section class="report__section" aria-labelledby="report-heading-climate">
      <h3 class="report__section-title" id="report-heading-climate">
        <span class="report__section-number" aria-hidden="true">2</span>
        Climate Summary
      </h3>
      <div class="report__kv-grid">
        <div class="report__kv">
          <span class="report__kv-label">Seasonal Rainfall</span>
          <span class="report__kv-value">${cd.effectiveRainfall} mm</span>
        </div>
        <div class="report__kv">
          <span class="report__kv-label">Dry Spell Risk</span>
          <span class="report__kv-value ${cd.drySpellPct >= 30 ? 'report-risk--high' : cd.drySpellPct >= 20 ? 'report-risk--moderate' : 'report-risk--safe'}">${cd.drySpellPct}%</span>
        </div>
        <div class="report__kv">
          <span class="report__kv-label">Flood Risk</span>
          <span class="report__kv-value ${cd.floodLevel === 'high' ? 'report-risk--high' : cd.floodLevel === 'medium' ? 'report-risk--moderate' : 'report-risk--safe'}">${capitalize(cd.floodLevel)}</span>
        </div>
        <div class="report__kv">
          <span class="report__kv-label">Temperature Stress</span>
          <span class="report__kv-value">${tempStressLabel} (${tempValue}°C)</span>
        </div>
        <div class="report__kv">
          <span class="report__kv-label">Rainfall CV</span>
          <span class="report__kv-value">${cd.rangeCV}%</span>
        </div>
      </div>
    </section>
  `;

  /* ----------------------------------------------------------------
     Section 3 — Soil Advisory
     ---------------------------------------------------------------- */
  const soilRecsHtml = sd.recommendations.length
    ? sd.recommendations.map(r => `<li>${r}</li>`).join('')
    : '<li>No specific soil amendments required.</li>';

  const soilAdvisorySection = `
    <section class="report__section" aria-labelledby="report-heading-soil">
      <h3 class="report__section-title" id="report-heading-soil">
        <span class="report__section-number" aria-hidden="true">3</span>
        Soil Advisory
      </h3>
      <div class="report__kv-grid">
        <div class="report__kv">
          <span class="report__kv-label">Soil Type</span>
          <span class="report__kv-value">${sd.soilType}</span>
        </div>
        <div class="report__kv">
          <span class="report__kv-label">Drainage</span>
          <span class="report__kv-value">${sd.drainage}</span>
        </div>
        <div class="report__kv">
          <span class="report__kv-label">Nitrogen Risk</span>
          <span class="report__kv-value ${riskModifier(sd.nitrogenRisk === 'moderate' ? 'moderate' : 'safe')}">${sd.nitrogenDetail}</span>
        </div>
        <div class="report__kv">
          <span class="report__kv-label">Waterlogging Risk</span>
          <span class="report__kv-value ${riskModifier(sd.waterlogRisk === 'high' ? 'high' : sd.waterlogRisk === 'medium' ? 'moderate' : 'safe')}">${sd.waterlogDetail}</span>
        </div>
      </div>
      <div class="report__recs">
        <h4 class="report__recs-title">Recommendations</h4>
        <ol class="report__recs-list">${soilRecsHtml}</ol>
      </div>
    </section>
  `;

  /* ----------------------------------------------------------------
     Section 4 — Key Warnings
     ---------------------------------------------------------------- */
  const allWarnings = [];
  if (top && top.reasons.length) {
    top.reasons.forEach(r => allWarnings.push(r));
  }
  /* Also pull warnings from other high-risk crops */
  crops.slice(0, 5).forEach(c => {
    if (c.risk_level === 'high' && c.isInfeasible) {
      allWarnings.push(`${c.name}: ${c.reasons[0] ?? 'Below bio-minimum threshold.'}`);
    }
  });

  const warningsSection = allWarnings.length ? `
    <section class="report__section report__section--warnings" aria-labelledby="report-heading-warnings">
      <h3 class="report__section-title" id="report-heading-warnings">
        <span class="report__section-number" aria-hidden="true">4</span>
        Key Warnings
      </h3>
      <ul class="report__warnings-list" role="list">
        ${allWarnings.map(w => `<li class="report__warning-item">${w}</li>`).join('')}
      </ul>
    </section>
  ` : `
    <section class="report__section" aria-labelledby="report-heading-warnings">
      <h3 class="report__section-title" id="report-heading-warnings">
        <span class="report__section-number" aria-hidden="true">4</span>
        Key Warnings
      </h3>
      <p class="report__empty report__empty--positive">No critical warnings. Environmental parameters are generally favourable.</p>
    </section>
  `;

  /* ----------------------------------------------------------------
     Section 5 — Top 3 Alternatives
     ---------------------------------------------------------------- */
  const alternativesRows = crops.slice(1, 4).map(c => `
    <tr>
      <td>${c.name || c.crop_name || c.crop || 'Crop'}</td>
      <td><span class="${riskModifier(c.risk_level)}">${capitalize(c.risk_level)}</span></td>
      <td>${c.suitability}%</td>
      <td>${c.profit_level}</td>
    </tr>
  `).join('');

  const alternativesSection = crops.length > 1 ? `
    <section class="report__section" aria-labelledby="report-heading-alternatives">
      <h3 class="report__section-title" id="report-heading-alternatives">
        <span class="report__section-number" aria-hidden="true">5</span>
        Alternative Crops
      </h3>
      <table class="report__table" role="table">
        <thead>
          <tr>
            <th scope="col">Crop</th>
            <th scope="col">Risk</th>
            <th scope="col">Suitability</th>
            <th scope="col">Profit</th>
          </tr>
        </thead>
        <tbody>${alternativesRows}</tbody>
      </table>
    </section>
  ` : '';

  /* ----------------------------------------------------------------
     Section 6 — Disclaimer
     ---------------------------------------------------------------- */
  const disclaimerSection = `
    <section class="report__section report__section--disclaimer" aria-labelledby="report-heading-disclaimer">
      <h3 class="report__section-title" id="report-heading-disclaimer">
        <span class="report__section-number" aria-hidden="true">6</span>
        Disclaimer
      </h3>
      <p class="report__disclaimer-text">
        This advisory is for guidance only. Final decisions should consider local conditions,
        ground-level observations, and expert advice from your local Krishi Vigyan Kendra (KVK)
        or District Agriculture Officer. AgroRisk Advisor does not bear liability for crop
        losses or financial decisions based on this report.
      </p>
    </section>
  `;

  /* ----------------------------------------------------------------
     Full Report Assembly
     ---------------------------------------------------------------- */
  return `
    <article class="advisory-report" id="advisory-report-content" aria-labelledby="report-main-title">
      <!-- Report Header -->
      <header class="report__header">
        <div class="report__header-brand">
          <span class="report__logo" aria-hidden="true">🌾</span>
          <div class="report__header-titles">
            <h2 class="report__title" id="report-main-title">AgroRisk Advisor</h2>
            <p class="report__subtitle">Agricultural Crop Risk Advisory Report</p>
          </div>
        </div>
        <div class="report__header-meta">
          <div class="report__meta-item">
            <span class="report__meta-label">District</span>
            <span class="report__meta-value">${district.name}, ${district.state ?? ''}</span>
          </div>
          <div class="report__meta-item">
            <span class="report__meta-label">Season</span>
            <span class="report__meta-value">${capitalize(season)}</span>
          </div>
          <div class="report__meta-item">
            <span class="report__meta-label">Irrigation</span>
            <span class="report__meta-value">${capitalize(irrigation)}</span>
          </div>
          <div class="report__meta-item">
            <span class="report__meta-label">Date</span>
            <span class="report__meta-value">${today}</span>
          </div>
        </div>
      </header>

      <!-- Report Body -->
      <div class="report__body">
        ${recommendedCropSection}
        ${climateSummarySection}
        ${soilAdvisorySection}
        ${warningsSection}
        ${alternativesSection}
        ${disclaimerSection}
      </div>

      <!-- Report Footer -->
      <footer class="report__footer">
        <p class="report__footer-text">
          Generated by AgroRisk Advisor on ${today} · Data: IMD / ICAR / FAO / Agmarknet
        </p>
        <p class="report__footer-text">
          © 2026 AgroRisk Advisor · For official guidance, contact your local KVK
        </p>
      </footer>
    </article>
  `;
}

/**
 * Initialises the advisory report modal and binds event listeners
 * for Print and PDF download actions.
 *
 * @param {HTMLElement} reportContainer – the modal/overlay element
 * @param {HTMLElement} reportContent   – the inner content wrapper
 */
export function initAdvisoryReportActions(reportContainer, reportContent) {
  const btnPrint = reportContainer.querySelector('#btn-report-print');
  const btnPdf = reportContainer.querySelector('#btn-report-pdf');
  const btnClose = reportContainer.querySelector('#btn-report-close');

  if (btnPrint) {
    btnPrint.addEventListener('click', () => {
      window.print();
    });
  }

  if (btnPdf) {
    btnPdf.addEventListener('click', async () => {
      btnPdf.disabled = true;
      btnPdf.textContent = 'Generating…';
      try {
        await generatePDF(reportContent);
      } catch (err) {
        console.error('PDF generation failed:', err);
        /* Fallback: print dialog */
        window.print();
      } finally {
        btnPdf.disabled = false;
        btnPdf.textContent = '📥 Download PDF';
      }
    });
  }

  if (btnClose) {
    btnClose.addEventListener('click', () => {
      reportContainer.setAttribute('hidden', '');
      reportContainer.classList.remove('report-overlay--visible');
      document.body.style.overflow = '';
    });

    /* Close on Escape key */
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !reportContainer.hidden) {
        btnClose.click();
      }
    });
  }
}

/**
 * Lightweight PDF generation using html2pdf.js (loaded on-demand).
 * Falls back to window.print() when offline / script unavailable.
 *
 * @param {HTMLElement} contentEl – the element to convert
 */
async function generatePDF(contentEl) {
  /* Attempt to load html2pdf.js dynamically */
  if (typeof html2pdf === 'undefined') {
    try {
      await loadScript('https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.2/html2pdf.bundle.min.js');
    } catch {
      console.warn('html2pdf.js unavailable (offline?). Using browser print.');
      window.print();
      return;
    }
  }

  /* eslint-disable-next-line no-undef */
  const worker = html2pdf()
    .set({
      margin:       [10, 10, 10, 10],
      filename:     `AgroRisk_Advisory_${Date.now()}.pdf`,
      image:        { type: 'jpeg', quality: 0.95 },
      html2canvas:  { scale: 2, useCORS: true },
      jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' },
      pagebreak:    { mode: ['avoid-all', 'css', 'legacy'] }
    })
    .from(contentEl);

  await worker.save();
}

/**
 * Dynamically loads an external script.
 * @param {string} src
 * @returns {Promise<void>}
 */
function loadScript(src) {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${src}"]`);
    if (existing) { resolve(); return; }

    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = resolve;
    script.onerror = reject;
    document.head.appendChild(script);
  });
}
