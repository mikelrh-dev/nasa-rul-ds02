"""Intervalos de predicción split-conformal para el ensamble de RUL.

Una predicción puntual no basta para desplegar: el mantenimiento decide sobre un
rango. Los intervalos son asimétricos a propósito. La penalización NASA también
lo es (sobreestimar RUL cuesta `exp(d/10)` y subestimarlo `exp(-d/13)`), así que
una banda simétrica gastaría la mitad del ancho en el lado barato.

La calibración es split-conformal: la banda sale de cuantiles de residuos
medidos en filas que el meta-aprendiz nunca vio, agrupados por RUL predicha para
que el ancho crezca donde crece el error. La cobertura se *reporta*, no se da por
supuesta: con solo tres motores de test una cifra global es una afirmación débil,
así que se espera que quien llama la publique por motor.
"""
from __future__ import annotations

import numpy as np

DEFAULT_EDGES = (0.0, 25.0, 50.0, 75.0, np.inf)


def _bin_index(pred: np.ndarray, edges) -> np.ndarray:
    edges = np.asarray(edges, dtype=np.float64)
    # `searchsorted(side='right') - 1` mete un valor justo en un borde en el
    # tramo que empieza ahí, que es lo que se espera de "[25, 50)".
    return np.clip(np.searchsorted(edges, pred, side="right") - 1, 0, len(edges) - 2)


def fit_conformal(y_true, pred, target: float = 0.90, edges=DEFAULT_EDGES,
                  min_rows: int = 100, debias: bool = False) -> dict:
    """Ajusta una banda asimétrica por tramo con residuos `y_true - pred`.

    Los tramos con menos de `min_rows` observaciones usan los cuantiles globales,
    para que una cola dispersa no genere una banda sacada de cuatro puntos.

    `debias=True` resta la mediana de residuos del tramo antes de calcular los
    cuantiles, así que la banda mide *dispersión* en vez de absorber el sesgo de
    nivel de la predicción. En este proyecto los modelos subestiman con RUL alta,
    lo que hace negativos ambos cuantiles y colapsa la banda a un lado; la
    variante sin sesgo la mantiene de dos lados. Es un diagnóstico, no la
    calibración desplegada: una banda sin sesgo deja de cubrir justo donde el
    modelo se desvía, y eso es información, no un defecto.
    """
    y_true = np.asarray(y_true, dtype=np.float64).ravel()
    pred = np.asarray(pred, dtype=np.float64).ravel()
    if y_true.shape != pred.shape:
        raise ValueError(f"shape mismatch: y {y_true.shape} vs pred {pred.shape}")

    alpha = (1.0 - float(target)) / 2.0
    resid = y_true - pred
    global_shift = float(np.median(resid)) if debias else 0.0
    global_lo, global_hi = np.quantile(resid - global_shift, [alpha, 1.0 - alpha])
    idx = _bin_index(pred, edges)

    bins = []
    for b in range(len(np.asarray(edges)) - 1):
        mask = idx == b
        n = int(mask.sum())
        if n >= min_rows:
            shift = float(np.median(resid[mask])) if debias else 0.0
            lo, hi = np.quantile(resid[mask] - shift, [alpha, 1.0 - alpha])
            source = "bin"
        else:
            lo, hi = global_lo, global_hi
            source = "global"
        lo_edge, hi_edge = float(edges[b]), float(edges[b + 1])
        bins.append({
            "index": b,
            # `inf` no es JSON válido; el límite superior abierto se escribe como null.
            "pred_range": [lo_edge, None if np.isinf(hi_edge) else hi_edge],
            "n": n,
            "q_low": round(float(lo), 4),
            "q_high": round(float(hi), 4),
            "source": source,
        })

    return {
        "method": "split-conformal, per predicted-RUL bin, asymmetric"
                  + (", level-debiased" if debias else ""),
        "debias": bool(debias),
        "target_coverage": float(target),
        "alpha_each_side": round(float(alpha), 4),
        "edges": [None if np.isinf(float(e)) else float(e) for e in edges],
        "bins": bins,
        "global_quantiles": [round(float(global_lo), 4), round(float(global_hi), 4)],
        "n_calibration": int(len(y_true)),
    }


def apply_conformal(pred, calib: dict):
    """Convierte predicciones puntuales en límites `(inferior, superior)`.

    Los límites nunca cruzan la predicción: una banda que excluyera su propio
    centro sería un fallo, no un matiz.
    """
    pred = np.asarray(pred, dtype=np.float64).ravel()
    edges = np.asarray(calib["edges"], dtype=np.float64)
    idx = _bin_index(pred, edges)
    lower = np.empty_like(pred)
    upper = np.empty_like(pred)
    for b, spec in enumerate(calib["bins"]):
        mask = idx == b
        if not mask.any():
            continue
        lower[mask] = pred[mask] + spec["q_low"]
        upper[mask] = pred[mask] + spec["q_high"]
    lower = np.minimum(lower, pred)
    upper = np.maximum(upper, pred)
    # La RUL no es negativa, así que el límite inferior se recorta a cero, pero
    # solo donde la predicción también lo es; si no, el recorte dejaría el límite
    # por encima de su centro y rompería `lower <= pred <= upper`.
    lower = np.where(pred >= 0.0, np.clip(lower, 0.0, None), lower)
    return lower, upper


def empirical_coverage(y_true, lower, upper) -> float:
    """Fracción de filas cuya verdad cae dentro de la banda."""
    y_true = np.asarray(y_true, dtype=np.float64).ravel()
    return float(np.mean((y_true >= lower) & (y_true <= upper)))
