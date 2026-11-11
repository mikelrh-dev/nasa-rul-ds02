# `src/ds02_rul/` — modelo C, contrato compartido y protocolo

`src/clase/` es la rúbrica; `src/ds02_rul/` es el modelo desplegado y lo que
ambos comparten. La dirección permitida es:

```text
clase  ──▶ ds02_rul
ds02_rul ──✗──▶ clase
```

`tests/test_architecture.py` falla si `ds02_rul` vuelve a importar `clase`.

## Qué es cada bloque

| Bloque | Módulos | Dueño / consumidor |
|---|---|---|
| **Contrato compartido** | `data.py`, `metrics.py` | Lo usan el bundle C y la evidencia de clase. Aquí viven columnas, particiones, imputación, `construir_raw_adaptado` y las métricas. |
| **Protocolo** | `features.py`, `pipeline.py`, `model.py`, `inference.py` | Cómo se ventanea, se preprocesa y se entrena. `clase` los reutiliza a propósito para comparar con el mismo protocolo. |
| **Modelo C** | `ensemble.py`, `stacking.py`, `conformal.py`, `smoothing.py`, `residualizer.py`, `pooling.py`, `persistence.py`, `bundle_c.py`, `shap_c.py`, `puente_c.py` | Artefacto desplegado y su lectura/explicación. |
| **API pública** | `__init__.py` | Reexporta lo que debe poder importarse como `ds02_rul`. |

## Contrato congelado

El bundle `models/ensemble.joblib` está pickled con nombres
`ds02_rul.ensemble.HybridStackingEnsemble` y
`ds02_rul.residualizer.SensorResidualizer`; el `.keras` registra
`ds02_rul.pooling.LastStepPooling`. **No muevas esos tres módulos** sin un shim
de compatibilidad y sin volver a verificar `load_ensemble` / `load_bilstm`.

El escritor del bundle es `bundle_c.py:entrenar`. Para un reentrenamiento en
sombra, sin tocar `models/`:

```bash
python - <<'PY'
from ds02_rul.bundle_c import entrenar
entrenar(out_dir="resultados/_shadow_bundle", write_results=False, write_manifest=False)
PY
```

Ese modo no escribe CSV/PNG ni un segundo manifiesto; el artefacto de sombra no
se carga con `load_ensemble` (verifica contra los manifiestos reales), sino con
`joblib.load` + `keras.models.load_model`, y hay que enlazar el grafo en memoria
antes de predecir:

```python
import joblib, keras
ens = joblib.load("resultados/_shadow_bundle/ensemble.joblib")
ens.bilstm_model = keras.models.load_model("resultados/_shadow_bundle/bilstm_ds02.keras")
```

## Comandos

```bash
# Entrenar y escribir el bundle C real (solo si se decide promover)
python src/ds02_rul/bundle_c.py

# Cargar el bundle congelado y predecir (sin reentrenar)
python - <<'PY'
from ds02_rul.persistence import load_ensemble
ens = load_ensemble("models/ensemble.joblib")
print(ens.scaler.n_features_in_, ens.lgb_standalone.n_features_in_, ens.ridge_meta.n_features_in_)
PY

# Estabilidad multisemilla (semilla 42 desde el manifiesto; 7 y 123 entrenadas)
python scripts/operativo/evaluate_bundle_stability.py
```
