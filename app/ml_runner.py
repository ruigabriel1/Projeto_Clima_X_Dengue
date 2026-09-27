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

    panel, lookup = build_base_panel(ROOT_DIR, modo=modo)
    emit(f"Painel carregado: {len(panel)} registros", 15)

    # Aplicar filtro avançado se código IBGE específico for solicitado
    if codigo_ibge:
        panel = panel[panel["code"] == str(codigo_ibge)].copy()

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

    # ═══════════════════════════════════════════════════════════
    # NOVOS DADOS: Tabela Epidemiológica
    # ═══════════════════════════════════════════════════════════
    MESES_PT = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
                7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}

    # Histórico mensal para tabela e séries
    hist_mensal = pd.read_sql_query(
        f"SELECT ANO as year, MES as month, SUM(CASOS_DENGUE) as casos "
        f"FROM ingestao_saude WHERE CODIGO_MUNICIPIO IN ({placeholders}) "
        f"GROUP BY ANO, MES ORDER BY ANO, MES",
        conn, params=codes
    )

    # População (tabela ingestao_populacao)
    try:
        pop_df = pd.read_sql_query(
            f"SELECT ANO as year, SUM(POPULACAO) as pop FROM ingestao_populacao "
            f"WHERE CODIGO_MUNICIPIO IN ({placeholders}) GROUP BY ANO",
            conn, params=codes
        )
    except Exception:
        pop_df = pd.DataFrame(columns=["year", "pop"])

    # Clima mensal para gráfico
    try:
        clima_mensal = pd.read_sql_query(
            f"SELECT ANO as year, MES as month, AVG(temp_media) as temp_media, "
            f"SUM(precipitacao) as precipitacao FROM ingestao_clima "
            f"WHERE CODIGO_MUNICIPIO IN ({placeholders}) "
            f"GROUP BY ANO, MES ORDER BY ANO, MES",
            conn, params=codes
        )
    except Exception:
        clima_mensal = pd.DataFrame()

    conn.close()

    # --- Tabela epidemiológica ---
    tabela_epidem = []
    if not hist_mensal.empty:
        for ano in sorted(hist_mensal["year"].unique()):
            dados_ano = hist_mensal[hist_mensal["year"] == ano]
            casos_total = int(dados_ano["casos"].sum())
            pico_row = dados_ano.loc[dados_ano["casos"].idxmax()]
            pico_mensal = int(pico_row["casos"])
            mes_pico = MESES_PT.get(int(pico_row["month"]), "-")

            # Incidência
            pop_row = pop_df[pop_df["year"] == ano]
            if not pop_row.empty and pop_row.iloc[0]["pop"] > 0:
                incidencia = round((casos_total / pop_row.iloc[0]["pop"]) * 100_000, 1)
            else:
                incidencia = None

            # Variação %
            if tabela_epidem:
                prev = tabela_epidem[-1]["casos"]
                if prev and prev > 0:
                    variacao = round(((casos_total - prev) / prev) * 100, 1)
                else:
                    variacao = None
            else:
                variacao = None

            tabela_epidem.append({
                "ano": int(ano), "casos": casos_total, "incidencia": incidencia,
                "pico": pico_mensal, "mes_pico": mes_pico, "variacao": variacao,
            })

    # ═══════════════════════════════════════════════════════════
    # NOVOS DADOS: Correlação de Pearson (clima vs dengue com lags)
    # ═══════════════════════════════════════════════════════════
    tabela_correlacao = []
    try:
        from scipy.stats import pearsonr
        nomes_preditores = {"temp_media": "Temperatura Média (°C)", "precipitacao": "Precipitação (mm)"}
        for var in ["temp_media", "precipitacao"]:
            if var not in panel.columns:
                continue
            for lag in [0, 1, 2, 3]:
                shifted = panel[var].shift(lag)
                valid = panel[["dengue_cases"]].assign(clima=shifted).dropna()
                if len(valid) > 5:
                    r, p = pearsonr(valid["clima"], valid["dengue_cases"])
                    tabela_correlacao.append({
                        "preditor": nomes_preditores.get(var, var),
                        "lag": lag,
                        "r_pearson": round(float(r), 3),
                        "p_valor": round(float(p), 4),
                    })
    except ImportError:
        pass  # scipy não instalado

    # ═══════════════════════════════════════════════════════════
    # NOVOS DADOS: Série temporal mensal (labels + real + previsto)
    # ═══════════════════════════════════════════════════════════
    serie_labels = []
    serie_real = []
    serie_previsto = []
    q95_threshold = 0.0

    if not hist_mensal.empty:
        q95_threshold = float(np.percentile(hist_mensal["casos"].dropna(), 95))
        for _, row in hist_mensal.iterrows():
            label = f"{int(row['year'])}-{int(row['month']):02d}"
            serie_labels.append(label)
            serie_real.append(float(row["casos"]) if not pd.isna(row["casos"]) else None)

        # Predições mensais do backtest (se disponíveis)
        try:
            bt = pd.read_csv(ML_OUTPUT / "backtest_ml_completo.csv")
            bt["label"] = bt["year"].astype(str) + "-" + bt["month"].astype(str).str.zfill(2)
            bt_map = dict(zip(bt["label"], bt["pred_cases_ml"]))
            serie_previsto = [round(bt_map.get(l, 0), 1) if l in bt_map else None for l in serie_labels]
        except Exception:
            serie_previsto = [None] * len(serie_labels)

    serie_temporal = {
        "labels": serie_labels,
        "real": serie_real,
        "previsto": serie_previsto,
        "q95": round(q95_threshold, 1),
    }

    # ═══════════════════════════════════════════════════════════
    # NOVOS DADOS: Clima mensal (para gráfico Clima vs Dengue)
    # ═══════════════════════════════════════════════════════════
    dados_clima = {"labels": [], "temp_media": [], "precipitacao": [], "dengue": []}
    if not clima_mensal.empty and not hist_mensal.empty:
        merged_clima = pd.merge(
            hist_mensal, clima_mensal, on=["year", "month"], how="inner"
        ).sort_values(["year", "month"])
        for _, row in merged_clima.iterrows():
            dados_clima["labels"].append(f"{int(row['year'])}-{int(row['month']):02d}")
            dados_clima["temp_media"].append(round(float(row["temp_media"]), 1) if not pd.isna(row["temp_media"]) else None)
            dados_clima["precipitacao"].append(round(float(row["precipitacao"]), 1) if not pd.isna(row["precipitacao"]) else None)
            dados_clima["dengue"].append(float(row["casos"]) if not pd.isna(row["casos"]) else 0)

    # ═══════════════════════════════════════════════════════════
    # NOVOS DADOS: Heatmap sazonal (meses × anos)
    # ═══════════════════════════════════════════════════════════
    heatmap_data = []
    if not hist_mensal.empty:
        for _, row in hist_mensal.iterrows():
            heatmap_data.append({
                "x": int(row["year"]),
                "y": int(row["month"]),
                "v": float(row["casos"]) if not pd.isna(row["casos"]) else 0,
            })

    # Merge com dados reais (gráfico de barras existente)
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

    # ═══════════════════════════════════════════════════════════
    # Exportação CSV para pasta de anexos
    # ═══════════════════════════════════════════════════════════
    export_dir = ROOT_DIR / "output" / "dashboard_exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    if tabela_epidem:
        pd.DataFrame(tabela_epidem).to_csv(export_dir / "tabela_epidemiologica.csv", index=False)
    if tabela_correlacao:
        pd.DataFrame(tabela_correlacao).to_csv(export_dir / "tabela_correlacao.csv", index=False)
    if serie_labels:
        pd.DataFrame({"label": serie_labels, "real": serie_real, "previsto": serie_previsto}).to_csv(
            export_dir / "serie_temporal_mensal.csv", index=False
        )
    if dados_clima["labels"]:
        pd.DataFrame(dados_clima).to_csv(export_dir / "dados_clima_mensal.csv", index=False)
    if heatmap_data:
        pd.DataFrame(heatmap_data).to_csv(export_dir / "heatmap_sazonal.csv", index=False)

    # ═══════════════════════════════════════════════════════════
    # Exportação PNG (Matplotlib) para relatórios acadêmicos
    # ═══════════════════════════════════════════════════════════
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import seaborn as sns
        
        sns.set_theme(style="whitegrid")

        # 1. Gráfico de Barras Anuais
        plt.figure(figsize=(10, 5))
        plt.bar(merged["year"], merged["real"], label="Casos Reais", color="mediumseagreen", alpha=0.7)
        plt.bar(merged["year"], merged["pred"], label="Previsão XGBoost", color="dodgerblue", alpha=0.7)
        plt.title("Casos Reais vs Previsão XGBoost (Anual)")
        plt.xlabel("Ano")
        plt.ylabel("Casos")
        plt.legend()
        plt.savefig(export_dir / "grafico_barras_anuais.png", dpi=150, bbox_inches="tight")
        plt.close()

        # 2. Gráfico de Série Temporal Mensal
        if serie_labels:
            plt.figure(figsize=(12, 5))
            x_labels = range(len(serie_labels))
            plt.plot(x_labels, serie_real, label="Real (Mensal)", color="mediumseagreen", linewidth=2)
            plt.plot(x_labels, serie_previsto, label="Previsto (XGBoost)", color="dodgerblue", linestyle="--", linewidth=2)
            plt.axhline(y=q95_threshold, color="crimson", linestyle=":", label="Teto Epidêmico (P95)")
            plt.title("Série Temporal Mensal — Real vs Previsto")
            plt.xticks(x_labels[::3], [serie_labels[i] for i in range(0, len(serie_labels), 3)], rotation=45)
            plt.legend()
            plt.tight_layout()
            plt.savefig(export_dir / "grafico_serie_temporal.png", dpi=150)
            plt.close()
            
        # 3. Gráfico Clima vs Dengue
        if dados_clima["labels"]:
            fig, ax1 = plt.subplots(figsize=(12, 5))
            ax2 = ax1.twinx()
            ax3 = ax1.twinx()
            ax3.spines['right'].set_position(('outward', 60))

            x_labels = range(len(dados_clima["labels"]))
            p1 = ax1.plot(x_labels, dados_clima["temp_media"], color="darkorange", label="Temperatura (°C)")
            p2 = ax2.fill_between(x_labels, dados_clima["precipitacao"], color="skyblue", alpha=0.3, label="Precipitação (mm)")
            p3 = ax3.plot(x_labels, dados_clima["dengue"], color="mediumseagreen", linestyle="--", label="Dengue")
            
            ax1.set_xlabel("Mês")
            ax1.set_ylabel("Temp (°C)", color="darkorange")
            ax2.set_ylabel("Precipitação (mm)", color="skyblue")
            ax3.set_ylabel("Dengue (casos)", color="mediumseagreen")
            plt.title("Anomalias Climáticas vs Incidência de Dengue")
            ax1.set_xticks(x_labels[::3])
            ax1.set_xticklabels([dados_clima["labels"][i] for i in range(0, len(dados_clima["labels"]), 3)], rotation=45)
            plt.tight_layout()
            plt.savefig(export_dir / "grafico_clima_vs_dengue.png", dpi=150)
            plt.close()

        # 4. Heatmap Sazonal
        if heatmap_data:
            df_heat = pd.DataFrame(heatmap_data)
            df_heat_pivot = df_heat.pivot(index="y", columns="x", values="v")
            df_heat_pivot.index = [MESES_PT.get(m, m) for m in df_heat_pivot.index]
            plt.figure(figsize=(10, 6))
            sns.heatmap(df_heat_pivot, cmap="YlOrRd", annot=True, fmt="g", cbar_kws={'label': 'Casos'})
            plt.title("Sazonalidade — Heatmap de Casos (Meses × Anos)")
            plt.xlabel("Ano")
            plt.ylabel("Mês")
            plt.tight_layout()
            plt.savefig(export_dir / "heatmap_sazonal.png", dpi=150)
            plt.close()

        # 5. Feature Importance
        if fi:
            plt.figure(figsize=(8, 6))
            fi_sorted = sorted(fi, key=lambda x: x[1], reverse=False)
            labels = [x[0] for x in fi_sorted]
            vals = [x[1] for x in fi_sorted]
            plt.barh(labels, vals, color="dodgerblue")
            plt.title("Importância das Variáveis (Feature Importance)")
            plt.tight_layout()
            plt.savefig(export_dir / "grafico_feature_importance.png", dpi=150)
            plt.close()

    except Exception as e:
        print(f"Erro ao exportar gráficos PNG: {e}")


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
        "tabela_epidemiologica": tabela_epidem,
        "tabela_correlacao": tabela_correlacao,
        "serie_temporal_mensal": serie_temporal,
        "dados_clima_mensal": dados_clima,
        "heatmap_sazonal": heatmap_data,
        "n_cidades": n_cidades,
        "n_registros": len(panel),
    }

