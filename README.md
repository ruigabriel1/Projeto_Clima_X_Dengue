# Clima × Arboviroses — Dengue e Chikungunya na Região Sul do Brasil

Dados públicos de 1.190 municípios (PR, SC, RS), 2015–2026, usados para responder duas perguntas
**separadas**:

1. **O clima afeta o risco de dengue e chikungunya?** → análise de efeito (DLNM).
2. **O clima ajuda a *prever* esse risco de 1 a 3 meses, além do histórico de casos?** → experimento preditivo
   com protocolo pré-registrado ([docs/PROTOCOLO_V5.md](docs/PROTOCOLO_V5.md)) e teste prospectivo em 2026.

## Resultados principais

**Efeito do clima (DLNM, Poisson condicional, 2015–2025)** — RR acumulado em 0–3 meses, P90 vs. mediana,
controlando sazonalidade de cada cidade e choques interanuais de cada estado:

| | Temperatura (P90 ≈ 24,5 °C) | Precipitação (P90 ≈ 253 mm) |
|---|---|---|
| Dengue | **1,46** [1,07–1,99] | 1,08 [0,94–1,23] |
| Chikungunya | **1,60** [1,04–2,48] | **1,68** [1,36–2,08] |

No caso da dengue, o efeito da temperatura cresce com a defasagem e é máximo em ~3 meses.

**Valor preditivo (XGBoost Poisson, OOF 2018–2024)** — ΔMAE ao acrescentar cada grupo, IC 95% por bootstrap de municípios:

| | Clima parcimonioso (temp. + chuva) | Suscetibilidade (incidência acumulada) |
|---|---|---|
| Dengue | −1,1% (h1), −0,7% (h2), −0,5% n.s. (h3) | −0,9% a −1,0% |
| Chikungunya | sem efeito (n.s. nos 3 horizontes) | −2,7% a −3,5% |

- O clima tem efeito real, mas acrescenta **~1%** à previsão de dengue e **nada** à de chikungunya.
- Na versão anterior (26 variáveis + índice ENSO), o "clima" piorava a dengue em até 8%. Isso era memorização:
  o ENSO é um único valor por mês para todas as cidades e funcionava como "identificador do ano".
- **Alerta de risco** (P(incidência > P75 da própria cidade)): AUC 0,76–0,82, superior ao alerta oficial do
  InfoDengue defasado (0,52–0,68). Para dengue em 1–2 meses, **repetir o último valor (persistência)
  empata ou supera o modelo** — o ganho real do modelo está na chikungunya e no horizonte de 3 meses.
- Teste prospectivo único em jan–ago/2026: ver `docs/resultados_v5/`.

Histórico da versão anterior (teste em 2025): [docs/resultados_experimento/](docs/resultados_experimento/).

## Dados

| Fonte | Conteúdo | Tabela |
|---|---|---|
| InfoDengue (notificações SINAN) | casos mensais de dengue, chikungunya, zika; nível de alerta | `ingestao_saude` |
| Open-Meteo (reanálise ERA5) | temperatura, precipitação e outras variáveis diárias | `ingestao_clima` |
| NOAA | índice ONI (El Niño / La Niña) | `ingestao_enso` |
| IBGE SIDRA | população estimada | `ingestao_populacao` |

O banco `data/processed/dengue_analytics.db` não é versionado. Para criá-lo ou atualizá-lo, rode `python main.py atualizar-dados`
(idempotente; preserva o histórico já usado nas análises).

## Como rodar

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Linux/Mac: .venv/bin/pip

python main.py atualizar-dados          # ingestão incremental (InfoDengue, Open-Meteo, NOAA)
python main.py dlnm                     # efeito do clima → output/dlnm/
python main.py experimento-v5           # clima × suscetibilidade → output/experimento_v5/
python main.py modelo-risco             # benchmark InfoDengue + modelos de alerta
python main.py teste-prospectivo --confirmar   # teste ÚNICO em 2026 (trava após rodar)
python main.py serve                    # dashboard + API em http://localhost:8000 (/docs)

python -m pytest -q                     # testes (dados sintéticos)
```

## API

```http
POST /api/predict
{"codigo_ibge": "4106902", "doenca": "dengue", "meses_a_frente": 2}
```

Resposta (campos principais):
- `probabilidade_risco_alto`: probabilidade calibrada de a incidência do mês-alvo ficar acima do P75 histórico da própria cidade;
- `nivel_risco`: baixo / médio / alto / crítico, derivado da probabilidade;
- `alerta_infodengue_ultimo`: alerta oficial do InfoDengue (1–4) no último mês observado;
- contagem secundária: `casos_previstos` e `intervalo_confianca` (intervalo de 90%);
- `confiabilidade`, `avisos` e `nota`, com as métricas de validação.

A cobertura é a Região Sul (código fora dela → 404). Zika não tem previsão (dados insuficientes).

## Estrutura

```
src/processamento/       ingestão (APIs públicas → SQLite, upsert idempotente)
src/analise_efeito/      DLNM (efeito do clima)
src/ml_pipeline/         features, treino, experimentos, alerta de risco, teste prospectivo
src/prediction_service/  preditor da API
app/                     FastAPI + dashboard
docs/                    protocolo, plano, arquitetura, resultados versionados
tests/                   pytest
```

Regras metodológicas e guia para quem for contribuir: [CLAUDE.md](CLAUDE.md).

## Limitações

- Os casos vêm de notificação: há subnotificação e atraso, principalmente nos meses recentes.
- Clima por centróide municipal (ERA5), não por estação.
- Só ~10 anos de dinâmica interanual: choques comuns (sorotipo, imunidade) dominam a variação entre anos e
  não são observados diretamente.
- O efeito da temperatura ainda cresce no lag 3: a janela de 0–3 meses pré-registrada pode ser curta.
