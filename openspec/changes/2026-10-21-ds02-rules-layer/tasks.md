# Tasks: formalize the DS02 rules layer

**Change:** `2026-10-21-ds02-rules-layer`
**Status:** Done (applied 2026-10-21)
**Specs:** [rules engine](specs/ds02-rules-engine/spec.md) · [DSS toggle](specs/ds02-dss-ui/spec.md)
**Design:** [design.md](design.md) · [proposal](proposal.md)
**Delivery:** ask-on-risk · **Review budget:** 400 changed lines · **TDD:** strict (`strict_tdd: true` after task 4.3)

## Conventions that bind every task

- **Strict TDD is active in this repo.** Every task that touches code runs
  `.\.venv\Scripts\python.exe -m pytest tests -q` and records the observed count. Test first, then
  the change, then green.
- **Cache gating copies `tests/test_mia_rules.py:29-33` exactly** — the two-line per-file marker,
  no `conftest.py`:

  ```python
  needs_oof = pytest.mark.skipif(
      not os.path.exists(os.path.join(ROOT, "_p1_oof_cache.npz")),
      reason="_p1_oof_cache.npz missing",
  )
  ```

  A missing instrument skips a **test**; the same missing instrument **fails** the
  **CLI** with exit 3 (RULES-06). Two policies, one artifact — task 2.1 asserts both.
- **Untouchable:** `models/`, `app/cache/`, `src/`, and every frozen metric. `mia/` takes one
  docstring addition and no behaviour change. The toggle stays off (RULES-07).
- **No hardcoded test counts** in `README.md` or `openspec/config.yaml`. The current count is 87 and
  this change adds 9; a written number is the defect being removed.
- New-file language: English under `scripts/`, Spanish under `mia/` and `tests/` (design, technical
  approach).

## Tasks

