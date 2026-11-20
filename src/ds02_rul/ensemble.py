"""Bundle de inferencia: BiLSTM + LightGBM tabular + meta-aprendiz + EMA causal.

La clase vive aquí (no en un notebook) para que `joblib` guarde un nombre
cualificado por módulo y el artefacto pueda cargarse desde cualquier proceso. El
grafo Keras no se serializa dentro del bundle a propósito: se guarda de forma
nativa como `.keras` y se engancha al cargar con
`ds02_rul.persistence.load_ensemble`.
"""
from __future__ import annotations

import os
import warnings

import numpy as np

from .smoothing import causal_ema_by_unit

PARADIGM = (
    "Hybrid Stacking (BiLSTM triple-pooling + LGBM residualizado + "
    "RidgeCV/LGBM meta + EMA5)"
)


class HybridStackingEnsemble:
    """BiLSTM campeón + rama tabular reconciliados por un meta-aprendiz.

    Parámetros
    ----------
    bilstm_model : keras.Model o None
        Se engancha directamente o se resuelve de forma perezosa desde
        `bilstm_path`.
    lgb_standalone : lightgbm.LGBMRegressor
        Rama tabular sobre el resumen de ventana de 92/93 columnas.
    ridge_meta, lgb_meta : estimadores
        Meta-aprendices sobre `[pred_lstm, pred_lgb]`. El reloj no se le ofrece a
        esta capa a propósito: con `cyc_norm` disponible se llevaba casi el 100 %
        del peso y el "ensamble" estaba leyendo un contador.
    conformal : dict o None
        Banda de predicción calibrada (ver `ds02_rul.conformal`). Si existe,
        `predict_interval` devuelve `(punto, inferior, superior)`.
    residualizer : SensorResidualizer
    scaler : sklearn.preprocessing.StandardScaler
        Ajustado sobre los 18 canales crudos.
    scaler_w : sklearn.preprocessing.StandardScaler
        Escalador de régimen. Se guarda por trazabilidad; la inferencia deriva el
        bloque de régimen del `scaler` global, que es numéricamente idéntico.
    n_op : int
        Número de canales operativos (4 en DS02).
    """

    def __init__(
        self,
        bilstm_model,
        lgb_standalone,
        ridge_meta,
        lgb_meta,
        residualizer,
        scaler,
        scaler_w,
        n_op: int,
        window_size: int = 50,
        beta: float = 1.0,
        ema_span: int = 5,
        bilstm_path: str | None = None,
        paradigm: str = PARADIGM,
        conformal: dict | None = None,
    ):
        self.bilstm_model = bilstm_model
        self.lgb_standalone = lgb_standalone
        self.ridge_meta = ridge_meta
        self.lgb_meta = lgb_meta
        self.residualizer = residualizer
        self.scaler = scaler
        self.scaler_w = scaler_w
        self.n_op = int(n_op)
        self.window_size = int(window_size)
        self.beta = float(beta)
        self.ema_span = int(ema_span)
        self.bilstm_path = bilstm_path
        self.paradigm = paradigm
        self.conformal = conformal

    # ------------------------------------------------------------------ model
    def _resolve_model(self):
        """Devuelve el modelo Keras y lo carga de `bilstm_path` la primera vez."""
        if self.bilstm_model is None:
            if not self.bilstm_path:
                raise RuntimeError(
                    "ensemble has no attached Keras model and no bilstm_path; "
                    "load it with ds02_rul.persistence.load_ensemble"
                )
            if not os.path.exists(self.bilstm_path):
                raise FileNotFoundError(
                    f"BiLSTM artifact not found at {self.bilstm_path!r}. "
                    "Load the bundled model with ds02_rul.persistence.load_ensemble."
                )
            from .persistence import load_bilstm

            self.bilstm_model = load_bilstm(self.bilstm_path)
        return self.bilstm_model

    # ---------------------------------------------------------------- predict
    def predict(self, X_raw_windows, cycles, units=None) -> np.ndarray:
        """Puntúa ventanas crudas `(n, ventana, 18)` y devuelve una RUL por ventana.

        `units` debe identificar el motor de cada ventana. Si se omite, todas las
        ventanas caen en una sola serie EMA, que suaviza entre motores distintos
        y produce números creíbles pero incorrectos; se emite un aviso para que
        no ocurra por accidente.
        """
        X_raw_windows = np.asarray(X_raw_windows, dtype=np.float64)
        n = X_raw_windows.shape[0]
        if X_raw_windows.ndim != 3:
            raise ValueError(f"expected (n, window, channels), got {X_raw_windows.shape}")
        if X_raw_windows.shape[1] != self.window_size:
            raise ValueError(
                f"window length {X_raw_windows.shape[1]} does not match the "
                f"artifact contract ({self.window_size})"
            )
        cycles = np.asarray(cycles, dtype=np.float64).ravel()
        if cycles.shape[0] != n:
            raise ValueError(f"cycles has {cycles.shape[0]} rows, expected {n}")

        if units is None:
            warnings.warn(
                "units=None: all windows are treated as ONE engine, so the causal "
                "EMA smooths across unrelated engines. Pass per-window unit ids.",
                UserWarning,
                stacklevel=2,
            )
            units = np.zeros(n)
        units = np.asarray(units).ravel()

        flat = X_raw_windows.reshape(-1, X_raw_windows.shape[2])
        X_scaled = self.scaler.transform(flat).reshape(X_raw_windows.shape).astype(np.float32)

        model = self._resolve_model()
        seq = self._sequence(X_scaled, cycles, model.input_shape)
        p_lstm = np.asarray(model.predict(seq, verbose=0)).ravel()

        tab = self._tabular(X_scaled, cycles)
        p_lgb = np.asarray(self.lgb_standalone.predict(tab)).ravel()

        # El meta-aprendiz puede haberse entrenado con la variable de ciclo o
        # sin ella; se respeta el ancho con el que se ajustó en vez de suponerlo.
        n_meta = int(getattr(self.ridge_meta, "n_features_in_", 3) or 3)
        columns = [p_lstm, p_lgb]
        if n_meta >= 3:
            columns.append(cycles / 100.0)
        Z = np.column_stack(columns)
        if Z.shape[1] != n_meta:
            raise ValueError(
                f"meta-learner expects {n_meta} features, built {Z.shape[1]}"
            )
        p_meta = 0.5 * np.asarray(self.ridge_meta.predict(Z)).ravel() + 0.5 * np.asarray(
            self.lgb_meta.predict(Z)
        ).ravel()

        p_raw = p_lstm + self.beta * (p_meta - p_lstm)
        p = causal_ema_by_unit(p_raw, units, cycles, span=self.ema_span)
        return np.clip(p, 0.0, None)

    def predict_interval(self, X_raw_windows, cycles, units=None):
        """Predicción puntual más su banda calibrada.

        Está separada de `predict` a propósito: el contrato de estimación puntual
        que usan la API y los tests no cambia, y quien quiera incertidumbre la
        pide explícitamente.
        """
        from .conformal import apply_conformal

        if self.conformal is None:
            raise RuntimeError(
                "this bundle has no conformal calibration; rebuild it with "
                "conformal=fit_conformal(...) or call predict() for the point estimate"
            )
        point = self.predict(X_raw_windows, cycles, units)
        lower, upper = apply_conformal(point, self.conformal)
        return point, lower, upper

    # --------------------------------------------------------------- internals
    def _sequence(self, X_scaled: np.ndarray, cycles: np.ndarray, input_shape) -> np.ndarray:
        """Añade el canal de ciclo normalizado cuando el grafo lo espera."""
        expected = input_shape[-1]
        if expected == X_scaled.shape[2]:
            return X_scaled
        if expected != X_scaled.shape[2] + 1:
            raise ValueError(
                f"artifact expects {expected} channels but received {X_scaled.shape[2]}"
            )
        cyc = (np.asarray(cycles, dtype=np.float64).reshape(-1, 1, 1) / 100.0)
        cyc = np.repeat(cyc, X_scaled.shape[1], axis=1).astype(np.float32)
        return np.concatenate([X_scaled, cyc], axis=2)

    def _tabular(self, X_scaled: np.ndarray, cycles: np.ndarray) -> np.ndarray:
        """Reconstruye el resumen de ventana igual que se entrenó la rama tabular."""
        W_win = X_scaled[:, :, : self.n_op]
        Xs_win = X_scaled[:, :, self.n_op :]
        # Los modelos de residuos se ajustaron con sensores crudos; se deshace el escalado global.
        Xs_raw = (
            Xs_win.astype(np.float64) * self.scaler.scale_[self.n_op :]
            + self.scaler.mean_[self.n_op :]
        )
        Xs_res = self.residualizer.transform(
            W_win.reshape(-1, self.n_op).astype(np.float64),
            Xs_raw.reshape(-1, Xs_raw.shape[2]),
        ).reshape(Xs_win.shape)

        op = W_win.astype(np.float64)
        xs = Xs_res.astype(np.float64)
        blocks = [
            op.mean(axis=1),
            op[:, -1, :],
            xs.mean(axis=1),
            xs[:, -1, :],
            xs.std(axis=1),
            xs[:, -10:, :].mean(axis=1),
            xs[:, -1, :] - xs[:, 0, :],
            xs[:, -5:, :].mean(axis=1) - xs[:, :5, :].mean(axis=1),
        ]
        n_features = int(getattr(self.lgb_standalone, "n_features_in_", 0) or 0)
        if n_features == 93:
            blocks.insert(0, (cycles.reshape(-1, 1) / 100.0))
        elif n_features not in (0, 92):
            raise ValueError(f"unexpected tabular width {n_features}; expected 92 or 93")
        return np.hstack(blocks).astype(np.float32)
