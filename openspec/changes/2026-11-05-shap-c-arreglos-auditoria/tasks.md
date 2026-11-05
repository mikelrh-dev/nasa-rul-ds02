# Tasks: SHAP-C por ramas y arreglos de auditoría

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~650–900 (incl. generated notebook) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 docs+drift+seguridad · PR2 deps/CI+guard · PR3 SHAP-C+builder+gate |
| Delivery strategy | local commits per wave, no PR, no push |
| Chain strategy | sequential local commits per SDD phase (parent consolidates, re-runs focused suite, commits); push only with explicit user order at the end |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

## Suggested Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|------|------|----------------------|-----------------|-------------------|
| 1 | Docs P0 + drift/freeze + seguridad | `python -m pytest tests -q` | N/A (docs/config; grep checks) | Revert docs/cache/api/docker diff |
| 2 | Deps/CI + guard `joblib.load` | `python -m pytest tests -q` | CI workflow run | Revert pyproject/CI/guard diff |
| 3 | SHAP-C RED→GREEN + builder+notebook | `python -m pytest tests/test_shap_c.py -q` | `python scripts/build_07_shap_c_notebook.py` | Delete `shap_c.py`+notebook+builder |
| 4 | Final gate + judges | `python -m pytest tests -q` | Notebook re-exec (offline) | Revert per-commit, no push |

## Phase 1: Docs P0 (DOC-C-01, MODIFIED SOTA)

- [x] 1.1 Record bundle C `4.338` as current in rul-spec; multiseed historical. Files: `docs/02_DS02_ensemble_RUL_spec.md` · Size: S · Dep: none · Accept: `4.338` current, multiseed historical, NASA SUM no clamp · Verify: `grep -n "4.338\|históric" docs/02_DS02_ensemble_RUL_spec.md`
- [x] 1.2 Set ADR-011 `R6=C` (deploy C, archive B). Files: `docs/decisions/ADR-011-deploy-bundle-c-archive-bundle-b.md` · Size: XS · Dep: 1.1 · Accept: `R6=C` stated, B archived · Verify: `grep -n "R6=C" docs/decisions/ADR-011*.md`
- **Checkpoint 1:** Docs read consistent; no `models/`/NB01-06 touched. Verify: `git status --porcelain -- models/ notebooks/`

## Phase 2: Drift/Freeze (CACHE-DRIFT-01)

- [x] 2.1 RED: stale `manifest_sha256` test fails loud, no cache reuse. Files: `tests/test_cache_drift.py` (new) · Size: S · Dep: 1.2 · Accept: mismatched digest raises pre-reuse · Verify: `python -m pytest tests/test_cache_drift.py -q` (RED)
- [x] 2.2 GREEN: validate `manifest_sha256` on cache load. Files: cache loader (`scripts/build_ui_cache.py` or `app/cache/` consumer) · Size: S · Dep: 2.1 · Accept: stale digest → loud failure · Verify: `python -m pytest tests/test_cache_drift.py -q`
- [x] 2.3 Freeze `_p1_oof_cache` (resolve path via `scripts/p1_oof_cache.py`); version drift evidence. Files: freeze site + evidence file · Size: S · Dep: 2.2 · Accept: cache frozen, evidence versioned · Verify: `python -m pytest tests -q`
- **Checkpoint 2:** Drift detected, no silent reuse. Verify: `python -m pytest tests -q`

## Phase 3: Security (SEC-API-01, SEC-DOCK-ST-01)

- [x] 3.1 RED: `/health` unauthenticated, `compare_digest` used, write rate-limit. Files: `tests/test_security_api.py` (new) · Size: S · Dep: 2.3 · Accept: tests fail pre-fix · Verify: `python -m pytest tests/test_security_api.py -q` (RED)
- [x] 3.2 GREEN: `compare_digest`, open `/health`, rate-limit writes in `app/api.py`. Files: `app/api.py` · Size: S · Dep: 3.1 · Accept: `/health` 200 unauthenticated; writes 429 over limit · Verify: `python -m pytest tests -q`
- [x] 3.3 Bind Docker/Streamlit to loopback at the host publish only: `docker-compose.yml` publishes `127.0.0.1:8000:8000` and `127.0.0.1:8501:8501`; keep `--host 0.0.0.0` inside the container (required for port mapping) and note TLS-proxy requirement. Files: `docker-compose.yml`, `Dockerfile` (note only), `app/streamlit_app.py` (docstring only) · Size: S · Dep: 3.2 · Accept: compose publishes loopback, container bind unchanged · Verify: `grep -n "127.0.0.1:8000\\|127.0.0.1:8501" docker-compose.yml`
- **Checkpoint 3:** Security green, no `0.0.0.0`. Verify: `python -m pytest tests -q`

## Phase 4: Deps/CI (DEP-CI-01)

