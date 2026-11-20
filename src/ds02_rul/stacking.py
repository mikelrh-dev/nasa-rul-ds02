"""Selección agrupada out-of-fold del factor de contracción `beta`.

El notebook original ajustaba los meta-aprendices con las filas de la unidad 16 y
luego puntuaba la rejilla de `beta` sobre esas mismas filas. Por eso reportaba un
RMSE de validación de 0.308 frente al 4.221 del BiLSTM y llevaba `beta` al máximo
de la rejilla. Aquí cada unidad puntuada lo está por meta-aprendices ajustados
solo con las demás unidades.

La fase A es cara (un ajuste del modelo base por grupo reservado) y la aporta
quien llama: `select_beta_grouped` consume predicciones out-of-fold ya
calculadas. Así el coste computacional queda explícito y no hay reajustes
ocultos.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import GroupKFold

from .metrics import calculate_nasa_score
from .smoothing import causal_ema_by_unit

BETA_GRID = np.linspace(0.0, 1.0, 21)
RIDGE_ALPHAS = np.logspace(-2, 3, 20)


@dataclass(frozen=True)
class MetaSpec:
    """Cómo se construye y se aplica la capa de stacking.

    El protocolo desplegado (`MetaSpec()`) es la media 50/50 de un `RidgeCV`
    libre y un `LGBMRegressor` poco profundo sobre `[p_lstm, p_lgb]`. Los campos
    existen para poder medir las alternativas en vez de discutirlas.

    level_mode : "free" | "sum_to_one" | "convex"
        `free` conserva los coeficientes ajustados, que se contraen (sumaban
        0.894 en el artefacto desplegado). Esa contracción es óptima dentro del
        soporte del meta y sesgada fuera, así que `sum_to_one` reescala los
        coeficientes de la cresta para que sumen 1 y reajusta el intercepto:
        quita la atenuación sin perder el reparto aprendido entre ramas.
        `convex` quita también el intercepto, de modo que el meta pasa a ser una
        mezcla convexa aprendida y no puede mover el nivel. Importa porque el
        meta desplegado lleva un intercepto ajustado con el sesgo de la unidad
        16, y ese desplazamiento no se traslada a otros motores.
    use_discrepancy : bool
        Añade `relu(p_lgb - p_lstm)` como tercera meta-variable, para que el meta
        vea cuánto se separa la rama cuantílica asimétrica del BiLSTM.
    support_gate : float
        Ancho de rampa, en ciclos, con el que la predicción del meta vuelve a
        `max(p_lstm, p_lgb)` cuando este supera el mayor objetivo con el que se
        ajustó. `0.0` desactiva la compuerta.
    blend_lgb : float
        Peso del meta de árboles en la reconciliación 50/50. `0.0` usa solo la
        cresta con el nivel restaurado.
    """

    level_mode: str = "free"
    use_discrepancy: bool = False
    support_gate: float = 0.0
    blend_lgb: float = 0.5

    def __post_init__(self):
        if self.level_mode not in ("free", "sum_to_one", "convex"):
            raise ValueError(f"unknown level_mode {self.level_mode!r}")
        if not 0.0 <= self.blend_lgb <= 1.0:
            raise ValueError("blend_lgb must be in [0, 1]")
        if self.support_gate < 0.0:
            raise ValueError("support_gate must be >= 0")


def meta_design(p_lstm, p_lgb, spec: MetaSpec = MetaSpec()) -> np.ndarray:
    """Construye la matriz de diseño del meta para una especificación."""
    p_lstm = np.asarray(p_lstm, dtype=np.float64).ravel()
    p_lgb = np.asarray(p_lgb, dtype=np.float64).ravel()
    cols = [p_lstm, p_lgb]
    if spec.use_discrepancy:
        cols.append(np.maximum(p_lgb - p_lstm, 0.0))
    return np.column_stack(cols)


def fit_meta(Z, y, spec: MetaSpec = MetaSpec(), seed: int = 42) -> dict:
    """Ajusta los meta-aprendices con `spec` y guarda el soporte que vieron.

    `support` es el mayor objetivo de las filas de ajuste: por encima de él el
    meta extrapola y, si la compuerta está activa, la predicción vuelve a las
    ramas base.
    """
    from lightgbm import LGBMRegressor

    Z = np.asarray(Z, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64).ravel()
    ridge = RidgeCV(alphas=RIDGE_ALPHAS).fit(Z, y)
    if spec.level_mode == "sum_to_one":
        coef = np.asarray(ridge.coef_, dtype=np.float64).copy()
        total = float(coef.sum())
        if abs(total) > 1e-9:
            coef = coef / total
            ridge.coef_ = coef
            ridge.intercept_ = float(np.mean(y - Z @ coef))
    elif spec.level_mode == "convex":
        from scipy.optimize import nnls

        raw_coef, _ = nnls(Z, y)
        total = float(raw_coef.sum())
        coef = (
            raw_coef / total
            if total > 1e-9
            else np.full(Z.shape[1], 1.0 / Z.shape[1])
        )
        ridge.coef_ = coef
        ridge.intercept_ = 0.0
    lgbm = LGBMRegressor(
        max_depth=3, num_leaves=7, n_estimators=120, learning_rate=0.03,
        min_child_samples=20, random_state=seed, verbose=-1,
    ).fit(Z, y)
    return {
        "ridge": ridge,
        "lgbm": lgbm,
        "spec": spec,
        "support": float(y.max()),
        "n_fit": int(y.size),
    }


def predict_meta(meta: dict, p_lstm, p_lgb) -> np.ndarray:
    """Aplica un meta ya ajustado a dos predicciones base según su spec."""
    spec: MetaSpec = meta["spec"]
    Z = meta_design(p_lstm, p_lgb, spec)
    p_meta = (1.0 - spec.blend_lgb) * np.asarray(meta["ridge"].predict(Z)).ravel()
    if spec.blend_lgb > 0.0:
        p_meta = p_meta + spec.blend_lgb * np.asarray(meta["lgbm"].predict(Z)).ravel()

    if spec.support_gate > 0.0:
        anchor = np.maximum(
            np.asarray(p_lstm, dtype=np.float64).ravel(),
            np.asarray(p_lgb, dtype=np.float64).ravel(),
        )
        w = np.clip((anchor - meta["support"]) / spec.support_gate, 0.0, 1.0)
        p_meta = (1.0 - w) * p_meta + w * anchor
    return p_meta


def grouped_folds(units, n_splits: int = 3, seed: int = 42):
    """Pliegues agrupados y equilibrados por unidad, deterministas con semilla."""
    units = np.asarray(units)
    unique = np.unique(units)
    rng = np.random.RandomState(seed)
    shuffled = unique.copy()
    rng.shuffle(shuffled)
    folds = [shuffled[i::n_splits] for i in range(n_splits)]
    out = []
    for held in folds:
        val = np.isin(units, held)
        out.append((np.where(~val)[0], np.where(val)[0]))
    return out


def fit_meta_learners(Z, y, seed: int = 42):
    """Ajusta los dos meta-aprendices sobre un diseño `[p_lstm, p_lgb]`.

    El pipeline lo usa con las filas de la unidad 16. Se midió juntar el vector
    out-of-fold de los cinco motores de ajuste y el resultado se **descartó**: el
    ajuste agrupado aprende un nivel de los motores largos de dev (RUL hasta 88)
    que no se traslada a los motores cortos de test. En la unidad 16 predice una
    media de 39.9 frente a un real de 31.5 y el RMSE crece con `beta` (4.04 en 0,
    10.17 en 1). Se conserva porque es el instrumento que hizo reproducible ese
    resultado negativo; ver `docs/evidencia/informes/informe-2026-10-21-motor16-vs-oof.md`.
    """
    from lightgbm import LGBMRegressor

    Z = np.asarray(Z, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64).ravel()
    ridge = RidgeCV(alphas=RIDGE_ALPHAS).fit(Z, y)
    lgbm = LGBMRegressor(
        max_depth=3, num_leaves=7, n_estimators=120, learning_rate=0.03,
        min_child_samples=20, random_state=seed, verbose=-1,
    ).fit(Z, y)
    return ridge, lgbm


def meta_predict(ridge, lgbm, Z) -> np.ndarray:
    """Reconciliación fija 50/50 de los dos meta-aprendices."""
    Z = np.asarray(Z, dtype=np.float64)
    return 0.5 * np.asarray(ridge.predict(Z)).ravel() + 0.5 * np.asarray(
        lgbm.predict(Z)
    ).ravel()


def score_beta_holdout(p_meta, p_lstm, y, units, cycles, beta_grid=BETA_GRID,
                       span: int = 5) -> dict:
    """Puntúa la rejilla de `beta` en filas que el meta no vio al ajustarse.

    Es el evaluador del diseño agrupado que se descartó: ese meta nunca vio la
    unidad 16, así que era el lugar honesto para puntuarlo. Con el protocolo
    desplegado el meta se ajusta con la propia unidad 16, así que la rejilla se
    puntúa con pliegues agrupados (`select_beta_grouped`).
    """
    p_meta = np.asarray(p_meta, dtype=np.float64).ravel()
    p_lstm = np.asarray(p_lstm, dtype=np.float64).ravel()
    y = np.asarray(y, dtype=np.float64).ravel()
    units = np.asarray(units)
    cycles = np.asarray(cycles, dtype=np.float64)

    rmse_ref = float(np.sqrt(np.mean((y - p_lstm) ** 2)))
    nasa_ref = max(calculate_nasa_score(y, p_lstm), 1e-9)

    rows = []
    for beta in beta_grid:
        blend = p_lstm + float(beta) * (p_meta - p_lstm)
        smoothed = causal_ema_by_unit(blend, units, cycles, span=span)
        rmse = float(np.sqrt(np.mean((y - smoothed) ** 2)))
        nasa = calculate_nasa_score(y, smoothed)
        rows.append({
            "beta": round(float(beta), 2), "rmse": rmse, "nasa": nasa,
            "criterion": rmse / rmse_ref + nasa / nasa_ref,
        })
    frame = pd.DataFrame(rows)
    best = frame.loc[frame["criterion"].idxmin()]
    return {
        "beta": float(best["beta"]),
        "rmse": float(best["rmse"]),
        "nasa": float(best["nasa"]),
        "rmse_lstm_ref": rmse_ref,
        "nasa_lstm_ref": nasa_ref,
        "table": frame,
        "scored_units": sorted(float(u) for u in np.unique(units)),
        "n_rows": int(len(y)),
    }


def select_beta_grouped(
    units,
    cycles,
    y,
    pred_lstm,
    pred_lgb,
    folds=None,
    beta_grid=BETA_GRID,
    span: int = 5,
    use_cycle_feature: bool = True,
    meta_spec: MetaSpec | None = None,
) -> dict:
    """Selecciona `beta` out-of-fold y reporta la dispersión por pliegue.

    Los meta-aprendices que puntúan un pliegue se ajustan solo con los *otros*
    pliegues, así que el criterio nunca se evalúa en filas que ajustaron el meta.
    Si se pasa `meta_spec`, cada pliegue ajusta y aplica exactamente esa spec, de
    modo que el `beta` elegido es el que implica el meta que se despliega.
    """
    from lightgbm import LGBMRegressor

    units = np.asarray(units)
    cycles = np.asarray(cycles, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    pred_lstm = np.asarray(pred_lstm, dtype=np.float64)
    pred_lgb = np.asarray(pred_lgb, dtype=np.float64)

    if folds is None:
        folds = grouped_folds(units, n_splits=3)

    def design(idx):
        """Matriz de diseño del meta-learner para los índices indicados."""
        cols = [pred_lstm[idx], pred_lgb[idx]]
        if use_cycle_feature:
            cols.append(cycles[idx] / 100.0)
        return np.column_stack(cols)

    records = []
    oof_idx, oof_pl, oof_pm = [], [], []
    for fold_id, (fit_idx, score_idx) in enumerate(folds):
        if len(score_idx) == 0 or len(fit_idx) == 0:
            continue
        if np.intersect1d(units[fit_idx], units[score_idx]).size:
            raise AssertionError(
                "grouped split leaked a unit between fit and score: "
                f"{np.intersect1d(units[fit_idx], units[score_idx])}"
            )

        if meta_spec is not None:
            Z_fit = meta_design(pred_lstm[fit_idx], pred_lgb[fit_idx], meta_spec)
            fold_meta = fit_meta(Z_fit, y[fit_idx], spec=meta_spec)
            p_meta = predict_meta(
                fold_meta, pred_lstm[score_idx], pred_lgb[score_idx]
            )
        else:
            Z_fit, Z_score = design(fit_idx), design(score_idx)
            ridge = RidgeCV(alphas=RIDGE_ALPHAS).fit(Z_fit, y[fit_idx])
            lgbm = LGBMRegressor(
                max_depth=3,
                num_leaves=7,
                n_estimators=120,
                learning_rate=0.03,
                min_child_samples=20,
                random_state=42,
                verbose=-1,
            ).fit(Z_fit, y[fit_idx])
            p_meta = 0.5 * ridge.predict(Z_score) + 0.5 * lgbm.predict(Z_score)
        oof_idx.append(score_idx)
        oof_pl.append(pred_lstm[score_idx])
        oof_pm.append(p_meta)

        base = pred_lstm[score_idx]
        rmse_ref = float(np.sqrt(np.mean((y[score_idx] - base) ** 2)))
        nasa_ref = max(calculate_nasa_score(y[score_idx], base), 1e-9)

        best = {"beta": 0.0, "criterion": np.inf, "rmse": np.inf, "nasa": np.inf}
        curve = []
        for beta in beta_grid:
            blend = base + beta * (p_meta - base)
            smoothed = causal_ema_by_unit(
                blend, units[score_idx], cycles[score_idx], span=span
            )
            rmse = float(np.sqrt(np.mean((y[score_idx] - smoothed) ** 2)))
            nasa = calculate_nasa_score(y[score_idx], smoothed)
            crit = rmse / rmse_ref + nasa / nasa_ref
            curve.append({"beta": round(float(beta), 2), "rmse": rmse, "nasa": nasa, "criterion": crit})
            if crit < best["criterion"]:
                best = {"beta": float(beta), "criterion": crit, "rmse": rmse, "nasa": nasa}

        records.append(
            {
                "fold": fold_id,
                "scored_units": sorted(float(u) for u in np.unique(units[score_idx])),
                "fit_units": sorted(float(u) for u in np.unique(units[fit_idx])),
                "beta": best["beta"],
                "rmse_val": round(best["rmse"], 4),
                "nasa_val": round(best["nasa"], 2),
                "rmse_lstm_ref": round(rmse_ref, 4),
                "nasa_lstm_ref": round(nasa_ref, 2),
                "curve": curve,
            }
        )

    betas = np.array([r["beta"] for r in records])
    beta_hat = float(np.median(betas)) if betas.size else 1.0
    spread = {
        "min": float(betas.min()) if betas.size else None,
        "max": float(betas.max()) if betas.size else None,
        "iqr": float(np.subtract(*np.percentile(betas, [75, 25]))) if betas.size else None,
        "n_folds": int(betas.size),
    }
    # Predicciones out-of-fold con el beta elegido, listas para calibrar una
    # banda. Cada fila la puntuó un meta ajustado con los otros motores, así que
    # los residuos no vienen del ajuste del propio meta.
    calib = None
    if oof_idx:
        idx = np.concatenate(oof_idx)
        pl = np.concatenate(oof_pl)
        pm = np.concatenate(oof_pm)
        blend = pl + beta_hat * (pm - pl)
        calib = {
            "units": units[idx],
            "cycles": cycles[idx],
            "y": y[idx],
            "pred_lstm": pl,
            "pred_meta": pm,
            "pred_ema": causal_ema_by_unit(blend, units[idx], cycles[idx], span=span),
            "beta": beta_hat,
            "n_rows": int(idx.size),
        }

    return {"beta": beta_hat, "folds": records, "spread": spread,
            "beta_grid": beta_grid.tolist(), "oof_calib": calib}


def in_sample_beta_diagnostic(
    units, cycles, y, pred_lstm, pred_lgb, beta_grid=BETA_GRID, span: int = 5,
    use_cycle_feature: bool = True,
) -> dict:
    """Reproduce el protocolo antiguo en UNA unidad para mostrar su sesgo.

    Solo diagnóstico: ajusta los meta-aprendices y puntúa la rejilla sobre las
    mismas filas. Se conserva para que el defecto siga siendo reproducible y no
    viva solo en la documentación.
    """
    from lightgbm import LGBMRegressor

    units = np.asarray(units)
    cycles = np.asarray(cycles, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    pred_lstm = np.asarray(pred_lstm, dtype=np.float64)
    pred_lgb = np.asarray(pred_lgb, dtype=np.float64)

    cols = [pred_lstm, pred_lgb]
    if use_cycle_feature:
        cols.append(cycles / 100.0)
    Z = np.column_stack(cols)

    ridge = RidgeCV(alphas=RIDGE_ALPHAS).fit(Z, y)
    lgbm = LGBMRegressor(
        max_depth=3, num_leaves=7, n_estimators=120, learning_rate=0.03,
        min_child_samples=20, random_state=42, verbose=-1,
    ).fit(Z, y)
    p_meta = 0.5 * ridge.predict(Z) + 0.5 * lgbm.predict(Z)

    rmse_ref = float(np.sqrt(np.mean((y - pred_lstm) ** 2)))
    nasa_ref = max(calculate_nasa_score(y, pred_lstm), 1e-9)
    rows = []
    for beta in beta_grid:
        smoothed = causal_ema_by_unit(pred_lstm + beta * (p_meta - pred_lstm), units, cycles, span=span)
        rmse = float(np.sqrt(np.mean((y - smoothed) ** 2)))
        nasa = calculate_nasa_score(y, smoothed)
        rows.append({"beta": round(float(beta), 2), "rmse_val": rmse, "nasa_val": nasa,
                     "criterion": rmse / rmse_ref + nasa / nasa_ref})
    frame = pd.DataFrame(rows)
    best = frame.loc[frame["criterion"].idxmin()]
    return {"beta": float(best["beta"]), "rmse_val": float(best["rmse_val"]),
            "nasa_val": float(best["nasa_val"]), "rmse_lstm_ref": rmse_ref,
            "nasa_lstm_ref": nasa_ref, "table": frame}
