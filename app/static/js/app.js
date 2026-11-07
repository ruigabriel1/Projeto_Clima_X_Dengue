// Aplicação Prodígia: previsão por mês, ranking, cenário de 5 anos e confiabilidade.
// Consome a API do próprio servidor (/api/*). Sem estado no servidor.

const MESES_LONGO = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
  "setembro", "outubro", "novembro", "dezembro"];
const SVG = (d) => `<svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg>`;
const ICONE = {
  baixo: SVG('<path d="M5 12l5 5 9-10"/>'), medio: SVG('<path d="M6 12h12"/>'),
  alto: SVG('<path d="M12 19V5M6 11l6-6 6 6"/>'), critico: SVG('<path d="M12 5v9M12 19h.01"/>'),
  aviso: SVG('<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18h.01"/>'),
  info: SVG('<circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7.5h.01"/>'),
  calendario: SVG('<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>'),
};
const NIVEIS = {
  baixo: { txt: "Baixo", cls: "nv-baixo", cor: "#2f7d4f" }, medio: { txt: "Médio", cls: "nv-medio", cor: "#a96c12" },
  alto: { txt: "Alto", cls: "nv-alto", cor: "#c2410c" }, critico: { txt: "Crítico", cls: "nv-critico", cor: "#9b1c1c" },
};
const ORDEM_NIVEL = ["baixo", "medio", "alto", "critico"];
const REGIAO = "Região Sul (PR, SC, RS)";
const COR = { modelo: "#0f6e6e", persist: "#4a6fa5", info: "#b07a1d", faixa: "rgba(15,110,110,0.14)", real: "#1c1b18",
  grade: "#e4e0d6", texto: "#55524b" };

const $ = (id) => document.getElementById(id);
const fmt = (v, d = 0) => (v == null || Number.isNaN(v) ? "–" : Number(v).toLocaleString("pt-BR", { maximumFractionDigits: d, minimumFractionDigits: d }));
const pct = (v) => (v == null ? "–" : `${fmt(v * 100, 0)}%`);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const nomeMes = (ym) => { const [a, m] = ym.split("-").map(Number); return `${MESES_LONGO[m - 1]} de ${a}`; };
const nomeDoenca = (d) => (d === "dengue" ? "dengue" : "chikungunya");
const layoutBase = {
  margin: { t: 44, r: 16, b: 48, l: 56 }, paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
  font: { family: "Inter, sans-serif", size: 12, color: COR.texto },
  title: { font: { family: "'Source Serif 4', Georgia, serif", size: 15, color: "#1c1b18" }, x: 0, xanchor: "left" },
  legend: { orientation: "h", y: -0.18 },
  xaxis: { showgrid: false, linecolor: COR.grade, zeroline: false },
  yaxis: { gridcolor: COR.grade, linecolor: COR.grade, zeroline: false },
  hoverlabel: { bgcolor: "#fffdf9", bordercolor: COR.grade, font: { family: "Inter, sans-serif", color: "#1c1b18" } },
};
const titulo = (t) => ({ ...layoutBase.title, text: t });
const cfgPlot = { displaylogo: false, responsive: true, modeBarButtonsToRemove: ["lasso2d", "select2d"] };

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

function erro(el, e) { el.innerHTML = `<div class="alert alert-erro">${ICONE.aviso}<div>${esc(e.message || e)}</div></div>`; }
const alerta = (tipo, html) => `<div class="alert alert-${tipo}">${ICONE[tipo === "aviso" ? "aviso" : "info"]}<div>${html}</div></div>`;
const seloNivel = (nivel, pequeno = false) => {
  const n = NIVEIS[nivel] || NIVEIS.baixo;
  return `<span class="${pequeno ? "nivel-sm" : "nivel"} ${n.cls}">${ICONE[nivel] || ICONE.baixo}${n.txt}</span>`;
};

