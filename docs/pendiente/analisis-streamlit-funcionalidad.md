# Análisis funcional de Streamlit (DS02)

Fecha: 2026-11-03 · App: `app/dashboard_ds02.py` en http://localhost:8503 · Rama `clase-experimental`.

## Pruebas realizadas
- Navegación en browser (pestañas Flota, Motor, Casos nuevos, Auditoría).
- Botones de ejemplo (Sano U15 APTO, Medio U11 INSPECCIÓN, Crítico U14 HANGAR).
- Traza del motor de reglas (R7_APTO, R9_HANGAR), L_inf, estado, gemelos, orden de trabajo.
- Auditoría: métricas, SHA-256, descarga PDF.
- Tests: `test_live_eval`, `test_dss_ui`, `test_dss_interaction`, `test_engine_flow`, `test_rules_gate` → 108 passed, 3 skipped. Tests de clase → 22 passed.

## Funciona correctamente
- Carga de la app y caché (6.196 ventanas, 12.538 filas).
- Muro del hangar con sparklines y estado por L_inf.
- Motor de reglas con traza visible y coherente con `mia/motor.py`.
- Casos nuevos: puntuación y regla aplicada.
- Auditoría: Macro-RMSE 4.84, MAE zona crítica 1.16, SHA-256 del artefacto, descarga de PDF.
- Gemelos registrados, orden de trabajo, descargas CSV/JSON.

## Observaciones / posibles fallos (no bloquean)
1. Texto "PRUEBAHANGAR" aparece como nombre de unidad en el muro (dato de prueba colado).
2. Inconsistencia en el banner: "1 motor(es) de los registrados en esta sesión están derivados a hangar" vs muro "0 / 3 en hangar".
3. El tab Auditoría no muestra SHAP/importancia visual (existe `app/ui_shap.py` pero no integrado en este tab).
4. El tab Auditoría tarda ~15s en renderizar y en un caso quedó en blanco (LEN 0) tras el click, requiriendo recarga.
5. Warnings de `use_container_width` deprecado en consola (cosmético).

## Pendiente
- Limpiar "PRUEBAHANGAR" y alinear el contador del banner.
- Integrar SHAP en la auditoría si se quiere explicabilidad en la app.
- Optimizar tiempo de renderizado del tab Auditoría.
- Migrar `use_container_width` a `width`.
