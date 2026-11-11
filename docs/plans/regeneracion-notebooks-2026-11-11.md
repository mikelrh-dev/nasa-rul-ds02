# Regeneración de notebooks — 2026-11-11

Guía para reejecutar los 7 notebooks después de la reestructuración. El objetivo
es regenerar outputs y evidencia **sin tocar el bundle congelado** y sin mezclar
los runs live con los 17 runs históricos de MLflow.

## 0. Preflight de datos (bloqueante)

`data/processed/` no está versionado y **no tiene generador en el repo** (ver
`data/README.md`): en un clon limpio NB01 falla. Comprueba las 8 piezas antes de
empezar; el comando está en `data/README.md` (sección "Preflight") y debe
imprimir `OK`. Si falta algo, para aquí: los notebooks no lo van a crear.

## 1. Antes de empezar

```bash
git branch --show-current          # debe ser refactor/estructura-ds02-clase-2026-11-10
git status --short                 # solo lo esperado; models/ no debe aparecer
sha256sum models/ensemble.joblib models/bilstm_ds02.keras models/scaler.joblib models/ds02_manifest.json > /tmp/models.before
```

Copia de seguridad (no borres nada):

```bash
cp -r mlruns mlruns.bak-2026-11-11
cp -r notebooks/artifacts_c notebooks/artifacts_c.bak-2026-11-11
```

`mlruns/` es el store de texto versionado. Los runs live se **añaden**; los 17
históricos están etiquetados `fuente=historico` y no se sobrescriben.

## 2. Regla de oro: `models/` es de solo lectura

Ningún notebook debe ejecutar `bundle_c.entrenar()` ni `save_ensemble()` contra
`models/`. Si un notebook intenta escribir ahí, para y revisa: el bundle C está
congelado y su SHA es el contrato de la app.

El reentrenamiento de comprobación, si lo haces, va en sombra:

```bash
python - <<'PY'
from ds02_rul.bundle_c import entrenar
entrenar(out_dir="resultados/_shadow_bundle", write_results=False, write_manifest=False)
PY
```

Ese modo no escribe en `models/`, no pisa CSV/PNG y no crea un segundo
manifiesto. No lo cargues con `load_ensemble` (verifica contra los manifiestos
reales); usa `joblib.load` + `keras.models.load_model` y enlaza el grafo antes
de predecir:

```python
import joblib, keras
ens = joblib.load("resultados/_shadow_bundle/ensemble.joblib")
ens.bilstm_model = keras.models.load_model("resultados/_shadow_bundle/bilstm_ds02.keras")
```

## 3. MLflow: qué hace cada notebook

- **Cabecera:** las celdas 0 de NB02–NB07 ejecutan `setup_mlflow()` antes de
  cualquier import de TensorFlow/Keras. No muevas esa celda ni importes `mlflow`
  antes de ella.
- **Store:** `setup_mlflow()` apunta a `mlruns/` (file store) y al experimento
  `ds02-clase`. Los runs live llevan `fuente=live_notebook`.
- **NB01:** la celda 0 tiene el bloque de cabecera colapsado en una sola línea
  comentada; no ejecuta `setup_mlflow`. La celda 39 importa `log_live_run` por su
  cuenta y puede loguear igualmente. Si NB01 no aparece en MLflow, es el
  comportamiento esperado de esta rama: **no lo arregles aquí**, es una tarea
  aparte.
- **NaN/inf:** `log_live_run` los descarta. Los tiempos de `puente_c` son `None`
  a propósito (bundle congelado, nada reentrenado); que falten en MLflow no es un
  error.
- **Timings:** `persist_timings` escribe JSON + CSV con `None`/vacío, nunca NaN.
  No los rellenes a mano.
- **No ejecutes** `scripts/operativo/backfill_mlflow.py` durante esta regeneración: escribe
  los 17 runs históricos y puede mezclar la evidencia curada.

### Decisión sobre `mlruns/`: no borrar ni mover

Los 17 runs históricos **ya están etiquetados** `fuente=historico`. Los de mañana
no los regeneran: `log_live_run()` hace `create_run(...)` y crea runs nuevos con
`fuente=live_notebook`, sin reutilizar ni sobrescribir los históricos. Por eso no
hay que borrar ni mover nada.

