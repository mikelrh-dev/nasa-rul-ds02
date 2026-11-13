# Handover 2026-11-13 — SDD cierre de hallazgos (app + n8n)

> Para el próximo agente/sesión: esto era lo que estaba en marcha y lo que queda.
> Todo lo SDD está en git; lo que NO está es el apply (cambios sin commitear).

## Dónde está el proyecto

- Repo: `C:\Users\mikel\Desktop\Pruebas\nasa` · rama `refactor/estructura-ds02-clase-2026-11-10` (con origin).
- App Streamlit: http://localhost:8501 (entrypoint `app/entrypoints/streamlit_app.py`).
- Flujo n8n vivo: localhost:5678, "DS02 Decision MIA-3", id `hLlkHl3X33roWPEQ`, webhook `http://localhost:5678/webhook/ds02/decision`.
- Bot Telegram: `NasaOperatorBot` (credencial n8n "DS02 Telegram", id `W5cSPgmsDNncBDBs`; token placeholder a sustituir). Chat id `1028762622`.

## Qué se estaba haciendo

Un loop SDD (propose→spec→design→tasks→apply→verify→archive) para cerrar los 6
hallazgos de la prueba exhaustiva (subagente `deleg_4da84161`):

- **H1**: el botón «Auditar hashes del artefacto» rompe la pestaña Auditoría (`TypeError`).
- **H2**: el nodo HANGAR Gmail usa umbrales por defecto 30/25 (los vigentes son 25/20).
- **H3**: un umbral inválido hace `st.stop()` y deja la app en blanco.
- **H4**: el evento de Calendar no declara `timeZone` (Europe/Madrid).
- **H5**: el insert de Postgres no mapea `idempotency_key`.
- **H6**: fallback SIN_DECISION, «Ver gemelo» no abre la ficha, test del panel sin dedupe.

## Estado del SDD (commits ya en git)

- `a15eaf9` sdd(propose)
- `af5f8c5` sdd(spec)
- `cf05dfe` sdd(design)
- `4020c90` sdd(tasks)
- Change: `openspec/changes/2026-11-13-cierre-hallazgos-app-n8n/` (proposal, specs, design, tasks).

El **apply** estaba en curso con un subagente (`deleg_9983ade1`). Sus cambios
quedan **sin commitear** en el working tree (`app/` y `n8n/flujo.json`).

## Siguientes pasos (cuando vuelvas)

1. Comprueba si el subagente terminó: `git status` y el transcript en
   `C:\Users\mikel\AppData\Local\hermes\cache\delegation\live\deleg_9983ade1\task-0.log`.
   Si no terminó, re-lanza el apply con el mismo encargo (tareas en `tasks.md`).
2. Verifica: `.venv/Scripts/python.exe -m pytest tests/test_dss_ui.py tests/test_n8n_decision.py tests/test_engine_flow.py -q`
   y luego `python scripts/verify_gate.py` (suite completa; hay **3 fallos
   preexistentes ajenos** de MLflow: `test_mlflow_backfill.py` y `test_mlflow_live.py`).
3. Aplica H2/H4/H5/H6a también al flujo **vivo** (n8n-mcp) si el subagente no lo
   hizo, y valida con `n8n_validate_workflow` (0 errores).
4. Commitea el apply y haz `git push`.
5. Verificación formal (`sdd-verify`): escribe `verify-report.md` en el change.
6. Archivo (`sdd-archive`): mueve el change a `openspec/changes/archive/2026-11-13-.../`
   y fusiona los deltas en `openspec/specs/ds02-dss-ui/spec.md` y
   `openspec/specs/ds02-n8n-decision/spec.md`.

## Pendientes / deuda conocida

- El flujo vivo tiene el texto Telegram enriquececido (HTML); alinea el repo si queda simple.
- La spec `ds02-n8n-decision` sigue describiendo 3 ramas; el delta la actualiza y el archive la fusiona.
- 3 fallos de test de MLflow preexistentes (`notebooks/00_datos.ipynb`), ajenos.
- El token de Telegram se pegó en el chat: revócalo en @BotFather y pon el nuevo en la credencial.
- La API :8000 está apagada (ningún flujo depende de ella).

## Claves

- Riesgo: H1/H2/H4/H6 bajo; H3 medio; H5 medio (BD).
- No toques `models/`, `notebooks/` ni `scripts/` sin permiso.
