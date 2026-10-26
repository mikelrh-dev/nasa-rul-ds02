# Proposal: DS02 pre-defense hardening

**Change:** `2026-10-26-ds02-pre-defense-hardening`
**Status:** Proposed
**Capability:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md) (modification) and
[`ds02-live-evaluation`](../../specs/ds02-live-evaluation/spec.md) (modification)

---

## Why

The DS02 surface is in good shape (211 tests green, frozen bundle, an honest
evidence trail). Four defects found by measurement on 2026-10-26 are not in the
project's own backlog, and all four are things a jury can check live. None of
them touches the model, the notebook, the conformal calibration or a single
decision rule.

1. **The container image cannot serve the dashboard.** `Dockerfile` copies
   `src/`, `app/`, `scripts/` and four files under `models/`. It does not copy
   `mia/`. `app/ui_rules.py:33` does `import motor as M` with `mia/` on
   `sys.path` (line 31), and `app/dashboard_ds02.py:42` imports `ui_rules` at
   module level. Reproduced by copying exactly the tree the Dockerfile produces
   (no `mia/`) and importing the dashboard:

   ```
   ModuleNotFoundError: No module named 'motor'
     File ".../app/ui_rules.py", line 33, in <module>
       import motor as M
   ```

   With `mia/` copied, the same tree imports cleanly. `docker-compose.yml`
   already points at `app/dashboard_ds02.py`, so the regression is complete:
   `docker compose up --build` builds an image whose dashboard container dies on
   start. The API service is unaffected (it does not import `mia/`).

2. **The twin panel cites a window that did not decide.** `app/twin.py:137`
   writes `"window": int(len(frame) - 1)` — the position of the last row of the
   saved series, not the position of the worst window of the last cycle, which
   is what `vista_resultado` itself selects on line 133. The panel cites it as
   "the window that decided" (`app/dashboard_ds02.py:1841-1842`). Measured on a
   real alta from the cache:

   ```
   U11 ciclo 22: 1219 rows in the series, 44 windows in the last cycle
     vista_resultado says  window = 1218
     the window that decides is at position 1177
   U14 ciclo 29: reports 285, the real position is 285 (coincides)
   ```

   The number is right for some engines and wrong for others, and nothing on
   screen says which. `start_row // step` reproduces the real position exactly
   (2354 // 2 = 1177), so the correct value is available without changing the
   twin's data model.

3. **`validate_table` accepts `±inf`.** `app/ui_inference.py:318-340` validates
   with `pd.to_numeric(errors="coerce")` followed by `coerced.isna()`. `isna()`
   does not catch infinities. Verified:

   ```
   validate_table ACEPTA +inf
   validate_table ACEPTA -inf
   ```

   From there the value reaches the scaler, the residualizer, the network and
   the causal EMA (a recurrence: an `inf` contaminates every later window of the
   unit), and the UI paints it as a finite number. The 2026-10-23 audit already
   recorded this hole (section 3.3) and it was never closed.

4. **The artifact hash is recorded but never verified.** `app/cache/cache_manifest.json:35`
   stores `ensemble_sha256`. Nothing compares it: it is read and displayed in
   four places (`app/dashboard_ds02.py:596, 737, 994, 2540`) and the command to
   verify it by hand is printed. If the bundle is retrained and
   `models/ensemble.joblib` replaced without rebuilding `app/cache/`, the surface
   shows stale predictions under a new seal. This is the one remaining silent
   substitution path in a project that removed the same failure for the dataset
   (`src/ds02_rul/data.py`) and for saving (`persistence.assert_ds02_artifact`).

A fifth, documentary defect: `docs/defensa_ds02_explicacion_logica_negocio.md:20`
and `:107` say the window is "remuestreada cada 2 filas". The dataset stride is
100 and 50 rows cover **0,44 flight cycles**, as `README.md` itself states in
its final limitation. The 2 is the cache `step` (`app/dashboard_ds02.py:567`) —
how many windows overlap — not the sampling distance. The README and the
defense document contradict each other on the number a jury is most likely to
multiply out loud.

## Scope

**In scope**

1. `Dockerfile`: ship `mia/` in the image.
2. `docs/defensa_ds02_explicacion_logica_negocio.md` and `README.md`: the stride
   wording, the legacy `dashboard.py` entrypoint and the "fifth tab" claim.
3. `app/dashboard_ds02.py.bak_pestanas`: stop tracking a 147 KB stale copy.
4. `app/twin.py`: `vista_resultado` reports the window that decided.
5. `app/ui_inference.py`: reject non-finite values.
6. `app/ui_data_loader.py` + `app/dashboard_ds02.py`: verify the cache artifact
   hash against the bundle on disk, and warn only when they differ.

**Out of scope**

- `models/`, `src/ds02_rul/`, `mia/` logic, `app/cache/` and
  `02_DS02_ensemble_RUL.ipynb` are read-only inputs. No retraining, no refit, no
  new weight, no change to the conformal calibration and no change to a single
  rule in `mia/`.
- The Ridge-residual radiography panel. Its gate is passed and its cost is
  measured (`docs/plans/plan-accion-gemelo-hangar-2026-10-24.md`, Phase 3), and
  the plan already postponed it past the defense because it adds a new signal to
  explain live.
- `app/api.py`, `mia/` packaging, SQLite persistence, dashboard restructure,
  moving the PDF generator out of `app/dashboard_ds02.py`. Real debt, none of it
  demo-blocking.
- Voice, Telegram, jittering, blocking held units — already rejected in Phase 5
  of `docs/plans/plan-prioridad-y-riesgo-2026-10-24.md`.

## Capability

The change modifies `ds02-dss-ui` (deployment, twin-window reporting, cache
provenance) and `ds02-live-evaluation` (validation of a user-supplied table). It
does not add a capability and does not touch `rul-prediction-ds02`.

## What changes

### Phase 1 — Deployment (`Dockerfile`)

- One line: `COPY mia/ ./mia/`. Nothing else.

### Phase 2 — Documentary coherence

- The defense document states the stride (`100`) and the window span
  (`~0,44 cycles`), not the cache `step`.
- `README.md` stops offering `app/dashboard.py` (the legacy board, which fails to
  render today — `ValueError: cannot reindex on an axis with duplicate labels`
  at `app/dashboard.py:100`, verified against the HDF5) and stops describing a
  "fifth tab" (the surface has four: Flota, Motor, Casos nuevos, Auditoría).
- `app/dashboard_ds02.py.bak_pestanas` leaves the repository.

### Phase 3 — The window that decided (`app/twin.py`, tests)

- `vista_resultado` returns the position of the deciding window within the saved
  series (`peor.name`), not `len(frame) - 1`.
- The label at the point of use states what the number is.
- The test that pins the old number is updated in the same commit.

### Phase 4 — Data robustness and provenance (`app/ui_inference.py`,
`app/ui_data_loader.py`, `app/dashboard_ds02.py`, tests)

