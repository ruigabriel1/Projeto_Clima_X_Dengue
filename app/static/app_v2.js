/* ═══════════════════════════════════════════════════════════
   Prodígia — Frontend Logic (SSE + Chart.js)
   ═══════════════════════════════════════════════════════════ */

const $ = (s) => document.querySelector(s);

let chartBarrasProjecao = null;
let chartCenarios = null;
let chartSazonal = null;
let chartHeatmap = null;

function getCSSVar(name) {
  return getComputedStyle(document.body).getPropertyValue(name).trim();
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
  
  // Tenta carregar resultados pré-computados ao abrir a tela
  carregarResultados(true);
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
  $("#results").style.display = "none";

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
async function carregarResultados(silent = false) {
  try {
    const r = await fetch("/api/resultados");
    const d = await r.json();
    if (d.error) {
      if (!silent) alert(d.error);
      return;
    }

    $("#results").style.display = "block";
    $("#results").classList.add("visible");
    
    const safeRender = (fn, data, name) => {
      try {
        if (data) fn(data);
      } catch (e) {
        console.error(`Erro ao renderizar ${name}:`, e);
      }
    };

    safeRender(renderMetricas, d.metricas, "Métricas");
    safeRender(renderTabelaHistorica, d.tabela_epidemiologica, "Tabela Histórica");
    safeRender(renderChartSazonal, d.dist_sazonal, "Sazonalidade");
    safeRender(renderChartHeatmap, d.dist_sazonal, "Heatmap");
    
    safeRender(renderTabelaProjecao, d.projecao_cenarios, "Tabela de Projeção");
    safeRender(renderChartBarrasProjecao, d.projecao_cenarios, "Gráfico Barras Projeção");
    safeRender(renderChartCenarios, d.projecao_cenarios, "Projeções de Cenários");
    safeRender(renderTabelaCorrelacao, d.tabela_correlacao, "Tabela Correlação");
    
  } catch (e) {
    console.error("Erro geral em carregarResultados:", e);
    alert("Houve um erro ao renderizar os resultados: " + e.message);
  }
}

// ── Gráficos e Tabelas ──

function renderMetricas(m) {
  if (!m) return;
  const r2El = document.getElementById("r2-val");
  const maeEl = document.getElementById("mae-val");
  const rmseEl = document.getElementById("rmse-val");
  
  if (r2El) r2El.innerText = m.r2 !== undefined ? m.r2 : "-";
  if (maeEl) maeEl.innerText = m.mae !== undefined ? m.mae : "-";
  if (rmseEl) rmseEl.innerText = m.rmse !== undefined ? m.rmse : "-";
}

function renderTabelaHistorica(data) {
  const tbody = $("#tabelaHistorica tbody");
  if (!tbody || !data) return;
  tbody.innerHTML = "";

  data.forEach((r) => {
    if (r.ano < 2026) return;
    const tr = document.createElement("tr");
    tr.innerHTML = 
      "<td><strong>" + r.ano + "</strong></td>" +
      "<td>" + (r.casos !== null ? r.casos.toLocaleString('pt-BR') : "-") + "</td>" +
      "<td>" + (r.incidencia !== null ? r.incidencia.toLocaleString('pt-BR', {minimumFractionDigits:1, maximumFractionDigits:1}) : "-") + "</td>" +
      "<td>" + (r.pico !== null ? r.pico.toLocaleString('pt-BR') : "-") + "</td>" +
      "<td>" + (r.mes_pico || "-") + "</td>" +
      "<td>" + (r.variacao !== null ? (r.variacao > 0 ? "+" : "") + r.variacao.toLocaleString('pt-BR', {minimumFractionDigits:1, maximumFractionDigits:1}) + "%" : "-") + "</td>";
    tbody.appendChild(tr);
  });
}

function renderTabelaCorrelacao(data) {
  const tbody = $("#tabelaCorrelacao tbody");
  if (!tbody) return;
  tbody.innerHTML = "";

  data.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = 
      "<td>" + r.preditor + "</td>" +
      "<td>" + r.lag + "</td>" +
      "<td>" + r.r_pearson + "</td>" +
      "<td>" + r.p_valor_ajustado + "</td>";
    tbody.appendChild(tr);
  });
}

function renderTabelaProjecao(data) {
  const tbody = $("#tabelaProjecao tbody");
  if (!tbody || !data || !data.ssp126) return;
  tbody.innerHTML = "";

  const anos = data.ssp126.anos;
  const filterIdx = anos.map((a, i) => (a >= 2026 && a <= 2030) ? i : -1).filter(i => i !== -1);

  for (let i of filterIdx) {
    const val1 = data.ssp126.casos[i];
    const val2 = data.ssp245 ? data.ssp245.casos[i] : "-";
    const val3 = data.ssp585 ? data.ssp585.casos[i] : "-";

    const tr = document.createElement("tr");
    tr.innerHTML = 
      "<td><strong>" + anos[i] + "</strong></td>" +
      "<td class='num' style='color: #27ae60; font-weight: bold;'>" + val1 + "</td>" +
      "<td class='num' style='color: #e67e22; font-weight: bold;'>" + val2 + "</td>" +
      "<td class='num' style='color: #c0392b; font-weight: bold;'>" + val3 + "</td>";
    tbody.appendChild(tr);
  }
}

function getPlotlyConfig() {
  return { responsive: true, displayModeBar: false };
}

