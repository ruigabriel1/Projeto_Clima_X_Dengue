// Aplicação v5.1: previsão por mês, ranking, cenário de 5 anos e confiabilidade.
// Consome a API do próprio servidor (/api/*). Sem estado no servidor.

const MESES_LONGO = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
  "setembro", "outubro", "novembro", "dezembro"];
const NIVEIS = {
  baixo: { txt: "Baixo", cls: "nv-baixo", cor: "#10b981" }, medio: { txt: "Médio", cls: "nv-medio", cor: "#f59e0b" },
  alto: { txt: "Alto", cls: "nv-alto", cor: "#f97316" }, critico: { txt: "Crítico", cls: "nv-critico", cor: "#ef4444" },
};
const REGIAO = "Região Sul (PR, SC, RS)";
const COR = { modelo: "#3b82f6", persist: "#94a3b8", info: "#f59e0b", faixa: "rgba(59,130,246,0.18)", real: "#1e293b" };

const $ = (id) => document.getElementById(id);
const fmt = (v, d = 0) => (v == null || Number.isNaN(v) ? "–" : Number(v).toLocaleString("pt-BR", { maximumFractionDigits: d, minimumFractionDigits: d }));
const pct = (v) => (v == null ? "–" : `${fmt(v * 100, 0)}%`);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const nomeMes = (ym) => { const [a, m] = ym.split("-").map(Number); return `${MESES_LONGO[m - 1]} de ${a}`; };
const layoutBase = { margin: { t: 40, r: 20, b: 50, l: 60 }, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "Inter, sans-serif", size: 12 }, legend: { orientation: "h", y: -0.2 } };
const cfgPlot = { displaylogo: false, responsive: true };

let municipios = [];           // [{codigo, nome, uf, populacao}]
const porRotulo = new Map();   // "Curitiba (PR)" -> codigo
let ultimoConsolidado = null;  // {dengue: "2026-09", ...}
const seq = { pv: 0, rk: 0, ce: 0, cf: 0 };   // só a resposta da requisição mais recente de cada aba é desenhada

async function api(path) {
  const r = await fetch(path);
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.detail ? (typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail)) : `Erro ${r.status}`);
  return j;
}

// Spinner por aba: só cobre a tela se a aba visível estiver carregando
const carregando = { previsao: 0, ranking: 0, cenario: 0, confiabilidade: 0 };
function atualizarLoader() {
  const ativa = document.querySelector(".tab.active")?.dataset.tab;
  $("loader").classList.toggle("active", (carregando[ativa] || 0) > 0);
}
function loader(aba, on) { carregando[aba] = Math.max(0, carregando[aba] + (on ? 1 : -1)); atualizarLoader(); }

function erro(el, e) { el.innerHTML = `<div class="alert alert-erro">⚠️ ${esc(e.message || e)}</div>`; }

// ------------------------------------------------------------------ navegação
function ativarAba(nome) {
  if (!$(`tab-${nome}`)) nome = "previsao";
  document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b.dataset.tab === nome));
  document.querySelectorAll(".tab-panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${nome}`));
  atualizarLoader();
  // Plotly desenha errado em div escondida: redimensiona ao mostrar
  document.querySelectorAll(`#tab-${nome} .js-plotly-plot`).forEach((g) => Plotly.Plots.resize(g));
  if (nome === "ranking" && !$("rkTabela").dataset.ok) carregarRanking();
  if (nome === "cenario" && !$("ceGrafico").dataset.ok) carregarCenario();
  if (nome === "confiabilidade" && !$("cfTabela").dataset.ok) carregarConfiabilidade();
  try { localStorage.setItem("prodigia_aba", nome); } catch (_) { /* sem storage */ }
}

