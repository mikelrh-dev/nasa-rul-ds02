# Proposal: DS02 maintenance decision-support surface (Streamlit)

**Change:** `2026-10-21-ds02-streamlit-dss`
**Status:** Implemented
**Capability:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md)

---

## Why

The DS02 ensemble ships a calibrated band (`predict_interval`) and per-engine
metrics, but the only interface is `app/dashboard.py`: one engine at a time, two
line charts, and a live 2.3 GB HDF5 read on every cold start. That surface cannot
answer the two questions a maintenance lead actually asks — *which aircraft is
grounded right now* and *how much do I trust the number* — and it cannot be shown
from a laptop that has no dataset on disk.

The audit of the original UI plan
([`docs/plans/planificacion_desarrollo_ui_streamlit.md`](../../../docs/plans/planificacion_desarrollo_ui_streamlit.md))
also found four blockers that this proposal resolves explicitly:

| Blocker | Finding | Resolution |
| --- | --- | --- |
| B1 — unreachable green state | With the proposed rule (`L_inf >= 50` = airworthy) **no unit is ever green**: the widest calibrated lower bound on the test split is ≈ 36 (point ≈ 60.6 minus the 24.47 quantile of the `[50, 75)` bin). | Thresholds re-based on the measured scale: airworthy at `L_inf >= 30`, preventive 25–30, AOG below 25. |
| B2 — FD001 artifacts mixed into a DS02 story | `models/alarm_policy.json` and `models/test_eval_ultima_ventana.csv` are FD001/v3 products (`"dataset_calibracion": "FD001"`, engines 1–100). | Both are excluded, and a regression test asserts the UI never references them. |
| B3 — hardcoded metrics | The plan hardcodes `2.88 / 3.72 / 8.04` and `1.12 / 4.17 / 5.35`, which come from `docs/informes/informe-2026-10-20-ejecucion-cuaderno.md`, not from `ds02_manifest.json` (whose macro per-engine RMSEs are `2.76 / 3.77 / 8.18`). | Every figure is computed from the cached predictions; the manifest is displayed separately as the frozen audit contract. |
| B4 — cache written into `models/` | The plan proposes `models/ds02_ui_telemetry_cache.csv`, contradicting its own golden rule and the repository rule that `models/` is immutable. | The cache lives in `app/cache/`, and `models/` is opened read-only. |

Two smaller corrections: `app/dashboard.py` is **already** DS02 (not FD001) and
stays untouched; engine 14 lasts **76** cycles, not 75; and the DS02 channels are
`T24 … Wf` (plus `alt/Mach/TRA/T2`), not the FD001 `s7`-style names.

## What changes

1. **`scripts/build_ui_cache.py`** — one offline pass over `models/ensemble.joblib`
   and the DS02 test split, writing two small Parquet tables into `app/cache/`
   (6 196 windows and 12 538 telemetry rows) plus a provenance manifest. Nothing
   under `models/` is written.
2. **`app/ui_data_loader.py`** — cached readers, a pure triage policy, live metric
   computation and work-order serialisation. Importing it does **not** import
   TensorFlow.
3. **`app/dashboard_ds02.py`** — sidebar simulation controls and four tabs: fleet
   hangar view, RUL + conformal band, sensor/operating-condition radiography, and
   the engine-14 honesty audit. Adds a JSON/CSV work-order download for grounded
   units.
4. **`.streamlit/config.toml`** — a locked dark theme (colors, fonts, radii,
   padding, chart palettes). The Plotly figures reuse the same tokens, so charts
   and widgets share one surface. No CSS is injected.
5. **`tests/test_dss_ui.py`** — the triage thresholds, the cache contract, the
   work-order contract, the theme, the accessible names (`alt`) and a guard
   against FD001 artifacts.

The model, the preprocessing and every artifact in `models/` are untouched:
`ensemble.joblib`, `bilstm_ds02.keras`, `scaler.joblib` and `ds02_manifest.json`
are read, never rewritten. `app/dashboard.py` and `app/api.py` keep working.

## Impact

| | Value |
| --- | --- |
| Runtime without the HDF5 | full UI from `app/cache/`; TF is not imported |
| Render time | 1.4 s first run, 0.24 s per rerun (measured) |
| `models/` | read-only; hashes unchanged (`0acd795b…`, `5923d2a1…`) |
| Cold start | cache read + Plotly render, no 2.3 GB scan |
| New dependency | `plotly` |
| Existing tests | `pytest tests -q` stays 10/10, plus the new module |

## Rollback plan

Delete `app/dashboard_ds02.py`, `app/ui_data_loader.py`, `app/cache/`,
`scripts/build_ui_cache.py` and `tests/test_dss_ui.py`; drop `plotly` from the
dependency files. Nothing else is modified, so there is no state to restore. The
regeneration script is idempotent, so a bad cache is fixed by re-running it.

## Artifacts that stay byte-compatible

`models/ensemble.joblib`, `models/bilstm_ds02.keras`, `models/scaler.joblib`,
`models/ds02_manifest.json`, `app/dashboard.py`, `app/api.py`, and every file under
`src/ds02_rul/`.
