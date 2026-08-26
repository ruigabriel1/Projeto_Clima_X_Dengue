# Predição Epidemiológica de Dengue — Região Sul do Brasil

Projeto de **Engenharia de Dados e Machine Learning** que cruza dados climáticos (INMET), epidemiológicos (SINAN) e anomalias oceânicas (NOAA/El Niño) para prever surtos de dengue nos 1.190 municípios da Região Sul.

## Resultado Principal

| Métrica | Valor |
|---------|-------|
| Algoritmo | XGBoost Regressor (Gradient Boosted Trees) |
| R² Score (Cross-Validation Global) | **0.744** |
| MAE (Erro Médio Absoluto) | **10.8 casos / cidade / mês** |
| Cobertura | 1.190 municípios × 10 anos (142.800 registros) |

O modelo foi validado com Cross-Validation Espacial (treino em 80% das cidades, teste em 20%) e demonstrou capacidade de capturar os padrões sazonais e geográficos da dengue, incluindo o surto recorde de 2024.

## Estrutura do Repositório

```
Projeto_Clima_X_Dengue/
├── data/
│   ├── raw/                    # Camada Bronze: CSVs brutos (SINAN, INMET, NOAA)
│   ├── processed/              # Camada Silver: dados_consolidados.csv
│   └── geodados/               # GeoPackages para mapas (cache local)
├── output/
│   ├── csvs_latitude/          # Camada Silver: 48 CSVs por faixa de latitude
│   ├── mapas_latitude/         # Mapas coropléticos anuais
│   └── *.png / *.json          # Gráficos e métricas do modelo
├── notebooks/
│   ├── 02_analise_completa_ml.ipynb   # EDA + Prophet vs Baseline
│   ├── 03_modelo_global_xgboost.ipynb # XGBoost: Teste Temporal (2024)
│   └── 04_xgboost_alta_precisao.ipynb # XGBoost: Validação Global (R²=0.74)
├── src/                        # Código-fonte do pipeline
├── docs/                       # Documentação técnica
│   ├── ARQUITETURA_DE_DADOS.md # Pipeline Medallion (Bronze/Silver/Gold)
│   ├── CIENCIA_DE_DADOS_XGBOOST.md # Decisões de modelagem
│   └── legado/                 # Documentos de versões anteriores
├── main.py                     # CLI principal (process-data, run-model, generate-reports)
└── requirements.txt
```

## Como Rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt
pip install xgboost

# 2. Processar dados brutos (Bronze → Silver)
python main.py process-data

# 3. Explorar o modelo interativamente
jupyter notebook notebooks/04_xgboost_alta_precisao.ipynb
```

## Documentação

- [Arquitetura de Dados (Medallion)](docs/ARQUITETURA_DE_DADOS.md) — Pipeline completo: ingestão, limpeza e preparação para ML
- [Ciência de Dados & XGBoost](docs/CIENCIA_DE_DADOS_XGBOOST.md) — Decisões de modelagem, features e validação

## Fontes de Dados

| Sigla | Nome Completo | O que fornece |
|-------|--------------|---------------|
| **SINAN** | Sistema de Informação de Agravos de Notificação (Ministério da Saúde) | Casos mensais de dengue por município |
| **INMET** | Instituto Nacional de Meteorologia | Temperatura média, mínima, máxima e precipitação mensal |
| **NOAA** | National Oceanic and Atmospheric Administration (EUA) | Índice ONI (Oceanic Niño Index) para classificação El Niño/La Niña |
