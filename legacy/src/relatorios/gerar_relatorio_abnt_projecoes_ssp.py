#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Relatório Técnico ABNT — Projeções com Cenários SSP (2025-2040)

Gera um documento Word (.docx) estruturado conforme ABNT NBR 14724,
com margens, espaçamento, fontes e tabelas corretos natively.

Saída: output/projecoes_regionais/relatorio_tecnico_abnt_projecoes_ssp.docx
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
OUT_SSP = ROOT / "output" / "projecoes_regionais"
OUT_DOCX = OUT_SSP / "relatorio_tecnico_abnt_projecoes_ssp.docx"

EPS = 1e-9
DATA_HOJE = datetime.now().strftime("%d/%m/%Y")
ANO_REF = 2026

SCENARIOS = {
    "ssp126": ("SSP1-2.6", "#3f8f8f"),
    "ssp245": ("SSP2-4.5", "#3b5f8a"),
    "ssp370": ("SSP3-7.0", "#cc7f2a"),
    "ssp585": ("SSP5-8.5", "#b24a3a"),
}

FONT_NAME = "Arial"
FONT_SIZE = Pt(12)
FONT_SIZE_SM = Pt(10)
FONT_SIZE_TITLE = Pt(14)
COLOR_HDR_FILL = "204070"   # azul marinho cabeçalho
COLOR_ROW_ALT  = "EEF4FA"  # azul claro alternado


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
    for tag, text in [
        ("w:fldChar", None, {"w:fldCharType": "begin"}),
        ("w:instrText", " PAGE ", {"xml:space": "preserve"}),
        ("w:fldChar", None, {"w:fldCharType": "end"}),
    ] if False else []:
        pass
    # Insere campo PAGE via XML
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
          keep_run: bool = False
          ) -> tuple:
    """Adiciona parágrafo com formatação ABNT e retorna (paragraph, run)."""
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
    if keep_run:
        return p, run
    return p, run


def _body(doc: Document, text: str) -> None:
    """Parágrafo de corpo padrão ABNT: justificado, recuo 1.25cm, 1.5."""
    _para(doc, text)


def _body_ni(doc: Document, text: str, bold: bool = False) -> None:
    """Corpo sem recuo de primeira linha."""
    _para(doc, text, first_indent=None, bold=bold)


def _h1(doc: Document, num: str, title: str) -> None:
    """Título de seção primária ABNT: negrito, maiúsculas, sem recuo."""
    p, r = _para(
        doc, f"{num}  {title.upper()}" if num else title.upper(),
        align=WD_ALIGN_PARAGRAPH.LEFT,
        bold=True,
        space_before=Pt(18),
        space_after=Pt(6),
        first_indent=None,
        keep_run=True,
    )


def _h2(doc: Document, num: str, title: str) -> None:
    """Título de seção secundária ABNT: negrito, título, sem recuo."""
    p, r = _para(
        doc, f"{num}  {title}",
        align=WD_ALIGN_PARAGRAPH.LEFT,
        bold=True,
        space_before=Pt(12),
        space_after=Pt(6),
        first_indent=None,
        keep_run=True,
    )


