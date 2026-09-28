/* ═══════════════════════════════════════════
   Prodígia — Frontend Logic (SSE + Chart.js)
   ═══════════════════════════════════════════ */

const $ = (s) => document.querySelector(s);

let chartBarras = null;
let chartFI = null;
let chartSerieTemporal = null;
let chartClima = null;
let chartHeatmap = null;
let chartCenarios = null; // NOVO

function getCSSVar(name) {
  return getComputedStyle(document.body).getPropertyValue(name).trim();
}

// Register Matrix Plugin for Chart.js 4 if available
if (window["chartjs-chart-matrix"]) {
  Chart.register(window["chartjs-chart-matrix"].MatrixController, window["chartjs-chart-matrix"].MatrixElement);
}

// ── Inicialização ──
document.addEventListener("DOMContentLoaded", () => {
  // Inicializar Tema
  const isDark = localStorage.getItem("theme") === "dark";
  if (isDark) document.body.classList.add("dark-mode");
  const themeBtn = $("#themeToggle");
  if (themeBtn) {
    themeBtn.textContent = isDark ? "☀️ Tema Claro" : "🌙 Tema Escuro";
    themeBtn.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
      const dark = document.body.classList.contains("dark-mode");
      localStorage.setItem("theme", dark ? "dark" : "light");
      themeBtn.textContent = dark ? "☀️ Tema Claro" : "🌙 Tema Escuro";
      // Opcional: recarregar página para re-renderizar gráficos com novas cores
      window.location.reload(); 
    });
  }

  loadStatus();
  loadCidades();
  $("#btnTreinar").addEventListener("click", iniciarTreino);
  $("#advToggle").addEventListener("click", () => {
    const body = $("#advBody");
    body.classList.toggle("open");
    $("#advToggle").textContent = body.classList.contains("open")
      ? "▾ Filtro avançado (cidade específica)"
      : "▸ Filtro avançado (cidade específica)";
  });
});

// ── Status do Banco ──
async function loadStatus() {
  try {
    const r = await fetch("/api/status");
    const d = await r.json();
    $("#stCidades").textContent = d.saude_cidades.toLocaleString("pt-BR");
    $("#stRegistros").textContent = d.saude_registros.toLocaleString("pt-BR");
    $("#stClima").textContent = d.clima_registros.toLocaleString("pt-BR");
    $("#stPeriodo").textContent = d.periodo;
  } catch (e) {
    console.error("Erro ao carregar status:", e);
  }
}

// ── Lista de Cidades ──
async function loadCidades() {
  try {
    const r = await fetch("/api/cidades");
    const cidades = await r.json();
    const sel = $("#cidadeSelect");
    cidades.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c.code;
      opt.textContent = `${c.nome} (${c.code})`;
      sel.appendChild(opt);
    });
  } catch (e) {
    console.error("Erro ao carregar cidades:", e);
  }
}

