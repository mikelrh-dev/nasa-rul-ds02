# Verification Report: SHAP-C por ramas y arreglos de auditoría

**Change:** `2026-11-05-shap-c-arreglos-auditoria` · **Rama:** `clase-modelo-c` · **Fecha:** 2026-11-05
**Verificador:** padre (orquestador), tras detener al subagente sdd-verify por bucle de lecturas repetidas.

## Gate completo (Fase 8.1)

- Comando: `.venv/Scripts/python scripts/verify_gate.py` (= `python -m pytest tests -q`, ~3 min)
- Primera corrida: `5 failed, 309 passed, 1 skipped` — fallos en `test_audit_fixes` (1), `test_mia_rules` (1), `test_rules_gate` (3), todos de reglas/freeze.
- Causa raíz (verificada por el padre, no regresión): el `_p1_oof_cache.npz` generado con `.venv` (3.12) des-skippea esos 5 tests, que fallan por drift venv vs intérprete histórico de notebooks (system 3.10, caveat en `openspec/config.yaml`). Sin el fichero: subset `3 passed, 5 skipped`.
- Decisión: fichero generado aparcado en scratch (no queda en el repo); freeze queda exit 3 en clon limpio / exit 5 documentado con OOF de venv (`freeze-evidence.md`). No se re-congela `calibracion_banda.json`.
- Segunda corrida: **GATE PASSED**. Conteo corregido por Juez 2 (re-ejecución completa propia): 315 tests = **308 passed + 7 skipped + 0 failed** (6× `_p1_oof_cache` ausente + 1× CSV multisemilla ausente en árbol limpio; el 309+6 inicial contaba CSV presente en la corrida del padre). El PASS es creíble; la cifra congelada correcta es 308+7. Exit 5 de freeze NO re-verificado (solo documentado); CI nunca ejercita freeze (skips).

## Invariantes (Fase 8.3)

- `git status --porcelain -- models/ notebooks/01_*.ipynb ... notebooks/06_*.ipynb` → **vacío** (models/ y NB01-06 byte-idénticos; la única edición en `models/ds02_manifest.json` fue en Fase 5: 3 claves de checksum en `artifacts`, métricas intactas).
- Aditividad SHAP-C (bundle completo 200×200, `resultados/shap_bundle_C/metadata.json`): BiLSTM **9.54e-07**, LGBM **3.85e-07**, meta **1.42e-13** (tolerancias spec: <1e-2 agrupado / <1e-5 Tree y meta).
- Ancho meta real verificado en runtime: `n_features_in_ = 2` (`Z=[p_lstm,p_lgb]`).
- Notebook 07: 6 celdas, execution_count 1..4 secuencial, 0 errores, determinista (idéntica aditividad a la corrida previa).

## Desviaciones aceptadas

- **D2 (DeepExplainer → Permutation agrupado BiLSTM):** DeepExplainer inviable con Keras3 While-LSTM + shap 0.54.1 (error medido 3.06 >> 1e-2; GradientExplainer 3-11). Sustituto exacto por telescopado (19 jugadores), declarado en docstring + metadata + spec/design enmendados.
- **Manifest en Fase 5:** sidecars de checksum de clase en `artifacts` (métricas y hashes de bundle intactos), con indexación unicode normalizada.
- **Freeze:** ver decisión arriba; evidencia en `freeze-evidence.md`.

## Pendiente

- **8.2 Dos jueces independientes: HECHO** — Juez 1: todo confirmado, puede cerrarse. Juez 2: PASS confirmado (308+7, exit 0), conteo 309+6 refutado y corregido arriba; exit 5 no re-verificado; CI sin freeze.
- **Archive** tras jueces: merge a `openspec/specs/` + mover change a `openspec/changes/archive/`.
