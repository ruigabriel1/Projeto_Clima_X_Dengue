import { fetchStatus, fetchResultados } from './api.js?v=5.4.1';
import { renderChartSazonal, renderChartHeatmap } from './charts.js?v=5.4.1';
import { showLoader, updateStats, populateTable } from './ui.js?v=5.4.1';

let cachedData = null;

async function loadAndRender() {
  showLoader(true);
  try {
    const data = await fetchResultados();
    if (data && !data.error) {
      cachedData = data;
      renderAll(data);
    } else {
      console.warn("Sem dados ainda:", data?.error);
    }
  } catch (e) {
    console.error("Erro carregando app:", e);
  } finally {
    showLoader(false);
  }
}

function renderAll(data) {
  if (!data) return;
  document.getElementById("chartsGrid").classList.add("visible");
  updateStats(data);
  populateTable(data);
  renderChartSazonal(data.dist_sazonal);
  renderChartHeatmap(data.dist_sazonal);
}

document.addEventListener("DOMContentLoaded", () => {
  loadAndRender();
});

// Tornar a função de download global para uso no onclick do HTML
window.downloadChart = function(divId, filename) {
  Plotly.downloadImage(divId, {format: 'png', width: 1200, height: 800, filename: filename});
};
