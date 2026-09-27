/* ═══════════════════════════════════════════
   Prodígia — Frontend Logic (SSE + Chart.js)
   ═══════════════════════════════════════════ */

const $ = (s) => document.querySelector(s);

let chartBarras = null;
let chartFI = null;
let chartSerieTemporal = null;
let chartClima = null;
let chartHeatmap = null;

// Register Matrix Plugin for Chart.js 4 if available
if (window["chartjs-chart-matrix"]) {
  Chart.register(window["chartjs-chart-matrix"].MatrixController, window["chartjs-chart-matrix"].MatrixElement);
}

// ── Inicialização ──
document.addEventListener("DOMContentLoaded", () => {
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

    $("#results").classList.add("visible");
    
    renderMetricas(d.metricas);
    
    const safeRender = (fn, data, name) => {
      try {
        if (data) fn(data);
      } catch (e) {
        console.error(`Erro ao renderizar ${name}:`, e);
      }
    };

    safeRender(renderTabelaEpidem, d.tabela_epidemiologica, "Tabela Epidemiológica");
    safeRender(renderChartBarras, d.grafico_barras, "Gráfico Barras");
    safeRender(renderChartSerieTemporal, d.serie_temporal_mensal, "Série Temporal");
    safeRender(renderChartClima, d.dados_clima_mensal, "Gráfico Clima");
    safeRender(renderChartHeatmap, d.heatmap_sazonal, "Heatmap");
    safeRender(renderTabelaCorrelacao, d.tabela_correlacao, "Tabela Correlação");
    safeRender(renderChartFI, d.feature_importance, "Feature Importance");
    
  } catch (e) {
    console.error("Erro geral em carregarResultados:", e);
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
        legend: { labels: { color: "#d4dae3", font: { family: "Inter" } } },
      },
      scales: {
        x: { ticks: { color: "#6b7a8d" }, grid: { color: "rgba(255,255,255,0.04)" } },
        y: { ticks: { color: "#6b7a8d" }, grid: { color: "rgba(255,255,255,0.04)" } },
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
        x: { ticks: { color: "#6b7a8d" }, grid: { color: "rgba(255,255,255,0.04)" } },
        y: { ticks: { color: "#d4dae3", font: { family: "Inter", size: 11 } }, grid: { display: false } },
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
  data.forEach((row) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${row.preditor}</td>
      <td class="num">${row.lag}</td>
      <td class="num">${row.r_pearson.toFixed(3)}</td>
      <td class="num">${row.p_valor.toFixed(4)}</td>
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
        legend: { labels: { color: "#d4dae3", font: { family: "Inter" } } },
      },
      scales: {
        x: { ticks: { color: "#6b7a8d" }, grid: { color: "rgba(255,255,255,0.04)" } },
        y: { ticks: { color: "#6b7a8d" }, grid: { color: "rgba(255,255,255,0.04)" } },
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
        legend: { labels: { color: "#d4dae3", font: { family: "Inter" } } },
      },
      scales: {
        x: { ticks: { color: "#6b7a8d" }, grid: { color: "rgba(255,255,255,0.04)" } },
        "y-temp": { 
          type: "linear", display: true, position: "left", 
          title: { display: true, text: "Temp (°C)", color: "rgba(255, 159, 64, 1)" },
          ticks: { color: "rgba(255, 159, 64, 1)" }, grid: { color: "rgba(255,255,255,0.04)" }
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

function renderChartHeatmap(data) {
  const ctx = $("#chartHeatmap").getContext("2d");
  if (chartHeatmap) chartHeatmap.destroy();

  // We need to know the min and max year to setup scales properly
  const anos = data.map(d => d.x);
  const minAno = Math.min(...anos);
  const maxAno = Math.max(...anos);
  const maxCasos = Math.max(...data.map(d => d.v), 1);

  const MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];

  chartHeatmap = new Chart(ctx, {
    type: "matrix",
    data: {
      datasets: [{
        label: "Casos por mês/ano",
        data: data,
        backgroundColor(context) {
          const value = context.dataset.data[context.dataIndex].v;
          if (value === 0) return "rgba(255,255,255,0.05)";
          // Color scale from green to red based on intensity
          const intensity = Math.min(value / maxCasos, 1);
          // HSL: 120 is green, 0 is red.
          const hue = (1 - intensity) * 120;
          return `hsla(${hue}, 80%, 50%, 0.8)`;
        },
        borderColor: "rgba(255,255,255,0.1)",
        borderWidth: 1,
        width: ({chart}) => (chart.chartArea || {}).width / (maxAno - minAno + 1) - 1,
        height: ({chart}) => (chart.chartArea || {}).height / 12 - 1
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title() { return ""; },
            label(context) {
              const d = context.dataset.data[context.dataIndex];
              return `${MESES[d.y - 1]} ${d.x}: ${d.v} casos`;
            }
          }
        }
      },
      scales: {
        x: {
          type: "linear",
          min: minAno - 0.5,
          max: maxAno + 0.5,
          ticks: {
            stepSize: 1,
            color: "#6b7a8d",
            callback: function(value) { return value; }
          },
          grid: { display: false }
        },
        y: {
          type: "linear",
          min: 0.5,
          max: 12.5,
          ticks: {
            stepSize: 1,
            color: "#6b7a8d",
            callback: function(value) {
              return MESES[value - 1] || "";
            }
          },
          grid: { display: false }
        }
      }
    }
  });
}
