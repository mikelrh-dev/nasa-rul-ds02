# Design: formalize the DS02 rules layer

**Change:** `2026-10-21-ds02-rules-layer` · **Status:** Proposed (design) · **Store:** openspec
**Specs:** [rules engine](specs/ds02-rules-engine/spec.md) · [DSS toggle](specs/ds02-dss-ui/spec.md)
**Delivery:** ask-on-risk · **Review budget:** 400 authored lines

## Technical approach

Document, prove, record — kept literal. The layer works, so this change adds **one executable
file**, `scripts/freeze_rules_evidence.py`, and otherwise only text. It is the arbiter for
RULES-06: rebuild the OOF instrument from `_p1_oof_cache.npz`, apply the shipped correction,
re-fit the frozen calibration, compare every recomputable figure against
`mia/calibracion_banda.json` and `INFORME_reglas_oof.md` §13, and print the monotonicity table
that §13 states in prose — so the report becomes regenerable instead of quotable. Nothing under
`models/`, `src/` or `app/cache/` moves; `mia/` changes by one docstring line; the toggle stays
off (RULES-07). New files follow their directory's language: English in `scripts/`, Spanish in
`mia/` and `tests/`.

## Architecture decisions

### Decision: the generator is a first-class repository CLI

**Choice.** argparse, `main() -> int`, `raise SystemExit(main())`, module-level constants — the
shape of `scripts/build_ui_cache.py`. **Rejected:** keeping the out-of-repo scratch script that
produced §13. **Why:** that script makes the evidence unfalsifiable on a fresh clone, and RULES-06
names a repository CLI as the check. Import safety also lets the no-TF test import the module
without running it, as `tests/test_live_eval.py:36` does.

### Decision: verification is the default; writing is explicit and has one target

**Choice.** `--check` is the default and mutually exclusive with `--write`; passing neither flag
is equivalent to `--check`. `--write` re-freezes `mia/calibracion_banda.json` **only**, from a
module constant, and only for fields outside tolerance. **Rejected:** `--write` as default (a
verification command that mutates a frozen artifact is a trap); an `--out PATH` (a stray argument
becomes an arbitrary-file write). **Why:** spelling `--check` states intent, and a later default
flip cannot silently turn verification into a write. `--write` is a no-op within tolerance.

### Decision: compare at the committed precision, not at the manifest's `5e-3`

**Choice.** Half-unit-in-the-last-place (HULP) of each figure *as committed*, from the decimals
in the committed literal, plus `1e-9` for accumulation; integers exact. **Rejected:** `5e-3`, the
tolerance the DSS tests use for manifest metrics. **Why:** `5e-3` is for a live re-run of a
**non-deterministic BiLSTM** — the README reports ±0.05 RMSE between runs and §1.3 measures
`p_lstm` differences of 19.58–26.26. The gate touches none of that: cached OOF predictions plus
seeded, deterministic steps. The only admissible difference is the JSON's own rounding, so `5e-3`
would hide drift (9.623 → 9.626 is a real change). Per figure: 3 dp → `5e-4`, 1 dp → `5e-2`,
4 dp → `5e-5`, 6 dp → `5e-7`.

### Decision: the gate reuses the production correction and imports no TensorFlow

**Choice.** `select_beta_grouped` from `ds02_rul.stacking`; `fit_conformal`, `apply_conformal`,
`empirical_coverage`, `DEFAULT_EDGES` from `ds02_rul.conformal`; `calculate_nasa_score` from
`ds02_rul.metrics`; `pava_causal_no_creciente` from `mia.reglas` via
`sys.path.insert(0, ROOT/"mia")` — the seam `app/ui_rules.py` and `test_mia_rules.py` use.
**Rejected:** re-implementing PAVA in the script (a copy lets gate and engine diverge silently —
the guarded failure). **Why:** a gate grading its private implementation proves nothing about the
shipped rule. TF is avoidable: at module level it appears only in `model.py`, `pipeline.py` and
`persistence.py`, and `ensemble.py` imports persistence lazily, so importing `ds02_rul.stacking`
pulls numpy, pandas, sklearn and (lazily) lightgbm — not Keras.