// ------------------------------------------------------------------ inicialização
async function iniciar() {
  document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => ativarAba(b.dataset.tab)));
  $("pvBotao").addEventListener("click", carregarPrevisao);
  $("rkBotao").addEventListener("click", carregarRanking);
  $("ceBotao").addEventListener("click", carregarCenario);
  document.querySelectorAll("input[name=ceDelta]").forEach((r) => r.addEventListener("change", carregarCenario));
  $("cfDoenca").addEventListener("change", carregarConfiabilidade);
  $("pvDoenca").addEventListener("change", preencherMeses);

  try {
    const [mun, cfD, cfC] = await Promise.all([api("/api/municipios"), api("/api/confiabilidade?doenca=dengue"),
      api("/api/confiabilidade?doenca=chikungunya")]);
    municipios = mun;
    ultimoConsolidado = { dengue: cfD.ultimo_mes_consolidado, chikungunya: cfC.ultimo_mes_consolidado };
    $("infoModelo").textContent = `Modelo ${cfD.versao}, treinado com ${cfD.periodo_treino}. Último mês consolidado: ${nomeMes(cfD.ultimo_mes_consolidado)}.`;
  } catch (e) {
    $("infoModelo").textContent = `Modelo indisponível: ${e.message}`;
    return;
  }
  const opts = municipios.map((m) => { const r = `${m.nome} (${m.uf})`; porRotulo.set(r, m.codigo); return `<option value="${esc(r)}">`; });
  $("listaCidades").innerHTML = opts.join("");
  $("listaCidadesSul").innerHTML = `<option value="${REGIAO}">` + opts.join("");
  porRotulo.set(REGIAO, "sul");
  preencherMeses();
  $("pvCidade").value = "Curitiba (PR)";
  let aba = "previsao";
  try { aba = localStorage.getItem("prodigia_aba") || aba; } catch (_) { /* sem storage */ }
  ativarAba(aba);
  carregarPrevisao();
}

function preencherMeses() {
  const ult = ultimoConsolidado?.[$("pvDoenca").value] || "2026-09";
  const [a0, m0] = ult.split("-").map(Number);
  const sel = $("pvMes");
  const atual = sel.value;
  const ops = [];
  for (let k = 1; k <= 12 * 5 + 3; k++) {
    const idx = a0 * 12 + (m0 - 1) + k;
    const a = Math.floor(idx / 12), m = (idx % 12) + 1;
    const ym = `${a}-${String(m).padStart(2, "0")}`;
    const tag = k <= 3 ? ` · previsão (${k} ${k === 1 ? "mês" : "meses"})` : " · faixa histórica";
    ops.push(`<option value="${ym}">${MESES_LONGO[m - 1]} de ${a}${tag}</option>`);
  }
  sel.innerHTML = ops.join("");
  sel.value = [...sel.options].some((o) => o.value === atual) ? atual : sel.options[2]?.value;
}

function codigoDe(input) {
  const v = input.value.trim();
  if (porRotulo.has(v)) return porRotulo.get(v);
  const m = municipios.find((x) => x.nome && x.nome.toLowerCase() === v.toLowerCase());
  if (m) return m.codigo;
  if (/^\d{6,7}$/.test(v)) return v.slice(0, 6);
  return null;
}

// ------------------------------------------------------------------ 1. previsão por mês
async function carregarPrevisao() {
  const out = $("pvResultado");
  const codigo = codigoDe($("pvCidade"));
  if (!codigo) { erro(out, "Município não encontrado. Escolha um nome da lista."); return; }
  const doenca = $("pvDoenca").value;
  const [ano, mes] = $("pvMes").value.split("-").map(Number);
  const meu = ++seq.pv;
  loader("previsao", true);
  try {
    const [r, hist] = await Promise.all([
      api(`/api/previsao?codigo=${codigo}&doenca=${doenca}&ano=${ano}&mes=${mes}`),
      api(`/api/historico?codigo=${codigo}&doenca=${doenca}&meses=24`),
    ]);
    if (meu !== seq.pv) return;
    out.innerHTML = cartaoPrevisao(r);
    graficoPrevisao(r, hist);
  } catch (e) { erro(out, e); $("pvGraficoCard").hidden = true; }
  finally { loader("previsao", false); }
}

