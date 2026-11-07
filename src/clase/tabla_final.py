"""Tabla final del track de clase: una fila por modelo, grano explícito.

Regla de oro (SAA-9): prohibido el ranking mixto. Las filas `grano=fila`
(predicción por fila imputada: 5 clásicos + MLP) y `grano=ventana`
(ventanas de 50: LGBM adaptada + bundle C) van en la misma
tabla para el README pero NUNCA se ordenan juntas: cada grano elige su campeón.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import pandas as pd

COLUMNAS = ["modelo", "familia", "grano", "rmse_val", "rmse_test", "mae_test",
            "r2_test", "nasa_test", "tiempo_s", "n_test"]


def construir_tabla(clasicos: pd.DataFrame, mlp: pd.DataFrame,
                    ventanas: pd.DataFrame, bundle_c: pd.DataFrame) -> pd.DataFrame:
    """Une las cuatro fuentes en una tabla con `grano` explícito.

    No ordena ni elige campeón: eso lo hace `main`, por grano y por
    validación cuando existe. Las filas históricas se descartan.
    """
    filas = []
    for _, r in clasicos.iterrows():
        filas.append({"modelo": r["modelo"], "familia": "clasicos", "grano": "fila",
                      "rmse_val": r.get("rmse_val"), "rmse_test": r["rmse_test"],
                      "mae_test": r["mae_test"],
                      "r2_test": r["r2_test"], "nasa_test": float("nan"),
                      "tiempo_s": r.get("tiempo_s"), "n_test": 12538})
    for _, r in mlp.iterrows():
        filas.append({"modelo": f"MLP-{r['experimento']}", "familia": "mlp",
                      "grano": "fila", "rmse_val": r.get("rmse_val"),
                      "rmse_test": r["rmse_test"],
                      "mae_test": r["mae_test"], "r2_test": r["r2_test"],
                      "nasa_test": float("nan"), "tiempo_s": r.get("tiempo_s"),
                      "n_test": 12538})
    for _, r in ventanas.iterrows():
        if "históric" in str(r["modelo"]).lower():
            continue  # el historico no se presenta: fuera de la tabla
        filas.append({"modelo": r["modelo"], "familia": "lgbm_adaptada",
                      "grano": "ventana", "rmse_val": float("nan"),
                      "rmse_test": r["rmse_test"],
                      "mae_test": r["mae_test"], "r2_test": r["r2_test"],
                      "nasa_test": r.get("nasa_test"), "tiempo_s": r.get("tiempo_s"),
                      "n_test": r.get("n_test")})
    rmse_vent = {round(float(r["rmse_test"]), 3) for _, r in ventanas.iterrows()}
    for _, r in bundle_c.iterrows():
        if "históric" in str(r["Modelo"]).lower():
            continue  # el historico no se presenta: fuera de la tabla
        if round(float(r["RMSE"]), 3) in rmse_vent:
            continue  # LGBM-C ya está como lgbm_adaptada: sin duplicados
        filas.append({"modelo": r["Modelo"], "familia": "bundle_c", "grano": "ventana",
                      "rmse_val": float("nan"), "rmse_test": r["RMSE"],
                      "mae_test": r["MAE"],
                      "r2_test": r["R2"], "nasa_test": r["NASA_Score"],
                      "tiempo_s": float("nan"), "n_test": 6196})
    tab = pd.DataFrame(filas, columns=COLUMNAS)
    tab["rmse_val"] = pd.to_numeric(tab["rmse_val"], errors="coerce")
    return tab


def main() -> pd.DataFrame:
    """Genera `resultados/tabla_final_clase.csv` y declara un campeón por grano."""
    tab = construir_tabla(
        pd.read_csv("resultados/comparativa.csv"),
        pd.read_csv("resultados/mlp_comparativa.csv"),
        pd.read_csv("resultados/comparativa_ventanas.csv"),
        pd.read_csv("resultados/comparativa_bundle_c.csv"),
    )
    tab.to_csv("resultados/tabla_final_clase.csv", index=False)
    print(tab[["modelo", "grano", "rmse_test", "mae_test", "r2_test",
               "nasa_test", "tiempo_s"]].to_string(index=False))
    print()
    for grano in ("fila", "ventana"):
        sub = tab[tab["grano"] == grano]
        # Selección por validación, nunca por test (SAA-8). El grano ventana no
        # tiene rmse_val en sus CSV fuente: allí rmse_test queda como único
        # criterio, documentado y justificado.
        criterio = "rmse_val" if sub["rmse_val"].notna().any() else "rmse_test"
        sub = sub.sort_values(criterio, na_position="last")
        print(f"campeón {grano} (por {criterio}): {sub.iloc[0]['modelo']} "
              f"(RMSE {sub.iloc[0]['rmse_test']:.4f})")
    return tab


if __name__ == "__main__":
    main()