## The gate: `scripts/freeze_rules_evidence.py`

### CLI surface

`python scripts/freeze_rules_evidence.py [--check | --write] [--cache PATH]`

| Flag | Default | Contract |
| --- | --- | --- |
| `--check` | on | Verifies. Spelling it is the documented form; omitting it changes nothing. |
| `--write` | off | Re-freezes if a field is outside tolerance; otherwise prints `no change` and writes nothing. Requires a readable cache. |
| both | — | Usage error, exit 2 (mutually exclusive group). |
| `--cache` | `ROOT/_p1_oof_cache.npz` | Read-only. `ROOT` from `__file__`, so any cwd works. |

### Exit codes

| Code | Class | Named cause |
| --- | --- | --- |
| `0` | pass | Every check passed; table printed. |
| `2` | usage | Unknown flag, or `--check` with `--write`. Argparse's own code, documented not remapped. |
| `3` | input | Cache absent, unreadable, missing any of `units, cycles, y, p_lstm, p_lgb`, or holding non-finite values. Names the path and the key. |
| `4` | drift | Any figure, the pure-mask size, or a rows-changed count outside tolerance; prints `expected` and `observed` per failing field. |
| `5` | API / contract | `select_beta_grouped` or `fit_conformal` lost a parameter or return key; **or** the JSON violates RULES-05 (not four bins, `n` not summing to `n_calibration`, `source` other than `bin`, missing provenance field). |

Distinct codes let CI tell "no data" (3) from "the numbers moved" (4) from "the code moved" (5).

### What it recomputes

1. `np.load(cache)` → five arrays; assert finite and equal length. Then
   `select_beta_grouped(units, cycles, y, p_lstm, p_lgb, span=5, use_cycle_feature=False)["oof_calib"]`;
   `beta` is printed (`median of 3 folds`), not compared — every figure depends on it.
2. **Pure mask** `np.isin(units, [2.0, 5.0, 10.0, 18.0, 20.0])`: must select 14 915 rows and
   exclude unit 16. **Ordering** `np.argsort(cycles[idx], kind="stable")` — the OOF cache has no
   `start_index`, so ties fall back to row order; the UI's `(cycle, start_index)` lexsort must
   not be imitated.
3. **Correction** `mia.reglas.pava_causal_no_creciente` per unit; **variants** V1
   `np.minimum.accumulate(raw)`, V2 the PAVA series, V3 `np.minimum.accumulate(PAVA)`.
   **Metrics** RMSE, NASA (sum, no clamp), rows changed, `max_positive_increment =
   max(0.0, max(diff(serie)))` per unit then across units.
4. **Conformal** `fit_conformal(y_pure, corregido_pure, target=0.90, edges=DEFAULT_EDGES, min_rows=100)`
   and `empirical_coverage(y_pure, *apply_conformal(corregido_pure, committed))`.

### What it compares, and how

| Committed field | Comparison | Tolerance |
| --- | --- | --- |
| `method`, `debias`, `target_coverage`, `alpha_each_side`, `edges` | echo of the `fit_conformal` inputs (`null` ↔ `inf`) | exact |
| `bins[].n` / `pred_range` / `source` | count, structural echo; `source` MUST be `bin` | exact |
| `bins[].q_low`, `q_high`, `global_quantiles` | recomputed residual quantiles | `5e-5` |
| `n_calibration` | `len(y_pure)` | exact = 14915 |
| `procedencia` | seven fields present and non-empty; `filas_calibracion` and `unidades_calibracion` recomputed | exact / non-empty |

