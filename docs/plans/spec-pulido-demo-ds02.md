# Spec: Pulido demo en vivo DSS DS02 (C1+C2+C3)

## Objective
Pulir solo la capa presentacional de `app/dashboard_ds02.py` para que un tribunal ajeno entienda en <10s el valor del DSS DS02 y el presentador pueda incorporar una unidad nueva en directo sin salir del flujo. Usuarios: presentador demo y tribunal evaluador. Éxito: C1+C2+C3 verificados con `pytest tests -q` verde y los 8 guards de `tests/test_dss_ui.py` verdes. C4 queda excluido por defecto por riesgo de credibilidad.

Assumptions:
1. Caché congelada válida: 6196 ventanas / 12538 filas / 3 unidades (manifest `app/cache/cache_manifest.json`).
2. Stack Streamlit 1.66.0, Plotly 7.1.0, pandas, PyArrow, sin TF en render.
3. Umbrales default 30/25 (ADR-008), decisión por `lower` (ventana más restrictiva por ciclo).
4. U14 primer ciclo puntuado = 3, HANGAR desde ciclo 29. U15 empieza en ciclo 2. U11 ciclo 1 L_inf 35.41.
5. Solo presentacional: no se toca inferencia ni artefactos.

## Tech Stack
Streamlit 1.66.0 · Plotly 7.1.0 · pandas · PyArrow · pytest + AppTest. Sin nuevas dependencias.

## Commands
```bash
# Fase 0 recalibrado (solo lectura)
./.venv/Scripts/python.exe -c "import pandas as pd; w=pd.read_parquet('app/cache/ds02_windows.parquet'); print(len(w))"
cat app/cache/cache_manifest.json
sed -n '186,206p' mia/reglas.py
# Tests
pytest tests/test_dss_ui.py -v
pytest tests/test_ui_alta.py -v
pytest tests -q
# Arranque
./.venv/Scripts/python.exe -m streamlit run app/dashboard_ds02.py --server.headless true
```

## Project Structure
```
app/dashboard_ds02.py     -> sidebar (184-241), header (368-399), tabs, KPIs flota (404-431)
app/ui_alta.py            -> NUEVO, puro sin Streamlit: ventanas_de_alta(perfil), estado_demo()
app/ui_data_loader.py     -> classify(), get_windows(), UNIT_LABELS (solo leer salvo C4)
app/twin.py               -> normalizar_id(), make_twin() (reutilizar validación MIN_ID=3)
app/hangar.py             -> abrir/revision (clampa, no extrapola)
app/cache/                -> SOLO LECTURA (windows/rows parquet + manifest)
tests/test_dss_ui.py      -> 8 guards (G1-G5, R6)
tests/test_ui_alta.py     -> NUEVO (contrato C1+C2)
.streamlit/config.toml    -> tema base #0b1220, superficie #141d2e (no CSS)
docs/plans/spec-pulido-demo-ds02.md -> esta spec (viva)
```

## Code Style
- `app/ui_alta.py` puro: sin `import streamlit`, funciones puras testeables sin levantar app (misma convención que `twin.py`/`hangar.py`).
- Naming negocio, no ingenieril en UI visible: "Incorporar unidad", "Perfil de desgaste", "Modo demo".
- Ejemplo:
```python
# app/ui_alta.py
def ventanas_de_alta(perfil: str, windows: pd.DataFrame) -> tuple[int,int,float]:
    """Mapeo puro perfil -> (unit, cycle, L_inf). Lanza ValueError si ciclo inexistente."""
    PRESETS = {"nuevo": (11,1), "medio": (11,20), "critico": (14,29), "atipico": (14,3)}
    ...
def estado_demo() -> dict:
    return {"threshold_apto": 30.0, "threshold_aog": 25.0, "cycle": 29, "unit": 14}
```
- Prohibido: `unsafe_allow_html`, `<style`, hardcodear métricas, reimplementar inferencia, offsets sensores.

## Testing Strategy
Framework pytest. Ubicación `tests/test_ui_alta.py` (nuevo) + `tests/test_dss_ui.py` (AppTest existente).
- Unit pequeño: cada preset C1 cae en banda declarada (APTO>=30, INSPECCION>=25, HANGAR<25); `estado_demo()` devuelve 30/25/29/14; `ValueError` para U14 ciclo 1-2 y U15 ciclo 1.
- Integración media: AppTest pulsa "Incorporar" y verifica fila en flota; pulsa "Modo demo" y verifica widgets + KPI hangar=1; panel C3 paridad con pestaña 1.
- Guards existentes deben seguir verdes (ver Boundaries). Cobertura: no baja.

## Boundaries
- Always: TDD RED->GREEN->REFACTOR; recalcular métricas de caché; `alt` no vacío en gráfico/tabla nueva; correr `pytest tests -q` por slice; un slice = un cambio, commiteable.
- Ask first: tocar `UNIT_LABELS` (C4); tocar `twin.py`/`registros_flota.json` para persistencia etiqueta; añadir dependencia.
- Never: escribir en `models/`, `src/ds02_rul/`, `mia/`, `notebooks/*.ipynb`, `02_*.ipynb`; modificar `ui_inference.py`, `cache/`; inyectar offset sensores; inventar reglas R3-R5, umbrales ROJO<=15, RMSE/R2/NASA no-manifiesto, euros, modelos avión por motor; CSS crudo; cambiar agregación ventana-más-restrictiva o reloj único flota.

## Success Criteria
- [ ] C1: formulario sidebar con matrícula>=3 chars + selector presets + botón; alta redirige a flota; `test_ui_alta.py` verde.
- [ ] C2: botón demo deja 30/25/ciclo29/U14/flota vaciada; KPI hangar=1; test verde.
- [ ] C3: header con 3 métricas (3 unidades/6196 ventanas, MAE crítica 1.13, hangar N) + frase límite-inferior; paridad con pestaña 1; `pytest -q` verde.
- [ ] 8 guards verdes: 292 no-CSS, 260 alt, 216 artefactos intactos, 51 APTO alcanzable, 203 no-FD001, 209 no-reimplementa-modelo, 114 métricas recalculadas, 299 slider->KPI.
- [ ] App arranca headless sin excepción.

## Open Questions
1. ¿Audiencia tribunal académico/mixto/MRO? (condiciona si reabrir C4 alias `Motor DS02-11`).
2. ¿Etiqueta C1 debe sobrevivir a recarga (tocar `twin.py`) o basta `session_state`? Default: session_state.
3. ¿Demo en portátil presentador o equipo tribunal? (caché 2MB suficiente).