// ------------------------------------------------------------------ navegação
function ativarAba(nome) {
  if (!$(`tab-${nome}`)) nome = "previsao";
  document.querySelectorAll(".tab").forEach((b) => {
    const on = b.dataset.tab === nome;
    b.classList.toggle("active", on);
    b.setAttribute("aria-selected", on ? "true" : "false");
  });
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
  $("pvDoenca").addEventListener("change", () => { preencherMeses(); carregarPrevisao(); });
  $("pvMes").addEventListener("change", carregarPrevisao);
  $("pvCidade").addEventListener("change", () => { if (codigoDe($("pvCidade"))) carregarPrevisao(); });
  $("pvCidade").addEventListener("focus", (e) => e.target.select());

  try {
    const [mun, cfD, cfC] = await Promise.all([api("/api/municipios"), api("/api/confiabilidade?doenca=dengue"),
      api("/api/confiabilidade?doenca=chikungunya")]);
    municipios = mun;
    ultimoConsolidado = { dengue: cfD.ultimo_mes_consolidado, chikungunya: cfC.ultimo_mes_consolidado };
    $("infoModelo").textContent = `Modelo ${cfD.versao}, treinado com ${cfD.periodo_treino}. Último mês consolidado: ${nomeMes(cfD.ultimo_mes_consolidado)}.`;
    $("topoDado").innerHTML = `Dados até <b>${nomeMes(cfD.ultimo_mes_consolidado)}</b> · modelo ${esc(cfD.versao)}`;
  } catch (e) {
    $("infoModelo").textContent = `Modelo indisponível: ${e.message}`;
    $("topoDado").textContent = "Modelo indisponível";
    erro($("pvResultado"), `Modelo indisponível: ${e.message}`);
    return;
  }
  const rotulos = municipios.map((m) => { const r = `${m.nome} (${m.uf})`; porRotulo.set(r, m.codigo); return r; });
  porRotulo.set(REGIAO, "sul");
  autocompletar($("pvCidade"), rotulos);
  autocompletar($("ceCidade"), [REGIAO, ...rotulos]);
  preencherMeses();
  $("pvCidade").value = "Curitiba (PR)";
  let aba = "previsao";
  try { aba = localStorage.getItem("prodigia_aba") || aba; } catch (_) { /* sem storage */ }
  ativarAba(aba);
  carregarPrevisao();
}

// ------------------------------------------------------------------ lista de sugestões dos municípios
// Substitui o <datalist>, que o Chrome desenha como uma janela escura e solta, sem aceitar estilo.
const semAcento = (s) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const MAX_SUGESTOES = 60;

