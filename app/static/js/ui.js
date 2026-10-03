// Módulo de manipulação da UI

// Funções de loader e formatação de UI
export function showLoader(show) {
  const loader = document.getElementById("loader");
  if (loader) {
    if (show) loader.classList.add("active");
    else loader.classList.remove("active");
  }
}

export function updateStats(data) {
  if (!data) return;
  
  const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  
  setEl("totalMunicipios", data.n_cidades || "1");
  setEl("periodoDados", "2015 a 2025");
  setEl("projecaoAte", "2030");
  
  // Métricas LOYO
  if (data.metricas) {
    setEl("metricR2", data.metricas.r2 ? data.metricas.r2.toFixed(3) : "-");
    setEl("metricMAE", data.metricas.mae ? data.metricas.mae.toFixed(1) : "-");
  }

  // Calcular totais de casos projetados (SSP245)
  let totalSSP245 = 0;
  if (data.projecao_cenarios && data.projecao_cenarios.ssp245) {
    const d = data.projecao_cenarios.ssp245;
    totalSSP245 = d.casos.reduce((a,b) => a+b, 0);
  }
  setEl("totalCasosProjetados", totalSSP245.toLocaleString('pt-BR', {maximumFractionDigits: 0}));
}

export function populateTable(data) {
  const tbody = document.querySelector("#resumoTable tbody");
  if (!tbody || !data) return;
  
  tbody.innerHTML = "";
  if (!data.projecao_cenarios || !data.projecao_cenarios.ssp126) return;

  const anos = data.projecao_cenarios.ssp126.anos;
  
  for (let i = 0; i < anos.length; i++) {
    const ano = anos[i];
    if (ano < 2026 || ano > 2030) continue;

    const val126 = data.projecao_cenarios.ssp126.casos[i] || 0;
    const val245 = data.projecao_cenarios.ssp245 ? data.projecao_cenarios.ssp245.casos[i] : 0;
    const val585 = data.projecao_cenarios.ssp585 ? data.projecao_cenarios.ssp585.casos[i] : 0;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${ano}</td>
      <td class="text-ssp126">${val126.toFixed(0)}</td>
      <td class="text-ssp245">${val245.toFixed(0)}</td>
      <td class="text-ssp585">${val585.toFixed(0)}</td>
    `;
    tbody.appendChild(tr);
  }
}