| Recorded figure | Value | Tolerance |
| --- | --- | --- |
| Baseline OOF RMSE / NASA | 9.491 / 19257.1 | `5e-4` / `5e-2` |
| R2 (V1) OOF RMSE / rows changed | 10.737 / 13000 | `5e-4` / exact |
| R2b (V2) OOF RMSE / NASA / rows changed | 9.623 / 18713.9 / 10715 | `5e-4` / `5e-2` / exact |
| Envelope identity | `min(V2) == V1` pointwise, and V1 == V3 | exact |
| Max positive increment, V2 / V3 | +1.328848 / 0.000000 | `5e-7` |
| OOF coverage over the corrected point | 0.9012 | `5e-5` |
| Pure rows | 14915 | exact |

The four `n` values 5291 / 5283 / 3922 / 419 sum to 14 915, so a `global` fallback in any bin is
a contract violation (exit 5), not a rounding difference.

### What it prints

One table, §13's shape, baseline as the reference row; then a check block (`ok` / `DRIFT` per
field, expected vs observed) and, for `--write`, a `field: old → new` list.

```
variant                       OOF RMSE   OOF NASA   Test RMSE*  Test NASA*  rows changed  max +inc
Baseline (raw EMA5)              9.491    19257.1       4.289      2310.6             0          —
V1 running-min                  10.737    21053.0       3.964      1906.6         13000     0.000000
V2 prefix PAVA                   9.623    18713.9       4.173      2182.9         10715    +1.328848
V3 min(prefix PAVA)             10.737    21053.0       3.964      1906.6         13000     0.000000
* recorded in INFORME_reglas_oof.md §13 and models/ds02_manifest.json — not recomputed:
  _p1_oof_cache.npz holds development rows only (RULES-06).
```

The star matters: the cache holds OOF rows only, so RULES-06 forbids claiming a test-panel
regeneration; that panel stays anchored by the manifest and `app/cache`. Because V3 and V1 carry
identical figures and V3 prints 0.000000, the table rebuts any "strict monotonicity" reading.

### Why no TensorFlow, and no `models/`

**Determinism:** the `5e-3` tolerance exists because the BiLSTM is non-deterministic (§1.3); any
path through `predict_interval` makes the gate flaky by construction. **Immutability:** `models/`
is read-only by repository rule and RULES-07. **Cost:** no Keras import, no 2.3 GB HDF5 — the
argument `build_ui_cache.py` makes for the DSS cache. Enforced by a test, not by comment.

### Missing cache degrades to a named failure

```
freeze-rules-evidence: cannot verify
  missing instrument: C:\...\_p1_oof_cache.npz
  rebuild it with:    python scripts/p1_oof_cache.py   (needs the DS02 HDF5 and the base models)
  policy:             RULES-06 — a missing instrument is a failure, never a skip
exit 3
```

The word `skip` MUST NOT appear in the output.

## Test strategy

New file `tests/test_rules_gate.py`; `tests/test_ui_rules.py` grows three tests. Gating copies
the two-line marker already in `tests/test_mia_rules.py`; no `conftest.py`, since the suite
declares its skips per file and changing collection for four other files is not this change.

```python
needs_oof = pytest.mark.skipif(
    not os.path.exists(os.path.join(ROOT, "_p1_oof_cache.npz")),
    reason="_p1_oof_cache.npz missing",
)
```

