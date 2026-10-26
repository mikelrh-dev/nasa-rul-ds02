# Spec delta: DS02 pre-defense hardening — `ds02-dss-ui`

**Change:** `2026-10-26-ds02-pre-defense-hardening`
**Status:** Proposed
**Capability:** `ds02-dss-ui` (modification)

---

## ADDED

### Requirement: Shipped image carries the rules layer

The container image built from `Dockerfile` SHALL include the `mia/` rules layer
alongside `src/`, `app/`, `scripts/` and the frozen artifacts. The dashboard
entrypoint depends on `mia/` at import time (`app/ui_rules.py` imports `motor`
and `reglas`), so an image without it SHALL NOT be considered buildable even
though the build itself succeeds.

The image SHALL NOT be considered verified by a successful build alone: the
dashboard entrypoint SHALL import without raising in the built tree.

#### Scenario: The image without the rules layer fails at import, not at build

- GIVEN the Dockerfile copies `src/`, `app/`, `scripts/` and four files under
  `models/` but not `mia/`
- WHEN the built tree is imported as the dashboard entrypoint
- THEN `mia/` is absent and `app/ui_rules.py` cannot import `motor`
- AND the failure happens at import time, which is why the build itself is not
  sufficient evidence

#### Scenario: The image with the rules layer serves the dashboard

- GIVEN `Dockerfile` copies `mia/ ./mia/`
- WHEN the built tree is imported as the dashboard entrypoint
- THEN no `ModuleNotFoundError` is raised
- AND the four tabs render from `app/cache/` without loading TensorFlow

### Requirement: The window that decided is identified

`vista_resultado` SHALL report the position, within the saved series, of the
window that decided the state — the window with the lowest conformal lower bound
in the last scored cycle. It SHALL NOT report the position of the last row of
the series, which is a different window whenever the last cycle holds more than
one.

The reported number SHALL be the position in the series the twin stores, so the
same value is meaningful for every origin: a cache-derived alta, a live
evaluation and a registered twin.

The point of use SHALL state what the number is, so a reader can tell a position
in the saved series from a window index in the dataset.

#### Scenario: The deciding window is the one reported

- GIVEN a twin built from cached windows at `step=2`, whose last cycle holds 44
  windows
- WHEN `vista_resultado` is called
- THEN the reported window is the position of the window with the lowest lower
  bound in that cycle
- AND it is not the position of the last row

#### Scenario: The number is stable across origins

- GIVEN a live-evaluation twin scored at `step=1`
- WHEN `vista_resultado` is called
- THEN the reported window equals the position of the deciding window
- AND the value is unchanged from the behaviour at `step=1`

#### Scenario: The work order carries the corrected window

- GIVEN a twin whose deciding window is not the last row
- WHEN the work order is generated
- THEN `ventana_evaluada.indice` names the deciding window
- AND the document remains JSON-serializable with the same keys

### Requirement: Cache provenance is checked against the artifact

The surface SHALL compare the artifact hash recorded in the cache provenance
(`app/cache/cache_manifest.json`, `artifact.ensemble_sha256`) with the SHA-256 of
`models/ensemble.joblib` on disk, and SHALL warn when they differ.

The check SHALL be non-fatal. A missing artifact, a truncated manifest, an
unreadable file or a hash recorded with a different path separator SHALL degrade
to "not checked", never to an exception at render.

The warning SHALL appear only when the two differ. When the cache and the
artifact agree, the surface SHALL render exactly as before, so no widget count
moves and no existing test changes for the green path.

#### Scenario: A matching cache stays quiet

- GIVEN `models/ensemble.joblib` whose SHA-256 equals the recorded hash
- WHEN the surface renders
- THEN no provenance warning appears
- AND the rendered widget tree is unchanged

#### Scenario: A stale cache is named

- GIVEN `models/ensemble.joblib` replaced without rebuilding `app/cache/`
- WHEN the surface renders
- THEN a warning appears naming the artifact hash recorded and the hash read
- AND the surface still renders every figure from the cache

#### Scenario: An unreadable artifact does not crash the surface

- GIVEN `models/ensemble.joblib` absent or the manifest unreadable
- WHEN the surface renders
- THEN the check reports "not checked"
- AND no exception is raised

## MODIFIED

### Requirement: Verification (deployed)

The change SHALL keep the existing artifact-contract suite green and SHALL add
tests for the triage thresholds, the cache contract, the work-order contract and
the dataset-isolation guard. The application SHALL render without an exception in
a headless run.

The deployed scenario named **five** tabs; the surface has **four** (Flota,
Motor, Casos nuevos, Auditoría). The count SHALL be corrected to four in the same
change that records the tests this change adds, so the spec does not keep a
number the code contradicts.

#### Scenario: The suite passes

- GIVEN the repository virtualenv
- WHEN `pytest tests -q` runs
- THEN the pre-existing contract tests still pass
- AND the new tests for the image contents, the deciding window and the cache
  hash pass

#### Scenario: The app renders headless

- GIVEN the cache and no browser
- WHEN the Streamlit app is executed by the test harness
- THEN no exception is raised
- AND the four tabs are present

#### Scenario: The app renders in a real browser

- GIVEN the server running and a headless browser pointed at it
- WHEN the page finishes loading
- THEN the title, the tab labels and the fleet timeline are present in the DOM
- AND the configured background color is applied

## REMOVED

None.

## Related capabilities

[`ds02-live-evaluation`](../ds02-live-evaluation/spec.md) inherits this surface's
theme, `alt=` and read-only rules and modifies its own validation requirement in
this change. The phrase "the fifth tab" in the deployed prose is superseded: the
live evaluation is the **Casos nuevos** tab, and the surface has four tabs.