| # | Task | Status | Acceptance check (measured) | Files touched | Verify |
| --- | --- | --- | --- | --- | --- |
| 1.1 | Consolidate the two sections numbered 13 in `INFORME_reglas_oof.md` into one | Done | `Select-String -Pattern '^## 13'` returns **1** hit (the heading at line 338, `## 13. Corrección: R2b no es una regla de monotonía`); the duplicate at line 381 is gone. The surviving section carries: the prefix-PAVA definition (extremum of the online non-increasing fit of `y_1..t`), the causality sentence, `+1.328848` (replacing the duplicate's rounded `+1.33`), the **four-row** table `Baseline 9.491 / 19257.1 / 4.289 / 2310.6`, `R2 10.737 / 21053.0 / 3.964 / 1906.6`, `R2b 9.623 / 18713.9 / 4.173 / 2182.9`, `min(R2b) 10.737 / 21053.0 / 3.964 / 1906.6`, the naming consequence (`R2b_ISOTONICO_CAUSAL`, `R2b_MONOTONIA` rejected) and the whole `### 13.1 Estado de la implementación` list. `git diff` shows **no changed digit** in any figure carried over; the only removed prose is the duplicate's restatement. The hardcoded `87 tests` line in 13.1 becomes the run command (see Notes). **Measured 2026-10-21:** `Select-String -Pattern '^## 13'` → 1 hit (line 338); `git diff --stat -- INFORME_reglas_oof.md` → 16 insertions / 63 deletions; the four-row table is byte-identical to the deleted copy (baseline 9.491 / 19257.1 / 4.289 / 2310.6, R2 10.737 / 21053.0 / 3.964 / 1906.6, R2b 9.623 / 18713.9 / 4.173 / 2182.9, min(R2b) 10.737 / 21053.0 / 3.964 / 1906.6); `+1.33` gone, `+1.328848` retained; no digit changed. | `INFORME_reglas_oof.md` | `Select-String -Path INFORME_reglas_oof.md -Pattern '^## 13'` + `git diff -- INFORME_reglas_oof.md` |
| 1.2 | Fix two of the three residual "monotónica" mislabels; the `test_ui_rules.py` header rides with 3.1 | Done | `tests/test_mia_rules.py` docstring item 3 reads "que la corrección es causal, isotónica en el prefijo y no rompe el invariante de la banda"; `mia/casos.py` docstring reads "El historial es lo que hace posible la corrección isotónica causal: sin pasado no hay tendencia que imponer." (two wrapped lines). `git diff` for both files touches docstring lines only — zero code lines, zero accent clean-up, zero reflow of surrounding paragraphs. | `tests/test_mia_rules.py`, `mia/casos.py` | `.\.venv\Scripts\python.exe -m pytest tests -q` → 87 passed, exit 0 |
| 2.1 | Gate part 1 — `scripts/freeze_rules_evidence.py` CLI surface, cache load, exits 2 and 3, fail-loud message | Done | `python scripts\freeze_rules_evidence.py --cache <tmp>\absent.npz` exits **3**, names the path, names `python scripts/p1_oof_cache.py` as the rebuild step, quotes RULES-06, and its output contains **no** `skip`; `--check --write` exits **2** (argparse mutually exclusive group); a cache missing any of `units, cycles, y, p_lstm, p_lgb` or holding non-finite values exits 3 and names the key. `import freeze_rules_evidence` in a fresh subprocess prints `tensorflow False` and `keras False`. The three tests are green on this tree. | `scripts/freeze_rules_evidence.py`, `tests/test_rules_gate.py` | `.\.venv\Scripts\python.exe -m pytest tests -q` → 87 + 3 passed, exit 0; `python scripts\freeze_rules_evidence.py --cache C:\none.npz; echo $LASTEXITCODE` → 3 |
| 2.2 | Gate part 2 — instrument rebuild, PAVA variants, comparison at committed precision, table, exit 4/5, `--write` | Done | `python scripts\freeze_rules_evidence.py` exits **0** on this tree and prints the four-row table (`Baseline 9.491 19257.1`, `V1 10.737 21053.0`, `V2 9.623 18713.9`, `V3 10.737 21053.0`), max `+inc` `0.000000 / +1.328848 / 0.000000`, rows changed `13000 / 10715 / 13000`, and the `(recorded)` footer for the test columns. Pure mask selects **14 915** rows and excludes unit 16. Recomputed coverage **0.9012** at `5e-5`; `global_quantiles` `[-19.1707, 17.1004]` at `5e-5`. A deepcopied expectation with `rmse_r2b` moved one order above its HULP exits **4** and prints both `expected` and `observed`. `--write` on a matching tree prints `no change` and leaves the SHA-256 of `mia/calibracion_banda.json` unchanged. Six tests in the gate file green. | `scripts/freeze_rules_evidence.py`, `tests/test_rules_gate.py`, `mia/reglas.py` (one docstring pointer line) | `.\.venv\Scripts\python.exe -m pytest tests -q` → 87 + 6 passed, exit 0; `python scripts\freeze_rules_evidence.py; echo $LASTEXITCODE` → 0 |
| 3.1 | UI guarantees — toggle default, copy ban, test-panel coverage, header docstring | Done | Three new tests green: (a) `AppTest` with no `set_value` → `app.toggle[0].value is False`, no exception, five tabs; (b) the copy scan over `app/dashboard_ds02.py`, `app/ui_rules.py` **and** the six live strings (`mia.reglas.REGLAS_CORRECCION/REGLAS_DECISION` names and `porque` texts) finds **0** banned formulations after `NFKD` + case-fold, using the same-sentence negator escape, and `git diff` for both app files is empty (they pass unmodified); (c) `empirical_coverage(y_true, lower, upper) == 1.0` over the **6 196** corrected test windows. The header docstring item 2 reads "el punto corregido es el extremo del ajuste isotónico causal por unidad y la banda sigue conteniéndolo". The scan does not touch the gate's OOF `0.9012`, and `test_la_cobertura_pura_es_la_nominal` stays at `abs=0.01`. | `tests/test_ui_rules.py` | `.\.venv\Scripts\python.exe -m pytest tests -q` → 87 + 6 + 3 passed, exit 0 |
| 4.1 | ADR-009 — R2b is an isotonic fit, not a monotonicity rule | Done | `docs/decisions/ADR-009-r2b-is-an-isotonic-fit-not-a-monotonicity-rule.md` exists in ADR-008's shape (`Status`, `Date`, `Context`, `Decision`, `Evidence`, `Alternatives rejected`, `Consequences`); carries `+1.328848`, the R2-vs-R2b pair `10.737 / 21053.0` vs `9.623 / 18713.9` (OOF) and `3.964 / 1906.6` vs `4.173 / 2182.9` (test), rows changed `13000 / 10715`, the identity `min(PAVA) == running-min`, and the four rejected alternatives (enforce the envelope, rename to `R2b_MONOTONIA`, ship R2, move it into the model). No figure disagrees with spec RULES-02 or with the consolidated §13. | `docs/decisions/ADR-009-*.md` | `git diff --stat` + cross-read against `INFORME_reglas_oof.md` §13 |
| 4.2 | README — rules-layer section and the two stale counts | Done | Heading order is `## Interfaces` → `## Rules layer — opt-in correction (mia/)` → `## Reproduce` → `## Layout` → `## Honest limitations`, and `## Honest limitations` is still last. The section states: toggle off by default; off reproduces `models/ds02_manifest.json` (RMSE 4.289 / MAE 3.179 / R² 0.9473 / NASA 2310.6 over 6 196 windows); on keeps `pred_enviada` / `lower_enviada` / `upper_enviada`; max rise `+1.328848`; strict monotonicity collapses to R2 (`10.737 / 21053.0` vs `9.623 / 18713.9`); 14 915 pure rows, `0.9012` OOF / `1.0000` test; the `python scripts/freeze_rules_evidence.py` command; links to ADR-009 and §13. `Select-String -Pattern '11 tests|artifact contract tests \(10\)'` returns **0** hits, and no digit test count replaces them. | `README.md` | `Select-String -Path README.md -Pattern '^## '` + `Select-String -Path README.md -Pattern '11 tests|artifact contract tests'` |
| 4.3 | `openspec/config.yaml` — runner, TDD flag, commands, specs list, archive rule | Done | Six fields move exactly as designed: `strict_tdd: true`; `testing.runner: pytest` with the new rationale; `layers.unit: true`, `layers.integration: true` (`e2e` stays `false`); `rules.apply.tdd: true` and `apply.test_command: "python -m pytest tests -q"`; `rules.verify.test_command` set; the "no test runner" verify guideline replaced. `specs:` has **four** entries — `rul-prediction-ds02`, `ds02-dss-ui`, `ds02-live-evaluation`, `ds02-rules-engine` — i.e. **two** entries added, not one: `ds02-live-evaluation` is deployed on disk and was absent from the list, `ds02-rules-engine` is the new capability. The archive rule no longer names a single spec path. `python -c "import yaml;d=yaml.safe_load(open('openspec/config.yaml'));print(len(d['specs']), d['strict_tdd'], d['testing']['runner'])"` → `4 True pytest`. | `openspec/config.yaml` | the `python -c` check above |
| 4.4 | `openspec/project.md` — layout, test runner, rules-layer section, contract note | Done | `## Repository layout` lists `mia/`, `docs/decisions/` (ADR-001…ADR-009), both `scripts/build_ui_cache.py` and `scripts/freeze_rules_evidence.py`, and `tests/` as "pytest suite: artifact contract, DSS, rules layer". `## How to run` carries the pytest command plus "never retrains and never writes under `models/`", keeps notebook re-execution as pipeline truth, and `Select-String -Pattern 'no test runner'` returns **0** hits. A `### Rules layer — mia/ (opt-in)` section states the two passes, the six rules, the off default, 14 915 / `0.9012` / `1.0000`, the gate command and links to ADR-009 and the spec. The artifact-contract section adds the sentence that `mia/` is post-processing and not part of the contract. | `openspec/project.md` | `Select-String -Path openspec/project.md -Pattern 'no test runner|mia/'` |
| 5.1 | Full verification and fresh-clone simulation | Done | `.\.venv\Scripts\python.exe -m pytest tests -q` → **96 passed, exit 0** (87 + 9 new: 6 gate + 3 UI; record the observed count, do not write it into docs). `python scripts\freeze_rules_evidence.py` → **0**. On a copy of the tree with `_p1_oof_cache.npz` and `app/cache/` absent: **5 skipped, 4 passed, 0 failed** — the gate test never fails on a fresh clone. `git status --porcelain models/ app/cache/ src/` is empty. `git diff --stat` on the four model files is empty. | none (verification only) | the three commands above |

## Apply record — 2026-10-21

| Check | Command | Result |
| --- | --- | --- |
| Full suite | `.\\.venv\\Scripts\\python.exe -m pytest tests -q` | **96 passed**, exit 0 |
| Gate | `python scripts/freeze_rules_evidence.py` | exit **0**; table printed; all 12 checks `ok` |
| Fresh-clone simulation (nine new tests, `_p1_oof_cache.npz` and `app/cache/` absent) | pytest on the new node ids | **4 passed, 5 skipped, 0 failed** |
| Missing cache | gate with `--cache <tmp>/absent.npz` | exit **3**, path + rebuild step + RULES-06, no `skip` |
| Frozen artifacts | `git status --porcelain models/ app/cache/ src/` | empty |
| Model files | `git diff --stat` on the four artifacts | empty |
| Config | `python -c "import yaml; …"` | `4 True pytest` |
| README | heading scan + stale-count scan | order correct; **0** hits for `11 tests` / `artifact contract tests (10)` |

## Review Workload Forecast

**estimated authored changed lines:** ~583 — 528 summed from the design's file map, plus ~55 for the §13 consolidation, which the map does not carry (delete the duplicate's ~48 lines, edit ~7 in the survivor).