function getPlotlyLayout(title, yTitle, isDark) {
  const fontColor = isDark ? "#e0e0e0" : "#2c3e50";
  const paperBg = isDark ? "#1e293b" : "#ffffff";
  const plotBg = isDark ? "#1e293b" : "#ffffff";
  const gridColor = isDark ? "#334155" : "#e0e0e0";

  return {
    title: { text: title, font: { color: fontColor } },
    paper_bgcolor: paperBg,
    plot_bgcolor: plotBg,
    font: { color: fontColor, family: "Inter, sans-serif" },
    xaxis: { gridcolor: gridColor, tickfont: { color: fontColor } },
    yaxis: { title: yTitle, gridcolor: gridColor, tickfont: { color: fontColor } },
    margin: { t: 50, b: 40, l: 50, r: 20 },
    legend: { font: { color: fontColor } }
  };
}

function renderChartBarrasProjecao(data) {
  if (!data || !data.ssp126) return;
  const isDark = document.body.classList.contains("dark-mode");
  
  const anos = data.ssp126.anos;
  const filterIdx = anos.map((a, i) => (a >= 2026 && a <= 2030) ? i : -1).filter(i => i !== -1);
  const xLabels = filterIdx.map(i => anos[i]);

  const traces = [
    { x: xLabels, y: filterIdx.map(i => data.ssp126.casos[i]), type: "bar", name: "SSP1-2.6", marker: { color: "#27ae60" } }
  ];
  if(data.ssp245) traces.push({ x: xLabels, y: filterIdx.map(i => data.ssp245.casos[i]), type: "bar", name: "SSP2-4.5", marker: { color: "#e67e22" } });
  if(data.ssp585) traces.push({ x: xLabels, y: filterIdx.map(i => data.ssp585.casos[i]), type: "bar", name: "SSP5-8.5", marker: { color: "#c0392b" } });

  const layout = getPlotlyLayout("Comparativo de Casos Projetados", "Casos Anuais", isDark);
  layout.barmode = "group";
  
  Plotly.newPlot("chartBarrasProjecao", traces, layout, getPlotlyConfig());
}

function renderChartCenarios(data) {
  if (!data || !data.ssp126) return;
  const isDark = document.body.classList.contains("dark-mode");
  
  const anos = data.ssp126.anos;
  const filterIdx = anos.map((a, i) => (a >= 2026 && a <= 2030) ? i : -1).filter(i => i !== -1);
  const xLabels = filterIdx.map(i => anos[i]);

  const traces = [
    { x: xLabels, y: filterIdx.map(i => data.ssp126.casos[i]), type: "scatter", mode: "lines+markers", name: "SSP1-2.6", line: { color: "#27ae60", width: 3 } }
  ];
  if(data.ssp245) traces.push({ x: xLabels, y: filterIdx.map(i => data.ssp245.casos[i]), type: "scatter", mode: "lines+markers", name: "SSP2-4.5", line: { color: "#e67e22", width: 3, dash: "dash" } });
  if(data.ssp585) traces.push({ x: xLabels, y: filterIdx.map(i => data.ssp585.casos[i]), type: "scatter", mode: "lines+markers", name: "SSP5-8.5", line: { color: "#c0392b", width: 3, dash: "dot" } });

  const layout = getPlotlyLayout("Evolução dos Cenários Climáticos (2026-2030)", "Casos Anuais Projetados", isDark);
  layout.legend = { orientation: "h", y: -0.2 };
  
  Plotly.newPlot("chartCenarios", traces, layout, getPlotlyConfig());
}

function renderChartSazonal(data) {
  if (!data || !data.meses) return;
  const isDark = document.body.classList.contains("dark-mode");
  
  const mesNomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  
  // Highlight peak
  const maxCasos = Math.max(...data.casos_mean);
  const colors = data.casos_mean.map(v => v === maxCasos ? "#c0392b" : "#3498db");

  const traces = [
    { 
      x: mesNomes, 
      y: data.casos_mean, 
      type: "bar", 
      name: "Casos Projetados", 
      marker: { color: colors },
      yaxis: "y"
    },
    { 
      x: mesNomes, 
      y: data.temp_mean, 
      type: "scatter", 
      mode: "lines+markers", 
      name: "Temperatura Média", 
      line: { color: "#e74c3c", width: 3 },
      yaxis: "y2"
    }
  ];

  const layout = getPlotlyLayout("", "Casos Médios Mensais", isDark);
  const gridColor = isDark ? "#334155" : "#e0e0e0";
  
  layout.yaxis2 = {
    title: "Temperatura Média (°C)",
    overlaying: "y",
    side: "right",
    gridcolor: gridColor,
    tickfont: { color: isDark ? "#e0e0e0" : "#2c3e50" }
  };
  layout.legend = { orientation: "h", y: -0.2 };

  Plotly.newPlot("chartSazonal", traces, layout, getPlotlyConfig());
}

function renderChartHeatmap(data) {
  if (!data || !data.heatmap) return;
  const isDark = document.body.classList.contains("dark-mode");
  
  const matriz = data.heatmap;
  let anosSet = new Set();
  
  matriz.forEach(item => {
    if(item.ano >= 2026 && item.ano <= 2030) {
      anosSet.add(item.ano);
    }
  });
  
  const anosArr = Array.from(anosSet).sort();
  const mesNomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  
  // Plotly heatmap expects 2D array [y][x] where y is mes, x is ano
  let zData = [];
  for (let m = 1; m <= 12; m++) {
    let row = [];
    for (let ano of anosArr) {
      const match = matriz.find(i => i.ano === ano && i.mes === m);
      row.push(match ? match.casos : null);
    }
    zData.push(row);
  }

  const traces = [{
    x: anosArr,
    y: mesNomes,
    z: zData,
    type: "heatmap",
    colorscale: "YlOrRd",
    hoverongaps: false
  }];

  const layout = getPlotlyLayout("", "Mês", isDark);
  layout.xaxis.tickmode = "array";
  layout.xaxis.tickvals = anosArr;
  
  Plotly.newPlot("chartHeatmap", traces, layout, getPlotlyConfig());
}

