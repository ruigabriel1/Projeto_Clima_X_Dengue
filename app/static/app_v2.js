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
async function carregarResultados() {
  try {
    const r = await fetch("/api/resultados");
    const d = await r.json();
    if (d.error) return;

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

function renderChartBarrasProjecao(data) {
  if (!data || !data.ssp126) return;
  const ctx = document.getElementById("chartBarrasProjecao");
  if (!ctx) return;

  if (chartBarrasProjecao) chartBarrasProjecao.destroy();

  const textColor = getCSSVar("--text-color") || "#2c3e50";
  const gridColor = getCSSVar("--border-color") || "#e0e0e0";

  const anos = data.ssp126.anos;
  const filterIdx = anos.map((a, i) => (a >= 2026 && a <= 2030) ? i : -1).filter(i => i !== -1);

  const labels = filterIdx.map(i => anos[i]);
  const datasets = [
    { label: "Referência (SSP126)", data: filterIdx.map(i => data.ssp126.casos[i]), backgroundColor: "#27ae60" }
  ];
  if(data.ssp245) datasets.push({ label: "Intermediário (SSP245)", data: filterIdx.map(i => data.ssp245.casos[i]), backgroundColor: "#e67e22" });
  if(data.ssp585) datasets.push({ label: "Intensificado (SSP585)", data: filterIdx.map(i => data.ssp585.casos[i]), backgroundColor: "#c0392b" });

  chartBarrasProjecao = new Chart(ctx, {
    type: "bar",
    data: { labels, datasets },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: textColor } },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: { ticks: { color: textColor }, grid: { color: gridColor } },
        y: { ticks: { color: textColor }, grid: { color: gridColor } }
      }
    }
  });
}

function renderChartCenarios(data) {
  if (!data || !data.ssp126) return;
  const ctx = document.getElementById("chartCenarios");
  if (!ctx) return;
  
  if (chartCenarios) chartCenarios.destroy();

  const textColor = getCSSVar("--text-color") || "#2c3e50";
  const gridColor = getCSSVar("--border-color") || "#e0e0e0";
  
  const anos = data.ssp126.anos;
  const filterIdx = anos.map((a, i) => (a >= 2026 && a <= 2030) ? i : -1).filter(i => i !== -1);
  
  const labels = filterIdx.map(i => anos[i]);

  const datasets = [];

  if (data.ssp585 && data.ssp126) {
    datasets.push({
      label: "Envelope de incerteza",
      data: filterIdx.map(i => data.ssp585.casos[i]),
      borderColor: "transparent",
      backgroundColor: "rgba(52, 152, 219, 0.15)",
      borderWidth: 0,
      pointRadius: 0,
      fill: 1
    });
  }

  datasets.push({
    label: "Referência (linha de base)",
    data: filterIdx.map(i => data.ssp126.casos[i]),
    borderColor: "#27ae60",
    backgroundColor: "#27ae60",
    borderWidth: 3,
    pointRadius: 5,
    tension: 0.1
  });

  if (data.ssp245) {
    datasets.push({
      label: "Intermediário (+0,6 °C / +3% precip.)",
      data: filterIdx.map(i => data.ssp245.casos[i]),
      borderColor: "#e67e22",
      backgroundColor: "#e67e22",
      borderWidth: 3,
      borderDash: [5, 5],
      pointRadius: 5,
      pointStyle: 'rect',
      tension: 0.1
    });
  }

  if (data.ssp585) {
    datasets.push({
      label: "Intensificado (+1,2 °C / +6% precip.)",
      data: filterIdx.map(i => data.ssp585.casos[i]),
      borderColor: "#c0392b",
      backgroundColor: "#c0392b",
      borderWidth: 3,
      borderDash: [2, 2],
      pointRadius: 5,
      pointStyle: 'rectRot',
      tension: 0.1
    });
  }

  chartCenarios = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: datasets
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: textColor } },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: { ticks: { color: textColor }, grid: { color: gridColor } },
        y: { 
            ticks: { color: textColor }, 
            grid: { color: gridColor },
            title: { display: true, text: "Casos anuais projetados", color: textColor }
        }
      }
    }
  });
}

