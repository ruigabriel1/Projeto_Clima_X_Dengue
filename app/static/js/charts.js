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

export function renderChartSazonal(data) {
  if (!data || !data.meses) return;
  
  const mesNomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"];
  const maxCasos = Math.max(...data.casos_mean);
  const colors = data.casos_mean.map(v => v === maxCasos ? "#c2410c" : "#0f6e6e");

  // Dois gráficos empilhados com o mesmo eixo de meses (nunca dois eixos y no mesmo gráfico)
  const casos = [{
    x: mesNomes, y: data.casos_mean, type: "bar", name: "Casos médios", marker: { color: colors },
    hovertemplate: "%{x}: %{y:,.0f} casos em média<extra></extra>",
  }];
  const lCasos = getPlotlyLayout("Casos médios por mês do ano", "Casos");
  lCasos.showlegend = false;
  lCasos.margin = { t: 40, b: 24, l: 60, r: 20 };
  Plotly.react("chartSazonal", casos, lCasos, getPlotlyConfig());

  const temp = [{
    x: mesNomes, y: data.temp_mean, type: "scatter", mode: "lines+markers", name: "Temperatura média",
    line: { color: "#b07a1d", width: 2 }, marker: { size: 6 },
    hovertemplate: "%{x}: %{y:.1f} °C<extra></extra>",
  }];
  const lTemp = getPlotlyLayout("Temperatura média por mês do ano", "°C");
  lTemp.showlegend = false;
  lTemp.margin = { t: 40, b: 30, l: 60, r: 20 };
  Plotly.react("chartTemp", temp, lTemp, getPlotlyConfig());
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
