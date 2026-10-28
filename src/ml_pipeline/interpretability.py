"""
Módulo de interpretabilidade do modelo XGBoost (v4 multi-doença).

Fornece:
  - SHAP nativo via pred_contribs do XGBoost (sem dependência extra).
  - Feature importance por ganho (já no modelo).
  - Curvas de dependência parcial para as top-N features.
  - Exportação de gráficos em PNG via Plotly.
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import xgboost as xgb

logger = logging.getLogger(__name__)


def compute_shap_values(
    model: xgb.XGBRegressor,
    X: pd.DataFrame,
    base_margin: Optional[np.ndarray] = None,
) -> pd.DataFrame:
    """
    Calcula SHAP values nativos do XGBoost via pred_contribs.

    Retorna DataFrame com as mesmas colunas de X + coluna 'bias' (intercept).
    Cada valor indica a contribuição da feature para mover a predição acima/abaixo
    do valor esperado.

    Args:
        model: modelo XGBoost treinado.
        X: DataFrame com as features (mesmas do treino).
        base_margin: offset de população, se usado no treino.

    Returns:
        DataFrame (n_samples × n_features + 1) com SHAP values.
    """
    booster = model.get_booster()
    dmatrix = xgb.DMatrix(X, feature_names=list(X.columns))
    if base_margin is not None:
        dmatrix.set_base_margin(base_margin)

    # pred_contribs retorna (n_samples, n_features + 1), última coluna = bias
    contribs = booster.predict(dmatrix, pred_contribs=True)

    cols = list(X.columns) + ["bias"]
    shap_df = pd.DataFrame(contribs, columns=cols, index=X.index)

    logger.info(
        f"SHAP values calculados: {shap_df.shape[0]} amostras × {shap_df.shape[1] - 1} features"
    )
    return shap_df


def shap_summary(shap_df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """
    Resumo de importância SHAP: média absoluta por feature, ordenada desc.

    Retorna DataFrame com colunas: feature, mean_abs_shap, std_shap.
    """
    # Excluir bias
    features = [c for c in shap_df.columns if c != "bias"]
    summary = pd.DataFrame({
        "feature": features,
        "mean_abs_shap": [shap_df[f].abs().mean() for f in features],
        "std_shap": [shap_df[f].std() for f in features],
    }).sort_values("mean_abs_shap", ascending=False).head(top_n).reset_index(drop=True)

    return summary


def plot_shap_importance(
    shap_df: pd.DataFrame,
    top_n: int = 15,
    save_path: Optional[Path] = None,
    title: str = "Importância SHAP (média |SHAP|)",
) -> None:
    """
    Gráfico de barras horizontais da importância SHAP (top_n features).
    Usa Plotly com template plotly_white.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        logger.warning("Plotly não disponível. Pulando gráfico SHAP.")
        return

    summary = shap_summary(shap_df, top_n=top_n)
    summary = summary.iloc[::-1]  # inverter para barras de baixo para cima

    fig = go.Figure(go.Bar(
        x=summary["mean_abs_shap"],
        y=summary["feature"],
        orientation="h",
        marker_color="rgba(55, 128, 191, 0.8)",
        error_x=dict(type="data", array=summary["std_shap"].values, visible=True),
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Média |SHAP value|",
        yaxis_title="",
        template="plotly_white",
        height=max(400, top_n * 28),
        margin=dict(l=180, r=40, t=60, b=40),
    )

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fig.write_image(str(save_path), scale=2)
            logger.info(f"Gráfico SHAP salvo em {save_path}")
        except Exception as e:
            logger.warning(f"Falha ao exportar PNG: {e}. Salvando HTML.")
            fig.write_html(str(save_path.with_suffix(".html")))

    return fig


def plot_partial_dependence(
    model: xgb.XGBRegressor,
    X: pd.DataFrame,
    feature: str,
    n_points: int = 50,
    save_path: Optional[Path] = None,
    base_margin: Optional[np.ndarray] = None,
    title: Optional[str] = None,
) -> None:
    """
    Curva de dependência parcial (PDP) para uma feature.

    Fixa todas as outras features nos valores observados e varia 'feature'
    sobre sua faixa, calculando a predição média.

    Args:
        model: modelo XGBoost treinado.
        X: DataFrame com features.
        feature: nome da feature para variar.
        n_points: resolução da curva.
        save_path: caminho para salvar PNG.
        base_margin: offset, se usado.
        title: título do gráfico.
    """
    try:
        import plotly.graph_objects as go
    except ImportError:
        logger.warning("Plotly não disponível. Pulando PDP.")
        return

    if feature not in X.columns:
        logger.warning(f"Feature '{feature}' ausente do DataFrame.")
        return

    # Grid entre P1 e P99 (extremos têm pouquíssimos dados e distorcem a curva)
    lo, hi = np.nanpercentile(X[feature].values.astype(float), [1, 99])
    feat_values = np.linspace(lo, hi, n_points)
    avg_preds = []

    # Subsample para performance (max 2000 linhas), por POSIÇÃO
    rng = np.random.default_rng(42)
    pos = rng.choice(len(X), size=min(2000, len(X)), replace=False)
    X_sub = X.iloc[pos]
    bm = np.asarray(base_margin)[pos] if base_margin is not None else None

    for val in feat_values:
        X_mod = X_sub.copy()
        X_mod[feature] = val
        preds = model.predict(X_mod, base_margin=bm) if bm is not None else model.predict(X_mod)
        avg_preds.append(np.mean(np.maximum(preds, 0)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=feat_values,
        y=avg_preds,
        mode="lines",
        line=dict(color="rgba(219, 64, 82, 0.9)", width=3),
        name="PDP",
    ))

    # Rug plot: distribuição dos valores reais
    fig.add_trace(go.Scatter(
        x=X_sub[feature].values,
        y=[min(avg_preds)] * len(X_sub),
        mode="markers",
        marker=dict(color="gray", size=3, symbol="line-ns-open"),
        name="Dados",
        showlegend=False,
    ))

    fig.update_layout(
        title=title or f"Dependência Parcial: {feature}",
        xaxis_title=feature,
        yaxis_title="Predição média (casos)",
        template="plotly_white",
        height=400,
        margin=dict(l=60, r=40, t=60, b=50),
    )

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fig.write_image(str(save_path), scale=2)
            logger.info(f"PDP salvo em {save_path}")
        except Exception as e:
            logger.warning(f"Falha ao exportar PNG: {e}. Salvando HTML.")
            fig.write_html(str(save_path.with_suffix(".html")))

    return fig


def plot_top_pdps(
    model: xgb.XGBRegressor,
    X: pd.DataFrame,
    shap_df: pd.DataFrame,
    top_n: int = 6,
    output_dir: Optional[Path] = None,
    base_margin: Optional[np.ndarray] = None,
    doenca: str = "dengue",
) -> list:
    """
    Gera PDPs para as top_n features mais importantes (por SHAP).

    Args:
        model: modelo treinado.
        X: DataFrame de features.
        shap_df: SHAP values (saída de compute_shap_values).
        top_n: quantas features.
        output_dir: diretório para salvar PNGs.
        base_margin: offset, se usado.
        doenca: nome da doença (para nomes de arquivos).

    Returns:
        Lista de figuras Plotly.
    """
    summary = shap_summary(shap_df, top_n=top_n)
    figs = []

    for _, row in summary.iterrows():
        feat = row["feature"]
        save_path = output_dir / f"pdp_{doenca}_{feat}.png" if output_dir else None
        fig = plot_partial_dependence(
            model, X, feat,
            save_path=save_path,
            base_margin=base_margin,
            title=f"PDP — {feat} ({doenca})",
        )
        if fig is not None:
            figs.append(fig)

    logger.info(f"Gerados {len(figs)} PDPs para {doenca}")
    return figs


def run_interpretability(
    model: xgb.XGBRegressor,
    df: pd.DataFrame,
    feature_cols: list[str],
    output_dir: Path,
    doenca: str = "dengue",
    base_margin: Optional[np.ndarray] = None,
    top_n_shap: int = 15,
    top_n_pdp: int = 6,
) -> dict:
    """
    Executa a pipeline completa de interpretabilidade.

    1. Calcula SHAP values.
    2. Gera gráfico de importância SHAP.
    3. Gera PDPs para as top features.
    4. Retorna resumo para o relatório.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    X = df[feature_cols]

    # 1. SHAP
    shap_df = compute_shap_values(model, X, base_margin=base_margin)
    summary = shap_summary(shap_df, top_n=top_n_shap)

    # 2. Gráfico SHAP
    shap_fig = plot_shap_importance(
        shap_df,
        top_n=top_n_shap,
        save_path=output_dir / f"shap_importance_{doenca}.png",
        title=f"Importância SHAP — {doenca.capitalize()}",
    )

    # 3. PDPs
    pdp_figs = plot_top_pdps(
        model, X, shap_df,
        top_n=top_n_pdp,
        output_dir=output_dir,
        base_margin=base_margin,
        doenca=doenca,
    )

    # 4. Relatório
    report = {
        "doenca": doenca,
        "n_samples": len(X),
        "n_features": len(feature_cols),
        "top_shap_features": summary.to_dict(orient="records"),
    }

    logger.info(f"Interpretabilidade concluída para {doenca}. Top SHAP: {summary['feature'].tolist()[:5]}")
    return report
