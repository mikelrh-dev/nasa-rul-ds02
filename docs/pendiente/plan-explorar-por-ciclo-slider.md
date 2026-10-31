# Sugerencia pendiente: bloque "Explorar por ciclo" (slider interactivo)

**Carpeta:** `docs/pendiente/`
**Fecha:** 2026-10-31
**Estado:** propuesta no implementada. Sugerencia para futura implementación.
**Prioridad sugerida:** media (mejora de UX/interactividad, bajo riesgo).

## Motivación

Las rutas actuales de "Casos nuevos" no son interactivas sin preparar datos:
- "Puntúa un ejemplo en 1 clic": 3 presets fijos (Sano/Medio/Crítico) con posiciones hardcodeadas.
- "Editar tabla"/"Subir CSV": requiere preparar un CSV o pegar datos.

Se propone añadir un bloque "Explorar por ciclo" que permita mover un slider y ver en vivo cómo cambia el estado (APTO/INSPECCIÓN/HANGAR) de un motor, sin preparar CSV ni romper la demo de 3 clics.

## Objetivo

Permitir al usuario seleccionar un motor (11/14/15) y un momento de su vida (posición 0.0-1.0 o ciclo final) mediante un slider, regenerar la tabla de 50+ filas, mostrar un preview del estado calculado dinámicamente, y puntuar ese tramo con un botón "Evaluar".

## Diseño propuesto

### Ubicación
- Pestaña "Casos nuevos", como bloque separado después de "Puntúa un ejemplo en 1 clic" y antes de "Puntúa un motor con datos que aportes tú", o dentro de "Ejemplo del test set" como modo adicional.

### Componentes UI
1. `st.selectbox` "Motor" con opciones 11/14/15 (con etiqueta legible).
2. `st.slider` "Momento del vuelo" (0.0 a 1.0, step 0.01) O selector de ciclo final (`st.number_input` o slider sobre ciclos disponibles del motor).
3. Al mover el slider (rerun), llamar a `INF.example_window(unit, position)` o `INF.window_ending_at(unit, cycle, rows=INF.DEMO_ROWS)` y mostrar:
   - Tabla de datos (read-only preview) o resumen (ciclos cubiertos, filas).
   - Estado calculado en vivo (APTO/INSPECCIÓN/HANGAR) a partir de `L.fleet_snapshot` o de la banda de la ventana, sin puntuar.
   - Aviso si el tramo cae fuera de dominio (plausibilidad).
4. Botón "Evaluar este tramo" (activa `score_table` sobre la tabla generada) → resultado + work order si hay bloqueo.

### Reglas de diseño
- El bloque NO promete un estado fijo (a diferencia de los 3 presets). El estado se calcula dinámicamente y se muestra como resultado, no como etiqueta.
- Los 3 presets canónicos ("Sano/Medio/Crítico") y sus tests (`test_live_eval.py`) NO se tocan.
- El slider usa `rows=INF.DEMO_ROWS` (300) por defecto para tener curva; opcionalmente un selector de "largo del tramo" (50/300) para comparar ventana sola vs trayectoria.

## Implementación (pasos)

1. Añadir función helper en `app/ui_inference.py` (opcional): `preview_state(table)` que devuelve el estado sin puntuar (reutilizando `L.fleet_snapshot` o cálculo de banda sobre la última ventana). O calcular en el dashboard con `L.classify`.
2. En `app/dashboard_ds02.py`, sección "Casos nuevos", añadir bloque:
   - Selectbox motor + slider posición/ciclo.
   - Generar tabla con `INF.example_window` / `INF.window_ending_at`.
   - Mostrar preview (ciclos, filas, estado estimado).
   - Botón "Evaluar este tramo" → `INF.score_table` → resultado.
3. Añadir `alt=` a cualquier chart nuevo (cumplir `test_every_chart_and_grid_has_an_accessible_name`).
4. No añadir CSS/JS (cumplir `test_no_css_is_injected_into_the_app`).

## Tests propuestos (nuevos, no modificar existentes)

- `test_explorar_por_ciclo_genera_tabla_valida`: slider a posición 0.5 → tabla con ≥50 filas, columnas correctas.
- `test_explorar_por_ciclo_estado_preview`: posición 0.05 → estado APTO; posición 0.9 → estado HANGAR (o el que corresponda).
- `test_explorar_por_ciclo_evaluar_funciona`: botón evaluar → `live_result` no None, ventanas > 0.
- `test_explorar_por_ciclo_no_rompe_presets`: los 3 presets siguen dando sus estados fijados.

## Riesgos

- Bajo-medio. El principal riesgo es que el usuario mueva el slider y el estado no coincida con una etiqueta prometida → por eso el bloque NO promete estado, solo lo calcula.
- Rendimiento: mover el slider dispara rerun completo; `example_window` lee parquet (~rápido). Evitar llamar a `score_table` en cada movimiento (solo en botón "Evaluar").
- AppTest: el slider debe tener `key` estable y los tests deben usar `set_value`.

## Referencias

- `app/ui_inference.py`: `example_window`, `window_ending_at`, `score_table`, `DEMO_ROWS`, `demo_presets`, `channel_order`, `window_size`.
- `app/ui_data_loader.py`: `get_rows`, `fleet_snapshot`, `classify`, `first_alarm_cycle`, `unit_curve`.
- `app/dashboard_ds02.py`: líneas 2800-2960 (sección "Puntúa un ejemplo en 1 clic" y "Puntúa un motor con datos que aportes tú").
- Tests: `tests/test_live_eval.py` (42 tests existentes, no modificar).

## Decisión pendiente

¿Implementar este bloque como mejora de UX? Si sí, prioridad media (después de los "APROBADOS" del estudio WOW). Si no, dejar como sugerencia archivada.
", "path">
docs/pendiente/plan-explorar-por-ciclo-slider.md