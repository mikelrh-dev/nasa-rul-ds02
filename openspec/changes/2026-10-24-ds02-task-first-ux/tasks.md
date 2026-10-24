# Tasks: DS02 task-first UX (Streamlit)

**Change:** `2026-10-24-ds02-task-first-ux`
**Status:** Proposed

Each task closes with its acceptance check. `tdd: true` per
`openspec/config.yaml`; the RED test is written before the implementation in
every task that adds logic. Commands assume the repository root.

---

## Phase 0 — One identity per engine

### 1. Registry module `app/flota.py`

**Creates** `app/flota.py`. Pure, no Streamlit import.

Contract: `etiqueta(clave, registro=None) -> str`,
`clave_de(unidad_float, registro=None) -> str`,
`unidad_de(clave, registro=None) -> float`,
`normalizar_matricula(texto) -> str`, `registrar_alta(registro, matricula,
unidad_cache, ciclo) -> registro`, `quitar_alta(registro, matricula) -> registro`,
`serializar(registro) -> str`, `cargar(ruta) -> dict`.

Rules: cache keys delegate to `L.UNIT_LABELS`; `clave_de` degrades to
`f"U{int(u)}"`; `normalizar_matricula` reuses `T.normalizar_id`; the id counter
is `max(existing) + 1` with prefix `-1000`; `registrar_alta` calls
`ventanas_de_alta` and `T.make_twin` and does not call the model.

**Creates** `tests/test_flota.py` with four cases: one key and one label per
engine; `clave_de`/`unidad_de` are inverses; an alta takes its matricula as key;
the counter never reuses an id after a removal.

Acceptance: `python -m pytest tests/test_flota.py -q` — 4 passed.

### 2. Persist the alta

**Modifies** `app/dashboard_ds02.py`: `_cargar_registros` and `_guardar_registros`
include `altas` in the same JSON; `ALTA_KEY` becomes a session cache fed from the
registry.

Acceptance: create an alta, reload the page, the engine is still in the fleet
register and in the hangar.

### 3. Alta with free unit and cycle (missing test)

**Modifies** `tests/test_ui_alta.py`. RED first: an alta built from a free
unit+cycle enters the fleet and creates a twin.

Acceptance: `python -m pytest tests/test_ui_alta.py -q` — the five assertions
that depend on `unidad_alta(n)` now take the id from `flota.registrar_alta`, and
the new test passes.

### 4. Cycle without scored windows (missing test)

**Creates** a test in `tests/test_ui_alta.py`: a unit+cycle combination with no
scored windows raises `ValueError` with the unit and its first scored cycle in
the message.

Acceptance: `python -m pytest tests/test_ui_alta.py -q` — the rejection test
passes and the message names the first scored cycle.

### 5. CSV template is the validator's contract (missing test)

**Creates** a test in `tests/test_live_eval.py`: the downloaded template parses
through `INF.validate_table` once filled, and carries no `unit` column.

**Modifies** `app/dashboard_ds02.py`: the new template button reuses
`INF.template_csv()`; the duplicate button is removed.

Acceptance: `python -m pytest tests/test_live_eval.py -q` and only one
"plantilla CSV" download button remains in the rendered app.

---

## Phase 1 — Turn-advance simulator

### 1.1 Simulator module `app/simulacion.py`

**Creates** `app/simulacion.py`. Pure, no Streamlit import.

Contract: `avanzar(frame, retenidos, n) -> frame`,
`retenidos_por_umbral(frame, umbrales) -> set`,
`ciclos_hasta_fallo(frame, umbrales) -> dict`,
`reiniciar_vida(registro, clave) -> registro`.

Rules: reads `pred`/`lower`/`upper` from the cache; never calls the model; the
held set is derived from the AOG threshold; the reset returns to the first
scored cycle and records it as a replay.

**Creates** `tests/test_simulacion.py`: advancing does not change the engine set;
a held engine does not advance while others do; `ciclos_hasta_fallo` matches the
cache; the reset returns to the first scored cycle and is labelled a replay.

Acceptance: `python -m pytest tests/test_simulacion.py -q` — 4 passed.

### 1.2 Reset transition in `app/hangar.py`

**Modifies** `app/hangar.py`: a reset transition that returns the record to
service and records the event with the replay label.

Acceptance: `python -m pytest tests/test_hangar.py -q` — the transition is
legal from the workshop states and the event is recorded.

---

## Phase 2 — Landing, seed and script

### 2.1 Landing card

**Modifies** `app/dashboard_ds02.py`: the first tab opens with a card stating the
decision rule (`L_inf` governs; the point estimate is the conservative quantile
`alpha = 0.35`), the fleet state and one primary action.

