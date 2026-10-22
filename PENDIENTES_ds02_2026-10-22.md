# Pendientes DS02 — traspaso para el 2026-10-22

Documento de traspaso: qué quedó cerrado, qué se verificó, qué falta y **cuánto
cuesta cada cosa**. Cinco minutos de lectura antes de tocar código.

> Las horas son estimación por lectura del código, no medidas. La única que puedo
> prometer casi exacta es la del punto 3. Los números de línea son referencia, no
> contrato: si el fichero se movió, busca por símbolo.

---

## 1. Estado al cerrar

### Arreglado en esta tanda

| Arreglo | Dónde | Test que lo sostiene |
| --- | --- | --- |
| Reemplazar gemelo conservando la RUL real; borrar gemelo sin tocar el hangar | `app/twin.py` (`registrar(..., reemplazar=)`, `eliminar`), `app/dashboard_ds02.py` (casilla «Reemplazar la serie guardada», expander «Eliminar un gemelo») | `test_registrar_puede_reemplazar_y_conserva_la_verdad`, `test_eliminar_saca_un_gemelo_y_deja_el_resto`, `test_reemplazar_el_gemelo_desde_la_pestana_en_vivo`, `test_el_panel_de_gemelos_documenta_y_elimina` |
| Tope de 5 000 filas cortado antes de cargar Keras | `app/ui_inference.py` (`MAX_FILAS`, `preflight`, `score_table`) | `test_a_table_over_the_row_cap_is_rejected_before_the_model` |
| Orden de un gemelo (JSON + CSV) desde la serie guardada | `app/dashboard_ds02.py` (expander «Documentar un gemelo»), `app/ui_data_loader.py` (`work_order_csv` emite `rul_real` vacía si no hay verdad) | `test_la_orden_de_un_gemelo_sale_de_la_serie_guardada` |

Detalle menor: el nombre del fichero de la orden se sanea (`slug_doc`) porque el id
lo escribe el usuario y un `/` rompía la descarga.

Spec y tareas alineadas: `openspec/changes/2026-10-21-ds02-engine-twin/`
(`specs/ds02-live-evaluation`, `specs/ds02-dss-ui`, `tasks.md` 1.5 / 2.6-2.8 / 6.5).

### Verificación

| Check | Resultado | Nota |
| --- | --- | --- |
| `pytest tests -q` | **139 passed**, exit 0 | Ejecutado **después** del último cambio de código |
| Servidor real | `/_stcore/health` **200**; tras `kill`, `down` | Puerto liberado |
| Gate de evidencias | **exit 0**, cobertura **0.9012** | **No se repitió**: no cambió el gate ni `mia/` desde su última ejecución |

### Estado del árbol

Nada commiteado. Modificados: `INFORME_reglas_oof.md`, `app/dashboard_ds02.py`,
`app/ui_data_loader.py`, `app/ui_inference.py`, `app/ui_rules.py`, `mia/reglas.py`,
`scripts/freeze_rules_evidence.py`, `tests/{test_dss_ui,test_live_eval,test_ui_rules}.py`.
Nuevos: `app/hangar.py`, `app/twin.py`, `AUDITORIA_ds02_2026-10-21.md`, los dos
`openspec/changes/…`, `tests/{test_twin,test_hangar,test_audit_fixes,test_engine_flow}.py`.

`models/` y `app/cache/` no se tocaron; `scripts/freeze_rules_evidence.py` viene
modificado de la tanda anterior (gate en 0 con 0.9012 tras esos cambios).

---

## 2. Backlog con coste, de un vistazo

| # | Qué | Coste | Riesgo | Toca |
| --- | --- | --- | --- | --- |
| 3 | Cortar el CSV **antes** de leerlo entero | 20-60 min | casi nulo | `app/dashboard_ds02.py`, un test |
| 1a | Exportar/importar gemelos en JSON | ~1 h | bajo | `app/twin.py`, panel de flota, un test |
| 1b | Persistencia real (JSON atómico) | ~medio día | medio: concurrencia, corrupción | módulo nuevo `app/state.py`, 5 call sites, tests |
| 1c | Persistencia en SQLite | 3-4 h | bajo-medio: esquema y migración | `app/state.py` con esquema mínimo, 5 call sites, tests |
| 2a | Varios puntos de verdad por gemelo | 2-3 h | bajo | `app/twin.py`, panel, `test_twin.py` |
| 2b | Validación con verdad OOF conocida | ~2 h | bajo | script/test nuevo, sin tocar la app |
| 4a | Ocultar la banda que no decide | ~1 h | bajo | `app/dashboard_ds02.py` |
| 4b | Un solo número canónico en UI y órdenes | ~1 día | medio | ruta de decisión, órdenes, KPI, tests, ADR |

---

## 3. Detalle

### 3.1 Persistencia de gemelos y hangar — la limitación más visible

**Hoy:** los dos registros viven en `st.session_state.setdefault("twins"/"hangar", {})`
(~línea 40) y se escriben en **cinco sitios** del tablero (~666, 722, 789, 821, 1583).

**Lo bueno:** no hay que serializar nada a mano. `twin` y el registro de hangar son
dicts puros (`id`, `source`, `fingerprint`, `created_at`, `banda`, `correccion`,
`umbrales`, `contrato`, `serie`, `truth`; y `unidad`, `estado`, `entrada`,
`eventos`), así que `json.dumps` los lleva tal cual.