**400-line budget risk:** High

**Chained PRs recommended:** Yes

**Decision needed before apply:** Yes

| File | Action | Estimated lines | Slice |
| --- | --- | --- | --- |
| `scripts/freeze_rules_evidence.py` | Create | 225 | 1 |
| `tests/test_rules_gate.py` | Create | 110 | 1 |
| `mia/reglas.py` | Modify | 1 | 1 |
| `INFORME_reglas_oof.md` | Modify | ~55 (mostly deletions) | 2 |
| `docs/decisions/ADR-009-*.md` | Create | 50 | 2 |
| `tests/test_ui_rules.py` | Modify | 42 | 2 |
| `README.md` | Modify | 38 | 2 |
| `openspec/project.md` | Modify | 34 | 2 |
| `openspec/config.yaml` | Modify | 24 | 2 |
| `tests/test_mia_rules.py` | Modify | 2 | 2 |
| `mia/casos.py` | Modify | 2 | 2 |
| **Total** | | **~583** | |

**Which files dominate:** the gate pair. `scripts/freeze_rules_evidence.py` (~225) plus
`tests/test_rules_gate.py` (~110) are 335 of the 528 design-mapped lines — 63 % of the map and
~57 % of the full estimate. Everything else is documentation or two-line docstring edits; no other
single file reaches 60 lines.

