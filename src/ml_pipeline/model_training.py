"""
Módulo de treinamento do motor de ML v4 (multi-doença, multi-horizonte).
Isola o algoritmo, a validação temporal e a tunagem de hiperparâmetros.

v4.2 — Correções de vazamento:
  - Corte P99 por cidade com limiar calculado SÓ nos anos de treino de cada fold
    (antes o limiar via o ano de teste).
  - Baseline de persistência usa lag h (último mês conhecido no horizonte h),
    não lag1.
  - _expanding_window_splits aceita max_test_year para preservar o holdout (2025).
  - Hiperparâmetros centralizados em XGB_PARAMS (fixos no experimento final).
"""
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)

from src.ml_pipeline.feature_engineering import PREFIXOS as _PREFIXOS

# Hiperparâmetros FIXOS do XGBoost Poisson. O experimento final mede o efeito de
# horizonte e clima, não otimiza o algoritmo: não alterar sem registrar no artigo.
XGB_PARAMS = dict(
    objective="count:poisson",
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    min_child_weight=5,
    reg_alpha=0.1,
    reg_lambda=5,
    random_state=42,
    eval_metric="poisson-nloglik",
    tree_method="hist",
    n_jobs=-1,
)


def clip_outliers_per_city(df: pd.DataFrame, col: str = "dengue_cases", percentile: float = 99.0) -> pd.Series:
    """
    Clipping P<percentile> **por cidade** usando o próprio df como referência.
    Atenção: só use em dados de treino. Para validação use limiares_por_cidade().
    """
    return df.groupby("code")[col].transform(
        lambda s: s.clip(upper=s.quantile(percentile / 100.0))
    )


def limiares_por_cidade(
    df_ref: pd.DataFrame,
    codes: pd.Series,
    col: str,
    q: float,
) -> np.ndarray:
    """
    Quantil q (0–1) de `col` por cidade, calculado em df_ref (tipicamente o treino),
    mapeado para `codes`. Cidade sem histórico em df_ref recebe o quantil global de df_ref.
    """
    por_cidade = df_ref.groupby("code")[col].quantile(q)
    global_q = float(df_ref[col].quantile(q)) if len(df_ref) else np.nan
    return codes.map(por_cidade).fillna(global_q).to_numpy(dtype=float)


def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true > 1.0
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def _expanding_window_splits(years: pd.Series, min_train_years: int = 3, max_test_year: int | None = None):
    """
    Gera splits Expanding Window (Walk Forward):
      Treina em anos < t, testa no ano t. Garante min_train_years anos no treino.
      max_test_year limita os anos de teste (ex.: 2024 para preservar o holdout 2025).
      O treino de cada fold nunca contém anos ≥ t.

    Yields: (train_mask, test_mask, ano_teste)
    """
    sorted_years = sorted(years.unique())
    for i, test_year in enumerate(sorted_years):
        if i < min_train_years:
            continue
        if max_test_year is not None and test_year > max_test_year:
            break
        train_mask = years < test_year
        test_mask = years == test_year
        yield train_mask, test_mask, test_year


def _persist_col(target_col: str, horizonte: int = 1) -> str | None:
    """Coluna do último valor conhecido no horizonte h (<prefixo>_lag<h>)."""
    prefix = _PREFIXOS.get(target_col)
    return f"{prefix}_lag{horizonte}" if prefix else None


def _build_base_margin(df: pd.DataFrame) -> np.ndarray | None:
    """Offset = log(pop / 100.000) para modelar incidência, não contagem bruta."""
    if "populacao" not in df.columns:
        return None
    pop = df["populacao"].fillna(1).clip(lower=1).values
    return np.log(pop / 100_000.0)


def alvo_treino(df_train: pd.DataFrame, target_col: str, clip_percentile: float | None) -> np.ndarray:
    """Alvo de treino, com corte P<clip_percentile> por cidade calculado no próprio treino."""
    y = df_train[target_col].to_numpy(dtype=float)
    if clip_percentile is None:
        return y
    lim = limiares_por_cidade(df_train, df_train["code"], target_col, clip_percentile / 100.0)
    return np.minimum(y, lim)


def fit_predict_fold(
    df_train: pd.DataFrame,
    df_test: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    clip_percentile: float | None = None,
    params: dict | None = None,
    use_pop_offset: bool = False,
):
    """Treina um XGBoost Poisson em df_train e prevê df_test. Retorna (modelo, previsões ≥ 0)."""
    params = params or XGB_PARAMS
    y_train = alvo_treino(df_train, target_col, clip_percentile)
    fit_kw, pred_kw = {}, {}
    if use_pop_offset:
        fit_kw["base_margin"] = _build_base_margin(df_train)
        pred_kw["base_margin"] = _build_base_margin(df_test)
    model = xgb.XGBRegressor(**params)
    model.fit(df_train[feature_cols], y_train, **fit_kw)
    preds = np.maximum(model.predict(df_test[feature_cols], **pred_kw), 0)
    return model, preds