function cartaoPrevisao(r) {
  const titulo = `${esc(r.cidade)} · ${r.doenca === "dengue" ? "Dengue" : "Chikungunya"} · ${nomeMes(r.mes_alvo)}`;
  if (r.modo === "observado") {
    return `<div class="card-resultado"><div class="badge badge-obs">Já observado</div><h3>${titulo}</h3>
      <div class="big">${fmt(r.casos_reais)} <small>casos notificados</small></div><p class="muted">${esc(r.nota)}</p></div>`;
  }
  if (r.modo === "cenario") {
    const f = r.faixa_historica;
    const mesNome = MESES_LONGO[Number(r.mes_alvo.slice(5)) - 1];
    return `<div class="card-resultado"><div class="badge badge-cen">Faixa histórica · não é previsão</div><h3>${titulo}</h3>
      <div class="big">${fmt(f.p10)} – ${fmt(f.p90)} <small>casos (80% dos anos)</small></div>
      <p>Mediana histórica de ${mesNome}: <strong>${fmt(f.p50)}</strong> casos. Último mês observado (${nomeMes(r.ultimo_mes_observado)}): ${fmt(r.casos_persistencia)} casos.</p>
      <div class="alert alert-info">📅 A previsão do modelo para este mês fica disponível a partir de
        <strong>${new Date(r.disponivel_a_partir_de + "T12:00").toLocaleDateString("pt-BR")}</strong>,
        quando ${mesNome} estiver a 3 meses do último dado consolidado.</div>
      <p class="muted">${esc(r.nota)}</p></div>`;
  }
  const p = r.previsao, d = r.desempenho_horizonte?.teste_2026, n = NIVEIS[p.nivel_risco] || NIVEIS.baixo;
  const comp = d ? `
    <div class="mini-tabela">
      <div><span>Erro médio por cidade-mês (2026)</span><strong>${fmt(d.modelo?.mae, 1)}</strong> modelo · ${fmt(d.persistencia?.mae, 1)} persistência</div>
      <div><span>Acerto na ordem de risco (AUC 2026)</span><strong>${fmt(d.modelo?.auc, 2)}</strong> modelo · ${fmt(d.persistencia?.auc, 2)} persistência · ${fmt(d.auc_infodengue, 2)} InfoDengue</div>
      <div><span>Total previsto ÷ real (2026)</span><strong>${fmt(d.razao_previsto_real, 2)}×</strong> ${d.razao_previsto_real > 1.2 ? "(superestimou o ano de baixa)" : ""}</div>
      <div><span>Real dentro do intervalo de 90%</span><strong>${pct(d.cobertura_intervalo_90)}</strong> das cidades-mês</div>
    </div>` : "";
  const avisos = (p.avisos || []).map((a) => `<li>${esc(a)}</li>`).join("");
  return `<div class="card-resultado">
    <div class="badge badge-prev">Previsão do modelo · ${r.horizonte_meses} ${r.horizonte_meses === 1 ? "mês" : "meses"} à frente</div>
    <h3>${titulo}</h3>
    <div class="resultado-grid">
      <div><span class="label">Casos previstos</span><div class="big">${fmt(p.casos_previstos)}</div>
        <span class="muted">intervalo de 90%: ${fmt(p.intervalo_confianca[0])} a ${fmt(p.intervalo_confianca[1])}</span></div>
      <div><span class="label">Risco relativo à própria cidade</span><div class="nivel ${n.cls}">${n.txt}</div>
        <span class="muted">${pct(p.probabilidade_risco_alto)} de chance de passar de ${fmt(p.limiar_risco_incidencia_100k, 1)} casos/100 mil (P75 da cidade)</span></div>
      <div><span class="label">Referência ingênua</span><div class="big muted-num">${fmt(r.casos_persistencia)}</div>
        <span class="muted">casos em ${nomeMes(r.ultimo_mes_observado)} (último mês conhecido)</span></div>
    </div>
    <h4>Como o modelo se saiu neste horizonte no teste de 2026</h4>${comp}
    <p class="confiab ${p.confiabilidade === "baixa" ? "confiab-baixa" : ""}">Confiabilidade: <strong>${p.confiabilidade === "baixa" ? "baixa" : "normal"}</strong></p>
    ${avisos ? `<details><summary>Avisos (${p.avisos.length})</summary><ul>${avisos}</ul></details>` : ""}
    <p class="muted">${esc(r.nota)}</p></div>`;
}

function graficoPrevisao(r, hist) {
  $("pvGraficoCard").hidden = false;
  const x = hist.map((h) => h.mes + "-15"), y = hist.map((h) => h.casos);
  const traces = [{ x, y, name: "Observado", mode: "lines+markers", line: { color: COR.real, width: 2 }, marker: { size: 4 } }];
  const alvo = r.mes_alvo + "-15";
  if (r.modo === "previsao") {
    const p = r.previsao;
    traces.push({ x: [alvo], y: [p.casos_previstos], name: "Previsão (IC 90%)", mode: "markers",
      marker: { color: COR.modelo, size: 12 }, error_y: { type: "data", symmetric: false,
        array: [p.intervalo_confianca[1] - p.casos_previstos], arrayminus: [p.casos_previstos - p.intervalo_confianca[0]], color: COR.modelo } });
    traces.push({ x: [r.ultimo_mes_observado + "-15", alvo], y: [r.casos_persistencia, r.casos_persistencia], name: "Persistência",
      mode: "lines", line: { color: COR.persist, dash: "dot" } });
  } else if (r.modo === "cenario") {
    const f = r.faixa_historica;
    traces.push({ x: [alvo], y: [f.p50], name: "Faixa histórica (P10–P90)", mode: "markers",
      marker: { color: COR.persist, size: 12, symbol: "diamond" }, error_y: { type: "data", symmetric: false,
        array: [f.p90 - f.p50], arrayminus: [f.p50 - f.p10], color: COR.persist } });
  }
  Plotly.react("pvGrafico", traces, { ...layoutBase, title: { text: "Últimos 24 meses e o mês consultado", font: { size: 14 } },
    yaxis: { title: "Casos", rangemode: "tozero" }, xaxis: { type: "date", tickformat: "%b %Y" } }, cfgPlot);
}

