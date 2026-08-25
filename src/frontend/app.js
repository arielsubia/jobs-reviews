"use strict";

/**
 * Jobs Reviews Dashboard
 * Client-side filtering and visualization of job application data.
 */

// State
let allApplications = [];
let filteredApplications = [];
let monthlyChart = null;
let statusChart = null;

// DOM Elements
const filterCompany = document.getElementById("filter-company");
const filterPosition = document.getElementById("filter-position");
const filterStatus = document.getElementById("filter-status");
const filterDateFrom = document.getElementById("filter-date-from");
const filterDateTo = document.getElementById("filter-date-to");
const btnClear = document.getElementById("btn-clear");
const resultCount = document.getElementById("result-count");
const metricTotal = document.getElementById("metric-total");
const metricPending = document.getElementById("metric-pending");
const metricRejected = document.getElementById("metric-rejected");
const metricFavorites = document.getElementById("metric-favorites");
const metricRate = document.getElementById("metric-rate");
const topCompaniesSection = document.getElementById("top-companies");
const topCompaniesList = document.getElementById("top-companies-list");
const applicationsList = document.getElementById("applications-list");

// Chart colors from Phil Dev palette
const CHART_COLORS = {
  accent: "#d4768a",
  accentHover: "#e0899b",
  pending: "#7a7a88",
  rejected: "#c0392b",
  favorite: "#d4768a",
  bar: "rgba(212, 118, 138, 0.7)",
  barBorder: "#d4768a",
};

// Initialize
document.addEventListener("DOMContentLoaded", async () => {
  await loadData();
  setupEventListeners();
  applyFilters();
});

/**
 * Load application data from JSON file.
 */
async function loadData() {
  try {
    const response = await fetch("data.json");
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    allApplications = await response.json();
  } catch (error) {
    console.error("Failed to load data:", error);
    showToast("Error al cargar los datos");
    allApplications = [];
  }
}

/**
 * Set up event listeners for filter inputs.
 */
function setupEventListeners() {
  let debounceTimer = null;

  const debounceFilter = () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(applyFilters, 300);
  };

  filterCompany.addEventListener("input", debounceFilter);
  filterPosition.addEventListener("input", debounceFilter);
  filterStatus.addEventListener("change", applyFilters);
  filterDateFrom.addEventListener("change", applyFilters);
  filterDateTo.addEventListener("change", applyFilters);

  btnClear.addEventListener("click", clearFilters);
}

/**
 * Clear all filters and reset view.
 */
function clearFilters() {
  filterCompany.value = "";
  filterPosition.value = "";
  filterStatus.value = "all";
  filterDateFrom.value = "";
  filterDateTo.value = "";
  applyFilters();
}

/**
 * Check if any filter is active.
 */
function hasActiveFilters() {
  return (
    filterCompany.value.trim() !== "" ||
    filterPosition.value.trim() !== "" ||
    filterStatus.value !== "all" ||
    filterDateFrom.value !== "" ||
    filterDateTo.value !== ""
  );
}

/**
 * Apply all filters and update the UI.
 */
function applyFilters() {
  const company = filterCompany.value.trim().toLowerCase();
  const position = filterPosition.value.trim().toLowerCase();
  const status = filterStatus.value;
  const dateFrom = filterDateFrom.value;
  const dateTo = filterDateTo.value;

  filteredApplications = allApplications.filter((app) => {
    if (company && !app.company.toLowerCase().includes(company)) {
      return false;
    }
    if (position && !app.position.toLowerCase().includes(position)) {
      return false;
    }
    if (status !== "all" && app.status !== status) {
      return false;
    }
    if (dateFrom && app.date < dateFrom) {
      return false;
    }
    if (dateTo && app.date > dateTo) {
      return false;
    }
    return true;
  });

  renderUI();
}

/**
 * Render all UI components based on filtered data.
 */
function renderUI() {
  renderResultCount();
  renderMetrics();
  renderMonthlyChart();
  renderStatusChart();
  renderTopCompanies();
  renderApplicationsList();
}

/**
 * Render the result count text.
 */
