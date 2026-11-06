---
title: Prodígia — Dengue e Chikungunya no Sul
emoji: 🦟
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
short_description: Previsão de 1–3 meses e cenários de dengue e chikungunya (PR, SC, RS)
---

# Prodígia

Aplicação de demonstração do projeto [Clima × Arboviroses](https://github.com/ruigabriel1/Projeto_Clima_X_Dengue):
previsão de risco e de casos de dengue e chikungunya, de 1 a 3 meses à frente, para os 1.190 municípios da Região Sul,
com a margem de erro e o desempenho real do modelo no teste prospectivo de 2026.

- **Previsão por mês:** casos previstos com intervalo de 90% e risco relativo ao padrão da própria cidade.
- **Ranking de risco:** cidades com maior probabilidade de ficar acima do seu padrão no próximo mês.
- **Próximos 5 anos:** faixa histórica por mês e cenário de aquecimento (+1/+2 °C) pelo DLNM. Cenário, não previsão.
- **Quão confiável é:** comparação honesta com a persistência e com o alerta oficial do InfoDengue.

API em `/docs`. Dados: InfoDengue, Open-Meteo, IBGE. Modelo: XGBoost Poisson com calibração isotônica.
