# Linux image with its own dependencies. The Windows .venv cannot be mounted in,
# so the environment is rebuilt from the pinned requirements.txt instead.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    PIP_NO_CACHE_DIR=1

# libgomp1 is required by LightGBM and TensorFlow on slim images.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY src/ ./src/
COPY app/ ./app/
COPY scripts/ ./scripts/
RUN pip install -e .

# Only the artifacts, not the 2.3 GB dataset.
COPY models/ensemble.joblib models/scaler.joblib models/bilstm_ds02.keras \
     models/ds02_manifest.json ./models/

ENV DS02_ARTIFACT=/app/models/ensemble.joblib
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
