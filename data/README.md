# Dados

Os dados **não ficam no repositório** porque são grandes (~70 MB) e regeneráveis. Todas as fontes são
**públicas e abertas**, e um único comando monta o banco local:

```bash
python main.py atualizar-dados          # cria/atualiza data/processed/dengue_analytics.db
```

A atualização é idempotente (upsert por município × ano × mês), retoma de onde parou se a internet cair
e nunca sobrescreve meses antigos já usados nas análises.

## Fontes

| Fonte | O que vem | Tabela | Acesso |
|---|---|---|---|
| [InfoDengue](https://info.dengue.mat.br/services/api) (Fiocruz/FGV) | Casos mensais de dengue, chikungunya e zika notificados ao SINAN; nível de alerta oficial | `ingestao_saude` | API pública |
| [Open-Meteo](https://open-meteo.com/en/docs/historical-weather-api) (reanálise ERA5) | Temperatura, precipitação, vento e temperatura do solo no centróide de cada município | `ingestao_clima` | API pública (tem limite por hora; o robô espera e continua) |
| [NOAA CPC](https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt) | Índice ONI (El Niño / La Niña) | `ingestao_enso` | Arquivo público |
| [IBGE SIDRA](https://apisidra.ibge.gov.br/) (tabela 6579) | População estimada por município | `ingestao_populacao` | API pública |

## Cobertura atual

- 1.190 municípios de PR, SC e RS, mensal, de janeiro/2015 até o último mês fechado.
- 2015–2025 completo e conferido contra a fonte (totais idênticos ao InfoDengue em novembro/2026).
- Zika só tem dados até o início de 2024 na fonte, por isso não é modelada.

## Estrutura

```
data/
├── processed/dengue_analytics.db   banco SQLite (gerado; fora do git)
└── geodados/                        malha municipal em cache (gerada; fora do git)
```

Os casos são notificações: há subnotificação e atraso, principalmente nos meses mais recentes. Por isso a
API de previsão ignora meses ingeridos menos de 28 dias após o fim do mês.
