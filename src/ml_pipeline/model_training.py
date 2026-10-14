"""
Módulo de treinamento do motor de ML v3.
Isola o algoritmo, validação temporal e tunagem de hiperparâmetros.

v3 — Corrige:
  - Clipping: agora é POR CIDADE (não global), com P99.
  - Validação: Expanding Window temporal (treina em ≤ano_t, testa em ano_t+1).
  - Log: usa logging em vez de print.
  - Retorna métricas detalhadas por fold.
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

logger = logging.getLogger(__name__)


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


def train_model(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "dengue_cases",
    tune_hyperparams: bool = False,
    save_path: Path | None = None,
    clip_percentile: float | None = 99.0,
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

    # ---------- Expanding Window CV ----------
    metrics = []
    logger.info("Iniciando Validação Temporal (Expanding Window)...")

    for train_mask, test_mask, test_year in _expanding_window_splits(years, min_train_years=3):
        X_train, y_train = X[train_mask], y_clipped[train_mask]
        X_test = X[test_mask]
        y_test = y_raw[test_mask].values  # avalia no valor REAL (sem clip)

        model_fold = xgb.XGBRegressor(**best_params)
        model_fold.fit(X_train, y_train)

        preds = model_fold.predict(X_test)
        preds = np.maximum(preds, 0)

        r2 = r2_score(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        rmse = np.sqrt(mean_squared_error(y_test, preds))
        mape = _safe_mape(y_test, preds)

        metrics.append({
            "year": int(test_year),
            "r2": round(r2, 4),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape": round(mape, 2) if not np.isnan(mape) else None,
            "n_train": int(train_mask.sum()),
            "n_test": int(test_mask.sum()),
        })
        logger.info(
            f"  EW {test_year}: R²={r2:.3f} | MAE={mae:.1f} | RMSE={rmse:.1f} | MAPE={mape:.1f}% "
            f"(treino={train_mask.sum()}, teste={test_mask.sum()})"
        )

    if metrics:
        avg_r2 = np.mean([m["r2"] for m in metrics])
        avg_mae = np.mean([m["mae"] for m in metrics])
        logger.info(f"EW Médio — R²: {avg_r2:.3f} | MAE: {avg_mae:.1f}")

    # ---------- Treino Final (dataset completo) ----------
    logger.info("Treinando modelo final no dataset completo...")
    final_model = xgb.XGBRegressor(**best_params)
    final_model.fit(X, y_clipped)

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

    return final_model, metrics, fi
