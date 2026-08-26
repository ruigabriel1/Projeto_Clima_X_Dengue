# 🧠 Ciência de Dados: Do Prophet ao XGBoost Global

A modelagem de dados da Dengue no Sul passou por uma evolução profunda. Começamos tentando prever surtos de forma univariada, município a município, utilizando o algoritmo **Prophet** (Meta/Facebook). 

### O Fracasso do Modelo Local (Prophet)
* **Zero-Inflated:** Mais de 60% dos meses nas cidades do Sul não têm dengue (invernos rigorosos). O Prophet colapsa ao tentar modelar zeros.
* **Falta de Memória:** O modelo não entendia a diferença climática entre uma metrópole e uma vila agrícola.

### O Triunfo da Árvore de Decisão Global (XGBoost)
A solução matemática adotada foi um modelo global onde as 1.190 cidades são treinadas simultaneamente por um único algoritmo XGBoost Regressor.

#### Engenharia de Features (A Chave do Sucesso)
Sem usar nenhuma API externa para puxar população ou relevo, derivamos conhecimento geobiológico a partir das próprias séries temporais:
1. **Proxy Populacional (`max_historico_casos`)**: A IA identifica cidades grandes se o pico histórico for alto.
2. **Barreira Geográfica (`latitude` + `longitude`)**: O XGBoost entende espacialmente a localização das Serras (barreiras de frio) pela correlação de coordenadas.
3. **Memória Imunológica (`casos_lag12`)**: Ensina à IA o efeito "Rebanho" (Ressaca). Se 2022 teve muito surto, a chance de 2023 ter surto cai.
4. **Velocidade de Contágio (`casos_lag1`)**: O surto atual retroalimenta o surto seguinte.

#### Cross-Validation Espacial
Ao usar um split espacial (treinar em 80% das cidades e testar em 20%) ao longo de 10 anos, conseguimos prever os Surtos Recordes de 2024 de forma cega, atingindo o invejável **R² de 0.744** e um erro médio absoluto de apenas 10.8 casos!