function renderResultCount() {
  const count = filteredApplications.length;
  const total = allApplications.length;

  if (hasActiveFilters()) {
    resultCount.textContent = `${count} de ${total} postulaciones`;
  } else {
    resultCount.textContent = `${total} postulaciones`;
  }
}

/**
 * Render metric cards.
 */
function renderMetrics() {
  const total = filteredApplications.length;
  const rejected = filteredApplications.filter((a) => a.status === "rechazada").length;
  const favorites = filteredApplications.filter((a) => a.status === "favorita").length;
  const pending = filteredApplications.filter((a) => a.status === "pendiente").length;
  const rate = total > 0 ? Math.round((rejected / total) * 100) : 0;

  metricTotal.textContent = total;
  metricPending.textContent = pending;
  metricRejected.textContent = rejected;
  metricFavorites.textContent = favorites;
  metricRate.textContent = `${rate}%`;
}

/**
 * Render the monthly bar chart.
 */
function renderMonthlyChart() {
  const monthCounts = {};

  filteredApplications.forEach((app) => {
    const month = app.date.substring(0, 7); // YYYY-MM
    monthCounts[month] = (monthCounts[month] || 0) + 1;
  });

  const sortedMonths = Object.keys(monthCounts).sort();
  const labels = sortedMonths.map((m) => {
    const [year, month] = m.split("-");
    const monthNames = [
      "Ene", "Feb", "Mar", "Abr", "May", "Jun",
      "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
    ];
    return `${monthNames[parseInt(month) - 1]} ${year.slice(2)}`;
  });
  const data = sortedMonths.map((m) => monthCounts[m]);

  const ctx = document.getElementById("chart-monthly").getContext("2d");

  if (monthlyChart) {
    monthlyChart.destroy();
  }

  monthlyChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Postulaciones",
          data,
          backgroundColor: CHART_COLORS.bar,
          borderColor: CHART_COLORS.barBorder,
          borderWidth: 1,
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { font: { size: 10 } },
        },
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1,
            font: { size: 10 },
          },
          grid: { color: "rgba(0,0,0,0.05)" },
        },
      },
    },
  });
}

/**
 * Render the status doughnut chart.
 */
function renderStatusChart() {
  const rejected = filteredApplications.filter((a) => a.status === "rechazada").length;
  const favorites = filteredApplications.filter((a) => a.status === "favorita").length;
  const pending = filteredApplications.filter((a) => a.status === "pendiente").length;

  const ctx = document.getElementById("chart-status").getContext("2d");

  if (statusChart) {
    statusChart.destroy();
  }

  statusChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Pendientes", "Rechazadas", "Favoritas"],
      datasets: [
        {
          data: [pending, rejected, favorites],
          backgroundColor: [
            CHART_COLORS.pending,
            CHART_COLORS.rejected,
            CHART_COLORS.favorite,
          ],
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: "bottom",
          labels: { font: { size: 11 }, padding: 12 },
        },
      },
    },
  });
}

/**
 * Render the top 10 companies section.
 */
function renderTopCompanies() {
  if (hasActiveFilters()) {
    topCompaniesSection.style.display = "none";
    return;
  }

  topCompaniesSection.style.display = "block";

  const companyCounts = {};
  allApplications.forEach((app) => {
    const name = app.company;
    companyCounts[name] = (companyCounts[name] || 0) + 1;
  });

  const sorted = Object.entries(companyCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  topCompaniesList.innerHTML = sorted
    .map(
      ([name, count]) => `
      <div class="top-item" role="button" tabindex="0" data-company="${escapeHtml(name)}">
        <span class="top-item-name">${escapeHtml(name)}</span>
        <span class="top-item-count">${count}</span>
      </div>
    `
    )
    .join("");

  // Click on a top company to filter
  topCompaniesList.querySelectorAll(".top-item").forEach((item) => {
    item.addEventListener("click", () => {
      filterCompany.value = item.dataset.company;
      applyFilters();
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
    item.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        item.click();
      }
    });
  });
}

/**
 * Render the filtered applications list.
 */
