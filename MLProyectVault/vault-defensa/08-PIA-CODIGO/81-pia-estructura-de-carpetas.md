---
title: PIA · Estructura de carpetas
course: Reto 1 · SAA+PIA+MIA
block: 08 — PIA código
node: C2
indicador: PIA-2
descriptor: 10
spine: false
status: en-curso
tags:
  - pia
  - estructura
  - rubrica/pia-2
---

# PIA · Estructura de carpetas

> [!abstract] En una frase
> La rúbrica dibuja una estructura concreta; nuestro repo hace lo mismo con más módulos. La
> respuesta no es excusarse: es tener la tabla de equivalencias memorizada.

## Nuestra estructura

```
src/
├── clase/        track de clase: dataset, pipeline, 5 modelos, MLP, SHAP
├── ds02_rul/     sistema desplegado: ventanas, BiLSTM, stacking, conformal, SHAP
├── mia/          reglas, motor de decisión, calibración de banda
├── n8n.py        envío al webhook
└── utils.py      utilidades compartidas
app/              dashboard Streamlit + API de decisión
models/           artefactos congelados + manifiesto
n8n/              flujo.json
resultados/       CSVs, figuras y capturas
notebooks/        01…07
```

## La tabla de equivalencias (memorizar)

| La rúbrica dice | Nosotros tenemos |
|---|---|
| `data/raw/` | `archive/CCMaps/N-CMAPSS_DS02-006.h5` |
| `data/processed/` | `app/cache/*.parquet` (ventanas y filas) |
| `notebooks/01_eda.ipynb` | `01_eda_y_contexto.ipynb` |
| `notebooks/02_modelos_A/B` | `02_modelos_clasicos_y_mlp.ipynb` + `05…06` |
| `src/reglas.py` | `src/mia/reglas.py` (+ `motor.py`) |
| `src/n8n.py` | `src/n8n.py` |
| `app/streamlit_app.py` | `app/dashboard_ds02.py` |
| `models/mejor_modelo.joblib` | `models/ensemble.joblib` (+ `mejor_modelo_clase.joblib`) |

## Qué digo

«Seguimos la estructura pedida —datos, notebooks, src, app, models, n8n, resultados—, pero `src`
está partido en tres paquetes porque el proyecto tiene tres capas: el track de clase, el sistema
desplegado y la capa de decisión. `reglas.py` está en `src/mia/reglas.py`; la app es
`app/dashboard_ds02.py`. Es la misma organización con nombres más explícitos.»

## Por qué se dice así

- PIA-2 da 10 con «estructura de carpetas y funciones comentadas + requirements correcto». La
  duda del corrector es si existe `src/reglas.py`: se responde con la tabla, no con una excusa.

## Evidencia

- `requirements.txt` en la raíz; `pyproject.toml` con `packages.find where = src`.
- `src/utils.py`, `src/mia/reglas.py`, `src/n8n.py`, `app/dashboard_ds02.py` existen con ese rol.

## Pregunta probable

**«¿Por qué tres paquetes en `src` y no uno?»**
→ «Porque tienen dependencias distintas: el track de clase usa solo sklearn, el desplegado usa
TensorFlow y LightGBM, y la capa de decisión no depende de ninguno de los dos. Un solo paquete
obligaría a importar TensorFlow para evaluar una regla.»

## Lo que NO digo

- No digo «es lo mismo»: es equivalente y lo demuestro con la tabla.
- No digo que la rúbrica esté mal: explico por qué nuestro corte es más fino.

## Di esto en el tribunal

> «La estructura pedida está: datos, notebooks, src, app, models, n8n y resultados; `src` se parte
> en tres capas porque tienen dependencias distintas.»

## Flashcards #flashcards

- ¿Dónde está `src/reglas.py`? :: en `src/mia/reglas.py`, con el motor en `src/mia/motor.py`.
- ¿Dónde está la app de Streamlit? :: en `app/dashboard_ds02.py`.
- ¿Qué sustituye a `data/processed`? :: `app/cache/*.parquet`, las ventanas ya construidas.
