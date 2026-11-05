# Teste prospectivo único — 2026 (meses [1, 2, 3, 4, 5, 6, 7, 8]), executado 2026-11-04 22:52:02

Treino 2015–2025; nada ajustado depois. Risco alto = incidência > P75 da cidade.

> ⚠️ Reexecução forçada: o holdout já tinha sido usado.


## Chikungunya

| h | previsor | MAE | Skill | MAE incid. (mediana cidades) | AUC | Brier skill |
|---|---|---|---|---|---|---|
| 1 | modelo (semclima_susc) | 0.30 | -0.386 | 0.5 | 0.796 | 0.034 |
| 1 | persistência | 0.22 | 0.000 | 0.0 | 0.692 | 0.125 |
| 1 | combinação (peso modelo 0.6) | 0.26 | -0.202 | 0.3 | 0.806 | 0.046 |
| 1 | alerta InfoDengue | — | — | — | 0.543 | — |
| 2 | modelo (semclima_susc) | 0.50 | -0.741 | 0.9 | 0.770 | -0.142 |
| 2 | persistência | 0.29 | 0.000 | 0.0 | 0.683 | 0.101 |
| 2 | combinação (peso modelo 0.9) | 0.48 | -0.645 | 0.8 | 0.773 | -0.052 |
| 2 | alerta InfoDengue | — | — | — | 0.537 | — |
| 3 | modelo (semclima_susc) | 0.68 | -1.081 | 1.2 | 0.741 | -0.296 |
| 3 | persistência | 0.33 | 0.000 | 0.0 | 0.667 | 0.077 |
| 3 | combinação (peso modelo 1.0) | 0.68 | -1.081 | 1.2 | 0.741 | -0.142 |
| 3 | alerta InfoDengue | — | — | — | 0.532 | — |

## Dengue

| h | previsor | MAE | Skill | MAE incid. (mediana cidades) | AUC | Brier skill |
|---|---|---|---|---|---|---|
| 1 | modelo (clima_susc) | 8.41 | -0.461 | 20.1 | 0.727 | -0.006 |
| 1 | persistência | 5.76 | 0.000 | 10.6 | 0.773 | 0.219 |
| 1 | combinação (peso modelo 0.6) | 6.64 | -0.152 | 15.2 | 0.746 | 0.026 |
| 1 | alerta InfoDengue | — | — | — | 0.604 | — |
| 2 | modelo (clima_susc) | 23.13 | -1.659 | 55.6 | 0.695 | -0.118 |
| 2 | persistência | 8.70 | 0.000 | 13.2 | 0.716 | 0.059 |
| 2 | combinação (peso modelo 0.9) | 21.28 | -1.447 | 50.8 | 0.696 | -0.112 |
| 2 | alerta InfoDengue | — | — | — | 0.562 | — |
| 3 | modelo (clima_susc) | 32.96 | -2.052 | 92.3 | 0.618 | -0.261 |
| 3 | persistência | 10.80 | 0.000 | 15.5 | 0.675 | -0.046 |
| 3 | combinação (peso modelo 1.0) | 32.96 | -2.052 | 92.3 | 0.618 | -0.261 |
| 3 | alerta InfoDengue | — | — | — | 0.527 | — |