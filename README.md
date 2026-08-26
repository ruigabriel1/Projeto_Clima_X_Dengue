# 🦟 Predição Epidemiológica de Dengue com XGBoost

Este projeto utiliza Engenharia de Dados e Machine Learning (XGBoost) para prever surtos de dengue na Região Sul do Brasil, cruzando dados climáticos (INMET), epidemiológicos (SINAN) e anomalias oceânicas (El Niño/NOAA).

## 🚀 O Grande Resultado: Antecipando o "Cisne Negro"
Em nosso teste de validação cruzada global, o modelo de Inteligência Artificial foi capaz de prever os surtos do ano de 2024 (o ano com o maior recorde epidêmico do Brasil) com **alta precisão científica**:
* **R² Score:** `0.744` (74,4% da variância climática e biológica explicada).
* **MAE:** Erro médio de apenas `10.8` casos por cidade ao mês.

Para alcançar este resultado sem depender de APIs externas para cada município, utilizamos Engenharia de Features avançada:
* `max_historico_casos` como **Proxy de Densidade Urbana**.
* `latitude / longitude` cruzadas como **Bússola Geográfica** (detectando a barreira natural das Serras).
* `casos_lag1` e `casos_lag12` para calcular matematicamente a **Velocidade de Contágio** e a **Memória Imunológica de Rebanho**.

---

## 🏗️ Estrutura da Documentação e Portfólio

Se você deseja entender a fundo como este projeto foi construído, leia nossa documentação definitiva:

1. [🏛️ Arquitetura de Dados (Medallion)](docs/ARQUITETURA_DE_DADOS.md): Como saímos do caos governamental em CSVs sujos para um painel analítico prateado.
2. [🧠 Ciência de Dados & XGBoost](docs/CIENCIA_DE_DADOS_XGBOOST.md): A explicação do salto de precisão, abandonando modelos ingênuos (Prophet) em favor de uma Árvore Global (XGBoost).
3. [📖 Diário do Projeto (Histórico)](docs/historico_diario_projeto.md): O log cronológico do desenvolvimento.

---

## ⚙️ Como Rodar (Setup)

**1. Instalar dependências:**
```bash
pip install -r requirements.txt
pip install xgboost jupyter
```

**2. Rodar a extração e limpeza (Bronze -> Silver):**
```bash
python main.py process-data
```

**3. Validar o Modelo Machine Learning:**
Abra o Jupyter e rode o notebook interativo do modelo final:
```bash
jupyter notebook notebooks/04_xgboost_alta_precisao.ipynb
```
