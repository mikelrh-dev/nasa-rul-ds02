# Proposal: SHAP-C por ramas y arreglos de auditoría

**Change:** `2026-11-05-shap-c-arreglos-auditoria`
**Status:** Proposed
**Capability:** modifica `rul-prediction-ds02` (`openspec/specs/rul-prediction-ds02/spec.md`)
**Rama/Fecha:** `clase-modelo-c` / 2026-11-05

## Decisiones congeladas

- Manifest C 4.338 manda; R6 = bundle C.
- Multisemilla no-CSV = histórica.
- SHAP-C por ramas: DeepSHAP BiLSTM→19 canales + TreeSHAP LGBM + meta `[p_lstm,p_lgb]`; EMA fuera; no causal.
- NB01-06 intactos; notebook nuevo fino.

## Intent

SHAP-C válido por rama sobre bundle C sin reentrenar ni tocar NB01-06, más arreglos P0 de auditoría.

## Scope

### In Scope

- `src/ds02_rul/shap_c.py`: DeepSHAP 19 canales + TreeSHAP + meta; aditividad por rama.
- Notebook fino nuevo (builder) + tests formas/aditividad/no-causal.
- Docs P0: rul-spec C vigente (4.338), ADR-011 R6=C, multisemilla histórica.
- Drift caché: `manifest_sha256`; freeze `_p1_oof_cache`; evidencia versionada.
- Seguridad: compare_digest, /health, rate-limit, bind 127.0.0.1 (API/Docker/Streamlit).
- Deps `pyproject` + CI mínimo; guard `joblib.load` sin verify (`clase/`, `scripts/`).

### Out of Scope

- Tocar `models/`, reentrenar, re-ejecutar multisemilla.
- Editar NB01-06; SHAP ensemble completo/EMA; lectura causal.
- MLflow/n8n.

## Capabilities

- New: `shap-c-explanation` (SHAP-C por ramas).
- Modified: `rul-prediction-ds02` (docs C, drift, seguridad, deps).

## Approach

TDD estricto (`python -m pytest tests -q`): RED→GREEN por rama; notebook vía builder; mismo preproceso que entrenamiento. Dep: bundle C en `models/` (lectura). Byte-compatibles: `models/*`, NB01-06, métricas.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `src/ds02_rul/shap_c.py` | New | SHAP-C por ramas |
| notebooks (nuevo) + builder, tests | New | notebook fino + tests |
| rul-spec, ADR-011 | Modified | C 4.338, R6=C, histórica |
| `app/cache/`, `_p1_oof_cache`, evidencia | Modified | manifest_sha256, freeze, versionado |
| `app/api.py`, Docker, Streamlit | Modified | compare_digest, /health, rate-limit, 127.0.0.1 |
| `pyproject.toml`, CI, `clase/`, `scripts/` | Modified | deps, CI mínimo, guard joblib.load |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Agregación 19 canales pierde detalle | Med | documentar; test formas |
| Preproceso distinto rompe aditividad | Med | features del bundle; assert base+suma |
| Drift silencioso / endurecer API | Low | manifest_sha256+freeze; /health sin auth, rate-limit escritura |

## Rollback Plan

Revert por commit sin push; `models/` y NB01-06 fuera del diff. Si falla aditividad, retirar `shap_c.py`+notebook; bundle C intacto.

## Success Criteria

- [ ] SHAP-C por ramas con aditividad; EMA fuera; no causal.
- [ ] NB01-06 y `models/` byte-idénticos.
- [ ] Docs P0: 4.338, R6=C, multisemilla histórica.
- [ ] Drift detectado (manifest_sha256 + freeze).
- [ ] Seguridad API/Docker/Streamlit + guard joblib.
- [ ] `python -m pytest tests -q` verde (preexistentes reportados).
