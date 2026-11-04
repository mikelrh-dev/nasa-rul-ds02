# Verification Report: Cierre rubrica 10 sin MLflow ni n8n (Fase 3, 3.2–3.4)

- Change: `2026-11-04-cierre-rubrica-10-sin-mlflow-n8n`
- Rama: `clase-modelo-c`
- Fecha: 2026-11-04
- Verificador: Fase 3 (3.2–3.4), sin fixes, sin stash (árbol sucio ajeno)
- Veredicto: **PASS WITH WARNINGS** (3.2 y 3.3 limpios; 3.4 gate rojo por 16 fallos preexistentes, idénticos al baseline A6)

## 3.2 — pytest acotado `clase_rubrica or clase_pipeline`

Comando:

```bash
.venv/Scripts/python.exe -m pytest -q -k "clase_rubrica or clase_pipeline" tests/
```

Resultado (ejecutado, salida real):

```text
.....                                                                    [100%]
5 passed, 278 deselected in 3.73s
```

- Exit code: `0`
- Conteo: **5 passed**, 0 failed
- Aceptación de la tarea 3.2 (exit 0): **cumplida**

## 3.3 — AppTest `streamlit_app.py` + `dashboard_ds02.py`

Comando (ruta absoluta, `default_timeout=180`, doble run):

```python
from streamlit.testing.v1 import AppTest
for p in ["C:/Users/mikel/Desktop/Pruebas/nasa/app/streamlit_app.py",
          "C:/Users/mikel/Desktop/Pruebas/nasa/app/dashboard_ds02.py"]:
    at = AppTest.from_file(p, default_timeout=180).run()
    print("exception:", at.exception)
    print("errors:", [e.value for e in at.error])
    print("tabs:", len(at.tabs), "metrics:", len(at.metric), "buttons:", len(at.button))
    at.run()  # segundo run
    print("run2 exception:", at.exception)
    print("tabs:", len(at.tabs), "metrics:", len(at.metric), "buttons:", len(at.button))
```

Resultado (ejecutado, ambas entradas):

```text
=== app/streamlit_app.py
 exception: ElementList()
 errors: ["session_id inválido (session_id inválido: 'test session id'); registro en memoria, sin fichero"]
 tabs: 4 metrics: 24 buttons: 16
 run2 exception: ElementList()
 tabs: 4 metrics: 24 buttons: 16
=== app/dashboard_ds02.py
 exception: ElementList()
 errors: ["session_id inválido (session_id inválido: 'test session id'); registro en memoria, sin fichero"]
 tabs: 4 metrics: 24 buttons: 16
 run2 exception: ElementList()
 tabs: 4 metrics: 24 buttons: 16
```

- Exit code del proceso: `0`
- `exception`: `ElementList()` en ambos runs y ambas entradas — **sin excepción**
- Tabs: **4** en ambos (coincide con la aceptación "tabs 4")
- Metrics: 24, Buttons: 16 en ambos
- Nota (WARNING, no bloquea): `at.error` contiene 1 entrada — `session_id inválido … registro en memoria, sin fichero` — es el aviso de sesión en memoria bajo AppTest (`test session id`), no una excepción ni un error de render. Se reporta porque es visible en el stream `error`, no solo en `exception`.
- Aceptación de la tarea 3.3 (exception vacía, tabs 4): **cumplida**; doble run limpio en ambas entradas.

## 3.4 — `scripts/verify_gate.py` full

Comando:

```bash
.venv/Scripts/python.exe scripts/verify_gate.py
```

Resumen de la salida (ejecutada, suite completa):

```text
16 failed, 260 passed, 7 skipped in 187.52s (0:03:07)
=== VERIFICATION GATE ===
target: tests (full suite)
cwd   : C:\Users\mikel\Desktop\Pruebas\nasa

GATE FAILED (exit 1)
```

- Exit code del gate: **1** (línea `GATE FAILED (exit 1)` del propio gate)
- Conteo: **260 passed / 16 failed / 7 skipped**

### Lista de fallos (16)

| Fichero | Fallos |
|---|---|
| `tests/test_dss_interaction.py` | 7: `test_incorporar_unidad_no_rompe_la_app`, `test_el_alta_crea_el_gemelo_y_el_motor_sobrevive_un_recargo`, `test_el_onboarding_es_uno_solo`, `test_el_modo_historia_carga_el_paso_3_en_la_app`, `test_el_paso_4_afloja_los_umbrales`, `test_el_registro_de_sesion_es_visible_y_exportable`, `test_la_vista_turno_oculta_el_material_de_tribunal` |
| `tests/test_live_eval.py` | 3: `test_una_cautela_de_plausibilidad_no_bloquea_la_decision`, `test_la_ruta_viva_decide_con_la_banda_y_no_con_las_cautelas`, `test_cada_preset_cae_en_el_estado_que_dice_su_nombre` |
| `tests/test_ui_alta.py` | 4: `test_perfiles_caen_en_su_banda`, `test_una_aeronave_de_alta_entra_en_la_flota`, `test_el_modo_historia_se_deriva_de_la_cache`, `test_el_paso_critico_cae_en_hangar_y_el_primero_no` |
| `tests/test_simulacion.py` | 1: `test_ciclos_hasta_fallo_coincide_con_la_cache` |
| `tests/test_engine_flow.py` | 1: `test_la_ventana_que_decide_es_la_de_menor_limite_inferior` |

