# Spec: Arreglos puntos 3-4 para el 10 (sin MLflow/n8n)

**Change:** `2026-11-03-saa-brechas-10` · **Rama:** `clase-experimental` · **Rúbrica:** v5
**Estado SDD:** SPECIFY (pendiente revisión humana)

## Objective

Cerrar los gaps de los puntos 3 (SAA-8, SAA-9, test-una-vez) y 4 (remates SAA-1/3/4, MIA-1, PIA-2/5) detectados en la auditoría reto-vs-rúbrica-vs-repo, para dejar cada indicador en criterio de 10 **salvo** PIA-4 (MLflow) y MIA-3 (n8n), explícitamente fuera a petición del usuario.

## Tech Stack

Python 3.12.10, scikit-learn 1.9.1, XGBoost 3.4.1, SHAP 0.54.1, pandas 3.0.6, kernel notebooks `ds02-venv`. CPU solo (sin GPU en este change).

## Commands

```bash
python -m pytest tests/test_clase_clasicos.py tests/test_clase_mlp.py tests/test_clase_shap.py tests/test_clase_tabla.py -q
python -m track_clase.train_clasicos      # ~1-2 min CPU (re-entreno clásicos)
python -m track_clase.train_mlp           # ~2 min CPU (MLP base+3)
python -m track_clase.shap_clase          # segundos (XGB + TreeExplainer, 200 filas)
```

## Project Structure (ficheros que toca el change)

```
track_clase/train_clasicos.py   → columnas de validación + selección por val (SAA-8, test-una-vez)
track_clase/train_mlp.py        → coherencia selección por val (si aplica)
track_clase/shap_clase.py       → explicar validación, no test (SAA-9)
tests/test_clase_*.py           → RED primero: val presente, SHAP no usa test (TDD)
notebooks/01_eda_y_contexto.ipynb      → markdown: IA fuerte (SAA-1), descarte (SAA-3), verificar comentarios (SAA-4)
notebooks/02_modelos_clasicos_y_mlp.ipynb → celdas espejo 2/4/13/15/27-29 + CV visible (SAA-8/9)
track_clase/README.md + README.md       → negocio € (MIA-1), modelo elegido (PIA-5), estructura (PIA-2), errores-empresa (SAA-8)
requirements.txt                        → sin cambios (mlflow fuera de este change)
track_clase/PENDIENTE_10.md             → marcar [x] con evidencia al cerrar
```

## Code Style

Respetar el existente: funciones puras + docstrings en `track_clase/`, TDD con RED antes de tocar lógica, seeds fijas (42 entreno, 7 SHAP/muestras). No reescribir celdas que funcionan; edición mínima del `.ipynb`.

## Testing Strategy

- TDD: test RED que falle antes del fix (p. ej. `comparativa.csv` sin columnas val; SHAP usando `X_test`).
- Tras cada slice: `pytest tests/test_clase_*.py -q` verde + `git status` limpio salvo ficheros del slice.
- Notebooks: solo celdas tocadas; ejecución completa la hace el usuario (ver Boundaries).

## Boundaries

- Always: un slice = un indicador; tests verdes antes de pasar al siguiente; actualizar `PENDIENTE_10.md` al cerrar cada gap.
- Ask first: si el ganador por validación ≠ SVM (reescribe el relato "modelo elegido"); cualquier re-entreno >10 min; tocar `models/`, `src/ds02_rul/`, `mia/`, `app/cache/`.
- Never: MLflow y n8n en este change (acordado fuera); commit de `.h5`/parquets pesados nuevos; ejecución completa de notebooks (la hace el usuario); afirmar el 10 sin evidencia.

## Success Criteria (por slice, verificable)

1. **SAA-8:** `comparativa.csv` trae train+val (+test solo lectura final), NB02 lo muestra, README explica errores para la empresa.
2. **Test-una-vez:** ningún `train_*.py` ordena por `rmse_test`; el elegido sale de validación.
3. **SAA-9:** `shap_importancia.*` generado desde validación + celdas 27-29 retejidas ("validación, no test").
4. **Remates:** SAA-1 (párrafo IA fuerte), SAA-3 (descarte+motivo), SAA-4 (5× "qué veo/conclusión"), MIA-1 (cifra €), PIA-2 (estructura justificada), PIA-5 ("modelo elegido" atado) — todo visible en README/notebooks.

## ASSUMPTIONS (corregidme o sigo con estas)

1. Validación = medias del `GroupKFold(3, groups=unit)` ya usado; SHAP-validación = unidades del fold-0, 200 filas, seed 7.
2. Yo ejecuto scripts (minutos CPU) + verifico CSV/PNG; las celdas retocadas las re-ejecuto solo si son baratas y aisladas — la ejecución completa del notebook la hace el usuario.
3. La permutación se mantiene como lectura complementaria (no sustituye SHAP para el 10).
4. Si validación corona otro modelo distinto del SVM, NO lo cambio en silencio: lo traigo a revisión (pregunta 1).

## Open Questions → ver preguntas al final del mensaje (gate).
