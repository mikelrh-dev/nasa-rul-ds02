# Tasks: Flujo n8n mínimo MIA-3

**Change:** `2026-11-06-ds02-n8n-decision`

Decision needed before apply: No
Chained PRs recommended: No
400-line budget risk: Low

---

## 1. Tests bundle C medidos desde la caché

- [ ] 1.1 Re-medir CASOS (`probar_casos`), PERFILES y ciclos de hangar desde `app/cache/` con comandos ejecutados y corregir las expectativas de los 6 tests nombrados solo si la medición lo exige, documentando cada cambio. **Acceptance:** `python -m pytest tests/test_mia_rules.py tests/test_simulacion.py tests/test_ui_alta.py -q` pasa y cada expectativa coincide con el valor medido (cifras en `spec.md`).
- [ ] 1.2 Escribir el test RED de `payload_desde_traza` (payload exacto de 14 claves, sin `X_raw`, sin re-clasificar, JSON-serializable). **Acceptance:** el test falla antes de implementar y pasa después.

## 2. Payload n8n

- [ ] 2.1 Crear `app/ui_n8n.py` con `payload_desde_traza` reutilizando la traza de `decision_en_vivo` (sin `L.classify`, sin nombre genérico que sombree `mia/motor.py`). **Acceptance:** el test RED 1.2 pasa y `grep -rn "L.classify\|classify(" app/ui_n8n.py` retorna vacío.

## 3. Envío por webhook

- [ ] 3.1 Escribir tests RED de `enviar_decision` (`src/n8n.py`): POST con `urllib` mockeado sin red, sin URL no hay POST, error de red no lanza, decisión inválida no hace POST. **Acceptance:** los tests fallan con el stub actual (`NotImplementedError`) y pasan tras implementar.
- [ ] 3.2 Implementar `enviar_decision` real: validación de decisión, URL por parámetro o env `N8N_WEBHOOK_URL`, POST `urllib` timeout 5 s, retorno `{ok,status,decision}`, errores logueados sin excepción. **Acceptance:** tests 3.1 en verde; `requests` no aparece en `src/n8n.py` ni en `requirements.txt`.

## 4. Punto de llamada en la app

- [ ] 4.1 Añadir el punto de llamada único tras `decision_en_vivo` en la pestaña Casos de `app/dashboard_ds02.py`: solo si `decision != SIN_DECISION`, dedupe por fingerprint en `st.session_state`, POST solo para HANGAR/INSPECCION, APTO solo log local sin POST. **Acceptance:** test de dedupe (mismo fingerprint no re-envía, SIN_DECISION nunca) en verde; `score_table`, `decidir_ventanas` y `live_work_order` sin cambios en el diff.

## 5. Flujo n8n

- [ ] 5.1 Escribir `n8n/flujo.json` real (webhook POST `ds02/decision`, Switch 3 ramas, HANGAR → Postgres+Calendar+Gmail, INSPECCION → Sheets, APTO → Set log) sin valores de credenciales, y su test (JSON válido, nodos y ramas). **Acceptance:** `json.load` pasa y el test del flujo está en verde.

## 6. Verificación y cierre

- [ ] 6.1 Ejecutar `python scripts/verify_gate.py` (suite completa) y el scope `--only` de los tests tocados; escribir `verify-report.md` separando EJECUTADO de LEÍDO. **Acceptance:** gate con salida real registrada y veredicto explícito.
- [ ] 6.2 Archivar a `openspec/changes/archive/2026-11-06-ds02-n8n-decision/` y mergear en `openspec/specs/` según la convención (avisar antes de mergear REMOVED/RENAMED — no hay ninguno). **Acceptance:** change archivado y spec desplegada creada.
