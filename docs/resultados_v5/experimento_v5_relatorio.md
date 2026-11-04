# Experimento v5 — clima parcimonioso × suscetibilidade (protocolo v5)

Dev = OOF 2018–2024. 2025 = segunda validação, já vista na v4 (não é teste limpo). Risco alto = incidência > P75 da cidade (treino).


## Dengue

| período | h | modelo | MAE | Skill | MAE incid. (mediana cidades) | AUC | Brier skill |
|---|---|---|---|---|---|---|---|
| dev_2018_2024 | 1 | clima_semsusc | 23.61 | 0.112 | 34.6 | 0.814 | 0.233 |
| dev_2018_2024 | 1 | clima_susc | 23.40 | 0.120 | 34.3 | 0.820 | 0.237 |
| dev_2018_2024 | 1 | persistencia | 26.60 | 0.000 | 48.7 | 0.836 | 0.366 |
| dev_2018_2024 | 1 | semclima_semsusc | 23.99 | 0.098 | 33.7 | 0.806 | 0.215 |
| dev_2018_2024 | 1 | semclima_susc | 23.66 | 0.110 | 34.3 | 0.817 | 0.226 |
| dev_2018_2024 | 2 | clima_semsusc | 27.94 | 0.369 | 45.3 | 0.776 | 0.147 |
| dev_2018_2024 | 2 | clima_susc | 27.67 | 0.375 | 44.8 | 0.780 | 0.153 |
| dev_2018_2024 | 2 | persistencia | 44.30 | 0.000 | 75.1 | 0.777 | 0.211 |
| dev_2018_2024 | 2 | semclima_semsusc | 27.97 | 0.369 | 44.7 | 0.766 | 0.128 |
| dev_2018_2024 | 2 | semclima_susc | 27.88 | 0.371 | 45.8 | 0.776 | 0.136 |
| dev_2018_2024 | 3 | clima_semsusc | 30.46 | 0.446 | 50.8 | 0.747 | 0.094 |
| dev_2018_2024 | 3 | clima_susc | 29.93 | 0.456 | 49.7 | 0.762 | 0.121 |
| dev_2018_2024 | 3 | persistencia | 55.02 | 0.000 | 93.4 | 0.725 | 0.116 |
| dev_2018_2024 | 3 | semclima_semsusc | 30.27 | 0.450 | 51.6 | 0.730 | 0.072 |
| dev_2018_2024 | 3 | semclima_susc | 30.09 | 0.453 | 51.5 | 0.747 | 0.092 |
| validacao_2025_ja_vista | 1 | clima_semsusc | 19.52 | 0.172 | 26.5 | 0.719 | 0.132 |
| validacao_2025_ja_vista | 1 | clima_susc | 19.01 | 0.193 | 28.6 | 0.711 | 0.137 |
| validacao_2025_ja_vista | 1 | persistencia | 23.56 | 0.000 | 24.2 | 0.809 | 0.339 |
| validacao_2025_ja_vista | 1 | semclima_semsusc | 20.86 | 0.115 | 31.7 | 0.689 | 0.098 |
| validacao_2025_ja_vista | 1 | semclima_susc | 19.96 | 0.153 | 34.3 | 0.679 | 0.108 |
| validacao_2025_ja_vista | 2 | clima_semsusc | 28.09 | 0.278 | 54.6 | 0.682 | 0.078 |
| validacao_2025_ja_vista | 2 | clima_susc | 29.21 | 0.249 | 62.4 | 0.669 | 0.085 |
| validacao_2025_ja_vista | 2 | persistencia | 38.92 | 0.000 | 29.3 | 0.740 | 0.194 |
| validacao_2025_ja_vista | 2 | semclima_semsusc | 30.19 | 0.224 | 70.6 | 0.658 | 0.053 |
| validacao_2025_ja_vista | 2 | semclima_susc | 32.31 | 0.170 | 80.7 | 0.654 | 0.069 |
| validacao_2025_ja_vista | 3 | clima_semsusc | 32.27 | 0.342 | 72.9 | 0.652 | 0.042 |
| validacao_2025_ja_vista | 3 | clima_susc | 36.20 | 0.262 | 105.8 | 0.639 | 0.036 |
| validacao_2025_ja_vista | 3 | persistencia | 49.05 | 0.000 | 35.6 | 0.683 | 0.118 |
| validacao_2025_ja_vista | 3 | semclima_semsusc | 38.11 | 0.223 | 115.5 | 0.619 | -0.005 |
| validacao_2025_ja_vista | 3 | semclima_susc | 42.89 | 0.126 | 147.1 | 0.609 | 0.011 |

### Efeitos (ΔMAE com − sem, IC 95% bootstrap por município)

| h | grupo | ΔMAE | IC 95% | Δ% | reduz erro? |
|---|---|---|---|---|---|
| 1 | clima | -0.266 | [-0.435, -0.129] | -1.1% | sim |
| 1 | suscetibilidade | -0.216 | [-0.338, -0.118] | -0.9% | sim |
| 2 | clima | -0.202 | [-0.358, -0.060] | -0.7% | sim |
| 2 | suscetibilidade | -0.270 | [-0.448, -0.124] | -1.0% | sim |
| 3 | clima | -0.157 | [-0.360, +0.059] | -0.5% | não |
| 3 | suscetibilidade | -0.183 | [-0.362, -0.009] | -0.6% | sim |

