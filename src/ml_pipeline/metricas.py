"""
As 5 métricas do experimento final (fixadas ANTES de rodar — ver docs/PLANO_EXPERIMENTO_FINAL.md §1.3).

  MAE          Erro médio absoluto em casos por cidade/mês.
  R²           Variação explicada (no valor real, sem corte).
  MAE-surto    MAE só nos meses de surto. Surto = casos > P90 da PRÓPRIA cidade,
               com o P90 calculado nos anos de treino do fold (sem olhar o futuro).
               Critério: MAE-surto < 50% do pico médio (média dos casos reais nos meses de surto).
  Skill Score  (MAE_persistência − MAE_modelo) / MAE_persistência, persistência = casos[t−h].
  AUC risco    Classificação "risco alto" = casos > mediana da PRÓPRIA cidade nos anos de treino.
               Score = casos previstos. Também reporta a acurácia com o mesmo limiar.

Critérios de aceitação para uso real:
  MAE < MAE_persistência · R² > 0,40 (só dengue) · MAE-surto < 0,5 × pico médio ·
  Skill > 0 · AUC > 0,75
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score, roc_auc_score

CRITERIO_R2_DENGUE = 0.40
CRITERIO_AUC = 0.75
CRITERIO_FRACAO_PICO = 0.50

# Quantis por cidade usados nas definições (calculados no treino de cada fold)
Q_SURTO = 0.90
Q_RISCO = 0.50


def calcular_metricas(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_persist: np.ndarray,
    limiar_surto: np.ndarray,
    limiar_risco: np.ndarray,
) -> dict:
    """
    Calcula as 5 métricas. Todos os argumentos são arrays alinhados (uma linha = cidade × mês).
    limiar_surto / limiar_risco: P90 / mediana da cidade nos anos de treino.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    y_persist = np.nan_to_num(np.asarray(y_persist, dtype=float), nan=0.0)
    limiar_surto = np.asarray(limiar_surto, dtype=float)
    limiar_risco = np.asarray(limiar_risco, dtype=float)

    mae = mean_absolute_error(y_true, y_pred)
    mae_persist = mean_absolute_error(y_true, y_persist)
    r2 = r2_score(y_true, y_pred) if len(y_true) > 1 else np.nan

    surto = y_true > limiar_surto
    if surto.any():
        mae_surto = mean_absolute_error(y_true[surto], y_pred[surto])
        pico_medio = float(y_true[surto].mean())
    else:
        mae_surto = pico_medio = np.nan

    alto = y_true > limiar_risco
    if 0 < alto.sum() < len(alto):
        auc = roc_auc_score(alto, y_pred)
    else:
        auc = np.nan
    acuracia = float(((y_pred > limiar_risco) == alto).mean())

    skill = (mae_persist - mae) / mae_persist if mae_persist > 0 else np.nan

    return {
        "n": int(len(y_true)),
        "mae": float(mae),
        "r2": float(r2),
        "mae_surto": float(mae_surto),
        "pico_medio_surto": float(pico_medio),
        "n_surto": int(surto.sum()),
        "mae_persistencia": float(mae_persist),
        "skill_score": float(skill),
        "auc_risco_alto": float(auc),
        "acuracia_risco_alto": acuracia,
        "pct_risco_alto": float(alto.mean()),
    }


def avaliar_criterios(m: dict, doenca: str) -> dict:
    """Aplica os critérios de aceitação do plano a um dicionário de métricas."""
    c = {
        "ok_mae_vs_persistencia": bool(m["mae"] < m["mae_persistencia"]),
        "ok_mae_surto": bool(
            np.isfinite(m["mae_surto"]) and m["mae_surto"] < CRITERIO_FRACAO_PICO * m["pico_medio_surto"]
        ),
        "ok_skill": bool(np.isfinite(m["skill_score"]) and m["skill_score"] > 0),
        "ok_auc": bool(np.isfinite(m["auc_risco_alto"]) and m["auc_risco_alto"] > CRITERIO_AUC),
    }
    # R² > 0,40 é critério só para dengue (plano §1.3)
    c["ok_r2"] = bool(m["r2"] > CRITERIO_R2_DENGUE) if doenca == "dengue" else True
    c["passa_todos"] = all(c.values())
    return c