function renderApplicationsList() {
  // Sort by date descending (newest first)
  const sorted = [...filteredApplications].sort((a, b) => b.date.localeCompare(a.date));

  // Limit display to 100 items for performance on mobile
  const display = sorted.slice(0, 100);

  applicationsList.innerHTML = display
    .map(
      (app) => `
      <div class="app-item app-item--${app.status}">
        <div class="app-item-header">
          <span class="app-item-position" title="${escapeHtml(app.position)}">${escapeHtml(app.position)}</span>
          <span class="app-item-badge badge--${app.status}">${statusLabel(app.status)}</span>
        </div>
        <div class="app-item-details">
          <span class="app-item-company">${escapeHtml(app.company)}</span>
          <span class="app-item-date">${formatDate(app.date)}</span>
          ${app.rejection_date ? `<span>Rech: ${formatDate(app.rejection_date)}</span>` : ""}
        </div>
        ${app.channel ? `<div class="app-item-channel">${escapeHtml(app.channel)}</div>` : ""}
      </div>
    `
    )
    .join("");

  if (sorted.length > 100) {
    applicationsList.innerHTML += `
      <div class="app-item" style="text-align:center; color: var(--text-secondary); font-size: 0.75rem;">
        Mostrando 100 de ${sorted.length} resultados. Usa los filtros para acotar.
      </div>
    `;
  }

  if (sorted.length === 0) {
    applicationsList.innerHTML = `
      <div class="app-item" style="text-align:center; color: var(--text-secondary);">
        No se encontraron postulaciones con los filtros aplicados.
      </div>
    `;
  }
}

// Utility functions

/**
 * Format ISO date to DD/MM/YYYY for display.
 */
function formatDate(isoDate) {
  if (!isoDate) return "";
  const [year, month, day] = isoDate.split("-");
  return `${day}/${month}/${year}`;
}

/**
 * Get a human-readable status label.
 */
function statusLabel(status) {
  const labels = {
    pendiente: "Pendiente",
    rechazada: "Rechazada",
    favorita: "Favorita",
  };
  return labels[status] || status;
}

/**
 * Escape HTML to prevent XSS.
 */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Show a toast notification.
 */
function showToast(message, duration = 3000) {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, duration);
}


// ============================================================
// Voice Search (Web Speech API)
// ============================================================

/**
 * Initialize voice search if supported by the browser.
 */
function initVoiceSearch() {
  const btnVoice = document.getElementById("btn-voice");
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (!SpeechRecognition) {
    // Browser doesn't support Speech API — hide the button
    btnVoice.style.display = "none";
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.lang = "es-AR";
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  let isListening = false;

  btnVoice.addEventListener("click", () => {
    if (isListening) {
      recognition.stop();
      return;
    }

    try {
      recognition.start();
    } catch (error) {
      showToast("Error al iniciar reconocimiento de voz");
    }
  });

  recognition.addEventListener("start", () => {
    isListening = true;
    btnVoice.classList.add("listening");
    btnVoice.setAttribute("aria-label", "Escuchando... toca para detener");
  });

  recognition.addEventListener("end", () => {
    isListening = false;
    btnVoice.classList.remove("listening");
    btnVoice.setAttribute("aria-label", "Búsqueda por voz");
  });

  recognition.addEventListener("result", (event) => {
    const transcript = event.results[0][0].transcript.trim();
    if (transcript) {
      filterCompany.value = transcript;
      applyFilters();
      showToast(`Búsqueda: "${transcript}"`);
    }
  });

  recognition.addEventListener("error", (event) => {
    isListening = false;
    btnVoice.classList.remove("listening");
    btnVoice.setAttribute("aria-label", "Búsqueda por voz");

    const errorMessages = {
      "not-allowed": "Permiso de micrófono denegado",
      "no-speech": "No se detectó voz. Intentá de nuevo",
      "audio-capture": "No se encontró micrófono",
      "network": "Error de red para reconocimiento de voz",
    };

    const message = errorMessages[event.error] || "Error de reconocimiento de voz";
    showToast(message);
  });
}

// Initialize voice search after DOM is ready
document.addEventListener("DOMContentLoaded", initVoiceSearch);