- `validate_table` rejects non-finite values, naming the column and the row.
- A pure helper compares `provenance["artifact"]["ensemble_sha256"]` with the
  SHA-256 of `models/ensemble.joblib` on disk.
- The surface warns **only when the two differ**, so the green path renders
  byte-identically and no widget count moves.

## Artifacts that stay byte-compatible

- `models/` (ensemble, scaler, bundle, manifest, conformal calibration) — read
  only; the hash check reads, never writes.
- `app/cache/` (Parquet + manifest) — read only.
- `src/ds02_rul/`, `mia/` — `mia/` is copied into the image, never edited.
- `app/registros_flota.json` — unchanged; the fixture in `tests/conftest.py`
  keeps isolating tests.
- The persisted registry format — unchanged.

## Rollback plan

Each phase is one commit with its verification in the message. Phase 1 is a
Dockerfile line: reverting it restores the current (broken-in-Docker, working
locally) state. Phase 2 is documentation plus `git rm --cached` on a file
nothing imports. Phase 3 is one expression in `app/twin.py` plus its test;
reverting restores the old number, which is wrong but harmless. Phase 4's
validator tightening is additive (it rejects a class of input that today
produces a contaminated series); the hash check warns only on mismatch, so
reverting it changes nothing observable while the cache matches.

## Risks

1. Phase 4 makes the validator stricter. A user table containing `inf` is
   rejected instead of scored. That is the intent, but it is the only place this
   change narrows accepted input, and the message must name the column and row
   like every other rejection in that function.
2. Phase 4's hash check must not raise. A missing artifact file, a truncated
   manifest or a builder that wrote a relative path with backslashes must all
   degrade to "not checked", never to a crash at render.
3. Phase 3 changes a number the work order carries
   (`ventana_evaluada.indice`). The export stays JSON-serializable and the
   contract keeps the same keys; only the value becomes correct.
4. `tests/conftest.py` empties `app/registros_flota.json` before every test, so
   any new registry-dependent behaviour fires in every test. Phase 4 adds no
   registry behaviour.
5. Phase 2 deletes a tracked file. It is a backup nobody imports (`grep -rn
   "bak_pestanas"` returns no import), but the deletion is a repository change
   and must be its own commit so it can be reverted alone.

## Open questions for the spec/design phase

1. Should the hash check be a sidebar warning or a line inside the existing
   provenance expander? This proposal assumes the sidebar, because the hash is
   already shown there and a mismatch is an operator-facing fact, not an audit
   detail.
2. Should `±inf` be rejected by `validate_table` (strict, names the row) or
   reported by `preflight` as a plausibility warning (non-blocking, like the
   out-of-domain note)? This proposal assumes rejection, because an `inf` is not
   a value the model can consume honestly and the existing validator already
   rejects NaN in the same loop.
3. Does the deployed `ds02-dss-ui` "Verification" requirement need its tab count
   corrected in the same change? It currently says "the five tabs are present"
   while the surface has four. It is not one of the four defects, but it is a
   stale claim in a spec this change modifies.
