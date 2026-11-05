# Combinação modelo + persistência (desvio pré-registrado de 2026-11-04)

Pesos escolhidos só com anos anteriores (cross-fitting temporal). 2025 já foi visto na v4.


## Chikungunya (modelo base `semclima_susc`)

| período | h | previsor | MAE | Skill | MAE incid. (mediana) | AUC | Brier skill |
|---|---|---|---|---|---|---|---|
| dev_2018_2024 | 1 | combinacao | 0.19 | 0.021 | 0.4 | 0.777 | 0.098 |
| dev_2018_2024 | 1 | modelo | 0.20 | -0.011 | 0.4 | 0.815 | 0.106 |
| dev_2018_2024 | 1 | persistencia | 0.20 | 0.000 | 0.3 | 0.676 | 0.108 |
| dev_2018_2024 | 2 | combinacao | 0.22 | 0.164 | 0.4 | 0.786 | 0.071 |
| dev_2018_2024 | 2 | modelo | 0.22 | 0.161 | 0.4 | 0.793 | 0.072 |
| dev_2018_2024 | 2 | persistencia | 0.26 | 0.000 | 0.4 | 0.635 | 0.061 |
| dev_2018_2024 | 3 | combinacao | 0.23 | 0.216 | 0.4 | 0.767 | 0.053 |
| dev_2018_2024 | 3 | modelo | 0.22 | 0.228 | 0.4 | 0.775 | 0.052 |
| dev_2018_2024 | 3 | persistencia | 0.29 | 0.000 | 0.4 | 0.614 | 0.040 |
| validacao_2025_ja_vista | 1 | combinacao | 0.81 | 0.220 | 0.5 | 0.824 | 0.188 |
| validacao_2025_ja_vista | 1 | modelo | 0.89 | 0.141 | 0.7 | 0.815 | 0.187 |
| validacao_2025_ja_vista | 1 | persistencia | 1.04 | 0.000 | 0.0 | 0.714 | 0.161 |
| validacao_2025_ja_vista | 2 | combinacao | 1.05 | 0.281 | 0.6 | 0.807 | 0.138 |
| validacao_2025_ja_vista | 2 | modelo | 1.07 | 0.266 | 0.7 | 0.805 | 0.150 |
| validacao_2025_ja_vista | 2 | persistencia | 1.46 | 0.000 | 0.0 | 0.680 | 0.099 |
| validacao_2025_ja_vista | 3 | combinacao | 1.13 | 0.337 | 0.7 | 0.793 | 0.105 |
| validacao_2025_ja_vista | 3 | modelo | 1.12 | 0.342 | 0.7 | 0.793 | 0.116 |
| validacao_2025_ja_vista | 3 | persistencia | 1.70 | 0.000 | 0.0 | 0.640 | 0.046 |

| h | peso final do modelo (2018–2025) | ΔMAE combinação − modelo (dev) | IC 95% | reduz erro? |
|---|---|---|---|---|
| 1 | 0.6 | -0.006 (-3.2%) | [-0.012, -0.002] | sim |
| 2 | 0.9 | -0.001 (-0.3%) | [-0.006, +0.003] | não |
| 3 | 1.0 | +0.003 (+1.5%) | [-0.001, +0.007] | não |

**Decisão:** fica o modelo puro.

## Dengue (modelo base `clima_susc`)

| período | h | previsor | MAE | Skill | MAE incid. (mediana) | AUC | Brier skill |
|---|---|---|---|---|---|---|---|
| dev_2018_2024 | 1 | combinacao | 20.92 | 0.213 | 36.3 | 0.842 | 0.281 |
| dev_2018_2024 | 1 | modelo | 23.40 | 0.120 | 34.3 | 0.820 | 0.237 |
| dev_2018_2024 | 1 | persistencia | 26.60 | 0.000 | 48.7 | 0.836 | 0.366 |
| dev_2018_2024 | 2 | combinacao | 27.57 | 0.378 | 46.4 | 0.797 | 0.181 |
| dev_2018_2024 | 2 | modelo | 27.67 | 0.375 | 44.8 | 0.780 | 0.153 |
| dev_2018_2024 | 2 | persistencia | 44.30 | 0.000 | 75.1 | 0.777 | 0.211 |
| dev_2018_2024 | 3 | combinacao | 30.00 | 0.455 | 49.7 | 0.769 | 0.134 |
| dev_2018_2024 | 3 | modelo | 29.93 | 0.456 | 49.7 | 0.762 | 0.121 |
| dev_2018_2024 | 3 | persistencia | 55.02 | 0.000 | 93.4 | 0.725 | 0.116 |
| validacao_2025_ja_vista | 1 | combinacao | 18.72 | 0.205 | 26.2 | 0.743 | 0.175 |
| validacao_2025_ja_vista | 1 | modelo | 19.01 | 0.193 | 28.6 | 0.711 | 0.137 |
| validacao_2025_ja_vista | 1 | persistencia | 23.56 | 0.000 | 24.2 | 0.809 | 0.339 |
| validacao_2025_ja_vista | 2 | combinacao | 28.55 | 0.266 | 57.9 | 0.673 | 0.093 |
| validacao_2025_ja_vista | 2 | modelo | 29.21 | 0.249 | 62.4 | 0.669 | 0.085 |
| validacao_2025_ja_vista | 2 | persistencia | 38.92 | 0.000 | 29.3 | 0.740 | 0.194 |
| validacao_2025_ja_vista | 3 | combinacao | 36.20 | 0.262 | 105.8 | 0.639 | 0.039 |
| validacao_2025_ja_vista | 3 | modelo | 36.20 | 0.262 | 105.8 | 0.639 | 0.036 |
| validacao_2025_ja_vista | 3 | persistencia | 49.05 | 0.000 | 35.6 | 0.683 | 0.118 |

| h | peso final do modelo (2018–2025) | ΔMAE combinação − modelo (dev) | IC 95% | reduz erro? |
|---|---|---|---|---|
| 1 | 0.6 | -2.475 (-10.6%) | [-3.661, -1.529] | sim |
| 2 | 0.9 | -0.103 (-0.4%) | [-0.434, +0.159] | não |
| 3 | 1.0 | +0.066 (+0.2%) | [-0.017, +0.128] | não |

**Decisão:** fica o modelo puro.