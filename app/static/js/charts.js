// Módulo responsável pela renderização com Plotly.js

function isDarkMode() {
  return document.body.classList.contains("dark-mode");
}

function getCSSVar(name) {
  return getComputedStyle(document.body).getPropertyValue(name).trim();
}

function getPlotlyConfig() {
  return { responsive: true, displayModeBar: false };
}

function getPlotlyLayout(title, yTitle) {
  const dark = isDarkMode();
  const fontColor = dark ? "#f8fafc" : "#1e293b";
  const paperBg = "transparent";
  const plotBg = "transparent";
  const gridColor = dark ? "#334155" : "#e2e8f0";

  return {
    title: { text: title, font: { color: fontColor, size: 16, family: "Inter" } },
    paper_bgcolor: paperBg,
    plot_bgcolor: plotBg,
    font: { color: fontColor, family: "Inter, sans-serif" },
    xaxis: { gridcolor: gridColor, tickfont: { color: fontColor } },
    yaxis: { title: yTitle, gridcolor: gridColor, tickfont: { color: fontColor } },
    margin: { t: 50, b: 40, l: 50, r: 20 },
    legend: { font: { color: fontColor } }
  };
}

export function renderChartBarrasProjecao(data) {
  if (!data || !data.ssp126) return;
  const anos = data.ssp126.anos;
  const filterIdx = anos.map((a, i) => (a >= 2026 && a <= 2030) ? i : -1).filter(i => i !== -1);
  const xLabels = filterIdx.map(i => anos[i]);

  const traces = [
    { x: xLabels, y: filterIdx.map(i => data.ssp126.casos[i]), type: "bar", name: "SSP1-2.6", marker: { color: "#10b981" } }
  ];
  if (data.ssp245) traces.push({ x: xLabels, y: filterIdx.map(i => data.ssp245.casos[i]), type: "bar", name: "SSP2-4.5", marker: { color: "#f59e0b" } });
  if (data.ssp585) traces.push({ x: xLabels, y: filterIdx.map(i => data.ssp585.casos[i]), type: "bar", name: "SSP5-8.5", marker: { color: "#ef4444" } });

  const layout = getPlotlyLayout("Comparativo de Casos Projetados", "Casos Anuais");
  layout.barmode = "group";
  layout.legend = { orientation: "h", y: -0.2 };
  
  Plotly.react("chartBarrasProjecao", traces, layout, getPlotlyConfig());
}

export function renderChartCenarios(data) {
  if (!data || !data.ssp126) return;
  
  const anos = data.ssp126.anos;
  const filterIdx = anos.map((a, i) => (a >= 2026 && a <= 2030) ? i : -1).filter(i => i !== -1);
  const xLabels = filterIdx.map(i => anos[i]);

  const traces = [
    { x: xLabels, y: filterIdx.map(i => data.ssp126.casos[i]), type: "scatter", mode: "lines+markers", name: "SSP1-2.6", line: { color: "#10b981", width: 3 } }
  ];
  if(data.ssp245) traces.push({ x: xLabels, y: filterIdx.map(i => data.ssp245.casos[i]), type: "scatter", mode: "lines+markers", name: "SSP2-4.5", line: { color: "#f59e0b", width: 3, dash: "dash" } });
  if(data.ssp585) traces.push({ x: xLabels, y: filterIdx.map(i => data.ssp585.casos[i]), type: "scatter", mode: "lines+markers", name: "SSP5-8.5", line: { color: "#ef4444", width: 3, dash: "dot" } });

  const layout = getPlotlyLayout("Evolução dos Cenários Climáticos (2026-2030)", "Casos Anuais Projetados");
  layout.legend = { orientation: "h", y: -0.2 };
  
  Plotly.react("chartCenarios", traces, layout, getPlotlyConfig());
}

export function renderChartSazonal(data) {
  if (!data || !data.meses) return;
  
  const mesNomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  const maxCasos = Math.max(...data.casos_mean);
  const colors = data.casos_mean.map(v => v === maxCasos ? "#ef4444" : "#3b82f6");

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
      line: { color: "#f59e0b", width: 3 },
      yaxis: "y2"
    }
  ];

  const layout = getPlotlyLayout("", "Casos Médios Mensais");
  layout.yaxis2 = {
    title: "Temperatura Média (°C)",
    overlaying: "y",
    side: "right",
    gridcolor: isDarkMode() ? "#334155" : "#e2e8f0",
    tickfont: { color: isDarkMode() ? "#f8fafc" : "#1e293b" }
  };
  layout.legend = { orientation: "h", y: -0.2 };

  Plotly.react("chartSazonal", traces, layout, getPlotlyConfig());
}

export function renderChartHeatmap(data) {
  if (!data || !data.heatmap) return;
  
  const matriz = data.heatmap;
  let anosSet = new Set();
  matriz.forEach(item => { if(item.ano >= 2026 && item.ano <= 2030) anosSet.add(item.ano); });
  
  const anosArr = Array.from(anosSet).sort();
  const mesNomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  
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
    colorscale: isDarkMode() ? "YlOrRd" : "OrRd",
    hoverongaps: false
  }];

  const layout = getPlotlyLayout("", "Mês");
  layout.xaxis.tickmode = "array";
  layout.xaxis.tickvals = anosArr;
  
  Plotly.react("chartHeatmap", traces, layout, getPlotlyConfig());
}
