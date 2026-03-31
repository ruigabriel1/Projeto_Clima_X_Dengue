# Projeto Clima x Dengue

Analise climatico-epidemiologica para apoiar previsao de risco de dengue no Sul do Brasil.

Este projeto conecta dados de clima, ENSO e dengue para transformar historico em inteligencia aplicada a saude publica.

## Visao rapida

- foco territorial: Regiao Sul do Brasil;
- janela historica: 2015 a 2024;
- janela de projecao: 2026 a 2040;
- cenarios climaticos: SSP1-2.6, SSP2-4.5, SSP3-7.0 e SSP5-8.5;
- entregas: mapas, tabelas consolidadas e relatorios tecnicos.

## Problema que o projeto resolve

A dengue varia no tempo e no espaco. Essa variacao e influenciada por fatores climaticos, sazonalidade e eventos como El Nino e La Nina. Sem integracao de dados, o planejamento costuma ser reativo.

Aqui, o objetivo e antecipar sinal de risco com base em evidencias quantitativas para apoiar decisoes antes do pico dos casos.

## Como funciona

O pipeline principal segue este fluxo:

1. consolidar e validar dados epidemiologicos e climaticos;
2. processar recortes por latitude e gerar bases analiticas;
3. executar analises estatisticas e modelagem;
4. projetar cenarios futuros por faixa e consolidado regional;
5. publicar resultados em relatorios e artefatos tecnicos.

Entradas analiticas principais:

- dengue mensal por municipio;
- temperatura maxima, media e minima;
- precipitacao;
- indice ENSO (El Nino, La Nina e Neutro).

## Valor para a sociedade

O projeto foi pensado para gerar utilidade publica real:

1. prevencao: melhora a capacidade de alerta precoce para periodos de maior risco;
2. eficiencia: apoia alocacao de equipes, insumos e campanhas com base em evidencia;
3. foco territorial: mostra diferencas regionais por latitude e por municipio;
4. transparencia: disponibiliza metodo, fluxo e interpretacao de forma reproduzivel.

Resultado esperado: reduzir tempo de resposta e elevar qualidade da tomada de decisao em saude coletiva.

## Estrutura do repositorio

```text
Projeto_Clima_X_Dengue/
├── data/
│   ├── raw/                  # dados primarios (privados)
│   ├── processed/            # bases intermediarias
│   └── geodados/             # cache geoespacial
├── docs/                     # guias e apoio metodologico
├── output/                   # resultados gerados
└── src/
    ├── analises/
    ├── mapas/
    ├── processamento/
    ├── relatorios/
    ├── validacao/
    ├── consolidar_dados.py
    └── pipeline.py
```

## Scripts de referencia

| Script | Papel no fluxo |
|---|---|
| src/processamento/motor_lote_modelagem_v2_por_latitude.py | Motor principal de projecao por latitude |
| src/processamento/motor_lote_modelagem_clima_saude.py | Entrada legada para o motor principal |
| src/consolidar_dados.py | Consolidacao da base historica |
| src/pipeline.py | Pipeline estatistico tradicional |

## Inicio rapido

1. Instalar dependencias

```bash
pip install -r requirements.txt
```

2. Executar o motor principal

```bash
python src/processamento/motor_lote_modelagem_v2_por_latitude.py
```

3. Opcional: executar entrada legada

```bash
python src/processamento/motor_lote_modelagem_clima_saude.py
```

## Metodologia em uma linha

Modelo log-linear com lag climatico de 3 meses e intercepto local por municipio, combinando clima, ENSO e latitude para estimativa de casos.

Forma base:

```text
log(Y + 1) = alpha_local
           + beta_temp * Temp_lag3
           + beta_prec * Prec_lag3
           + beta_enso * ENSO_lag3
           + beta_lat  * Latitude
```

## Saidas principais

Geradas principalmente em output/projecoes_regionais/ e output/analise_estatistica/.

- projecao_regiao_sul_consolidado.csv
- projecao_latitude_*.csv
- relatorio_graficos_por_latitude.pdf
- relatorio_executivo_completo.pdf
- resumos tecnicos em txt e json

## Privacidade e publicacao de dados

Este repositorio adota publicacao seletiva.

- dados primarios sensiveis (por exemplo, CSVs brutos) nao sao publicados;
- CSVs pesados e intermediarios de latitude sao excluidos;
- prioridade de publicacao: codigo, documentacao e relatorios finais.

As regras de exclusao estao em .gitignore.

## Documentacao complementar

- docs/guia_execucao.md
- docs/guia_interpretacao.md
- docs/instrucoes_mapas_latitude.md

## Requisitos

- Python 3.10+
- dependencias listadas em requirements.txt

## Referencias

- Spearman, C. (1904). The proof and measurement of association between two things.
- Mann, H.B.; Whitney, D.R. (1947). On a test of whether one of two random variables is stochastically larger than the other.
- Kruskal, W.H.; Wallis, W.A. (1952). Use of ranks in one-criterion variance analysis.
- Teixeira, T.R.A. et al. (2009). Relationship between dengue and climate factors.
- SciPy stats documentation: https://docs.scipy.org/doc/scipy/reference/stats.html
- GeoPandas documentation: https://geopandas.org

---

Projeto academico com foco em impacto social, vigilancia epidemiologica e apoio a decisao baseada em dados.
