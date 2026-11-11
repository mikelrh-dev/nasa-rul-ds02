"""FastAPI surface over the DS02 artifact.

    uvicorn app.api:app --host 127.0.0.1 --port 8000
    curl -X POST localhost:8000/predict -H 'content-type: application/json' \\
         -d '{"unit": 11, "window": 0}'

P1 hardening:
- The artifact SHA-256 is verified by `ds02_rul.persistence.load_ensemble`
  (against `models/ds02_manifest.json` and `app/cache/cache_manifest.json`)
  before any deserialization; mismatch raises `RuntimeError`.
- `DS02_ARTIFACT` is allowlisted: it must resolve inside the repository
  (`resolve_within_repo`). Free absolute paths outside the repo are refused.
- `docs_url`/`redoc_url`/`openapi_url` are disabled in production
  (`ENVIRONMENT=production` or `prod`).
- CORS is localhost-only; security headers are set on every response.
- `/predict` and `/units` require an API key when `DS02_API_KEY` is set
  (`X-API-Key` header via `Depends`, compared with `hmac.compare_digest`).
  A fixed-window rate limit of 10 requests/minute per client IP applies
  with or without an API key, so authenticated writes are throttled too.
- `/health` stays public (200 without credentials) as a liveness contract.
- `/n8n-decision` (MIA-3 novel action) is a token-guarded write endpoint that
  records a decision in `app/registros_n8n.json`; it is idempotent by
  `fingerprint` and answers 503 when `N8N_WEBHOOK_TOKEN` is not configured.
  It is NOT rate-limited: the per-IP limiter protects scoring, not the log.
- `PredictRequest` validates `unit`/`window` with `ge`/`le` and rejects
  NaN/Inf via an explicit validator (pydantic allows them by default).

Deployment note: never expose this service on `0.0.0.0` with plain HTTP.
Bind `0.0.0.0` only behind a TLS-terminating reverse proxy (e.g. nginx,
Caddy, or a cloud load balancer) that adds TLS and ideally authentication.
For local/standalone use bind `127.0.0.1`; there is no container image by design.
"""
from __future__ import annotations

