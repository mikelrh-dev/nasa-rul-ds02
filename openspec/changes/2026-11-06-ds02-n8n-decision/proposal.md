# Proposal: Flujo n8n mínimo MIA-3 (decisión por webhook)

**Change:** `2026-11-06-ds02-n8n-decision`
**Status:** Proposed
**Capability:** `ds02-n8n-decision` (new) — no modifica `rul-prediction-ds02`, `ds02-dss-ui`, `ds02-live-evaluation`
**Fecha:** 2026-11-06

---

## Why

El change `2026-11-02-clase-track` dejó `src/n8n.py` como stub que lanza `NotImplementedError` y `n8n/flujo.json` como placeholder, con el flujo real diferido a «el change siguiente». Este change es ese siguiente: la app ya decide en vivo (`decision_en_vivo` en `app/ui_rules.py`), pero ninguna decisión sale de la app. MIA-3 exige que la decisión dispare una acción distinta según su valor. Sin este change, la trazabilidad de la decisión termina en la pantalla.

## Scope

**In scope**

1. **App primero — corregir la deriva bundle B → bundle C en los tests.** Re-medir `CASOS` (`src/mia/casos.py:33-43`), `PERFILES` (`app/ui_alta.py`) y los ciclos de hangar desde `app/cache/` con comandos ejecutados, y corregir las expectativas de `tests/test_mia_rules.py` (`test_todos_los_casos_salen_BIEN`, `test_hay_casos_para_cada_estado`), `tests/test_simulacion.py` (`test_ciclos_hasta_fallo_coincide_con_la_cache`) y `tests/test_ui_alta.py` (`test_perfiles_caen_en_su_banda`, `test_el_modo_historia_se_deriva_de_la_cache`, `test_el_paso_critico_cae_en_hangar_y_el_primero_no`). Solo se tocan tests y, si la medición lo exige, los datos de casos/perfiles; no se toca código de la app para esto. Cada cambio de expectativa se documenta con el valor medido.
2. **Payload n8n.** Función nueva que, reutilizando la traza de `decision_en_vivo` (sin re-clasificar con `L.classify`), devuelve exactamente: `decision`, `unidad`, `ciclo`, `rul_punto`, `limite_inferior`, `limite_superior`, `umbrales {apto:30.0, hangar:25.0}`, `usadas`, `porque`, `motivo`, `alertas_datos`, más `artefacto_sha256` y `fingerprint` (que actúa como `idempotency_key`). Se excluye `X_raw` (numpy, no JSON).
3. **`src/n8n.py` real.** `enviar_decision` valida `decision ∈ {APTO,INSPECCION,HANGAR,SIN_DECISION}`, toma `webhook_url` del parámetro o del env `N8N_WEBHOOK_URL`, hace POST con `urllib` stdlib (requests no está en `requirements.txt`: no se usa ni se añade), timeout 5 s, devuelve `{ok,status,decision}`; los errores se loguean sin lanzar excepción a la UI.
4. **Punto de llamada único.** Tras `decision_en_vivo` en la pestaña Casos de `app/dashboard_ds02.py`, solo si `decision != SIN_DECISION`, deduplicado por fingerprint en `st.session_state`. Notifican HANGAR e INSPECCION; APTO solo deja log local sin POST. No se toca `score_table`, `decidir_ventanas` ni `live_work_order`.
5. **`n8n/flujo.json` real.** Sustituye el placeholder por un workflow importable: webhook POST `ds02/decision`, Switch con 3 ramas APTO / INSPECCION / HANGAR; HANGAR → Postgres insert + Google Calendar + Gmail; INSPECCION → Google Sheets append; APTO → Set log. Si no se puede exportar del n8n local, se escribe el JSON en formato de exportación de n8n a mano y se verifica que es JSON válido. Las credenciales viven en la instancia local de n8n; el repo solo guarda el flujo. No se inventan valores de credenciales.

**Out of scope**

- Watcher autónomo (polling / servicio en segundo plano que vigile la flota sin intervención de la app).
- Telegram (ni bot, ni canal, ni notificación por Telegram).
- Endpoint `/decide` en la API (`app/api.py`): rechazado porque `/predict` no aplica reglas y duplicaría la decisión fuera del motor.
- Reentrenar modelos, re-ejecutar notebooks, tocar `MLProyectVault`, `docs/`, `notebooks/` o los pptx.

## Capability

Nueva capacidad `ds02-n8n-decision` (flujo n8n mínimo MIA-3). No añade ni modifica las capacidades desplegadas: cita `ds02-rules-engine` (traza), `ds02-live-evaluation` (evaluación en vivo) y `ds02-dss-ui` (pestaña Casos).

## Artifacts that stay byte-compatible

- `models/*`, `app/cache/*`, `src/ds02_rul/*`, `src/mia/reglas.py`, `src/mia/motor.py`, `02_DS02_ensemble_RUL.ipynb`, `archive/*` — sin cambios: no se reentrena, no se recalibra la banda, no se re-ejecutan notebooks.
- La función de payload reutiliza la traza de `decision_en_vivo`; no reclasifica.

## Rollback plan

Un commit por fase (propose → spec → design → tasks → apply → verify → archive), o un commit final si no es viable separar. Revertir `apply` borra la función de payload, el POST real de `src/n8n.py`, el punto de llamada en la pestaña Casos y restaura el placeholder de `n8n/flujo.json`, sin tocar `models/` ni `app/cache/`. La corrección de tests bundle C (fase apply) es independiente: si se revierte el resto, las expectativas medidas desde la caché se mantienen.

## Risks

1. **Doble envío por rerun de Streamlit.** Mitigación: dedupe por fingerprint en `st.session_state` (cada rerun sin cambio de fingerprint no re-envía).
2. **POST bloquea o rompe la UI.** Mitigación: timeout 5 s, errores logueados sin excepción a la UI, `{ok,status,decision}` siempre devuelto.
3. **Re-clasificar en el payload y divergir del motor.** Mitigación: el payload lee la traza de `decision_en_vivo`; prohibido `L.classify` en el camino.
4. **Sombreado de módulos genéricos.** Mitigación: no crear `app/motor.py` ni nombres genéricos que sombreen `mia/motor.py`; la función nueva vive con nombre específico (p. ej. `ui_n8n`).
5. **Credenciales inventadas en `flujo.json`.** Mitigación: el JSON referencia credenciales por nombre/ID de la instancia local, nunca valores; documentado en `design.md`.