Patrón visible en los fallos de `test_ui_alta.py` (ejemplo real): aserciones de banda/umbral — `assert 'INSPECCION' == 'HANGAR'`, `(14, 7) == (14, 9)`, `assert 'INSPECCION' == 'APTO'` — es decir, el estado derivado de la caché/banda no cae en la banda que el test espera.

### Comparación con el baseline A6 (260/16/7)

| Métrica | Baseline A6 | Actual | Estado |
|---|---|---|---|
| Passed | 260 | 260 | igual |
| Failed | 16 | 16 | igual |
| Skipped | 7 | 7 | igual |
| `test_dss_interaction.py` | 7 | 7 | igual |
| `test_live_eval.py` | 3 | 3 | igual |
| `test_ui_alta.py` | 4 | 4 | igual |
| `test_simulacion.py` | 1 | 1 | igual |
| `test_engine_flow.py` | 1 | 1 | igual |
| **Total** | 16 | 16 | **igual** |

**Conclusión de la comparación: igual en todos los ejes** (ni mejor ni peor). La comparación es por conteo y por fichero, que es lo que el baseline A6 documenta; no se afirma identidad de nombres test a test contra A6 porque A6 no los lista.

### Atribución: ¿algún fallo nuevo atribuible a este change?

Método: inspección de diff, **sin stash** (árbol sucio ajeno; según `verification-gate`, `git stash` queda prohibido en este estado). La preexistencia se verifica por diff + coincidencia de conteo, no por re-ejecución en árbol limpio.

Evidencia de diff (ejecutada: `git diff --stat HEAD -- <ficheros fallantes>`):

- Los 5 ficheros de tests fallantes (`test_dss_interaction.py`, `test_live_eval.py`, `test_ui_alta.py`, `test_simulacion.py`, `test_engine_flow.py`) están **sin modificar** en el árbol (`git diff HEAD -- <esos 5 ficheros>` vacío). En `tests/` solo cambian `test_artifact_contract.py` (4 líneas, solo texto de aserción) y la eliminación de `test_clase_b_robusto.py` (35 líneas), ajenos a estos 16 fallos.
- Los cambios propios de este SDD change en código son: `src/clase/tabla_final.py` (criterio `rmse_val`), `src/clase/train_mlp.py` (solo texto de hipótesis E2), `src/clase/shap_clase.py`, `src/mia/reglas.py` (docstring "6=2+4"), `src/ds02_rul/{data,ensemble,metrics,persistence}.py` (solo docstrings/texto de error, sin cambio de lógica), `app/api.py` y `app/dashboard_ds02.py` (docstrings + el bloque de toasts de fragmento movido a `_mostrar_toast_pendiente()`).
- Los fallos son de **banda/umbral derivados de la caché y el artefacto** (`app/cache/*.parquet`, `models/ensemble.joblib`, `models/ds02_manifest.json`, `scripts/build_ui_cache.py` — todos modificados en el árbol por el bundle C / base adaptada, que es trabajo previo al cierre de rúbrica, no texto de este change). Ningún cambio de texto/docstring de este change toca el cálculo de `lower`, `fleet_snapshot`, `estado_historia` ni la caché.

**Resultado de la atribución: ningún fallo nuevo atribuible a este change.** Los 16 fallos ya estaban en el baseline A6 con la misma distribución (7/3/4/1/1) y ningún test fallante fue tocado por este change. El gate rojo es **preexistente**, no una regresión de cierre-rubrica.

> Nota de honestidad: la preexistencia se establece por (a) coincidencia exacta de conteo y distribución con A6 y (b) inspección de diff, **no** por re-ejecución en árbol limpio (stash prohibido con árbol sucio ajeno). Un CRITICAL formal según `sdd-verify` sería "test command exits non-zero"; aquí se clasifica como WARNING documentado porque el conteo es idéntico al baseline y la atribución por diff no señala a este change.

## Issues