function autocompletar(input, opcoes) {
  const chaves = opcoes.map((o) => [o, semAcento(o)]);
  const lista = document.createElement("ul");
  lista.className = "sugestoes";
  lista.id = `${input.id}-sugestoes`;
  lista.setAttribute("role", "listbox");
  lista.hidden = true;
  input.setAttribute("aria-controls", lista.id);
  input.parentElement.classList.add("ac-campo");
  input.parentElement.appendChild(lista);
  let itens = [], ativo = -1;

  const fechar = () => { lista.hidden = true; input.setAttribute("aria-expanded", "false"); ativo = -1; };
  const marcar = (i) => {
    ativo = i;
    [...lista.children].forEach((li, k) => li.classList.toggle("ativo", k === i));
    if (i >= 0) {
      const li = lista.children[i];   // rola só a lista (scrollIntoView rolaria a página inteira)
      if (li.offsetTop < lista.scrollTop) lista.scrollTop = li.offsetTop - 4;
      else if (li.offsetTop + li.offsetHeight > lista.scrollTop + lista.clientHeight) lista.scrollTop = li.offsetTop + li.offsetHeight - lista.clientHeight + 4;
      input.setAttribute("aria-activedescendant", li.id);
    }
  };
  const escolher = (valor) => {
    input.value = valor;
    fechar();
    input.dispatchEvent(new Event("change", { bubbles: true }));
  };
  const abrir = () => {
    const q = semAcento(input.value.trim());
    const exato = chaves.some(([o]) => o === input.value);   // já escolhido: mostra a lista toda
    const comeca = [], contem = [];
    for (const [o, k] of chaves) {
      if (!q || exato) comeca.push(o);
      else if (k.startsWith(q)) comeca.push(o);
      else if (k.includes(q)) contem.push(o);
    }
    itens = exato ? comeca : [...comeca, ...contem].slice(0, MAX_SUGESTOES);   // escolhido: lista toda, na posição dele
    lista.innerHTML = itens.length
      ? itens.map((o, k) => `<li role="option" id="${lista.id}-${k}" data-v="${esc(o)}"${o === input.value ? ' aria-selected="true"' : ""}>${esc(o)}</li>`).join("")
      : `<li class="vazio">Nenhum município com esse nome</li>`;
    lista.hidden = false;
    input.setAttribute("aria-expanded", "true");
    lista.scrollTop = 0;
    const i = itens.indexOf(input.value);
    marcar(i >= 0 ? i : (q ? 0 : -1));   // digitando: a 1ª sugestão já fica pronta para o Enter
    if (i >= 0) lista.scrollTop = Math.max(0, lista.children[i].offsetTop - lista.clientHeight / 2);
  };

  input.addEventListener("focus", () => { input.select(); abrir(); });
  input.addEventListener("input", abrir);
  input.addEventListener("blur", () => setTimeout(fechar, 120));
  input.addEventListener("keydown", (e) => {
    if (lista.hidden && (e.key === "ArrowDown" || e.key === "ArrowUp")) { abrir(); e.preventDefault(); return; }
    if (e.key === "ArrowDown") { marcar(Math.min(itens.length - 1, ativo + 1)); e.preventDefault(); }
    else if (e.key === "ArrowUp") { marcar(Math.max(0, ativo - 1)); e.preventDefault(); }
    else if (e.key === "Enter" && !lista.hidden && itens.length) { escolher(itens[Math.max(0, ativo)]); e.preventDefault(); }
    else if (e.key === "Escape") fechar();
  });
  lista.addEventListener("mousedown", (e) => e.preventDefault());   // não perde o foco antes do clique
  lista.addEventListener("click", (e) => {
    const li = e.target.closest("li[data-v]");
    if (li) escolher(li.dataset.v);
  });
}