**Decisão (regra pré-registrada):** clima = entra; suscetibilidade = entra → `clima_susc`

## Chikungunya

| período | h | modelo | MAE | Skill | MAE incid. (mediana cidades) | AUC | Brier skill |
|---|---|---|---|---|---|---|---|
| dev_2018_2024 | 1 | clima_semsusc | 0.20 | -0.038 | 0.4 | 0.814 | 0.109 |
| dev_2018_2024 | 1 | clima_susc | 0.20 | -0.002 | 0.4 | 0.815 | 0.104 |
| dev_2018_2024 | 1 | persistencia | 0.20 | 0.000 | 0.3 | 0.676 | 0.108 |
| dev_2018_2024 | 1 | semclima_semsusc | 0.20 | -0.040 | 0.4 | 0.813 | 0.108 |
| dev_2018_2024 | 1 | semclima_susc | 0.20 | -0.011 | 0.4 | 0.815 | 0.106 |
| dev_2018_2024 | 2 | clima_semsusc | 0.22 | 0.138 | 0.4 | 0.789 | 0.065 |
| dev_2018_2024 | 2 | clima_susc | 0.22 | 0.161 | 0.4 | 0.794 | 0.068 |
| dev_2018_2024 | 2 | persistencia | 0.26 | 0.000 | 0.4 | 0.635 | 0.061 |
| dev_2018_2024 | 2 | semclima_semsusc | 0.23 | 0.113 | 0.5 | 0.784 | 0.059 |
| dev_2018_2024 | 2 | semclima_susc | 0.22 | 0.161 | 0.4 | 0.793 | 0.072 |
| dev_2018_2024 | 3 | clima_semsusc | 0.23 | 0.201 | 0.5 | 0.771 | 0.049 |
| dev_2018_2024 | 3 | clima_susc | 0.22 | 0.229 | 0.4 | 0.778 | 0.052 |
| dev_2018_2024 | 3 | persistencia | 0.29 | 0.000 | 0.4 | 0.614 | 0.040 |
| dev_2018_2024 | 3 | semclima_semsusc | 0.24 | 0.174 | 0.5 | 0.765 | 0.042 |
| dev_2018_2024 | 3 | semclima_susc | 0.22 | 0.228 | 0.4 | 0.775 | 0.052 |
| validacao_2025_ja_vista | 1 | clima_semsusc | 0.96 | 0.071 | 0.6 | 0.815 | 0.184 |
| validacao_2025_ja_vista | 1 | clima_susc | 0.90 | 0.134 | 0.6 | 0.816 | 0.187 |
| validacao_2025_ja_vista | 1 | persistencia | 1.04 | 0.000 | 0.0 | 0.714 | 0.161 |
| validacao_2025_ja_vista | 1 | semclima_semsusc | 0.96 | 0.072 | 0.6 | 0.814 | 0.187 |
| validacao_2025_ja_vista | 1 | semclima_susc | 0.89 | 0.141 | 0.7 | 0.815 | 0.187 |
| validacao_2025_ja_vista | 2 | clima_semsusc | 1.09 | 0.258 | 0.6 | 0.806 | 0.137 |
| validacao_2025_ja_vista | 2 | clima_susc | 1.07 | 0.269 | 0.6 | 0.801 | 0.142 |
| validacao_2025_ja_vista | 2 | persistencia | 1.46 | 0.000 | 0.0 | 0.680 | 0.099 |
| validacao_2025_ja_vista | 2 | semclima_semsusc | 1.11 | 0.245 | 0.6 | 0.802 | 0.130 |
| validacao_2025_ja_vista | 2 | semclima_susc | 1.07 | 0.266 | 0.7 | 0.805 | 0.150 |
| validacao_2025_ja_vista | 3 | clima_semsusc | 1.13 | 0.336 | 0.6 | 0.791 | 0.095 |
| validacao_2025_ja_vista | 3 | clima_susc | 1.12 | 0.342 | 0.7 | 0.792 | 0.106 |
| validacao_2025_ja_vista | 3 | persistencia | 1.70 | 0.000 | 0.0 | 0.640 | 0.046 |
| validacao_2025_ja_vista | 3 | semclima_semsusc | 1.15 | 0.326 | 0.7 | 0.789 | 0.078 |
| validacao_2025_ja_vista | 3 | semclima_susc | 1.12 | 0.342 | 0.7 | 0.793 | 0.116 |

### Efeitos (ΔMAE com − sem, IC 95% bootstrap por município)

| h | grupo | ΔMAE | IC 95% | Δ% | reduz erro? |
|---|---|---|---|---|---|
| 1 | clima | -0.002 | [-0.004, +0.001] | -0.8% | não |
| 1 | suscetibilidade | -0.007 | [-0.013, -0.002] | -3.4% | sim |
| 2 | clima | +0.000 | [-0.001, +0.002] | +0.1% | não |
| 2 | suscetibilidade | -0.006 | [-0.009, -0.003] | -2.7% | sim |
| 3 | clima | -0.000 | [-0.003, +0.002] | -0.2% | não |
| 3 | suscetibilidade | -0.008 | [-0.012, -0.005] | -3.5% | sim |

**Decisão (regra pré-registrada):** clima = fica de fora; suscetibilidade = entra → `semclima_susc`