"""FastAPI surface over the DS02 artifact.

    uvicorn app.api:app --host 0.0.0.0 --port 8000
    curl -X POST localhost:8000/predict -H 'content-type: application/json' \
         -d '{"unit": 11, "window": 0}'
"""
from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from ds02_rul.data import load_ds02  # noqa: E402
from ds02_rul.inference import windows_for_unit  # noqa: E402
from ds02_rul.persistence import load_ensemble  # noqa: E402

ARTIFACT = os.environ.get("DS02_ARTIFACT", os.path.join("models", "ensemble.joblib"))
STATE: dict = {}


@asynccontextmanager
async def lifespan(_app: FastAPI):
    STATE["ensemble"] = load_ensemble(ARTIFACT)
    STATE["raw"] = None  # lazily loaded; the HDF5 is 2.3 GB
    yield
    STATE.clear()


app = FastAPI(title="DS02 RUL API", version="4.1.0", lifespan=lifespan)


class PredictRequest(BaseModel):
    unit: float = Field(..., description="engine id, e.g. 11")
    window: int = Field(0, ge=0, description="window index within the engine")
    all_windows: bool = Field(False, description="score the whole trajectory")


class PredictResponse(BaseModel):
    unit: float
    cycle: float
    rul: float
    window_size: int
    beta: float


def _raw():
    if STATE.get("raw") is None:
        STATE["raw"] = load_ds02(stride=100)
    return STATE["raw"]


@app.get("/health")
def health() -> dict:
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
def units() -> dict:
    raw = _raw()
    return {"test_units": sorted(float(u) for u in np.unique(raw["A_test"][:, 0]))}


@app.post("/predict", response_model=None)
def predict(req: PredictRequest) -> dict:
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
