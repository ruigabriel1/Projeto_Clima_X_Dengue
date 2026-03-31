# Projeto Clima x Dengue

<p align="center">
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" alt="Python 3.10+" />
    <img src="https://img.shields.io/badge/Regiao-Sul%20do%20Brasil-1f7a8c" alt="Regiao Sul do Brasil" />
    <img src="https://img.shields.io/badge/Periodo%20historico-2015--2024-2a9d8f" alt="Periodo historico" />
    <img src="https://img.shields.io/badge/Projecao-2026--2040-e76f51" alt="Projecao 2026 a 2040" />
    <img src="https://img.shields.io/badge/Cenarios-SSP1--2.6%20%7C%20SSP2--4.5%20%7C%20SSP3--7.0%20%7C%20SSP5--8.5-264653" alt="Cenarios SSP" />
</p>

Plataforma de inteligencia climatico-epidemiologica para antecipar risco de dengue no Sul do Brasil.

Este projeto integra clima, ENSO e historico epidemiologico para apoiar vigilancia em saude publica com base em evidencia.

## Resumo executivo

O Projeto Clima x Dengue transforma dados dispersos em informacao orientada a decisao.

Ele foi desenhado para responder uma pergunta central:

Como antecipar periodos e territorios de maior risco de dengue antes do pico dos casos?

## O que voce encontra aqui

- pipeline completo de dados: consolidacao, processamento, validacao, analise e projecao;
- recortes por latitude e consolidado regional;
- mapas e paineis para leitura territorial;
- relatorios tecnicos em formato executivo;
- metodologia reproduzivel com documentacao de apoio.

## Impacto para a sociedade

Este repositorio foi estruturado para gerar valor pratico em saude coletiva:

1. alerta antecipado: identifica janelas de maior risco com base em sinais climaticos;
2. planejamento eficiente: orienta alocacao de equipes, insumos e campanhas;
3. priorizacao territorial: evidencia diferencas entre municipios e faixas de latitude;
4. transparencia tecnica: torna metodo, premissas e resultados auditaveis.

Resultado esperado: reduzir tempo de reacao e melhorar a qualidade das decisoes publicas frente a surtos de dengue.

## Fluxo do projeto

```text
Dados brutos -> Consolidacao -> Processamento por latitude -> Modelagem estatistica
            -> Projecoes 2026-2040 -> Mapas e relatorios -> Apoio a decisao
```

Entradas analiticas utilizadas:

- dengue mensal por municipio;
- temperatura maxima, media e minima;
- precipitacao;
- indice ENSO (El Nino, La Nina e Neutro).

## Arquitetura do repositorio

```text
Projeto_Clima_X_Dengue/
├── data/
│   ├── raw/                  # dados primarios (privados)
│   ├── processed/            # bases intermediarias
│   └── geodados/             # cache geoespacial
├── docs/                     # guias de execucao e interpretacao
├── output/                   # resultados gerados
└── src/
        ├── analises/             # analises estatisticas
        ├── mapas/                # mapas e paineis
        ├── processamento/        # transformacoes e modelagem
        ├── relatorios/           # relatorios finais
        ├── validacao/            # verificacoes de integridade
        ├── consolidar_dados.py
        └── pipeline.py
```

## Scripts chave

| Script | Funcao |
|---|---|
| src/processamento/motor_lote_modelagem_v2_por_latitude.py | Motor principal de projecao por latitude |
| src/processamento/motor_lote_modelagem_clima_saude.py | Entrada legada para o motor principal |
| src/consolidar_dados.py | Consolidacao da base historica |
| src/pipeline.py | Pipeline estatistico tradicional |

## Comece em 3 passos

1. Instale as dependencias

```bash
pip install -r requirements.txt
```

2. Execute o motor principal

```bash
python src/processamento/motor_lote_modelagem_v2_por_latitude.py
```

3. Analise os produtos em output/projecoes_regionais e output/analise_estatistica

## Metodologia resumida

Modelo log-linear com lag climatico de 3 meses e intercepto local por municipio:

```text
log(Y + 1) = alpha_local
                     + beta_temp * Temp_lag3
                     + beta_prec * Prec_lag3
                     + beta_enso * ENSO_lag3
                     + beta_lat  * Latitude
```

## Entregas do projeto

Principais artefatos gerados:

- projecao_regiao_sul_consolidado.csv
- projecao_latitude_*.csv
- relatorio_graficos_por_latitude.pdf
- relatorio_executivo_completo.pdf
- resumos tecnicos em txt e json

## Documentacao

- [Guia de Execucao](docs/guia_execucao.md)
- [Guia de Interpretacao](docs/guia_interpretacao.md)
- [Instrucoes de Mapas por Latitude](docs/instrucoes_mapas_latitude.md)

## Privacidade e governanca dos dados

O projeto adota publicacao seletiva para proteger dados sensiveis.

- dados primarios brutos nao sao publicados;
- CSVs pesados e intermediarios de latitude sao excluidos;
- sao publicados codigo-fonte, documentacao e relatorios finais.

As regras estao definidas no arquivo .gitignore.

## Requisitos

- Python 3.10+
- dependencias em requirements.txt

## Referencias

- Spearman, C. (1904). The proof and measurement of association between two things.
- Mann, H.B.; Whitney, D.R. (1947). On a test of whether one of two random variables is stochastically larger than the other.
- Kruskal, W.H.; Wallis, W.A. (1952). Use of ranks in one-criterion variance analysis.
- Teixeira, T.R.A. et al. (2009). Relationship between dengue and climate factors.
- SciPy stats documentation: https://docs.scipy.org/doc/scipy/reference/stats.html
- GeoPandas documentation: https://geopandas.org

---

Projeto academico com foco em impacto social, vigilancia epidemiologica e decisao baseada em dados.
