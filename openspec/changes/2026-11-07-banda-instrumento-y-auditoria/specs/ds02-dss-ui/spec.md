# Spec delta: the screen MUST name the 90 % as a nominal target

**Change:** `2026-11-07-banda-instrumento-y-auditoria`
**Capability:** `ds02-dss-ui`
**Status:** Applied
**Sources of truth:** `app/dashboard_ds02.py`, `app/ui_modulos/_tab_flota.py`,
`tests/test_live_eval.py`

## MODIFIED

### The band is described by its target and its measured coverage

The screen MUST describe the conformal band as a nominal 90 % target whose coverage is
measured empirically, and MUST NOT present the nominal target as realised coverage. The
vocabulary expander MUST contain both strings `objetivo nominal 90 %` and
`cobertura medida`; the chart legend MUST read `objetivo 90 % · cobertura medida`.

The measured value on the rules-layer instrument is 0.901643 against a nominal 0.90.

#### Scenario: the vocabulary line does not claim 90 % coverage

- GIVEN the dashboard with the rules layer available
- WHEN the `Cómo leer esta pantalla` expander renders
- THEN it SHALL contain `objetivo nominal 90 %` and `cobertura medida`
- AND it MUST NOT label the band as `Banda 90 %` or as a guaranteed coverage

#### Scenario: the legend matches the vocabulary

- GIVEN the fleet tab chart with the band drawn
- WHEN the trace is rendered
- THEN its name SHALL be `objetivo 90 % · cobertura medida`

## Related capabilities

Cites, without modifying, `ds02-rules-engine` (which defines the band and its instrument)
and `ds02-live-evaluation` (which asserts the on-screen vocabulary).
