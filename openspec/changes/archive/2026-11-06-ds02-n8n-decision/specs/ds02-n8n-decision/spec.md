# Spec delta: Flujo n8n mínimo MIA-3 — `ds02-n8n-decision` (nueva capacidad)

**Change:** `2026-11-06-ds02-n8n-decision`
**Status:** Proposed
**Capability:** `ds02-n8n-decision` (new; no modifica `rul-prediction-ds02`, `ds02-dss-ui`, `ds02-live-evaluation`, `ds02-rules-engine`)

Mediciones de referencia (ejecutadas el 2026-11-06 desde `app/cache/`, bundle C):
CASOS `probar_casos` → 9/9 BIEN (U11 c1 APTO L_inf 34.95, U11 c21 INSPECCION 29.71,
U11 c26 HANGAR 24.72, U14 c3 APTO 33.07, U14 c35 HANGAR 23.98, U14 c60 HANGAR 13.70,
U15 c20 APTO 32.53, U15 c26 HANGAR 24.52, dato imposible SIN_DECISION);
primer INSPECCION/HANGAR por unidad: U11 6/23, U14 7/25, U15 9/24;
PERFILES y modo historia coinciden con las expectativas bundle C ya presentes en los tests.

---

## ADDED

### Requirement: Payload de decisión construido desde la traza en vivo

La capacidad SHALL exponer una función pura (p. ej. `payload_desde_traza`) que, dada la traza de `decision_en_vivo` (`app/ui_rules.py`), los umbrales en vigor y la procedencia del contrato (`artefacto_sha256`, `fingerprint`), devuelva EXACTAMENTE las claves: `decision`, `unidad`, `ciclo`, `rul_punto`, `limite_inferior`, `limite_superior`, `umbrales`, `usadas`, `porque`, `motivo`, `alertas_datos`, `artefacto_sha256`, `fingerprint` e `idempotency_key` (igual a `fingerprint`). La función MUST NOT re-clasificar (prohibido `L.classify` y prohibido re-ejecutar reglas de decisión): `decision`, `usadas` y `porque` SHALL leerse de la traza; `motivo` SHALL ser `" · ".join(porque)`, igual que `motivo_decision` en `decidir_ventanas`. Los umbrales SHALL ser `{"apto": 30.0, "hangar": 25.0}` por defecto. El payload MUST NOT incluir `X_raw` (numpy, no JSON-serializable). Todos los valores SHALL ser JSON-serializables (float/int/str/list/dict nativos, nunca numpy).

#### Scenario: Payload exacto desde una traza HANGAR
- GIVEN una traza de `decision_en_vivo` con `decision=HANGAR`, ventana con `unit=14`, `cycle=25`, `pred=33.1`, `lower=23.9`, `upper=44.2`, `usadas=["R9_HANGAR"]`, `alertas=[]`, umbrales 30.0/25.0, `artefacto_sha256="abc"` y `fingerprint="fp1"`
- WHEN se construye el payload
- THEN el payload tiene exactamente las 14 claves listadas, sin `X_raw`
- AND `decision="HANGAR"`, `unidad=14`, `ciclo=25`, `rul_punto=33.1`, `limite_inferior=23.9`, `limite_superior=44.2`, `umbrales={"apto":30.0,"hangar":25.0}`, `motivo` contiene `"R9_HANGAR"`
- AND `idempotency_key="fp1"` y `json.dumps(payload)` no lanza

#### Scenario: La función no reclasifica
- GIVEN una traza con `decision=INSPECCION` y un límite inferior que, con otros umbrales, sería APTO
- WHEN se construye el payload con los umbrales en vigor
- THEN `decision` sigue siendo `INSPECCION` (el de la traza), nunca el recalculado

### Requirement: Envío por webhook con stdlib y errores sin excepción

`src/n8n.py` SHALL implementar `enviar_decision(decision, payload, webhook_url=None)` que: valida `decision ∈ {APTO,INSPECCION,HANGAR,SIN_DECISION}` (valor inválido → `{"ok": False, "status": None, "decision": decision}` sin POST); resuelve la URL del parámetro o del env `N8N_WEBHOOK_URL` (ausente → `ok=False` sin POST ni excepción); hace POST con `urllib.request` stdlib y timeout 5 s, cuerpo JSON del payload y cabecera `Content-Type: application/json`; devuelve `{"ok": bool, "status": int|None, "decision": decision}` (`ok=True` solo con status 2xx). Cualquier error de red/timeout/HTTP SHALL loguearse (`logging`) y devolverse como `ok=False`, nunca lanzarse a la UI. `requests` MUST NOT importarse ni añadirse a `requirements.txt`.

