"""
ml_runner.py — Wrapper leve do motor ML para a interface Prodígia.
Encapsula build_base_panel() e run_full_ml(), emitindo progresso via callback.
"""
import sqlite3
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Callable, Optional

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "processed" / "dengue_analytics.db"
ML_OUTPUT = ROOT_DIR / "output" / "projecoes_regionais" / "ml_completo"

FEATURE_COLS = [
    "temp_media", "precipitacao", "enso", "latitude", "month_sin", "month_cos",
    "dengue_lag1", "dengue_lag2", "dengue_lag3", "temp_lag1", "prec_lag1", "enso_lag1",
]


def get_db_status() -> dict:
    """Retorna estatísticas do banco para o painel de status."""
    conn = sqlite3.connect(DB_PATH)
    try:
        saude = pd.read_sql_query(
            "SELECT COUNT(*) as n, COUNT(DISTINCT CODIGO_MUNICIPIO) as cidades, "
            "MIN(ANO) as ano_min, MAX(ANO) as ano_max FROM ingestao_saude", conn
        ).iloc[0]
        clima = pd.read_sql_query(
            "SELECT COUNT(*) as n, COUNT(DISTINCT CODIGO_MUNICIPIO) as cidades FROM ingestao_clima", conn
        ).iloc[0]
    finally:
        conn.close()

    return {
        "saude_registros": int(saude["n"]),
        "saude_cidades": int(saude["cidades"]),
        "clima_registros": int(clima["n"]),
        "clima_cidades": int(clima["cidades"]),
        "periodo": f"{int(saude['ano_min'])}–{int(saude['ano_max'])}",
        "db_size_mb": round(DB_PATH.stat().st_size / (1024 * 1024), 1),
    }


def get_cidades() -> list[dict]:
    """Lista cidades disponíveis no SQLite para o filtro avançado."""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT DISTINCT s.CODIGO_MUNICIPIO as code, s.NOME_MUNICIPIO as nome "
            "FROM ingestao_saude s ORDER BY s.NOME_MUNICIPIO", conn
        )
    finally:
        conn.close()
    return df.to_dict(orient="records")


