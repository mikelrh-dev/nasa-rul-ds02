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
# NOTE (P1): binding 0.0.0.0 here is only safe behind a TLS-terminating reverse
# proxy (nginx/Caddy/load balancer) that adds TLS and ideally authentication
# (DS02_API_KEY). Never expose this container to the public internet with
# plain HTTP. For a standalone local run, override with --host 127.0.0.1,
# e.g. `docker run -p 127.0.0.1:8000:8000 ...` and bind loopback, or
# `uvicorn app.api:app --host 127.0.0.1 --port 8000`.
# SEC-DOCK-ST-01: docker-compose.yml publishes this port as
# 127.0.0.1:8000:8000 (loopback on the host) while the container itself
# keeps binding 0.0.0.0 internally so port mapping keeps working. Do not
# publish 0.0.0.0:8000; any external exposure must go through the
# TLS-terminating proxy described above.