// ------------------------------------------------------------------ 2. ranking
async function carregarRanking() {
  const doenca = $("rkDoenca").value, h = $("rkH").value, uf = $("rkUf").value, pop = $("rkPop").value;
  const meu = ++seq.rk;
  loader("ranking", true);
  try {
    const r = await api(`/api/ranking?doenca=${doenca}&h=${h}&pop_min=${pop}&limite=20${uf ? `&uf=${uf}` : ""}`);
    if (meu !== seq.rk) return;
    $("rkResumo").innerHTML = `<div class="alert alert-info">Previsão para <strong>${nomeMes(r.mes_alvo)}</strong>
      (${r.horizonte_meses} ${r.horizonte_meses === 1 ? "mês" : "meses"} à frente). Total previsto na Região Sul:
      <strong>${fmt(r.total_previsto)}</strong> casos de ${doenca}. O risco é <em>relativo ao histórico de cada cidade</em>:
      "alto" significa acima do que é comum ali, não necessariamente muitos casos. O filtro de população tira as cidades
      muito pequenas, onde 1 ou 2 casos já superam o padrão.</div>`;
    const tb = $("rkTabela").querySelector("tbody");
    tb.innerHTML = r.itens.map((it, i) => {
      const n = NIVEIS[it.nivel_risco] || NIVEIS.baixo;
      return `<tr><td>${i + 1}</td><td>${esc(it.cidade)}</td><td>${it.uf}</td><td><span class="nivel-sm ${n.cls}">${n.txt}</span></td>
        <td>${pct(it.probabilidade_risco_alto)}</td><td>${fmt(it.casos_previstos)} <small class="muted">(${fmt(it.intervalo_confianca[0])}–${fmt(it.intervalo_confianca[1])})</small></td>
        <td>${fmt(it.casos_persistencia)}</td><td>${fmt(it.incidencia_prevista_100k, 1)}</td></tr>`;
    }).join("") || `<tr><td colspan="8" class="muted">Nenhuma cidade com esses filtros.</td></tr>`;
    $("rkTabela").dataset.ok = "1";
    const itens = [...r.itens].reverse();
    Plotly.react("rkGrafico", [{
      type: "bar", orientation: "h", x: itens.map((i) => i.probabilidade_risco_alto * 100),
      y: itens.map((i) => `${i.cidade} (${i.uf})`), marker: { color: itens.map((i) => (NIVEIS[i.nivel_risco] || NIVEIS.baixo).cor) },
      hovertemplate: "%{y}<br>%{x:.0f}% de chance de risco alto<extra></extra>",
    }], { ...layoutBase, title: { text: "20 maiores probabilidades de risco alto", font: { size: 14 } },
      xaxis: { title: "Probabilidade (%)", range: [0, 100] }, margin: { ...layoutBase.margin, l: 200 }, showlegend: false }, cfgPlot);
  } catch (e) { erro($("rkResumo"), e); }
  finally { loader("ranking", false); }
}

