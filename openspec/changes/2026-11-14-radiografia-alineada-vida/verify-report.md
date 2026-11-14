# Verify report: Life-aligned sensor radiography across test units

**Change:** `2026-11-14-radiografia-alineada-vida`
**Verified:** 2026-11-14
**Mode:** Strict TDD (pytest)

## Gate

Command: `python -m pytest tests -q`

| Run | Passed | Failed |
|---|---|---|
| Baseline before the change | 465 | 3 |
| After the change | 471 | 3 |

Exit code 1 comes from the three **pre-existing** MLflow failures, identical before and
after: `test_mlflow_backfill.py::test_notebooks_instrument_mlflow_live`,
`test_mlflow_live.py::test_all_notebooks_have_mlflow_header_and_log_cell`,
`test_mlflow_live.py::test_no_late_tfenable_onednn_opts`. Delta: +6 passed, the new test
file. No new failures.

Focused: `pytest tests/test_radioografia_alineada.py -q` → 6 passed.
UI surfaces keep passing: `test_dss_ui.py`, `test_app_ux_bundle.py`, `test_mejoras_streamlit.py`,
`test_ui_rules.py`, `test_ui_batch.py`, `test_dss_interaction.py`, `test_hangar.py`,
`test_fleet_registries_session.py` (green inside the full run).

## Visual verification (Playwright, live app on http://127.0.0.1:8501/)

The Motor tab now renders six Plotly charts: the per-cycle pressures and temperature
radiographies, the two new RUL-aligned aggregate views, the RUL trajectory and the gauge.

New charts (bounding boxes, CSS pixels, negative = inside the figure viewport):

| Viewport | Chart | X title | Y title top / bottom | X title bottom | legend gap to plot | legend inside figure |
|---|---|---|---|---|---|---|
| 1280x900 | aligned pressures | RUL real (ciclos) | -24 / -72 | -58 | 65 | yes (-26) |
| 1280x900 | aligned temperatures | RUL real (ciclos) | -24 / -72 | -58 | 65 | yes (-26) |
| 560x900 | aligned pressures | RUL real (ciclos) | -22 / -73 | -61 | 68 | yes (-7) |
| 560x900 | aligned temperatures | RUL real (ciclos) | -24 / -72 | -58 | 65 | yes (-26) |

Other checks: `.modebar` count 0 on every tab and both viewports; zero Streamlit exception
banners; the pre-existing charts keep their verified geometry.

Captions rendered from the same frame:

- Pressures: «Deriva media de las unidades test alineada por RUL real. Ninguno de estos
  canales muestra una deriva sostenida: oscila con las condiciones de vuelo. Método:
  valor del ciclo dividido por la media de los 5 primeros ciclos del propio motor, menos
  1, en %. Fuente: app/cache (ds02_rows y ds02_windows).»
- Temperatures: «... Solo T50 +1.31 ppt muestra una deriva sostenida entre el primer y el
  último tramo de vida; el resto oscila con las condiciones de vuelo. ...»

## Residual defect found and fixed during verification

On the first render the rotated Y title of both new charts extended **16 px above the
SVG top**, because the helper inherited the 44 px top margin while carrying a longer title.
Fixed with the same 72 px top margin used by the per-cycle radiography and a shorter title,
and locked with `assert fig.layout.margin.t >= 72` in the test so it cannot regress.

## Corrected figures (honest deviation)

The proposal quoted T50 **+1.54 ppt** and T48 **+1.28 ppt**. Those came from a
life-fraction alignment measured before the aggregation was fixed. Under the implemented
alignment (real RUL bins of 10 cycles, bins with fewer than five observations excluded)
only T50 clears the declared rule (`abs(corr) >= 0.3` **and** `abs(salto) >= 0.5` ppt):

| Channel | inicio_vida | fin_vida | salto | corr_rul | resaltar |
|---|---|---|---|---|---|
| T50 | 0.416 | 1.725 | **+1.31** | -0.407 | yes |
| T48 | -0.933 | -0.480 | +0.45 | -0.294 | no |
| P40 | -0.797 | -3.006 | -2.38 | -0.010 | no |
| Ps30 | -0.712 | -3.022 | -2.32 | -0.014 | no |
| rest of pressures | — | — | \|salto\| < 1.6 | \|corr\| < 0.05 | no |

So T48 is borderline and is **not** highlighted; the caption is computed from the same
frame and therefore says only T50. Pressure channels show large end-to-end differences
without any monotone relation to RUL, so they are not claimed as degradation. The spec
required the figures to be computed rather than fixed, so this is a correction of the
proposal's example numbers, not of the contract.

## TDD cycle evidence

| Task | Test file | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.1–1.5 | `tests/test_radioografia_alineada.py` | Unit | 465 passed / 3 failed | ✅ 6 written, 6 failed | ✅ 6 passed | ✅ baseline semantics, finding, highlight rule, figure contract, restricted caption | ✅ assertions behavioural |
| 2.1–2.3 | same | Unit | previous green | ➖ covered by 1.1–1.3 | ✅ passed | ✅ empty-frame guard, min-sample bins | ✅ constants hoisted |
| 3.1–3.3 | same | Unit | previous green | ➖ covered by 1.4 | ✅ passed | ✅ critical band present, margin locked | ➖ None needed |
| 4.1–4.3 | suite | Integration | previous green | ➖ covered by existing UI suites | ✅ passed | — | — |
| 5.1 | suite | Integration | — | — | ✅ 471 passed | — | — |
| 5.2 | Playwright | E2E evidence | — | — | ✅ see tables | ✅ two viewports | — |

Total tests written: 6. Passing: 6. Layers: unit 5, integration 1.

## Deviations from design

1. **Highlight rule.** The design declared `abs(corr) >= 0.3` over the aligned frame;
   the implementation adds an effect floor of 0.5 ppt (`abs(corr) >= 0.3 AND
   abs(salto) >= 0.5`) and computes the correlation over all points instead of the binned
   means. Reason: with only eight bins the binned correlation was unstable and flagged a
   rotor-speed channel with no physical claim. Both thresholds are applied uniformly to
   every channel.
2. **Aligned charts need the wide top margin** (72 px), same as the per-cycle
   radiography; not in the original design and caught only by measurement.

## Known limitations

- Only T50 clears the declared rule on this cache. T48 sits just below on both criteria
  and is reported as borderline, not as a second confirmed signal.
- The aligned view averages three engines; a per-engine breakdown is not offered.
- Telemetry covers cycles 1..59 (U11), 1..76 (U14) and 1..67 (U15); the RUL join leaves
  out U14 cycles 1–2 and U15 cycle 1, which have no scored window at that cycle.

## Evidence

- `scratch/sdd-radiografia-alineada/final-1280-motor.png`

## Verdict

**PASS** — gate has no new failures, both new charts render clean at 1280 px and 560 px,
the captions carry figures computed from the drawn data, and the corrected numbers are
documented above.
