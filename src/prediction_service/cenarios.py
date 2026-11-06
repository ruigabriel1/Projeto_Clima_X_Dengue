"""
Longo prazo (até 5 anos) — CENÁRIO, não previsão (docs/PROTOCOLO_V5.md, "Produção v5.1").

O modelo treinado só prevê 1–3 meses à frente (depende dos casos recentes). Para horizontes maiores, a
aplicação mostra:

1. Faixa histórica: P10/P50/P90 dos casos por mês-calendário, com todos os anos consolidados
   ("em janeiro, esta cidade teve entre X e Y casos em 80% dos anos").
2. Cenário climático: a faixa multiplicada pelo fator de risco do DLNM para uma temperatura média
   Δ °C acima da normal da cidade naquele mês.

Sobre a curva do DLNM (temperatura média, RR acumulado nos lags 0–3, relativo à mediana):
- Só a parte quente da curva é usada, a partir do ponto de mínimo (~17–19 °C), e de forma monotônica
  (máximo acumulado). A cauda fria tem IC largo e formato em U pouco plausível (sugeriria que aquecer o
  inverno reduz a dengue), então nos meses frios o fator fica em 1, com aviso.
- Acima da maior temperatura observada o fator não é extrapolado (fica no último valor), com aviso.
- A faixa de incerteza do fator usa os limites do IC da curva, cada um normalizado no seu valor em T
  (envelope aproximado, não um IC formal da razão).
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.ml_pipeline.feature_engineering import DOENCA_PARA_COL
from src.prediction_service.data_fetcher import FonteDados

logger = logging.getLogger(__name__)

REGIAO = "sul"                 # código especial: soma dos 1.190 municípios
JANELA_MINIMO = (15.0, 21.0)   # onde procurar o ponto de mínimo da curva (região de referência)
QUANTIS = (0.10, 0.50, 0.90)


class CurvaClima:
    """Curva exposição-resposta do DLNM reduzida à parte quente e monotônica."""

    def __init__(self, curva: pd.DataFrame):
        c = curva.sort_values("valor").reset_index(drop=True)
        janela = c[c["valor"].between(*JANELA_MINIMO)]
        self.t_ref = float(janela.loc[janela["rr"].idxmin(), "valor"]) if len(janela) else float(c["valor"].median())
        quente = c[c["valor"] >= self.t_ref]
        self.x = quente["valor"].to_numpy(float)
        self.t_max = float(self.x[-1])
        # máximo acumulado: o fator nunca diminui com o aquecimento
        self.log_rr = np.log(np.maximum.accumulate(quente["rr"].to_numpy(float)))
        self.log_lo = np.log(np.maximum.accumulate(quente["ic_lo"].to_numpy(float)))
        self.log_hi = np.log(np.maximum.accumulate(quente["ic_hi"].to_numpy(float)))

    def _g(self, serie: np.ndarray, t) -> np.ndarray:
        return np.interp(np.maximum(np.asarray(t, float), self.t_ref), self.x, serie)

    def fator(self, t_normal, delta: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """(fator, lo, hi) do risco para t_normal + delta em relação a t_normal."""
        t = np.asarray(t_normal, float)
        f = np.exp(self._g(self.log_rr, t + delta) - self._g(self.log_rr, t))
        a = np.exp(self._g(self.log_lo, t + delta) - self._g(self.log_lo, t))
        b = np.exp(self._g(self.log_hi, t + delta) - self._g(self.log_hi, t))
        return f, np.minimum(a, b), np.maximum(a, b)


class Cenarios:
    def __init__(self, fonte: FonteDados, model_dir: Path):
        self.fonte = fonte
        self.model_dir = Path(model_dir)
        self._curvas: dict[str, CurvaClima | None] = {}

    def curva(self, doenca: str) -> CurvaClima | None:
        if doenca not in self._curvas:
            path = self.model_dir / doenca / "dlnm_curva.csv"
            self._curvas[doenca] = CurvaClima(pd.read_csv(path)) if path.exists() else None
        return self._curvas[doenca]

    def _obs(self, doenca: str) -> pd.DataFrame:
        alvo = DOENCA_PARA_COL[doenca]
        p = self.fonte.panel
        cols = ["code", "year", "month", alvo] + [c for c in ("temp_media", "city_name") if c in p.columns]
        return p.dropna(subset=[alvo])[cols].rename(columns={alvo: "casos"})

    def faixa_historica(self, code: str, doenca: str) -> pd.DataFrame:
        """P10/P50/P90 dos casos por mês-calendário (índice 1–12). code='sul' soma a região."""
        o = self._obs(doenca)
        if code == REGIAO:
            n_cid = o.groupby(["year", "month"])["code"].transform("nunique")
            o = o[n_cid >= 0.95 * o["code"].nunique()]          # só meses com a região (quase) completa
            s = o.groupby(["year", "month"], as_index=False)["casos"].sum()
        else:
            s = o[o["code"] == code]
        if s.empty:
            raise LookupError(f"Sem histórico para {code}.")
        q = s.groupby("month")["casos"].quantile(list(QUANTIS)).unstack()
        q.columns = ["p10", "p50", "p90"]
        return q.reindex(range(1, 13))

    def anos_historico(self, doenca: str) -> list[int]:
        o = self._obs(doenca)
        return [int(o["year"].min()), int(o["year"].max())]

    def fator_clima(self, code: str, doenca: str, delta: float) -> tuple[pd.DataFrame, list[str]]:
        """Fator (e envelope) por mês-calendário. Na região: média dos fatores das cidades pesada pelos casos."""
        avisos: list[str] = []
        um = pd.DataFrame({"fator": 1.0, "lo": 1.0, "hi": 1.0}, index=range(1, 13))
        cur = self.curva(doenca)
        if cur is None or delta == 0:
            if cur is None and delta:
                avisos.append("Curva do DLNM indisponível: cenário climático não aplicado.")
            return um, avisos
        o = self._obs(doenca)
        if code != REGIAO:
            o = o[o["code"] == code]
        if "temp_media" not in o.columns:
            avisos.append("Sem temperatura histórica: cenário climático não aplicado.")
            return um, avisos
        norm = (o.groupby(["code", "month"]).agg(t=("temp_media", "mean"), peso=("casos", "mean"))
                .reset_index().dropna(subset=["t"]))
        if norm.empty:
            avisos.append("Sem temperatura histórica para a cidade: cenário climático não aplicado.")
            return um, avisos
        f, lo, hi = cur.fator(norm["t"], delta)
        norm = norm.assign(fator=f, lo=lo, hi=hi, peso=norm["peso"] + 1e-9)
        linhas = {m: {k: float(np.average(g[k], weights=g["peso"])) for k in ("fator", "lo", "hi")}
                  for m, g in norm.groupby("month")}
        out = pd.DataFrame.from_dict(linhas, orient="index")
        frios = sorted(int(m) for m in norm.loc[norm["t"] + delta <= cur.t_ref, "month"].unique())
        if frios:
            onde = "em parte das cidades, " if code == REGIAO else ""
            avisos.append(f"Meses {', '.join(map(str, frios))}: {onde}abaixo de ~{cur.t_ref:.0f} °C o DLNM não estima "
                          "efeito claro do aquecimento; ali o fator fica em 1.")
        if (norm["t"] + delta > cur.t_max).any():
            avisos.append(f"Temperaturas acima de {cur.t_max:.1f} °C ficam fora da faixa observada: o efeito não é extrapolado.")
        return out.reindex(range(1, 13)).fillna(1.0), avisos

    def projecao(self, code: str, doenca: str, delta: float = 0.0, meses: int = 60) -> dict:
        """Faixa (× fator climático) para os `meses` seguintes ao último mês consolidado."""
        faixa = self.faixa_historica(code, doenca)
        fator, avisos = self.fator_clima(code, doenca, delta)
        o = self._obs(doenca)
        ult = o.sort_values(["year", "month"]).iloc[-1]
        base = int(ult["year"]) * 12 + int(ult["month"]) - 1
        pontos = []
        for k in range(1, meses + 1):
            ano, mes = divmod(base + k, 12)
            mes += 1
            fz, fx = faixa.loc[mes], fator.loc[mes]
            pontos.append({"mes": f"{ano}-{mes:02d}",
                           **{q: round(float(fz[q] * fx["fator"]), 1) for q in ("p10", "p50", "p90")},
                           "fator_clima": round(float(fx["fator"]), 3),
                           "fator_clima_lo": round(float(fx["lo"]), 3), "fator_clima_hi": round(float(fx["hi"]), 3)})
        if code == REGIAO:
            nome = "Região Sul (PR, SC, RS)"
        else:
            nomes = o.loc[o["code"] == code, "city_name"].dropna() if "city_name" in o.columns else pd.Series(dtype=str)
            nome = nomes.iloc[-1] if len(nomes) else None
        return {"cidade": nome, "anos_historico": self.anos_historico(doenca), "pontos": pontos, "avisos": avisos}
