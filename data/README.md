# 📂 Dados do Projeto — Clima × Dengue

> **IMPORTANTE**: Os dados brutos **não estão incluídos neste repositório** por serem dados sensíveis de saúde pública e meteorologia com restrições de distribuição.

## Como obter os dados

Para reproduzir as análises, você precisará coletar os seguintes dados e organizá-los na estrutura abaixo:

### 1. Dados Meteorológicos (INMET)
- **Fonte**: [INMET - BDMEP](https://bdmep.inmet.gov.br/)
- **Arquivos necessários**:
  - `Temp_media_MENSAL.csv` — Temperatura média mensal por município
  - `Temp_minima_MENSAL.csv` — Temperatura mínima mensal por município
  - `Temp_maxima_MENSAL.csv` — Temperatura máxima mensal por município
  - `precipitacao_mensal_rev.csv` — Precipitação acumulada mensal por município
- **Formato**: CSV separado por `;`, formato wide (municípios nas colunas), com 2 linhas de cabeçalho
- **Período**: 2015 a 2024
- **Região**: Municípios da Região Sul (PR, SC, RS)

### 2. Dados Epidemiológicos (DataSUS/SINAN)
- **Fonte**: [DataSUS - SINAN](http://tabnet.datasus.gov.br/)
- **Arquivo necessário**:
  - `dengue_MENSAL.csv` — Incidência mensal de dengue por município
- **Formato**: CSV separado por `;`, formato wide (municípios nas colunas)

### 3. Dados ENSO (NOAA)
- **Fonte**: [NOAA - ONI Index](https://origin.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php)
- **Arquivo necessário**:
  - `elnino_lanina_2015-2024.csv` — Índice Oceânico Niño (ONI) mensal

### 4. Recurso Gráfico
- `R_transparent.png` — Imagem de rosa dos ventos para composição de mapas

## Estrutura esperada

```
data/
├── raw/                          ← Coloque os dados brutos aqui
│   ├── Temp_media_MENSAL.csv
│   ├── Temp_minima_MENSAL.csv
│   ├── Temp_maxima_MENSAL.csv
│   ├── precipitacao_mensal_rev.csv
│   ├── dengue_MENSAL.csv
│   ├── elnino_lanina_2015-2024.csv
│   └── R_transparent.png
├── processed/                    ← Gerado automaticamente pelo pipeline
│   ├── dados_consolidados.csv
│   └── dados_consolidados_log.csv
└── geodados/                     ← Gerado automaticamente pelo cache de geodados
    ├── cache_municipios_sul.gpkg
    ├── cache_estados_brasil.gpkg
    └── cache_paises_vizinhos.gpkg
```
