# Plano de Experimento Final — Clima × Arboviroses

> **Pergunta de pesquisa (fixada antes de rodar qualquer coisa):**
> "Variáveis climáticas melhoram a previsão de casos de dengue e chikungunya
> em horizontes de 1, 2 e 3 meses, além do que o histórico de casos já explica?"

> **Produto final:** um modelo empacotado, com API, que receba código IBGE + mês
> e devolva previsão de casos + nível de risco, pronto para uso real.

---

## Fase 0 — Estabilizar (≈ 30 min)

O que está pendente e precisa ser feito antes de qualquer experimento.

- [ ] `git add -A && git commit` — tudo que foi alterado está sem commit
- [ ] Abrir o dashboard no navegador (`python main.py serve`) e confirmar visualmente
- [ ] Verificar sanidade dos dados de clima: pegar 3 cidades aleatórias, plotar temperatura e precipitação mensal, conferir se fazem sentido geográfico
- [ ] Rodar `pytest` uma última vez para garantir que está limpo

> [!CAUTION]
> Sem o commit, qualquer erro apaga semanas de trabalho. Isso é prioridade zero.

---

## Fase 1 — Experimento Controlado (≈ 2–3 horas de execução)

### 1.1 Variáveis do experimento

| Fator | Níveis | Justificativa |
|---|---|---|
| **Horizonte** | 1, 2, 3 meses | Clima age com atraso (ciclo do mosquito: 2–12 semanas) |
| **Clima** | Com vs. Sem variáveis climáticas | Mede o valor agregado real do clima |
| **Corte P99** | Com vs. Sem | Suspeita de que o corte achata surtos e piora R² |
| **Doença** | Dengue, Chikungunya | Zika fica fora (dados insuficientes, tratamento descritivo) |

**Total: 2 × 3 × 2 × 2 = 24 rodadas**, mais os 4 baselines (persistência e sazonal, por doença).

### 1.2 O que muda em cada horizonte

- **Horizonte 1 (atual):** prever os casos do mês seguinte
- **Horizonte 2:** prever os casos de 2 meses à frente — os lags de casos ficam defasados em 2 meses; o clima de 2 meses atrás vira o clima "atual"
- **Horizonte 3:** idem, 3 meses

Na prática, é trocar a variável-alvo: em vez de `casos_t+1`, usar `casos_t+2` e `casos_t+3`.

### 1.3 Métricas (fixadas agora, antes de rodar)

| Métrica | O que mede | Critério de aceitação para uso real |
|---|---|---|
| **MAE** | Erro médio em casos por cidade/mês | Menor que o da persistência |
| **R²** | Variação explicada | > 0,40 para dengue |
| **MAE-surto** | Erro só nos meses acima do percentil 90 | Menor que 50% do pico médio |
| **Skill Score** | (MAE_persistência − MAE_modelo) / MAE_persistência | > 0 (o modelo agrega valor) |
| **Classificação** | Acurácia em "risco alto" (acima da mediana) vs. "risco baixo" | AUC > 0,75 |

> [!IMPORTANT]
> Se nenhuma configuração passar nesses critérios, o resultado é "o clima não agrega valor
> nesse formato de dados". Isso é uma conclusão válida, não um fracasso.

### 1.4 Validação

- **Desenvolvimento:** janela expansiva (expanding window), treina até o ano X, testa no ano X+1, de 2018 a 2024
- **Teste final:** ano 2025, **usado uma única vez**, depois que todas as decisões de modelo estiverem feitas
- A zika **não entra** no experimento. Será descrita no artigo com estatísticas e uma nota sobre insuficiência de dados

### 1.5 Implementação

Criar um script `src/ml_pipeline/experimento_horizontes.py` que:

```
Para cada doença em [dengue, chikungunya]:
    Para cada horizonte em [1, 2, 3]:
        Para cada uso_clima em [True, False]:
            Para cada corte_p99 em [True, False]:
                1. Montar features com o horizonte correto
                2. Treinar com expanding window
                3. Calcular as 5 métricas
                4. Salvar resultado em output/experimento/resultados.csv
    Calcular persistência e sazonal para cada horizonte
```

O CSV final terá 28 linhas (24 modelos + 4 baselines) e será a tabela central do artigo.

---

## Fase 2 — Análise e Decisão (≈ 1 hora)

- [ ] Montar tabela comparativa e identificar a melhor configuração **por doença**
- [ ] Responder: "Em qual horizonte o clima agrega valor?"
  - Se horizonte 1: ótimo, já temos
  - Se horizonte 2 ou 3: a previsão é menos precisa, mas o clima é mais relevante — trade-off honesto
  - Se nenhum: a conclusão do artigo muda para "o histórico de casos domina a previsão de curto prazo"
- [ ] Verificar se remover o corte P99 melhora o R² sem explodir o MAE
- [ ] Gerar SHAP da melhor configuração e confirmar se o clima subiu no ranking