- **No borres** `mlruns/` ni runs históricos después de regenerar.
- **No renombres** `mlruns/` a `mlruns-historico/`: `setup_mlflow()` escribe en
  `./mlruns`, `backfill_mlflow.py --check` verifica `./mlruns` y git lo vería
  como un borrado masivo de archivos trackeados.
- **Copia de seguridad sí, movimiento no:**
  `cp -r mlruns mlruns.bak-2026-11-11`.
- **Filtra en la UI** en vez de borrar:
  `tags.fuente = "historico"` o `tags.fuente = "live_notebook"`.
- Después de ejecutar, `git status --short mlruns` mostrará los runs live como
  untracked. Decide si los dejas sin commitear o si restauras el backup; no los
  borres a mano run por run.
- Si restauras el backup, cierra la UI primero:
  `rm -rf mlruns && mv mlruns.bak-2026-11-11 mlruns`. Eso elimina los runs live de
  mañana; es la forma segura de volver a la foto de hoy.
- Si quieres separación física, **copia** el store a `mlruns-historico/` y abre
  una segunda UI con `--backend-store-uri ./mlruns-historico`; no lo muevas ni
  lo mezcles. No es necesario para la defensa.
- El borrado desde la UI de MLflow es soft-delete (`.trash`), no libera el store;
  el borrado manual con `rm -rf` es permanente salvo que git pueda restaurar los
  archivos trackeados.

Si quieres ver el store:

```bash
MLFLOW_ALLOW_FILE_STORE=true mlflow ui --backend-store-uri ./mlruns
```

## 4. Orden de ejecución

```text
01 → 02 → 03 → 04 → 05 → 06 → 07
```

- **04 antes de 05:** NB05 recarga `notebooks/artifacts_c/` que deja NB04.
- **06 después de 03/04/05:** lee CSV/artefactos de esos notebooks.
- **07 es independiente**, pero necesita el bundle C y los parquet adaptados.

Comando recomendado, parando al primer fallo:

```bash
set -e
for nb in notebooks/0*.ipynb; do
  echo "== $nb =="
  jupyter nbconvert --to notebook --execute --inplace "$nb" \
    --ExecutePreprocessor.timeout=-1
done
```

Si falla un notebook, **no sigas** con los dependientes. Corrige el import o el
artefacto que falta y vuelve a empezar por ese notebook.

## 5. Después de ejecutar

```bash
sha256sum -c /tmp/models.before
git status --short models/          # debe estar vacío
python -m pytest tests/test_architecture.py tests/test_clase_*.py tests/test_artifact_contract.py -q
```

Comprueba también:

- `notebooks/artifacts_c/` tiene los joblib de NB04.
- `resultados/` tiene los PNG/CSV de cada notebook.
- `mlruns/` tiene runs live nuevos y los históricos siguen ahí
  (`git status --short mlruns | head`).
- `models/` no aparece en `git status`.

## 6. Si algo sale mal

| Síntoma | Causa probable | Acción |
|---|---|---|
| `ModuleNotFoundError: ds02_rul` | kernel sin `src/` en `sys.path` | usa el kernel `ds02-venv` y ejecuta desde la raíz |
| `FileNotFoundError: train_con_nulos.parquet` | parquet no regenerado | revisa `data/processed/` antes de NB01 |
| NB05 falla al recargar `artifacts_c/` | NB04 no se ejecutó o se borró la carpeta | ejecuta NB04 primero; no borres `artifacts_c/` |
| `load_ensemble` falla por SHA | alguien reescribió `models/` | restaura el bundle desde git; no “arregles” el manifiesto |
| MLflow no muestra un run | NaN descartado o NB01 sin `setup_mlflow` | revisa la sección 3; no añadas NaN |
| `mlruns/` demasiado ruidoso | runs live nuevos | restaura `mlruns.bak-2026-11-11` si necesitas la foto limpia |

## 7. Lo que no se toca en esta regeneración

- `models/ensemble.joblib`, `models/bilstm_ds02.keras`, `models/scaler.joblib`,
  `models/ds02_manifest.json`.
- `src/ds02_rul/ensemble.py`, `residualizer.py`, `pooling.py`: están pickled o
  registrados en el `.keras`.
- La lógica de MLflow (`mlflow_live.py`, `backfill_mlflow.py`): se usa tal cual.
- Los runs históricos de `mlruns/`: no se borran ni se reetiquetan.
