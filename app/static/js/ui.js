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
  setEl("periodoDados", data.periodo || "-");
  setEl("projecaoAte", data.projecao_ate || "-");
  
  // Métricas fora-da-amostra (expanding window)
  if (data.metricas) {
    setEl("metricR2", data.metricas.r2 != null ? data.metricas.r2.toFixed(3) : "-");
    setEl("metricMAE", data.metricas.mae != null ? data.metricas.mae.toFixed(1) : "-");
  }

  // Variação relativa do último período SSP2-4.5 vs baseline
  let txt = "-";
  const d = data.projecao_cenarios && data.projecao_cenarios.ssp245;
  if (d && d.delta_pct && d.delta_pct.length) {
    const v = d.delta_pct[d.delta_pct.length - 1];
    if (v != null) txt = `${v > 0 ? "+" : ""}${v.toFixed(1)}%`;
  }
  setEl("totalCasosProjetados", txt);
}

export function populateTable(data) {
  const tbody = document.querySelector("#resumoTable tbody");
  if (!tbody || !data) return;
  
  tbody.innerHTML = "";
  if (!data.projecao_cenarios || !data.projecao_cenarios.ssp126) return;

  const pc = data.projecao_cenarios;
  const anos = pc.ssp126.anos;
  const fmt = (sc, i) => {
    if (!pc[sc]) return "-";
    const c = pc[sc].casos[i];
    const dp = pc[sc].delta_pct ? pc[sc].delta_pct[i] : null;
    const casos = c != null ? Number(c).toLocaleString("pt-BR") : "-";
    return (dp != null && i > 0) ? `${casos} <small>(${dp > 0 ? "+" : ""}${dp.toFixed(1)}%)</small>` : casos;
  };
  
  for (let i = 0; i < anos.length; i++) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${anos[i]}</td>
      <td class="text-ssp126">${fmt("ssp126", i)}</td>
      <td class="text-ssp245">${fmt("ssp245", i)}</td>
      <td class="text-ssp585">${fmt("ssp585", i)}</td>
    `;
    tbody.appendChild(tr);
  }
}
