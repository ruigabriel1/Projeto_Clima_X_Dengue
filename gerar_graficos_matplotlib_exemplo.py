"""
Exemplo de geração de gráficos acadêmicos usando Matplotlib e Seaborn.
Foi solicitado pelo usuário para comparação com o Plotly.
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def gerar_graficos_matplotlib():
    root = Path(__file__).parent
    in_dir = root / "output" / "projecoes_regionais" / "ml_completo"
    out_dir = root / "graficos_artigo"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("Gerando gráficos de publicação (Matplotlib/Seaborn)...")
    
    # Configurar estilo acadêmico (estilo ABNT/APA)
    sns.set_theme(style="whitegrid", font="serif")
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 16,
        'figure.titlesize': 18,
        'legend.fontsize': 12,
        'xtick.labelsize': 12,
        'ytick.labelsize': 12,
        'figure.dpi': 300,  # Alta resolução
        'savefig.dpi': 300,
        'savefig.bbox': 'tight'
    })

    # 1. Gráfico de Cenários
    try:
        df_anual = pd.read_csv(in_dir / "projecao_ml_completa_municipios_anual.csv")
        df_anual = df_anual[(df_anual["year"] >= 2026) & (df_anual["year"] <= 2030)]
        df_agg = df_anual.groupby(["scenario", "year"])["pred_cases_ml"].sum().reset_index()
        
        plt.figure(figsize=(10, 6))
        
        cores = {"ssp126": "#27ae60", "ssp245": "#e67e22", "ssp370": "#8e44ad", "ssp585": "#c0392b"}
        nomes = {"ssp126": "SSP1-2.6", "ssp245": "SSP2-4.5", "ssp370": "SSP3-7.0", "ssp585": "SSP5-8.5"}
        linhas = {"ssp126": "-", "ssp245": "--", "ssp370": ":", "ssp585": "-."}
        
        for sc in ["ssp126", "ssp245", "ssp370", "ssp585"]:
            d_sc = df_agg[df_agg["scenario"] == sc]
            if not d_sc.empty:
                plt.plot(
                    d_sc["year"], d_sc["pred_cases_ml"], 
                    label=nomes.get(sc, sc), 
                    color=cores.get(sc, "black"),
                    linestyle=linhas.get(sc, "-"),
                    linewidth=2.5,
                    marker='o'
                )
                
        plt.title("Projeção de Casos (2026-2030)")
        plt.xlabel("Ano")
        plt.ylabel("Casos Anuais")
        plt.legend()
        plt.xticks(range(2026, 2031))
        
        plt.savefig(out_dir / "01_projecao_cenarios_matplotlib.png")
        plt.close()
        print(" -> 01_projecao_cenarios_matplotlib.png gerado.")
    except Exception as e:
        print(f"Erro no matplotlib: {e}")

if __name__ == "__main__":
    gerar_graficos_matplotlib()
