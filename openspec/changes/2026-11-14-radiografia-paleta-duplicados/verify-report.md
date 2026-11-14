# Verify report: One palette per channel, duplicate collapse, honest pressure caption

**Change:** `2026-11-14-radiografia-paleta-duplicados`
**Verified:** 2026-11-14
**Mode:** Strict TDD (pytest)

## Gate

Command: `python -m pytest tests -q`

| Run | Passed | Failed |
|---|---|---|
| Baseline before the change | 471 | 3 |
| After the change | 475 | 3 |

Exit code 1 comes from the three **pre-existing** MLflow failures, identical before and
after: `test_mlflow_backfill.py::test_notebooks_instrument_mlflow_live`,
`test_mlflow_live.py::test_all_notebooks_have_mlflow_header_and_log_cell`,
`test_mlflow_live.py::test_no_late_tfenable_onednn_opts`. Delta: +4 passed, the four new
contracts. No new failures.

Focused: `pytest tests/test_radioografia_alineada.py -q` → 10 passed;
`pytest tests/test_ui_chart_chrome.py -q` → 7 passed.

## Visual verification (Playwright, live app on http://127.0.0.1:8501/)

Viewport 1280x900, Motor tab, bounding boxes read from the DOM:

| Chart | Traces | Legend labels | Trace colours |
|---|---|---|---|
| Pressures per cycle | **5** (was 7) | `P15 · P21`, `P2`, `P24`, `Ps30 · P40`, `P50` | green, teal, slate, pink, purple |
| Pressures aligned | **5** | same five | **identical rgb values** |
| Temperatures per cycle | 3 | `T24`, `T2`, `T50` | sky, violet, amber |
| Temperatures aligned | 3 | same three | **identical rgb values** |
| Trajectory | 5 | unchanged | unchanged (no channel identity claimed) |

The duplicated pairs collapsed into one trace each, labelled with both codes. The colour
of every shared channel matches exactly across both views (`rgb(52,211,153)`,
`rgb(45,212,191)`, `rgb(100,116,139)`, `rgb(244,114,182)`, `rgb(192,132,252)` for
pressures; `rgb(56,189,248)`, `rgb(167,139,250)`, `rgb(245,158,11)` for temperatures).

Captions rendered in the browser:

- Pressures: «Deriva media de las unidades test alineada por RUL real. Ninguno de estos
  canales supera el criterio de deriva (|corr con el RUL| >= 0,3 y salto >= 0,5 ppt):
  el mayor cambio entre tramos es de 2.3 ppt y la forma no es monótona. Método: valor del
  ciclo dividido por la media de los 5 primeros ciclos del propio motor, menos 1, en %.
  Fuente: app/cache (ds02_rows y ds02_windows).» — the sentence no longer asserts flight
  conditions, and the figure matches the drawn curve.
- Temperatures: «... Solo T50 +1.31 ppt supera el criterio de deriva ...; el resto queda
  por debajo. ...»

Other checks: `.modebar` count 0 on every tab, zero Streamlit exception banners, and the
geometry verified in the previous change is unchanged (no clipping introduced).

## Residual issue found during verification

The first caption draft read «la forma es una forma no monótona» (duplicated noun). Fixed
to «la forma no es monótona»; the test contract for the wording was left on the measured
claim rather than on the literal phrase.

## TDD cycle evidence

| Task | Test file | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.1–1.5 | `tests/test_radioografia_alineada.py` | Unit | 471 passed / 3 failed | ✅ 4 written, 4 failed | ✅ 10 passed | ✅ collapse order, palette uniqueness, trace count, caption | ✅ assertion on the claim, not on the string |
| 2.1–2.4 | same | Unit | previous green | ➖ covered by 1.1–1.3 | ✅ passed | ✅ both input orders, partial groups | ✅ constants hoisted |
| 3.1–3.3 | same | Unit | previous green | ➖ covered by 1.4 | ✅ passed | ✅ monotone branch vs not | ➖ None needed |
| 4.1 | suite | Integration | — | — | ✅ 475 passed | — | — |
| 4.2 | Playwright | E2E evidence | — | — | ✅ see tables | ✅ colour identity measured numerically | — |

Total tests written: 10. Passing: 10. Layers: unit 9, integration 1.

## Deviations from design

None behavioural. One dead constant (`COLORES_DESTACO`) left over from the earlier
highlight implementation was removed because the fixed palette replaces it.

## Known limitations

- The collapse decision rests on the frozen-cache measurement (correlation 1.000, maximum
  absolute difference 0.25 psia). If the cache were rebuilt with different pairs,
  `CANALES_DUPLICADOS` needs revisiting; the label names both codes so the choice stays
  auditable.
- Colour identity covers the two radiography views; other figures keep their own palettes.

## Evidence

- `scratch/sdd-paleta-duplicados/presiones-ciclo.png`
- `scratch/sdd-paleta-duplicados/presiones-alineado.png`
- `scratch/sdd-paleta-duplicados/temperaturas-alineado.png`

## Verdict

**PASS** — five pressure traces instead of seven with paired labels, identical channel
colours across both views, a caption that reports what is drawn instead of a causal claim,
and no new gate failures.