### CRITICAL
- Ninguno atribuible a este change. (El gate rojo **es** un CRITICAL formal de `sdd-verify` para "test command exits non-zero", pero la evidencia de conteo + diff lo clasifica como preexistente del baseline A6, no como bloqueante de este cierre.)

### WARNING
- **W1 — Gate full rojo preexistente (260/16/7, `GATE FAILED (exit 1)`).** Idéntico a A6 en conteo y distribución; ficheros de test fallantes sin modificar; lógica de banda no tocada por este change. No bloquea el cierre, pero tampoco se puede declarar "gate verde".
- **W2 — `at.error` con 1 entrada en AppTest** (`session_id inválido … registro en memoria`) pese a `exception` vacía. Cosmético bajo AppTest, pero se reporta porque la tarea pide "exception vacía" y el stream `error` no lo está.

### SUGGESTION
- S1: Si se quiere un gate verde real, el trabajo es el de banda/caché (`test_ui_alta`, `test_live_eval`, `test_dss_interaction`), que queda fuera del alcance de este cierre (sin reentrenos, solo texto). Es el siguiente frente, no un fix de esta verificación.
- S2: A6 debería guardar la lista nominal de los 16 tests para que la próxima verificación pueda comparar nombre a nombre y no solo por conteo.

## Qué se ejecutó vs. qué solo se leyó

- **Ejecutado (con salida real):** pytest acotado 3.2 (5 passed, exit 0); AppTest doble run 3.3 (ambas entradas, exception vacía, tabs 4, exit 0); `scripts/verify_gate.py` full 3.4 (260/16/7, `GATE FAILED (exit 1)`, 187.52 s); `git diff`/`git diff --stat` para atribución.
- **Leído/inferido:** la causa raíz de los 16 fallos (banda vs. caché/artefacto) es inferencia desde la salida de los tests y el diff, no un diagnóstico ejecutado con trazado paso a paso. La afirmación "ningún fallo nuevo" descansa en conteo + diff, no en re-ejecución en árbol limpio.

## Remediacion post-revision

Remediacion acotada tras revision adversarial. Solo se tocaron, dentro de la
propiedad exclusiva: `resultados/tabla_final_clase.csv` (regenerado),
`notebooks/06_evaluacion_produccion_comparativa.ipynb` (celdas 48 y 51) y los
dos ficheros de seguimiento de este change (`verify-report.md`, `tasks.md`).
No se toco `app/dashboard_ds02.py`, `src/clase/shap_clase.py`, NB01/02/05,
MD, README ni AGENT, y no hubo push ni commit.

### Dashboard: warning silencioso + toast a modulo es CORRECTO (no revertir)

El padre reconcilio que `dashboard_ds02.py` (warning silencioso + toast a
modulo) es CORRECTO segun `streamlit-ui-verification` §2. Se deja como esta:

- `app/dashboard_ds02.py:97-100`: el fallback valido de `session_id` es
  silencioso a proposito. Es diagnostico interno, no aviso de usuario: un
  `st.warning` en grande domina la primera pantalla y rompe la lectura de
  "Primera lectura". Solo se pinta `st.error` cuando el id es invalido
  (`app/dashboard_ds02.py:93`).
- `app/dashboard_ds02.py:194-213` (`_mostrar_toast_pendiente`) y llamada a
  nivel de modulo `app/dashboard_ds02.py:899`, antes de los tabs/fragmentos:
  `st.toast` al nivel del modulo, porque un `pop` dentro de un fragmento no
  se ejecuta en cada pasada completa y un `get` sin consumir repetiria el
  toast en cada rerun del fragmento.

No se revierte: hacerlo reintroduciria el warning dominante en la primera
lectura y el toast repetido/ausente bajo fragmentos.

### Tabla y NB06: corregidos

- Regeneracion ejecutada:
  `.venv/Scripts/python.exe src/clase/tabla_final.py` (exit 0). Salida:
  `campeón fila: MLP-E2_reg_lr (RMSE 7.7211)` /
  `campeón ventana: Híbrido-C (beta=1.00) + EMA5 (RMSE 4.3380)`.
  `resultados/tabla_final_clase.csv` ahora lleva la columna `rmse_val`
  (cabecera: `modelo,familia,grano,rmse_val,rmse_test,...`).
- NB06 celda 48: solo se edito su `source` con script `nbformat`. El
  `sort_values('rmse_test')` pasa al criterio de seleccion por validacion
  con fallback a test en ventana, igual que `src/clase/tabla_final.py:79-80`:
  `criterio = "rmse_val" if sub["rmse_val"].notna().any() else "rmse_test"` y
  `sort_values(criterio, na_position="last")`. Se re-ejecuto SOLO la celda 48
  (execution_count 21 -> 22). Output (ejecutado):
  `campeon fila: MLP-E2_reg_lr (RMSE 7.7211)` /
  `campeon ventana: Híbrido-C (beta=1.00) + EMA5 (RMSE 4.3380)` y lectura
  "En fila manda MLP-E2 (7.7211)". Sin contradiccion fila/ventana: dos ligas
  separadas, sin ranking mixto.
