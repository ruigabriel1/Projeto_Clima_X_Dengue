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
  
  const tab = (data.tabela_epidemiologica || []).filter(r => !r.parcial);   // último ano COMPLETO
  const ultimo = tab.length ? tab[tab.length - 1] : null;

  setEl("totalMunicipios", data.n_cidades || "1");
  setEl("periodoDados", data.periodo || "-");
  setEl("casosUltimoAno", ultimo ? Number(ultimo.casos).toLocaleString("pt-BR") : "-");
  setEl("labelUltimoAno", ultimo ? `Casos em ${ultimo.ano}` : "Casos no último ano");
  setEl("incidenciaUltimoAno", ultimo && ultimo.incidencia != null ? ultimo.incidencia.toLocaleString("pt-BR") : "-");

  // Métricas fora-da-amostra (expanding window)
  if (data.metricas) {
    setEl("metricR2", data.metricas.r2 != null ? data.metricas.r2.toFixed(3) : "-");
    setEl("metricMAE", data.metricas.mae != null ? data.metricas.mae.toFixed(1) : "-");
  }
}

export function populateTable(data) {
  const tbody = document.querySelector("#resumoTable tbody");
  if (!tbody || !data) return;
  tbody.innerHTML = "";
  const fmtN = v => (v != null ? Number(v).toLocaleString("pt-BR") : "-");
  for (const r of data.tabela_epidemiologica || []) {
    const tr = document.createElement("tr");
    const varTxt = r.variacao != null ? `${r.variacao > 0 ? "+" : ""}${r.variacao.toFixed(1)}%` : "-";
    const ano = r.parcial ? `${r.ano}* <small>(${r.meses} meses, parcial)</small>` : r.ano;
    tr.innerHTML = `<td>${ano}</td><td>${fmtN(r.casos)}</td><td>${fmtN(r.incidencia)}</td>` +
                   `<td>${fmtN(r.pico)} (${r.mes_pico})</td><td>${varTxt}</td>`;
    tbody.appendChild(tr);
  }
}