**Tres opciones, de barata a buena:**

- **1a. Export/import de gemelos (1 h).** Botones `download_button` del registro
  completo y `file_uploader` que valide y **fusione por id** (rechazando duplicados
  o pidiendo reemplazo, como ya hace `registrar`). No resuelve el cierre accidental,
  pero no hay ficheros sueltos, ni concurrencia, ni corrupción.
- **1b. JSON en disco (medio día).** `app/state.py` con `cargar()`/`guardar()`,
  escritura atómica (`tmp` + `os.replace`), `STATE_DIR` inyectable para tests y
  `version: 1`. `app/state/` al `.gitignore`. Un `guardar()` que envuelva escritura
  y persistencia en los cinco call sites.
- **1c. SQLite (3-4 h).** Lo mismo, pero gratis en concurrencia y sin fichero a medio
  escribir. Es lo que yo elegiría si esto deja de ser demo.

**Preguntas que hay que contestar antes:** ¿dos pestañas escribiendo a la vez es un
caso real o solo teórico? ¿el fichero corrupto se pone en cuarentena o la app falla
en cerrado? ¿los gemelos son datos del usuario (nunca al repo) o fixtures de demo?

**Criterio de aceptación:** cerrar y reabrir la pestaña conserva gemelos, hangar y
verdades; un fichero inválido no rompe el arranque; los tests no escriben en el
árbol real.

### 3.2 La verdad es manual y de un punto por gemelo

Son dos problemas separados:

- **2a. Varios puntos (2-3 h).** `truth: dict` → `truths: list`. Tocar `con_verdad`,
  `metricas_verdad` (hoy se queda con el ciclo más cercano), `resumen` (la MAE pasa a
  ser sobre puntos, no sobre gemelos) y el expander. Retrocompatible: si el gemelo
  trae `truth` antigua, se lee como lista de uno.
- **2b. Precisión defendible (2 h, sin datos nuevos).** La verdad reportada a mano
  nunca dará una precisión validada. Lo que sí: un modo «validación» que trate las
  unidades 11/14/15 de la caché como gemelos —su verdad OOF es conocida— y calcule
  MAE y cobertura por ciclo. Da una frase honesta («validado en 3 motores OOF,
  cobertura X») sin inventar nada.

**Lo que no se arregla con código:** precisión real de flota. Eso son datos de campo.

### 3.3 El CSV se lee entero antes del tope

Es la deuda más barata y la que más se nota en una demo con un histórico real.
La única línea implicada es `pd.read_csv(upload)` (~1411).

- **Mínimo (20 min):** `pd.read_csv(upload, nrows=INF.MAX_FILAS + 1)`. Si hay más,
  rechazo inmediato. Peaje: el mensaje dice «más de 5 000 filas» en vez del total
  exacto.
- **Con total exacto (1 h):** lectura por `chunksize` contando sin retener; el pico
  de memoria es un trozo.

**Test:** CSV temporal de 5 001 filas y otro de 200 k; se exige el rechazo, el
mensaje y que no se construyan ventanas. Se puede medir el tiempo (<1 s).

### 3.4 Banda dual (artefacto vs R6) — decisión, no defecto

Hoy la banda y el estado salen de la lectura en uso (`banda_en_uso`, ~210) y la
orden lo declara. El mismo punto puede dar dos `L_inf` según el toggle.

| Salida | Coste | Qué compra |
| --- | --- | --- |
| Dejarlo declarado y cerrarlo por escrito | 0 | Nada nuevo; el tribunal sigue viendo dos números |
| Ocultar la banda que no decide, dejarla en auditoría | ~1 h | Menos ruido, misma física |
| Un número canónico en UI, órdenes y KPI + ADR | ~1 día | Una sola respuesta; toca tests de 4.90/4.86 y la ruta de decisión |

Recalibrar R6 sobre el punto crudo para «unificarlas» **no** es una opción: la banda
quedaría inválida para el punto corregido. Unificar es elegir cuál manda, no promediar.

---

## 4. Orden recomendado

1. **#3** primero: 20-60 min, riesgo nulo, se nota enseguida.
2. **#1a** (export/import) si la prioridad es «no perder el trabajo»; **#1c** (SQLite)
   si esto pasa a uso real. No hagas #1b si ya sabes que habrá dos usuarios.
3. **#2a + #2b**: convierte «da método y cobertura» en «da una cifra y un método».
4. **#4** al final y con ADR: el código es lo de menos, la decisión es tuya.

Ninguno toca `models/`, `app/cache/` ni el gate: la integridad de evidencias (0.9012)
no está en juego en ninguna de las cuatro.

---

## 5. Decisiones que necesito de ti

1. **Persistencia:** ¿demo (export/import basta) o uso real (SQLite)?
2. **Banda:** ¿qué número manda cuando la corrección está activa, y qué se hace con
   el otro: auditoría o fuera?
3. **Verdad:** ¿vas a reportar un punto por motor o varios? Cambia el modelo de datos.

---

## 6. Para retomar

```bash
# suite completa (139 tests, ~70 s)
./.venv/Scripts/python.exe -m pytest tests -q

# app
./.venv/Scripts/python.exe -m streamlit run app/dashboard_ds02.py

# gate de evidencias (no escribe si hay deriva)
./.venv/Scripts/python.exe scripts/freeze_rules_evidence.py
```
