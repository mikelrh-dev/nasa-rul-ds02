# Proposal: one palette per channel, duplicate channels collapsed, honest pressure caption

**Change:** `2026-11-14-radiografia-paleta-duplicados`
**Status:** Proposed
**Capabilities:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md) (Modified)

## Intent

Inspection of the Motor tab found three presentational defects that undermine the
radiography as evidence. First, two channel pairs are effectively the same signal
(measured correlation 1.000 in all three test units: `P15`/`P21`, maximum difference
0.25 psia, and `Ps30`/`P40`), so half of the pressure traces repeat information. Second,
the same channel changes colour between the per-cycle view and the RUL-aligned view (T50
green in one, cyan in the other), forcing the reader to re-learn the legend. Third, the
pressure caption says "ninguno de estos canales muestra una deriva sostenida" while the
aligned chart draws a visible arc; a tribunal member could measure the correlation and
contradict the sentence. The caption must state what is actually drawn.

## Scope

### In scope

- Fixed colour table per channel code, shared by both views, defined in `app/lib/theme.py`.
- Collapse duplicated channels into one trace labelled with both codes.
- Caption rebuilt from the aligned frame: measured largest change between RUL bins,
  monotonicity, and the criterion a channel must pass to be called drifting.
- Tests locking the collapse, the shared palette and the caption figures.

### Out of scope

- The gauge (duplicates the RUL p35 card); it stays as it is and is decided separately.
- Any metric, threshold, rule, artifact or triage change; channel labels used by the
  glossary and paste grid stay untouched.

## Assumed decisions

The proposal round timed out, so these follow the recommended options and can be
corrected before apply:

- Duplicated pairs are merged into one trace (`P15 · P21`, `Ps30 · P40`).
- The pressure caption carries figures (largest bin change, non-monotonic shape).
- Colour comes from one fixed table keyed by channel code.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `ds02-dss-ui`: extends "Physical sensor radiography" with a channel identity contract
  (one colour per channel across views, duplicated channels collapsed) and a caption that
  cannot contradict its own curve.

## Approach

A `COLOR_CANAL` table plus a `canales_unicos()` helper in `theme.py`; `fig_deriva` and
`fig_deriva_vida` consume both. The aligned summary gains a `monotono` flag computed from
the sign changes of the bin series; `caption_deriva_vida` reports the largest bin change
and the monotonicity instead of asserting operating-condition noise.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/lib/theme.py` | Modify | colour table, `canales_unicos()`, duplicate collapse in both figures, caption |
| `tests/test_radioografia_alineada.py` | Modify | collapse, palette and caption contracts |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Collapsing channels hides a real difference inside a pair | Low | measured max difference 0.25 psia; the label names both codes so nothing is hidden |
| A fixed palette repeats a hue for two channels | Medium | table assigns a distinct hue per visible channel code; test asserts uniqueness |
| Caption becomes longer and crowds the card | Low | one sentence with figures, same length class as today |

## Rollback Plan

`git revert` the apply commit. Only `app/lib/theme.py` and its test are touched.

## Dependencies

Repository virtualenv and pytest. No new dependency.

## Success Criteria

- [ ] Pressure charts show five traces, not seven, with the paired codes in the label.
- [ ] The same channel has the same colour in both views at 1280 px and 560 px.
- [ ] The pressure caption states the measured largest change and that the shape is not
      monotone, with method and source.
- [ ] `python -m pytest tests -q` green except the three pre-existing MLflow failures.