// ------------------------------------------------------------------ 3. cenário de 5 anos
async function carregarCenario() {
  const codigo = codigoDe($("ceCidade"));
  if (!codigo) { erro($("ceAvisos"), "Local não encontrado. Escolha da lista."); return; }
  const doenca = $("ceDoenca").value;
  const delta = document.querySelector("input[name=ceDelta]:checked").value;
  loader("cenario", true);
  try {
    const reqs = [api(`/api/cenario?codigo=${codigo}&doenca=${doenca}&delta_temp=${delta}&anos=5`),
      api(`/api/historico?codigo=${codigo}&doenca=${doenca}&meses=36`)];
    if (delta !== "0") reqs.push(api(`/api/cenario?codigo=${codigo}&doenca=${doenca}&delta_temp=0&anos=5`));
    const meu = ++seq.ce;
    const [c, hist, base] = await Promise.all(reqs);
    if (meu !== seq.ce) return;
    const x = c.pontos.map((p) => p.mes + "-15");
    const traces = [
      { x, y: c.pontos.map((p) => p.p90), mode: "lines", line: { width: 0 }, showlegend: false, hoverinfo: "skip" },
      { x, y: c.pontos.map((p) => p.p10), mode: "lines", line: { width: 0 }, fill: "tonexty", fillcolor: COR.faixa,
        name: `Faixa P10–P90 (${c.anos_historico[0]}–${c.anos_historico[1]})`, hoverinfo: "skip" },
      { x, y: c.pontos.map((p) => p.p50), mode: "lines", name: delta === "0" ? "Mediana histórica" : `Mediana com +${delta} °C`,
        line: { color: COR.modelo, width: 2 }, customdata: c.pontos.map((p) => [p.p10, p.p90, p.fator_clima]),
        hovertemplate: "%{x|%b %Y}: %{y:.0f} casos (faixa %{customdata[0]:.0f}–%{customdata[1]:.0f}; fator clima %{customdata[2]:.2f})<extra></extra>" },
      { x: hist.map((h) => h.mes + "-15"), y: hist.map((h) => h.casos), mode: "lines", name: "Observado", line: { color: COR.real, width: 1.5 } },
    ];
    if (base) traces.splice(2, 0, { x, y: base.pontos.map((p) => p.p50), mode: "lines", name: "Mediana com clima atual", line: { color: COR.persist, dash: "dot" } });
    Plotly.react("ceGrafico", traces, { ...layoutBase, title: { text: `${c.cidade} · ${doenca}: o que costuma acontecer em cada mês`, font: { size: 14 } },
      yaxis: { title: "Casos por mês", rangemode: "tozero" }, xaxis: { type: "date", tickformat: "%b %Y" } }, cfgPlot);
    $("ceGrafico").dataset.ok = "1";
    const verao = c.pontos.filter((p) => [12, 1, 2, 3].includes(Number(p.mes.slice(5))));
    const media = (k) => (verao.length ? verao.reduce((s, p) => s + p[k], 0) / verao.length : 1);
    const resumo = delta === "0" ? "" : `<div class="alert alert-info">Com +${delta} °C, os meses de verão (dez–mar) teriam em média
      <strong>${fmt((media("fator_clima") - 1) * 100, 0)}% mais casos</strong> que o habitual
      (faixa de incerteza do efeito: ${fmt((media("fator_clima_lo") - 1) * 100, 0)}% a ${fmt((media("fator_clima_hi") - 1) * 100, 0)}%).</div>`;
    $("ceAvisos").innerHTML = resumo + (c.avisos || []).map((a) => `<p class="muted">• ${esc(a)}</p>`).join("") + `<p class="muted">${esc(c.nota)}</p>`;
  } catch (e) { erro($("ceAvisos"), e); }
  finally { loader("cenario", false); }
}

