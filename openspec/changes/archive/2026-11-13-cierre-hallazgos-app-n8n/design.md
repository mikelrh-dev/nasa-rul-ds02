# Design: Cierre de los 6 hallazgos de la prueba exhaustiva

## Technical Approach

Arreglos pequeños y localizados: dos guardas en la UI (hash del artefacto y
umbral inválido), un ajuste de las plantillas del flujo n8n (umbrales, zona,
idempotency_key, fallback) y dos retoques de UI (ficha del gemelo y huella del
test del panel). Sin cambios de arquitectura ni de datos; la BD viva no se
migra en este change.

## Architecture Decisions

### Decision: H1 lee el hash del manifiesto
**Choice**: tomar el esperado de `models/ds02_manifest.json`
(`artifacts.bilstm_sha256`) con fallback a `provenance`, y guardia para `None`.
**Alternatives considered**: regenerar `app/cache/` con el hash (lento, no
aporta); mostrar «no registrado» sin comparar (pierde la comprobación).
**Rationale**: el manifiesto ya trae el hash correcto (`bf9620a7…`); el fix es
local y verificable.

### Decision: H3 no usa `st.stop()`
**Choice**: `st.error` + restaurar el preset en `session_state` y continuar;
`max_value=threshold_apto - 1` en el input de hangar.
**Alternatives considered**: dejar `st.stop()` (app irrecuperable); recargar
la página (mala UX).
**Rationale**: la app debe seguir operable; el preset ya tiene los valores.

### Decision: H2/H4/H5/H6a se arreglan en el JSON del flujo
**Choice**: editar `n8n/flujo.json` (y el vivo vía n8n-mcp).
**Alternatives considered**: tocar la app (los umbrales ya viajan en el payload;
el problema es el fallback del nodo).
**Rationale**: el flujo es la fuente; la app ya envía los umbrales correctos.

### Decision: H5 solo mapea, no UNIQUE/upsert
**Choice**: mapear `idempotency_key`; no añadir UNIQUE en la BD viva.
**Alternatives considered**: UNIQUE + upsert (requiere migración y validación
con la BD).
**Rationale**: fuera de alcance; el mapeo ya evita perder la clave.

### Decision: H6b fija la selección del gemelo
**Choice**: en el handler, fijar `st.session_state["gemelo_detalle_sel"]`.
**Alternatives considered**: cambiar de pestaña programáticamente (Streamlit no
lo permite con `st.tabs`).
**Rationale**: la ficha ya existe; solo hay que seleccionarla.

## Data Flow

    app ──payload(umbrales, fingerprint, idempotency_key)──▶ n8n ──▶ Telegram
                                                              ├─▶ Gmail
                                                              ├─▶ Calendar
                                                              └─▶ Postgres

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/ui/_tab_auditoria.py` | Modify | guardia `None` + hash del manifiesto |
| `app/entrypoints/dashboard_ds02.py` | Modify | quitar `st.stop()` y restaurar preset |
| `app/ui/_tab_flota.py` | Modify | `max_value` + `gemelo_detalle_sel` |
| `app/lib/dashboard_helpers.py` | Modify | huella única por prueba |
| `n8n/flujo.json` | Modify | Gmail 25/20, Calendar timeZone, Postgres idempotency_key, fallback SIN_DECISION |
| `tests/test_dss_ui.py` | Modify | regresiones H1/H3 |
| `tests/test_n8n_decision.py` | Modify | regresiones H2/H4/H5/H6a |
| `tests/test_engine_flow.py` | Modify | regresión del gemelo |

## Interfaces / Contracts

- Hash esperado del `.keras`: `models/ds02_manifest.json` → `artifacts.bilstm_sha256`.
- Umbral por defecto del nodo Gmail: 25/20 (`app/lib/_constantes.py`).
- `idempotency_key`: ya viaja en el payload; el nodo Postgres lo mapea.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | H1, H3 | AppTest (`tests/test_dss_ui.py`) |
| Integration | H2, H4, H5, H6a | `tests/test_n8n_decision.py` (estructural sobre el JSON) |
| E2E | app + flujo | suite completa (`scripts/verify_gate.py`) |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file
classification, or process-integration boundary.

## Migration / Rollout

No migration required. El flujo n8n se arregla en el repo y en el vivo (vía
n8n-mcp).

## Open Questions

- [ ] ¿Requiere `idempotency_key` una restricción UNIQUE en la BD viva? (fuera de alcance)
- [ ] ¿El Gmail 500 requiere reintentos? (no reproducible desde repo; se documenta)
