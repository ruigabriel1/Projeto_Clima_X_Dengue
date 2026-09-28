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

    # Executa o pipeline completo do motor para gerar as projeções oficiais e métricas
    emit("Treinando XGBoost e rodando motor oficial...", 45)
    from src.processamento.motor_lote_modelagem_v2_por_latitude import run_full_ml
    
    # Executa run_full_ml e extrai o dicionário de resultados
    ml_results = run_full_ml(ROOT_DIR, panel)
    
    emit("Calculando métricas...", 85)
    fi = ml_results.get("feature_importance", [(f, 0.0) for f in FEATURE_COLS])
    
    metrics_ml = ml_results.get("metricas", [])
    m_test = metrics_ml[1] if len(metrics_ml) > 1 else {}
    real_metrics = {
        "mae": m_test.get("mae", 0),
        "rmse": m_test.get("rmse", 0),
        "r2": m_test.get("r2", 0)
    }

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

    # --- Lê projeção mensal para tabelas e gráficos ---
    try:
        proj_mensal_file = ML_OUTPUT / "projecao_ml_completa_municipios_mensal.csv"
        df_proj_m = pd.read_csv(proj_mensal_file)
        df_proj_m = df_proj_m[(df_proj_m["scenario"] == "ssp245") & (df_proj_m["year"] >= 2026) & (df_proj_m["year"] <= 2030)]
        
        if codigo_ibge:
            df_proj_m = df_proj_m[df_proj_m["code"] == int(codigo_ibge)]
        elif modo == "rapido":
            df_proj_m = df_proj_m[df_proj_m["code"] == 421600]
            
        proj_mensal = df_proj_m.groupby(["year", "month"])["pred_cases_ml"].sum().reset_index()
        proj_mensal.rename(columns={"pred_cases_ml": "casos"}, inplace=True)
    except Exception as e:
        print(f"Erro ao carregar proj_mensal: {e}")
        proj_mensal = pd.DataFrame()

    # --- Tabela epidemiológica (Projetada) ---
    tabela_epidem = []
    if not proj_mensal.empty:
        # Última população disponível
        pop_recente = pop_df["pop"].iloc[-1] if not pop_df.empty else 0
        
        for ano in sorted(proj_mensal["year"].unique()):
            dados_ano = proj_mensal[proj_mensal["year"] == ano]
            casos_total = int(dados_ano["casos"].sum())
            pico_row = dados_ano.loc[dados_ano["casos"].idxmax()]
            pico_mensal = int(pico_row["casos"])
            mes_pico = MESES_PT.get(int(pico_row["month"]), "-")

            incidencia = round((casos_total / pop_recente) * 100_000, 1) if pop_recente > 0 else None

            if tabela_epidem:
                prev = tabela_epidem[-1]["casos"]
                variacao = round(((casos_total - prev) / prev) * 100, 1) if prev and prev > 0 else None
            else:
                # Calcular variação em relação ao último ano histórico (2025 ou 2024)
                if not hist_mensal.empty:
                    ult_ano_hist = hist_mensal["year"].max()
                    prev = hist_mensal[hist_mensal["year"] == ult_ano_hist]["casos"].sum()
                    variacao = round(((casos_total - prev) / prev) * 100, 1) if prev > 0 else None
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
        nomes_preditores = {"temp_media": "Temperatura média (°C)", "precipitacao": "Precipitação acum. (mm)"}
        
        # Coleta de todos os testes para ajuste de Bonferroni
        testes = []
        for var in ["temp_media", "precipitacao"]:
            if var not in panel.columns:
                continue
            for lag in [0, 1, 2, 3, 4]:
                if var == "precipitacao" and lag not in [2, 4]:
                    continue
                if var == "temp_media" and lag not in [0, 1, 2, 3]:
                    continue
                shifted = panel[var].shift(lag)
                valid = panel[["dengue_cases"]].assign(clima=shifted).dropna()
                if len(valid) > 5:
                    r, p = pearsonr(valid["clima"], valid["dengue_cases"])
                    
                    # Calcula IC 95%
                    z = np.arctanh(r)
                    se = 1.0 / np.sqrt(len(valid) - 3)
                    lo = np.tanh(z - 1.96 * se)
                    hi = np.tanh(z + 1.96 * se)
                    
                    testes.append({
                        "preditor": nomes_preditores.get(var, var),
                        "lag": lag,
                        "r_pearson": float(r),
                        "p_valor": float(p),
                        "ic_lo": lo,
                        "ic_hi": hi
                    })
        
        # Ajuste de p-valor (Bonferroni simplificado)
        n_testes = len(testes)
        for t in testes:
            p_adj = min(t["p_valor"] * n_testes, 1.0)
            tabela_correlacao.append({
                "preditor": t["preditor"],
                "lag": t["lag"],
                "r_pearson": f"{t['r_pearson']:.2f}".replace('.', ','),
                "ic_95": f"{t['ic_lo']:.2f} – {t['ic_hi']:.2f}".replace('.', ','),
                "p_valor_ajustado": f"< 0,001" if p_adj < 0.001 else f"{p_adj:.3f}".replace('.', ',')
            })
    except Exception as e:
        print(f"Erro na tabela de correlação: {e}")

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
            bt = pd.read_csv(ML_OUTPUT / "projecoes_regionais" / "ml_completo" / "backtest_ml_completo.csv")
            bt["label"] = bt["year"].astype(str) + "-" + bt["month"].astype(str).str.zfill(2)
            bt_map = dict(zip(bt["label"], bt["pred_cases_ml"]))
            serie_previsto = []
            for l in serie_labels:
                serie_previsto.append(round(bt_map.get(l, 0), 1) if l in bt_map else None)
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
    # NOVOS DADOS: Distribuição Sazonal (Casos vs Temp Média)
    # ═══════════════════════════════════════════════════════════
    dist_sazonal_dict = {"meses": [], "casos_mean": [], "temp_mean": []}
    if not proj_mensal.empty and not clima_mensal.empty:
        # Usa a temperatura média histórica mensal
        clima_medio = clima_mensal.groupby("month")["temp_media"].mean().reset_index()
        # Junta com a média projetada de casos mensais
        proj_medio = proj_mensal.groupby("month")["casos"].mean().reset_index()
        
        df_saz = pd.merge(proj_medio, clima_medio, on="month", how="inner")
        
        for _, row in df_saz.iterrows():
            dist_sazonal_dict["meses"].append(int(row["month"]))
            dist_sazonal_dict["casos_mean"].append(round(float(row["casos"]), 1))
            dist_sazonal_dict["temp_mean"].append(round(float(row["temp_media"]), 1))
            
    # Heatmap (Projetado)
    heatmap_data = []
    if not proj_mensal.empty:
        for _, row in proj_mensal.iterrows():
            heatmap_data.append({
                "ano": int(row["year"]),
                "mes": int(row["month"]),
                "casos": float(row["casos"]) if not pd.isna(row["casos"]) else 0
            })
    
    dist_sazonal_dict["heatmap"] = heatmap_data

    # Merge com dados reais (gráfico de barras existente)
    merged = pd.merge(hist, chart_data, on="year", how="outer").sort_values("year")
    
    emit("Gerando métricas e salvando gráficos...", 95)

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
    if dist_sazonal_dict and dist_sazonal_dict["meses"]:
        pd.DataFrame({"mes": dist_sazonal_dict["meses"], "casos": dist_sazonal_dict["casos_mean"], "temp": dist_sazonal_dict["temp_mean"]}).to_csv(export_dir / "distribuicao_sazonal.csv", index=False)

    # Lê projeções climáticas futuras se existirem para usar no matplotlib
    projecao_cenarios = {}
    try:
        fut_file = ML_OUTPUT / "projecao_ml_completa_regional_anual.csv"
        if not fut_file.exists():
            fut_file = ML_OUTPUT / "projecao_ml_completa_municipios_anual.csv"
            
        if fut_file.exists():
            fut_df = pd.read_csv(fut_file)
            for sc in fut_df["scenario"].unique():
                sc_df = fut_df[(fut_df["scenario"] == sc) & (fut_df["year"] <= 2030)]
                sc_df = sc_df.groupby("year")["pred_cases_ml"].sum().reset_index()
                projecao_cenarios[sc] = {
                    "anos": sc_df["year"].tolist(),
                    "casos": sc_df["pred_cases_ml"].round().tolist()
                }
            
            # Export CSV for the frontend
            export_cenarios = []
            if "ssp126" in projecao_cenarios:
                for idx, ano in enumerate(projecao_cenarios["ssp126"]["anos"]):
                    export_cenarios.append({
                        "ano": ano,
                        "ssp126": projecao_cenarios.get("ssp126", {}).get("casos", [])[idx] if "ssp126" in projecao_cenarios else None,
                        "ssp245": projecao_cenarios.get("ssp245", {}).get("casos", [])[idx] if "ssp245" in projecao_cenarios else None,
                        "ssp585": projecao_cenarios.get("ssp585", {}).get("casos", [])[idx] if "ssp585" in projecao_cenarios else None,
                    })
                pd.DataFrame(export_cenarios).to_csv(export_dir / "grafico_cenarios.csv", index=False)
                
    except Exception as e:
        print(f"Erro ao carregar projeções futuras: {e}")

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

        # 4. Distribuição Sazonal (Casos e Temp Média)
        if dist_sazonal_dict and dist_sazonal_dict["meses"]:
            df_saz = pd.DataFrame({"mes": dist_sazonal_dict["meses"], "casos": dist_sazonal_dict["casos_mean"], "temp": dist_sazonal_dict["temp_mean"]})
            fig, ax1 = plt.subplots(figsize=(10, 5))
            
            x_labels = [MESES_PT.get(m, m) for m in df_saz["mes"]]
            
            color_bar = "#5fa8d3"
            color_peak = "#c0392b"
            color_line = "#e74c3c"
            
            # Find peak
            peak_idx = df_saz["casos"].idxmax()
            
            colors = [color_peak if i == peak_idx else color_bar for i in range(len(df_saz))]
            
            ax1.bar(x_labels, df_saz["casos"], color=colors, alpha=0.9, label="Casos (média 2015-2025)")
            ax1.set_ylabel("Casos médios mensais", color="#1f4e79", fontweight='bold')
            ax1.tick_params(axis='y', labelcolor="#1f4e79")
            
            # Add callout to peak
            peak_val = df_saz.loc[peak_idx, "casos"]
            ax1.annotate(f"Pico: {int(peak_val)} casos", 
                        xy=(peak_idx, peak_val), 
                        xytext=(peak_idx+0.5, peak_val + max(df_saz["casos"])*0.1),
                        arrowprops=dict(facecolor='#2c3e50', shrink=0.05, width=1.5, headwidth=6),
                        fontsize=10, fontweight='bold', color="#2c3e50")
            
            ax2 = ax1.twinx()
            ax2.plot(x_labels, df_saz["temp"], color=color_line, marker="o", linewidth=2.5, label="Temperatura média (°C)")
            ax2.set_ylabel("Temperatura média (°C)", color=color_line, fontweight='bold')
            ax2.tick_params(axis='y', labelcolor=color_line)
            
            plt.title("Distribuição Sazonal de Casos de Dengue e Temperatura Média\nSão Carlos (SC), 2015–2025", fontweight='bold')
            ax1.set_xlabel("Mês", fontweight='bold')
            
            # Custom legend
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
            
            plt.grid(True, linestyle="--", alpha=0.3)
            plt.tight_layout()
            plt.savefig(export_dir / "distribuicao_sazonal.png", dpi=150)
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

        # 6. Gráfico Projeção Cenários Climáticos (2026-2030)
        if projecao_cenarios and "ssp126" in projecao_cenarios:
            anos_cenario = projecao_cenarios["ssp126"]["anos"]
            
            plt.figure(figsize=(10, 5))
            
            # Envelope de incerteza (ssp126 to ssp585 se existirem)
            if "ssp585" in projecao_cenarios:
                plt.fill_between(
                    anos_cenario, 
                    projecao_cenarios["ssp126"]["casos"], 
                    projecao_cenarios["ssp585"]["casos"], 
                    color="#3498db", alpha=0.15, label="Envelope de incerteza"
                )
            
            # ssp126
            plt.plot(anos_cenario, projecao_cenarios["ssp126"]["casos"], 
                     color="#27ae60", marker="o", linewidth=2.5, 
                     label="Referência (linha de base)")
                     
            # ssp245
            if "ssp245" in projecao_cenarios:
                plt.plot(anos_cenario, projecao_cenarios["ssp245"]["casos"], 
                         color="#e67e22", marker="s", linestyle="--", linewidth=2.5, 
                         label="Intermediário (+0,6 °C / +3% precip.)")
                         
            # ssp585
            if "ssp585" in projecao_cenarios:
                plt.plot(anos_cenario, projecao_cenarios["ssp585"]["casos"], 
                         color="#c0392b", marker="D", linestyle="-.", linewidth=2.5, 
                         label="Intensificado (+1,2 °C / +6% precip.)")
            
            plt.title("Projeção de Casos de Dengue por Cenário Climático\nSão Carlos (SC), 2026–2030", fontweight='bold')
            plt.xlabel("Ano", fontweight='bold')
            plt.ylabel("Casos anuais projetados", fontweight='bold')
            plt.xticks(anos_cenario)
            plt.ylim(1000, 2000)
            
            # Annotations values
            for sc_key, color in [("ssp126", "#27ae60"), ("ssp245", "#e67e22"), ("ssp585", "#c0392b")]:
                if sc_key in projecao_cenarios:
                    for x, y in zip(anos_cenario, projecao_cenarios[sc_key]["casos"]):
                        plt.annotate(f"{int(y)}", (x, y), textcoords="offset points", xytext=(0, 10), ha='center', color=color, fontsize=8, fontweight='bold')
            
            plt.legend(loc="upper left")
            plt.grid(True, linestyle="--", alpha=0.3)
            plt.tight_layout()
            plt.savefig(export_dir / "grafico_cenarios.png", dpi=150)
            plt.close()

    except Exception as e:
        print(f"Erro ao exportar gráficos PNG: {e}")

    return {
        "metricas": {
            "mae": round(real_metrics["mae"], 2),
            "rmse": round(real_metrics["rmse"], 2),
            "r2": round(real_metrics["r2"], 4)
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
        "dist_sazonal": dist_sazonal_dict,
        "projecao_cenarios": projecao_cenarios,
        "n_cidades": n_cidades,
        "n_registros": len(panel),
    }