// ── Treinamento ──
async function iniciarTreino() {
  const btn = $("#btnTreinar");
  btn.disabled = true;
  btn.textContent = "Treinando...";

  const wrap = $("#progressWrap");
  wrap.classList.add("active");
  $("#progressFill").style.width = "0%";
  $("#progressLabel").textContent = "Iniciando...";
  $("#results").classList.remove("visible");

  const modo = document.querySelector('input[name="modo"]:checked').value;
  const cidadeSel = $("#cidadeSelect").value;

  const body = { modo };
  if (cidadeSel) body.codigo_ibge = cidadeSel;

  try {
    await fetch("/api/treinar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    // Conectar ao SSE de progresso
    const es = new EventSource("/api/treinar/progresso");
    es.onmessage = (ev) => {
      const data = JSON.parse(ev.data);
      if (data.metricas) {
        document.getElementById('erro-abs-val').innerText = `±${data.metricas.erro_abs}`;
        
        const tendEl = document.getElementById('tendencia-val');
        tendEl.innerText = data.metricas.tendencia;
        tendEl.className = data.metricas.tendencia.includes("Acertou") ? "metric-value highlight-green" : "metric-value highlight-red";

        const riscoEl = document.getElementById('risco-val');
        riscoEl.innerText = data.metricas.risco;
        if (data.metricas.risco === "Baixo") {
            riscoEl.className = "metric-value highlight-green";
        } else if (data.metricas.risco === "Médio") {
            riscoEl.className = "metric-value highlight-yellow";
        } else {
            riscoEl.className = "metric-value highlight-red";
        }
      }
      if (data.pct >= 0) {
        $("#progressFill").style.width = data.pct + "%";
        $("#progressLabel").textContent = data.msg;
      }
      if (data.pct >= 100) {
        es.close();
        btn.disabled = false;
        btn.textContent = "Treinar Prodígia";
        carregarResultados();
      }
      if (data.pct === -1) {
        es.close();
        btn.disabled = false;
        btn.textContent = "Treinar Prodígia";
        $("#progressLabel").textContent = data.msg;
      }
    };
    es.onerror = () => {
      es.close();
      btn.disabled = false;
      btn.textContent = "Treinar Prodígia";
    };
  } catch (e) {
    btn.disabled = false;
    btn.textContent = "Treinar Prodígia";
    console.error("Erro ao iniciar treino:", e);
  }
}

// ── Resultados ──
async function carregarResultados() {
  try {
    const r = await fetch("/api/resultados");
    const d = await r.json();
    if (d.error) return;

    $("#results").style.display = "block";
    
    renderMetricas(d.metricas);
    
    const safeRender = (fn, data, name) => {
      try {
        if (data) fn(data);
      } catch (e) {
        console.error(`Erro ao renderizar ${name}:`, e);
      }
    };

    safeRender(renderTabelaProjecao, d.projecao_cenarios, "Tabela de Projeção");
    safeRender(renderChartBarrasProjecao, d.projecao_cenarios, "Gráfico Barras Projeção");
    safeRender(renderChartCenarios, d.projecao_cenarios, "Projeções de Cenários");
    safeRender(renderTabelaCorrelacao, d.tabela_correlacao, "Tabela Correlação");
    
  } catch (e) {
    console.error("Erro geral em carregarResultados:", e);
    alert("Houve um erro ao renderizar os resultados: " + e.message);
  }
}

function renderMetricas(m) {
  try {
      const erroEl = document.getElementById('erro-abs-val');
      if (erroEl) erroEl.innerText = `±${m.erro_abs}`;
      
      const tendEl = document.getElementById('tendencia-val');
      if (tendEl) {
          tendEl.innerText = m.tendencia;
          tendEl.className = m.tendencia.includes("Acertou") ? "metric-value highlight-green" : "metric-value highlight-red";
      }

      const riscoEl = document.getElementById('risco-val');
      if (riscoEl) {
          riscoEl.innerText = m.risco;
          if (m.risco === "Baixo") {
              riscoEl.className = "metric-value highlight-green";
          } else if (m.risco === "Médio") {
              riscoEl.className = "metric-value highlight-yellow";
          } else {
              riscoEl.className = "metric-value highlight-red";
          }
      }
  } catch(e) {
      console.error("Erro renderizando métricas:", e);
  }
}

function renderChartBarras(data) {
  const ctx = $("#chartBarras").getContext("2d");
  if (chartBarras) chartBarras.destroy();

  chartBarras = new Chart(ctx, {
    type: "bar",
    data: {
      labels: data.anos,
      datasets: [
        {
          label: "Casos Reais",
          data: data.real,
          backgroundColor: "rgba(52, 211, 153, 0.7)",
          borderColor: "rgba(52, 211, 153, 1)",
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: "Previsão XGBoost",
          data: data.previsto,
          backgroundColor: "rgba(88, 166, 255, 0.7)",
          borderColor: "rgba(88, 166, 255, 1)",
          borderWidth: 1,
          borderRadius: 4,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: getCSSVar('--text'), font: { family: "Inter" } } },
      },
      scales: {
        x: { ticks: { color: getCSSVar('--text-dim') }, grid: { color: "rgba(128,128,128,0.1)" } },
        y: { ticks: { color: getCSSVar('--text-dim') }, grid: { color: "rgba(128,128,128,0.1)" } },
      },
    },
  });
}