| Test | Gate | Asserts | Fresh clone |
| --- | --- | --- | --- |
| `test_el_gate_reproduce_las_cifras_comprometidas` | `@needs_oof` | `run(EXPECTED) == 0`; each figure at its HULP; stdout has the three variant rows and the `(recorded)` footer | **skip** |
| `test_el_gate_detecta_drift` | `@needs_oof` | deepcopy `EXPECTED`, `rmse_r2b` one order above tolerance → `4`, both values printed | **skip** |
| `test_la_escritura_es_idempotente` | `@needs_oof` | sha256 before/after `run(..., write=True)` equal on a matching tree | **skip** |
| `test_el_gate_falla_sin_cache_y_no_escribe` | none | `run(cache=<tmp>/absent.npz)` → `3`; path named; no `skip` in stdout; JSON sha256 unchanged | pass |
| `test_el_gate_no_carga_tensorflow` | none | subprocess import prints `False False` for `tensorflow`/`keras` | pass |
| `test_el_defecto_es_check_y_los_flags_son_excluyentes` | none | `main([])` with absent cache → `3`; `main(["--check","--write"])` → `2` | pass |
| `test_el_interruptor_arranca_apagado` | `@needs_cache` | `AppTest`, no `set_value`: `app.toggle[0].value is False`, no exception, five tabs | **skip** |
| `test_la_copia_no_dice_monotonia_estricta` | none | source scan, below | pass |
| `test_la_cobertura_en_test_es_total` | `@needs_cache` | `empirical_coverage(y_true, lower, upper) == 1.0` over the 6 196 corrected windows | **skip** |

**A fresh clone reports five skips and four passes, never a failure** — the contract the
`@needs_oof` pattern in `test_mia_rules.py` already implements.

- **Copy ban:** normalise case, strip accents (`NFKD`), scan `app/dashboard_ds02.py` and
  `app/ui_rules.py` **plus** the live rule strings (`mia.reglas.reglas[i][0]` and `[4]`, which
  the audit tab renders). `BANNED_ALWAYS`: `monotonia estricta`, `estrictamente monoton`,
  `serie monotona`, `serie no creciente`, `regla de monotonia`, `R2b_MONOTONIA`, `R2b_MONOTONICO`;
  a hit is forgiven only when the same sentence carries a negator (`no`, `nunca`, `ni`), which
  keeps honest disclaimers legal while killing a claim. Both files and the six `porque` strings
  pass **unmodified**.
- **Coverage scope:** the existing test asserts the *point* is inside the band; nothing asserts
  the *truth* is. That OOF figure (0.9012) belongs to the gate, so the two do not overlap.
  `test_la_cobertura_pura_es_la_nominal` stays at `abs=0.01`, and 0.9012 sits 0.0012 above 0.90.

## Documentation plan

### README: one section, between `## Interfaces` and `## Reproduce`

Placement is the design. `## Interfaces` ends by telling the reader the DSS reads `app/cache/`
only and triages on the conformal lower bound; the rules layer is the next thing that surface
does. `## Reproduce` owns the command, and `## Honest limitations` must stay the closing section.

```markdown
## Rules layer — opt-in correction (`mia/`)

Two passes over an existing prediction: correction (R2b, R6) then decision
(R1, R7, R8, R9). Table of the six rules with priority and effect.

The toggle. Off by default. Off = the cached reading, the one that reproduces
`models/ds02_manifest.json` (RMSE 4.289 / MAE 3.179 / R² 0.9473 / NASA 2310.6 over
6 196 windows). On = corrected point + recalibrated band; the raw values stay in
`pred_enviada` / `lower_enviada` / `upper_enviada`.

R2b is an isotonic fit, not a monotonicity rule. The prefix fit is non-increasing;
the returned series can rise (max +1.328848 cycles). Forcing strict monotonicity
collapses to R2 — 10.737 / 21053.0 OOF against 9.623 / 18713.9 for R2b.

The calibration is frozen: 14 915 pure OOF rows (units 2, 5, 10, 18, 20; unit 16
excluded as in-sample), coverage 0.9012 OOF / 1.0000 test, point inside the band on
all 6 196 test windows.

Re-check it: `python scripts/freeze_rules_evidence.py`. Links: ADR-009,
INFORME_reglas_oof.md §13.
```

Two adjacent stale counts go with it, because the section claims a test command and they
contradict it: `(11 tests)` in `## Reproduce` and `artifact contract tests (10)` in `## Layout`.
Both become a pointer to `python -m pytest tests -q` with **no hardcoded count** — the count just
went stale, so writing 87 would repeat the defect.

