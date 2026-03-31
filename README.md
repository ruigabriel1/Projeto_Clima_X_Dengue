# Projeto Clima x Dengue

Plataforma de analise clima-saude para apoiar projecoes de dengue na Regiao Sul do Brasil.

O projeto combina epidemiologia, estatistica e geoprocessamento para transformar dados climaticos e de dengue em informacao acionavel para vigilancia, planejamento e tomada de decisao.

## Por que este projeto importa

A dengue nao depende apenas de um fator isolado. Temperatura, chuva e variabilidade climatica em grande escala (ENSO) alteram o risco de transmissao ao longo do tempo e entre territorios.

Este repositorio foi construido para responder a uma pergunta pratica:

Como antecipar cenarios de risco de dengue com base em sinais climaticos e historico epidemiologico?

## Ideia geral

O fluxo central do projeto e:

1. consolidar e validar dados historicos de dengue e clima;
2. gerar recortes por latitude e analises estatisticas;
3. produzir mapas e relatorios tecnicos;
4. projetar cenarios futuros (2026 a 2040) com base em SSPs do AR6.

Principais entradas analiticas:

- dengue mensal por municipio;
- temperatura (maxima, media e minima);
- precipitacao;
- indice ENSO (El Nino/La Nina/Neutro).

## Como o projeto agrega para a sociedade

Este trabalho busca gerar valor publico em quatro frentes:

1. Saude publica preventiva: antecipa janelas de maior risco para apoiar vigilancia e resposta precoce.
2. Gestao de recursos: ajuda a priorizar equipes, insumos e comunicacao em periodos mais criticos.
3. Planejamento territorial: identifica diferencas regionais por latitude e por municipio, reduzindo decisoes genericas.
4. Transparencia tecnica: organiza um pipeline reproduzivel com documentacao, metodos explicitos e relatorios interpretaveis.

Em resumo, a proposta e reduzir tempo de reacao e melhorar a qualidade da decisao publica frente a surtos de dengue.

## Escopo tecnico

- horizonte de projecao: 2026 a 2040;
- cenarios climaticos: SSP1-2.6, SSP2-4.5, SSP3-7.0, SSP5-8.5;
- recorte espacial: Regiao Sul do Brasil, com consolidado regional e faixas de latitude;
- produtos finais: relatorios PDF, tabelas consolidadas e mapas tematicos.

## Estrutura do repositorio

```text
Projeto_Clima_X_Dengue/
├── data/
│   ├── raw/                  # dados primarios (privados)
│   ├── processed/            # bases intermediarias consolidadas
│   └── geodados/             # cache geoespacial
├── docs/                     # guias de execucao e interpretacao
├── output/                   # resultados gerados pelo pipeline
└── src/
    ├── analises/             # analises estatisticas e relatorios
    ├── mapas/                # geracao de mapas e paineis
    ├── processamento/        # preparo e transformacoes de dados
    ├── relatorios/           # montagens de relatorios
    ├── validacao/            # checagens de consistencia
    ├── consolidar_dados.py
    └── pipeline.py
```

## Scripts principais

- src/processamento/motor_lote_modelagem_v2_por_latitude.py
- src/processamento/motor_lote_modelagem_clima_saude.py
- src/pipeline.py
- src/consolidar_dados.py

## Execucao rapida

1. Instale dependencias:

```bash
pip install -r requirements.txt
```

2. Execute o motor principal de projecoes:

```bash
python src/processamento/motor_lote_modelagem_v2_por_latitude.py
```

3. Opcionalmente, rode a entrada legada:

```bash
python src/processamento/motor_lote_modelagem_clima_saude.py
```

## Metodologia resumida

Modelo de referencia (forma log-linear com lag climatico):

```text
log(Y + 1) = alpha_local
           + beta_temp * Temp_lag3
           + beta_prec * Prec_lag3
           + beta_enso * ENSO_lag3
           + beta_lat  * Latitude
```

Elementos aplicados no motor:

- intercepto local por municipio;
- lag de 3 meses para variaveis climaticas;
- variabilidade interanual inspirada no historico;
- projecoes com tendencia associada aos cenarios SSP;
- faixas de incerteza nos produtos finais.

## Saidas esperadas

As saidas sao geradas principalmente em output/projecoes_regionais/ e output/analise_estatistica/.

Exemplos:

- projecao_regiao_sul_consolidado.csv
- projecao_latitude_*.csv
- relatorio_graficos_por_latitude.pdf
- relatorio_executivo_completo.pdf
- resumos tecnicos em .txt e .json

## Privacidade e publicacao de dados

Este repositorio adota publicacao seletiva para proteger dados primarios.

- arquivos brutos sensiveis (ex.: CSVs de data/raw/) nao sao publicados;
- CSVs pesados e intermediarios de latitude tambem sao excluidos;
- sao priorizados codigo-fonte, documentacao e relatorios finais.

As regras estao configuradas em .gitignore.

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

Projeto academico de modelagem climatico-epidemiologica com foco em utilidade publica.
