# Proposal: DS02 task-first UX (Streamlit)

**Change:** `2026-10-24-ds02-task-first-ux`
**Status:** Proposed
**Capability:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md)

---

## Why

The DS02 surface (`app/dashboard_ds02.py`, 2 865 lines, 5 tabs, 31 `st.metric`,
79 `st.caption`, 12 charts) is organised by **layers of the model**, not by the
tasks a person performs. A new visitor sees "Hangar virtual", "Telemetría RUL",
"Radiografía física", "Auditoría" and "Evaluar unidad nueva" and has to
reconstruct for themselves that all five describe the same engine. The first
screen answers no question; the user has to decide where to click before they
know what the app decides.

Measured against the repository as it is today (2026-10-24, commit `db978c3`):

1. **Identity breaks.** Four views use four different keys for the same engine.
   Measured with three altas (IBERIA-350, AIRBUS-A320, BOEING-737):

   ```
   snapshot unit= -1002 -> clave_hangar=U-1002     matricula_ui=BOEING-737
   snapshot unit= -1001 -> clave_hangar=U-1001     matricula_ui=AIRBUS-A320
   snapshot unit= -1000 -> clave_hangar=U-1000     matricula_ui=IBERIA-350
   ```

   The wall names the aircraft; the hangar key is `U-1000`. The toast at
   `app/dashboard_ds02.py:410` promises the matricula in "Cola y Cronología" and
   it is not there. Four separate faults: the matricula never reaches the
   hangar, the altas are not persisted (`ALTA_KEY = "flota_alta"` lives only in
   `session_state`, `app/dashboard_ds02.py:76`), the alta ids collide
   (`ui_alta.unidad_alta(len(altas))`, so removing and re-adding reuses an id),
   and the alta creates no twin.

2. **The engine looks static.** The cache holds scored values per cycle
   (U11: 59 cycles, U14: 74, U15: 66) but nothing advances through them. The
   only clock is a slider. There is no "what happens if I keep flying" loop.

3. **Jargon without translation.** The decision metric is labelled "RUL
   predicha" with no indication that it is a conservative quantile
   (`alpha = 0.35`, ADR-003) and that the governing quantity is the conformal
   lower bound `L_inf`. Quality metrics (MAE, Macro-RMSE, coverage) sit on the
   decision screen next to the triage KPIs. Two SHA values are shown as if they
   named the engine; measured, the same engine in two windows gives two SHAs
   and two engines with identical data give the same SHA — it is a window
   fingerprint, not an identity.

The goal is a surface a jury understands in under 10 seconds and an operator can
use daily, without changing inference, the frozen model, or the cached data.

## Scope

**In scope**

1. A single engine registry, `app/flota.py` (pure, no Streamlit), persisted in
   `app/registros_flota.json` alongside `twins` and `hangar`. Hard prerequisite
   for every navigation-by-engine feature.
2. A turn-advance simulator, `app/simulacion.py` (pure, no Streamlit), that
   advances the shared fleet clock and gates engines by state, reading the
   cache and never calling the model.
3. A landing screen inside the first tab that answers three questions: what the
   system decides, which engines are at risk today, and what to do next.
4. A task-first information architecture of three tabs — **Flota**, **Motor**,
   **Evidencia** — replacing the current five internal-layer tabs, with
   progressive disclosure inside each.
5. A demo seed (session only, not written to disk) plus a four-step guided
   script that releases control, so the app opens with an engine already loaded.
6. Renaming and relocating metrics so the decision screen carries one KPI per
   concept and the audit screen carries quality and provenance.

**Out of scope**

- `models/`, `src/ds02_rul/`, `mia/`, `app/cache/` and `app/dashboard.py` are
  not touched. The frozen ensemble, scaler, bundle and conformal calibration are
  read-only inputs.
- No new dependencies, no CSS (`unsafe_allow_html` / `<style>`), no second
  validator, no synthetic sensor perturbation (R5 rejected).