function preencherMeses() {
  const ult = ultimoConsolidado?.[$("pvDoenca").value] || "2026-09";
  const [a0, m0] = ult.split("-").map(Number);
  const sel = $("pvMes");
  const atual = sel.value;
  const prev = [], faixa = [];
  for (let k = 1; k <= 12 * 5 + 3; k++) {
    const idx = a0 * 12 + (m0 - 1) + k;
    const a = Math.floor(idx / 12), m = (idx % 12) + 1;
    const op = `<option value="${a}-${String(m).padStart(2, "0")}">${MESES_LONGO[m - 1]} de ${a}</option>`;
    (k <= 3 ? prev : faixa).push(op);
  }
  sel.innerHTML = `<optgroup label="Previsão do modelo (até 3 meses)">${prev.join("")}</optgroup>` +
    `<optgroup label="Faixa histórica (4 meses ou mais)">${faixa.join("")}</optgroup>`;
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

// ------------------------------------------------------------------ faixa do intervalo (escala logarítmica)
function faixaIntervalo({ lo, hi, centro, pers, hist = false }) {
  const vals = [lo, hi, centro, pers].filter((v) => v != null && !Number.isNaN(v));
  const L = (v) => Math.log10(Math.max(0, v) + 1);
  const vmin = Math.min(...vals.map(L)), vmax = Math.max(...vals.map(L));
  const folga = (vmax - vmin || 1) * 0.06;
  const a = vmin - folga, b = vmax + folga;
  const pos = (v) => Math.min(98, Math.max(2, (100 * (L(v) - a)) / (b - a)));
  const pLo = pos(lo), pHi = pos(hi), pC = pos(centro);
  let html = `<div class="eixo"></div><div class="intervalo${hist ? " hist" : ""}" style="left:${pLo}%;width:${Math.max(1, pHi - pLo)}%"></div>`;
  if (pers != null) {
    const pP = pos(pers);
    const perto = (x) => Math.abs(pP - x) < 9;
    const embaixo = !(perto(pLo) || perto(pHi));
    html += `<div class="marca-p" style="left:${pP}%"></div>`;
    if (embaixo || !perto(pC)) html += `<div class="etq ${embaixo ? "baixo" : "cima"} pers" style="left:${pP}%">${fmt(pers)}</div>`;
  }
  html += `<div class="ponto${hist ? " hist" : ""}" style="left:${pC}%"></div><div class="etq cima" style="left:${pC}%"><b>${fmt(centro)}</b></div>`;
  html += `<div class="etq baixo" style="left:${pLo}%">${fmt(lo)}</div>`;
  if (pHi - pLo > 6) html += `<div class="etq baixo" style="left:${pHi}%">${fmt(hi)}</div>`;
  return `<div class="faixa num" role="img" aria-label="Intervalo de ${fmt(lo)} a ${fmt(hi)}, valor central ${fmt(centro)}">${html}</div>`;
}

// ------------------------------------------------------------------ 1. previsão por mês
async function carregarPrevisao() {
  const out = $("pvResultado");
  const codigo = codigoDe($("pvCidade"));
  if (!codigo) { erro(out, "Município não encontrado. Escolha um nome da lista."); return; }
  const doenca = $("pvDoenca").value;
  const [ano, mes] = $("pvMes").value.split("-").map(Number);
  const meu = ++seq.pv;
  const primeira = !!out.querySelector(".aquecendo");   // a mensagem de aquecimento já explica a espera
  if (!primeira) loader("previsao", true);
  try {
    const [r, hist] = await Promise.all([
      api(`/api/previsao?codigo=${codigo}&doenca=${doenca}&ano=${ano}&mes=${mes}`),
      api(`/api/historico?codigo=${codigo}&doenca=${doenca}&meses=24`),
    ]);
    if (meu !== seq.pv) return;
    out.innerHTML = cartaoPrevisao(r);
    graficoPrevisao(r, hist);
  } catch (e) { erro(out, e); $("pvGraficoCard").hidden = true; }
  finally { if (!primeira) loader("previsao", false); }
}

function cartaoPrevisao(r) {
  if (r.modo === "observado") {
    return `<div class="card-resultado"><span class="selo-modo obs">Já observado</span>
      <span class="rotulo">Casos notificados em ${nomeMes(r.mes_alvo)}</span>
      <div class="big">${fmt(r.casos_reais)}<small>casos</small></div><p class="nota">${esc(r.nota)}</p></div>`;
  }
  if (r.modo === "cenario") {
    const f = r.faixa_historica;
    const mesNome = MESES_LONGO[Number(r.mes_alvo.slice(5)) - 1];
    const disp = new Date(r.disponivel_a_partir_de + "T12:00").toLocaleDateString("pt-BR");
    return `<div class="grade-prev">
      <section class="card-resultado"><span class="selo-modo cen">Faixa histórica · não é previsão</span>
        <span class="rotulo">O que costuma acontecer em ${mesNome}</span>
        <div class="big faixa-num">${fmt(f.p10)} – ${fmt(f.p90)}<small>casos (80% dos anos)</small></div>
        ${faixaIntervalo({ lo: f.p10, hi: f.p90, centro: f.p50, pers: r.casos_persistencia, hist: true })}
        <div class="legenda"><span><i style="background:#55524b"></i>Mediana histórica: ${fmt(f.p50)}</span>
          <span><i style="background:#e9e6de;border:1px solid #d3cec2"></i>80% dos anos: ${fmt(f.p10)} a ${fmt(f.p90)}</span>
          <span><i style="background:var(--pers)"></i>Último mês observado (${nomeMes(r.ultimo_mes_observado)}): ${fmt(r.casos_persistencia)}</span></div>
      </section>
      <section class="card-resultado"><span class="rotulo">Previsão do modelo</span>
        ${alerta("info", `Disponível a partir de <strong>${disp}</strong>, quando ${mesNome} estiver a 3 meses do último dado consolidado.`)}
        <p class="nota">${esc(r.nota)}</p></section></div>`;
  }
  const p = r.previsao, d = r.desempenho_horizonte?.teste_2026, h = r.horizonte_meses;
  const [lo, hi] = p.intervalo_confianca;
  const iNivel = Math.max(0, ORDEM_NIVEL.indexOf(p.nivel_risco));
  const n = NIVEIS[p.nivel_risco] || NIVEIS.baixo;
  const escala = ORDEM_NIVEL.map((_, i) => `<div style="${i === iNivel ? `background:${n.cor}` : ""}"></div>`).join("");
  const largo = hi >= 4 * Math.max(p.casos_previstos, 1);
  const metr = d ? `<div class="metricas">
      <div class="${(d.modelo?.mae ?? 0) <= (d.persistencia?.mae ?? 0) ? "bom" : "ruim"}"><b>${fmt(d.modelo?.mae, 1)}</b>
        <span>erro médio por cidade-mês<br>repetir o último mês: ${fmt(d.persistencia?.mae, 1)}</span></div>
      <div class="${(d.modelo?.auc ?? 0) > (d.auc_infodengue ?? 1) ? "bom" : "ruim"}"><b>${fmt(d.modelo?.auc, 2)}</b>
        <span>acerto na ordem de risco (AUC)<br>persistência ${fmt(d.persistencia?.auc, 2)} · InfoDengue ${fmt(d.auc_infodengue, 2)}</span></div>
      <div class="${Math.abs((d.razao_previsto_real ?? 1) - 1) <= 0.25 ? "bom" : "ruim"}"><b>${fmt(d.razao_previsto_real, 1)}×</b>
        <span>total previsto ÷ real${d.razao_previsto_real > 1.2 ? "<br>superestimou o ano de baixa" : ""}</span></div>
      <div class="${(d.cobertura_intervalo_90 ?? 0) >= 0.85 ? "bom" : "ruim"}"><b>${pct(d.cobertura_intervalo_90)}</b>
        <span>casos reais dentro<br>do intervalo de 90%</span></div></div>` : "";
  const avisos = (p.avisos || []).map((a) => `<li>${esc(a)}</li>`).join("");
  return `<div class="grade-prev">
    <section class="card-resultado"><span class="selo-modo prev">Previsão do modelo · ${h} ${h === 1 ? "mês" : "meses"} à frente</span>
      <span class="rotulo">Casos previstos</span>
      <div class="big">${fmt(p.casos_previstos)}<small>casos</small></div>
      ${faixaIntervalo({ lo, hi, centro: p.casos_previstos, pers: r.casos_persistencia })}
      <div class="legenda"><span><i style="background:var(--modelo)"></i>Previsão</span>
        <span><i style="background:var(--modelo-claro);border:1px solid var(--modelo-borda)"></i>Intervalo de 90%: ${fmt(lo)} a ${fmt(hi)}</span>
        <span><i style="background:var(--pers)"></i>Repetir ${MESES_LONGO[Number(r.ultimo_mes_observado.slice(5)) - 1]}: ${fmt(r.casos_persistencia)}</span></div>
      ${largo ? alerta("aviso", `A ${h} ${h === 1 ? "mês" : "meses"} o intervalo é largo: o número central é o mais provável, mas qualquer valor entre ${fmt(lo)} e ${fmt(hi)} é plausível.`) : ""}
    </section>
    <section class="card-resultado"><span class="rotulo">Risco relativo à própria cidade</span>
      <div class="risco">${seloNivel(p.nivel_risco)}<span class="prob">${pct(p.probabilidade_risco_alto)}</span></div>
      <div class="escala">${escala}</div>
      <div class="escala-r"><span>baixo</span><span>médio</span><span>alto</span><span>crítico</span></div>
      <p class="texto">Chance de ${esc(r.cidade)} passar de <b class="num">${fmt(p.limiar_risco_incidencia_100k, 1)} casos por 100 mil</b>,
        o nível acima do qual ela fica em só 25% dos meses (P75 da cidade).</p>
    </section></div>
    <section class="card-resultado">
      <h3>Quanto confiar neste horizonte</h3>
      <p class="sub-t">Como o modelo se saiu a ${h} ${h === 1 ? "mês" : "meses"} no teste de 2026, com meses que ele nunca tinha visto.</p>
      ${metr}
      ${p.confiabilidade === "baixa" ? alerta("aviso", `Confiabilidade <strong>baixa</strong> para esta cidade e horizonte. Veja os avisos.`) : ""}
      ${avisos ? `<details><summary>Avisos (${p.avisos.length})</summary><ul>${avisos}</ul></details>` : ""}
      <p class="nota">${esc(r.nota)}</p>
    </section>`;
}

function graficoPrevisao(r, hist) {
  $("pvGraficoCard").hidden = false;
  const x = hist.map((h) => h.mes + "-15"), y = hist.map((h) => h.casos);
  const traces = [{ x, y, name: "Observado", mode: "lines+markers", line: { color: COR.real, width: 2 }, marker: { size: 5 },
    hovertemplate: "%{x|%b %Y}: %{y:,.0f} casos<extra></extra>" }];
  const alvo = r.mes_alvo + "-15";
  if (r.modo === "previsao") {
    const p = r.previsao;
    traces.push({ x: [alvo], y: [p.casos_previstos], name: "Previsão (intervalo de 90%)", mode: "markers",
      marker: { color: COR.modelo, size: 12, line: { color: "#fffdf9", width: 2 } }, error_y: { type: "data", symmetric: false,
        array: [p.intervalo_confianca[1] - p.casos_previstos], arrayminus: [p.casos_previstos - p.intervalo_confianca[0]],
        color: COR.modelo, thickness: 2, width: 8 },
      hovertemplate: `%{x|%b %Y}: %{y:,.0f} casos previstos (${fmt(p.intervalo_confianca[0])} a ${fmt(p.intervalo_confianca[1])})<extra></extra>` });
    traces.push({ x: [r.ultimo_mes_observado + "-15", alvo], y: [r.casos_persistencia, r.casos_persistencia], name: "Persistência (repetir o último mês)",
      mode: "lines", line: { color: COR.persist, dash: "dot", width: 2 }, hovertemplate: "Persistência: %{y:,.0f} casos<extra></extra>" });
  } else if (r.modo === "cenario") {
    const f = r.faixa_historica;
    traces.push({ x: [alvo], y: [f.p50], name: "Faixa histórica (P10–P90)", mode: "markers",
      marker: { color: COR.texto, size: 11, symbol: "diamond" }, error_y: { type: "data", symmetric: false,
        array: [f.p90 - f.p50], arrayminus: [f.p50 - f.p10], color: COR.texto, thickness: 2, width: 8 },
      hovertemplate: `Mediana histórica: %{y:,.0f} (${fmt(f.p10)} a ${fmt(f.p90)})<extra></extra>` });
  }
  Plotly.react("pvGrafico", traces, { ...layoutBase, title: titulo("Últimos 24 meses e o mês consultado"),
    yaxis: { ...layoutBase.yaxis, title: "Casos", rangemode: "tozero" },
    xaxis: { ...layoutBase.xaxis, type: "date", tickformat: "%b %Y" } }, cfgPlot);
}

// ------------------------------------------------------------------ 2. ranking
async function carregarRanking() {
  const doenca = $("rkDoenca").value, h = $("rkH").value, uf = $("rkUf").value, pop = $("rkPop").value;
  const meu = ++seq.rk;
  loader("ranking", true);
  try {
    const r = await api(`/api/ranking?doenca=${doenca}&h=${h}&pop_min=${pop}&limite=20${uf ? `&uf=${uf}` : ""}`);
    if (meu !== seq.rk) return;
    $("rkResumo").innerHTML = alerta("info", `Previsão para <strong>${nomeMes(r.mes_alvo)}</strong>
      (${r.horizonte_meses} ${r.horizonte_meses === 1 ? "mês" : "meses"} à frente). Total previsto na Região Sul:
      <strong>${fmt(r.total_previsto)}</strong> casos de ${nomeDoenca(doenca)}. O risco é <em>relativo ao histórico de cada cidade</em>:
      "alto" significa acima do que é comum ali, não necessariamente muitos casos. O filtro de população tira as cidades
      muito pequenas, onde 1 ou 2 casos já superam o padrão.`);
    const tb = $("rkTabela").querySelector("tbody");
    tb.innerHTML = r.itens.map((it, i) => `<tr><td class="muted">${i + 1}</td><td><strong>${esc(it.cidade)}</strong></td><td>${it.uf}</td>
        <td>${seloNivel(it.nivel_risco, true)}</td><td>${pct(it.probabilidade_risco_alto)}</td>
        <td>${fmt(it.casos_previstos)} <small class="muted">(${fmt(it.intervalo_confianca[0])}–${fmt(it.intervalo_confianca[1])})</small></td>
        <td>${fmt(it.casos_persistencia)}</td><td>${fmt(it.incidencia_prevista_100k, 1)}</td></tr>`).join("")
      || `<tr><td colspan="8" class="muted">Nenhuma cidade com esses filtros.</td></tr>`;
    $("rkTabela").dataset.ok = "1";
    const itens = [...r.itens].reverse();
    Plotly.react("rkGrafico", [{
      type: "bar", orientation: "h", x: itens.map((i) => i.probabilidade_risco_alto * 100),
      y: itens.map((i) => `${i.cidade} (${i.uf})`), marker: { color: itens.map((i) => (NIVEIS[i.nivel_risco] || NIVEIS.baixo).cor) },
      text: itens.map((i) => (NIVEIS[i.nivel_risco] || NIVEIS.baixo).txt), textposition: "inside", insidetextanchor: "end",
      textfont: { color: "#fff", size: 11 },
      hovertemplate: "%{y}<br>%{x:.0f}% de chance de risco alto · %{text}<extra></extra>",
    }], { ...layoutBase, title: titulo("20 maiores probabilidades de risco alto"), bargap: 0.25,
      xaxis: { ...layoutBase.xaxis, title: "Probabilidade (%)", range: [0, 100] },
      yaxis: { ...layoutBase.yaxis, automargin: true }, margin: { ...layoutBase.margin, l: 10 }, showlegend: false }, cfgPlot);
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
        hovertemplate: "%{x|%b %Y}: %{y:,.0f} casos (faixa %{customdata[0]:,.0f}–%{customdata[1]:,.0f}; fator clima %{customdata[2]:.2f})<extra></extra>" },
      { x: hist.map((h) => h.mes + "-15"), y: hist.map((h) => h.casos), mode: "lines", name: "Observado", line: { color: COR.real, width: 1.5 },
        hovertemplate: "%{x|%b %Y}: %{y:,.0f} casos observados<extra></extra>" },
    ];
    if (base) traces.splice(2, 0, { x, y: base.pontos.map((p) => p.p50), mode: "lines", name: "Mediana com clima atual",
      line: { color: COR.persist, dash: "dot", width: 2 }, hovertemplate: "%{x|%b %Y}: %{y:,.0f} (clima atual)<extra></extra>" });
    Plotly.react("ceGrafico", traces, { ...layoutBase, title: titulo(`${c.cidade} · ${nomeDoenca(doenca)}: o que costuma acontecer em cada mês`),
      yaxis: { ...layoutBase.yaxis, title: "Casos por mês", rangemode: "tozero" },
      xaxis: { ...layoutBase.xaxis, type: "date", tickformat: "%b %Y" } }, cfgPlot);
    $("ceGrafico").dataset.ok = "1";
    const verao = c.pontos.filter((p) => [12, 1, 2, 3].includes(Number(p.mes.slice(5))));
    const media = (k) => (verao.length ? verao.reduce((s, p) => s + p[k], 0) / verao.length : 1);
    const resumo = delta === "0" ? "" : alerta("info", `Com +${delta} °C, os meses de verão (dez–mar) teriam em média
      <strong>${fmt((media("fator_clima") - 1) * 100, 0)}% mais casos</strong> que o habitual
      (faixa de incerteza do efeito: ${fmt((media("fator_clima_lo") - 1) * 100, 0)}% a ${fmt((media("fator_clima_hi") - 1) * 100, 0)}%).`);
    $("ceAvisos").innerHTML = resumo + (c.avisos || []).map((a) => `<p class="muted">• ${esc(a)}</p>`).join("") + `<p class="nota">${esc(c.nota)}</p>`;
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
      <div class="stat-card ${venceInfo ? "ok" : "ruim"}"><span class="stat-label">Contra o último alerta do InfoDengue</span>
        <span class="stat-value">${venceInfo ? "Melhor" : "Não supera"}</span><span class="muted">na ordem de risco das cidades, ${venceInfo ? "em todos os horizontes" : "em parte dos horizontes"}</span></div>
      <div class="stat-card ${vencePers === hs.length ? "ok" : vencePers ? "medio" : "ruim"}"><span class="stat-label">Contra repetir o último mês</span>
        <span class="stat-value">${vencePers} de ${hs.length} horizontes</span><span class="muted">em que o modelo ordena o risco melhor (AUC)</span></div>
      <div class="stat-card ruim"><span class="stat-label">Total de casos em 2026 (1 mês à frente)</span>
        <span class="stat-value">${fmt(h1.razao_previsto_real, 1)}× o real</span><span class="muted">ano de baixa após epidemia: o modelo esperou mais casos</span></div>`;
    const rot = hs.map((h) => `${h.slice(1)} ${h === "h1" ? "mês" : "meses"} à frente`);
    const barra = (nome, ys, cor) => ({ type: "bar", name: nome, x: rot, y: ys, marker: { color: cor },
      text: ys.map((v) => fmt(v, 2)), textposition: "outside", textfont: { size: 11, color: "#1c1b18" },
      hovertemplate: `${nome}: %{y:.2f}<extra></extra>` });
    Plotly.react("cfGrafico", [
      barra("Modelo", hs.map((h) => t(h).modelo?.auc), COR.modelo),
      barra("Persistência (repetir o último mês)", hs.map((h) => t(h).persistencia?.auc), COR.persist),
      barra("Último alerta InfoDengue", hs.map((h) => t(h).auc_infodengue), COR.info),
    ], { ...layoutBase, barmode: "group", bargap: 0.3, bargroupgap: 0.08,
      title: titulo("Acerto na ordem de risco (AUC) no teste de 2026 · 0,5 = acaso, 1 = perfeito"),
      yaxis: { ...layoutBase.yaxis, range: [0.4, 1], title: "AUC" },
      shapes: [{ type: "line", xref: "paper", x0: 0, x1: 1, y0: 0.5, y1: 0.5, line: { dash: "dot", color: "#8a867c" } }] }, cfgPlot);
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
      ? `<div class="table-responsive"><table class="data-table"><thead><tr><th>Horizonte</th><th>Meses avaliados</th><th>Previsto ÷ real</th><th>Erro médio (modelo · persistência)</th><th>Dentro do IC 90%</th></tr></thead><tbody>` +
        c.ao_vivo.map((v) => `<tr><td>${v.horizonte}</td><td>${v.meses.join(", ")}</td><td>${fmt(v.razao_previsto_real, 2)}×</td><td>${fmt(v.mae, 1)} · ${fmt(v.mae_persistencia, 1)}</td><td>${pct(v.cobertura_intervalo_90)}</td></tr>`).join("") + "</tbody></table></div>"
      : `<p class="muted">Ainda não há previsões emitidas cujo mês já tenha sido observado. A cada mês, as previsões são registradas
         antes de o mês acontecer e comparadas com o real quando os dados consolidam.</p>`;
    $("cfAoVivo").innerHTML = `<div class="chart-card"><h3>Desempenho ao vivo (previsões registradas antes do mês acontecer)</h3>${vivo}
      <p class="nota">Modelo ${esc(c.versao)} treinado com ${esc(c.periodo_treino)}; calibração: ${esc(c.calibracao)}.</p></div>`;
  } catch (e) { erro($("cfResumo"), e); }
  finally { loader("confiabilidade", false); }
}

document.addEventListener("DOMContentLoaded", iniciar);
