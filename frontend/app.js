/**
 * AgroRisk Advisor — Frontend Application (v8.0 - Production Edition)
 * Orchestrates UI interactions, service calls, and component rendering.
 */

import { loadDatasets } from '../services/dataset_loader.js?v=8.1';
import { runAnalysis } from '../services/analysis_service.js?v=8.1';
import { renderClimatePanel } from './components/climate_panel.js?v=8.1';
import { renderSoilPanel } from './components/soil_panel.js?v=8.1';
import { renderCropCard, renderResultsGrid } from './components/crop_cards.js?v=8.1';
import { renderAnalysisSummary, renderDataStatus } from './components/analysis_summary.js?v=8.1';
import { renderAdvisoryReport, initAdvisoryReportActions } from './components/advisory_report.js?v=8.1';

(async function AgroRiskApp() {
  "use strict";

  /* ------------------------------------------------------------------
     Constants & DOM References
     ------------------------------------------------------------------ */
  const DATA_VERSION = 'v8.1';

  const form = document.getElementById("advisor-form");
  const btnAnalyze = document.getElementById("btn-analyze");
  const selectDistrict = document.getElementById("select-district");
  const selectPrevCrop = document.getElementById("select-prev-crop");
  const resultsSection = document.getElementById("results-section");
  const resultsPlaceholder = document.getElementById("results-placeholder");
  const resultsSummary = document.getElementById("results-summary");
  const topRecommender = document.getElementById("top-recommendation");
  const resultsGrid = document.getElementById("results-grid");
  const filterBar = document.querySelector(".filter-bar");
  const districtMeta = document.getElementById("district-meta");
  const telemetryText = document.getElementById("telemetry");
  const climateAdvisory = document.getElementById("climate-risk-advisory");
  const soilAdvisory = document.getElementById("soil-health-advisory");
  const checkResidue = document.getElementById("check-residue");
  const checkFertilizer = document.getElementById("check-fertilizer");
  const reportOverlay = document.getElementById("report-overlay");
  const reportRenderTarget = document.getElementById("report-render-target");
  const btnViewReport = document.getElementById("btn-view-report");

  let DATASETS = null;
  let currentResults = [];
  let lastAnalysisResults = null;
  let lastAnalysisInput = null;

  /* ------------------------------------------------------------------
     Initialisation
     ------------------------------------------------------------------ */
  async function init() {
    try {
      DATASETS = await loadDatasets(DATA_VERSION);

      populateSelects();
      setupEventListeners();

      // Initial telemetry
      telemetryText.innerHTML = renderDataStatus(DATA_VERSION);

    } catch (err) {
      console.error("Initialization failed:", err);
      if (selectDistrict) selectDistrict.innerHTML = '<option value="" disabled selected>Offline load failed</option>';
    }
  }

  function populateSelects() {
    selectDistrict.innerHTML = '<option value="" disabled selected>Select district</option>';
    DATASETS.districts
      .sort((a, b) => a.name.localeCompare(b.name))
      .forEach((d) => {
        const opt = document.createElement("option");
        opt.value = d.id;
        opt.textContent = d.name;
        selectDistrict.appendChild(opt);
      });

    selectPrevCrop.innerHTML = '<option value="">None / First crop</option>';
    DATASETS.crops
      .sort((a, b) => a.name.localeCompare(b.name))
      .forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = c.name;
        selectPrevCrop.appendChild(opt);
      });
  }

  function setupEventListeners() {
    selectDistrict.addEventListener("change", () => {
      const d = DATASETS.districtLookup[selectDistrict.value];
      if (d && districtMeta) {
        districtMeta.innerHTML = `
          <span class="district-info__chip">📍 ${d.zone}</span>
          <span class="district-info__chip">🌧️ ${d.annualRainfall} mm/yr</span>
          <span class="district-info__chip">🌱 Soil: ${d.soil.type} (${d.soil.drainage} Dr)</span>
        `;
        districtMeta.hidden = false;
      }
    });


    form.addEventListener("submit", (e) => {
      e.preventDefault();
      triggerAnalysis();

      setTimeout(() => resultsSection.scrollIntoView({ behavior: "smooth", block: "start" }), 200);
    });

    if (filterBar) {
      filterBar.addEventListener("click", (e) => {
        const pill = e.target.closest(".filter-pill");
        if (!pill) return;
        const filter = pill.dataset.filter;
        filterBar.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("filter-pill--active"));
        pill.classList.add("filter-pill--active");
        filterResults(filter);
      });
    }

    /* --- Advisory Report Button --- */
    if (btnViewReport && reportOverlay && reportRenderTarget) {
      btnViewReport.addEventListener('click', () => {
        if (!lastAnalysisResults || !lastAnalysisInput) return;

        reportRenderTarget.innerHTML = renderAdvisoryReport(
          lastAnalysisResults,
          lastAnalysisInput.season,
          lastAnalysisInput.irrigation
        );

        reportOverlay.removeAttribute('hidden');
        /* Trigger reflow for animation */
        void reportOverlay.offsetWidth;
        reportOverlay.classList.add('report-overlay--visible');
        document.body.style.overflow = 'hidden';
      });

      initAdvisoryReportActions(reportOverlay, reportRenderTarget);
    }

    // State for comparison
    const selectedCompareIndices = new Set();
    const compareBar = document.getElementById('compare-bar');
    const compareBarCount = document.getElementById('compare-bar-count');
    const btnCompareClear = document.getElementById('btn-compare-clear');
    const btnCompareLaunch = document.getElementById('btn-compare-launch');
    const compareModal = document.getElementById('compare-modal');
    const compareModalBody = document.getElementById('compare-modal-body');
    const compareModalClose = document.getElementById('compare-modal-close');
    const compareBackdrop = document.getElementById('compare-backdrop');

    function updateCompareBarUI() {
      if (!compareBar) return;
      const count = selectedCompareIndices.size;
      if (count > 0) {
        compareBar.removeAttribute('hidden');
        compareBarCount.textContent = `${count} crop${count > 1 ? 's' : ''} selected`;
      } else {
        compareBar.setAttribute('hidden', 'true');
      }
    }

    // Toggle Compare Button click
    resultsGrid.addEventListener('click', (e) => {
      const compareBtn = e.target.closest('.btn-compare-toggle');
      if (compareBtn) {
        const idx = parseInt(compareBtn.dataset.cropIndex, 10);
        if (selectedCompareIndices.has(idx)) {
          selectedCompareIndices.delete(idx);
          compareBtn.classList.remove('is-selected');
          compareBtn.innerHTML = `<span aria-hidden="true">⚖️</span> Compare`;
        } else {
          if (selectedCompareIndices.size >= 3) {
            alert('You can compare up to 3 crops at a time.');
            return;
          }
          selectedCompareIndices.add(idx);
          compareBtn.classList.add('is-selected');
          compareBtn.innerHTML = `<span aria-hidden="true">✓</span> Added`;
        }
        updateCompareBarUI();
        return;
      }

      const btn = e.target.closest('.btn-explain');
      if (!btn) return;
      const idx = parseInt(btn.dataset.cropIndex, 10);
      const crop = currentResults[idx];
      if (crop) {
        renderExplanationModal(crop);
      }
    });

    if (btnCompareClear) {
      btnCompareClear.addEventListener('click', () => {
        selectedCompareIndices.clear();
        resultsGrid.querySelectorAll('.btn-compare-toggle').forEach(b => {
          b.classList.remove('is-selected');
          b.innerHTML = `<span aria-hidden="true">⚖️</span> Compare`;
        });
        updateCompareBarUI();
      });
    }

    if (btnCompareLaunch) {
      btnCompareLaunch.addEventListener('click', () => {
        const selectedCrops = Array.from(selectedCompareIndices).map(idx => currentResults[idx]).filter(Boolean);
        if (!selectedCrops.length) return;

        compareModalBody.innerHTML = renderCompareMatrix(selectedCrops);
        compareModal.removeAttribute('hidden');
        void compareModal.offsetWidth;
        compareModal.classList.add('is-open');
        document.body.style.overflow = 'hidden';
      });
    }

    function closeCompareModal() {
      if (!compareModal || compareModal.hidden) return;
      compareModal.classList.remove('is-open');
      compareModal.addEventListener('transitionend', () => {
        compareModal.hidden = true;
        document.body.style.overflow = '';
      }, { once: true });
    }

    if (compareModalClose) compareModalClose.addEventListener('click', closeCompareModal);
    if (compareBackdrop) compareBackdrop.addEventListener('click', closeCompareModal);

    // Close: close button
    const closeBtn = document.getElementById('explanation-modal-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', closeModal);
    }

    // Close: backdrop click
    const backdrop = document.getElementById('explanation-backdrop');
    if (backdrop) {
      backdrop.addEventListener('click', closeModal);
    }

    // Close: Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeModal();
        closeCompareModal();
      }
    });

    function closeModal() {
      const modal = document.getElementById('explanation-modal');
      if (!modal || modal.hidden) return;
      modal.classList.remove('is-open');
      modal.addEventListener('transitionend', () => {
        modal.hidden = true;
        document.body.style.overflow = '';
      }, { once: true });
    }

    function renderCompareMatrix(crops) {
      if (!crops || !crops.length) return "<p style='color: var(--text-secondary); text-align: center; padding: var(--s-3);'>No crops selected for comparison.</p>";

      const cols = crops.map(c => `
        <div class="compare-card-col">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: var(--s-1);">
            <span class="crop-card__badge crop-card__badge--${c.risk_level || 'safe'}">${(c.risk_level || 'safe').toUpperCase()}</span>
            <span class="compare-card__score-label">${c.suitability}% Match</span>
          </div>
          <h3 class="compare-card__name">${c.name || c.crop_name}</h3>
          <p class="compare-card__category" style="margin: 2px 0 var(--s-15) 0; font-size: 0.8125rem; color: var(--text-secondary);">${c.category || 'Crop'} &bull; ${c.family || 'Family'}</p>
          <div class="compare-meter-track">
             <div class="compare-meter-fill" style="width: ${c.suitability}%; background: ${c.suitability >= 70 ? 'var(--green-600)' : (c.suitability >= 50 ? 'var(--amber-500)' : 'var(--red-600)')};"></div>
          </div>
        </div>
      `).join('');

      const durRow = crops.map(c => `<td><strong>${c.duration?.min || '–'}–${c.duration?.max || '–'}</strong> days</td>`).join('');
      const waterRow = crops.map(c => `<td><strong>${c.waterNeeds?.min || '–'}–${c.waterNeeds?.max || '–'}</strong> mm</td>`).join('');
      const profitRow = crops.map(c => `<td><span class="compare-tag compare-tag--profit">${c.profit_level || 'Medium'} Tier</span></td>`).join('');
      const mspRow = crops.map(c => {
         const m = c.economics || {};
         return m.mspPricePerQtl 
           ? `<td><span class="compare-tag compare-tag--msp">₹${m.mspPricePerQtl.toLocaleString('en-IN')} / qtl</span></td>` 
           : `<td><span class="compare-tag compare-tag--none">No Govt MSP</span></td>`;
      }).join('');
      const riskRow = crops.map(c => `<td><strong>${(c.risk_level || 'safe').toUpperCase()}</strong> <span style="color: var(--text-secondary); font-size: 0.8125rem;">(${c.confidence || 'High'} Conf)</span></td>`).join('');
      const summaryRow = crops.map(c => `<td><p class="compare-verdict-text">${c.explanation ? c.explanation.farmerSummary.text : c.description}</p></td>`).join('');

      return `
        <div class="compare-intro-header">
          <p class="compare-intro-subtitle">Comparative Agronomic Evaluation Matrix</p>
        </div>
        <div class="compare-header-grid" style="display: grid; grid-template-columns: repeat(${crops.length}, 1fr); gap: var(--s-2); margin-bottom: var(--s-3);">
          ${cols}
        </div>
        <div class="compare-table-container">
          <table class="compare-table">
            <tbody>
              <tr><th class="compare-table__row-header">Growth Duration</th>${durRow}</tr>
              <tr><th class="compare-table__row-header">Water Requirement</th>${waterRow}</tr>
              <tr><th class="compare-table__row-header">Profitability</th>${profitRow}</tr>
              <tr><th class="compare-table__row-header">Govt MSP Support</th>${mspRow}</tr>
              <tr><th class="compare-table__row-header">Risk Profile</th>${riskRow}</tr>
              <tr><th class="compare-table__row-header">Agronomic Summary</th>${summaryRow}</tr>
            </tbody>
          </table>
        </div>
      `;
    }

    function renderExplanationModal(crop) {
      const e = crop.explanation;
      const name = crop.name || crop.crop_name || crop.crop;
      const modal = document.getElementById('explanation-modal');
      const body = document.getElementById('explanation-modal-body');
      const title = document.getElementById('explanation-modal-title');

      title.textContent = `Decision Report: ${name}`;

      // Badges row
      const riskClass = `crop-card__badge--${crop.risk_level}`;
      const confClass = crop.confidence === 'High' ? 'badge--ok'
                      : crop.confidence === 'Moderate' ? 'badge--warn' : 'badge--error';
      const badgesHTML = `
        <div class="explanation-meta-badges">
          <span class="crop-card__badge ${riskClass}">${(crop.risk_level || 'Safe').toUpperCase()}</span>
          <span class="crop-card__badge" style="background: var(--bg-surface-alt); border: 1px solid var(--border-soft); color: var(--text-primary);">Suitability: ${crop.suitability}%</span>
          <span class="crop-card__badge" style="background: var(--bg-surface-alt); border: 1px solid var(--border-soft); color: var(--text-primary);">Confidence: ${crop.confidence}</span>
          <span class="crop-card__badge" style="background: var(--bg-surface-alt); border: 1px solid var(--border-soft); color: var(--text-primary);">Profit: ${crop.profit_level}</span>
        </div>`;

      // Sections — one per explanation key
      const SECTIONS = [
        { key: 'overallRecommendation',  icon: '🎯' },
        { key: 'climateSuitability',     icon: '🌡️' },
        { key: 'rainfallAnalysis',       icon: '🌧️' },
        { key: 'temperatureSuitability', icon: '☀️' },
        { key: 'soilCompatibility',      icon: '🌱' },
        { key: 'waterAvailability',      icon: '💧' },
        { key: 'irrigationEffect',       icon: '🚿' },
        { key: 'seasonCompatibility',    icon: '📅' },
        { key: 'cropRotationEffect',     icon: '🔄' },
        { key: 'diseaseStressRisks',     icon: '🦠' },
        { key: 'marketInformation',      icon: '📈' },
        { key: 'profitability',          icon: '💰' },
        { key: 'confidenceAnalysis',     icon: '🛡️' },
        { key: 'riskAnalysis',           icon: '⚠️' },
        { key: 'finalRecommendation',    icon: '✅', isFinal: true },
      ];

      const sectionsHTML = SECTIONS.map(({ key, icon, isFinal }) => {
        const section = e?.[key];
        if (!section) return '';
        // Convert markdown **bold** to <strong> for visual emphasis
        const text = (section.text || '').replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        const finalClass = isFinal ? ' explanation-section--final' : '';
        return `
          <div class="explanation-section${finalClass}">
            <p class="explanation-section__title">
              <span aria-hidden="true">${icon}</span> ${section.title}
            </p>
            <p class="explanation-section__text">${text}</p>
          </div>`;
      }).join('');

      body.innerHTML = badgesHTML + sectionsHTML;

      // Open modal
      modal.hidden = false;
      void modal.offsetWidth;               // force reflow for CSS transition
      modal.classList.add('is-open');
      document.body.style.overflow = 'hidden';
      
      const closeBtn = document.getElementById('explanation-modal-close');
      if (closeBtn) closeBtn.focus();
    }
  }

  async function triggerAnalysis() {
    const input = {
      districtId: selectDistrict.value,
      season: document.getElementById("select-season").value,
      irrigation: document.getElementById("select-irrigation").value,
      prevCropId: selectPrevCrop.value || null,
      hasResidue: checkResidue ? checkResidue.checked : false,
      hasFertilizer: checkFertilizer ? checkFertilizer.checked : false
    };

    if (!input.districtId || !input.season || !input.irrigation) return;

    if (resultsPlaceholder) resultsPlaceholder.setAttribute('hidden', '');
    btnAnalyze.classList.add("btn-primary--loading");
    btnAnalyze.disabled = true;

    const startTime = performance.now();

    try {
      const results = await runAnalysis(input, DATASETS);
      currentResults = results.crops;
      lastAnalysisResults = results;
      lastAnalysisInput = input;

      renderAll(results, input.season);

      const endTime = performance.now();
      console.log(`Analysis completed in ${(endTime - startTime).toFixed(1)} ms.`);

      revealResultsSection();

    } catch (err) {
      console.error("Analysis pipeline failed:", err);
    } finally {
      btnAnalyze.classList.remove("btn-primary--loading");
      btnAnalyze.disabled = false;
    }
  }

  function renderAll(results, season) {
    // DEBUG: Log crop object structure to diagnose undefined properties
    if (results.crops.length > 0) {
      const c = results.crops[0];
      console.log('[DEBUG] First crop keys:', Object.keys(c));
      console.log('[DEBUG] duration:', c.duration);
      console.log('[DEBUG] waterNeeds:', c.waterNeeds);
      console.log('[DEBUG] economics:', c.economics);
      console.log('[DEBUG] Full crop:', JSON.stringify(c, null, 2).substring(0, 1000));
    }

    climateAdvisory.innerHTML = `<h2 class="section-title">Environmental Profiling</h2>` + renderClimatePanel(results.climate.details, results.district, season);
    climateAdvisory.hidden = false;

    soilAdvisory.innerHTML = renderSoilPanel(results.soil.details);
    soilAdvisory.hidden = false;

    renderSummaryGrid(results.crops, results.district);
    topRecommender.innerHTML = `<h2 class="section-title">Strategic Recommendation</h2>` + renderAnalysisSummary(results, results.district);
    topRecommender.hidden = false;

    resultsGrid.innerHTML = `<h2 class="section-title" style="grid-column: 1/-1;">All Analyzed Crops</h2>` + renderResultsGrid(results.crops);
  }

  function revealResultsSection() {
    resultsSection.removeAttribute('hidden');
    resultsSection.classList.remove('results-section--visible');
    void resultsSection.offsetWidth;
    resultsSection.classList.add('results-section--visible');

    filterBar.querySelectorAll(".filter-pill").forEach((p) => {
      p.classList.toggle("filter-pill--active", p.dataset.filter === "all");
    });
  }

  function filterResults(filter) {
    const cards = resultsGrid.querySelectorAll(".crop-card");
    cards.forEach(card => {
      if (filter === "all" || card.dataset.risk === filter) {
        card.style.display = "block";
      } else {
        card.style.display = "none";
      }
    });
  }

  function renderSummaryGrid(results, district) {
    const counts = { safe: 0, moderate: 0, high: 0 };
    results.forEach((r) => { counts[r.risk_level]++; });

    const rain = district.annualRainfall;
    const pct = Math.min(Math.max((rain - 300) / (1200) * 100, 0), 100);

    resultsSummary.innerHTML = `
      <div class="district-map-widget">
        <h4 class="map-widget-title">${district.name}, ${district.state}</h4>
        <div class="rainfall-color-map-container" aria-hidden="true">
           <div class="rainfall-color-map">
             <div class="color-map-indicator" style="left: ${pct}%;">
               <span class="indicator-tooltip">${rain}mm</span>
             </div>
           </div>
           <div class="color-map-labels">
             <span>Arid (300mm)</span>
             <span>Moderate</span>
             <span>Humid (1500mm+)</span>
           </div>
        </div>
      </div>
      <div class="summary-chips-container">
        <div class="summary-chips">
          <div class="summary-chip summary-chip--safe"><span class="summary-chip__count">${counts.safe}</span> Safe</div>
          <div class="summary-chip summary-chip--moderate"><span class="summary-chip__count">${counts.moderate}</span> Moderate</div>
          <div class="summary-chip summary-chip--high"><span class="summary-chip__count">${counts.high}</span> High Risk</div>
        </div>
      </div>
    `;
  }

  init();

})();
