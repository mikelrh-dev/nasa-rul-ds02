# Tasks: DS02 pre-defense hardening

**Change:** `2026-10-26-ds02-pre-defense-hardening`
**Status:** Proposed

Each task closes with its acceptance check. `tdd: true` per
`openspec/config.yaml`; the RED test is written before the implementation in
every task that adds logic. Commands assume the repository root
`C:\Users\mikel\Desktop\Pruebas\nasa` and the repository virtualenv
`.venv\Scripts\python.exe`.

## Review workload guard

```
Decision needed before apply: No
Chained PRs recommended: No
400-line budget risk: Low
```

Forecast: the whole change is under 120 authored lines across `Dockerfile`, two
documents, `app/twin.py`, `app/ui_inference.py`, `app/ui_data_loader.py`,
`app/dashboard_ds02.py` and three test files. No single task exceeds 40 lines.
One commit per phase, one phase at a time.

---

## Phase 1 — Deployment

### 1. Ship the rules layer in the image

**Modifies** `Dockerfile`: add `COPY mia/ ./mia/` beside the existing `COPY`
lines.

Acceptance: `grep -n "^COPY" Dockerfile` lists `mia/`, and the Dockerfile parses
(`docker compose config` still succeeds).

### 1.1 Prove the fix in the tree the Dockerfile produces

**Creates** a scratch copy of the tree the Dockerfile copies — `src/`, `app/`,
`scripts/`, the four files under `models/` listed in the Dockerfile, plus
`mia/` — outside the repository, and imports the dashboard entrypoint from it.

Acceptance: the import raises no `ModuleNotFoundError`, and the same tree
without `mia/` does raise it. Both results are printed and recorded in the
verify report. The scratch copy lives in the Hermes scratch directory, never in
the repository.

---

## Phase 2 — Documentary coherence

### 2. State the stride in the defense document

**Modifies** `docs/defensa_ds02_explicacion_logica_negocio.md`: line 20 and the
phrase at line 107. The window is 50 rows sampled every **100** rows
(`STRIDE = 100`), so it spans **~0,44 flight cycles**. The `2` that appears
today is the cache `step` (`app/dashboard_ds02.py:567`), which is how many
windows overlap, not the sampling distance.

Acceptance: `grep -rn "cada 2 filas" docs/` returns nothing, and the document
states 100 and 0,44.

### 3. Stop pointing at the broken legacy board

**Modifies** `README.md`: the interfaces block offers `streamlit run
app/dashboard.py`, which fails to render today
(`ValueError: cannot reindex on an axis with duplicate labels` at
`app/dashboard.py:100`, verified against the HDF5). Point it at
`app/dashboard_ds02.py` only. The same section describes a "fifth tab"; the
surface has four (Flota, Motor, Casos nuevos, Auditoría).

Acceptance: `grep -n "dashboard.py" README.md` returns only
`app/dashboard_ds02.py`, and `grep -n "fifth tab" README.md` returns nothing.

### 4. Stop tracking a stale copy of the dashboard

**Modifies** the repository: `git rm --cached app/dashboard_ds02.py.bak_pestanas`.
The file is a 147 KB copy of `app/dashboard_ds02.py` from the previous day,
committed by mistake; nothing imports it.

Acceptance: `git ls-files | grep bak_pestanas` returns nothing, and
`grep -rn "bak_pestanas" app/ tests/ scripts/` returns nothing.

---

## Phase 3 — The window that decided

### 5. `vista_resultado` reports the deciding window

**Creates** a RED test first, in `tests/test_engine_flow.py`: build a twin from
cached windows at `step=2` whose last cycle holds more than one window, and
assert that `vista_resultado` reports the position of the window with the lowest
lower bound in that cycle.

**Modifies** `app/twin.py`: replace `"window": int(len(frame) - 1)` with the
index label of the deciding row, and state in the docstring that the value is a
position in the saved series. Update the existing test that pins the old number
in the same commit.

Acceptance: `python -m pytest tests/test_engine_flow.py -q` passes, and the
reported value for the U11/ciclo 22 alta is 1177, not 1218.

### 5.1 The point of use says what the number is

**Modifies** `app/dashboard_ds02.py` around line 1841: the caption cites the
window as a position in the saved series, so a reader cannot mistake it for a
dataset window index.

Acceptance: the rendered caption contains the phrase that names the saved series,
and `AppTest` renders without an exception.

---

## Phase 4 — Data robustness and provenance

### 6. Reject non-finite values

**Creates** a RED test first, in `tests/test_live_eval.py`: a window whose `T48`
holds `inf` and another whose `Ps30` holds `-inf` are both rejected with the
column and the row named.

**Modifies** `app/ui_inference.py`: extend the existing numeric check (the loop
that already rejects NaN with `coerced.isna()`) to reject `np.isinf`, reusing the
same message format at `app/ui_inference.py:336-339`.

Acceptance: `python -m pytest tests/test_live_eval.py -q` passes, and the
rejection message names the column and the row.

### 7. Verify the cache hash against the artifact

**Creates** `artifact_hash_check(provenance)` in `app/ui_data_loader.py`: a pure
function, no Streamlit, that compares
`provenance["artifact"]["ensemble_sha256"]` with the SHA-256 of
`models/ensemble.joblib` on disk and returns `{"checked", "ok", "esperado",
"leido"}`. Any unreadable input returns `checked: False` instead of raising.

**Creates** a test in `tests/test_dss_ui.py` covering the three outcomes: the
hashes match, they differ, and the artifact is missing.

**Modifies** `app/dashboard_ds02.py`: paint a warning in the sidebar only when
`checked` is true and `ok` is false. The green path adds no widget.

Acceptance: `python -m pytest tests/test_dss_ui.py -q` passes, and a grep of the
dashboard shows the warning is inside the `if not ok` branch.

### 7.1 The green path moves nothing

**Modifies** nothing; this task exists to prove the previous one did not move a
widget count. Run the whole suite and record the count before and after.

Acceptance: `python -m pytest tests -q` passes and the collected test count is
unchanged from the baseline recorded in the verify report.

---

## Phase 5 — Verification

### 8. Full gate and evidence gate

**Runs** `python scripts/verify_gate.py` (the full suite, ~3,5 min) and
`python scripts/freeze_rules_evidence.py`.

Acceptance: both exit 0; the suite count is recorded in the verify report; the
evidence gate reports coverage 0.9012 and no drift.

### 8.1 Headless render

Acceptance: `AppTest.from_file('app/dashboard_ds02.py').run()` raises no
exception, reports no error, and shows four tabs.

### 8.2 Frozen artifacts untouched

Acceptance: `git status --porcelain models/ src/ mia/ app/cache/
02_DS02_ensemble_RUL.ipynb` returns nothing after the whole change.

### 8.3 Repository byte-identical outside the change

Acceptance: `git status --porcelain` lists only the files this change owns plus
the `openspec/changes/2026-10-26-ds02-pre-defense-hardening/` directory.
