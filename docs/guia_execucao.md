# GUIA DE EXECUÇÃO DAS ANÁLISES URGENTES

📅 **Prazo:** Terça-feira  
🎯 **Objetivo:** Executar 4 análises específicas de dengue e clima

---

## 📋 TAREFAS CRIADAS

### ✅ Tarefa 1: Mapa de Incidência Total (2015-2024)
**Script:** `scripts/criar_mapa_dengue_agregado_total.py`

**O que faz:**
- Soma a incidência de dengue de todos os anos (2015-2024)
- Cria mapa coroplético no mesmo formato dos mapas existentes
- Identifica os 10 municípios com maior incidência total

**Saídas:**
- 🗺️ PNG: `output/mapas/mapa_dengue_agregado_2015_2024_YYYYMMDD_HHMMSS.png`
- 📊 CSV: `output/mapas/dengue_agregado_2015_2024.csv`
- 📝 Console: Lista dos top 10 municípios

**Como executar:**
```bash
cd "C:\Users\ruiga\OneDrive\Documents\Projeto fernando"
python scripts/criar_mapa_dengue_agregado_total.py
```

---

### ✅ Tarefa 2: Análise Global com Dengue Logaritmado
**Script:** `scripts/analise_global_dengue_log_pdf.py`

**O que faz:**
- Análise global (sem considerar latitude)
- Usa dengue com transformação logarítmica (log10+1)
- Testes estatísticos não-paramétricos
- Correlações com temperatura, precipitação e ONI
- Comparação entre fases ENSO

**Saídas:**
- 📄 PDF: `output/analise_estatistica/analise_global_dengue_log_YYYYMMDD_HHMMSS.pdf`
  - 6 páginas com gráficos e análises
- 📊 CSV: `output/analise_estatistica/dataset_consolidado_global.csv`

**Conteúdo do PDF:**
1. Série temporal de dengue log
2. Distribuições (histograma, boxplot, violin)
3. Matriz de correlação de Spearman
4. Comparação fases ENSO (El Niño vs La Niña vs Neutro)
5. Scatter plots com linhas de tendência
6. Relatório estatístico completo

**Como executar:**
```bash
python scripts/analise_global_dengue_log_pdf.py
```

---

### ✅ Tarefa 3: El Niño vs La Niña por Latitude
**Script:** `scripts/analise_el_nino_la_nina_latitude_pdf.py`

**O que faz:**
- Compara El Niño vs La Niña usando médias mensais por latitude
- **DETERMINA QUAL FENÔMENO INFLUENCIA MAIS A DENGUE**
- Testes Mann-Whitney U e Kruskal-Wallis
- Análise separada para cada faixa de latitude (8 faixas)
- Análise global agregada

**Saídas:**
- 📄 PDF: `output/analise_estatistica/analise_el_nino_la_nina_latitude_YYYYMMDD_HHMMSS.pdf`
  - 6 páginas com análises comparativas
- 📊 CSV: `output/analise_estatistica/dados_enso_latitude_processados.csv`
- 📝 TXT: `output/analise_estatistica/resumo_el_nino_la_nina.txt`

**Conteúdo do PDF:**
1. Série temporal colorida por fase ENSO + índice ONI
2. Boxplots por faixa de latitude
3. Comparação global (boxplot, violin, barras)
4. Heatmap: média de dengue por faixa × fase ENSO
5. Resultados dos testes estatísticos por faixa
6. Relatório final com conclusão de qual fase predomina

**Como executar:**
```bash
python scripts/analise_el_nino_la_nina_latitude_pdf.py
```

---

### ✅ Tarefa 4: Regressão Linear Múltipla
**Script:** `scripts/analise_regressao_multipla_pdf.py`

**O que faz:**
- Regressão linear múltipla com TODAS as variáveis
- Usa médias mensais de:
  - Dengue (log)
  - Temperatura máxima, média e mínima
  - Precipitação
  - ONI (índice ENSO)
  - Latitude
- Análise completa de diagnóstico do modelo

**Saídas:**
- 📄 PDF: `output/analise_estatistica/analise_regressao_multipla_YYYYMMDD_HHMMSS.pdf`
  - 8 páginas com gráficos e tabelas
- 📊 CSV modelagem: `output/analise_estatistica/dados_regressao_multipla.csv`
- 📈 CSV predições: `output/analise_estatistica/predicoes_regressao_multipla.csv`
- 📝 TXT: `output/analise_estatistica/resumo_regressao_multipla.txt`

**Conteúdo do PDF:**
1. Visão geral do modelo (equação, métricas R², RMSE, F-test)
2. Matriz de correlação de Pearson
3. Coeficientes do modelo (com erro padrão e importância)
4. Predições vs Observado (scatter, linha identidade, Q-Q plot)
5. Diagnóstico de resíduos (homocedasticidade, normalidade)
6. Importância das variáveis (gráfico pizza + tabela)
7. Efeitos parciais de cada variável preditora
8. Relatório técnico (objetivo, resultados, limitações)

**Como executar:**
```bash
python scripts/analise_regressao_multipla_pdf.py
```

---

## 🚀 EXECUTAR TODAS AS ANÁLISES DE UMA VEZ

Para executar todas as 4 análises sequencialmente:

```bash
cd "C:\Users\ruiga\OneDrive\Documents\Projeto fernando"

echo "=== TAREFA 1: Mapa Agregado ==="
python scripts/criar_mapa_dengue_agregado_total.py

echo ""
echo "=== TAREFA 2: Análise Global Log ==="
python scripts/analise_global_dengue_log_pdf.py

echo ""
echo "=== TAREFA 3: El Niño vs La Niña ==="
python scripts/analise_el_nino_la_nina_latitude_pdf.py

echo ""
echo "=== TAREFA 4: Regressão Múltipla ==="
python scripts/analise_regressao_multipla_pdf.py

echo ""
echo "✅ TODAS AS ANÁLISES CONCLUÍDAS!"
```

---

## 📦 ARQUIVOS DE SAÍDA ESPERADOS

Após executar todos os scripts, você terá:

### Mapas:
- `output/mapas/mapa_dengue_agregado_2015_2024_*.png`
- `output/mapas/dengue_agregado_2015_2024.csv`

### PDFs (3 relatórios):
- `output/analise_estatistica/analise_global_dengue_log_*.pdf`
- `output/analise_estatistica/analise_el_nino_la_nina_latitude_*.pdf`
- `output/analise_estatistica/analise_regressao_multipla_*.pdf`

### Dados Processados:
- `output/analise_estatistica/dataset_consolidado_global.csv`
- `output/analise_estatistica/dados_enso_latitude_processados.csv`
- `output/analise_estatistica/dados_regressao_multipla.csv`
- `output/analise_estatistica/predicoes_regressao_multipla.csv`

### Resumos Textuais:
- `output/analise_estatistica/resumo_el_nino_la_nina.txt`
- `output/analise_estatistica/resumo_regressao_multipla.txt`

---

## ⚙️ REQUISITOS

Certifique-se de que as bibliotecas Python estão instaladas:

```bash
pip install pandas numpy matplotlib seaborn scipy scikit-learn geopandas
```

---

## 📊 DADOS NECESSÁRIOS

Os scripts utilizam os seguintes arquivos (já existentes):

### Dados de entrada:
- `Dados/dengue_MENSAL.csv` (casos de dengue)
- `Dados/log10+1.csv` (dengue transformado)
- `Dados/Temp_maxima_MENSAL.csv`
- `Dados/Temp_media_MENSAL.csv`
- `Dados/Temp_minima_MENSAL.csv`
- `Dados/precipitacao_mensal_rev.csv`
- `Dados/elnino_lanina_2015-2024.csv` (índice ONI)

### Médias por latitude:
- `output/medias_latitude/todas_faixas_medias_mensais.csv`

### Geoespacial:
- `cache_municipios_sul.gpkg` (para mapas)

---

## 🎯 RESUMO DAS ANÁLISES

| Tarefa | Script | Formato Saída | Tempo Estimado |
|--------|--------|---------------|----------------|
| 1 - Mapa agregado | `criar_mapa_dengue_agregado_total.py` | PNG + CSV | ~1 min |
| 2 - Análise global log | `analise_global_dengue_log_pdf.py` | PDF (6 pgs) | ~2 min |
| 3 - El Niño vs La Niña | `analise_el_nino_la_nina_latitude_pdf.py` | PDF (6 pgs) | ~2 min |
| 4 - Regressão múltipla | `analise_regressao_multipla_pdf.py` | PDF (8 pgs) | ~2 min |
| **TOTAL** | - | **1 mapa + 3 PDFs** | **~7 min** |

---

## ❓ SOLUÇÃO DE PROBLEMAS

### Erro: "Arquivo não encontrado"
- Verifique se está executando no diretório correto
- Confirme que os arquivos de dados existem em `Dados/`

### Erro: "ModuleNotFoundError"
- Instale as dependências: `pip install -r requirements.txt`

### Mapa não aparece
- Verifique se o arquivo `cache_municipios_sul.gpkg` existe
- O script criará o cache automaticamente se não existir

### PDF vazio ou incompleto
- Verifique se há dados suficientes no período 2015-2024
- Confira se o arquivo de médias por latitude foi gerado

---

## 📧 ENTREGA

Para a entrega na terça-feira:

1. ✅ **Tarefa 1:** Enviar o PNG do mapa agregado
2. ✅ **Tarefas 2-4:** Enviar os 3 PDFs gerados

**Tempo total de execução:** ~7 minutos  
**Arquivos para entregar:** 1 PNG + 3 PDFs

---

## ✨ DESTAQUES DOS RESULTADOS

### Tarefa 2:
- Correlações de Spearman entre dengue e clima
- Comparação ENSO com teste Kruskal-Wallis
- Gráficos de distribuição e série temporal

### Tarefa 3:
- **RESPONDE: Qual fenômeno influencia mais (El Niño ou La Niña)?**
- Análise por faixa de latitude
- Testes estatísticos Mann-Whitney U

### Tarefa 4:
- **R²** e coeficientes de cada variável
- Importância relativa de temperatura, precipitação e ONI
- Diagnóstico completo do modelo
- Predições vs valores observados

---

📅 **Gerado em:** 2025  
🔬 **Projeto:** Análise Dengue e Clima - Região Sul do Brasil