**Basis and caveat:** these are the design's own per-file estimates, used as scope and summed as
written — not a measured `git diff`. `design.md` is ~390 lines and its 528 total is an estimate, so
treat the forecast as a band, not a fact. The budget verdict does not depend on the band width: both
totals exceed 400.

## Dependency order and slice split

```
1.1 (INFORME §13) ──> 4.1 (ADR-009) ──> 4.2 (README: links §13 + ADR-009)
1.1 ─────────────────────────────────> 4.2
2.1 (CLI + inputs + 3 tests) ──> 2.2 (recompute + compare + table + 3 tests) ──> 4.2 (gate command)
1.2 (mislabels) ──> 3.1 (copy-ban test reads the live strings)
4.3, 4.4 (config / project) ── independent of everything except 5.1
5.1 last
```

Ordered: **1.1 → 2.1 → 2.2 → 1.2 → 3.1 → 4.1 → 4.2 → 4.3 → 4.4 → 5.1.** 1.1 first because both
README and ADR-009 cite "§13" and the number is ambiguous until the duplicate is gone.

### Slice 1 — "the gate" (tasks 2.1, 2.2) · 336 lines

`scripts/freeze_rules_evidence.py` + `tests/test_rules_gate.py` + the `mia/reglas.py` pointer.
Ships a working, self-contained CLI: RULES-06 becomes checkable, the table is regenerable, the
suite grows by six tests. **Revert:** delete the two files and the one docstring line; no artifact,
cache or metric moves.

### Slice 2 — "the record" (tasks 1.1, 1.2, 3.1, 4.1–4.4) · 247 lines

INFORME consolidation, ADR-009, README, `project.md`, `config.yaml`, the three UI tests, the two
mislabels. **Revert:** `git revert` of these commits leaves slice 1 intact and green; the only
cross-slice references are the README/ADR mentions of the gate command, so revert slice 2 **before**
slice 1 if both must go.

Both slices are under 400. Slice 2 depends on slice 1 only for the command it documents; slice 1 is
independently shippable and independently revertible.

