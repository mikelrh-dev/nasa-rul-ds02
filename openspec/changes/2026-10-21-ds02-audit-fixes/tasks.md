# Tasks — audit fixes without retraining

## 1. Gate

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 1.1 | Evaluate `_compare` before `_write_frozen`; drift returns 4 with the file untouched | Done | `test_el_gate_no_toca_el_json_si_las_cifras_derivan`: exit 4, message `refusing to re-freeze`, SHA-256 unchanged |
| 1.2 | Keep the clean path identical | Done | `test_la_escritura_es_idempotente` still green; `freeze_rules_evidence.py` exits **0** and prints `no change` |

Files: `scripts/freeze_rules_evidence.py`

## 2. Thresholds and aggregation

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 2.1 | Alarm and critical-zone MAE take the operator's hangar threshold | Done | dashboard passes `threshold_aog` at both sites; no `25.0` literal remains |
| 2.2 | Per-unit metrics and critical-zone MAE read the frame in use | Done | `per_unit_metrics(frame)` and `critical_zone_mae(frame, threshold_aog)`; card names the reading |
| 2.3 | One criterion: worst window per cycle for state, alarm and order | Done | `first_alarm_cycle` defaults to `lower_min`; `test_la_alarma_usa_la_peor_ventana_del_ciclo` |
| 2.4 | Chart labels the mean it draws | Done | `unit_curve` docstring and the metrics caption say which statistic decides |

Files: `app/dashboard_ds02.py`, `app/ui_data_loader.py`

## 3. Provenance of the reading

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 3.1 | `work_order` carries `banda`, `correccion` and per-unit `regla` | Done | JSON and CSV expose the three fields; CSV header test updated on purpose |
| 3.2 | `live_work_order` decides with `mia.motor` and serialises rule and motive | Done | `test_la_orden_externa_la_decide_el_motor` and `..._con_r1` |
| 3.3 | The dashboard declares the band in use next to the toggle | Done | `test_la_ui_declara_la_banda_en_uso` reads the caption with the toggle off and on |

Files: `app/ui_data_loader.py`, `app/ui_inference.py`, `app/dashboard_ds02.py`

## 4. Calibration guard

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 4.1 | Bins under 500 rows may only widen the band | Done | at 75.0 the sides are `min(q_low, -19.1707)` and `max(q_high, 17.1004)`; crossing drop 2.66 cycles |
| 4.2 | Document the guard in the measurement report | Done | `INFORME_reglas_oof.md` §13.2 names the rule and its threshold |

Files: `mia/reglas.py`, `INFORME_reglas_oof.md`, `AUDITORIA_ds02_2026-10-21.md`

## 5. Verification

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 5.1 | Unit tests for every new behaviour | Done | `python -m pytest tests -q` → **111 passed**, exit 0 |
| 5.2 | Gate exits 0 on the real tree | Done | `python scripts/freeze_rules_evidence.py` → exit 0, coverage 0.9012 unchanged |
| 5.3 | Dashboard renders with the toggle off and on | Done | AppTest: no exception, five tabs, correct caption per state |
| 5.4 | Live tab scores a unit after the change | Done | AppTest clicks `Evaluar unidad`: `RUL estimada` and `Ventanas puntuadas` render, no exception |

## Not done, by design

- Unifying the artifact band with the R6 recalibration numerically. The surface
  declares the source instead; see design D1.
- Any change under `models/` or `app/cache/`. Verified untouched.
