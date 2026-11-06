# Hugging Face Space (SDK Docker) da Prodígia.
# Clona o repositório público na tag da versão e, ao iniciar, baixa os artefatos da GitHub Release
# (modelos v5.1 + snapshot do banco), conferindo o SHA-256 de cada arquivo.
FROM python:3.12-slim

ARG VERSAO=modelo-v5.1
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PORT=7860

RUN apt-get update && apt-get install -y --no-install-recommends git libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 user
WORKDIR /app
RUN git clone --depth 1 --branch ${VERSAO} https://github.com/ruigabriel1/Projeto_Clima_X_Dengue.git . \
    && pip install -r requirements-api.txt \
    && mkdir -p data/processed output && chown -R user:user /app

USER user
EXPOSE 7860
CMD ["sh", "-c", "python -m src.prediction_service.artefatos garantir && exec uvicorn app.server:app --host 0.0.0.0 --port ${PORT}"]