function renderChartSazonal(data) {
  const ctx = document.getElementById("chartSazonal");
  if (!ctx || !data || !data.meses) return;
  if (chartSazonal) chartSazonal.destroy();

  const textColor = getCSSVar("--text-color") || "#2c3e50";
  const gridColor = getCSSVar("--border-color") || "#e0e0e0";
  
  // Nomes dos meses para o eixo X
  const mesNomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  
  chartSazonal = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: mesNomes,
      datasets: [
        {
          type: 'bar',
          label: 'Casos Projetados (média 2026-2030)',
          data: data.casos_mean,
          backgroundColor: data.casos_mean.map((v, i) => i === data.casos_mean.indexOf(Math.max(...data.casos_mean)) ? '#c0392b' : '#3498db'),
          yAxisID: 'y'
        },
        {
          type: 'line',
          label: 'Temperatura média (°C)',
          data: data.temp_mean,
          borderColor: '#e74c3c',
          backgroundColor: '#e74c3c',
          borderWidth: 2,
          pointRadius: 4,
          tension: 0.3,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { labels: { color: textColor } },
        tooltip: { mode: 'index', intersect: false }
      },
      scales: {
        x: { ticks: { color: textColor }, grid: { display: false } },
        y: { 
          type: 'linear', display: true, position: 'left', 
          ticks: { color: textColor }, grid: { color: gridColor },
          title: { display: true, text: "Casos médios mensais", color: "#3498db" }
        },
        y1: { 
          type: 'linear', display: true, position: 'right', 
          ticks: { color: textColor }, grid: { drawOnChartArea: false },
          title: { display: true, text: "Temperatura média (°C)", color: "#e74c3c" }
        }
      }
    }
  });
}

function renderChartHeatmap(data) {
  const ctx = document.getElementById("chartHeatmap");
  if (!ctx || !data || !data.heatmap) return;
  if (chartHeatmap) chartHeatmap.destroy();

  const textColor = getCSSVar("--text-color") || "#2c3e50";
  
  const matriz = data.heatmap;
  let parsed = [];
  let anosSet = new Set();
  
  matriz.forEach(item => {
    if(item.ano >= 2026 && item.ano <= 2030) {
      anosSet.add(item.ano);
      parsed.push({
        x: item.ano,
        y: item.mes,
        v: item.casos
      });
    }
  });
  
  const anosArr = Array.from(anosSet).sort();
  const mesNomes = ["", "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  
  chartHeatmap = new Chart(ctx, {
    type: 'matrix',
    data: {
      datasets: [{
        label: 'Casos Mensais',
        data: parsed,
        backgroundColor: function(c) {
          const val = c.dataset.data[c.dataIndex].v;
          if (val === null || val === undefined) return 'rgba(0,0,0,0.1)';
          if (val === 0) return '#27ae60';
          if (val < 10) return '#2ecc71';
          if (val < 50) return '#f1c40f';
          if (val < 100) return '#e67e22';
          return '#c0392b';
        },
        width: ({chart}) => (chart.chartArea || {}).width / anosArr.length - 1,
        height: ({chart}) => (chart.chartArea || {}).height / 12 - 1,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: () => '',
            label: (ctx) => {
              const v = ctx.dataset.data[ctx.dataIndex];
              return `${mesNomes[v.y]} ${v.x}: ${v.v} casos`;
            }
          }
        }
      },
      scales: {
        x: {
          type: 'linear',
          min: Math.min(...anosArr) - 0.5,
          max: Math.max(...anosArr) + 0.5,
          ticks: { stepSize: 1, callback: (v) => v, color: textColor },
          grid: { display: false }
        },
        y: {
          type: 'linear',
          min: 0.5,
          max: 12.5,
          ticks: { stepSize: 1, callback: (v) => mesNomes[v], color: textColor },
          grid: { display: false }
        }
      }
    }
  });
}
