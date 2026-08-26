# 📊 Mapas de Faixas de Latitude - Incidência de Dengue

## Descrição
Este documento descreve o script `gerar_mapas_faixas_latitude.py`, que gera mapas de barras horizontais mostrando a incidência média de dengue por faixa de latitude na região Sul do Brasil.

## 🎯 Objetivo
Criar visualizações anuais (2015-2023) que mostrem como a incidência de dengue varia entre diferentes faixas de latitude, facilitando a identificação de padrões geográficos da doença.

## 📁 Estrutura de Arquivos

### Entrada
- **Localização**: `output/csvs_latitude/`
- **Arquivos**: `dengue_faixa_latitude_1.csv` até `dengue_faixa_latitude_8.csv`
- **Formato**: CSV com colunas:
  - `CODIGO_MUNICIPIO`: Código IBGE do município
  - `ANO`: Ano do registro
  - `MES`: Mês do registro
  - `CASOS_DENGUE`: Número de casos
  - `NOME_MUNICIPIO`: Nome do município
  - `LATITUDE`: Latitude do centroide do município
  - `LONGITUDE`: Longitude do centroide do município
  - `FAIXA_LATITUDE`: Número da faixa (1-8)
  - `CLASSIFICACAO_VISUAL`: Classificação textual da incidência

### Saída
- **Localização**: `output/mapas_latitude/`
- **Arquivos**: `mapa_faixas_latitude_YYYY.png` (onde YYYY = 2015 a 2023)
- **Formato**: PNG de alta resolução (300 DPI)

## 🗺️ Faixas de Latitude

O mapa divide a região Sul em 8 faixas horizontais:

| Faixa | Intervalo de Latitude | Descrição |
|-------|----------------------|-----------|
| 1 | 22.0°S – 23.0°S | Norte do Paraná |
| 2 | 23.0°S – 24.0°S | Centro-Norte do Paraná |
| 3 | 24.0°S – 25.5°S | Centro do Paraná |
| 4 | 25.5°S – 27.0°S | Sul do Paraná / Norte de SC |
| 5 | 27.0°S – 28.0°S | Norte de Santa Catarina |
| 6 | 28.0°S – 29.5°S | Centro de Santa Catarina |
| 7 | 29.5°S – 31.0°S | Sul de SC / Norte do RS |
| 8 | 31.0°S – 34.0°S | Centro e Sul do RS |

## 🎨 Classificação de Cores

A incidência é classificada em 5 categorias com cores distintas:

| Categoria | Cor | Descrição |
|-----------|-----|-----------|
| 0 a 9 | ![#FFFFCC](https://via.placeholder.com/15/FFFFCC/000000?text=+) Amarelo claro | Incidência muito baixa |
| 10 a 99 | ![#FFEDA0](https://via.placeholder.com/15/FFEDA0/000000?text=+) Amarelo | Incidência baixa |
| 100 a 299 | ![#FEB24C](https://via.placeholder.com/15/FEB24C/000000?text=+) Laranja | Incidência média |
| 300 a 599 | ![#F03B20](https://via.placeholder.com/15/F03B20/000000?text=+) Vermelho | Incidência alta |
| > 600 | ![#BD0026](https://via.placeholder.com/15/BD0026/000000?text=+) Vermelho escuro | Incidência muito alta |

## 🚀 Como Executar

### Pré-requisitos
```bash
# Bibliotecas necessárias
pip install pandas matplotlib numpy
```

### Execução
```powershell
# Navegar até a pasta do projeto
cd "c:\Users\ruiga\OneDrive\Documents\Projeto fernando"

# Executar o script
python scripts\gerar_mapas_faixas_latitude.py
```

### Resultado Esperado
```
================================================================================
GERAÇÃO DE MAPAS DE FAIXAS DE LATITUDE - INCIDÊNCIA DE DENGUE
================================================================================

[INFO] Verificando arquivos de entrada...
    ✓ dengue_faixa_latitude_1.csv
    ✓ dengue_faixa_latitude_2.csv
    ...
    Total de arquivos encontrados: 8/8

[PROCESSAMENTO] Gerando mapas por ano...

[2015] Gerando mapa de faixas de latitude...
    ✓ Mapa salvo: mapa_faixas_latitude_2015.png
    → Total de casos: 51,454
    → Municípios: 1190
    → Média geral: 43.24
...

✅ PROCESSAMENTO CONCLUÍDO!
```

## 📊 Informações nos Mapas

Cada mapa gerado contém:

1. **Título**: "Incidência de Dengue por Faixa de Latitude - Ano YYYY"
2. **Barras horizontais**: Uma barra por faixa de latitude
3. **Cores**: Baseadas na classificação de incidência
4. **Valores**: Média de casos por 100 mil habitantes em cada barra
5. **Legenda**: Classificação de cores e suas respectivas categorias
6. **Informações adicionais**:
   - Total de casos no ano
   - Número de municípios analisados
   - Fonte dos dados (DATASUS)
   - Elaboração (NEDE/UFSM)

## 🔍 Metodologia

### Cálculo da Média por Faixa
Para cada faixa de latitude em cada ano:

1. **Agregação**: Soma-se todos os casos de cada município ao longo do ano
2. **Média**: Calcula-se a média aritmética dos casos de todos os municípios da faixa
3. **Classificação**: A média é classificada segundo as 5 categorias de incidência
4. **Visualização**: Uma barra horizontal colorida representa a média calculada

### Fórmula
```
Média_Faixa = Σ(Casos_Município) / N_Municípios
```

Onde:
- `Casos_Município`: Soma anual de casos em cada município
- `N_Municípios`: Número de municípios na faixa de latitude

## 📈 Análise dos Resultados (2015-2023)

### Tendências Observadas

| Ano | Total de Casos | Média Geral | Destaque |
|-----|----------------|-------------|----------|
| 2015 | 51,454 | 43.24 | Ano moderado |
| 2016 | 71,247 | 59.87 | Aumento significativo |
| 2017 | 2,588 | 2.17 | Queda drástica |
| 2018 | 1,737 | 1.46 | Ano de menor incidência |
| 2019 | 47,893 | 40.25 | Retorno a níveis moderados |
| 2020 | 277,809 | 233.45 | Pico significativo |
| 2021 | 65,108 | 54.71 | Redução pós-pico |
| 2022 | 309,849 | 260.38 | **Maior incidência** |
| 2023 | 389,117 | 326.99 | **Recorde histórico** |

### Padrões Identificados
- **Ciclicidade**: Alternância entre anos de alta e baixa incidência
- **Tendência**: Aumento geral nos últimos anos (2020-2023)
- **Geografia**: Faixas mais ao norte (1-3) tendem a ter maior incidência

## 🛠️ Manutenção e Atualizações

### Para adicionar novos anos:
1. Certifique-se de que os arquivos CSV por faixa existam
2. Modifique a linha no script:
   ```python
   for ano in range(2015, 2024):  # Alterar 2024 para o próximo ano
   ```
3. Execute o script novamente

### Personalização de cores:
Edite a variável `CLASSIFICACAO_CORES` no script:
```python
CLASSIFICACAO_CORES = [
    {"min": 0, "max": 10, "cor": "#FFFFCC", "label": "0 a 9"},
    # ... adicionar ou modificar categorias
]
```

### Ajuste de faixas de latitude:
Edite a variável `FAIXAS_LATITUDE` no script:
```python
FAIXAS_LATITUDE = [
    {"num": 1, "min": 22.0, "max": 23.0, "label": "Faixa 1: 22.0°S – 23.0°S"},
    # ... adicionar ou modificar faixas
]
```

## ❓ Resolução de Problemas

### Erro: "Nenhum arquivo CSV encontrado"
**Causa**: Os arquivos `dengue_faixa_latitude_X.csv` não estão na pasta `output/csvs_latitude/`

**Solução**: Execute primeiro o script `processar_dengue_latitude_mapas.py` para gerar os CSVs

### Erro: "Nenhum dado encontrado para YYYY"
**Causa**: O arquivo CSV não contém dados para o ano especificado

**Solução**: Verifique se os dados originais em `Dados/dengue_MENSAL.csv` incluem o ano desejado

### Mapas com barras muito pequenas
**Causa**: Valores de incidência muito baixos em todos os municípios

**Solução**: Este é um comportamento esperado em anos de baixa incidência (ex: 2017, 2018)

## 📚 Referências

- **Fonte dos dados**: DATASUS (Ministério da Saúde)
- **Elaboração**: NEDE/UFSM (Núcleo de Estudos de Doenças Emergentes - Universidade Federal de Santa Maria)
- **Região analisada**: Estados do Sul do Brasil (PR, SC, RS)
- **Período**: 2015-2023

## 📝 Notas Técnicas

- **Resolução dos mapas**: 300 DPI (adequado para publicações)
- **Formato de saída**: PNG com fundo branco
- **Tamanho da figura**: 12x8 polegadas (30.48 x 20.32 cm)
- **Sistema de coordenadas**: Latitude/Longitude (WGS84)

## 🔄 Histórico de Versões

| Versão | Data | Descrição |
|--------|------|-----------|
| 1.0 | 2025-01-03 | Versão inicial do script - mapas 2015-2023 |

---

**Última atualização**: 03 de janeiro de 2025
**Responsável**: Análise de Dados - Projeto Fernando