def _add_chart(doc: Document, fig: plt.Figure, caption: str,
               width_cm: float = 14.5) -> None:
    """Embute figura matplotlib como PNG no documento e adiciona legenda."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=180, bbox_inches="tight")
    buf.seek(0)
    plt.close(fig)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(4)
    run = p.add_run()
    run.add_picture(buf, width=Cm(width_cm))

    cp = doc.add_paragraph(caption)
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cp.paragraph_format.space_before = Pt(2)
    cp.paragraph_format.space_after = Pt(12)
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
    """Tabela formatada com cabeçalho azul e linhas alternadas."""
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
        for ci, (cell, val) in enumerate(zip(tbl.rows[ri + 1].cells, row_data)):
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


def _load_ssp() -> pd.DataFrame:
    p = OUT_SSP / "projecao_regiao_sul_consolidado.csv"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p)
    return df.groupby(["scenario", "year"], as_index=False)["pred_cases"].sum()


def _load_ml() -> pd.DataFrame:
    p = OUT_SSP / "previsao_ml_2025_regional.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _load_metricas() -> pd.DataFrame:
    p = OUT_SSP / "ml_completo" / "metricas_ml_completo.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()


def _load_por_lat() -> pd.DataFrame:
    files = sorted(OUT_SSP.glob("projecao_latitude_-*.csv"))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_csv(f) for f in files], ignore_index=True)


# ═══════════════════════════ SEÇÕES DO DOCUMENTO ═══════════════════════════

def _sec_capa(doc: Document) -> None:
    # Espaço superior
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
        "PROJEÇÕES DE RISCO DE DENGUE\nNA REGIÃO SUL DO BRASIL\n"
        "SOB CENÁRIOS CLIMÁTICOS SSP DO IPCC\n(2025 – 2040)",
        align=WD_ALIGN_PARAGRAPH.CENTER, bold=True,
        size=FONT_SIZE_TITLE, first_indent=None,
        space_before=Pt(0), space_after=Pt(18), keep_run=True,
    )

    p, r = _para(
        doc,
        "Modelo Log-linear Municipal com Lag Climático\n"
        "e HistGradientBoosting · Cenários SSP1-2.6 a SSP5-8.5",
        align=WD_ALIGN_PARAGRAPH.CENTER, italic=True,
        first_indent=None, space_after=Pt(60), keep_run=True,
    )

    for _ in range(6):
        doc.add_paragraph()

    p, r = _para(
        doc,
        f"Relatório Técnico — {DATA_HOJE}\n"
        "Projeto Clima × Dengue\n"
        "Dados: SINAN · INMET · NOAA · IBGE",
        align=WD_ALIGN_PARAGRAPH.CENTER,
        first_indent=None, keep_run=True,
    )

    doc.add_page_break()


def _sec_resumo(doc: Document) -> None:
    _h1(doc, "", "Resumo")
    _body(doc,
        "Este relatório técnico apresenta as projeções de incidência de dengue para a "
        "Região Sul do Brasil (Paraná, Santa Catarina e Rio Grande do Sul) no horizonte "
        "2025–2040, sob quatro cenários de emissões do IPCC AR6: SSP1-2.6 (mitigação "
        "agressiva), SSP2-4.5 (intermediário), SSP3-7.0 (alta emissão) e SSP5-8.5 "
        "(muito alta emissão). O modelo combina regressão log-linear por município com "
        "lag temporal de três meses e um modelo de Machine Learning (HistGradientBoosting) "
        "treinado sobre dados históricos de temperatura, precipitação e ENSO (ONI). "
        "Os resultados indicam elevação expressiva do risco em todos os cenários, com "
        "gradiente crescente em direção ao sul ao longo do período projetado.")
    p, r = _para(doc,
        "Palavras-chave: dengue; projeções climáticas; SSP; Região Sul; ML; epidemiologia.",
        italic=True, first_indent=None, space_after=Pt(0))
    doc.add_page_break()


def _sec_sumario(doc: Document) -> None:
    _h1(doc, "", "Sumário")
    itens = [
        ("1", "Introdução", "4"),
        ("2", "Fontes de Dados", "4"),
        ("3", "Metodologia", "5"),
        ("3.1", "Modelo Log-linear com Lag Climático", "5"),
        ("3.2", "Modelo de Machine Learning", "5"),
        ("3.3", "Cenários SSP e Incrementos Climáticos", "5"),
        ("3.4", "Faixas de Latitude", "6"),
        ("4", "Resultados — Histórico 2015–2024", "6"),
        ("5", "Resultados — Projeções 2025–2040", "7"),
        ("5.1", "Consolidado Regional por Cenário SSP", "7"),
        ("5.2", "Análise por Faixa de Latitude", "8"),
        ("5.3", "Previsão Pontual 2025 (Modelo ML)", "8"),
        ("6", "Discussão e Limitações", "9"),
        ("7", "Referências", "9"),
    ]
    for num, title, pg in itens:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.first_line_indent = None
        # Configura tab stops: esquerda 0.8cm e direita pontilhada em ~13.5cm
        pPr = p._p.get_or_add_pPr()
        tabs_el = OxmlElement("w:tabs")
        t_left = OxmlElement("w:tab")
        t_left.set(qn("w:val"), "left")
        t_left.set(qn("w:pos"), "576")         # 0.8cm
        t_right = OxmlElement("w:tab")
        t_right.set(qn("w:val"), "right")
        t_right.set(qn("w:leader"), "dot")
        t_right.set(qn("w:pos"), "9360")        # ~16.5cm (area util)
        tabs_el.append(t_left)
        tabs_el.append(t_right)
        pPr.append(tabs_el)
        r1 = p.add_run(f"{num}\t{title}\t{pg}")
        r1.font.name = FONT_NAME
        r1.font.size = FONT_SIZE
    doc.add_page_break()


def _sec_introducao(doc: Document) -> None:
    _h1(doc, "1", "Introdução")
    _body(doc,
        "A dengue representa um dos principais desafios de saúde pública no Brasil, "
        "com incidência fortemente influenciada por variáveis climáticas — temperatura "
        "do ar, precipitação pluviométrica e padrões de circulação oceânica (ENSO). "
        "A expansão geográfica do vetor Aedes aegypti em direção ao sul do país torna "
        "a Região Sul um território de crescente vulnerabilidade epidemiológica.")
    _body(doc,
        "Este relatório documenta as projeções de risco para o período 2025–2040 nos "
        "estados do Paraná (PR), Santa Catarina (SC) e Rio Grande do Sul (RS), "
        "abrangendo 1.190 municípios distribuídos em oito faixas de latitude. As "
        "projeções integram os Caminhos Socioeconômicos Compartilhados (SSP) do "
        "Sexto Relatório de Avaliação do IPCC (AR6), fornecendo subsídios "
        "quantitativos para o planejamento de políticas de vigilância epidemiológica "
        "e controle vetorial ao longo das próximas duas décadas.")


def _sec_fontes(doc: Document) -> None:
    _h1(doc, "2", "Fontes de Dados")
    _body(doc,
        "As projeções baseiam-se em quatro conjuntos de dados primários de domínio "
        "público, obtidos de fontes oficiais nacionais e internacionais:")
    hdr = ["Variável", "Fonte", "Período", "Granularidade"]
    rows = [
        ["Casos de Dengue", "SINAN / SVS / MS", "2015–2024", "Mensal por município"],
        ["Temperatura (Tx, Tm, Tn)", "INMET / BDMEP", "2015–2024", "Mensal por estação"],
        ["Precipitação Pluviométrica", "INMET / BDMEP", "2015–2024", "Mensal por estação"],
        ["Índice ONI (ENSO)", "NOAA / CPC", "2015–2024", "Trimestral"],
        ["Geocodificação Municipal", "IBGE", "2022", "Polígonos e centroides"],
    ]
    _table(doc, hdr, rows,
           col_widths=[4.0, 4.0, 2.5, 4.5],
           caption="Tabela 1 — Fontes de dados utilizadas na modelagem.")
    _body(doc,
        "Os dados do SINAN foram consolidados em frequência mensal por município. "
        "As séries climáticas passaram por controle de qualidade (z-score > 3,5) "
        "e interpolação IDW para municípios sem estação meteorológica próxima.")


def _sec_metodologia(doc: Document) -> None:
    _h1(doc, "3", "Metodologia")

    _h2(doc, "3.1", "Modelo Log-linear com Lag Climático Temporal")
    _body(doc,
        "O modelo primário é uma regressão log-linear por município, estimada por "
        "MQO sobre a série histórica 2015–2024. Utiliza lag temporal de três meses "
        "para as variáveis climáticas, capturando o ciclo de incubação e de vida do vetor:")

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.first_line_indent = None
    r = p.add_run(
        "log(Y\u209c + 1) = \u03b1_local + \u03b2_T\u00b7T\u209c\u208b\u2083 "
        "+ \u03b2_P\u00b7P\u209c\u208b\u2083 + \u03b2_ENSO\u00b7ONI\u209c\u208b\u2083 "
        "+ \u03b2_lat\u00b7Lat + \u03b5"
    )
    r.font.name = "Courier New"
    r.font.size = Pt(10)

    _body(doc,
        "onde Y\u209c é o número de casos no mês t; \u03b1_local é o intercepto "
        "municipal calibrado pela mediana dos resíduos históricos; T, P e ONI são "
        "temperatura média, precipitação e ENSO defasados em três meses; e Lat é a "
        "latitude do centroide municipal. Um cap de plausibilidade (percentil 95 "
        "histórico) evita extrapolações biologicamente implausíveis.")

    _h2(doc, "3.2", "Modelo de Machine Learning")
    _body(doc,
        "Um HistGradientBoostingRegressor (scikit-learn \u2265 1.1) foi treinado sobre "
        "o painel histórico completo de 1.190 municípios. Features incluem temperatura "
        "máxima e mínima, precipitação, ONI, faixa de latitude, mês calendário e "
        "lags de 1 a 6 meses. Divisão temporal: 2015–2021 treino, 2022 validação, "
        "2023–2024 teste — sem data leakage.")

    _h2(doc, "3.3", "Cenários SSP e Incrementos Climáticos Anuais")
    hdr = ["Cenário SSP", "Descrição", "\u0394 Temp. (°C/ano)", "Nível IPCC AR6"]
    rows = [
        ["SSP1-2.6", "Mitigação agressiva — metas do Acordo de Paris", "+0,02", "Baixo"],
        ["SSP2-4.5", "Intermediário — continuidade das políticas atuais", "+0,04", "Médio"],
        ["SSP3-7.0", "Alta emissão — sem cooperação climática global", "+0,06", "Alto"],
        ["SSP5-8.5", "Muito alta emissão — intensificação de fósseis", "+0,08", "Muito Alto"],
    ]
    _table(doc, hdr, rows,
           col_widths=[2.8, 6.0, 3.2, 3.0],
           caption="Tabela 2 — Cenários SSP e incrementos térmicos anuais aplicados.")

    _h2(doc, "3.4", "Faixas de Latitude")
    _body(doc,
        "Os 1.190 municípios foram estratificados em oito faixas latitudinais de "
        "1,4° cada, cobrindo –33,7°S a –22,6°S. A estratificação captura o gradiente "
        "climático norte–sul e permite análise espacial diferenciada.")


def _sec_historico(doc: Document, hist: pd.DataFrame) -> None:
    _h1(doc, "4", "Resultados — Histórico 2015–2024")
    media_v = int(hist["casos"].mean()) if not hist.empty else 0
    pico_yr = int(hist.loc[hist["casos"].idxmax(), "year"]) if not hist.empty else 0
    pico_v = int(hist["casos"].max()) if not hist.empty else 0
    _body(doc,
        f"A série histórica 2015–2024 registrou média anual de {_fmt(media_v)} casos "
        f"na Região Sul, com pico em {pico_yr} ({_fmt(pico_v)} casos). A variabilidade "
        "interanual reflete a influência dos eventos El Niño sobre a atividade vetorial, "
        "corroborando a especificação com o índice ONI. O Paraná concentra a maior "
        "parte dos registros, com expansão progressiva para SC e RS a partir de 2019.")

    if not hist.empty:
        fig, ax = plt.subplots(figsize=(11, 4.5))
        bars = ax.bar(hist["year"], hist["casos"], color="#3b5f8a",
                      alpha=0.72, width=0.72, edgecolor="white", linewidth=0.5)
        ax.plot(hist["year"], hist["casos"], color="#1a3a6b", linewidth=2.0,
                marker="o", markersize=6, zorder=3)
        for bar, val in zip(bars, hist["casos"]):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + hist["casos"].max() * 0.012,
                    _fmt(val), ha="center", va="bottom", fontsize=8)
        ax.set_title("Casos de Dengue Observados — Região Sul (2015–2024)",
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
                   "Figura 1 — Série histórica anual de casos de dengue na Região Sul "
                   "(2015–2024). Fonte: SINAN/MS.")


def _sec_projecoes(doc: Document, ssp: pd.DataFrame, hist: pd.DataFrame) -> None:
    _h1(doc, "5", "Resultados — Projeções 2025–2040")

    _h2(doc, "5.1", "Consolidado Regional por Cenário SSP")
    _body(doc,
        "As projeções indicam tendência de elevação em todos os cenários SSP, com "
        "gradiente proporcional à intensidade do aquecimento projetado. O SSP5-8.5 "
        "apresenta a maior aceleração; o SSP1-2.6 exibe trajetória mais estável. "
        "A tabela abaixo consolida os resultados nos anos-chave:")

    if not ssp.empty:
        anos_key = [2025, 2028, 2031, 2034, 2037, 2040]
        hdr_t = ["Cenário"] + [str(a) for a in anos_key]
        tbl_rows = []
        for sc, (label, _) in SCENARIOS.items():
            ds = ssp[ssp["scenario"] == sc].sort_values("year")
            row = [label]
            for a in anos_key:
                v = ds.loc[ds["year"] == a, "pred_cases"]
                row.append(_fmt(float(v.iloc[0])) if not v.empty else "—")
            tbl_rows.append(row)
        widths = [2.5] + [2.0] * len(anos_key)
        _table(doc, hdr_t, tbl_rows, col_widths=widths,
               caption="Tabela 3 — Projeção de casos (anos-chave) por cenário SSP · Região Sul.")

    if not ssp.empty:
        fig, ax = plt.subplots(figsize=(11, 5))
        if not hist.empty:
            ax.plot(hist["year"], hist["casos"], color="black", linewidth=2.2,
                    marker="o", markersize=4, label="Observado (2015–2024)", zorder=6)
        for sc, (label, color) in SCENARIOS.items():
            ds = ssp[ssp["scenario"] == sc].sort_values("year")
            if not ds.empty:
                ax.plot(ds["year"], ds["pred_cases"], color=color, linewidth=2.0,
                        linestyle="-" if sc == "ssp245" else "--",
                        marker=".", markersize=4, label=label, zorder=4)
        ax.axvline(x=2024.5, color="#aaa", linewidth=0.8, linestyle=":")
        ax.set_title("Projeções de Dengue 2025–2040 — Cenários SSP · Região Sul",
                     fontsize=12, fontweight="bold", pad=8)
        ax.set_xlabel("Ano", fontsize=10)
        ax.set_ylabel("Casos Projetados", fontsize=10)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", ".")))
        ax.legend(loc="upper left", fontsize=9, frameon=True)
        ax.grid(axis="y", linestyle="--", alpha=0.3)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        _add_chart(doc, fig,
                   "Figura 2 — Projeções consolidadas 2025–2040 por cenário SSP. "
                   "Linha preta: observado 2015–2024.")


def _sec_por_lat(doc: Document, lat_df: pd.DataFrame) -> None:
    _h2(doc, "5.2", "Análise por Faixa de Latitude")
    _body(doc,
        "A estratificação latitudinal revela que as faixas mais ao norte "
        "(latitude < –24°S) mantêm concentração de risco mais elevada. "
        "As faixas do extremo sul exibem crescimento relativo mais expressivo, "
        "pois partem de patamares históricos menores e são mais sensíveis ao "
        "incremento térmico projetado.")

    if not lat_df.empty:
        sc_ref = "ssp245"
        ds = lat_df[lat_df["scenario"] == sc_ref].copy()
        hdr_l = ["Faixa de Latitude", "Municípios", "2025", "2030", "2035", "2040", "Var. 25→40"]
        rows_l = []
        for (lmin, lmax), grp in ds.groupby(["latitude_min", "latitude_max"]):
            grp = grp.sort_values("year")
            n_m = int(grp["n_municipios"].iloc[0]) if "n_municipios" in grp.columns else "—"
            def gv(yr):
                v = grp.loc[grp["year"] == yr, "pred_cases"]
                return float(v.iloc[0]) if not v.empty else 0.0
            v25, v30, v35, v40 = gv(2025), gv(2030), gv(2035), gv(2040)
            rows_l.append([
                f"{abs(lmin):.1f}°S — {abs(lmax):.1f}°S",
                str(n_m), _fmt(v25), _fmt(v30), _fmt(v35), _fmt(v40),
                _pct(v40, v25),
            ])
        _table(doc, hdr_l, rows_l,
               col_widths=[3.5, 1.8, 2.0, 2.0, 2.0, 2.0, 2.2],
               caption="Tabela 4 — Projeção por faixa de latitude (SSP2-4.5 · anos selecionados).")


def _sec_ml(doc: Document, ml: pd.DataFrame, metricas: pd.DataFrame) -> None:
    _h2(doc, "5.3", "Previsão Pontual 2025 — Modelo de Machine Learning")
    _body(doc,
        "O HistGradientBoosting gera previsão pontual para 2025 por cenário de "
        "incremento. A seguir, as previsões regionais consolidadas e as métricas "
        "de desempenho por partição temporal:")

    if not ml.empty:
        hdr_m = ["Cenário", "Tipo de Incremento", "Casos 2025 (ML)"]
        rows_m = [[str(r.get("scenario", "")),
                   str(r.get("tipo_incremento", "")),
                   _fmt(float(r.get("pred_cases", 0)))]
                  for _, r in ml.iterrows()]
        _table(doc, hdr_m, rows_m,
               col_widths=[3.5, 5.0, 4.0],
               caption="Tabela 5 — Previsão regional 2025 pelo modelo ML por cenário.")

    if not metricas.empty:
        _body_ni(doc, "Métricas de desempenho do modelo:")
        hdr_mt = ["Partição", "MAE", "RMSE", "MAPE (%)", "R²"]
        rows_mt = [[str(r.get("split", "")),
                    f"{r.get('mae', 0):.2f}",
                    f"{r.get('rmse', 0):.2f}",
                    f"{r.get('mape_pct', 0):.1f}",
                    f"{r.get('r2', 0):.3f}"]
                   for _, r in metricas.iterrows()]
        _table(doc, hdr_mt, rows_mt,
               col_widths=[3.5, 2.5, 2.5, 2.5, 2.0],
               caption="Tabela 6 — Métricas de desempenho do HistGradientBoosting.")


def _sec_discussao(doc: Document) -> None:
    _h1(doc, "6", "Discussão e Limitações")
    _body(doc,
        "Os resultados confirmam a sensibilidade climática da dengue na Região Sul e "
        "evidenciam que a expansão do risco não é uniforme no espaço e no tempo. "
        "O gradiente latitudinal — com maior crescimento relativo nas faixas meridionais "
        "— aponta para homogeneização do risco, com potencial impacto sobre sistemas "
        "de saúde historicamente menos preparados para dengue no extremo sul.")
    _body(doc,
        "Limitações relevantes: (i) incerteza intrínseca dos cenários SSP (trajetórias, "
        "não previsões determinísticas); (ii) ausência de modelagem explícita de "
        "imunidade de rebanho e variações na cobertura de saúde pública; "
        "(iii) premissa de distribuição geográfica do vetor constante; "
        "(iv) possível viés de notificação no SINAN; (v) não inclusão de downscaling "
        "regional de precipitação por cenário SSP. "
        "Recomenda-se atualização anual do modelo com novos dados observacionais.")


def _sec_referencias(doc: Document) -> None:
    _h1(doc, "7", "Referências")
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

        "SCIKIT-LEARN DEVELOPERS. HistGradientBoostingRegressor. "
        "scikit-learn 1.x Documentation. 2024. "
        "Disponível em: <https://scikit-learn.org>.",
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
    logger.info("Carregando dados para relatório ABNT SSP (.docx)...")
    hist = _load_hist()
    ssp = _load_ssp()
    ml = _load_ml()
    metricas = _load_metricas()
    lat_df = _load_por_lat()

    doc = Document()
    _setup_document(doc)
    _add_footer_page_number(doc)

    logger.info("Compondo seções ABNT...")
    _sec_capa(doc)
    _sec_resumo(doc)
    _sec_sumario(doc)
    _sec_introducao(doc)
    _sec_fontes(doc)
    _sec_metodologia(doc)
    _sec_historico(doc, hist)
    _sec_projecoes(doc, ssp, hist)
    _sec_por_lat(doc, lat_df)
    _sec_ml(doc, ml, metricas)
    _sec_discussao(doc)
    _sec_referencias(doc)

    OUT_DOCX.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT_DOCX)
    logger.info("Documento ABNT salvo: %s", OUT_DOCX)


if __name__ == "__main__":
    generate()
