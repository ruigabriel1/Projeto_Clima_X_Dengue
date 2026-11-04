"""
Tradução de casos previstos em nível de risco.

O risco é RELATIVO À PRÓPRIA CIDADE (mesma lógica da métrica "risco alto" do experimento):
  baixo   ≤ mediana histórica mensal da cidade (ou < 1 caso)
  medio   mediana < previsto ≤ P75
  alto    P75 < previsto ≤ P90
  critico previsto > P90
Uma cidade grande com 50 casos/mês pode estar em risco baixo; uma pequena com 5, em risco crítico.
"""
from __future__ import annotations

NIVEIS = ("baixo", "medio", "alto", "critico")


def classificar_risco(casos_previstos: float, p50: float, p75: float, p90: float) -> str:
    if casos_previstos < 1 or casos_previstos <= p50:
        return "baixo"
    if casos_previstos <= p75:
        return "medio"
    if casos_previstos <= p90:
        return "alto"
    return "critico"
