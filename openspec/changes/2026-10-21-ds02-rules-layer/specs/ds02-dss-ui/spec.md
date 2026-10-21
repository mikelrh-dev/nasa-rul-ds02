# Spec delta: the rules correction stays opt-in

**Change:** `2026-10-21-ds02-rules-layer`
**Capability:** `ds02-dss-ui` (modified)
**Status:** Proposed
**Deployed spec:** [`openspec/specs/ds02-dss-ui/spec.md`](../../../../specs/ds02-dss-ui/spec.md)

This delta adds one requirement to the deployed surface. It does not change the
triage thresholds, the tab layout or the artifact contract.

---

## ADDED

### Requirement UI-RULES-01: The correction is opt-in and the raw reading stays authoritative

The DSS SHALL expose the rules correction behind a toggle that defaults to **off**
on every fresh session. While the toggle is off, every displayed point, band and
metric SHALL come from the cached prediction exactly as stored, and that raw
reading SHALL be the one that reproduces `models/ds02_manifest.json`.

When the toggle is on, the surface SHALL show the corrected point and the
recalibrated band, and SHALL retain the raw values in `pred_enviada`,
`lower_enviada` and `upper_enviada` so both readings remain available. The raw
columns MUST NOT be overwritten, dropped or hidden; the surface SHALL state where
the raw reading can be inspected.

User-facing copy — labels, help text, captions and `alt` text — SHALL describe R2b
as a **causal isotonic adjustment**, the extremum of the online prefix fit. It MUST
NOT describe the corrected series as strictly monotone, non-increasing, or call
the rule a monotonicity rule.

#### Scenario: A fresh session shows the raw reading

- GIVEN a newly started dashboard
- WHEN the correction toggle is inspected
- THEN its default is off
- AND the displayed point and band are the cached values
- AND each per-engine RMSE matches `models/ds02_manifest.json` within `5e-3`

#### Scenario: Turning the correction on hides nothing

- GIVEN the correction toggle is on
- WHEN the corrected frame is displayed
- THEN `pred_enviada`, `lower_enviada` and `upper_enviada` are still present
- AND the row count is unchanged
- AND the surface states where the raw reading is available

#### Scenario: The copy does not overclaim

- GIVEN the toggle label, its help text, the active-correction caption and the
  audit tab
- WHEN the user-facing strings are read
- THEN R2b is described as a causal isotonic adjustment
- AND no string says the corrected series is strictly monotone or non-increasing

**Checks:** `tests/test_ui_rules.py::test_el_tablero_rendea_con_la_correccion_activada`,
`tests/test_ui_rules.py::test_el_tablero_sigue_entregando_las_mismas_metricas_crudas`,
`tests/test_ui_rules.py::test_la_correccion_conserva_filas_y_deja_la_lectura_cruda`,
`tests/test_ui_rules.py::test_la_lectura_cruda_sigue_siendo_la_envolvente_monotono`,
and a copy scan over `app/dashboard_ds02.py` and `app/ui_rules.py` that rejects the
banned formulations.
