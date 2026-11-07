"""
Versão estática da aplicação (GitHub Pages): as mesmas 5 abas, com as respostas da API calculadas antes.

As previsões só mudam uma vez por mês (quando um mês consolida), então tudo o que a aplicação pede ao servidor pode
ser gerado de uma vez e servido como arquivos. Quem abre o link não espera o modelo aquecer, e o site não "dorme".

    python main.py exportar-site            → site/ (index.html, static/, dados/*.json)

Os arquivos são produzidos chamando as MESMAS funções das rotas da API (app/server.py), para não haver duas versões
da regra de negócio. O navegador só remonta o que é repetitivo:
  - meses além de 3 à frente (faixa histórica) a partir do cenário-base do município;
  - cenários de +1/+2 °C a partir do cenário-base × o fator de clima de cada mês do calendário.

Arquivos em site/dados/:
  municipios.json, confiabilidade_<doenca>.json, desempenho_<doenca>.json, ranking_<doenca>_h<h>.json,
  local/<doenca>/<codigo|sul>.json  ({previsoes, historico, cenario}), resultados_dengue.json, meta.json
"""
from __future__ import annotations

import json
import logging
import shutil
import time
from pathlib import Path

from src.config import BASE_DIR, OUTPUT_DIR

logger = logging.getLogger(__name__)

DESTINO = BASE_DIR / "site"
DOENCAS = ("dengue", "chikungunya")
DELTAS = (1.0, 2.0)
MESES_HISTORICO = 36
LINK_API = "https://github.com/ruigabriel1/Projeto_Clima_X_Dengue#o-que-a-api-entrega"


def _gravar(path: Path, obj) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), default=str)
    path.write_text(texto, encoding="utf-8")
    return len(texto)


def _dump(x):
    return x.model_dump(mode="json") if hasattr(x, "model_dump") else x


def _proximos_meses(ano_mes: tuple[int, int], n: int = 3) -> list[tuple[int, int]]:
    base = ano_mes[0] * 12 + ano_mes[1] - 1
    return [divmod(base + k, 12) for k in range(1, n + 1)]


def _cenario(srv, code: str, doenca: str) -> dict:
    """Cenário-base (clima atual) + fator de clima por mês do calendário para +1 e +2 °C."""
    base = _dump(srv.api_cenario(code, doenca, 0.0, 5))
    deltas = {}
    for d in DELTAS:
        r = _dump(srv.api_cenario(code, doenca, d, 5))
        # o cenário se repete a cada ano no mesmo mês do calendário: guarda os valores EXATOS do servidor por mês
        meses = {}
        for p in r["pontos"]:
            meses.setdefault(str(int(p["mes"][5:])), [p["p10"], p["p50"], p["p90"], p["fator_clima"],
                                                      p["fator_clima_lo"], p["fator_clima_hi"]])
        deltas[str(int(d))] = {"meses": meses, "avisos": r.get("avisos", []), "nota": r.get("nota")}
    return {"base": base, "deltas": deltas}


def _pagina(gerado_em: str) -> str:
    html = (BASE_DIR / "app" / "templates" / "index.html").read_text(encoding="utf-8")
    trocas = {
        '"/static/': '"static/',
        '<a href="/docs">API (/docs)</a>': f'<a href="{LINK_API}" target="_blank" rel="noopener">API (roda com Docker)</a>',
        "<strong>Preparando o modelo…</strong>": "<strong>Carregando os dados…</strong>",
        ("Na primeira abertura leva cerca de 40 segundos: o servidor carrega 12 anos de dados dos 1.190 municípios\n"
         "                e calcula as previsões de todos eles. Depois disso, as respostas são imediatas."):
            "Previsões calculadas para os 1.190 municípios do PR, SC e RS.",
    }
    for a, b in trocas.items():
        if a not in html:
            raise RuntimeError(f"index.html mudou: trecho não encontrado para a versão estática: {a[:60]!r}")
        html = html.replace(a, b)
    marca = '  <script type="module" src="static/js/main.js'
    flag = f'  <script>window.PRODIGIA_ESTATICO = {{"gerado_em": "{gerado_em}"}};</script>\n'
    return html.replace(marca, flag + marca, 1)


def exportar(destino: Path = DESTINO, doencas=DOENCAS, limite_cidades: int | None = None) -> dict:
    """Gera a versão estática. `limite_cidades` serve para testes rápidos."""
    from app import server as srv
    from src.prediction_service.predictor import CidadeNaoEncontrada, get_preditor

    t0 = time.time()
    if destino.exists():
        shutil.rmtree(destino)
    dados = destino / "dados"
    p = get_preditor()
    gerado_em = time.strftime("%Y-%m-%d")

    # página e arquivos do front-end
    shutil.copytree(BASE_DIR / "app" / "static", destino / "static",
                    ignore=shutil.ignore_patterns("proposta_visual.html", "*.map"))
    (destino / "index.html").write_text(_pagina(gerado_em), encoding="utf-8")
    (destino / ".nojekyll").write_text("", encoding="utf-8")   # GitHub Pages: servir como está

    tamanho = _gravar(dados / "municipios.json", srv.api_municipios("dengue"))
    resultados = OUTPUT_DIR / "dashboard" / "resultados_dengue.json"
    if resultados.exists():
        shutil.copy(resultados, dados / "resultados_dengue.json")

    resumo = {"gerado_em": gerado_em, "doencas": {}, "pulados": {}}
    for d in doencas:
        meta = p.metadata(d)
        tamanho += _gravar(dados / f"confiabilidade_{d}.json", srv.api_confiabilidade(d))
        tamanho += _gravar(dados / f"desempenho_{d}.json",
                           {h: x.get("desempenho") for h, x in meta["horizontes"].items()})
        for h in (1, 2, 3):
            tamanho += _gravar(dados / f"ranking_{d}_h{h}.json", _dump(srv.api_ranking(d, h, None, 0, 1190)))
        meses = _proximos_meses(p.ultimo_mes_consolidado(d))
        codigos = sorted(meta["cidades"])[:limite_cidades] if limite_cidades else sorted(meta["cidades"])
        pulados = []
        for i, code in enumerate(["sul", *codigos]):
            arq = {"historico": srv.api_historico(code, d, MESES_HISTORICO), "cenario": _cenario(srv, code, d)}
            if code != "sul":
                prev = {}
                for ano, mes in meses:
                    try:
                        r = _dump(p.prever_mes(code, d, ano, mes + 1))
                    except (CidadeNaoEncontrada, LookupError) as e:
                        pulados.append(f"{code}: {e}")
                        prev = None
                        break
                    r.pop("desempenho_horizonte", None)   # igual para todas as cidades: vai em desempenho_<d>.json
                    prev[f"{ano}-{mes + 1:02d}"] = r
                if prev is None:
                    continue
                arq["previsoes"] = prev
            tamanho += _gravar(dados / "local" / d / f"{code}.json", arq)
            if i % 200 == 0:
                logger.info(f"site estático {d}: {i}/{len(codigos)} municípios ({time.time() - t0:.0f} s)")
        resumo["doencas"][d] = {"municipios": len(codigos) - len(pulados),
                                "meses_previsao": [f"{a}-{m + 1:02d}" for a, m in meses]}
        resumo["pulados"][d] = pulados
    resumo["tamanho_mb"] = round(tamanho / 1e6, 1)
    resumo["duracao_s"] = round(time.time() - t0)
    _gravar(dados / "meta.json", resumo)
    logger.info(f"Versão estática em {destino}: {resumo['tamanho_mb']} MB de dados, {resumo['duracao_s']} s")
    return resumo
