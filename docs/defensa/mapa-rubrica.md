# Mapa rúbrica → código real (MIA-2 / PIA-2)

> La rúbrica v5 usa rutas de ejemplo (`src/reglas.py`, `src/utils.py`,
> `app/streamlit_app.py`, `notebooks/01_eda.ipynb`). El repositorio conserva la
> misma función en rutas canónicas. **No se reintroducen fachadas**:
> `tests/test_architecture.py::test_las_fachadas_de_rubrica_no_vuelven` prohíbe
> `src/reglas.py` y `src/utils.py`, y `tests/test_reglas_sombreado.py` protege el
> import canónico para evitar el shadowing por `sys.path`.

## MIA-2 — reglas de decisión

| Rúbrica | Ruta real | Evidencia |
|---|---|---|
| `src/reglas.py`: 6 reglas o más, con prioridad, porqué y una regla de seguridad | `src/mia/reglas.py` | 8 reglas: 2 de corrección + 6 de decisión; cada una con `id`, `prioridad`, `porque` y `accion`; R1 tiene prioridad 10. |
| Regla de seguridad | `src/mia/reglas.py` | R1: si no hay lectura válida o el modelo no puede predecir, se deriva a inspección; nunca se devuelve un APTO sin evidencia. |
| Gate de decisión | `src/mia/motor.py` | Aplica las reglas y devuelve la decisión final. |

**Por qué no existe `src/reglas.py`:** era una fachada histórica. Con `src` en
`sys.path`, un `import reglas` desnudo podía resolver a la fachada y el gate
medía el alias en vez del módulo canónico. El test de arquitectura fija que no
vuelva. La ruta que se defiende es `src.mia.reglas`.

## PIA-2 — estructura de carpetas

| Elemento de la rúbrica | Ruta real | Nota |
|---|---|---|
| `README.md` | `README.md` | Objetivo, datos, pipeline, resultados y defensa. |
| `requirements.txt` | `requirements.txt` | Versiones fijadas. |
| `data/` | `data/raw/`, `data/processed/` | HDF5 original + parquet procesados. |
| `notebooks/01_eda.ipynb` | `notebooks/01_eda_y_contexto.ipynb` | Mismo contenido; nombre descriptivo. |
| `src/reglas.py` | `src/mia/reglas.py` | Ver MIA-2; no se duplica. |
| `src/utils.py` | — | No existe: las utilidades viven en `src/ds02_rul/`, `src/clase/` y `app/lib/`; no se crea una fachada. |
| `src/n8n.py` | `src/n8n.py` | Cliente/construcción del payload de n8n. |
| `app/streamlit_app.py` | `app/entrypoints/streamlit_app.py` | Entrypoint real de Streamlit. |
| `models/mejor_modelo.joblib` | `models/mejor_modelo.joblib` | Copia manual del mejor clásico; el bundle desplegado es `models/ensemble.joblib`. |
| `n8n/flujo.json` | `n8n/flujo.json` | 15 nodos; 3 ramas APTO/INSPECCION/HANGAR. |
| `resultados/` | `resultados/` | CSV, PNG y tablas finales. |

## Frase de defensa (20 s)

«La rúbrica cita rutas de ejemplo. En este repo la lógica de reglas está en
`src/mia/reglas.py` y el entrypoint en `app/entrypoints/streamlit_app.py`; no
duplicamos `src/reglas.py` ni `src/utils.py` porque un test de arquitectura
prohíbe las fachadas y otro protege el import canónico. El mapa de arriba une
cada ruta de la rúbrica con su ruta real.»
