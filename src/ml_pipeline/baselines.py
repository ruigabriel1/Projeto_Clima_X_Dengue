"""
Modelos de baseline para comparação com o XGBoost.
Todos usam a mesma interface: fit(X_train, y_train) + predict(X_test) → np.array.

Baselines implementados:
  - Persistência (t-1): y_hat = dengue_lag1
  - Naive sazonal: y_hat = dengue_lag12 (mesmo mês do ano anterior)
  - GLM Binomial Negativa: statsmodels com clima + sazonalidade + offset log(pop)
"""
import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class PersistenciaBaseline:
    """Prever = valor do mês anterior (dengue_lag1)."""

    def __init__(self, lag_col: str = "dengue_lag1"):
        self.lag_col = lag_col

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return df[self.lag_col].fillna(0).values.astype(float)


class NaiveSazonalBaseline:
    """Prever = mesmo mês do ano anterior (dengue_lag12)."""

    def __init__(self, lag_col: str = "dengue_lag12"):
        self.lag_col = lag_col

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        return df[self.lag_col].fillna(0).values.astype(float)


class GLMBinomialNegativa:
    """
    GLM Binomial Negativa com offset log(população).
    Usa variáveis climáticas + sazonalidade (sem lags de casos).
    Boa como baseline estatística clássica para o artigo.
    """

    def __init__(self):
        self.model = None
        self.feature_cols = None

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Seleciona features do Modelo B (sem lags de dengue)."""
        candidatas = [
            "month_sin", "month_cos", "is_outbreak_season",
            "temp_lag1", "temp_lag2",
            "prec_lag1", "prec_lag2",
            "umid_lag1",
            "enso_lag1", "enso_lag2",
            "amplitude_lag1",
            "graus_dia_18_lag1",
            "prec_acum_3m",
            "temp_anomalia_lag1",
            "prec_anomalia_lag1",
            "abs_latitude",
            "log_pop",
        ]
        return [c for c in candidatas if c in df.columns]

    def fit(self, df_train: pd.DataFrame, target_col: str = "dengue_cases"):
        """Ajusta o GLM NB com offset log(pop)."""
        import statsmodels.api as sm

        self.feature_cols = self._prepare_features(df_train)
        X = df_train[self.feature_cols].copy()
        X = sm.add_constant(X)
        y = df_train[target_col].values

        # Offset: log(população / 100.000), para modelar incidência
        if "populacao" in df_train.columns:
            offset = np.log(df_train["populacao"].clip(lower=1).values / 100_000)
        else:
            offset = np.zeros(len(y))

        try:
            self.model = sm.GLM(
                y, X, family=sm.families.NegativeBinomial(alpha=1.0), offset=offset
            ).fit(maxiter=100, method="irls")
            logger.info(f"GLM NB ajustado. AIC={self.model.aic:.0f}, deviance={self.model.deviance:.0f}")
        except Exception as e:
            logger.warning(f"GLM NB falhou: {e}. Usando fallback (média global).")
            self.model = None
            self._fallback_mean = float(np.mean(y))

        return self

    def predict(self, df_test: pd.DataFrame) -> np.ndarray:
        """Prediz casos a partir do GLM ajustado."""
        import statsmodels.api as sm

        if self.model is None:
            return np.full(len(df_test), self._fallback_mean)

        X = df_test[self.feature_cols].copy()
        X = sm.add_constant(X)

        if "populacao" in df_test.columns:
            offset = np.log(df_test["populacao"].clip(lower=1).values / 100_000)
        else:
            offset = np.zeros(len(df_test))

        preds = self.model.predict(X, offset=offset)
        return np.maximum(preds, 0)


def evaluate_baselines(
    df: pd.DataFrame,
    target_col: str = "dengue_cases",
) -> list[dict]:
    """
    Avalia persistência, naive sazonal e GLM NB com Expanding Window.
    Retorna lista de dicts com métricas por fold.
    """
    from sklearn.metrics import mean_absolute_error, r2_score

    from src.ml_pipeline.model_training import _expanding_window_splits

    years = df["year"]
    results = []

    for train_mask, test_mask, test_year in _expanding_window_splits(years, min_train_years=3):
        df_train = df[train_mask]
        df_test = df[test_mask]
        y_test = df_test[target_col].values

        fold_result = {"year": int(test_year), "n_test": int(test_mask.sum())}

        # Persistência
        persist = PersistenciaBaseline()
        p_pred = persist.predict(df_test)
        fold_result["persist_r2"] = round(r2_score(y_test, p_pred), 4)
        fold_result["persist_mae"] = round(mean_absolute_error(y_test, p_pred), 2)

        # Naive sazonal
        if "dengue_lag12" in df.columns:
            sazonal = NaiveSazonalBaseline()
            s_pred = sazonal.predict(df_test)
            fold_result["sazonal_r2"] = round(r2_score(y_test, s_pred), 4)
            fold_result["sazonal_mae"] = round(mean_absolute_error(y_test, s_pred), 2)

        # GLM NB
        try:
            glm = GLMBinomialNegativa()
            glm.fit(df_train, target_col)
            g_pred = glm.predict(df_test)
            fold_result["glm_nb_r2"] = round(r2_score(y_test, g_pred), 4)
            fold_result["glm_nb_mae"] = round(mean_absolute_error(y_test, g_pred), 2)
        except Exception as e:
            logger.warning(f"GLM NB falhou no fold {test_year}: {e}")

        results.append(fold_result)
        logger.info(f"  Baselines {test_year}: {fold_result}")

    return results
