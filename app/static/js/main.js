import { fetchStatus, fetchResultados, startTraining } from './api.js';
import { renderChartBarrasProjecao, renderChartCenarios, renderChartSazonal, renderChartHeatmap } from './charts.js';
import { initThemeToggle, showLoader, updateProgress, updateStats, populateTable } from './ui.js';

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
  renderChartBarrasProjecao(data.projecao_cenarios);
  renderChartCenarios(data.projecao_cenarios);
  renderChartSazonal(data.dist_sazonal);
  renderChartHeatmap(data.dist_sazonal);
}

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  loadAndRender();

  // Re-render quando o tema mudar
  window.addEventListener("themeChanged", () => {
    if (cachedData) renderAll(cachedData);
  });

  const btnTreinar = document.getElementById("btnTreinar");
  if (btnTreinar) {
    btnTreinar.addEventListener("click", () => {
      if (!confirm("Isso iniciará o treinamento com os últimos parâmetros da base. Deseja continuar?")) return;
      
      btnTreinar.disabled = true;
      btnTreinar.innerHTML = "⏳ Processando...";
      updateProgress(5);

      startTraining("rapido", "421600", 
        (prog) => { // onProgress
          updateProgress(prog.pct);
        },
        () => { // onComplete
          updateProgress(100);
          setTimeout(() => {
            updateProgress(0);
            btnTreinar.disabled = false;
            btnTreinar.innerHTML = "▶ Reprocessar ML (Otimizado)";
            loadAndRender(); // Recarrega os gráficos!
          }, 1000);
        },
        (errMsg) => { // onError
          alert("Erro: " + errMsg);
          btnTreinar.disabled = false;
          btnTreinar.innerHTML = "▶ Reprocessar ML";
          updateProgress(0);
        }
      );
    });
  }
});