## Risks and mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| **The gate test fails instead of skipping on a fresh clone** — a module-level `np.load` or an import-time read of the cache breaks collection for the whole suite | High | `@needs_oof` on the three cache-dependent tests, copied verbatim from `test_mia_rules.py`; no `conftest.py`; 5.1 proves it by running with both caches absent and requires **0 failed**. |
| Two policies on the same missing artifact look contradictory: the test skips, the CLI exits 3 | Med | Stated as a contract in Conventions; 2.1 asserts exit 3, the named path and the **absence of `skip`** in stdout. |
| Tolerance too tight for a different numpy/BLAS build, so a legitimate environment reports drift | Med | HULP from the committed decimals (`5e-5` for 4 dp, `5e-4` for 3 dp, `5e-2` for 1 dp, `5e-7` for 6 dp) plus `1e-9`; the fix for a real difference is to record it and re-freeze deliberately, **never** to edit the frozen JSON (RULES-07). |
| `--write` mutates a frozen artifact by accident | High | `--check` default, mutually exclusive group, `--write` has no path argument (module constant only), no-op within tolerance; 2.2 asserts an unchanged SHA-256 on a matching tree. |
| The gate reintroduces TensorFlow and becomes flaky and slow | High | Imports limited to the numpy/sklearn path plus `mia.reglas`; 2.1 asserts `tensorflow False` / `keras False` in a fresh subprocess. |
| Copy ban flags the honest disclaimers the codebase needs | Med | Negator escape inside the same sentence (`no`, `nunca`, `ni`); both app files and the six `porque` strings must pass **unmodified** — if a real hit appears, fix the copy, never the scan. |
| The §13 consolidation silently moves a figure | High | 1.1 requires zero changed digits; the four-row table and `+1.328848` are copied from the duplicate and kept byte-identical; deletion review is read against the surviving section line by line. |
| 13.1's `87 tests` line goes stale the moment this change lands (87 → 96) | Low | 1.1 replaces the number with the run command; 4.2/4.3 forbid hardcoded counts for the same reason. Flagged in Notes for the human to confirm. |
| Docs drift from the shipped gate (README promises a flag the CLI lacks) | Med | 4.2 quotes only `--check`/`--write`/`--cache` as designed; 5.1 runs the documented command verbatim. |
| Scope creep beyond the file map (translation, spec merge, re-derivation) | Med | Out of scope is explicit: no translation, no model change, no metric edit, spec merge happens at archive. Open question 1 (`0.9012`), 2 (`global_quantiles`) and 4 (RMSE +1.25 / NASA +1796 attribution) are **closed** — no task re-derives or "fixes" them. |

## Checkpoints

- **After 2.2:** `.\.venv\Scripts\python.exe -m pytest tests -q` → 93 passed; gate exits 0; slice 1 is
  shippable and revertible on its own.
- **After 4.4:** 96 passed; gate exits 0; heading order in README correct; `config.yaml` parses with
  four specs; `models/`, `app/cache/`, `src/` clean.
- **After 5.1:** fresh-clone simulation reports 5 skipped / 4 passed / 0 failed.

## Notes

- **Closed, do not re-open.** `0.9012` is reproducible: an out-of-repo run of the freeze chain
  produced exactly the committed JSON (bins identical, OOF coverage 0.9012, test 1.0000,
  `lower <= point <= upper` on all 6 196 windows). §7's `0.8977` belongs to the R2+R3+R4ii
  correction, a different rule. `global_quantiles [-19.1707, 17.1004]` is what the committed JSON
  contains. The §7 / line-425 attribution of RMSE +1.25 and NASA +1796 to R2 is arithmetically
  correct against the baseline and stays untouched. No task exists to revisit any of them.
- **Open question 3 is closed by 1.1:** the two `## 13.` headings duplicated each other. The fix was
  consolidation, not renumbering; one heading remains (line 338) and no measured figure changed.
- **`87 tests` in §13.1** is the one judgement call in 1.1: carrying the number forward guarantees
  it is wrong after this change (96). The task replaces it with the run command, matching the
  no-hardcoded-count rule applied to README and `config.yaml`.
- **Not counted in the budget:** the archive-time merge of `specs/ds02-rules-engine/spec.md` into
  `openspec/specs/`, per the openspec convention.
- **Deviation recorded during apply.** The design states that importing `ds02_rul.stacking` pulls no
  Keras. It does: `src/ds02_rul/__init__.py` imports `pooling`, which imports `keras`, so the package
  `__init__` runs before any submodule. The claim held for the module bodies only. The gate registers
  `ds02_rul` as an explicit namespace package (`__path__ = src/ds02_rul`) so the `__init__` never
  executes and the no-TF test holds; nothing under `src/` changed. The runtime cost the design
  rejected stays rejected.
