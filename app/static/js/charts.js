// Módulo responsável pela renderização com Plotly.js

// Módulo responsável pela renderização com Plotly.js usando paleta clara e clean (Plotly White)

function getPlotlyConfig() {
  return { responsive: true, displayModeBar: false };
}

function getPlotlyLayout(title, yTitle) {
  const fontColor = "#55524b";
  const paperBg = "transparent";
  const plotBg = "transparent";
  const gridColor = "#e4e0d6";

  return {
    title: { text: title, font: { color: fontColor, size: 15, family: "'Source Serif 4', Georgia, serif" } },
    paper_bgcolor: paperBg,
    plot_bgcolor: plotBg,
    font: { color: fontColor, family: "Inter, sans-serif" },
    xaxis: { showgrid: false, tickfont: { color: fontColor }, showline: true, linecolor: gridColor },
    yaxis: { title: yTitle, gridcolor: gridColor, tickfont: { color: fontColor }, showline: true, linecolor: gridColor },
    margin: { t: 50, b: 40, l: 60, r: 20 },
    legend: { font: { color: fontColor }, orientation: "h", y: -0.2 }
  };
}

// Backtest fora-da-amostra: casos reais × previstos (expanding window), soma da região
export function renderChartBacktest(serie) {
  if (!serie || !serie.labels || serie.labels.length === 0) return;
  const traces = [
    { x: serie.labels, y: serie.real, type: "scatter", mode: "lines", name: "Casos reais", line: { color: "#1c1b18", width: 2 } },
    { x: serie.labels, y: serie.previsto, type: "scatter", mode: "lines", name: "Previsto (fora da amostra)", line: { color: "#0f6e6e", width: 2, dash: "dash" } },
  ];
  const layout = getPlotlyLayout("Backtest: real × previsto 1 mês à frente", "Casos mensais");
  Plotly.react("chartBacktest", traces, layout, getPlotlyConfig());
}

export function renderChartSazonal(data) {
  if (!data || !data.meses) return;
  
  const mesNomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  const maxCasos = Math.max(...data.casos_mean);
  const colors = data.casos_mean.map(v => v === maxCasos ? "#c2410c" : "#0f6e6e");

  const traces = [
    { 
      x: mesNomes, 
      y: data.casos_mean, 
      type: "bar", 
      name: "Casos Médios (histórico)", 
      marker: { color: colors },
      yaxis: "y"
    },
    { 
      x: mesNomes, 
      y: data.temp_mean, 
      type: "scatter", 
      mode: "lines+markers", 
      name: "Temperatura Média", 
      line: { color: "#b07a1d", width: 3 },
      yaxis: "y2"
    }
  ];

  const layout = getPlotlyLayout("", "Casos Médios Mensais");
  layout.yaxis2 = {
    title: "Temperatura Média (°C)",
    overlaying: "y",
    side: "right",
    gridcolor: "#e4e0d6",
    tickfont: { color: "#1c1b18" }
  };
  layout.legend = { orientation: "h", y: -0.2 };

  Plotly.react("chartSazonal", traces, layout, getPlotlyConfig());
}

export function renderChartHeatmap(data) {
  if (!data || !data.heatmap) return;
  
  const matriz = data.heatmap;
  // v4: períodos categóricos, preservando a ordem de exportação
  const anosArr = [];
  matriz.forEach(item => { const a = String(item.ano); if (!anosArr.includes(a)) anosArr.push(a); });
  const mesNomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  
  let zData = [];
  for (let m = 1; m <= 12; m++) {
    let row = [];
    for (let ano of anosArr) {
      const match = matriz.find(i => String(i.ano) === ano && i.mes === m);
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
  layout.xaxis.type = "category";
  
  Plotly.react("chartHeatmap", traces, layout, getPlotlyConfig());
}