import hmac
import json
import logging
import math
import os
import sys
import threading
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import numpy as np
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from ds02_rul.data import load_ds02  # noqa: E402
from ds02_rul.inference import windows_for_unit  # noqa: E402
from ds02_rul.persistence import load_ensemble, resolve_within_repo  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Allowlist: env may only point inside the repo (relative to repo root or
# absolute-under-repo). Anything else is refused at import time.
ARTIFACT = resolve_within_repo(
    os.environ.get("DS02_ARTIFACT", os.path.join("models", "ensemble.joblib")),
    base=REPO_ROOT,
)
STATE: dict = {}

_ENVIRONMENT = os.environ.get("ENVIRONMENT", "dev").strip().lower()
_IS_PROD = _ENVIRONMENT in ("production", "prod")
_API_KEY = os.environ.get("DS02_API_KEY", "").strip() or None

log = logging.getLogger(__name__)

# In-memory fixed-window rate limiter (no extra dependency): 10/min per IP.
_RATE_LIMIT_PER_MIN = 10
_RATE_WINDOW_S = 60.0
_rate_lock = threading.Lock()
_rate_hits: dict[str, list[float]] = {}


def _client_ip(request: Request) -> str:
    """Client IP for the rate limiter (host, or 'unknown' if absent)."""
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
    """API-key auth when configured, plus in-memory rate limiting always.

    The key is compared with `hmac.compare_digest` (constant-time).
    The 10/min per-IP limiter runs after successful auth with or
    without a configured key, so authenticated writes (POST /predict)
    are throttled the same as unauthenticated ones.
    """
    if _API_KEY is not None:
        if not x_api_key or not hmac.compare_digest(x_api_key, _API_KEY):
            raise HTTPException(status_code=401, detail="invalid or missing API key")
    _check_rate_limit(request)


def require_api_key(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> None:
    """`Depends` guard for `/predict` and `/units`.

    If `DS02_API_KEY` is set, requires a matching `X-API-Key` header
    (compared with `hmac.compare_digest`). The 10/min per-IP rate
    limit applies in every case, with or without a key.
    """
    _protect(request, x_api_key)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Loads and verifies the ensemble artifact on startup, clears on shutdown."""
    # load_ensemble verifies the SHA-256 against the manifests before
    # deserializing; on mismatch it raises RuntimeError and startup aborts.
    STATE["ensemble"] = load_ensemble(ARTIFACT)
    STATE["raw"] = None  # lazily loaded; the HDF5 is 2.3 GB
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

# CORS: localhost only, no wildcard origins.
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
    """Adds the security headers to every response."""
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
        """Rejects NaN/Inf in the unit field."""
        # Pydantic/float accepts NaN and Inf by default; reject them here.
        if not math.isfinite(float(value)):
            raise ValueError("unit must be a finite number (NaN/Inf rejected)")
        return float(value)



# ----------------------------------------------------------- n8n decision
# MIA-3: accion novedosa de la rama HANGAR. El flujo n8n llama a la API del
# propio proyecto; el token es el mismo N8N_WEBHOOK_TOKEN que la app envia en
# X-DS02-Token (src/n8n.py). El registro es idempotente por fingerprint.
_N8N_TOKEN = os.environ.get("N8N_WEBHOOK_TOKEN", "").strip() or None
_N8N_DECISIONES = ("APTO", "INSPECCION", "HANGAR")
_N8N_REGISTROS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "registros_n8n.json")
# RLock: `n8n_decision` ya lo toma y despues llama a `_guardar_n8n_registros`,
# que lo vuelve a pedir. Con `Lock` el endpoint se autobloqueaba en el primer POST.
_N8N_LOCK = threading.RLock()


class N8NDecisionRequest(BaseModel):
    """Decision que n8n registra en el log local del proyecto."""

    decision: str = Field(..., description="APTO | INSPECCION | HANGAR")
    fingerprint: str = Field(..., description="idempotency key de la traza")
    artefacto_sha256: str = Field("", description="SHA-256 del artefacto")
    unidad: int | None = Field(None, description="motor, si se conoce")
    # El token puede venir en el body (contrato original, cubierto por tests) o
    # en la cabecera X-DS02-Token, que es como lo envian la app (src/n8n.py) y
    # el nodo n8n. La cabecera manda si esta presente.
    token: str = Field("", description="N8N_WEBHOOK_TOKEN compartido (body o X-DS02-Token)")


class N8NDecisionResponse(BaseModel):
    """Resultado del registro: `recorded` es False si el fingerprint ya estaba."""

    ok: bool
    recorded: bool


def _n8n_registro_path() -> str:
    """Ruta del registro; inyectable en tests."""
    return _N8N_REGISTROS_PATH


def _cargar_n8n_registros() -> list:
    """Lee el registro; ausente o corrupto se trata como lista vacia."""
    ruta = _n8n_registro_path()
    if not os.path.exists(ruta):
        return []
    try:
        with open(ruta, encoding="utf-8") as fh:
            datos = json.load(fh)
        return list(datos) if isinstance(datos, list) else []
    except (OSError, ValueError):
        log.warning("n8n: registro %s ilegible; se empieza vacio", ruta)
        return []


def _guardar_n8n_registros(filas: list) -> None:
    """Escritura atomica: tmp + fsync + replace, con lock de proceso."""
    ruta = _n8n_registro_path()
    tmp = f"{ruta}.tmp"
    with _N8N_LOCK:
        os.makedirs(os.path.dirname(os.path.abspath(ruta)), exist_ok=True)
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(filas, fh, ensure_ascii=False, indent=1)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, ruta)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)


@app.post("/n8n-decision", response_model=N8NDecisionResponse)
def n8n_decision(
    req: N8NDecisionRequest,
    x_ds02_token: str | None = Header(default=None, alias="X-DS02-Token"),
) -> N8NDecisionResponse:
    """Registra una decision vinda del flujo n8n (accion novedosa MIA-3).

    Auth por token compartido (`hmac.compare_digest`, igual que el webhook de
    n8n y `X-DS02-Token` de `src/n8n.py`). El token se acepta en la cabecera
    `X-DS02-Token` (como lo envian la app y el nodo n8n) o en el body.
    Sin token configurado, 503: el endpoint degrada de forma visible y no
    rompe el arranque del servicio. Idempotente por `fingerprint`: un
    reintento de n8n no duplica la fila.
    """
    if _N8N_TOKEN is None:
        raise HTTPException(
            status_code=503,
            detail="N8N_WEBHOOK_TOKEN no esta configurado en el servidor; "
                   "el endpoint /n8n-decision no puede autenticar la peticion",
        )
    token = x_ds02_token or req.token
    if not token or not hmac.compare_digest(token, _N8N_TOKEN):
        raise HTTPException(status_code=401, detail="invalid or missing n8n token")
    if req.decision not in _N8N_DECISIONES:
        raise HTTPException(
            status_code=400,
            detail=f"decision invalida: {req.decision!r}; "
                   f"debe ser una de {_N8N_DECISIONES}",
        )

    fila = {
        "decision": req.decision,
        "fingerprint": str(req.fingerprint),
        "artefacto_sha256": str(req.artefacto_sha256),
        "unidad": None if req.unidad is None else int(req.unidad),
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with _N8N_LOCK:
        filas = _cargar_n8n_registros()
        if any(str(f.get("fingerprint")) == fila["fingerprint"] for f in filas):
            return N8NDecisionResponse(ok=True, recorded=False)
        filas.append(fila)
        _guardar_n8n_registros(filas)
    log.info("n8n: decision %s registrada (fingerprint %s)",
             req.decision, fila["fingerprint"])
    return N8NDecisionResponse(ok=True, recorded=True)


def _raw():
    """Lazily loads the raw DS02 data (HDF5 is ~2.3 GB)."""
    if STATE.get("raw") is None:
        STATE["raw"] = load_ds02(stride=100)
    return STATE["raw"]


@app.get("/health")
def health() -> dict:
    """Health check: artifact loaded, with its config."""
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
    """Lists the test engine ids available for scoring."""
    raw = _raw()
    return {"test_units": sorted(float(u) for u in np.unique(raw["A_test"][:, 0]))}


@app.post("/predict", response_model=None)
def predict(req: PredictRequest, _auth: None = Depends(require_api_key)) -> dict:
    """Scores one window (or the whole trajectory, if all_windows) for an engine."""
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
