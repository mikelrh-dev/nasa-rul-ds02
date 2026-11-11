# Tasks: app/ readability restructure

**Change:** `2026-11-11-app-reestructuracion-legibilidad`
**Status:** Proposed
**Test command:** `python -m pytest tests -q`

| # | Task | Status | Acceptance |
|---|------|--------|------------|
| 1 | **Phase 0 — gate prerequisite** | | |
| 1.1 | Re-export `pava_causal_no_creciente` from `src/reglas.py` | Done | `pytest tests/test_rules_gate.py -q` passes 9/9 in isolation and in the full suite |
| 1.2 | Add a regression test that reproduces the shadowing order | Done | `pytest tests/test_mia_reglas_directas.py tests/test_api_limites.py tests/test_rules_gate.py -q` passes |
| 2 | **Phase 1 — dead code and duplicated tokens** | | |
| 2.1 | Delete the 22 dead imports in `app/dashboard_ds02.py` | Done | AST scan finds 0 unused imported names; suite green |
| 2.2 | Unify the design tokens on `app/theme.py` | Done | `_tab_flota`, `_tab_motor`, `_tab_auditoria` and `_sandbox_estres` import tokens from `theme.py`; no local hex literals |
| 2.3 | Unify `_latin1` on `pdf_partes.py` and `_ahora` on `hangar.py` | Done | one definition each; both call sites resolve to it; suite green |
| 2.4 | Unify the 30/25 thresholds on `L.DEFAULT_AIRWORTHY` / `L.DEFAULT_AOG` | Done | `_sidebar`, `_sandbox_estres`, `ui_alta`, `ui_n8n` and `dashboard_helpers` read the constants |
| 2.5 | Refresh `app/README.md` and `app/ui_modulos/__init__.py` | Done | docs match the code; suite green |
| 3 | **Phase 2 — close the `AppCtx` cycle** | | |
| 3.1 | `_sandbox_estres` receives `AppCtx`; delete the 8 optional parameters and the `sys.modules.get` fallback | Done | `_tab_casos.py:943` passes `ctx`; no dashboard import in the module |
| 3.2 | Drop the `if ctx is None` fallback in the four tabs | Done | no `ctx_from_dashboard` call sites remain |
| 3.3 | Delete `ctx_from_dashboard()` from `app/context.py` | Done | `context.py` is a dataclass only; suite green |
| 4 | **Phase 3 — path owner** | | |
| 4.1 | Create `app/_paths.py` with `ROOT`, `APP_DIR`, `CACHE_DIR`, registry paths and the secrets path | Done | `app/_paths.py` anchors on `Path(__file__).resolve().parents[1]`; the absolute-path fingerprint before/after is byte-identical (empty `diff`) |
| 4.2 | Point `ui_data_loader`, `ui_inference`, `ui_rules`, `ui_shap`, `api`, `dashboard_ds02`, `hangar` and `streamlit_app` at `_paths.py` | Done | `grep -rn "__file__" app/` finds it only in `_paths.py` (plus a docstring mention); the 20-file app suite passes `250 passed, 1 skipped` |
| 5 | **Phase 4 — package move** | | |
| 5.1 | Create `app/__init__.py` and the `app/entrypoints/`, `app/ui/`, `app/lib/`, `app/services/` packages | Pending | `app.lib.ui_data_loader`, `app.ui._tab_flota` and `app.services.api` import |
| 5.2 | Move the entrypoints, UI, lib and API modules | Pending | no module left at the old `app/` root except `_paths.py` |
| 5.3 | Replace the flat imports with package imports | Pending | `grep -rn "sys.path.insert" app/` finds no library module; no flat app import remains |
| 5.4 | Update the 32 `AppTest.from_file` paths and the 12 structural `ui_modulos` references | Pending | suite green |
| 5.5 | Update the `README.md` start commands | Pending | `streamlit run app/entrypoints/dashboard_ds02.py` and `uvicorn app.services.api:app` |
| 6 | **Verification** | | |
| 6.1 | Run the full suite and a headless render | Pending | `python -m pytest tests -q` green; dashboard renders without exception |
| 6.2 | Hash `models/`, `app/cache/` and `src/mia/` before and after | Pending | every SHA-256 unchanged and no new file under `models/` |