def train_model(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "dengue_cases",
    save_path: Path | None = None,
    clip_percentile: float | None = None,
    use_pop_offset: bool = False,
    return_oof: bool = False,
    horizonte: int = 1,
    max_test_year: int | None = None,
):
    """
    Treina o modelo XGBoost Poisson com Expanding Window CV.

    Parâmetros:
      df            — DataFrame já com features, incluindo 'year' e 'code'.
      feature_cols  — lista de colunas X.
      target_col    — nome da coluna alvo.
      save_path     — se fornecido, salva o modelo .joblib.
      clip_percentile — corte por cidade no alvo de treino (None = sem corte).
      horizonte     — h usado nas features; define a coluna do baseline de persistência.
      max_test_year — último ano usado como fold de validação.

    Retorna:
      model   — modelo treinado no dataset completo.
      metrics — lista de dicts (um por fold Expanding Window).
      fi      — lista de tuplas (feature, importância), ordenada desc.
      oof     — (só se return_oof=True) DataFrame code/year/month/y_true/y_pred.
    """
    X = df[feature_cols]
    y_raw = df[target_col]
    years = df["year"]

    # Hiperparâmetros fixos (protocolo: sem grid search — com ~10 anos de informação
    # interanual, otimizar hiperparâmetros só aumenta o sobreajuste à validação).
    best_params = dict(XGB_PARAMS)

    # ---------- Expanding Window CV ----------
    metrics = []
    oof_parts = []
    persist_col = _persist_col(target_col, horizonte)
    if persist_col not in df.columns:
        persist_col = None
    logger.info(f"Iniciando Validação Temporal (Expanding Window)... persist_col={persist_col}")

    for train_mask, test_mask, test_year in _expanding_window_splits(years, 3, max_test_year):
        df_tr, df_te = df[train_mask], df[test_mask]
        _, preds = fit_predict_fold(
            df_tr, df_te, feature_cols, target_col,
            clip_percentile=clip_percentile, params=best_params, use_pop_offset=use_pop_offset,
        )
        y_test = y_raw[test_mask].to_numpy(dtype=float)  # avalia no valor REAL (sem corte)

        if return_oof:
            oof_parts.append(pd.DataFrame({
                "code": df_te["code"].values,
                "year": df_te["year"].values,
                "month": df_te["month"].values,
                "y_true": y_test,
                "y_pred": preds,
            }))

        r2 = r2_score(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        mape = _safe_mape(y_test, preds)

        r2_persist = mae_persist = None
        if persist_col:
            base = df_te[persist_col].fillna(0).values
            r2_persist = round(r2_score(y_test, base), 4)
            mae_persist = round(mean_absolute_error(y_test, base), 2)

        metrics.append({
            "year": int(test_year),
            "r2": round(r2, 4),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape": round(mape, 2) if not np.isnan(mape) else None,
            "r2_persistencia": r2_persist,
            "mae_persistencia": mae_persist,
            "n_train": int(train_mask.sum()),
            "n_test": int(test_mask.sum()),
        })
        logger.info(
            f"  EW {test_year}: R²={r2:.3f} | MAE={mae:.1f} | RMSE={rmse:.1f} | MAPE={mape:.1f}% "
            f"| persistência R²={r2_persist} MAE={mae_persist}"
        )

    if metrics:
        logger.info(
            f"EW Médio — R²: {np.mean([m['r2'] for m in metrics]):.3f} | "
            f"MAE: {np.mean([m['mae'] for m in metrics]):.1f}"
        )

    # ---------- Treino Final (dataset completo) ----------
    logger.info("Treinando modelo final no dataset completo...")
    fit_kw_final = {"base_margin": _build_base_margin(df)} if use_pop_offset else {}
    final_model = xgb.XGBRegressor(**best_params)
    final_model.fit(X, alvo_treino(df, target_col, clip_percentile), **fit_kw_final)

    fi = sorted(zip(feature_cols, final_model.feature_importances_), key=lambda t: t[1], reverse=True)

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(final_model, save_path)
        logger.info(f"Modelo salvo em {save_path}")

    if return_oof:
        oof = pd.concat(oof_parts, ignore_index=True) if oof_parts else pd.DataFrame()
        return final_model, metrics, fi, oof
    return final_model, metrics, fi