function renderChartFI(fiData) {
  const ctx = $("#chartFI").getContext("2d");
  if (chartFI) chartFI.destroy();

  const labels_map = {
    temp_media: "Temperatura Média",
    precipitacao: "Precipitação",
    enso: "ENSO (El Niño)",
    latitude: "Latitude",
    month_sin: "Sazonalidade (sin)",
    month_cos: "Sazonalidade (cos)",
    dengue_lag1: "Dengue Mês Anterior",
    dengue_lag2: "Dengue 2 Meses Antes",
    dengue_lag3: "Dengue 3 Meses Antes",
    temp_lag1: "Temp. Mês Anterior",
    prec_lag1: "Precip. Mês Anterior",
    enso_lag1: "ENSO Mês Anterior",
  };

  chartFI = new Chart(ctx, {
    type: "bar",
    data: {
      labels: fiData.map((f) => labels_map[f.feature] || f.feature),
      datasets: [
        {
          label: "Importância",
          data: fiData.map((f) => f.importance),
          backgroundColor: "rgba(88, 166, 255, 0.6)",
          borderColor: "rgba(88, 166, 255, 1)",
          borderWidth: 1,
          borderRadius: 4,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: { ticks: { color: getCSSVar('--text-dim') }, grid: { color: "rgba(128,128,128,0.1)" } },
        y: { ticks: { color: getCSSVar('--text'), font: { family: "Inter", size: 11 } }, grid: { display: false } },
      },
    },
  });
}

function renderTabelaEpidem(data) {
  const tbody = $("#tabelaEpidem tbody");
  tbody.innerHTML = "";
  data.forEach((row) => {
    const tr = document.createElement("tr");
    
    // Variação formatada
    let varHtml = "<td>-</td>";
    if (row.variacao !== null && row.variacao !== undefined) {
      const isUp = row.variacao > 0;
      const cls = isUp ? "var-up" : "var-down";
      varHtml = `<td class="${cls} num">${Math.abs(row.variacao).toFixed(1)}%</td>`;
    }

    tr.innerHTML = `
      <td>${row.ano}</td>
      <td class="num">${row.casos.toLocaleString("pt-BR")}</td>
      <td class="num">${row.incidencia !== null ? row.incidencia.toLocaleString("pt-BR") : "-"}</td>
      <td class="num">${row.pico.toLocaleString("pt-BR")}</td>
      <td>${row.mes_pico}</td>
      ${varHtml}
    `;
    tbody.appendChild(tr);
  });
}

function renderTabelaCorrelacao(data) {
  const tbody = $("#tabelaCorrelacao tbody");
  tbody.innerHTML = "";
  
  // Update header to ensure it matches
  const thead = $("#tabelaCorrelacao thead tr");
  if (thead) {
      thead.innerHTML = `<th>Preditor climático</th><th>Lag (meses)</th><th>r de Pearson</th><th>IC 95%</th><th>p-valor ajustado</th>`;
  }

  data.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.preditor}</td>
      <td class="num">${row.lag}</td>
      <td class="num">${row.r_pearson}</td>
      <td class="num">${row.ic_95 || "-"}</td>
      <td class="num">${row.p_valor_ajustado || "-"}</td>
    `;
    tbody.appendChild(tr);
  });
}

function renderChartSerieTemporal(data) {
  const ctx = $("#chartSerieTemporal").getContext("2d");
  if (chartSerieTemporal) chartSerieTemporal.destroy();

  // Create an array for the q95 line
  const q95Data = data.labels.map(() => data.q95);

  chartSerieTemporal = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.labels,
      datasets: [
        {
          label: "Teto Epidêmico (P95)",
          data: q95Data,
          borderColor: "rgba(255, 99, 132, 0.8)",
          borderWidth: 1.5,
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false,
        },
        {
          label: "Real (Mensal)",
          data: data.real,
          borderColor: "rgba(52, 211, 153, 1)",
          backgroundColor: "rgba(52, 211, 153, 0.1)",
          borderWidth: 2,
          pointRadius: 2,
          fill: true,
        },
        {
          label: "Previsto (XGBoost)",
          data: data.previsto,
          borderColor: "rgba(88, 166, 255, 1)",
          borderWidth: 2,
          borderDash: [3, 3],
          pointRadius: 2,
          fill: false,
        }
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: getCSSVar('--text'), font: { family: "Inter" } } },
      },
      scales: {
        x: { ticks: { color: getCSSVar('--text-dim') }, grid: { color: "rgba(128,128,128,0.1)" } },
        y: { ticks: { color: getCSSVar('--text-dim') }, grid: { color: "rgba(128,128,128,0.1)" } },
      },
    },
  });
}

function renderChartClima(data) {
  const ctx = $("#chartClima").getContext("2d");
  if (chartClima) chartClima.destroy();

  chartClima = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.labels,
      datasets: [
        {
          label: "Temperatura Média (°C)",
          data: data.temp_media,
          borderColor: "rgba(255, 159, 64, 1)",
          borderWidth: 2,
          pointRadius: 0,
          yAxisID: "y-temp",
        },
        {
          label: "Precipitação (mm)",
          data: data.precipitacao,
          borderColor: "rgba(54, 162, 235, 1)",
          backgroundColor: "rgba(54, 162, 235, 0.2)",
          borderWidth: 1,
          pointRadius: 0,
          fill: true,
          yAxisID: "y-precip",
        },
        {
          label: "Casos de Dengue",
          data: data.dengue,
          borderColor: "rgba(52, 211, 153, 1)",
          borderWidth: 2,
          borderDash: [2, 2],
          pointRadius: 0,
          yAxisID: "y-dengue",
        }
      ],
    },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: getCSSVar('--text'), font: { family: "Inter" } } },
      },
      scales: {
        x: { ticks: { color: getCSSVar('--text-dim') }, grid: { color: "rgba(128,128,128,0.1)" } },
        "y-temp": { 
          type: "linear", display: true, position: "left", 
          title: { display: true, text: "Temp (°C)", color: "rgba(255, 159, 64, 1)" },
          ticks: { color: "rgba(255, 159, 64, 1)" }, grid: { color: "rgba(128,128,128,0.1)" }
        },
        "y-precip": { 
          type: "linear", display: true, position: "right", 
          title: { display: true, text: "Precipitação (mm)", color: "rgba(54, 162, 235, 1)" },
          ticks: { color: "rgba(54, 162, 235, 1)" }, grid: { drawOnChartArea: false }
        },
        "y-dengue": {
          type: "linear", display: false, position: "right", // Oculto mas ajusta a escala
        }
      },
    },
  });
}

function renderChartSazonal(data) {
  const ctx = $("#chartHeatmap").getContext("2d");
  if (chartHeatmap) chartHeatmap.destroy();

  const MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  
  const labels = data.map(d => MESES[d.mes - 1]);
  const casos = data.map(d => d.casos);
  const temps = data.map(d => d.temp);

  // Achar o mês de pico para destacar
  const maxCasos = Math.max(...casos);
  const peakIndex = casos.indexOf(maxCasos);
  
  const bgColors = casos.map((c, i) => i === peakIndex ? "#c0392b" : "#5fa8d3");

  chartHeatmap = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          type: "bar",
          label: "Casos (média 2015-2025)",
          data: casos,
          backgroundColor: bgColors,
          yAxisID: "y",
          order: 2
        },
        {
          type: "line",
          label: "Temperatura média (°C)",
          data: temps,
          borderColor: "#e74c3c",
          backgroundColor: "#e74c3c",
          borderWidth: 2,
          pointRadius: 4,
          yAxisID: "y-temp",
          order: 1
        }
      ]
    },
    options: {
      responsive: true,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { labels: { color: getCSSVar('--text'), font: { family: "Inter" } } },
      },
      scales: {
        x: { 
          ticks: { color: getCSSVar('--text-dim') }, 
          grid: { display: false } 
        },
        y: { 
          type: "linear", 
          display: true, 
          position: "left",
          title: { display: true, text: "Casos médios mensais", color: "#5fa8d3" },
          ticks: { color: "#5fa8d3" }, 
          grid: { color: "rgba(128,128,128,0.1)", borderDash: [2, 2] }
        },
        "y-temp": { 
          type: "linear", 
          display: true, 
          position: "right",
          title: { display: true, text: "Temperatura média (°C)", color: "#e74c3c" },
          ticks: { color: "#e74c3c" }, 
          grid: { drawOnChartArea: false }
        }
      }
    }
  });
}

function renderChartCenarios(data) {
  const ctx = $("#chartCenarios").getContext("2d");
  if (chartCenarios) chartCenarios.destroy();

  const scenarios = Object.keys(data);
  if (scenarios.length === 0) return;

  const labels = data[scenarios[0]].anos;

  // Garantir a ordem dos datasets para o preenchimento (fill) funcionar bem
  const datasetConfig = {
    "ssp126": { 
      label: "Referência (linha de base)", 
      color: "#27ae60", 
      dash: [], 
      pointStyle: 'circle',
      fill: false
    },
    "ssp245": { 
      label: "Intermediário (+0,6 °C / +3% precip.)", 
      color: "#e67e22", 
      dash: [5, 5], 
      pointStyle: 'rect',
      fill: false
    },
    "ssp585": { 
      label: "Intensificado (+1,2 °C / +6% precip.)", 
      color: "#c0392b", 
      dash: [10, 5, 2, 5], 
      pointStyle: 'rectRot',
      // Preenche até o primeiro dataset (ssp126)
      fill: {
        target: 0,
        above: 'rgba(52, 152, 219, 0.15)'
      }
    }
  };

  // Precisamos colocar ssp126 primeiro, depois ssp245, depois ssp585
  const orderedScenarios = ["ssp126", "ssp245", "ssp585"].filter(sc => scenarios.includes(sc));
  
  const datasets = orderedScenarios.map(sc => {
    const config = datasetConfig[sc];
    return {
      label: config.label,
      data: data[sc].casos,
      borderColor: config.color,
      backgroundColor: config.color,
      borderWidth: 2,
      pointRadius: 4,
      pointStyle: config.pointStyle,
      borderDash: config.dash,
      fill: config.fill,
    };
  });

  chartCenarios = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: datasets,
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: getCSSVar('--text'), font: { family: "Inter" } } },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: { ticks: { color: getCSSVar('--text-dim') }, grid: { color: "rgba(128,128,128,0.1)" } },
        y: { 
          ticks: { color: getCSSVar('--text-dim') }, 
          grid: { color: "rgba(128,128,128,0.1)", borderDash: [2, 2] },
          min: 1000,
          max: 2000
        },
      },
    },
  });
}
function renderTabelaProjecao(data) {
  const tbody = document.querySelector("#tabelaProjecao tbody");
  if(!tbody) return;
  tbody.innerHTML = "";
  if(!data || !data.ssp126) return;
  
  const anos = data.ssp126.anos;
  for (let i = 0; i < anos.length; i++) {
    const tr = document.createElement("tr");
    const val1 = data.ssp126 ? Math.round(data.ssp126.casos[i]) : "-";
    const val2 = data.ssp245 ? Math.round(data.ssp245.casos[i]) : "-";
    const val3 = data.ssp585 ? Math.round(data.ssp585.casos[i]) : "-";
    tr.innerHTML = "<td><strong>" + anos[i] + "</strong></td>" +
      "<td class='num' style='color: #27ae60; font-weight: bold;'>" + val1 + "</td>" +
      "<td class='num' style='color: #e67e22; font-weight: bold;'>" + val2 + "</td>" +
      "<td class='num' style='color: #c0392b; font-weight: bold;'>" + val3 + "</td>";
    tbody.appendChild(tr);
  }
}

let cBarrasProjecao = null;
function renderChartBarrasProjecao(data) {
  const ctx = document.getElementById("chartBarrasProjecao");
  if(!ctx) return;
  if(cBarrasProjecao) cBarrasProjecao.destroy();
  if(!data || !data.ssp126) return;

  const anos = data.ssp126.anos;
  const datasets = [
    { label: "Referência (SSP126)", data: data.ssp126.casos, backgroundColor: "#27ae60" }
  ];
  if(data.ssp245) datasets.push({ label: "Intermediário (SSP245)", data: data.ssp245.casos, backgroundColor: "#e67e22" });
  if(data.ssp585) datasets.push({ label: "Intensificado (SSP585)", data: data.ssp585.casos, backgroundColor: "#c0392b" });

  cBarrasProjecao = new Chart(ctx, {
    type: "bar",
    data: { labels: anos, datasets: datasets },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: "#ecf0f1" } }
      },
      scales: {
        x: { ticks: { color: "#bdc3c7" }, grid: { color: "#34495e" } },
        y: { ticks: { color: "#bdc3c7" }, grid: { color: "#34495e" } }
      }
    }
  });
}