- [x] 4.1 Pin `pyproject.toml` deps (TF, LightGBM, sklearn, shap, numpy, pandas, nbformat). Files: `pyproject.toml` · Size: S · Dep: 3.3 · Accept: pinned install succeeds on clean checkout · Verify: `python -m pip install -e . --dry-run`
- [x] 4.2 Create CI running `python -m pytest tests -q` (no retrain). Files: `.github/workflows/ci.yml` (new) · Size: S · Dep: 4.1 · Accept: CI executes pytest, reads `app/cache/` only · Verify: `cat .github/workflows/ci.yml`
- **Checkpoint 4:** Pinned deps + CI defined. Verify: `python -m pytest tests -q`

## Phase 5: Guard joblib (SEC-JOBLIB-01)

- [x] 5.1 RED: unverified `joblib.load` refused pre-deserialization. Files: `tests/test_joblib_guard.py` (new) · Size: S · Dep: 4.2 · Accept: no-checksum load refused · Verify: `python -m pytest tests/test_joblib_guard.py -q` (RED)
- [x] 5.2 GREEN: create checksum sidecars/manifest for clase models first (so valid loads keep working), then route the 5 `joblib.load` sites (shap_clase, shap_clase_e2, train_mlp, predict, repackage) through `verify_artifact_sha256` before deserialization. Files: sidecar generator + 5 files above · Size: M · Dep: 5.1 · Accept: valid checksum loads, invalid refused, `test_clase_shap*` still green · Verify: `python -m pytest tests/test_joblib_guard.py tests/test_clase_shap.py tests/test_clase_shap_e2.py -q`
- **Checkpoint 5:** Guard green. Verify: `python -m pytest tests -q`

## Phase 6: SHAP-C RED→GREEN (SHAPC-BILSTM/LGBM/META/DATA-01)

- [x] 6.1 RED: shapes `(50,19)`/`(93,)`/2D, additivity, no causal. Files: `tests/test_shap_c.py` (new) · Size: M · Dep: 5.2 · Accept: tests fail without `ejecutar_shap_c` · Verify: `python -m pytest tests/test_shap_c.py -q` (RED)
- [x] 6.2 GREEN BiLSTM grouped Permutation (DeepExplainer infeasible, error 3.06; exact telescoping), 19 channels, train fold-0 background; error `<1e-2` in metadata. Files: `src/ds02_rul/shap_c.py` · Size: M · Dep: 6.1 · Accept: `base+sum≈model` within `1e-2`, EMA out · Verify: `python -m pytest tests/test_shap_c.py -q`
- [x] 6.3 GREEN LGBM TreeSHAP (reuse `ensemble._tabular`) + meta Permutation over the REAL meta width (verify `ridge_meta.n_features_in_` first: if 3, include `cycles/100` as documented third input; if 2, `Z=[p_lstm,p_lgb]`); `1e-5`. Files: `src/ds02_rul/shap_c.py` · Size: M · Dep: 6.2 · Accept: both within `1e-5`, meta width matches bundle · Verify: `python -m pytest tests/test_shap_c.py -q`
- [x] 6.4 NASA SUM no clamp (`>125` targets) + `metadata.json` (explainer, background, `aditividad_max_error`). Files: `src/ds02_rul/shap_c.py`, `resultados/shap_bundle_C/` · Size: S · Dep: 6.3 · Accept: SUM exponentials, bundle C read-only · Verify: `python -m pytest tests/test_shap_c.py -q`
- **Checkpoint 6:** Additivity per branch green. Verify: `python -m pytest tests/test_shap_c.py -q`

## Phase 7: Builder+Notebook (SHAPC-NB-01)

- [ ] 7.1 Builder nbformat notebook (never hand-edited). Files: `scripts/build_07_shap_c_notebook.py` (new) · Size: M · Dep: 6.4 · Accept: build produces notebook, NB01-06 untouched · Verify: `python scripts/build_07_shap_c_notebook.py`
- [ ] 7.2 Generate thin notebook `notebooks/07_shap_c_bundle_c.ipynb`, no causal text. Files: `notebooks/07_shap_c_bundle_c.ipynb` (generated) · Size: S · Dep: 7.1 · Accept: runs, shapes pass, no causal claim · Verify: `python -m pytest tests/test_shap_c.py -q`
- **Checkpoint 7:** Notebook built via builder only. Verify: `git status --porcelain -- notebooks/01* notebooks/02* notebooks/03* notebooks/04* notebooks/05* notebooks/06*`

## Phase 8: Gate + Judges

- [ ] 8.1 Full gate: suite green, `models/`+NB01-06 byte-identical. Dep: 7.2 · Accept: pytest green (pre-existing failures reported), no retrain · Verify: `python -m pytest tests -q && git status --porcelain -- models/`
- [ ] 8.2 Two independent judges re-execute scope, classify claims confirmed/refuted/not-verifiable. Dep: 8.1 · Accept: judge report filed, no refuted claim merges · Verify: `python -m pytest tests -q`
- **Checkpoint 8 (final):** SHAP-C per branch additive, P0 fixes verified, bundle C intact.
