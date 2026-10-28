"""
Módulo de treinamento do motor de ML v4 (multi-doença).
Isola o algoritmo, validação temporal e tunagem de hiperparâmetros.

v4 — Mudanças:
  - Clipping: agora é POR CIDADE (não global), com P99.
  - Validação: Expanding Window temporal (treina em ≤ano_t, testa em ano_t+1).
  - Baseline de persistência detectado pelo prefixo da doença-alvo.
  - Suporte a offset de população (base_margin) para Poisson / Tweedie.
"""
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

logger = logging.getLogger(__name__)

# Mapa de doença → prefixo (consistente com feature_engineering)
_PREFIXOS = {
    "dengue_cases": "dengue",
    "chik_cases": "chik",
    "zika_cases": "zika",
}


def clip_outliers_per_city(df: pd.DataFrame, col: str = "dengue_cases", percentile: float = 99.0) -> pd.Series:
    """
    Aplica clipping P99 **por cidade** em vez de globalmente,
    para que cidades de alta endemia (ex: Porto Alegre) não tenham
    seus surtos legítimos cortados.
    """
    return df.groupby("code")[col].transform(
        lambda s: s.clip(upper=s.quantile(percentile / 100.0))
    )


def _safe_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true > 1.0
    if not np.any(mask):
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100.0)


def _expanding_window_splits(years: pd.Series, min_train_years: int = 3):
    """
    Gera splits Expanding Window (Walk Forward):
      Treina em anos ≤ t, testa em ano t+1.
      Garante min_train_years anos no treino.

    Yields: (train_mask, test_mask, ano_teste)
    """
    sorted_years = sorted(years.unique())
    for i, test_year in enumerate(sorted_years):
        if i < min_train_years:
            continue
        train_mask = years < test_year
        test_mask = years == test_year
        yield train_mask, test_mask, test_year


def _detect_persist_col(df: pd.DataFrame, target_col: str) -> str | None:
    """Encontra a coluna de lag1 da doença-alvo para o baseline de persistência."""
    prefix = _PREFIXOS.get(target_col)
    if prefix is None:
        return None
    for c in df.columns:
        m = re.fullmatch(rf"{prefix}_lag(\d+)", c)
        if m and int(m.group(1)) == 1:
            return c
    return None


def _build_base_margin(df: pd.DataFrame) -> np.ndarray | None:
    """Offset = log(pop / 100.000) para modelar incidência, não contagem bruta."""
    if "populacao" not in df.columns:
        return None
    pop = df["populacao"].fillna(1).clip(lower=1).values
    return np.log(pop / 100_000.0)


