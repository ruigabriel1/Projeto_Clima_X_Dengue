# Projeto Clima x Dengue

Modelagem climatico-epidemiologica para projecao de casos de dengue na Regiao Sul do Brasil, com foco em:

- projecoes anuais de 2026 a 2040;
- cenarios SSP do AR6 (SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5);
- saidas agregadas por faixas de latitude e consolidado regional;
- relatorios PDF com series historicas e curvas projetadas.

## Visao Geral

O projeto integra dados de:

- dengue mensal por municipio;
- temperatura media mensal;
- precipitacao mensal;
- indice ENSO (El Nino/La Nina).

O motor principal estima interceptos locais por municipio e aplica uma formulacao log-linear com lag climatico de 3 meses para projetar os casos futuros.

## Arquivos Principais

- `src/processamento/motor_lote_modelagem_v2_por_latitude.py`: motor principal atual.
- `src/processamento/motor_lote_modelagem_clima_saude.py`: entrada legada que redireciona para o motor V2.
- `src/pipeline.py`: pipeline estatistico tradicional do projeto.
- `src/consolidar_dados.py`: consolidacao dos dados historicos.

## Estrutura Essencial

```text
Projeto_Clima_X_Dengue/
├── data/
│   ├── raw/                 # CSVs originais (dengue, clima e ENSO)
│   ├── processed/           # bases consolidadas
│   └── geodados/            # caches geograficos
├── src/
│   ├── processamento/
│   │   ├── motor_lote_modelagem_v2_por_latitude.py
│   │   └── motor_lote_modelagem_clima_saude.py
│   ├── pipeline.py
│   └── consolidar_dados.py
├── docs/
└── output/
    ├── projecoes_regionais/
    ├── analise_estatistica/
    ├── mapas/
    ├── mapas_latitude/
    └── csvs_latitude/
```

## Como Executar

### 1) Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2) Rodar o motor principal de projecoes

```bash
python src/processamento/motor_lote_modelagem_v2_por_latitude.py
```

### 3) (Opcional) Rodar via entrada legada

```bash
python src/processamento/motor_lote_modelagem_clima_saude.py
```

## Saidas do Motor V2

As saidas sao gravadas em `output/projecoes_regionais/`:

- `projecao_latitude_*.csv`: projecoes anualizadas por faixa de latitude e cenario.
- `projecao_regiao_sul_consolidado.csv`: projecao consolidada da Regiao Sul.
- `calibracao_regional.json`: parametros de calibracao/controle do motor.
- `relatorio_graficos_por_latitude.pdf`: graficos historicos e projetados por faixa.
- `relatorio_executivo_completo.pdf`: relatorio executivo com metodologia e conclusoes.

## Metodologia Resumida

Modelo base:

```text
log(Y + 1) = alpha_local
           + beta_temp * Temp_lag3
           + beta_prec * Prec_lag3
           + beta_enso * ENSO_lag3
           + beta_lat  * Latitude
```

Comportamentos implementados no V2:

- variabilidade interanual tipo serrilhado (templates historicos);
- tendencia de crescimento conforme deltas anuais dos cenarios SSP;
- faixa de incerteza crescente nos graficos;
- saida em casos absolutos (com eixo em milhoes nos PDFs).

## Fluxo Recomendado

```text
1. Validar estrutura dos dados em data/raw
2. Executar motor_lote_modelagem_v2_por_latitude.py
3. Revisar CSVs e PDFs em output/projecoes_regionais
4. Interpretar resultados com apoio dos guias em docs/
```

## Requisitos

- Python 3.10+
- Dependencias em `requirements.txt`

## Documentacao de Apoio

- `docs/guia_execucao.md`
- `docs/guia_interpretacao.md`
- `docs/instrucoes_mapas_latitude.md`

## Observacoes

- O repositorio ignora saidas pesadas via `.gitignore` (como pastas de output).
- Para reproducao consistente, mantenha os arquivos de `data/raw` inalterados.

## Referências

- **Spearman, C. (1904).** The proof and measurement of association between two things. *American Journal of Psychology*.
- **Mann, H.B., & Whitney, D.R. (1947).** On a test of whether one of two random variables is stochastically larger than the other. *Annals of Mathematical Statistics*.
- **Kruskal, W.H., & Wallis, W.A. (1952).** Use of ranks in one-criterion variance analysis. *Journal of the American Statistical Association*.
- **Teixeira, T.R.A., et al. (2009).** Relationship between dengue and climate factors. *Revista de Saúde Pública*.
- **SciPy Documentation:** https://docs.scipy.org/doc/scipy/reference/stats.html
- **GeoPandas Documentation:** https://geopandas.org

---

*Projeto acadêmico — análise epidemiológica e climática — Sul do Brasil, 2015–2024.*
