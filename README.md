# Clima × Arboviroses — Previsão de Dengue e Chikungunya na Região Sul

Projeto de Machine Learning que prevê casos mensais de **dengue e chikungunya** nos
**1.190 municípios da Região Sul** (PR, SC, RS) com 1, 2 e 3 meses de antecedência, a partir do
histórico de casos e de variáveis climáticas, e serve a previsão por uma API.

**Pergunta de pesquisa:** *"Variáveis climáticas melhoram a previsão de casos de dengue e
chikungunya em horizontes de 1, 2 e 3 meses, além do que o histórico de casos já explica?"*

Plano completo do experimento: [docs/PLANO_EXPERIMENTO_FINAL.md](docs/PLANO_EXPERIMENTO_FINAL.md).

## Dados

| Fonte | O que fornece | Tabela no SQLite |
|---|---|---|
| **InfoDengue** (notificações SINAN) | Casos mensais de dengue, chikungunya e zika por município; umidade; receptividade | `ingestao_saude` |
| **Open-Meteo** (reanálise ERA5) | Temperatura média/mín/máx, precipitação, vento, temperatura do solo | `ingestao_clima` |
| **NOAA** | Índice ONI (El Niño / La Niña) | `ingestao_enso` |
| **IBGE SIDRA** | População estimada por município | `ingestao_populacao` |

Painel: 1.190 municípios × 132 meses (2015–2025). Banco em `data/processed/dengue_analytics.db`
(não versionado; gerado pelos robôs em `src/processamento/`).

## Metodologia (resumo)

- **Modelo:** XGBoost com objetivo Poisson e hiperparâmetros **fixos** (sem grid search).
- **Features:** lags e médias móveis de casos (a partir de t−h), sazonalidade, incidência da faixa
  de latitude, população, e — na variante "com clima" — lags de temperatura, chuva, umidade,
  graus-dia, anomalias, ENSO e receptividade.
- **Experimento:** doença (2) × horizonte (3) × clima (com/sem) × corte P99 (com/sem) = 24 modelos,
  mais baselines de persistência (casos[t−h]) e sazonal (casos[t−12]).
- **Validação:** expanding window com folds de teste 2018–2024. **2025 é holdout**, usado uma única vez.
- **Métricas (fixadas antes):** MAE, R², MAE-surto, Skill Score vs. persistência, AUC de "risco alto".

## Como rodar

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt     # Windows (Linux/Mac: .venv/bin/pip)

python main.py experimento              # Fase 1 — 24 rodadas + baselines (~4 min)
python main.py analise --diagnostico    # Fase 2 — tabela, efeito do clima, SHAP, config sugerida
python main.py teste-final --confirmar  # Fase 3 — teste ÚNICO em 2025 (trava após rodar)
python main.py modelo-final             # Fase 4 — retreino 2015–2025 para produção
python main.py serve                    # Dashboard + API em http://localhost:8000 (docs em /docs)

python -m pytest -q                     # testes (dados sintéticos, não precisam do banco)
```

Saídas do experimento em `output/experimento/` (`resultados.csv`, `analise.md`, `teste_final_2025.md`).

## API de previsão

```http
POST /api/predict
{"codigo_ibge": "4106902", "doenca": "dengue", "meses_a_frente": 2}
```

```json
{
  "cidade": "Curitiba", "doenca": "dengue", "horizonte_meses": 2,
  "mes_alvo": "2026-02", "ultimo_mes_observado": "2025-12",
  "casos_previstos": 812, "intervalo_confianca": [140, 4630],
  "nivel_risco": "alto", "confiabilidade": "normal",
  "avisos": ["Os meses mais recentes ... podem estar incompletos (atraso de notificação) ..."],
  "nota": "Modelo validado no ano de 2025 (teste único): MAE ..., R² ..."
}
```
*(valores ilustrativos)*

- Código IBGE de 6 ou 7 dígitos; cobertura: municípios da Região Sul (fora disso → 404).
- `nivel_risco` é **relativo à própria cidade**: baixo ≤ mediana histórica < médio ≤ P75 < alto ≤ P90 < crítico.
- Intervalo de 90% calibrado nos erros fora-da-amostra de 2018–2024.
- Cidades com poucos casos ou R² fora-da-amostra < 0,2 recebem `confiabilidade: "baixa"`.
- Sem dados de clima para os meses necessários → usa o modelo sem clima.
- Zika: sem previsão (dados insuficientes), resposta explicativa.
- `GET /api/modelo/info`: configuração, métricas e prazo de retreino dos modelos carregados.

## Estrutura

```
src/ml_pipeline/        pipeline de ML (ingestão → features → treino → experimento → produção)
src/prediction_service/ preditor, classificador de risco, fonte de dados, schemas da API
src/processamento/      robôs de ingestão das APIs públicas
app/                    FastAPI + dashboard
tests/                  pytest
docs/                   plano do experimento, arquitetura de dados, decisões de modelagem
```

Detalhes de arquitetura e regras metodológicas para quem for contribuir: [CLAUDE.md](CLAUDE.md).

## Limitações conhecidas

- Os casos vêm de notificação (SINAN via InfoDengue): sujeitos a subnotificação e atraso, em
  especial nos meses mais recentes.
- O modelo precisa ser retreinado a cada 6–12 meses com dados novos.
- Zika não é modelada; chikungunya tem poucos surtos no período, então suas métricas são instáveis.
