# Proposal: Cerrar los 6 hallazgos de la prueba exhaustiva (app + n8n)

**Change:** `2026-11-13-cierre-hallazgos-app-n8n`
**Branch:** `refactor/estructura-ds02-clase-2026-11-10`
**Date:** 2026-11-13
**Capabilities:** `ds02-dss-ui` (MODIFIED) · `ds02-n8n-decision` (MODIFIED)

## Intent

Cerrar los seis hallazgos de la prueba exhaustiva (subagente `deleg_4da84161`) antes
de la defensa del tribunal:

- **H1** (alta): el botón «Auditar hashes del artefacto» rompe la pestaña Auditoría
  con `TypeError: NoneType object is not subscriptable`.
- **H2** (media): el nodo HANGAR Gmail usa umbrales por defecto 30/25; los vigentes
  son 25/20.
- **H3** (media): un umbral inválido hace `st.stop()` y deja la app en blanco, sin
  forma de corregirlo.
- **H4** (media): el evento de Google Calendar no declara `timeZone` (queda
  America/New_York).
- **H5** (media): el insert de Postgres no mapea `idempotency_key` (duplicados).
- **H6** (bajas): el fallback trata SIN_DECISION como no reconocida; «Ver gemelo» no
  abre la ficha; el test del panel usa huella fija sin dedupe.

## Scope

### In Scope
- H1, H2, H3, H4, H5 (mapeo de `idempotency_key`), H6a, H6b y H6c, cada uno con su
  test de regresión.

### Out of Scope
- UNIQUE/upsert sobre `idempotency_key` en la tabla viva (requiere migración y
  validación con la BD).
- Reintentos/onError del Gmail (fallo HTTP 500 histórico no reproducible desde repo).
- Los tres fallos de test de MLflow preexistentes (ajenos a este cambio).

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `ds02-dss-ui`: H1, H3, H6b, H6c.
- `ds02-n8n-decision`: H2, H4, H5 (mapeo), H6a.

## Approach

- **H1**: tomar el hash esperado de `models/ds02_manifest.json`
  (`artifacts.bilstm_sha256`) con fallback y guardia explícita para `None`.
- **H3**: sustituir `st.stop()` por `st.error` + restauración del preset en
  `session_state` y `max_value` en el input de hangar.
- **H2/H4/H6a**: ajustar el JSON del flujo (fallbacks 25/20, `timeZone`
  `Europe/Madrid`, ternario que distingue SIN_DECISION).
- **H5**: mapear `idempotency_key` en el nodo Postgres.
- **H6b/H6c**: fijar `gemelo_detalle_sel` al pulsar «Ver gemelo»; huella única por
  clic en el test del panel.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/ui/_tab_auditoria.py` | Modified | guardia `None` + hash del manifiesto |
| `app/entrypoints/dashboard_ds02.py` | Modified | quitar `st.stop()` y restaurar el preset |
| `app/ui/_tab_flota.py` | Modified | `max_value` + `gemelo_detalle_sel` |
| `app/lib/dashboard_helpers.py` | Modified | huella única por prueba |
| `n8n/flujo.json` | Modified | Gmail, Calendar, Postgres, fallback |
| `tests/` | Modified | regresiones de cada hallazgo |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| H3 cambia el comportamiento del preset | Med | Tests AppTest existentes + regresión |
| H5 sin UNIQUE real deja duplicados | Med | Mapeo sí; UNIQUE/upsert fuera de alcance |
| Tocar `n8n/flujo.json` a mano | Low | Validar JSON y suite |

## Rollback Plan
Revertir el commit del change; cada fase commitea por separado.

## Dependencies
- Streamlit corriendo en `localhost:8501` para la verificación de UI.

## Success Criteria
- [ ] Los seis hallazgos quedan arreglados y con test de regresión.
- [ ] `python scripts/verify_gate.py` en verde.
- [ ] La app ya no se queda en blanco con un umbral inválido.
