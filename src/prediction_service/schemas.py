"""Schemas Pydantic de entrada e saída da API de previsão (v5: alerta de risco)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

Doenca = Literal["dengue", "chikungunya", "zika"]
NivelRisco = Literal["baixo", "medio", "alto", "critico"]


class PredictRequest(BaseModel):
    codigo_ibge: str = Field(..., description="Código IBGE do município (6 ou 7 dígitos)", examples=["410690"])
    doenca: Doenca = Field("dengue")
    meses_a_frente: int = Field(1, ge=1, le=3, description="Horizonte da previsão (1 a 3 meses)")

    @field_validator("codigo_ibge")
    @classmethod
    def _normaliza_codigo(cls, v: str) -> str:
        v = str(v).strip()
        if not v.isdigit() or len(v) not in (6, 7):
            raise ValueError("codigo_ibge deve ter 6 ou 7 dígitos")
        return v[:6]   # o 7º dígito do IBGE é verificador; o painel usa 6


class PredictResponse(BaseModel):
    disponivel: bool = True
    codigo_ibge: str
    cidade: Optional[str] = None
    doenca: Doenca
    horizonte_meses: int
    mes_alvo: Optional[str] = None
    ultimo_mes_observado: Optional[str] = None
    # ---- produto principal: risco relativo à própria cidade
    probabilidade_risco_alto: Optional[float] = Field(
        None, description="P(incidência do mês-alvo > P75 histórico da própria cidade), calibrada")
    nivel_risco: Optional[NivelRisco] = None
    limiar_risco_incidencia_100k: Optional[float] = None
    alerta_infodengue_ultimo: Optional[int] = Field(
        None, description="Nível de alerta oficial do InfoDengue (1–4) no último mês observado")
    # ---- informação secundária: magnitude
    casos_previstos: Optional[int] = None
    intervalo_confianca: Optional[list[int]] = Field(None, description="Intervalo de 90% [inferior, superior]")
    incidencia_prevista_100k: Optional[float] = None
    modelo_usado: Optional[str] = None
    confiabilidade: Optional[Literal["normal", "baixa"]] = None
    avisos: list[str] = []
    nota: str = ""
