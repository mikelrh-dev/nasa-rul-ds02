# models/ — procedencia de artefactos

> Este fichero es **documentación**: no lo genera ningún script. Si un artefacto
> cambia sin re-ejecutar su escritor, el manifiesto / la celda ancla lo detecta.

| Artefacto | Escritor `.py` (función:línea) | Comando para regenerarlo |
|---|---|---|
| `models/ensemble.joblib` + `bilstm_ds02.keras` + `scaler.joblib` + `models/ds02_manifest.json` | `src/clase/train_ensemble_adaptado.py:entrenar` (183-222; `save_ensemble` en `src/ds02_rul/persistence.py:202`) | `python src/clase/train_ensemble_adaptado.py` |
| `resultados/comparativa_ventanas.csv` + `src/clase/models/lgbm_adaptada.joblib` | `src/clase/train_lgbm_adaptada.py:entrenar` (60-61) | `python src/clase/train_lgbm_adaptada.py` |
| `models/mejor_modelo_clase.joblib` | `src/clase/train_clasicos.py:158` (`entrenar_todo`, `joblib.dump(best_pipe, ...)`) | `python src/clase/train_clasicos.py` |
| `models/mejor_modelo.joblib` | **copia manual** de `mejor_modelo_clase.joblib`, **sin escritor en código** (mismo tamaño: 526049 bytes) | Copia manual — no se regenera sola |
| `resultados/tabla_final_clase.csv` | `src/clase/tabla_final.py` (`main` → `to_csv`, línea 76) | `python src/clase/tabla_final.py` |
| `resultados/mlp_comparativa.csv` + `models/mejor_modelo_clase_E2.joblib` (E2) | `src/clase/train_mlp.py:137` (`to_csv`) y `src/clase/train_mlp.py:142` (`joblib.dump(pipes["E2_reg_lr"], E2_MODEL_PATH)`; `E2_MODEL_PATH` en línea 50) | `python src/clase/train_mlp.py` |

Notas:

- `ensemble.joblib` es el **bundle C desplegado desde 2026-11-04** (seed 42). Se carga
  siempre por `load_ensemble` (verificación SHA-256 antes de deserializar).
- `mejor_modelo.joblib` y `mejor_modelo_clase.joblib` tienen el mismo tamaño y contenido:
  el primero es el alias de rúbrica; el segundo lo escribe `train_clasicos.py:158`.
  Ningún notebook ni script hace la copia: si se borra el alias, no se regenera solo.
- La fila de `comparativa_ventanas.csv` y el joblib `lgbm_adaptada.joblib` comparten escritor:
  `train_lgbm_adaptada.py:entrenar` escribe ambos en la misma ejecución (líneas 60-61).
