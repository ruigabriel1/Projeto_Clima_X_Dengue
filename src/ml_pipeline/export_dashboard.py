"""
ml_runner.py — Wrapper leve do motor ML para a interface Prodígia.
Encapsula build_base_panel() e run_full_ml(), emitindo progresso via callback.
"""
import sqlite3
import json
import numpy as np
import pandas as pd
from pathlib import Path
import argparse
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT_DIR / "data" / "processed" / "dengue_analytics.db"
ML_OUTPUT = ROOT_DIR / "output" / "projecoes_regionais" / "ml_completo"

FEATURE_COLS = [
    "temp_media", "precipitacao", "enso", "latitude", "month_sin", "month_cos",
    "dengue_lag1", "dengue_lag2", "dengue_lag3", "temp_lag1", "prec_lag1", "enso_lag1",
    "dengue_rolling_12",
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


def exportar_dados_dashboard(
    modo: str = "rapido",
    codigo_ibge: Optional[str] = None
) -> dict:
    """Consolida os dados do banco e resultados ML (ml_run_log) no JSON do dashboard."""
    print("Carregando dados do SQLite...")

    from src.processamento.motor_lote_modelagem_v2_por_latitude import (
        build_base_panel, _build_ml_features, _evaluate_split, _safe_mape,
    )
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    panel, lookup = build_base_panel(ROOT_DIR, modo=modo)
    print(f"Painel carregado: {len(panel)} registros")

    # Aplicar filtro avançado se código IBGE específico for solicitado
    if codigo_ibge:
        panel = panel[panel["code"] == str(codigo_ibge)].copy()

    n_cidades = panel["code"].nunique()
    print(f"Escopo: {n_cidades} cidade(s) selecionada(s)")

    if panel.empty:
        raise ValueError("Nenhum dado encontrado para o escopo selecionado.")

    print("Carregando métricas e features do ml_run_log.json...")
    
    # Carregar resultados do novo pipeline de MLOps
    log_file = ROOT_DIR / "output" / "ml_run_log.json"
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            ml_log = json.load(f)
            metrics_ml = ml_log.get("metrics", [])
            fi_raw = ml_log.get("feature_importance", [])
            fi = [(item[0], item[1]) for item in fi_raw] if fi_raw else []
    else:
        print("[AVISO] ml_run_log.json não encontrado. Use o novo pipeline (ml_orchestrator.py) antes.")
        metrics_ml = []
        fi = []

    # Extrair médias do LOYO (novo modelo)
    if metrics_ml:
        # Usa a média das métricas LOYO ou o último ano para o dashboard principal
        avg_r2 = np.mean([m["r2"] for m in metrics_ml])
        avg_mae = np.mean([m["mae"] for m in metrics_ml])
        avg_rmse = np.mean([m["rmse"] for m in metrics_ml])
        real_metrics = {"mae": avg_mae, "rmse": avg_rmse, "r2": avg_r2}
    else:
        real_metrics = {"mae": 0, "rmse": 0, "r2": 0}

    print("Montando dados para gráficos...")
    
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
            bt = pd.read_csv(ML_OUTPUT / "backtest_ml_completo.csv")
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
    
    print("Gerando métricas e salvando gráficos...")

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

    # Lê projeções climáticas futuras se existirem
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
                
    except Exception as e:
        print(f"Erro ao carregar projeções futuras: {e}")

    # ═══════════════════════════════════════════════════════════
    # Exportação estática (Plotly + Kaleido) para relatórios acadêmicos
    # ═══════════════════════════════════════════════════════════
    export_dir = ROOT_DIR / "graficos_artigo"
    export_dir.mkdir(parents=True, exist_ok=True)

    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        def export_fig(fig, filename):
            fig.update_layout(template="plotly_white", paper_bgcolor='white', plot_bgcolor='white', font=dict(family="Inter, sans-serif"))
            fig.write_image(export_dir / filename, scale=2)

        # 1. Gráfico de Barras Anuais
        fig = go.Figure()
        
        # Filtrar o df merged para mostrar apenas a janela de interesse (ex: 2020 a 2030)
        merged_filtered = merged[(merged["year"] >= 2020) & (merged["year"] <= 2030)]
        
        fig.add_trace(go.Bar(x=merged_filtered["year"], y=merged_filtered["real"], name="Casos Reais", marker_color="#10b981"))
        fig.add_trace(go.Bar(x=merged_filtered["year"], y=merged_filtered["pred"], name="Previsão do Modelo", marker_color="#3b82f6"))
        fig.update_layout(title="Casos Reais vs Previsão do Modelo (Anual) — São Carlos, SC", barmode="group")
        export_fig(fig, "grafico_barras_anuais.png")

        # 2. Gráfico de Série Temporal Mensal
        if serie_labels:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=serie_labels, y=serie_real, name="Real (Mensal)", line=dict(color="#10b981", width=2)))
            fig.add_trace(go.Scatter(x=serie_labels, y=serie_previsto, name="Previsto", line=dict(color="#3b82f6", width=2, dash="dash")))
            fig.add_trace(go.Scatter(x=[serie_labels[0], serie_labels[-1]], y=[q95_threshold, q95_threshold], mode="lines", name="Teto Epidêmico", line=dict(color="#ef4444", width=2, dash="dot")))
            fig.update_layout(title="Série Temporal Mensal — Real vs Previsto")
            export_fig(fig, "grafico_serie_temporal.png")
            
        # 3. Gráfico Clima vs Dengue
        if dados_clima["labels"]:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Scatter(x=dados_clima["labels"], y=dados_clima["temp_media"], name="Temp (°C)", line=dict(color="#f59e0b")), secondary_y=False)
            fig.add_trace(go.Bar(x=dados_clima["labels"], y=dados_clima["precipitacao"], name="Precip (mm)", marker_color="rgba(59, 130, 246, 0.3)"), secondary_y=False)
            fig.add_trace(go.Scatter(x=dados_clima["labels"], y=dados_clima["dengue"], name="Dengue", line=dict(color="#10b981", dash="dash")), secondary_y=True)
            fig.update_layout(title="Anomalias Climáticas vs Incidência de Dengue")
            export_fig(fig, "grafico_clima_vs_dengue.png")

        # 4. Distribuição Sazonal (Casos e Temp Média)
        if dist_sazonal_dict and dist_sazonal_dict["meses"]:
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            x_labels = [MESES_PT.get(m, m) for m in dist_sazonal_dict["meses"]]
            colors = ["#1e293b" for _ in x_labels]
            
            # Find peak
            if dist_sazonal_dict["casos_mean"]:
                peak_idx = dist_sazonal_dict["casos_mean"].index(max(dist_sazonal_dict["casos_mean"]))
                colors[peak_idx] = "#ef4444"
                
            fig.add_trace(go.Bar(x=x_labels, y=dist_sazonal_dict["casos_mean"], name="Casos", marker_color=colors), secondary_y=False)
            fig.add_trace(go.Scatter(x=x_labels, y=dist_sazonal_dict["temp_mean"], name="Temp", line=dict(color="#f59e0b", width=3)), secondary_y=True)
            fig.update_layout(title="Distribuição Sazonal de Casos e Temperatura Média")
            export_fig(fig, "distribuicao_sazonal.png")

        # 5. Feature Importance
        if fi:
            LABEL_MAP = {
                "dengue_lag1": "Dengue mês anterior",
                "dengue_rolling_12": "Média móvel 12 meses",
                "precipitacao": "Precipitação (mm)",
                "temp_media": "Temperatura média (°C)",
                "enso": "Índice ENSO",
                "is_outbreak_season": "Estação de Surto",
                "temp_lag1": "Temp. mês anterior",
                "prec_lag1": "Precip. mês anterior",
                "enso_lag1": "ENSO mês anterior",
                "month_sin": "Sazonalidade (Seno)",
                "month_cos": "Sazonalidade (Cosseno)",
                "latitude": "Latitude"
            }
            
            fi_sorted = sorted(fi, key=lambda x: x[1], reverse=False)
            labels = [LABEL_MAP.get(x[0], x[0]) for x in fi_sorted]
            vals = [x[1] for x in fi_sorted]
            fig = go.Figure(go.Bar(x=vals, y=labels, orientation='h', marker_color="#3b82f6"))
            fig.update_layout(title="Importância das Variáveis")
            export_fig(fig, "grafico_feature_importance.png")

        # 6. Gráfico Projeção Cenários Climáticos (2026-2030)
        if projecao_cenarios and "ssp126" in projecao_cenarios:
            anos_cenario = projecao_cenarios["ssp126"]["anos"]
            fig = go.Figure()
            
            if "ssp585" in projecao_cenarios:
                # Envelope
                fig.add_trace(go.Scatter(
                    x=anos_cenario + anos_cenario[::-1],
                    y=projecao_cenarios["ssp585"]["casos"] + projecao_cenarios["ssp126"]["casos"][::-1],
                    fill='toself',
                    fillcolor='rgba(59, 130, 246, 0.1)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name="Incerteza"
                ))

            fig.add_trace(go.Scatter(x=anos_cenario, y=projecao_cenarios["ssp126"]["casos"], name="SSP1-2.6 (Otimista)", line=dict(color="#10b981", width=3)))
            
            if "ssp245" in projecao_cenarios:
                fig.add_trace(go.Scatter(x=anos_cenario, y=projecao_cenarios["ssp245"]["casos"], name="SSP2-4.5 (Moderado)", line=dict(color="#f59e0b", width=3, dash="dash")))
                
            if "ssp585" in projecao_cenarios:
                fig.add_trace(go.Scatter(x=anos_cenario, y=projecao_cenarios["ssp585"]["casos"], name="SSP5-8.5 (Pessimista)", line=dict(color="#ef4444", width=3, dash="dot")))
                
            fig.update_layout(title="Projeção de Casos de Dengue (2026-2030)")
            export_fig(fig, "grafico_cenarios.png")

    except Exception as e:
        print(f"Erro ao exportar gráficos Plotly estáticos: {e}")

    resultado_final = {
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

    try:
        with open(ROOT_DIR / "output" / "prodigia_resultados_v2.json", "w", encoding="utf-8") as f:
            json.dump(resultado_final, f, ensure_ascii=False)
    except Exception as e:
        print(f"Erro ao salvar JSON de resultados finais: {e}")

    return resultado_final

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Exporta dados do banco e ML para JSON consumido pelo Dashboard")
    parser.add_argument("--modo", type=str, choices=["rapido", "regional", "completo"], default="rapido")
    parser.add_argument("--codigo_ibge", type=str, default=None)
    args = parser.parse_args()
    
    exportar_dados_dashboard(modo=args.modo, codigo_ibge=args.codigo_ibge)