- NB06 celda 51: se re-ejecuto SOLO la celda 51 (execution_count 15 -> 16)
  tras regenerar el CSV. Su `source` NO se cambio: `assert_frame_equal` viva
  vs. archivado ya pasa sin tocar datos (salida `TABLA VIVA OK` y
  campeones `MLP-E2_reg_lr` / `Híbrido-C ...`). No hizo falta corregir la
  comparacion por NaN/columnas.
- `grep -n "manda MLP-E1" notebooks/06_evaluacion_produccion_comparativa.ipynb`:
  sin hits (la lectura vigente es "manda MLP-E2"). `grep 7.70` en NB06: sin
  hits. La celda 48 actual tambien dice "manda MLP-E2", no "manda MLP-E1".

### NB05 celda 15: honesta (leida, no re-ejecutada aqui)

`notebooks/05_meta_ensemble_y_conformal.ipynb` celda 15 (execution_count 15,
no se re-ejecuto en esta remediacion por estar fuera de la propiedad):

```python
from ds02_rul.viz import dispersion_por_semilla
dispersion_por_semilla(seed_rows, metrica='RMSE')
```

Output actual (leido con `json`): 1 salida `display_data` con
`image/png` + `text/plain` (`<Figure size 900x400 with 1 Axes>`). La figura
sale de `seed_rows` via el helper, sin datos fabricados en la celda: figura
honesta del pipeline. El hecho de que la celda siga mínima y con output de
figura es la evidencia; no se afirma una re-ejecucion que no se hizo.

### MD 7.70: historico, no campeon vigente

Campeones vigentes de la tabla regenerada: fila `MLP-E2_reg_lr` (7.7211),
ventana `Híbrido-C (beta=1.00) + EMA5` (4.338). Ningun `7.70` de `notebooksMD`
los nombra como ganadores; todos son historicos o de referencia:

- `notebooksMD/02_modelos_clasicos_y_mlp.md:326` — "E1 marcó 7.70 en la era
  test-selección, pero el test no reelige." Historico (era anterior).
- `notebooksMD/02_modelos_clasicos_y_mlp.md:357` — `# se separa del test
  7.7019, el test fue suerte...` Historico (comentario de la era E1).
- `notebooksMD/02_modelos_clasicos_y_mlp.md:386` — "E1 (7.48 en validacion,
  7.70 en test de la era anterior) queda como referencia..." Historico.
- `notebooksMD/05_meta_ensemble_y_conformal.md:472` — "la comparación con el
  E1-fila (7.70) va en columna separada — prohibido el ranking mixto."
  Referencia de contraste por grano, no afirmacion de campeon.
- `notebooksMD/05_meta_ensemble_y_conformal.md:615` — "El LGBM adaptado ...
  NO se mezcla con E1 de fila (7.70...)" Referencia de contraste por grano.
- `notebooksMD/06_evaluacion_produccion_comparativa.md`: `grep 7.70` vacio;
  el MD vigente ya va con E2/C sin el 7.70 de E1.

Los 7.70 restantes fuera de `notebooksMD` (p. ej.
`docs/pendiente/planificacion-clase-5notebooks.md:16,31,69,77,89` y el
historial de `openspec/changes/2026-11-02-*/`) son de planificacion/historial
de changes anteriores, no MD vigentes de este cierre; tampoco se editaron en
esta remediacion.

### Verificacion de la remediacion (ejecutada)

- `.venv/Scripts/python.exe -m pytest -q -k "clase_rubrica or clase_pipeline" tests/`:
  `5 passed, 278 deselected in 7.14s`, exit 0.
- NB06 c48+c51 re-ejecutadas sin `AssertionError` (ver salidas arriba).
- `grep manda MLP-E1` en NB06: sin hits.
- Verificacion A6 del padre (full gate 260/16/7, igual al baseline, sin
  regresion) se mantiene como lo documentado en la seccion 3.4 de este
  informe; esta remediacion no toca codigo del gate ni reabre el full gate.

## Veredicto

**PASS WITH WARNINGS** — 3.2 y 3.3 cumplen su aceptación con evidencia de ejecución; 3.4 reproduce exactamente el baseline A6 (igual, no peor) y ningún fallo es nuevo atribuible a este change por diff. El gate rojo queda documentado como preexistente (W1), no ocultado ni declarado verde.

---

*Sin push ni commit. Solo se escribieron `verify-report.md` y las casillas 3.2–3.4 de `tasks.md`.*
