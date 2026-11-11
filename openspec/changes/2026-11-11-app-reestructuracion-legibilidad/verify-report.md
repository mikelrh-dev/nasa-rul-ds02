# Verify report: app/ readability restructure

**Date:** 2026-11-11
**Change:** `2026-11-11-app-reestructuracion-legibilidad`
**Mode:** standard (strict_tdd active; full suite executed by the parent)
**Completeness:** proposal + spec delta + design + tasks + implementation (phases 0-5) + 2 independent judges

## Verification command

`python -m pytest tests -q`

## Result

`446 passed, 1 skipped` (exit 0). Run by the parent after every phase and again after Phase 5.
The single skip is `test_mia_rules.py:181` (pre-existing expected skip).

## Spec compliance matrix

| Requirement | Status | Evidence |
|---|---|---|
| Stable cache and registry location invariant (ADDED) | Compliant | `app/_paths.py:23` anchors `ROOT`; `app/lib/ui_data_loader.py:26-35`, `ui_inference.py:19-24`, `ui_rules.py:26-29`, `ui_shap.py:18-22`, `hangar.py:24,194-195`, `app/services/api.py:50,56,193` read from it. Resolved paths: `<repo>/app/cache`, `<repo>/models/ds02_manifest.json`, `<repo>/app/registros_flota.json`, `<repo>/app/registros_sesiones`. No other cache directory created. |
| Package layout and import contract (ADDED) | Compliant | `app/__init__.py` plus `entrypoints/`, `ui/`, `lib/`, `services/`. `grep -rn "sys.path.insert" app/` matches only `app/entrypoints/`. `app.lib.ui_data_loader`, `app.ui._tab_flota` and `app.services.api` import; 0 flat app imports remain. |
| Dashboard orchestrator facade (MODIFIED) | Compliant | `app/entrypoints/dashboard_ds02.py` is orchestration-only (LOC 909 -> 603); the four tabs live in `app/ui/`; the dashboard constructs `AppCtx` and passes it to every tab; `app/lib/context.py` is a pure dataclass; the hot path (`windows/telemetry/frame_cache`, corregir+decidir) is byte-identical to the pre-change code. |

## Design coherence

| Decision | Status | Evidence |
|---|---|---|
| D1 - Phase 0 fixes the gate before any move | Done | `src/reglas.py:20,37` re-exports `pava_causal_no_creciente` (borrado después: ver nota en «Frozen artifacts»); `tests/test_reglas_sombreado.py` reproduces the shadowing order deterministically. |
| D2 - `_paths.py` owns every repository path | Done | `app/_paths.py`; before/after absolute-path fingerprint is byte-identical (empty diff). |
| D3 - One `AppCtx` cycle, no `ctx_from_dashboard` | Done | 0 occurrences of `ctx_from_dashboard`, `sys.modules.get` and `if ctx is None` in `app/`. |
| D4 - Package imports, one entrypoint bootstrap | Done | 0 flat app imports; `sys.path.insert` only in the two entrypoints. |
| D5 - Delete dead code instead of relocating it | Done | 22 dead imports removed; duplicated tokens, `_latin1`, `_ahora` and thresholds unified. |

## Independent judges

Two independent verifier subagents (read-only) explored the whole project:

- **Judge A (spec/architecture):** PASA CON OBSERVACIONES. Found the thin orchestrator only partial, the entrypoint deriving `ROOT` from `__file__`, obsolete docstrings and a wrong line in `tasks.md`. All addressed in Phase 5.
- **Judge B (behavior/residual):** PASA CON OBSERVACIONES. Found false "pure/no Streamlit" docstrings, old routes in live docs, dead imports/route constants and a stale API docstring. All addressed in Phase 5.

## Frozen artifacts and hashes

- `git diff --name-status 298272f..HEAD` lists no change under `models/`, `app/cache/`, `src/mia/`, `src/ds02_rul/`, `notebooks/`, `scripts/` or `n8n/`. The only source change outside `app/` is the additive `src/reglas.py` re-export in Phase 0. Nota posterior: ese modulo se elimino en esta misma rama; hoy `scripts/auditoria/freeze_rules_evidence.py` importa `src.mia.reglas` directamente.
- `app/cache/` keeps its three tracked files; the `cache_manifest.json` seal matches the manifest and the parquet files.
- `models/ensemble.joblib` SHA-256 `d6c70142...` matches `models/ds02_manifest.json` and the README.
- Threshold probe: `DEFAULT_AIRWORTHY = 30.0`, `DEFAULT_AOG = 25.0`; `classify(30)=APTO`, `classify(29.9)=INSPECCION`, `classify(25)=INSPECCION`, `classify(24.9)=HANGAR`.

## Runtime verification (Playwright MCP)

Streamlit launched with `streamlit run app/entrypoints/dashboard_ds02.py --server.address 127.0.0.1 --server.port 8501 --server.headless true`; HTTP 200. All four tabs render and the model paths were exercised end-to-end:

| Use case | Action | Observed result |
|---|---|---|
| Fleet scoring from cache (Flota) | Load demo scenario (unidad 14, ciclo 29) | "Unidades en hangar 3 / 3 en el ciclo 29"; header SHA-256 d6c70142, 6.196 ventanas, banda 90% |
| Single unit (Motor) | Open Motor with the demo unit | RUL restante 36.9, L_inf 22.1, regla R9_HANGAR ("L_inf por debajo del umbral de hangar"), derivacion a hangar |
| New case scoring (Casos) | "Evaluar unidad" on the demo window (U15, ciclos 1->6, 300 filas) | RUL p35 56.6, L_inf 32.2, L_sup 76.6 (banda 90%), 251 ventanas puntuadas, SHA-256 del artefacto d6c701429eed, contrato w50/s1, regla R7_APTO, estado APTO |
| SHAP (Casos) | "Calcular SHAP para este motor" | Top-10 features computed with TreeExplainer (xs_last10_Nc, xs_mean_Nc, xs_last_T48, ..., cyc_norm) |
| Sandbox (Casos) | Demo segment (ciclos 3->25, 243 ventanas) | RUL p35 al final del tramo 39.1 ciclos, cruce a hangar en ciclo 25, INSPECCION PROGRAMADA |

- 0 console errors across navigation, scoring, demo and SHAP.
- Screenshots: `C:/Users/mikel/.playwright-mcp/ds02_flota.png`, `ds02_casos.png`, `ds02_resultado_ejemplo.png`, `ds02_shap.png`, `ds02_demo_hangar.png`.

## Issues

- None critical. Phase 5 closed every observation the two judges raised.
- Two pre-existing Pyright typing warnings remain in `app/lib/informe_auditoria.py` (`itertuples` attribute access); no runtime effect, not a gate.

## Final verdict

PASS.