- The SHA is not used as an engine name; it is demoted to a provenance datum.
- **No geographic map.** Measured: the dataset's 18 channels are `alt, Mach,
  TRA, T2` plus fourteen sensors. There is no latitude, longitude or position
  channel. A map would have to invent routes, which breaks the honest-protocol
  premise. The honest alternative is a Flight Profile (`alt` vs `Mach`), both
  real channels.
- No "demo mode" switch: demo and operation share one surface.

## Capability

The change modifies the deployed capability `ds02-dss-ui`. It does not add a new
capability and does not change `rul-prediction-ds02` or `ds02-live-evaluation`.

## What changes

### Phase 0 — one identity per engine (`app/flota.py`, `app/ui_alta.py`,
`app/twin.py`, `app/dashboard_ds02.py`, tests)

- New pure module with `etiqueta`, `clave_de`, `unidad_de`,
  `normalizar_matricula`, `registrar_alta`, `quitar_alta`, `serializar`,
  `cargar`. Cache engines keep their `U11`/`U14`/`U15` keys derived from
  `L.UNIT_LABELS`; an alta takes its normalised matricula as its key; a twin
  takes its `engine_id`.
- `clave_de` degrades to `f"U{int(u)}"` for floats not in the registry, so the
  cache keeps working without explicit entries.
- `_cargar_registros` / `_guardar_registros` include `altas` in the same JSON;
  `ALTA_KEY` becomes a session cache fed from the registry.
- Alta ids stop depending on `len(altas)`: the counter lives in the persisted
  registry and only grows (`max(existing ids) + 1`, prefix `-1000`).
- Alta creates the twin from cached windows (`ventanas_de_alta` +
  `T.make_twin`), so a high engine appears in "Gemelos registrados" with a
  saved series.

### Phase 1 — the simulator (`app/simulacion.py`, `app/hangar.py`, tests)

- New pure module, **no Streamlit**: `avanzar`, `retenidos_por_umbral`,
  `ciclos_hasta_fallo`, `reiniciar_vida`.
- The shared fleet clock (`app/dashboard_ds02.py:942`) advances; each engine
  carries a *held* mark, not its own clock. An engine that crosses the
  threshold stops advancing with the rest.
- Source of truth is the cache: `pred`, `lower` and `upper` are already scored
  per cycle. **Zero model calls.** Re-scoring a single window does not
  reproduce the cache — measured 0,6692 against 0,8654 on U14 at cycle 76 —
  because the point estimate is EMA-smoothed causally (`ensemble.py:158`) and the
  cache is built at `step=2` while live scoring uses `step=1`.
- `hangar.py` gains a reset transition. No parallel `estado_operativo`: the
  existing five-state machine already covers the lifecycle.
- The reset is framed as **replaying the recorded life**, not as a repair: the
  cache holds the same degradation data, so a "repaired" engine that fails at
  the same cycle would be a replay and the jury would see it.

### Phase 2 — landing and entry (`app/dashboard_ds02.py`)

- The first tab opens with a single card that states the decision rule
  (`L_inf` governs; the point estimate is the conservative quantile
  `alpha = 0.35`), shows fleet state and offers one start action.
- Demo seed: on first load with an empty registry and no `_semilla_demo` in the
  session, load one cached engine and leave it selected. Session state only;
  `tests/conftest.py` keeps isolating tests.
- Guided script: a "next step" button advances four steps and then releases
  control (reuses `estado_historia`).
- `docker-compose.yml` is pointed at `app/dashboard_ds02.py`. Verified: the
  legacy `app/dashboard.py` fails to render today — `ValueError: cannot reindex
  on an axis with duplicate labels` at `app/dashboard.py:100` — and the compose
  service starts exactly that entrypoint.
- The lying toast is corrected to name the real key under which the engine will
  appear.

### Phase 3 — task-first information architecture

- Three tabs: **Flota**, **Motor**, **Evidencia**.
- **Flota** (landing + wall + queue + lifecycle + policy workshop + script).
  The hangar becomes a fleet register: every engine with its lifecycle state,
  with the derivation queue as a filter on top. The manual fallback
  `registros.get(etiqueta) or registros.get(f"U{int(unit)}")` is removed.
- **Motor** (the complete engine card, reachable by clicking a wall card):
  gauge, trajectory with conformal band, decision with rule trace, sensor
  radiography, lifecycle record, saved twin series, comparator. Works for all
  three origins: cache, alta, registered twin.
- **Evidencia** (sensors, audit, batch/live evaluation, stress sandbox,
  Flight Profile, provenance and the frozen contract), all behind progressive
  disclosure. Metrics are normalised to one name per concept declared once;
  model-quality metrics move to Evidencia; duplicate literals ("Unidades en
  hangar") are removed; the point estimate is labelled "RUL p35 (conservative)"
  with a one-line `help=`; the two SHAs live in a "Provenance and contract"
  expander.

## Artifacts that stay byte-compatible

- `models/` (ensemble, scaler, bundle, conformal calibration) — read only.
- `app/cache/` (Parquet + manifest) — read only; cache and live inference share
  `raw_windows` + `ensemble.predict_interval`.
- `src/ds02_rul/`, `mia/` — unchanged.
- The persisted registry format gains an `altas` key but remains a single JSON
  file next to `twins` and `hangar`.
- `app/dashboard.py` — untouched (and broken today; out of scope).

## Rollback plan

Each phase is one commit with its verification in the message. If a phase fails
its gate, the previous commit remains deployable: the registry change (Phase 0)
is additive (old code ignores the new `altas` key), the simulator (Phase 1) is a
new pure module the dashboard only reads, the landing (Phase 2) is a purely
presentational addition, and the IA change (Phase 3) is confined to
`app/dashboard_ds02.py`. Reverting Phase 3 restores the five tabs; the registry
and landing remain valid because they were designed against the new identity
layer and degrade gracefully to the old keys via `clave_de`.

## Risks

1. Phase 3 is the highest-risk phase for the suite: widget counts and the
   "El taller" label assertion move. The counts are updated in the same commit
   with an explicit list, never silently.
2. Phase 0 writes to disk for the first time in the alta flow; `conftest.py`
   already removes `app/registros_flota.json` before and after each test, so
   isolation is unchanged.
3. The demo seed can break widget counts in Phase 2. The mechanism is broader
   than one file: `tests/conftest.py:24` deletes `app/registros_flota.json`
   before **every** test, so the registry is empty in every test and the seed
   fires in every test. Seven files read the widget tree and are in scope
   (`test_audit_fixes.py`, `test_dss_interaction.py`, `test_dss_ui.py`,
   `test_engine_flow.py`, `test_live_eval.py`, `test_ui_rules.py`,
   `test_ux_round3.py`). Seeding the same engine the sidebar already defaults to
   (`_vistas[0]`, `app/dashboard_ds02.py:364`) is a no-op; seeding another
   engine moves value assertions. If a count cannot be updated honestly, the
   seed is reverted and replaced by a "try an example engine" button on the wall.
4. `step=2` (cache) versus `step=1` (live) density difference is documented, not
   reconciled; a 1e-5 equality claim requires scoring with `step=2` and prior
   history for the EMA.
5. The alta with free unit+cycle, the cycle-without-windows rejection and the
   CSV template have **no test today**. They are written in Phase 0.

## Open questions for the spec/design phase

1. Should the guided script restore the initial state when it finishes, or leave
   the thresholds as the presenter set them?
2. Is the engine card read-only, or may the jury annotate a note on the twin?
3. Does the new "Motor" tab replace the RUL tab or coexist? This proposal
   assumes coexistence (lower risk for the tab guard); replacement changes
   Phase 3 scope.
