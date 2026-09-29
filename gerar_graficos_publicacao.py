"""
Script dedicado a gerar gráficos estáticos de alta qualidade (PNG) para o artigo,
utilizando Plotly + Kaleido.
Lê os CSVs gerados pelo motor ML e exporta PNGs em `graficos_artigo/`.
"""
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

def gerar_graficos_publicacao():
    root = Path(__file__).parent
    in_dir = root / "output" / "projecoes_regionais" / "ml_completo"
    out_dir = root / "graficos_artigo"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("Gerando gráficos de publicação (Plotly)...")

    # 1. Gráfico de Cenários (2026-2030)
    try:
        df_anual = pd.read_csv(in_dir / "projecao_ml_completa_municipios_anual.csv")
        df_anual = df_anual[(df_anual["year"] >= 2026) & (df_anual["year"] <= 2030)]
        
        # Agrupar por cenário e ano
        df_agg = df_anual.groupby(["scenario", "year"])["pred_cases_ml"].sum().reset_index()
        
        fig = go.Figure()
        
        cores = {"ssp126": "#27ae60", "ssp245": "#e67e22", "ssp370": "#8e44ad", "ssp585": "#c0392b"}
        nomes = {"ssp126": "SSP1-2.6 (Otimista)", "ssp245": "SSP2-4.5 (Intermediário)", 
                 "ssp370": "SSP3-7.0 (Pessimista)", "ssp585": "SSP5-8.5 (Extremo)"}
        tracos = {"ssp126": "solid", "ssp245": "dash", "ssp370": "dot", "ssp585": "dashdot"}
        
        for sc in ["ssp126", "ssp245", "ssp370", "ssp585"]:
            d_sc = df_agg[df_agg["scenario"] == sc]
            if not d_sc.empty:
                fig.add_trace(go.Scatter(
                    x=d_sc["year"], y=d_sc["pred_cases_ml"],
                    mode="lines+markers",
                    name=nomes.get(sc, sc),
                    line=dict(color=cores.get(sc, "blue"), width=3, dash=tracos.get(sc, "solid")),
                    marker=dict(size=8)
                ))
                
        fig.update_layout(
            title="Projeção de Casos de Dengue por Cenário Climático (2026-2030)",
            xaxis_title="Ano",
            yaxis_title="Casos Anuais Projetados",
            template="plotly_white",
            font=dict(family="Arial", size=14),
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        
        fig.write_image(out_dir / "01_projecao_cenarios_plotly.png", width=1200, height=600, scale=2)
        print(" -> 01_projecao_cenarios_plotly.png gerado.")
    except Exception as e:
        print(f"Erro ao gerar gráfico de cenários: {e}")

    # 2. Distribuição Sazonal Média
    try:
        df_mensal = pd.read_csv(in_dir / "projecao_ml_completa_municipios_mensal.csv")
        df_mensal = df_mensal[(df_mensal["scenario"] == "ssp245") & (df_mensal["year"] >= 2026) & (df_mensal["year"] <= 2030)]
        df_mes_agg = df_mensal.groupby("month")["pred_cases_ml"].mean().reset_index()
        
        fig = go.Figure(data=[
            go.Bar(
                x=df_mes_agg["month"],
                y=df_mes_agg["pred_cases_ml"],
                marker_color="#3498db"
            )
        ])
        
        fig.update_layout(
            title="Distribuição Sazonal Média Projetada (2026-2030, SSP2-4.5)",
            xaxis_title="Mês do Ano",
            yaxis_title="Média de Casos Mensais",
            xaxis=dict(tickmode="linear", tick0=1, dtick=1),
            template="plotly_white",
            font=dict(family="Arial", size=14)
        )
        
        fig.write_image(out_dir / "02_distribuicao_sazonal_plotly.png", width=1000, height=500, scale=2)
        print(" -> 02_distribuicao_sazonal_plotly.png gerado.")
    except Exception as e:
        print(f"Erro ao gerar gráfico sazonal: {e}")

    print("Concluído! Gráficos salvos em graficos_artigo/")

if __name__ == "__main__":
    gerar_graficos_publicacao()
