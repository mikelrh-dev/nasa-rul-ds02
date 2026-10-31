---
title: Persistencia y notebooks end to end
course: DS02-RUL
block: B0 — Guion defensa
node: N05
status: en-curso
tags:
  - persistencia
  - notebooks
---

# Persistencia y notebooks end to end

## Idea central

El grafo va en `.keras`, el resto en `joblib`, todo con manifiesto y recarga que lo demuestra.

> Si no recarga en proceso limpio, no es entregable.

## ¿Qué problema resuelve?

El notebook viejo ataba `ensemble.joblib` a `__main__` y a una `Lambda` de otra versión de Python. Este diseño lo hace cargable desde `app/mia` sin el notebook.

## Las piezas del modelo mental

### Guardar (`src/ds02_rul/persistence.py:108`)

```python
def save_ensemble(ensemble, out_dir=".", manifest=None):
    model.save(bilstm_path)              # .keras nativo
    joblib.dump(ensemble.scaler, scaler_path)
    detached = _detached_copy(ensemble, bilstm_path)  # grafo por ruta, no picklado
    joblib.dump(detached, ensemble_path)
    # + manifest.json con sha256, alpha, beta, formas
```

- Qué entra: ensemble en memoria + manifiesto.
- Qué sale: `models/ensemble.joblib (468862 B), scaler.joblib, bilstm_ds02.keras (1935767 B), ds02_manifest.json`.
- SHAs: `ensemble 0acd795b…`, `manifest 051e0af4…`, `bilstm 5923d2a1…`.

### Cargar (`src/ds02_rul/persistence.py:189`)

```python
def load_ensemble(path="ensemble.joblib"):
    ensemble = joblib.load(path)  # + re-engancha .keras por ruta
```

- Lo usan `app/ui_inference.py, app/api.py, mia/modelo.py, scripts/*.py` siempre como `models/ensemble.joblib`, nunca la copia de raíz.

### Cadena NB01→NB02→NB03

- NB01 guarda `artifacts/: nb1_dev/test.npz, nb1_aux.joblib, bilstm_seed42.keras` → `[NB1 OK]`.
- NB02 recarga (Puente), no re-entrena 42, guarda `nb2_selection/conformal/eval.joblib + nb2_p_ens.npy` → `[NB2 OK] beta=1.0`.
- NB03 recarga 01+02, multisemilla `[42,7,123]`, `save_ensemble` (celda 51) + `[RELOAD OK] 60.40 vs 58.00` (celda 52). Ejecutar reescribe `models/` y cambia cifras por no-determinismo TF: no re-ejecutar antes de defensa.

## El proceso completo, sin centrarnos en las cuentas

```mermaid
flowchart LR
    NB1[NB01 artifacts] --> NB2[NB02 puente]
    NB2 --> NB3[NB03 multisemilla]
    NB3 --> SAVE[models/]
    SAVE --> RELOAD[RELOAD OK]
```

## Qué no debemos confundir

| Concepto | Qué significa | Qué no significa |
|---|---|---|
| .keras | Grafo nativo | Pickle |
| joblib | Solo scikit/LGBM + ruta | Modelo TF dentro |
| artifacts/ | Paso entre notebooks | Entregable |

## Conexión con los notebooks del repositorio

- NB01 21, NB02 27, NB03 51/52.

## Resumen para recordar

> Keras aparte, joblib sin grafo, manifiesto con sha, recarga que lo prueba.

## Autoevaluación

1. ¿Por qué el grafo no va dentro del joblib?
2. ¿Qué pasa si re-ejecutas NB03?
3. ¿Qué lee `app/` al arrancar?