> [!NOTE]
> Aqui **não tem escolha de hiperparâmetros**. O XGBoost Poisson com os parâmetros atuais
> fica fixo. Estamos medindo o efeito do horizonte e do clima, não otimizando o algoritmo.

---

## Fase 3 — Teste Final no Ano 2025 (≈ 30 min)

- [ ] Pegar a configuração escolhida na Fase 2
- [ ] Treinar no painel 2015–2024
- [ ] Testar em 2025
- [ ] Reportar as 5 métricas **sem ajustar nada depois**
- [ ] Se o resultado cair muito em relação à validação, há overfitting na validação — reportar honestamente

---

## Fase 4 — Modelo Final para Produção (≈ 2–3 horas)

### 4.1 Retreinar no painel completo (2015–2025)

Usando a configuração vencedora, treinar o modelo final que vai para produção.

### 4.2 Empacotar

Criar `src/prediction_service/`:

```
prediction_service/
├── __init__.py
├── predictor.py        # Carrega o modelo, recebe dados, devolve previsão
├── risk_classifier.py  # Traduz casos previstos em nível de risco (baixo/médio/alto/crítico)
├── data_fetcher.py     # Busca dados de clima e casos recentes das APIs públicas
└── schemas.py          # Pydantic: entrada e saída da API
```

### 4.3 API de previsão

Endpoint no FastAPI existente:

```
POST /api/predict
{
    "codigo_ibge": "3550308",
    "doenca": "dengue",
    "meses_a_frente": 2
}

→ {
    "cidade": "São Paulo",
    "doenca": "dengue",
    "horizonte_meses": 2,
    "mes_alvo": "2026-01",
    "casos_previstos": 1247,
    "intervalo_confianca": [890, 1580],
    "nivel_risco": "alto",
    "nota": "Modelo validado com MAE X e R² Y no ano 2025"
}
```

### 4.4 Critérios de qualidade para uso real

| Requisito | Detalhe |
|---|---|
| **Aviso de incerteza** | Sempre mostrar intervalo de confiança, nunca só um número |
| **Aviso de limitação** | Se a cidade tem poucos dados ou R² < 0.2, avisar que a previsão é pouco confiável |
| **Atualização** | O modelo precisa ser retreinado a cada 6–12 meses com dados novos |
| **Zika** | Sem previsão. Retorna mensagem explicando que os dados são insuficientes |
| **Fallback** | Se os dados de clima não estiverem disponíveis, usar o modelo sem clima |

---

## Fase 5 — Escrita do Artigo (≈ 1–2 semanas)

### Estrutura sugerida

1. **Introdução:** arboviroses no Brasil, papel do clima, lacuna (poucos estudos com horizontes > 1 mês e comparação honesta com baselines)
2. **Dados:** painel municipal, clima ERA5/CMIP6, limitações da notificação
3. **Metodologia:** XGBoost Poisson, expanding window, baselines, 5 métricas, experimento dos horizontes
4. **Resultados:** tabela das 28 rodadas, SHAP, teste final em 2025
5. **Discussão:** onde o clima ajuda, onde não ajuda, por que a zika não funciona, limitações
6. **Conclusão**

> [!WARNING]
> O artigo **precisa** reportar onde o modelo perde. Se só mostrar os resultados bons,
> é desonesto e enfraquece o trabalho. Mostrar as limitações com honestidade é o que
> diferencia um artigo sério de um exercício escolar.

---

## Cronograma Estimado

| Fase | Tempo | Pode ser automatizada? |
|---|---|---|
| 0 — Estabilizar | 30 min | Parcialmente (commit + pytest) |
| 1 — Experimento | 2–3h de execução | Sim, script roda sozinho |
| 2 — Análise | 1h | Não, requer decisão humana |
| 3 — Teste final | 30 min | Sim |
| 4 — Empacotamento | 2–3h | Sim |
| 5 — Escrita | 1–2 semanas | Não |

**Da Fase 0 à 4, tudo pode ser feito em um dia intenso de trabalho.**

---

## O que NÃO está no plano (e por quê)

| Tentação | Por que não |
|---|---|
| Testar outros algoritmos (Random Forest, LSTM, etc.) | Muda o algoritmo sem antes saber se o dado sustenta a pergunta. O XGBoost Poisson já é adequado. |
| Grid search de hiperparâmetros | Com 24 rodadas e expanding window, a chance de overfitting à validação já existe. Otimizar hiperparâmetros piora isso. |
| Incluir zika | Dados insuficientes. Forçar um modelo é pior que admitir a limitação. |
| Variáveis socioeconômicas | Válido, mas é outro projeto. Este é Clima × Doença. |
| Dados diários | O SINAN é mensal na prática. Fingir resolução diária com dados semanais é fabricar precisão. |
