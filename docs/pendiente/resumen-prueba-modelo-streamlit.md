# Resumen: cómo se prueba el modelo en Streamlit (Casos nuevos)

**Carpeta:** `docs/pendiente/`
**Fecha:** 2026-10-31
**Estado:** referencia para defensa; sin cambios de código.

## Dónde se predice de verdad

- Pestaña **"Casos nuevos"**: inferencia en vivo (`score_table` → `predict_interval`, bundle cacheado con `st.cache_resource`). Carga del bundle ~8 s la primera vez.
- Pestaña **"Flota"**: solo lee caché Parquet (`ds02_windows.parquet`); NO carga modelo. Render puro.

## Qué necesita el modelo para puntuar

- Ventana fija de **50 filas × 18 canales** (4 ops + 14 sensores), definida por el artefacto (`models/ds02_manifest.json`, `window_size=50`). No cambiable sin reentrenar.
- Las 50 filas deben ser **consecutivas en el tiempo** del mismo motor (el modelo ve la trayectoria reciente).

## Qué le inyectamos en la prueba

- `DEMO_ROWS = 300` filas de telemetría downsampleada (stride 100) → 251 ventanas (300 − 50 + 1).
- La decisión final es la **última ventana**; por eso 300 y 50 dan el mismo veredicto. 300 aporta historia + EMA suavizada (más estable visualmente).
- Límites: 50 filas = 1 predicción mínima; >1500 → aviso en editor; >5000 → error duro (`MAX_FILAS=5000`, `UMBRAL_RECORTE_EDITOR=1500`).
- Prueba manual realizada: 60 filas → 11 ventanas, pred ≈58.4, L_inf≈34.5, L_sup≈78.8.

## Presets canónicos (no tocar)

| Preset | Posición | Estado esperado |
|--------|----------|-----------------|
| Sano | 0.05 | APTO |
| Medio | 0.36 | INSPECCIÓN |
| Crítico | 0.55 / ciclo crítico | HANGAR |

Tests que los fijan: `tests/test_live_eval.py` (42/42 pasan).

## Flujo de demo recomendado

1. 300 filas por defecto.
2. Presets en orden: Sano → Medio → Crítico.
3. Descargar work order en el tercero.
4. ~2-3 s por evaluación (bundle cacheado tras la primera carga).

## Propuesta interactiva pendiente

"Editar tabla CSV no es interactivo" → bloque **"Explorar por ciclo"**: selectbox motor (11/14/15) + slider de posición/ciclo + preview de estado calculado + botón "Evaluar este tramo". No promete estado fijo (se calcula dinámicamente), no toca presets ni tests. Plan detallado en `docs/pendiente/plan-explorar-por-ciclo-slider.md`.

## Referencias

- `app/ui_inference.py`: `score_table`, `validate_table`, `raw_windows`, `get_ensemble`, `example_window`, `window_ending_at`, `DEMO_ROWS`, `MAX_FILAS`.
- `app/ui_data_loader.py`: `get_rows`, `fleet_snapshot`, `classify`, `work_order`, `live_work_order`.
- `app/dashboard_ds02.py`: sección "Puntúa un ejemplo en 1 clic" (~2800-2960).
- Tests: `tests/test_live_eval.py` (42), `tests/test_dss_ui.py` (31), `tests/test_engine_flow.py`.
", "path">
docs/pendiente/resumen-prueba-modelo-streamlit.md