### `openspec/config.yaml` — exact field-level diffs

```diff
-strict_tdd: false
+strict_tdd: true
@@ testing
-  runner: none
-  rationale: "No test runner is configured for the ML notebooks. Verification is by re-executing the notebook and comparing the recorded metrics. strict_tdd stays false; re-evaluate if a pytest suite lands."
+  runner: pytest
+  rationale: "`python -m pytest tests -q` collects the DS02 suite under `tests/` (artifact contract, DSS surface, rules layer). Pipeline correctness is still established by re-executing the notebook and comparing the recorded metrics; the suite never retrains and never writes under `models/`."
   layers:
-    unit: false
-    integration: false
+    unit: true
+    integration: true
@@ rules.apply
-    tdd: false
-    test_command: ""
+    tdd: true
+    test_command: "python -m pytest tests -q"
@@ rules.verify
-    test_command: ""
+    test_command: "python -m pytest tests -q"
@@ rules.verify.guidelines
-      - Do not retrain models in CI (no test runner is configured)
+      - Do not retrain models in CI; the suite reads `app/cache/` and `_p1_oof_cache.npz` only
@@ specs
   - rul-prediction-ds02
   - ds02-dss-ui
+  - ds02-live-evaluation
+  - ds02-rules-engine
@@ rules.archive
-    - Update openspec/specs/rul-prediction-ds02/spec.md when archiving
+    - Update the deployed spec of every capability the change touches when archiving
```

`layers.e2e` stays `false`: the Streamlit `AppTest` renders are integration-level and there is no
browser or HTTP end-to-end path. `ds02-live-evaluation` is added because
`openspec/specs/ds02-live-evaluation/` is deployed on disk and absent from that list — the
proposal's "missing spec" is two missing entries, not one. The archive rule names one spec and
would leave a new capability unmerged. 24 changed lines.

### `openspec/project.md` — exact field-level diffs

| Anchor | Diff |
| --- | --- |
| `## Repository layout` (44-58) | `+├── mia/` (rules layer, opt-in post-processing); `+├── docs/decisions/` (ADR-001…ADR-009); `+│   ├── build_ui_cache.py`; `+│   ├── freeze_rules_evidence.py`; `-├── tests/  # artifact contract tests` → `+├── tests/  # pytest suite: artifact contract, DSS, rules layer` |
| `## How to run` (100-102) | Replace the "There is **no test runner**…" paragraph with the pytest command plus "the suite never retrains and never writes under `models/`"; keep the notebook re-execution sentence as the pipeline-truth statement. |
| new `### Rules layer — mia/ (opt-in)` after line 84 | ~18 lines: the two passes, the six rules, the toggle default, the frozen calibration numbers, the gate command, links to ADR-009 and the spec. |
| `## DS02 artifact contract` (120-130) | `+` one sentence: the rules layer is post-processing over the frozen prediction and never retrains; `mia/` is not part of the artifact contract. |

34 changed lines. The layout block is not decoration: a reader who cannot find `mia/` in the tree
has no reason to trust the spec describing it.

### ADR-009 outline

`docs/decisions/ADR-009-r2b-is-an-isotonic-fit-not-a-monotonicity-rule.md`, in ADR-008's shape
(`Status`, `Date`, `Context`, `Decision`, `Evidence`, `Alternatives rejected`, `Consequences`),
~50 lines:

- **Context:** §9 called R2b "the defensible version of monotonicity"; the name survived into
  tests and docstrings. The series is not non-increasing: max positive increment +1.328848 over
  14 915 pure OOF rows, and its strictly non-increasing envelope is, by identity,
  `np.minimum.accumulate` — R2.
