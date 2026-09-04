#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Relatório Técnico ABNT — Cenário Sem Incremento Climático (Baseline)

Gera um documento Word (.docx) estruturado conforme ABNT NBR 14724,
documentando o cenário contrafactual de climatologia histórica constante
e sua comparação com os cenários SSP.

Saída: output/projecoes_sem_incremento/relatorio_tecnico_abnt_sem_incremento.docx
"""

from __future__ import annotations

import io
import logging
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ═══════════════════════════ CONFIGURAÇÃO ═══════════════════════════
ROOT = Path(__file__).parent.parent.parent
OUT_SEM = ROOT / "output" / "projecoes_sem_incremento"
OUT_SSP = ROOT / "output" / "projecoes_regionais"
OUT_DOCX = OUT_SEM / "relatorio_tecnico_abnt_sem_incremento.docx"

EPS = 1e-9
DATA_HOJE = datetime.now().strftime("%d/%m/%Y")
ANO_REF = 2026

SCENARIOS_SSP = {
    "ssp126": ("SSP1-2.6", "#3f8f8f"),
    "ssp245": ("SSP2-4.5", "#3b5f8a"),
    "ssp370": ("SSP3-7.0", "#cc7f2a"),
    "ssp585": ("SSP5-8.5", "#b24a3a"),
}
COLOR_SEM = "#5a5a9a"

FONT_NAME = "Arial"
FONT_SIZE = Pt(12)
FONT_SIZE_SM = Pt(10)
FONT_SIZE_TITLE = Pt(14)
COLOR_HDR_FILL = "3a3a7a"   # roxo-azul para diferenciar do relatório SSP
COLOR_ROW_ALT  = "EEEEF8"


# ═══════════════════════════ HELPERS CORE ═══════════════════════════

def _fmt(n: float) -> str:
    return f"{int(round(n)):,}".replace(",", ".")


def _pct(a: float, b: float) -> str:
    if b < EPS:
        return "—"
    return f"{((a - b) / b * 100):+.1f}%"


def _setup_document(doc: Document) -> None:
    """Margens ABNT NBR 14724: esq 3cm, dir 2cm, sup 3cm, inf 2cm."""
    sec = doc.sections[0]
    sec.page_height = Cm(29.7)
    sec.page_width = Cm(21.0)
    sec.left_margin = Cm(3.0)
    sec.right_margin = Cm(2.0)
    sec.top_margin = Cm(3.0)
    sec.bottom_margin = Cm(2.0)


def _add_footer_page_number(doc: Document) -> None:
    """Número de página alinhado à direita no rodapé (ABNT)."""
    sec = doc.sections[0]
    footer = sec.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run()
    run.font.name = FONT_NAME
    run.font.size = FONT_SIZE_SM
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


def _para(doc: Document, text: str = "", *,
          align: WD_ALIGN_PARAGRAPH = WD_ALIGN_PARAGRAPH.JUSTIFY,
          bold: bool = False,
          italic: bool = False,
          size: Pt | None = None,
          space_before: Pt = Pt(0),
          space_after: Pt = Pt(6),
          first_indent: Cm | None = Cm(1.25),
          keep_run: bool = False) -> tuple:
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.alignment = align
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_before = space_before
    pf.space_after = space_after
    pf.first_line_indent = first_indent
    run = p.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = size or FONT_SIZE
    run.font.bold = bold
    run.font.italic = italic
    return p, run


def _body(doc: Document, text: str) -> None:
    _para(doc, text)


def _body_ni(doc: Document, text: str, bold: bool = False) -> None:
    _para(doc, text, first_indent=None, bold=bold)


def _h1(doc: Document, num: str, title: str) -> None:
    _para(doc, f"{num}  {title.upper()}" if num else title.upper(),
          align=WD_ALIGN_PARAGRAPH.LEFT, bold=True,
          space_before=Pt(18), space_after=Pt(6), first_indent=None, keep_run=True)


def _h2(doc: Document, num: str, title: str) -> None:
    _para(doc, f"{num}  {title}",
          align=WD_ALIGN_PARAGRAPH.LEFT, bold=True,
          space_before=Pt(12), space_after=Pt(6), first_indent=None, keep_run=True)


def _add_chart(doc: Document, fig: plt.Figure, caption: str,
               width_cm: float = 14.5) -> None:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.first_line_indent = None
    run = p.add_run()
    run.add_picture(buf, width=Cm(width_cm))
    cp = doc.add_paragraph(caption)
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_before = Pt(2)
    cp.paragraph_format.space_after = Pt(12)
    cp.paragraph_format.first_line_indent = None
    for r in cp.runs:
        r.font.name = FONT_NAME
        r.font.size = FONT_SIZE_SM
        r.font.italic = True


def _set_cell_bg(cell, hex_color: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tc_pr.append(shd)


def _table(doc: Document,
           header: list[str],
           rows: list[list],
           col_widths: list[float] | None = None,
           caption: str = "") -> None:
    n_cols = len(header)
    tbl = doc.add_table(rows=1 + len(rows), cols=n_cols)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER

    if col_widths:
        for row in tbl.rows:
            for i, cell in enumerate(row.cells):
                if i < len(col_widths):
                    cell.width = Cm(col_widths[i])

    # Cabeçalho
    for cell, txt in zip(tbl.rows[0].cells, header):
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(txt)
        r.font.name = FONT_NAME
        r.font.size = FONT_SIZE_SM
        r.font.bold = True
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        _set_cell_bg(cell, COLOR_HDR_FILL)

    # Dados
    for ri, row_data in enumerate(rows):
        fill = COLOR_ROW_ALT if ri % 2 == 0 else "FFFFFF"
        for cell, val in zip(tbl.rows[ri + 1].cells, row_data):
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(str(val))
            r.font.name = FONT_NAME
            r.font.size = FONT_SIZE_SM
            _set_cell_bg(cell, fill)

    if caption:
        cp = doc.add_paragraph(caption)
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.space_before = Pt(2)
        cp.paragraph_format.space_after = Pt(12)
        cp.paragraph_format.first_line_indent = None
        for r in cp.runs:
            r.font.name = FONT_NAME
            r.font.size = FONT_SIZE_SM
            r.font.italic = True


# ═══════════════════════════ CARREGAMENTO DE DADOS ═══════════════════════════

def _load_hist() -> pd.DataFrame:
    csv_dir = ROOT / "output" / "csvs_latitude"
    files = sorted(csv_dir.glob("dengue_faixa_latitude_*.csv"))
    if not files:
        return pd.DataFrame(columns=["year", "casos"])
    frames = [pd.read_csv(f, usecols=["ANO", "CASOS_DENGUE"]) for f in files]
    agg = pd.concat(frames, ignore_index=True).groupby("ANO", as_index=False)["CASOS_DENGUE"].sum()
    agg = agg.rename(columns={"ANO": "year", "CASOS_DENGUE": "casos"})
    return agg[agg["year"].between(2015, 2024)].sort_values("year").reset_index(drop=True)


def _load_sem() -> pd.DataFrame:
    p = OUT_SEM / "projecao_regiao_sul_sem_incremento_2025_2040.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    return df.groupby("year", as_index=False)["pred_cases"].sum()


def _load_ssp() -> pd.DataFrame:
    p = OUT_SSP / "projecao_regiao_sul_consolidado.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    return df.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()


def _load_ml_sem() -> pd.DataFrame:
    p = OUT_SEM / "previsao_ml_2025_sem_incremento_regional.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _load_lat_sem() -> pd.DataFrame:
    files = sorted(OUT_SEM.glob("projecao_latitude_sem_incremento_-*.csv"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


def _load_comparacao() -> str:
    p = OUT_SEM / "comparacao_sem_incremento_vs_ssp.txt"
    return p.read_text(encoding="utf-8") if p.exists() else ""


# ═══════════════════════════ SEÇÕES DO DOCUMENTO ═══════════════════════════

def _sec_capa(doc: Document) -> None:
    for _ in range(3):
        doc.add_paragraph()

    p, r = _para(doc, "PROJETO CLIMA × DENGUE — REGIÃO SUL DO BRASIL",
                 align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, first_indent=None,
                 space_after=Pt(4), keep_run=True)
    r.font.size = FONT_SIZE_SM

    for _ in range(2):
        doc.add_paragraph()

    p, r = _para(
        doc,
        "PROJEÇÕES DE RISCO DE DENGUE — REGIÃO SUL\n"
        "CENÁRIO BASELINE: SEM INCREMENTO CLIMÁTICO\n"
        "(2025 – 2040)",
        align=WD_ALIGN_PARAGRAPH.CENTER, bold=True,
        size=FONT_SIZE_TITLE, first_indent=None,
        space_before=Pt(0), space_after=Pt(18), keep_run=True,
    )

    p, r = _para(
        doc,
        "Análise Contrafactual sob Climatologia Histórica Constante\n"
        "(\u0394 Temperatura = 0 · \u0394 Precipitação = 0 · \u0394 ONI = 0)",
        align=WD_ALIGN_PARAGRAPH.CENTER, italic=True,
        first_indent=None, space_after=Pt(18), keep_run=True,
    )

    # Caixa de nota (tabela simples de 1 célula)
    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = "Table Grid"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.rows[0].cells[0]
    _set_cell_bg(cell, "EEEEF8")
    p_note = cell.paragraphs[0]
    p_note.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_note.paragraph_format.space_before = Pt(6)
    p_note.paragraph_format.space_after = Pt(6)
    r_note = p_note.add_run(
        "Este relatório complementa o Relatório SSP, apresentando o cenário neutro "
        "como referência para quantificar o impacto adicional das mudanças climáticas projetadas."
    )
    r_note.font.name = FONT_NAME
    r_note.font.size = FONT_SIZE_SM
    r_note.font.italic = True

    for _ in range(5):
        doc.add_paragraph()

    p, r = _para(
        doc,
        f"Relatório Técnico Complementar — {DATA_HOJE}\n"
        "Projeto Clima × Dengue\n"
        "Dados: SINAN · INMET · NOAA · IBGE",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        first_indent=None, keep_run=True,
    )

    doc.add_page_break()


def _sec_resumo(doc: Document) -> None:
    _h1(doc, "", "Resumo")
    _body(doc,
        "Este relatório técnico documenta o cenário contrafactual (baseline) de "
        "projeção de dengue para a Região Sul do Brasil (2025–2040), no qual os "
        "incrementos anuais de temperatura, precipitação e índice ENSO são definidos "
        "como zero — reproduzindo ciclicamente a climatologia histórica 2015–2024. "
        "O objetivo é isolar o componente estrutural do risco epidemiológico e "
        "quantificar, por subtração, o impacto adicional atribuível às mudanças "
        "climáticas projetadas pelos cenários SSP do IPCC AR6. Os resultados "
        "demonstram que, mesmo sem aceleração climática, a Região Sul manteria "
        "patamares expressivos de incidência de dengue ao longo de toda a projeção, "
        "evidenciando que parte relevante do risco é de natureza estrutural e não "
        "seria eliminada por estabilização climática imediata.")
    p, r = _para(doc,
        "Palavras-chave: dengue; cenário baseline; análise contrafactual; Região Sul; "
        "epidemiologia; modelo log-linear.",
        italic=True, first_indent=None, space_after=Pt(0))
    doc.add_page_break()


def _sec_sumario(doc: Document) -> None:
    _h1(doc, "", "Sumário")
    itens = [
        ("1", "Objetivo e Contexto do Cenário Baseline", "4"),
        ("2", "Premissas do Modelo Sem Incremento", "4"),
        ("3", "Metodologia Específica", "5"),
        ("4", "Base Histórica 2015–2024", "5"),
        ("5", "Projeção Baseline 2025–2040", "6"),
        ("5.1", "Consolidado Regional", "6"),
        ("5.2", "Por Faixa de Latitude", "7"),
        ("5.3", "Previsão Pontual 2025 (Modelo ML)", "7"),
        ("6", "Comparativo: Baseline vs Cenários SSP", "8"),
        ("7", "Implicações e Interpretação", "8"),
        ("8", "Referências", "9"),
    ]
    for num, title, pg in itens:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.first_line_indent = None
        pPr = p._p.get_or_add_pPr()
        tabs_el = OxmlElement("w:tabs")
        t_left = OxmlElement("w:tab")
        t_left.set(qn("w:val"), "left")
        t_left.set(qn("w:pos"), "576")
        t_right = OxmlElement("w:tab")
        t_right.set(qn("w:val"), "right")
        t_right.set(qn("w:leader"), "dot")
        t_right.set(qn("w:pos"), "9360")
        tabs_el.append(t_left)
        tabs_el.append(t_right)
        pPr.append(tabs_el)
        r1 = p.add_run(f"{num}\t{title}\t{pg}")
        r1.font.name = FONT_NAME
        r1.font.size = FONT_SIZE
    doc.add_page_break()


def _sec_objetivo(doc: Document) -> None:
    _h1(doc, "1", "Objetivo e Contexto do Cenário Baseline")
    _body(doc,
        "O cenário 'sem incremento' (baseline) representa uma hipótese contrafactual: "
        "e se as condições climáticas permanecessem idênticas à climatologia observada "
        "entre 2015 e 2024? Neste cenário, os incrementos anuais de temperatura, "
        "precipitação e índice ENSO são definidos como zero para todo o horizonte "
        "projetado (2025–2040), com o ciclo climático histórico reproduzido integralmente.")
    _body(doc,
        "Este cenário cumpre três funções analíticas centrais:")
    for txt in [
        "1.  REFERÊNCIA ESTRUTURAL: Isola o efeito da tendência climática sobre a "
        "incidência de dengue, separando o sinal climático da estrutura epidemiológica "
        "intrínseca (densidade vetorial, susceptibilidade populacional, urbanização).",

        "2.  QUANTIFICAÇÃO DO IMPACTO ADICIONAL: A diferença entre o cenário baseline "
        "e os cenários SSP representa o incremento marginal de risco atribuível "
        "exclusivamente às mudanças climáticas projetadas.",

        "3.  LIMITE INFERIOR DE PRECAUÇÃO: Mesmo sem aceleração climática, as projeções "
        "revelam o nível de risco que persistiria apenas pela continuidade das condições "
        "atuais — definindo o patamar mínimo de preparação necessária.",
    ]:
        _body(doc, txt)


def _sec_premissas(doc: Document) -> None:
    _h1(doc, "2", "Premissas do Modelo Sem Incremento")
    _body(doc,
        "O motor sem incremento utiliza o mesmo conjunto de equações, parâmetros e "
        "municípios do motor principal, com a única diferença de definir deltas "
        "climáticos anuais iguais a zero:")
    hdr = ["Parâmetro", "Valor", "Observação"]
    rows = [
        ["\u0394 Temperatura/ano", "0,00 °C", "Climatologia histórica mantida inalterada"],
        ["\u0394 Precipitação/ano", "0,00 %", "Precipitação estável em 2025–2040"],
        ["\u0394 ONI (ENSO)/ano", "0,00", "Índice oceânico sem tendência acumulada"],
        ["Template climático", "Ciclo 2015–2024", "Variação interanual histórica preservada"],
        ["Correção 2024→2025", "Floor 75%", "Mesma regra de continuidade do motor SSP"],
        ["Municípios cobertos", "1.190", "Idêntico ao motor de cenários SSP"],
    ]
    _table(doc, hdr, rows,
           col_widths=[4.5, 3.5, 7.0],
           caption="Tabela 1 — Premissas operacionais do cenário sem incremento climático.")


def _sec_metodologia(doc: Document) -> None:
    _h1(doc, "3", "Metodologia Específica")
    _body(doc,
        "O fluxo de processamento do cenário baseline segue as etapas abaixo, "
        "idênticas ao motor SSP exceto pela definição dos deltas climáticos:")
    steps = [
        "1.  Carrega painel histórico de output/csvs_latitude/ (fonte canônica — "
        "1.190 municípios com coordenadas validadas pelo IBGE).",
        "2.  Treina intercepto local \u03b1 por município (mediana dos resíduos "
        "históricos 2015–2024).",
        "3.  Projeta cada município com \u0394_temp = 0, \u0394_prec = 0, \u0394_enso = 0 "
        "para 2025–2040.",
        "4.  Aplica cap de plausibilidade (percentil 95 histórico por município).",
        "5.  Aplica correção de continuidade 2024→2025 (floor de 75% do nível de 2024).",
        "6.  Salva CSVs por faixa de latitude e consolidado regional.",
        "7.  Gera comparativo textual vs cenários SSP.",
    ]
    for s in steps:
        _body(doc, s)
    _body(doc,
        "A equação de projeção mensal é idêntica ao motor SSP, sem ajuste acumulado "
        "ao longo dos anos projetados:")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.first_line_indent = None
    r = p.add_run(
        "log(Y\u209c + 1) = \u03b1_local + \u03b2_T\u00b7T_hist(t\u22123) "
        "+ \u03b2_P\u00b7P_hist(t\u22123) + \u03b2_ENSO\u00b7ONI_hist(t\u22123) "
        "+ \u03b2_lat\u00b7Lat + \u03b5"
    )
    r.font.name = "Courier New"
    r.font.size = Pt(10)
    _body(doc,
        "onde T_hist, P_hist e ONI_hist são os valores da climatologia histórica "
        "(2015–2024) sem qualquer ajuste acumulado ao longo do horizonte projetado.")


def _sec_historico(doc: Document, hist: pd.DataFrame) -> None:
    _h1(doc, "4", "Base Histórica 2015–2024")
    media_v = int(hist["casos"].mean()) if not hist.empty else 0
    pico_yr = int(hist.loc[hist["casos"].idxmax(), "year"]) if not hist.empty else 0
    pico_v = int(hist["casos"].max()) if not hist.empty else 0
    _body(doc,
        f"A climatologia base do cenário sem incremento compreende o período 2015–2024, "
        f"com média anual de {_fmt(media_v)} casos e pico em {pico_yr} "
        f"({_fmt(pico_v)} casos). Esta série define o envelope climático reproduzido "
        "ciclicamente ao longo de todo o horizonte 2025–2040 no cenário baseline.")

    if not hist.empty:
        fig, ax = plt.subplots(figsize=(11, 4.5))
        bars = ax.bar(hist["year"], hist["casos"], color=COLOR_SEM,
                      alpha=0.72, width=0.72, edgecolor="white", linewidth=0.5)
        ax.plot(hist["year"], hist["casos"], color="#2a2a6a", linewidth=2.0,
                marker="o", markersize=6, zorder=3)
        for bar, val in zip(bars, hist["casos"]):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + hist["casos"].max() * 0.012,
                    _fmt(val), ha="center", va="bottom", fontsize=8)
        ax.set_title("Casos de Dengue Observados — Base do Cenário Baseline (2015–2024)",
                     fontsize=12, fontweight="bold", pad=8)
        ax.set_xlabel("Ano", fontsize=10)
        ax.set_ylabel("Total de Casos", fontsize=10)
        ax.set_xticks(hist["year"])
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        _add_chart(doc, fig,
                   "Figura 1 — Série histórica 2015–2024 que define a climatologia base "
                   "do cenário sem incremento. Fonte: SINAN/MS.")


def _sec_projecao(doc: Document, sem: pd.DataFrame, hist: pd.DataFrame) -> None:
    _h1(doc, "5", "Projeção Baseline 2025–2040")

    _h2(doc, "5.1", "Consolidado Regional")
    _body(doc,
        "A projeção baseline indica manutenção do nível de risco histórico, sem "
        "tendência de crescimento estrutural no horizonte 2025–2040. A variabilidade "
        "interanual reflete exclusivamente o ciclo climático histórico reproduzido:")

    if not sem.empty:
        anos_key = [2025, 2027, 2030, 2033, 2036, 2040]
        hdr_t = ["Ano", "Casos Projetados (Baseline)", "Variação vs Ano Anterior"]
        rows_t = []
        prev_v = None
        for a in anos_key:
            v_row = sem.loc[sem["year"] == a, "pred_cases"]
            v = float(v_row.iloc[0]) if not v_row.empty else 0.0
            var_str = _pct(v, prev_v) if prev_v is not None else "—"
            rows_t.append([str(a), _fmt(v), var_str])
            prev_v = v
        _table(doc, hdr_t, rows_t,
               col_widths=[2.5, 5.5, 5.0],
               caption="Tabela 2 — Projeção baseline regional (anos selecionados 2025–2040).")

    if not sem.empty:
        fig, ax = plt.subplots(figsize=(11, 5))
        if not hist.empty:
            ax.plot(hist["year"], hist["casos"], color="black", linewidth=2.2,
                    marker="o", markersize=4, label="Observado (2015–2024)", zorder=6)
        ax.plot(sem["year"], sem["pred_cases"], color=COLOR_SEM, linewidth=2.5,
                marker="s", markersize=4, label="Baseline (sem incremento)", zorder=5)
        if not hist.empty and 2024 in hist["year"].values and 2025 in sem["year"].values:
            h2024 = float(hist.loc[hist["year"] == 2024, "casos"].sum())
            v2025 = float(sem.loc[sem["year"] == 2025, "pred_cases"].iloc[0])
            ax.plot([2024, 2025], [h2024, v2025], color=COLOR_SEM,
                    linewidth=1.8, linestyle="--", alpha=0.7, zorder=3)
        ax.axvline(x=2024.5, color="#aaa", linewidth=0.8, linestyle=":")
        ax.set_title("Projeção Baseline — Região Sul (2025–2040)",
                     fontsize=12, fontweight="bold", pad=8)
        ax.set_xlabel("Ano", fontsize=10)
        ax.set_ylabel("Total de Casos", fontsize=10)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
        ax.legend(loc="upper left", fontsize=9, frameon=True)
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        _add_chart(doc, fig,
                   "Figura 2 — Projeção baseline 2025–2040 sobre série histórica. "
                   "Linha tracejada: transição 2024→2025.")


def _sec_por_lat(doc: Document, lat_sem: pd.DataFrame) -> None:
    _h2(doc, "5.2", "Por Faixa de Latitude")
    _body(doc,
        "A tabela abaixo apresenta as projeções baseline por faixa de latitude. "
        "A variação 2025→2040 indica a dinâmica epidemiológica esperada mesmo sem "
        "alteração climática, reflexo da estrutura demográfica e do padrão de "
        "variação interanual histórica de cada faixa:")

    if not lat_sem.empty:
        hdr_l = ["Faixa de Latitude", "2025", "2030", "2035", "2040", "Var. 25→40"]
        rows_l = []
        for (lmin, lmax), grp in lat_sem.groupby(["latitude_min", "latitude_max"]):
            grp = grp.sort_values("year")
            def gv(yr):
                v = grp.loc[grp["year"] == yr, "pred_cases"]
                return float(v.iloc[0]) if not v.empty else 0.0
            v25, v30, v35, v40 = gv(2025), gv(2030), gv(2035), gv(2040)
            rows_l.append([
                f"{abs(lmin):.1f}°S — {abs(lmax):.1f}°S",
                _fmt(v25), _fmt(v30), _fmt(v35), _fmt(v40),
                _pct(v40, v25),
            ])
        _table(doc, hdr_l, rows_l,
               col_widths=[3.8, 2.2, 2.2, 2.2, 2.2, 2.4],
               caption="Tabela 3 — Projeção baseline por faixa de latitude (anos selecionados).")
    else:
        _body_ni(doc,
            "Dados de projeção por latitude não disponíveis. "
            "Execute o motor sem incremento para gerar os arquivos necessários.")


def _sec_ml(doc: Document, ml_sem: pd.DataFrame) -> None:
    _h2(doc, "5.3", "Previsão Pontual 2025 — Modelo de Machine Learning")
    _body(doc,
        "A previsão para 2025 com o HistGradientBoosting, sem qualquer incremento "
        "climático SSP, representa a expectativa de casos no nível basal condicionado "
        "pela climatologia histórica:")

    if not ml_sem.empty:
        hdr_m = ["Cenário", "Casos Projetados 2025 (ML Regional)"]
        rows_m = [[str(r.get("scenario", "sem_incremento")),
                   _fmt(float(r.get("pred_cases", 0)))]
                  for _, r in ml_sem.iterrows()]
        _table(doc, hdr_m, rows_m,
               col_widths=[5.0, 6.0],
               caption="Tabela 4 — Previsão regional 2025 pelo modelo ML (cenário baseline).")
    else:
        _body_ni(doc, "Dados ML sem incremento não disponíveis.")


def _sec_comparativo(doc: Document, sem: pd.DataFrame, ssp: pd.DataFrame,
                     hist: pd.DataFrame, cmp_txt: str) -> None:
    _h1(doc, "6", "Comparativo: Baseline vs Cenários SSP")
    _body(doc,
        "A diferença entre o cenário baseline e os cenários SSP quantifica o risco "
        "ADICIONAL atribuível às mudanças climáticas projetadas. Esta diferença cresce "
        "ao longo do horizonte, reforçando que investimentos em redução de emissões "
        "têm retorno epidemiológico mensurável:")

    if not sem.empty and not ssp.empty:
        anos_cmp = [2025, 2030, 2035, 2040]
        hdr_c = ["Ano", "Baseline", "SSP1-2.6", "SSP2-4.5", "SSP3-7.0", "SSP5-8.5",
                 "Dif. SSP5 vs Base"]
        rows_c = []
        for a in anos_cmp:
            v_sem = sem.loc[sem["year"] == a, "pred_cases"]
            val_sem = float(v_sem.iloc[0]) if not v_sem.empty else 0.0
            row = [str(a), _fmt(val_sem)]
            v585 = 0.0
            for sc in ["ssp126", "ssp245", "ssp370", "ssp585"]:
                ds = ssp[(ssp["scenario"] == sc) & (ssp["year"] == a)]
                val = float(ds["pred_cases"].iloc[0]) if not ds.empty else 0.0
                row.append(_fmt(val))
                if sc == "ssp585":
                    v585 = val
            row.append(_pct(v585, val_sem))
            rows_c.append(row)
        _table(doc, hdr_c, rows_c,
               col_widths=[1.5, 2.2, 2.2, 2.2, 2.2, 2.2, 2.5],
               caption="Tabela 5 — Comparativo anual: Baseline vs cenários SSP (casos projetados).")

    if not sem.empty:
        fig, ax = plt.subplots(figsize=(11, 5.5))
        if not hist.empty:
            ax.plot(hist["year"], hist["casos"], color="black", linewidth=2.2,
                    marker="o", markersize=4, label="Observado (2015–2024)", zorder=7)
        ax.plot(sem["year"], sem["pred_cases"], color=COLOR_SEM, linewidth=2.8,
                marker="s", markersize=4, label="Baseline (sem incremento)", zorder=6)
        if not ssp.empty:
            for sc, (label, color) in SCENARIOS_SSP.items():
                ds = ssp[ssp["scenario"] == sc].sort_values("year")
                if not ds.empty:
                    ax.plot(ds["year"], ds["pred_cases"], color=color, linewidth=1.5,
                            linestyle="--", alpha=0.8, label=f"SSP: {label}", zorder=3)
        ax.axvline(x=2024.5, color="#aaa", linewidth=0.8, linestyle=":")
        ax.set_title("Baseline vs Cenários SSP — Projeção Regional Consolidada (2025–2040)",
                     fontsize=12, fontweight="bold", pad=8)
        ax.set_xlabel("Ano", fontsize=10)
        ax.set_ylabel("Total de Casos", fontsize=10)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
        ax.legend(loc="upper left", fontsize=8.5, frameon=True, ncol=2)
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        _add_chart(doc, fig,
                   "Figura 3 — Comparativo baseline vs cenários SSP. "
                   "A faixa entre a linha roxa e cada linha SSP representa o risco adicional climático.")


def _sec_implicacoes(doc: Document) -> None:
    _h1(doc, "7", "Implicações e Interpretação")
    _body(doc,
        "O cenário baseline, mesmo sem qualquer incremento climático adicional, "
        "projeta patamares expressivos de dengue ao longo de 2025–2040. Isso evidencia "
        "que parte relevante do risco epidemiológico é de natureza estrutural — "
        "associada à temperatura já observada, às condições urbanas e ao padrão ENSO "
        "— e não seria eliminada mesmo em um cenário hipotético de estabilização "
        "climática imediata.")
    _body(doc,
        "A diferença quantificada entre o baseline e o SSP5-8.5 representa o risco "
        "ADICIONAL evitável por políticas de mitigação climática. Esta diferença "
        "cresce ao longo do horizonte, reforçando que o valor de saúde pública das "
        "políticas de descarbonização aumenta com o tempo.")
    _body(doc,
        "Do ponto de vista operacional, o cenário baseline define o nível mínimo de "
        "alerta permanente: não há janela de 'baixo risco' estrutural suficiente para "
        "reduzir equipes de vigilância ou interromper campanhas de controle vetorial. "
        "O planejamento de capacidade do sistema de saúde deve ser dimensionado pelo "
        "menos para o nível baseline, com reserva estratégica proporcional ao cenário "
        "SSP considerado mais provável.")


def _sec_referencias(doc: Document) -> None:
    _h1(doc, "8", "Referências")
    refs = [
        "BRASIL. Ministério da Saúde. Sistema de Informação de Agravos de Notificação "
        "(SINAN). Brasília: SVS/MS, 2024. Disponível em: <https://sinan.saude.gov.br>.",

        "INSTITUTO NACIONAL DE METEOROLOGIA (INMET). Banco de Dados Meteorológicos "
        "para Ensino e Pesquisa (BDMEP). Brasília: INMET, 2024. "
        "Disponível em: <https://bdmep.inmet.gov.br>.",

        "INTERGOVERNMENTAL PANEL ON CLIMATE CHANGE (IPCC). Sixth Assessment Report — "
        "Working Group I: The Physical Science Basis. Cambridge: Cambridge University "
        "Press, 2021.",

        "LOWE, R. et al. Combined effects of hydrometeorological hazards and "
        "urbanisation on dengue risk in Brazil. The Lancet Planetary Health, "
        "v. 5, n. 4, p. e209–e219, 2021.",

        "NATIONAL OCEANIC AND ATMOSPHERIC ADMINISTRATION (NOAA). Oceanic Niño Index "
        "(ONI). Silver Spring: NOAA, 2024. "
        "Disponível em: <https://www.cpc.ncep.noaa.gov>.",
    ]
    for ref in refs:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        pf.space_before = Pt(0)
        pf.space_after = Pt(4)
        pf.first_line_indent = Cm(-0.5)
        pf.left_indent = Cm(0.5)
        r = p.add_run(ref)
        r.font.name = FONT_NAME
        r.font.size = FONT_SIZE


# ═══════════════════════════ GERADOR PRINCIPAL ═══════════════════════════

def generate() -> None:
    logger.info("Carregando dados para relatório ABNT Sem Incremento (.docx)...")
    hist = _load_hist()
    sem = _load_sem()
    ssp = _load_ssp()
    ml_sem = _load_ml_sem()
    lat_sem = _load_lat_sem()
    cmp_txt = _load_comparacao()

    doc = Document()
    _setup_document(doc)
    _add_footer_page_number(doc)

    logger.info("Compondo seções ABNT...")
    _sec_capa(doc)
    _sec_resumo(doc)
    _sec_sumario(doc)
    _sec_objetivo(doc)
    _sec_premissas(doc)
    _sec_metodologia(doc)
    _sec_historico(doc, hist)
    _sec_projecao(doc, sem, hist)
    _sec_por_lat(doc, lat_sem)
    _sec_ml(doc, ml_sem)
    _sec_comparativo(doc, sem, ssp, hist, cmp_txt)
    _sec_implicacoes(doc)
    _sec_referencias(doc)

    OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_DOCX)
    logger.info("Documento ABNT salvo: %s", OUT_DOCX)


if __name__ == "__main__":
    generate()
