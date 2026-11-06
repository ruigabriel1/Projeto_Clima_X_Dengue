# Prodígia — API + aplicação web de previsão de dengue e chikungunya (Região Sul)
#
#   docker build -t prodigia .
#   docker run -p 8000:8000 prodigia
#
# Na primeira inicialização, os artefatos (modelos v5.1 + snapshot do banco) são baixados da GitHub Release
# e conferidos por SHA-256. Para usar artefatos locais, monte os diretórios:
#   docker run -p 8000:8000 -v "$PWD/data/processed:/app/data/processed" -v "$PWD/output:/app/output" prodigia
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PORT=8000

# libgomp1: OpenMP exigido pelo xgboost
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 app
WORKDIR /app

COPY requirements-api.txt .
RUN pip install -r requirements-api.txt

COPY --chown=app:app src ./src
COPY --chown=app:app app ./app
COPY --chown=app:app main.py ./
RUN mkdir -p data/processed output && chown -R app:app /app

USER app
EXPOSE 8000
CMD ["sh", "-c", "python -m src.prediction_service.artefatos garantir && exec uvicorn app.server:app --host 0.0.0.0 --port ${PORT}"]