// ------------------------------------------------------------------ 4. confiabilidade
async function carregarConfiabilidade() {
  const doenca = $("cfDoenca").value;
  loader("confiabilidade", true);
  try {
    const meu = ++seq.cf;
    const c = await api(`/api/confiabilidade?doenca=${doenca}`);
    if (meu !== seq.cf) return;
    const hs = Object.keys(c.horizontes).sort();
    const t = (h) => c.horizontes[h]?.teste_2026 || {};
    const h1 = t("h1");
    const venceInfo = hs.every((h) => (t(h).modelo?.auc ?? 0) > (t(h).auc_infodengue ?? 1));
    const vencePers = hs.filter((h) => (t(h).modelo?.auc ?? 0) > (t(h).persistencia?.auc ?? 1)).length;
    $("cfResumo").innerHTML = `
      <div class="stat-card ${venceInfo ? "ok" : "ruim"}"><span class="stat-label">Contra o alerta oficial (InfoDengue)</span>
        <span class="stat-value">${venceInfo ? "Melhor" : "Não supera"}</span><span class="muted">na ordem de risco das cidades, ${venceInfo ? "em todos os horizontes" : "em parte dos horizontes"}</span></div>
      <div class="stat-card ${vencePers === hs.length ? "ok" : vencePers ? "medio" : "ruim"}"><span class="stat-label">Contra repetir o último mês</span>
        <span class="stat-value">${vencePers} de ${hs.length} horizontes</span><span class="muted">em que o modelo ordena o risco melhor (AUC)</span></div>
      <div class="stat-card ruim"><span class="stat-label">Total de casos em 2026 (1 mês à frente)</span>
        <span class="stat-value">${fmt(h1.razao_previsto_real, 1)}× o real</span><span class="muted">ano de baixa após epidemia: o modelo esperou mais casos</span></div>`;
    const rot = hs.map((h) => `${h.slice(1)} ${h === "h1" ? "mês" : "meses"} à frente`);
    Plotly.react("cfGrafico", [
      { type: "bar", name: "Modelo", x: rot, y: hs.map((h) => t(h).modelo?.auc), marker: { color: COR.modelo } },
      { type: "bar", name: "Persistência", x: rot, y: hs.map((h) => t(h).persistencia?.auc), marker: { color: COR.persist } },
      { type: "bar", name: "Alerta InfoDengue", x: rot, y: hs.map((h) => t(h).auc_infodengue), marker: { color: COR.info } },
    ], { ...layoutBase, barmode: "group", title: { text: "Acerto na ordem de risco (AUC) no teste de 2026 · 0,5 = acaso, 1 = perfeito", font: { size: 14 } },
      yaxis: { range: [0.4, 1], title: "AUC" }, shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: 0.5, y1: 0.5, line: { dash: "dot", color: "#94a3b8" } }] }, cfgPlot);
    const linhas = [
      ["AUC (ordem de risco)", (x) => fmt(x?.auc, 2)],
      ["Erro médio por cidade-mês (casos)", (x) => fmt(x?.mae, 1)],
      ["Skill na contagem vs persistência", (x) => fmt(x?.skill, 2)],
      ["Brier skill (probabilidade vs média histórica)", (x) => fmt(x?.brier_skill, 2)],
    ];
    $("cfTabela").querySelector("thead").innerHTML = `<tr><th>Teste 2026</th>${rot.map((r) => `<th colspan="2">${r}</th>`).join("")}</tr>
      <tr><th></th>${hs.map(() => "<th>Modelo</th><th>Persistência</th>").join("")}</tr>`;
    $("cfTabela").querySelector("tbody").innerHTML = linhas.map(([nome, f]) =>
      `<tr><td>${nome}</td>${hs.map((h) => `<td><strong>${f(t(h).modelo)}</strong></td><td>${f(t(h).persistencia)}</td>`).join("")}</tr>`).join("") +
      `<tr><td>Total previsto ÷ real</td>${hs.map((h) => `<td colspan="2">${fmt(t(h).razao_previsto_real, 2)}× (${fmt(t(h).casos_previstos)} vs ${fmt(t(h).casos_reais)})</td>`).join("")}</tr>
       <tr><td>Real dentro do intervalo de 90%</td>${hs.map((h) => `<td colspan="2">${pct(t(h).cobertura_intervalo_90)}</td>`).join("")}</tr>`;
    $("cfTabela").dataset.ok = "1";
    const vivo = c.ao_vivo?.length
      ? `<table class="data-table"><thead><tr><th>Horizonte</th><th>Meses avaliados</th><th>Previsto ÷ real</th><th>Erro médio (modelo · persistência)</th><th>Dentro do IC 90%</th></tr></thead><tbody>` +
        c.ao_vivo.map((v) => `<tr><td>${v.horizonte}</td><td>${v.meses.join(", ")}</td><td>${fmt(v.razao_previsto_real, 2)}×</td><td>${fmt(v.mae, 1)} · ${fmt(v.mae_persistencia, 1)}</td><td>${pct(v.cobertura_intervalo_90)}</td></tr>`).join("") + "</tbody></table>"
      : `<p class="muted">Ainda não há previsões emitidas cujo mês já tenha sido observado. A cada mês, as previsões são registradas
         antes de o mês acontecer e comparadas com o real quando os dados consolidam.</p>`;
    $("cfAoVivo").innerHTML = `<div class="chart-card"><h3>Desempenho ao vivo (previsões registradas antes do mês acontecer)</h3>${vivo}
      <p class="muted">Modelo ${esc(c.versao)} treinado com ${esc(c.periodo_treino)}; calibração: ${esc(c.calibracao)}.</p></div>`;
  } catch (e) { erro($("cfResumo"), e); }
  finally { loader("confiabilidade", false); }
}

document.addEventListener("DOMContentLoaded", iniciar);