Acceptance: `AppTest` shows the card with "RUL p35" in the source of the
decision metric.

### 2.2 Demo seed (session only)

**Modifies** `app/dashboard_ds02.py`: on first load with an empty registry and no
`_semilla_demo`, select one cached engine. Session state only.

Acceptance: the seed does not create `app/registros_flota.json`; the seven files
in scope for widget counts are listed with the exact assertions changed.

### 2.3 Guided script with release

**Modifies** `app/dashboard_ds02.py`: a "next step" control advances four steps
from `estado_historia` and then releases control.

Acceptance: `python -m pytest tests/test_ui_alta.py -q` — the four steps still
derive from the cache and the fifth press releases control.

### 2.4 Entrypoint fix and toast fix

**Modifies** `docker-compose.yml`: the dashboard service runs
`app/dashboard_ds02.py`.

**Modifies** `app/dashboard_ds02.py`: the alta toast names the real registry key.

Acceptance: `docker-compose.yml` no longer names `app/dashboard.py`, and the
toast names the key the hangar will use.

---

## Phase 3 — Task-first information architecture

### 3.1 Three tabs

**Modifies** `app/dashboard_ds02.py`: Flota, Motor, Evidencia. The five
internal-layer tabs fold into them.

**Modifies** `tests/test_dss_ui.py:252-256`, `tests/test_ui_rules.py:109,197`,
`tests/test_dss_interaction.py:211`.

Acceptance: `AppTest` reports exactly three tabs whose labels contain "Flota",
"Motor" and "Evidencia"; the seven structural guards stay green.

### 3.2 Remove the manual key fallback

**Modifies** `app/dashboard_ds02.py`: the line
`registros.get(etiqueta) or registros.get(f"U{int(unit)}")` becomes
`registros.get(motor.clave_de(unit))`.

Acceptance: `grep -n "registros.get(" app/dashboard_ds02.py` shows exactly one
lookup, keyed by the registry key.

### 3.3 Work orders move to Motor

**Modifies** `app/dashboard_ds02.py`: the work-order download lives next to the
engine card.

Acceptance: the export still carries only AOG units with the artifact hash, the
thresholds, the cycle and the lower bound.

### 3.4 Fleet register with the queue as a filter

**Modifies** `app/dashboard_ds02.py`: the hangar lists every engine with its
lifecycle state; the derivation queue is a filter on top.

Acceptance: `python -m pytest tests/test_engine_flow.py -q` — every engine
appears and the queue filter shows only AOG candidates.

---

## Phase 4 — Noise

### 4.1 Metric relocation

**Modifies** `app/dashboard_ds02.py`, `app/ui_data_loader.py`: model-quality
metrics move to Evidencia; one KPI per concept on the decision screen; the
duplicate literal "Unidades en hangar" appears once; the point estimate is
labelled "RUL p35 (conservative)" with a `help=`.

Acceptance: `grep -c "Unidades en hangar" app/dashboard_ds02.py` returns 1; no
quality metric label appears in the decision screen's source region.

### 4.2 SHA provenance

**Modifies** `app/dashboard_ds02.py`: both SHAs move to a "Provenance and
contract" expander; the window fingerprint is no longer called "Huella" in the
twin table.

Acceptance: the twin table has no "Huella" column and the expander names the
ensemble hash and the window fingerprint.

### 4.3 Flight Profile

**Modifies** `app/dashboard_ds02.py`: an `alt` vs `Mach` chart in Evidencia, with
`alt=`.

Acceptance: `AppTest` finds the new chart with a non-empty `alt`, and no
latitude or longitude channel is referenced.

---

## Phase 5 — Verification

### 5.1 Suite and guards

Acceptance: `python -m pytest tests -q` — green, with the list of tests added
and updated in this change.

### 5.2 Headless render

Acceptance: `AppTest.from_file('app/dashboard_ds02.py').run()` raises no
exception, reports no error, and shows three tabs.

### 5.3 Jury walkthrough

Acceptance: open, click a card, alta an engine, reload, advance the fleet, press
the script — the six steps work without reading documentation, and the engine
alta survives the reload.

### 5.4 Guards untouched

Acceptance: the seven structural guards pass unmodified:
`test_airworthy_state_is_reachable_on_this_band`,
`test_metrics_are_recomputed_from_the_cache`,
`test_reading_the_ui_leaves_the_frozen_artifacts_untouched`,
`test_app_renders_headless_without_exception`,
`test_every_chart_and_grid_has_an_accessible_name`,
`test_no_css_is_injected_into_the_app`,
`test_the_cycle_slider_drives_the_grounded_kpi`.
