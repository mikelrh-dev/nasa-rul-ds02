# Verify report: Flujo n8n mínimo MIA-3

**Change:** `2026-11-06-ds02-n8n-decision`
**Fecha:** 2026-11-06

## EJECUTADO

- `.venv/Scripts/python -m pytest tests/test_n8n_decision.py -q` (RED inicial): error de colección `ModuleNotFoundError: No module named 'ui_n8n'` — el test RED fallaba antes de implementar, como exige el TDD estricto.
- `.venv/Scripts/python -m pytest tests/test_n8n_decision.py tests/test_mia_rules.py tests/test_simulacion.py tests/test_ui_alta.py tests/test_ui_rules.py -q`: `53 passed, 2 skipped` (tras corregir el assert de tipos del flujo a minúsculas).
- `.venv/Scripts/python scripts/verify_gate.py --only tests/test_n8n_decision.py`: `GATE PASSED`.
- `.venv/Scripts/python scripts/verify_gate.py` (suite completa, ~3 min): primera pasada `3 failed, 324 passed, 6 skipped — GATE FAILED`. Los 3 fallos (`test_reemplazar_el_gemelo_desde_la_pestana_en_vivo`, `test_el_preset_demo_pinta_el_estado_que_promete`, `test_explorar_por_ciclo_evaluar_funciona`) eran regresión de este change: `KeyError: 'unit'` en `dashboard_ds02.py:1878` porque la ventana en vivo de `score_table` no trae columna `unit`. Se corrigió tomando la unidad del contrato (`unidad_simulada`), con test de regresión `test_payload_ventana_en_vivo_sin_columna_unit`; los 3 tests + `test_n8n_decision.py` pasaron (`16 passed`).
- `.venv/Scripts/python scripts/verify_gate.py` (segunda pasada, suite completa): `GATE PASSED`.
- Re-medición bundle C desde `app/cache/` (comando ejecutado, no de memoria): CASOS 9/9 BIEN (U11 c1 APTO 34.95, c21 INSPECCION 29.71, c26 HANGAR 24.72; U14 c3 APTO 33.07, c35 HANGAR 23.98, c60 HANGAR 13.70; U15 c20 APTO 32.53, c26 HANGAR 24.52; dato imposible SIN_DECISION); primer INSPECCION/HANGAR U11 6/23, U14 7/25, U15 9/24; PERFILES y modo historia coinciden con las expectativas bundle C ya presentes en los tests — **ningún cambio de expectativa fue necesario** y no se tocó código de la app para esto.
- `n8n/flujo.json`: `json.load` válido (vía test), webhook `ds02/decision` + Switch 3 ramas + acciones por rama, sin valores de credenciales.

## LEÍDO (no ejecutado)

- `openspec/config.yaml`, `AGENT.md`, convenciones `_shared/` y la skill `sdd-openspec-loop`: leídos antes de empezar.
- Layout de un change hermano (`2026-11-02-clase-track/specs/clase-track/spec.md`): copiado para el delta.
- Servidor n8n local (`:5678`) y sus credenciales: **no se accedió ni se exportó**; el flujo se escribió a mano en formato de exportación y las credenciales quedan solo en la instancia local, como documenta `design.md`.

## Veredicto

Gate ejecutado con resultado real: **GATE PASSED** en la suite completa tras corregir una regresión propia (unidad desde el contrato). Nada pendiente de este change salvo el archive, que sigue.