#### Scenario: POST exitoso mockeado sin red
- GIVEN `enviar_decision("HANGAR", payload, webhook_url="http://n8n.invalid/hook")` con `urllib.request.urlopen` mockeado que devuelve status 200
- WHEN se llama
- THEN se invoca `urlopen` una vez con timeout 5 y cuerpo JSON que contiene `"decision": "HANGAR"`
- AND el resultado es `{"ok": True, "status": 200, "decision": "HANGAR"}`

#### Scenario: Sin URL no hay POST ni excepción
- GIVEN sin parámetro `webhook_url` y sin env `N8N_WEBHOOK_URL`
- WHEN se llama `enviar_decision("HANGAR", payload)`
- THEN `urlopen` no se llama y el resultado es `ok=False`

#### Scenario: Error de red no rompe la UI
- GIVEN `urlopen` mockeado que lanza `URLError("sin red")`
- WHEN se llama `enviar_decision("INSPECCION", payload, url)`
- THEN no se lanza excepción y el resultado es `ok=False`

### Requirement: Punto de llamada único con dedupe por fingerprint

Tras `decision_en_vivo` en la pestaña Casos de `app/dashboard_ds02.py`, la app SHALL llamar a `enviar_decision` SOLO si `decision != SIN_DECISION`, deduplicando por `fingerprint` en `st.session_state` (un fingerprint ya enviado en la sesión MUST NOT re-enviarse en reruns de Streamlit). Notifican HANGAR e INSPECCION; APTO SHALL solo dejar log local (`_log`) sin POST, y esto SHALL documentarse en el código. El punto de llamada MUST NOT tocar `score_table`, `decidir_ventanas` ni `live_work_order`.

#### Scenario: Rerun con el mismo fingerprint no re-envía
- GIVEN un fingerprint ya enviado en `st.session_state` y una traza HANGAR con ese fingerprint
- WHEN la pestaña Casos se re-ejecuta (rerun)
- THEN `enviar_decision` no se llama de nuevo

#### Scenario: SIN_DECISION nunca notifica
- GIVEN una traza con `decision=SIN_DECISION`
- WHEN se evalúa el punto de llamada
- THEN no se llama a `enviar_decision` ni se deja log de notificación

### Requirement: Flujo n8n importable con Switch de 3 ramas

`n8n/flujo.json` SHALL contener un workflow n8n válido (JSON parseable, formato de exportación) con: nodo Webhook POST con path `ds02/decision`; nodo Switch con 3 ramas sobre `decision` (APTO / INSPECCION / HANGAR); rama HANGAR con Postgres insert + Google Calendar + Gmail; rama INSPECCION con Google Sheets append; rama APTO con Set (log). El JSON MUST NOT contener valores de credenciales (solo referencias). Las credenciales viven en la instancia local de n8n; el repo solo guarda el flujo.

#### Scenario: Flujo válido y con las 3 ramas
- GIVEN `n8n/flujo.json`
- WHEN se parsea como JSON y se inspeccionan los nodos
- THEN es válido, contiene un Webhook `ds02/decision` y un Switch con las 3 salidas APTO/INSPECCION/HANGAR conectadas a sus acciones

### Requirement: Tests bundle C medidos desde la caché

Los tests `test_todos_los_casos_salen_BIEN`, `test_hay_casos_para_cada_estado_y_para_sin_decision` (`tests/test_mia_rules.py`), `test_ciclos_hasta_fallo_coincide_con_la_cache` (`tests/test_simulacion.py`) y `test_perfiles_caen_en_su_banda`, `test_el_modo_historia_se_deriva_de_la_cache`, `test_el_paso_critico_cae_en_hangar_y_el_primero_no` (`tests/test_ui_alta.py`) SHALL reflejar los valores medidos desde `app/cache/` con bundle C (ver cifras en el encabezado de esta spec). Si la medición exige cambiar `CASOS` o `PERFILES`, el cambio SHALL documentarse con el valor medido.

#### Scenario: Las expectativas coinciden con la medición
- GIVEN la caché `app/cache/` del bundle C
- WHEN se ejecutan los 6 tests nombrados
- THEN todos pasan y ninguna expectativa corresponde a valores del bundle B

## MODIFIED

None (capacidad nueva; las desplegadas quedan intactas).

## REMOVED

None.

## RENAMED

None.

## Related capabilities

Cita (no modifica) `ds02-rules-engine` (traza de decisión), `ds02-live-evaluation` (evaluación en vivo y contrato), `ds02-dss-ui` (pestaña Casos). Esta capacidad sustituye el stub de `src/n8n.py` y el placeholder de `n8n/flujo.json` dejados por `2026-11-02-clase-track`.
