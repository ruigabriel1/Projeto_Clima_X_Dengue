# Projeto Clima x Dengue

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

