# Proposal: formalize the DS02 rules layer

**Change:** `2026-10-21-ds02-rules-layer`

## Intent

The rules layer shipped in `39c7c47`, `0dd73b8`, `989e722`, `90d440f` and works:
`mia/`, the frozen calibration, `app/ui_rules.py`, an off-by-default toggle, 87
tests green. It has no SDD coverage — zero hits for `mia/|R2b|isoton|reglas` in
`openspec/`. This change formalizes what shipped and closes its gaps.
Not greenfield; nothing is rebuilt.

## Scope

### In Scope

- `ds02-rules-engine` spec from the code and `INFORME_reglas_oof.md`.
- `scripts/freeze_rules_evidence.py`: regenerates the calibration numbers from
  `_p1_oof_cache.npz`, prints the monotonicity table, fails on drift or missing cache.
- ADR-009: R2b is an isotonic fit, not a monotonicity rule.
- README: the layer and toggle.
- `openspec/config.yaml` and `project.md`: real runner, real TDD flag, missing spec.
- One docstring line in `mia/reglas.py`.

### Out of Scope

- Retraining, editing `models/`, changing any frozen metric.
- Translating the Spanish sources.
- Enabling the toggle.

## Capabilities

### New

- `ds02-rules-engine`: causal correction pass (R2b, R6), decision pass (R1, R7,
  R8, R9), frozen calibration and its provenance.

### Modified

- `ds02-dss-ui`: one requirement — off-by-default toggle, raw reading preserved.

## Facts the spec MUST preserve

- R2b returns the **extremum of the online prefix PAVA fit**: non-increasing fit,
  non-monotone series, max measured increment **+1.328848**.
- `min(PAVA)` equals raw running min (R2) on all four metrics, so the gain comes
  exactly from letting the point rise: R2b 9.623 / 18713.9 OOF, 4.173 / 2182.9
  test; R2 10.737 / 21053.0, 3.964 / 1906.6.
- Calibration: 14 915 pure OOF rows (2, 5, 10, 18, 20; 16 in-sample), coverage
  0.9012 OOF / 1.0000 test, point inside the band on all 6 196 test windows;
  provenance fix, same bins.
- Off by default: the raw cache read reproduces `models/ds02_manifest.json`.

## Approach

Document, prove, record. The script is the only new executable code and reads the
OOF instrument, not the model. Byte-compatible: `models/`, `app/cache/`, `src/`,
`mia/` except that line.

## Affected Areas

| Area | Impact | Description |
| --- | --- | --- |
| `openspec/specs/ds02-rules-engine/spec.md` | New | Engine contract |
| `.../2026-10-21-ds02-rules-layer/specs/ds02-dss-ui/spec.md` | New | Toggle delta |
| `scripts/freeze_rules_evidence.py` | New | Regeneration gate |
| `docs/decisions/ADR-009-*.md` | New | Decision record |
| `README.md`, `mia/reglas.py` | Modified | Docs, one docstring |
| `openspec/config.yaml`, `openspec/project.md` | Modified | Runner and TDD truth |

## Risks

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Exact regeneration needs a gitignored cache and a non-deterministic BiLSTM | High | Gate the freeze step against committed numbers; fail loudly |
| "Monotonic" creeps back | Med | Spec and ADR state the non-monotone series |
| Docs exceed the review budget | Med | Docs only, no translation |

## Rollback Plan

Revert the change commits; deleting the script restores the tree. No artifact,
cache or metric moves.

## Dependencies

- `_p1_oof_cache.npz` (gitignored); absence MUST fail, not skip.
- `pytest` in `.venv`.

## Success Criteria

- [ ] The spec covers both passes, calibration and the no-retrain boundary.
- [ ] Rules-layer grep hits under `openspec/`; `config.yaml` lists all four deployed specs.
- [ ] The script reproduces the committed numbers and fails on drift.
- [ ] `pytest tests -q` green: 87 plus the gate test.
- [ ] README documents the toggle; ADR-009 is linked.
- [ ] `models/` untouched; manifest hashes unchanged.