def treinar(
    modo: str = "rapido",
    codigo_ibge: Optional[str] = None,
    on_progress: Optional[Callable[[str, int], None]] = None,
) -> dict:
    """Executa treino XGBoost e retorna métricas + dados para gráficos.

    Parameters
    ----------
    modo : str
        "rapido" (São Carlos), "regional", "completo"
    codigo_ibge : str, optional
        Código IBGE específico (modo avançado)
    on_progress : callable, optional
        Callback(mensagem, percentual) para SSE
    """
    import sys
    sys.path.insert(0, str(ROOT_DIR))

    def emit(msg: str, pct: int):
        if on_progress:
            on_progress(msg, pct)

    emit("Carregando dados do SQLite...", 5)

    from src.processamento.motor_lote_modelagem_v2_por_latitude import (
        build_base_panel, _build_ml_features, _evaluate_split, _safe_mape,
    )
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    panel, lookup = build_base_panel(ROOT_DIR)
    emit(f"Painel carregado: {len(panel)} registros", 15)

    # Aplicar filtro de escopo
    if codigo_ibge:
        panel = panel[panel["code"] == str(codigo_ibge)].copy()
    elif modo == "rapido":
        panel = panel[panel["code"] == "421600"].copy()
    # "regional" e "completo" usam o painel inteiro por enquanto

    n_cidades = panel["code"].nunique()
    emit(f"Escopo: {n_cidades} cidade(s) selecionada(s)", 20)

    if panel.empty:
        raise ValueError("Nenhum dado encontrado para o escopo selecionado.")

    # Build features
    emit("Construindo features (lags, sazonalidade)...", 30)
    feat = _build_ml_features(panel)

    train_df = feat[feat["year"] <= 2021].copy()
    val_df = feat[feat["year"] == 2022].copy()
    test_df = feat[(feat["year"] >= 2023) & (feat["year"] <= 2024)].copy()

    emit("Treinando XGBoost (HistGradientBoosting)...", 45)

    model = HistGradientBoostingRegressor(
        loss="squared_error", learning_rate=0.05, max_depth=6,
        max_iter=500, min_samples_leaf=max(10, len(train_df) // 20),
        l2_regularization=0.1, random_state=42,
    )
    y_train_log = np.log1p(train_df["dengue_cases"].to_numpy(dtype=float))
    model.fit(train_df[FEATURE_COLS].to_numpy(dtype=float), y_train_log)

    emit("Avaliando modelo (validação + teste)...", 65)

    val_pred = np.expm1(model.predict(val_df[FEATURE_COLS].to_numpy(dtype=float))).clip(min=0)
    test_pred = np.expm1(model.predict(test_df[FEATURE_COLS].to_numpy(dtype=float))).clip(min=0)

    met_val = _evaluate_split(val_df["dengue_cases"].to_numpy(dtype=float), val_pred, "valid_2022")
    met_test = _evaluate_split(test_df["dengue_cases"].to_numpy(dtype=float), test_pred, "test_2023_2024")

    # Executa o pipeline completo do motor para gerar as projeções oficiais corretamente
    emit("Rodando motor oficial para predições precisas (usando cenários climáticos)...", 75)
    from src.processamento.motor_lote_modelagem_v2_por_latitude import run_full_ml
    run_full_ml(ROOT_DIR, panel)

    # Re-treino apenas para calcular Feature Importance
    emit("Calculando importância das variáveis...", 85)
    full_model = HistGradientBoostingRegressor(
        loss="squared_error", learning_rate=0.05, max_depth=6,
        max_iter=300, min_samples_leaf=max(10, len(feat) // 20),
        l2_regularization=0.1, random_state=42,
    )
    full_model.fit(feat[FEATURE_COLS].to_numpy(dtype=float), np.log1p(feat["dengue_cases"].to_numpy(dtype=float)))
    
    try:
        from sklearn.inspection import permutation_importance
        result = permutation_importance(
            full_model, feat[FEATURE_COLS].to_numpy(dtype=float), np.log1p(feat["dengue_cases"].to_numpy(dtype=float)),
            n_repeats=3, random_state=42, n_jobs=-1
        )
        importances = result.importances_mean
        fi = sorted(zip(FEATURE_COLS, importances.tolist()), key=lambda x: x[1], reverse=True)
    except Exception as e:
        print("Erro no permutation_importance:", e)
        fi = [(f, 0.0) for f in FEATURE_COLS]

    emit("Montando dados para gráficos...", 90)
    
    # Lendo projeções oficiais geradas pelo motor
    try:
        df_test = pd.read_csv(ML_OUTPUT / "backtest_ml_completo.csv")
        df_test_anual = df_test.groupby('year')['pred_cases_ml'].sum().reset_index()
    except Exception:
        df_test_anual = pd.DataFrame(columns=['year', 'pred_cases_ml'])

    try:
        df_proj = pd.read_csv(ML_OUTPUT / "projecao_ml_completa_municipios_anual.csv")
        # Filtra pelo escopo atual e cenário ssp245
        df_2025 = df_proj[(df_proj["year"] == 2025) & (df_proj["scenario"] == "ssp245")]
        if codigo_ibge:
            df_2025 = df_2025[df_2025["code"] == int(codigo_ibge)]
        elif modo == "rapido":
            df_2025 = df_2025[df_2025["code"] == 421600]
        pred_2025 = float(df_2025["pred_cases_ml"].sum())
    except Exception:
        pred_2025 = 0.0

    chart_data = pd.concat([df_test_anual.rename(columns={"pred_cases_ml": "pred"}), pd.DataFrame({"year": [2025], "pred": [pred_2025]})])

    # Histórico real anual completo
    conn = sqlite3.connect(DB_PATH)
    codes = panel["code"].unique().tolist()
    placeholders = ",".join(["?"] * len(codes))
    hist = pd.read_sql_query(
        f"SELECT ANO as year, SUM(CASOS_DENGUE) as real FROM ingestao_saude "
        f"WHERE CODIGO_MUNICIPIO IN ({placeholders}) GROUP BY ANO ORDER BY ANO",
        conn, params=codes
    )
    conn.close()
    
    # Merge com dados reais
    merged = pd.merge(hist, chart_data, on="year", how="outer").sort_values("year")
    
    emit("Concluído!", 100)

    # Cálculo das métricas de negócio para 2025
    try:
        real_2025 = hist[hist["year"] == 2025]["real"].sum() if 2025 in hist["year"].values else 0
        real_2024 = hist[hist["year"] == 2024]["real"].sum() if 2024 in hist["year"].values else 0
        
        erro_abs = abs(round(pred_2025) - real_2025)
        
        tendencia_real = "Queda" if real_2025 < real_2024 else "Alta"
        tendencia_pred = "Queda" if pred_2025 < real_2024 else "Alta"
        acertou_tendencia = f"Acertou ({tendencia_pred})" if tendencia_real == tendencia_pred else "Errou Tendência"
        
        if pred_2025 < 300:
            risco = "Baixo"
        elif pred_2025 < 1000:
            risco = "Médio"
        else:
            risco = "Alto"
    except:
        erro_abs = 0
        acertou_tendencia = "Calculando..."
        risco = "Indeterminado"

    return {
        "metricas": {
            "erro_abs": int(erro_abs),
            "tendencia": acertou_tendencia,
            "risco": risco,
        },
        "feature_importance": [{"feature": f, "importance": round(v, 4)} for f, v in fi],
        "grafico_barras": {
            "anos": merged["year"].tolist(),
            "real": [None if pd.isna(x) else float(x) for x in merged["real"]],
            "previsto": [None if pd.isna(x) else round(x) for x in merged["pred"]],
        },
        "n_cidades": n_cidades,
        "n_registros": len(panel),
    }