- **Decision:** R2b **is** the extremum of the online prefix PAVA fit; the returned series MAY
  rise; the name is `R2b_ISOTONICO_CAUSAL` and MUST NOT be replaced by a monotonicity claim.
  Strict monotonicity, if wanted, is R2 — a separate decision, not a relabelling.
- **Evidence:** the V1/V2/V3 table, the identity `min(PAVA) == running-min` on all four figures,
  rows changed 13000 / 10715.
- **Alternatives rejected:** (a) call it monotonicity and enforce the envelope — it becomes R2 and
  the gain disappears (9.623 → 10.737 RMSE, 18713.9 → 21053.0 NASA); (b) rename to
  `R2b_MONOTONIA` and keep the behaviour — the name would describe an unmeasured rule; (c) ship R2
  instead — better on test (4.173 → 3.964 RMSE, 2182.9 → 1906.6 NASA), worse on OOF, a
  fleet-regime trade-off needing its own ADR; (d) move the correction into the model — RULES-07
  forbids it and it would invalidate the manifest.
- **Consequences:** copy is constrained (RULES-UI-01); the gate enforces the numbers; every future
  description inherits "causal isotonic adjustment, extremum of the prefix fit"; the R2-vs-R2b
  trade-off is recorded instead of argued.

## Residual mislabels

Same class, three sites — two named by the brief, one found while reading an edited file.

| File | Current | Correction |
| --- | --- | --- |
| `tests/test_mia_rules.py:7` | `3. que la corrección es causal, monótona y no rompe el invariante de la banda;` | `3. que la corrección es causal, isotónica en el prefijo y no rompe el invariante de la banda;` |
| `mia/casos.py:7-8` | `El historial es lo que hace posible la regla de monotonía: sin pasado no hay restriccion que imponer.` | `El historial es lo que hace posible la corrección isotónica causal: sin pasado no hay tendencia que imponer.` |
| `tests/test_ui_rules.py:6` | `el punto corregido es monótono por unidad y la banda sigue conteniéndolo;` | `el punto corregido es el extremo del ajuste isotónico causal por unidad y la banda sigue conteniéndolo;` |
| `mia/reglas.py:16` | no link to the evidence | `+` `Los números de esta capa los reproduce scripts/freeze_rules_evidence.py; si divergen, el gate falla (ADR-009).` |

No translation, no reflow of surrounding paragraphs, no accent clean-up; one line each
(`casos.py` takes two because the sentence wraps). The `mia/reglas.py` line is the proposal's
"one docstring line" and is a *pointer*: the limitation is already correct at lines 54-59, so
repeating it would create a second copy to keep in sync.

## Alternatives considered and rejected

| Alternative | Why rejected |
| --- | --- |
| Keep the generator out of the repo (scratch script) | The evidence becomes unfalsifiable on a fresh clone; nobody can re-derive §13; RULES-06 names a repository CLI as the check. Replacing it is the point of the change. |
| Make the gate a pytest-only test | A red suite reports *that* something moved, not *what*. The script prints expected vs observed per field, offers a re-freeze path after an intentional change, and is the interface the README and RULES-06 promise. The test calls the CLI; it does not replace it. |
| Make the toggle default on | Off is the only setting that reproduces `models/ds02_manifest.json`, which the README and the deployed spec publish. Default-on would silently change every per-engine figure and every triage state, contradicting RULES-07. |
| `--write` as default / `--out PATH` | The first invites accidental re-freezing of a drift; the second turns a caller-supplied path into an arbitrary-file write. |
| Tolerance `5e-3` everywhere | Right for the non-deterministic BiLSTM path, ~10× too loose for a deterministic recomputation; it would hide real drift. |
| Ban the word "monoton" outright | Flags the honest disclaimers the codebase needs and forces a rewrite of correct prose. The negation escape targets claims, not vocabulary. |
| `conftest.py` with shared markers | Changes collection for five files in a documentation change; the per-file two-line marker is the house pattern. |
| Re-implement PAVA / recompute the test panel | The gate must grade the shipped function, not a copy; the cache holds OOF rows only, so recorded test figures under a `(recorded)` header are the honest maximum. |

