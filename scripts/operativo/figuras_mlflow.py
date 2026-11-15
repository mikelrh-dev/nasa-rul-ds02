"""Figuras de apoyo del README generadas desde el export de MLflow.

Entrada: `docs/evidencia/mlflow/comparativa.csv` (export del store de 17 runs).
Salida:  `docs/evidencia/mlflow/figura_*_rmse.png` (resúmenes legibles por grano).

Las capturas `compare_*.jpg` siguen siendo la evidencia dentro de la herramienta;
estas figuras son el resumen reproducible que acompaña a la tabla.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "docs" / "evidencia" / "mlflow" / "comparativa.csv"
OUT = ROOT / "docs" / "evidencia" / "mlflow"

NOMBRES_FILA = {
    "clasico__regresion": "Ridge",
    "clasico__knn": "KNN",
    "clasico__rf": "Random Forest",
    "clasico__svm": "SVR",
    "clasico__xgb": "XGBoost",
    "mlp__base": "MLP base",
    "mlp__E1_capacidad": "MLP E1 capacidad",
    "mlp__E2_reg_lr": "MLP E2 reg-lr",
    "mlp__E3_batch": "MLP E3 batch",
}
NOMBRES_VENTANA = {
    "bundle__lgbm_c": "LGBM-C",
    "bundle__bilstm_c": "BiLSTM-C",
    "bundle__bilstm_ema5": "BiLSTM+EMA5",
    "prod__bundle_c": "Híbrido-C + EMA5",
}
NOMBRES_ABLACION = {
    "ablacion__off__bilstm_ema5": "OFF",
    "ablacion__off_delta__bilstm_ema5": "OFF + delta",
    "ablacion__on__bilstm_ema5": "ON",
    "ablacion__on_delta__bilstm_ema5": "ON + delta",
}
COLOR_BASE = "#4c78a8"
COLOR_DESTACADO = "#d95f02"


def cargar() -> list[dict]:
    with open(CSV, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def barra_horizontal(
    filas: list[dict],
    campo: str,
    titulo: str,
    ruta: Path,
    nombres: dict,
    clave: str,
    destacados: set[str],
) -> None:
    orden = sorted(filas, key=lambda r: float(r[campo]), reverse=True)
    etiquetas = [nombres.get(r[clave], r[clave]) for r in orden]
    valores = [float(r[campo]) for r in orden]
    colores = [COLOR_DESTACADO if r[clave] in destacados else COLOR_BASE for r in orden]
    alto = max(3.2, 0.52 * len(orden) + 1.6)
    fig, ax = plt.subplots(figsize=(8.2, alto))
    barras = ax.barh(etiquetas, valores, color=colores, height=0.62)
    tope = max(valores)
    for barra, valor in zip(barras, valores):
        ax.text(
            valor + tope * 0.012,
            barra.get_y() + barra.get_height() / 2,
            f"{valor:.3f}",
            va="center",
            fontsize=9,
        )
    ax.set_title(titulo, fontsize=12, pad=10)
    ax.set_xlabel(campo.replace("_", " "), fontsize=10)
    ax.set_xlim(0, tope * 1.12)
    ax.grid(axis="x", alpha=0.3)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=9)
    fig.text(
        0.01,
        0.01,
        "Fuente: comparativa.csv (export del store MLflow, 17 runs)",
        fontsize=7,
        color="gray",
    )
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(ruta, dpi=160)
    plt.close(fig)


def main() -> None:
    filas = cargar()
    fila = [r for r in filas if r["grano"] == "fila"]
    ventana = [r for r in filas if r["grano"] == "ventana"]
    ablacion = [r for r in filas if r["grano"] == "ablacion"]

    barra_horizontal(
        fila,
        "rmse_val",
        "Grano fila: RMSE de validación por modelo (GroupKFold por motor)",
        OUT / "figura_fila_rmse.png",
        NOMBRES_FILA,
        "run_key",
        {r["run_key"] for r in fila if r.get("seleccion")},
    )
    barra_horizontal(
        ventana,
        "rmse_test",
        "Grano ventana: RMSE test por run (uds 11/14/15)",
        OUT / "figura_ventana_rmse.png",
        NOMBRES_VENTANA,
        "run_key",
        {r["run_key"] for r in ventana if r.get("rol") == "produccion"},
    )
    barra_horizontal(
        ablacion,
        "rmse_test",
        "Ablación cyc_norm: RMSE test por variante (BiLSTM+EMA5)",
        OUT / "figura_ablacion_rmse.png",
        NOMBRES_ABLACION,
        "run_key",
        set(),
    )
    print("figuras escritas en", OUT)


if __name__ == "__main__":
    main()
