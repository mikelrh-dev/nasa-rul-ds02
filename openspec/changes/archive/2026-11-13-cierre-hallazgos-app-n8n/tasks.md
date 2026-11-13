# Tasks: Cierre de los 6 hallazgos de la prueba exhaustiva

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~180 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | single change |
| Delivery strategy | auto-chain |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Phase 1 — H1: Auditoría no rompe

- [x] 1.1 RED: `tests/test_dss_ui.py` — AppTest que pulsa `btn_audit_hashes` con `provenance` sin `bilstm_sha256` y espera sin excepción.
- [x] 1.2 GREEN: `app/ui/_tab_auditoria.py` — hash desde `models/ds02_manifest.json` (`artifacts.bilstm_sha256`) con fallback y guardia `None` antes de `[:12]`.
- [x] 1.3 Verificar `tests/test_dss_ui.py`.

## Phase 2 — H3: umbral inválido recupera la app

- [x] 2.1 RED: `tests/test_dss_ui.py` — AppTest con umbrales invertidos que espera sidebar y pestañas.
- [x] 2.2 GREEN: `app/entrypoints/dashboard_ds02.py` — quitar `st.stop()`, `st.error` + restaurar el preset en `session_state`.
- [x] 2.3 GREEN: `app/ui/_tab_flota.py` — `max_value=threshold_apto - 1` en el input de hangar.
- [x] 2.4 Verificar `tests/test_dss_ui.py` y `tests/test_app_fixes*.py`.

## Phase 3 — n8n: H2, H4, H5, H6a

- [x] 3.1 RED: `tests/test_n8n_decision.py` — aserciones de umbrales 25/20 en Gmail, `timeZone` en Calendar, `idempotency_key` en Postgres y SIN_DECISION distinguido en el fallback.
- [x] 3.2 GREEN: `n8n/flujo.json` — Gmail fallbacks 25/20; Calendar `timeZone` Europe/Madrid; Postgres mapea `idempotency_key`; FALLBACK con ternario que distingue SIN_DECISION.
- [x] 3.3 Aplicar el mismo JSON al flujo vivo (n8n-mcp) y validar (0 errores).
- [x] 3.4 Verificar `tests/test_n8n_decision.py`.

## Phase 4 — UI: H6b y H6c

- [x] 4.1 RED: `tests/test_engine_flow.py` — pulsar «Ver gemelo» selecciona la ficha del gemelo registrado.
- [x] 4.2 GREEN: `app/ui/_tab_flota.py` — fijar `gemelo_detalle_sel`; `app/lib/dashboard_helpers.py` — huella única por prueba.
- [x] 4.3 Verificar `tests/test_engine_flow.py` y `tests/test_dss_ui.py`.

## Phase 5 — Verificación

- [x] 5.1 `python scripts/verify_gate.py` (suite completa): ejecutado; `GATE FAILED (exit 1)` por 3 fallos preexistentes de MLflow/notebooks ajenos a este change (ver `verify-report.md`); el scope del change va en verde (81/81).
- [x] 5.2 Verificar la app (Streamlit) y el flujo vivo (n8n-mcp) una vez aplicado: app renderizada bajo `AppTest` (incluido el umbral inválido) y flujo vivo `hLlkHl3X33roWPEQ` con `valid: true`, `errorCount: 0` y los 4 arreglos presentes.