## File changes and review budget

| File | Action | Description | Lines |
| --- | --- | --- | --- |
| `scripts/freeze_rules_evidence.py` | Create | Gate: CLI, recomputation, comparison, table, write path | 225 |
| `tests/test_rules_gate.py` | Create | Six tests: reproduce, drift, idempotence, missing cache, no-TF, flags | 110 |
| `tests/test_ui_rules.py` | Modify | Toggle default, copy ban, test-panel coverage; header docstring fix | 42 |
| `tests/test_mia_rules.py` | Modify | Docstring item 3 | 2 |
| `mia/casos.py` | Modify | Docstring sentence | 2 |
| `mia/reglas.py` | Modify | One pointer line to the gate | 1 |
| `README.md` | Modify | Rules-layer section; two stale counts | 38 |
| `openspec/config.yaml` | Modify | Runner, TDD flag, test commands, four specs, archive rule | 24 |
| `openspec/project.md` | Modify | Layout, test runner, rules-layer section, contract note | 34 |
| `docs/decisions/ADR-009-*.md` | Create | Decision record | 50 |
| **Total** | | | **528** |

528 authored lines exceeds the 400-line budget, so `ask-on-risk` needs a decision. Two autonomous
slices, both under budget:

- **PR 1 — the gate (336):** script (225) + `tests/test_rules_gate.py` (110) + the
  `mia/reglas.py` line (1). Rollback: delete the script and the test file; no artifact moves.
- **PR 2 — the record (192):** ADR-009 (50) + README (38) + `project.md` (34) + `config.yaml`
  (24) + `test_ui_rules.py` (42) + the two mislabel docstrings (2 + 2).

The `openspec/specs/ds02-rules-engine/spec.md` merge is not counted: it happens at archive, per
the openspec convention, and adds no authored code.

## Threat matrix

N/A — no routing, shell, subprocess, VCS/PR automation or executable-file classification. One
boundary sits outside the matrix: `--cache` is only read, and it cannot cause a write because
`--write` targets the module constant `CALIBRACION` and takes no path.

## Migration / rollout

No migration: no data move, no flag flip, no schema change. The toggle stays off, so every
existing UI reading and manifest figure is unchanged. Rollback is `git revert` of both slices.

## Open questions

- [ ] **Does `0.9012` reproduce from `fit_conformal(y_pure, corregido_pure)`?** §7 records
  **0.8977** for "recalibrada en 14 915 (5 puras)" — but under the R2+R3+R4ii correction, not R2b.
  If it disagrees, the spec is wrong: fix the spec, **never** edit the frozen JSON (RULES-07).
- [ ] **Does `global_quantiles` `[-19.1707, 17.1004]` reproduce?** Same risk, same path. Both are
  asserted by the gate, so this is a blocker to green.
- [ ] **§13 is numbered twice:** `## 13. Corrección: R2b no es una regla de monotonía` (line 338)
  and `## 13. Corrección al informe …` (line 381). README and ADR-009 must cite "§13"
  unambiguously; renumbering is out of scope, so citations point at the first and name the table.
- [ ] **The report attributes R2-vs-baseline to R2-vs-R2b.** Line 425 says R2 "perjudica en OOF
  (RMSE +1.25, NASA +1796)"; those are baseline deltas (10.737 − 9.491 = 1.246; 21053.0 −
  19257.1 = 1795.9), not R2b deltas (1.114; 2339.1). ADR-009 quotes the R2b comparison. The
  report stays untouched — out of scope.
- [ ] **Proposal says "87 plus the gate test".** This design adds nine tests (five skip, four pass
  on a fresh clone). Read the criterion as "the gate's tests"; README and `config.yaml` must not
  hardcode a count for exactly this reason.
