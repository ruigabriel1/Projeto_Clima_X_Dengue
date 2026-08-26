# 🏛️ Arquitetura de Dados (Pipeline Medallion)

Este documento descreve como saímos do caos de dados governamentais sujos para um painel consolidado de alta confiabilidade.

## 1. Camada Bronze (Raw Data)
**Local:** `data/raw/`
* **SINAN**: CSVs de notificações mensais de dengue.
* **INMET**: CSVs massivos de temperaturas e precipitação (com falhas de leitura).
* **NOAA**: CSV do El Niño Oceanic Index (ONI).

## 2. Camada Silver (Processamento & Limpeza)
**Local:** `src/consolidar_dados.py` e `src/processamento/processar_clima_por_latitude.py`
* **Outliers Climáticos**: Filtro de valores absurdos (-99.9) gerados por estações offline do INMET.
* **Preenchimento Epidêmico**: Interpolação de valores ausentes de dengue para 0 (sem casos no mês).
* **Faixas de Latitude**: Agrupamento geográfico transversal para estabilizar as séries climáticas.

## 3. Camada Gold (Painel ML)
**Local:** `notebooks/` (Gerado dinamicamente via `build_base_panel`)
O cruzamento final gera uma matriz de mais de 142.000 registros prontos para o consumo da IA (XGBoost), agregando os `lags` temporais das chuvas e anomalias oceânicas.
