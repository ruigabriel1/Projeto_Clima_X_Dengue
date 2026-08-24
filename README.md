<div align="center">

# 🦟 Clima × Dengue — Modelagem Climático-Epidemiológica

### Região Sul do Brasil · 2015 – 2040

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Ativo-brightgreen)]()
[![Região](https://img.shields.io/badge/Regi%C3%A3o-Sul%20do%20Brasil-blue)]()
[![Municípios](https://img.shields.io/badge/Munic%C3%ADpios-1.190-orange)]()

> **Como transformar sinais climáticos em evidência acionável para vigilância de dengue — antes do pico epidemiológico?**

</div>

---

## 🎯 Visão Geral

Este projeto integra séries históricas de dengue (2015–2024), temperatura, precipitação e índice ENSO (El Niño / La Niña) em um pipeline de modelagem estatística e machine learning para projetar o risco de casos de dengue na Região Sul do Brasil até **2040**, sob quatro cenários climáticos do IPCC.

A leitura territorial é feita em **8 faixas de latitude**, cobrindo do litoral norte do Paraná ao extremo sul gaúcho, com resolução de município.

---

## 📦 O que o projeto entrega

| Produto | Descrição |
|---|---|
| 📊 **Histórico consolidado** | Incidência mensal por município, 2015–2024 |
| 🗺️ **Mapas coropléticos** | Dengue, temperatura e precipitação por ano |
| 📈 **Projeções 2025–2040** | Quatro cenários SSP, por faixa de latitude e consolidado |
| 🤖 **Previsão ML 2025** | HistGradientBoosting com split temporal (val 2022, test 2023–2024) |
| ⚖️ **Cenário sem incremento** | Projeção contrafactual (climatologia estável) para comparação |
| 📄 **Relatórios PDF** | Executivo completo + relatório técnico ABNT por cenário |

---

## 🧮 Modelo em uma equação

O motor log-linear usa defasagem de **3 meses** para capturar a resposta epidemiológica ao clima:

$$\log(Y + 1) = \alpha_{local} + \beta_{T} \cdot T_{t-3} + \beta_{P} \cdot P_{t-3} + \beta_{ENSO} \cdot ENSO_{t-3} + \beta_{lat} \cdot Lat$$

| Parâmetro | Valor | Significância |
|---|---|---|
| β temperatura | 0,661 | *** p < 0,001 |
| β precipitação | 0,093 | *** p < 0,001 |
| β ENSO (ONI) | 0,043 | *** p < 0,001 |
| β latitude | 0,142 | *** p < 0,001 |

> **Resultado de validação:** Latitude responde por ~77% da importância relativa no modelo de regressão múltipla (R² = 0,177).

---

## 🌡️ Cenários SSP (IPCC)

| Cenário | Δ Temp./ano | Δ Prec./ano | Descrição |
|---|---|---|---|
| **SSP1-2.6** | +0,02 °C | +0,3% | Transição sustentável — emissões baixas |
| **SSP2-4.5** | +0,04 °C | +0,6% | Desenvolvimento moderado |
| **SSP3-7.0** | +0,06 °C | +1,0% | Fragmentação regional — emissões altas |
| **SSP5-8.5** | +0,08 °C | +1,5% | Combustíveis fósseis — cenário severo |

---

## 🗂️ Estrutura do Repositório

```text
Projeto_Clima_X_Dengue/
│
├── data/
│   ├── raw/                    # Séries brutas mensais (dengue, temp, prec, ENSO)
│   ├── processed/              # Painel consolidado para análises rápidas
│   └── geodados/               # Cache de polígonos geoespaciais (geopandas)
│
├── docs/
│   ├── guia_execucao.md        # Passo a passo de execução
│   └── guia_interpretacao.md   # Como ler os outputs e gráficos
│
├── output/
│   ├── csvs_latitude/          # Séries longas por faixa (8 faixas × 4 variáveis)
│   ├── medias_latitude/        # Médias mensais por faixa (CSV + XLSX)
│   ├── mapas/                  # PNGs coropléticos por ano (2015–2024)
│   ├── mapas_latitude/         # Mapas por faixa de latitude + consolidado
│   ├── analise_estatistica/    # PDFs analíticos, CSVs de resultados
│   ├── projecoes_regionais/    # ★ Saída principal — projeções SSP + PDFs
│   └── projecoes_sem_incremento/ # Projeções contrafactuais (delta = 0)
│
└── src/
    ├── processamento/          # Motor de modelagem (log-linear + ML)
    ├── analises/               # Regressão, ENSO, análise global
    ├── mapas/                  # Scripts de visualização geoespacial
    ├── relatorios/             # Geração de relatórios PDF (ABNT)
    ├── validacao/              # Integridade de dados e mapas
    ├── pipeline.py             # Orquestrador de análises estatísticas
    └── consolidar_dados.py     # Consolidação do painel base
```

---

## 🚀 Como Executar

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Ordem de execução obrigatória

```bash
# Passo 0 — Consolida dados brutos → data/processed/dados_consolidados.csv
python main.py process-data

# Passo 1 — Gera csvs_latitude (dengue por faixa)
python src/processamento/processar_dengue_latitude_mapas.py

# Passo 2 — Gera csvs_latitude (clima por faixa)  [depende do passo 1]
python src/processamento/processar_clima_por_latitude.py

# Passo 3 — Motor principal: projeções SSP + ML + PDFs
python main.py run-model

# Passo 4 (opcional) — Projeções sem incremento (cenário neutro)
python src/processamento/motor_lote_modelagem_v2_sem_incremento.py
```

> **Nota:** Os passos 1 e 2 são pré-requisitos do motor principal. O motor detecta automaticamente se `output/csvs_latitude/` está populado e usa essa fonte canônica (1.190 municípios com coordenadas) em vez dos arquivos raw em formato wide.

### 3. Validação dos outputs

Após a execução, verifique se estes arquivos foram gerados:

| Passo | Arquivo de validação | Resultado esperado |
|---|---|---|
| 0 | `data/processed/dados_consolidados.csv` | 121 linhas, 20 colunas |
| 1 | `output/csvs_latitude/dengue_faixa_latitude_*.csv` | 8 arquivos por faixa de latitude |
| 2 | `output/medias_latitude/todas_faixas_medias_mensais.csv` | Médias consolidadas |
| 3 | `output/projecoes_regionais/relatorio_executivo_completo.pdf` | Relatório com gráficos |
| 3 | `output/projecoes_regionais/ml_completo/metricas_ml_completo.json` | Métricas do ML |

---

## 📊 Principais Outputs

### Projeções com SSP (`output/projecoes_regionais/`)

| Arquivo | Conteúdo |
|---|---|
| `projecao_regiao_sul_consolidado.csv` | Projeção anual regional (4 cenários × 16 anos) |
| `projecao_latitude_-24.0a-22.6.csv` | Projeção por faixa de latitude (8 arquivos) |
| `previsao_ml_2025_municipios.csv` | Previsão ML 2025 por município (com/sem SSP) |
| `previsao_ml_2025_regional.csv` | Previsão ML 2025 consolidada regional |
| `ml_completo/` | Backtest, métricas e projeção recursiva mensal |
| `relatorio_graficos_por_latitude.pdf` | Visão visual: histórico + projeção por faixa |
| `relatorio_executivo_completo.pdf` | Relatório executivo com metodologia e resultados |

### Projeções sem incremento (`output/projecoes_sem_incremento/`)

| Arquivo | Conteúdo |
|---|---|
| `projecao_regiao_sul_sem_incremento_2025_2040.csv` | Cenário neutro regional |
| `comparacao_sem_incremento_vs_ssp.txt` | Diferença percentual vs cenários SSP |
| `relatorio_graficos_sem_incremento.pdf` | PDF visual — cenário baseline |

---

## 🔬 Metodologia Resumida

```
Dados Históricos (2015–2024)
    ↓ dengue mensal + temp + prec + ENSO (por município)
    ↓ lag-3 meses aplicado em todas variáveis climáticas
    ↓
Modelo Log-Linear Local (por município)
    intercepto α treinado por mediana dos resíduos históricos
    ↓
Projeção 2025–2040
    climatologia histórica + delta SSP acumulado (linear)
    continuidade controlada 2024→2025 (floor 75%)
    faixa de incerteza simétrica crescente (6–16%)
    ↓
Modelo ML (HistGradientBoosting)
    features: temp, prec, ENSO, lat, sazonalidade, lags 1-3
    split temporal: treino ≤2021 | val 2022 | test 2023–2024
    projeção recursiva mensal 2025–2040
```

---

## 📋 Dependências

```
pandas · geopandas · numpy · scipy · statsmodels · scikit-learn
matplotlib · seaborn · Pillow · openpyxl · shapely · pyproj · geobr
```

---

## 📄 Documentação

| Documento | Link |
|---|---|
| Guia de execução | [docs/guia_execucao.md](docs/guia_execucao.md) |
| Guia de interpretação | [docs/guia_interpretacao.md](docs/guia_interpretacao.md) |
| Relatório executivo | [output/projecoes_regionais/relatorio_executivo_completo.pdf](output/projecoes_regionais/relatorio_executivo_completo.pdf) |
| Relatório técnico ABNT (SSP) | [output/projecoes_regionais/relatorio_tecnico_abnt_projecoes_ssp.pdf](output/projecoes_regionais/relatorio_tecnico_abnt_projecoes_ssp.pdf) |
| Relatório técnico ABNT (sem SSP) | [output/projecoes_sem_incremento/relatorio_tecnico_abnt_sem_incremento.pdf](output/projecoes_sem_incremento/relatorio_tecnico_abnt_sem_incremento.pdf) |

---

<div align="center">

**Projeto de pesquisa aplicada em saúde pública e climatologia**  
Dados: SINAN / INMET / NOAA · Período: 2015–2040 · Região Sul do Brasil

</div>


Projeto de modelagem climatico-epidemiologica para antecipar risco de dengue na Regiao Sul do Brasil, com leitura territorial por latitude e projecoes anuais ate 2040.

## Visao do projeto

Este repositorio foi organizado para funcionar como uma documentacao tecnica viva: codigo, dados processados, relatorios e graficos conversam entre si.

Pergunta central:

Como transformar sinais climaticos em evidencia acionavel para vigilancia de dengue antes do pico epidemiologico?

## O que o projeto entrega

1. Historico consolidado de incidentes (2015-2024).
2. Projecoes anuais para 2025-2040 em quatro cenarios SSP.
3. Leitura regional e por 8 faixas de latitude.
4. Previsao especifica de 2025 por ML (com e sem incremento SSP).
5. Relatorios em PDF com narrativa, graficos e implicacoes para decisao.

## Leitura recomendada (ordem)

1. [docs/guia_execucao.md](docs/guia_execucao.md)
2. [output/projecoes_regionais/relatorio_graficos_por_latitude.pdf](output/projecoes_regionais/relatorio_graficos_por_latitude.pdf)
3. [output/projecoes_regionais/relatorio_executivo_completo.pdf](output/projecoes_regionais/relatorio_executivo_completo.pdf)
4. [docs/guia_interpretacao.md](docs/guia_interpretacao.md)

## Como executar

1. Instale dependencias.

```bash
pip install -r requirements.txt
```

2. Execute o motor principal.

```bash
python src/processamento/motor_lote_modelagem_v2_por_latitude.py
```

3. Consulte as saidas em output/projecoes_regionais.

## Metodo em uma pagina

O motor integra dengue mensal, temperatura, precipitacao e ENSO em um painel unico por municipio.

Modelo base:

```text
log(Y + 1) = alpha_local
             + beta_temp * Temp_lag3
             + beta_prec * Prec_lag3
             + beta_enso * ENSO_lag3
             + beta_lat  * Latitude
```

Premissas da versao atual:

1. Horizonte de projecao: 2025-2040.
2. Continuidade controlada entre 2024 e 2025.
3. Quatro cenarios: SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5.
4. Faixas de incerteza percentuais, simetricas e visiveis por cenario.
5. Sem ajuste externo de imunidade ou calibracao exogena.

## Estrutura do repositorio

```text
Projeto_Clima_X_Dengue/
├── data/
│   ├── raw/                  # dados primarios (uso interno)
│   ├── processed/            # consolidacoes intermediarias
│   └── geodados/             # caches geoespaciais
├── docs/                     # guias e instrucoes
├── output/                   # produtos finais e analiticos
└── src/
    ├── processamento/        # motor de modelagem
    ├── analises/             # analises estatisticas
    ├── mapas/                # mapas e visualizacoes
    ├── relatorios/           # componentes de relatorios
    ├── validacao/            # verificacoes de qualidade
    ├── consolidar_dados.py
    └── pipeline.py
```

## Arquivos principais de saida

1. output/projecoes_regionais/projecao_regiao_sul_consolidado.csv
2. output/projecoes_regionais/projecao_latitude_*.csv
3. output/projecoes_regionais/previsao_ml_2025_municipios.csv
4. output/projecoes_regionais/previsao_ml_2025_regional.csv
5. output/projecoes_regionais/relatorio_graficos_por_latitude.pdf
6. output/projecoes_regionais/relatorio_executivo_completo.pdf

## Interpretando os dois PDFs

1. relatorio_graficos_por_latitude.pdf
Panorama visual: historico a esquerda, projecao a direita, por faixa de latitude e no consolidado.

2. relatorio_executivo_completo.pdf
Narrativa completa: contexto, metodo, leitura guiada dos graficos, conclusoes e limites da versao.

## Impacto pratico esperado

1. Melhor antecipacao de risco epidemiologico.
2. Prioriza recursos de vigilancia por territorio.
3. Apoia decisao com transparencia metodologica.
4. Facilita comunicacao entre area tecnica e gestao.

## Governanca dos dados

Publicacao seletiva para proteger dados sensiveis:

1. Dados brutos nao sao publicados.
2. Intermediarios pesados permanecem fora do versionamento publico.
3. Codigo, documentacao e relatorios finais sao priorizados.