def train_model(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "dengue_cases",
    tune_hyperparams: bool = False,
    save_path: Path | None = None,
    clip_percentile: float | None = None,
    use_pop_offset: bool = False,
    return_oof: bool = False,
):
    """
    Treina o modelo XGBoost Poisson com Expanding Window CV.

    Parâmetros:
      df            — DataFrame já com features, incluindo 'year' e 'code'.
      feature_cols  — lista de colunas X.
      target_col    — nome da coluna alvo.
      tune_hyperparams — se True, faz RandomizedSearchCV.
      save_path     — se fornecido, salva o modelo .joblib.

    Retorna:
      model   — modelo treinado no dataset completo.
      metrics — lista de dicts (um por fold Expanding Window).
      fi      — lista de tuplas (feature, importância), ordenada desc.
      oof     — (só se return_oof=True) DataFrame code/year/month/y_true/y_pred
                com as predições fora-da-amostra de cada fold.
    """
    X = df[feature_cols].copy()
    y_raw = df[target_col].copy()
    years = df["year"].copy()

    # Clipping por cidade (None = sem clipping)
    if clip_percentile is not None:
        y_clipped = clip_outliers_per_city(df, target_col, clip_percentile).values
    else:
        y_clipped = y_raw.values.astype(float)

    # ---------- Hiperparâmetros ----------
    if tune_hyperparams:
        logger.info("Tuning hyperparams com RandomizedSearchCV...")
        from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

        base = xgb.XGBRegressor(
            objective="count:poisson",
            eval_metric="poisson-nloglik",
            random_state=42,
        )
        param_grid = {
            "max_depth": [3, 4, 5, 6, 7],
            "learning_rate": [0.01, 0.03, 0.05, 0.1],
            "n_estimators": [100, 200, 300, 500],
            "subsample": [0.7, 0.8, 0.9],
            "colsample_bytree": [0.6, 0.7, 0.8, 0.9],
            "min_child_weight": [3, 5, 10, 20],
            "reg_alpha": [0, 0.1, 1.0],
            "reg_lambda": [1, 5, 10],
        }
        tscv = TimeSeriesSplit(n_splits=4)
        search = RandomizedSearchCV(
            base, param_grid,
            n_iter=30,
            cv=tscv,
            scoring="neg_mean_absolute_error",
            random_state=42,
            n_jobs=-1,
        )
        search.fit(X, y_clipped)
        best_params = search.best_estimator_.get_params()
        logger.info(f"Best Params: {search.best_params_}")
    else:
        best_params = dict(
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
        )

    # ---------- Offset de população ----------
    base_margin_all = _build_base_margin(df) if use_pop_offset else None

    # ---------- Expanding Window CV ----------
    metrics = []
    oof_parts = []
    persist_col = _detect_persist_col(df, target_col)
    logger.info(f"Iniciando Validação Temporal (Expanding Window)... persist_col={persist_col}")

    for train_mask, test_mask, test_year in _expanding_window_splits(years, min_train_years=3):
        X_train, y_train = X[train_mask], y_clipped[train_mask]
        X_test = X[test_mask]
        y_test = y_raw[test_mask].values  # avalia no valor REAL (sem clip)

        fit_kw = {}
        pred_kw = {}
        if base_margin_all is not None:
            fit_kw["base_margin"] = base_margin_all[train_mask]
            pred_kw["base_margin"] = base_margin_all[test_mask]

        model_fold = xgb.XGBRegressor(**best_params)
        model_fold.fit(X_train, y_train, **fit_kw)

        preds = model_fold.predict(X_test, **pred_kw)
        preds = np.maximum(preds, 0)

        if return_oof:
            oof_parts.append(pd.DataFrame({
                "code": df.loc[test_mask, "code"].values,
                "year": df.loc[test_mask, "year"].values,
                "month": df.loc[test_mask, "month"].values,
                "y_true": y_test,
                "y_pred": preds,
            }))

        r2 = r2_score(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        mape = _safe_mape(y_test, preds)

        # Baseline de persistência: prever que o mês seguinte repete o anterior
        r2_persist = mae_persist = None
        if persist_col and persist_col in df.columns:
            base = df.loc[test_mask, persist_col].fillna(0).values
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
        avg_r2 = np.mean([m["r2"] for m in metrics])
        avg_mae = np.mean([m["mae"] for m in metrics])
        logger.info(f"EW Médio — R²: {avg_r2:.3f} | MAE: {avg_mae:.1f}")

    # ---------- Treino Final (dataset completo) ----------
    logger.info("Treinando modelo final no dataset completo...")
    final_model = xgb.XGBRegressor(**best_params)
    fit_kw_final = {}
    if base_margin_all is not None:
        fit_kw_final["base_margin"] = base_margin_all
    final_model.fit(X, y_clipped, **fit_kw_final)

    # Feature Importance
    fi = sorted(
        zip(feature_cols, final_model.feature_importances_),
        key=lambda t: t[1], reverse=True,
    )

    # Salvar
    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(final_model, save_path)
        logger.info(f"Modelo salvo em {save_path}")

    if return_oof:
        oof = pd.concat(oof_parts, ignore_index=True) if oof_parts else pd.DataFrame()
        return final_model, metrics, fi, oof
    return final_model, metrics, fi
