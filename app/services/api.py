"""Superficie FastAPI sobre el artefacto DS02.

    uvicorn app.services.api:app --host 127.0.0.1 --port 8000
    curl -X POST localhost:8000/predict -H 'content-type: application/json' \\
         -d '{"unit": 11, "window": 0}'

Refuerzos de seguridad:
- `ds02_rul.persistence.load_ensemble` verifica el SHA-256 del artefacto contra
  `models/ds02_manifest.json` y `app/cache/cache_manifest.json` antes de
  deserializar; si no coincide, lanza `RuntimeError`.
- `DS02_ARTIFACT` está en lista blanca: debe resolver dentro del repositorio
  (`resolve_within_repo`). Las rutas absolutas de fuera se rechazan.
- `docs_url`, `redoc_url` y `openapi_url` se desactivan en producción
  (`ENVIRONMENT=production` o `prod`).
- CORS solo para localhost; las cabeceras de seguridad se añaden a cada respuesta.
- `/predict` y `/units` piden API key cuando existe `DS02_API_KEY` (cabecera
  `X-API-Key` vía `Depends`, comparada con `hmac.compare_digest`). El límite de
  10 peticiones por minuto y por IP se aplica con o sin key, así que las
  escrituras autenticadas también van limitadas.
- `/health` sigue siendo público (200 sin credenciales) como contrato de vida.
- `PredictRequest` valida `unit`/`window` con `ge`/`le` y rechaza NaN/Inf con un
  validador explícito (pydantic los acepta por defecto).

Nota de despliegue: nunca expongas este servicio en `0.0.0.0` con HTTP plano.
Usa `0.0.0.0` solo detrás de un proxy inverso que termine TLS (nginx, Caddy o
un balanceador cloud) y añada TLS y, a ser posible, autenticación. Para uso
local, enlaza `127.0.0.1`; no hay imagen de contenedor por diseño.
"""
from __future__ import annotations

import hmac
import logging
import math
import os
import threading
import time
from contextlib import asynccontextmanager

import numpy as np
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from app import _paths

from ds02_rul.data import load_ds02  # noqa: E402
from ds02_rul.inference import windows_for_unit  # noqa: E402
from ds02_rul.persistence import load_ensemble, resolve_within_repo  # noqa: E402

REPO_ROOT = str(_paths.ROOT)
# Lista blanca: la variable de entorno solo puede apuntar dentro del repo
# (relativa a la raíz o absoluta bajo ella). Cualquier otra cosa se rechaza al importar.
ARTIFACT = resolve_within_repo(
    os.environ.get("DS02_ARTIFACT", os.path.join("models", "ensemble.joblib")),
    base=REPO_ROOT,
)
STATE: dict = {}

_ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev").strip().lower()
_IS_PROD = _ENVIRONMENT in ("production", "prod")
_API_KEY = os.environ.get("DS02_API_KEY", "").strip() or None

log = logging.getLogger(__name__)

# Limitador de tasa en memoria por ventana fija (sin dependencias extra): 10/min por IP.
_RATE_LIMIT_PER_MIN = 10
_RATE_WINDOW_S = 60.0
_rate_lock = threading.Lock()
_rate_hits: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    """IP del cliente para el limitador (el host o 'unknown' si falta)."""
    if request.client is not None:
        return request.client.host
    return "unknown"


def _check_rate_limit(request: Request) -> None:
    """Fixed-window per-IP limiter: 10 requests/minute."""
    ip = _client_ip(request)
    now = time.monotonic()
    with _rate_lock:
        hits = [t for t in _rate_hits.get(ip, []) if now - t < _RATE_WINDOW_S]
        if len(hits) >= _RATE_LIMIT_PER_MIN:
            raise HTTPException(status_code=429, detail="rate limit exceeded (10/min)")
        hits.append(now)
        _rate_hits[ip] = hits


def _protect(request: Request, x_api_key: str | None = None) -> None:
    """Autenticación por API key si está configurada y límite en memoria siempre.

    La clave se compara con `hmac.compare_digest` (tiempo constante). El límite
    de 10/min por IP corre tras la autenticación, con o sin clave configurada,
    así que las escrituras autenticadas (POST /predict) se limitan igual que las
    anónimas.
    """
    if _API_KEY is not None:
        if not x_api_key or not hmac.compare_digest(x_api_key, _API_KEY):
            raise HTTPException(status_code=401, detail="invalid or missing API key")
    _check_rate_limit(request)


