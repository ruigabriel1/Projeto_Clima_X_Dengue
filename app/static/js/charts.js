// Módulo responsável pela renderização com Plotly.js

// Módulo responsável pela renderização com Plotly.js usando paleta clara e clean (Plotly White)

function getPlotlyConfig() {
  return { responsive: true, displayModeBar: false };
}

function getPlotlyLayout(title, yTitle) {
  const fontColor = "#1e293b";
  const paperBg = "transparent";
  const plotBg = "transparent";
  const gridColor = "#e2e8f0";

  return {
    title: { text: title, font: { color: fontColor, size: 16, family: "Inter, sans-serif" } },
    paper_bgcolor: paperBg,
    plot_bgcolor: plotBg,
    font: { color: fontColor, family: "Inter, sans-serif" },
    xaxis: { gridcolor: gridColor, tickfont: { color: fontColor }, showline: true, linecolor: gridColor },
    yaxis: { title: yTitle, gridcolor: gridColor, tickfont: { color: fontColor }, showline: true, linecolor: gridColor },
    margin: { t: 50, b: 40, l: 60, r: 20 },
    legend: { font: { color: fontColor }, orientation: "h", y: -0.2 }
  };
}

export function renderChartCenarios(data) {
  if (!data || Object.keys(data).length === 0) return;
  
  // Encontra a chave principal para extrair os anos
  const cenarioBase = data.ssp126 || data.ssp245 || Object.values(data)[0];
  if (!cenarioBase) return;
  
  const anos = cenarioBase.anos;
  const filterIdx = anos.map((a, i) => (a >= 2026 && a <= 2030) ? i : -1).filter(i => i !== -1);
  const xLabels = filterIdx.map(i => anos[i]);

  const traces = [];
  
  // SSP1-2.6 (Otimista)
  if (data.ssp126) {
    traces.push({ x: xLabels, y: filterIdx.map(i => data.ssp126.casos[i]), type: "scatter", mode: "lines+markers", name: "SSP1-2.6 (Otimista)", line: { color: "#10b981", width: 2 } });
  }
  
  // SSP2-4.5 (Intermediário - mais grosso)
  if (data.ssp245) {
    traces.push({ x: xLabels, y: filterIdx.map(i => data.ssp245.casos[i]), type: "scatter", mode: "lines+markers", name: "SSP2-4.5 (Moderado)", line: { color: "#f59e0b", width: 4, dash: "dash" } });
  }

  // SSP3-7.0 (Intermediário/Pessimista)
  if (data.ssp370) {
    traces.push({ x: xLabels, y: filterIdx.map(i => data.ssp370.casos[i]), type: "scatter", mode: "lines+markers", name: "SSP3-7.0", line: { color: "#f97316", width: 2, dash: "dot" } });
  }

  // SSP5-8.5 (Pessimista - mais grosso)
  if (data.ssp585) {
    traces.push({ x: xLabels, y: filterIdx.map(i => data.ssp585.casos[i]), type: "scatter", mode: "lines+markers", name: "SSP5-8.5 (Pessimista)", line: { color: "#ef4444", width: 4, dash: "dashdot" } });
  }

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
    gridcolor: "#e2e8f0",
    tickfont: { color: "#1e293b" }
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
    colorscale: "OrRd",
    hoverongaps: false
  }];

  const layout = getPlotlyLayout("", "Mês");
  layout.xaxis.tickmode = "array";
  layout.xaxis.tickvals = anosArr;
  
  Plotly.react("chartHeatmap", traces, layout, getPlotlyConfig());
}
