/* ═══════════════════════════════════════════
   Prodígia — Frontend Logic (SSE + Chart.js)
   ═══════════════════════════════════════════ */

const $ = (s) => document.querySelector(s);

let chartBarras = null;
let chartFI = null;

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

    renderMetricas(d.metricas);
    renderChartBarras(d.grafico_barras);
    renderChartFI(d.feature_importance);
    $("#results").classList.add("visible");
  } catch (e) {
    console.error("Erro ao carregar resultados:", e);
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
