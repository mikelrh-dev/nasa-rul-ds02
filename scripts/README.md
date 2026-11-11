# scripts/ — cuatro zonas

Regla para decidir dónde va un script nuevo:

| Lo usa… | Dónde va |
|---|---|
| un notebook o `src/` | no va aquí: `src/ds02_rul/` o `src/clase/` |
| la app o el uso diario | `operativo/` |
| para generar notebooks o caché | `build/` |
| para medir o congelar evidencia | `auditoria/` |
| nadie (etapa cerrada) | `legacy/` |

## operativo/ — lo que se ejecuta para operar

- `verify_gate.py` — gate completo: lanza `pytest tests/` y resume el resultado.
- `backfill_mlflow.py` — escribe/verifica/exporta los 17 runs curados de MLflow.
- `evaluate_bundle_stability.py` — reentrena el bundle C con varias semillas y agrega RMSE/NASA.
- `predict_ds02.py` — CLI de inferencia DS02 (una ventana, un motor o lista de unidades).
- `anclar_raiz_pylance.py` — helper de editor (Pylance); no afecta al runtime.

## build/ — lo que genera artefactos derivados

- `build_ui_cache.py` — construye `app/cache/` desde `models/` para la app sin TensorFlow.
- `build_07_shap_c_notebook.py` — regenera el notebook 07 cuando cambia su sección SHAP.

## auditoria/ — medir y congelar evidencia

- `freeze_rules_evidence.py` — gate de la capa de reglas (RULES-06, ADR-009); deriva o verifica la banda.
- `freeze_oof_instrument.py` — deriva, escribe y comprueba `src/mia/instrumento_oof.npz`.
- `make_clase_checksums.py` — recalcula los checksums del track de clase.
- `p0_density_control.py` — sonda de densidad del preprocesado (P0).
- `p1_oof_cache.py` — construye el caché OOF que consume el gate de reglas.
- `p1_meta_support.py` — mide el soporte del meta-learner por motor (P1).
- `ablate_meta_cycle.py` — ablación del contador de ciclos en el meta.
- `evaluate_model_quality.py` — informe de calidad del bundle (RMSE/NASA por tramo y motor).

## legacy/ — etapas cerradas

No se ejecuta. Cada fichero y su sustituto están en [`legacy/README.md`](legacy/README.md).