def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """Guarda `Depends` para `/predict` y `/units`.

    Si existe `DS02_API_KEY`, exige una cabecera `X-API-Key` que coincida
    (comparada con `hmac.compare_digest`). El límite de 10/min por IP se aplica
    siempre, con o sin clave.
    """
    _protect(request, x_api_key)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Carga y verifica el artefacto al arrancar, y lo limpia al apagar."""
    # load_ensemble verifica el SHA-256 contra los manifiestos antes de
    # deserializar; si no coincide, lanza RuntimeError y el arranque se aborta.
    STATE["ensemble"] = load_ensemble(ARTIFACT)
    STATE["raw"] = None  # carga diferida; el HDF5 pesa 2.3 GB
    yield
    STATE.clear()


app = FastAPI(
    title="DS02 RUL API",
    version="4.1.0",
    lifespan=lifespan,
    docs_url=None if _IS_PROD else "/docs",
    redoc_url=None if _IS_PROD else "/redoc",
    openapi_url=None if _IS_PROD else "/openapi.json",
)

# CORS: solo localhost, sin orígenes comodín.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.middleware("http")
async def _security_headers(request: Request, call_next):  # noqa: ANN001, ANN202
    """Añade las cabeceras de seguridad a cada respuesta."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    return response


class PredictRequest(BaseModel):
    """Unidad y ventana solicitadas a la API del bundle congelado."""
    unit: float = Field(..., ge=1, le=10000, description="engine id, e.g. 11")
    window: int = Field(0, ge=0, le=10000, description="window index within the engine")
    all_windows: bool = Field(False, description="score the whole trajectory")

    @field_validator("unit")
    @classmethod
    def _unit_must_be_finite(cls, value: float) -> float:
        """Rechaza NaN/Inf en el campo de unidad."""
        # Pydantic y float aceptan NaN e Inf por defecto; aquí se rechazan.
        if not math.isfinite(float(value)):
            raise ValueError("unit must be a finite number (NaN/Inf rejected)")
        return float(value)


def _raw():
    """Carga los datos crudos DS02 de forma diferida (el HDF5 pesa ~2.3 GB)."""
    if STATE.get("raw") is None:
        STATE["raw"] = load_ds02(stride=100)
    return STATE["raw"]


@app.get("/health")
def health() -> dict:
    """Comprobación de salud: artefacto cargado y su configuración."""
    ensemble = STATE.get("ensemble")
    if ensemble is None:
        raise HTTPException(status_code=503, detail="artifact not loaded")
    return {
        "status": "ok",
        "paradigm": ensemble.paradigm,
        "window_size": ensemble.window_size,
        "beta": ensemble.beta,
        "ema_span": ensemble.ema_span,
        "n_op": ensemble.n_op,
        "tabular_features": int(getattr(ensemble.lgb_standalone, "n_features_in_", -1)),
    }


@app.get("/units")
def units(_auth: None = Depends(require_api_key)) -> dict:
    """Lista los ids de motores de test disponibles para puntuar."""
    raw = _raw()
    return {"test_units": sorted(float(u) for u in np.unique(raw["A_test"][:, 0]))}


@app.post("/predict", response_model=None)
def predict(req: PredictRequest, _auth: None = Depends(require_api_key)) -> dict:
    """Puntúa una ventana o toda la trayectoria de un motor si `all_windows`."""
    ensemble = STATE.get("ensemble")
    if ensemble is None:
        raise HTTPException(status_code=503, detail="artifact not loaded")

    try:
        raw = _raw()
        X, cycles, uni, _ = windows_for_unit(
            raw["W_test"], raw["Xs_test"], raw["A_test"][:, 0], raw["A_test"][:, 1],
            req.unit, window=ensemble.window_size, step=2,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if req.all_windows:
        preds = ensemble.predict(X, cycles, uni)
        return {
            "unit": float(req.unit),
            "n_windows": int(len(preds)),
            "cycles": [float(c) for c in cycles],
            "predictions": [round(float(p), 2) for p in preds],
            "rul_final": round(float(preds[-1]), 2),
        }

    if req.window >= len(X):
        raise HTTPException(
            status_code=422,
            detail=f"window {req.window} out of range (0..{len(X) - 1})",
        )
    pred = float(
        ensemble.predict(
            X[req.window : req.window + 1],
            cycles[req.window : req.window + 1],
            uni[req.window : req.window + 1],
        )[0]
    )
    return {
        "unit": float(req.unit),
        "cycle": float(cycles[req.window]),
        "rul": round(pred, 2),
        "window_size": ensemble.window_size,
        "beta": ensemble.beta,
    }
