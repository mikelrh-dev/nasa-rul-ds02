# Chuleta de defensa — Reto 1 DS02 (léeme la noche antes)

## Apertura (30 segundos, memorízala)

> "Predigo la vida útil restante de motores DS02 y la convierto en decisión — APTO, INSPECCIÓN o HANGAR — con reglas de negocio. El mejor modelo del track de clase es el MLP E2 (RMSE 7,72 en test); el modelo de producción, y el que defiendo, es el ensemble C (4,338, macro-RMSE 5,02). Y lo importante: el modelo se elige por validación, el test solo confirma."

## El arco (si te pierdes, vuelve aquí)

1. **Honestidad**: GroupKFold por motor; el test ni se mira hasta el final.
2. **La validación manda**: E1 memoriza train (5,23) y pierde en val (7,48) → fuera. Gana E2 (val 7,34).
3. **Una sola lectura**: test una vez (7,72). SHAP en validación fold-0, nunca en test.

## Dónde vive qué (notebook → .py)

| Me preguntan por… | Digo (notebook) | Abro (.py) |
|---|---|---|
| Nulos + `fase_vuelo` | NB01, celdas 5–7 | `src/clase/dataset_clase.py` |
| 5 clásicos, gana XGB | NB02, celdas 4–6 | `src/clase/train_clasicos.py` (`ESPEC`, `ORDEN_SIMPLE`) |
| MLP base/E1/E2/E3 | NB02, celdas 15–20 | `src/clase/train_mlp.py` (`EXPS`, `ORDEN_MLP`) |
| SHAP + permutación | NB02, celdas 23–28 | `src/clase/shap_clase.py` (`top_shap`) |
| Pipeline sin fuga | NB02, celda 4 | `src/clase/pipeline_clase.py` (`make_pipeline`) |
| Reglas R1/R9/R8/R7 | App demo + NB06 | `src/mia/motor.py`, `src/mia/reglas.py` |
| RMSE/MAE qué significan | README + NB02 | `src/ds02_rul/metrics.py` (`evaluate_predictions`) |

## Cifras (solo 6, el resto está en los CSVs)

- Clásicos val: **XGB 8,22** < Ridge 8,28 < SVM 8,29 (test solo XGB: 11,03).
- MLP val: **E2 7,34** < base 7,36 < E3 7,36 < E1 7,48 (test E2: 7,72).
- E1 = overfit de libro: train 5,23 (el mejor) → val 7,48 (el peor).
- Producción: ensemble C **4,338** (macro-RMSE 5,02; U14 8,58 es el agujero). Banda R6 opcional
  recalibrada sobre **14.915** filas OOF puras (sin la unidad 16, que entrenó el meta); la lectura
  por defecto usa la banda del artefacto (17.450).
- Multisemilla [42, 7, 123]: **4,322 ± 0,064** RMSE · 2342,3 ± 43,4 NASA (NB06); NB05 4,330 ± 0,053 · 2343,2 ± 24,1.
- Clase no compite con producción: la entiende; C es el que se despliega.
- Negocio: un AOG ≈ 10.000–15.000 USD/h (rango Boeing; ver `costes_reales_aeronauticos.md` §1); el equivalente 240.000–360.000 USD/día vale solo como hipotético de 24 h continuas. Evitar un AOG paga el sistema. RMSE manda porque un motor parado cuesta más que segundos de CPU.
- SHAP + permutación (en validación): **cycle ≫ T50 > Nc**.

## Los 5 guiones (30 s cada uno)

1. **¿Por qué validación y no test?** → "El test es una lectura con suerte. E1 lo demuestra: mejor en train, peor en val. Elegir por test sería autoengaño."
2. **¿Qué hace `make_pipeline`?** → "Un preprocesado único (StandardScaler + OneHot, fit solo en train) que usan los 5 clásicos y el MLP. Sin él habría fuga."
3. **¿SHAP por qué en validación?** → "SHAP describe al modelo, y el modelo se eligió con validación. Explicar el test sería espiar el examen."
4. **¿7,72 qué significa?** → "Unos 8 ciclos de error medio por motor. RMSE castiga los fallos gordos, que son los caros."
5. **¿El `src/` en tres carpetas?** → "`utils/reglas/n8n` la fachada del reto, `clase/` los experimentos, `mia/` las reglas, `ds02_rul/` la librería de producción. Cada notebook dice en su primera celda de dónde importa."

## Trucos de supervivencia

- **No sabes el detalle** → navega: *"te lo enseño: NB02 celda 15, vive en `src/clase/train_mlp.py`"*. Abrir el fichero y leer el docstring puntúa como 10 de la pregunta individual.
- **Duda de número** → no inventes: *"está en `resultados/comparativa.csv`, fila XGB, columna rmse_val: 8,22"*.
- **Demo app** → `streamlit run app/entrypoints/streamlit_app.py`: métricas del elegido + caso nuevo con decisión (la p=RUL sale junto a la decisión).
- **MLflow / n8n** → MLflow: 17 runs en `mlruns/` (9 fila + 4 ventana + 4 ablación de `cyc_norm`), export en `docs/evidencia/mlflow/comparativa.csv` y capturas; el store es texto, versionado en git y sin binarios. n8n: flujo incluido en `n8n/flujo.json`, inactivo hasta credenciales; no vendas una ejecución real que no existe.

## Noche antes (checklist)

- [ ] Abrir la app una vez y puntuar un caso (que no sea la primera vez en vivo).
- [ ] Recitar la apertura + el arco en voz alta, una vez, con cronómetro.
- [ ] Tener a mano: esta chuleta, `resultados/comparativa.csv`, `resultados/mlp_comparativa.csv`, `docs/evidencia/mlflow/comparativa.csv`.
- [ ] `models/ds02_manifest.json` abre y trae 4.338 (prueba de que lo defendido es lo de disco).
