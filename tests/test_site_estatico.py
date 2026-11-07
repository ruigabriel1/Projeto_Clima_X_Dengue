"""Versão estática (GitHub Pages): a página gerada aponta para os arquivos e liga o modo estático."""
from src.prediction_service.site_estatico import LINK_API, _pagina, _proximos_meses


def test_pagina_estatica():
    html = _pagina("2026-11-07")
    assert '"/static/' not in html and '"static/css/modern.css' in html      # caminhos relativos (subpasta do Pages)
    assert 'window.PRODIGIA_ESTATICO = {"gerado_em": "2026-11-07"}' in html
    assert html.index("PRODIGIA_ESTATICO") < html.index('src="static/js/app.js')   # a marca vem antes do app
    assert LINK_API in html and 'href="/docs"' not in html                    # /docs não existe no Pages
    assert "40 segundos" not in html                                          # sem servidor para aquecer


def test_proximos_meses_vira_o_ano():
    assert _proximos_meses((2026, 11)) == [(2026, 11), (2027, 0), (2027, 1)]   # (ano, mês 0-based)
