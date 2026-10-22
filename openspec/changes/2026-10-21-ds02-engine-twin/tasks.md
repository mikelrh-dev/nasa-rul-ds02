# Tasks — engine twin and hangar lifecycle

## 1. Passport and pre-flight

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 1.1 | Engine id, source and fingerprint in the result, the order and the twin | Done | `test_el_gemelo_guarda_la_serie_y_el_contrato`; UI writes the id into the contract |
| 1.2 | Fingerprint over values, not formatting | Done | `test_la_huella_ignora_el_formato` (int vs float, padded header) |
| 1.3 | Model-free pre-flight: validation, window count, envelope, fingerprint | Done | `test_el_pre_vuelo_cuenta_ventanas_y_detecta_el_orden`; the live tab renders rows/windows/hash before the button |
| 1.4 | Scoring refuses before loading the model | Done | `test_el_pre_vuelo_no_carga_tensorflow`: fresh process, `ok False`, no `tensorflow`/`keras` in `sys.modules` |
| 1.5 | Row cap so a full history cannot freeze the demo | Done | `test_a_table_over_the_row_cap_is_rejected_before_the_model`: `preflight` refuses and names the limit; `score_table` raises before importing Keras |

Files: `app/ui_inference.py`, `app/twin.py`, `app/dashboard_ds02.py`

## 2. Twin registry

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 2.1 | Twin record with id, fingerprint, band, correction, thresholds, series | Done | `test_el_gemelo_guarda_la_serie_y_el_contrato` |
| 2.2 | Registry rejects duplicate ids without mutating the original | Done | `test_registrar_rechaza_duplicados_sin_tocar_el_original` |
| 2.3 | State derived on read from the worst window per cycle | Done | `test_el_estado_se_deriva_de_la_peor_ventana` |
| 2.4 | A threshold change moves the state, not the series | Done | `test_mover_el_umbral_cambia_la_decision_y_no_la_serie` |
| 2.5 | Twins visible in the fleet tab | Done | AppTest: after scoring and registering, the table lists `ESN-DEMO-01`, `R9_HANGAR`, `L_inf 17.34` |
| 2.6 | Replace a twin explicitly, keeping the reported truth | Done | `test_registrar_puede_reemplazar_y_conserva_la_verdad`; the panel shows a replace checkbox instead of failing silently |
| 2.7 | Delete a twin without touching its hangar record | Done | `test_eliminar_saca_un_gemelo_y_deja_el_resto`, `test_el_panel_de_gemelos_documenta_y_elimina` |
| 2.8 | Work order per twin from the stored series | Done | `test_la_orden_de_un_gemelo_sale_de_la_serie_guardada`: cycle 41, `L_inf 8.0`, stored hash, empty `rul_real` in the CSV |

Files: `app/twin.py`, `app/ui_data_loader.py`, `app/dashboard_ds02.py`

## 3. Hangar lifecycle

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 3.1 | Pure state machine with an explicit transition table | Done | `test_avanzar_acepta_solo_la_ruta_declarada`, `test_el_ciclo_completo_vuelve_al_servicio` |
| 3.2 | Entry decision frozen with its thresholds | Done | `test_la_revision_no_reescribe_la_entrada` |
| 3.3 | Queue ordered by urgency | Done | `test_la_cola_ordena_por_urgencia` |
| 3.4 | Panel: open a record, move it, show frozen vs today | Done | `test_el_gemelo_entra_en_la_flota_y_recorre_el_hangar`: abre, congela `L_inf 8.0`, mueve a taller y la cola lo refleja |

Files: `app/hangar.py`, `app/dashboard_ds02.py`

## 4. Truth loop

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 4.1 | Store a reported RUL and cycle per twin | Done | `test_la_verdad_reportada_da_error_y_cobertura` |
| 4.2 | Aggregate coverage and MAE across twins | Done | `test_resumen_agrega_cobertura_y_mae` |
| 4.3 | Panel to report truth | Done | expander wired in the fleet tab |

## 5. Carried-over fixes

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 5.1 | Fleet KPI reads the frame in use | Done | `test_el_macro_rmse_sigue_a_la_lectura_en_uso` (4.90 raw vs 4.86 corrected) |
| 5.2 | Work orders cite the evaluated window | Done | `start_index` and window index asserted in both orders |
| 5.3 | Coverage fixed per band source | Done | `test_la_cobertura_se_mide_por_fuente_de_banda` (both 1.0 on test) |

## 6. Verification

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 6.1 | Full suite | Done | `python -m pytest tests -q` → **138 passed**, exit 0 |
| 6.2 | Evidence gate unchanged | Done | `freeze_rules_evidence.py` → exit 0, coverage 0.9012 |
| 6.3 | Real server | Done | `streamlit run` → `/_stcore/health` 200, process stopped |
| 6.4 | End-to-end demo path | Done | AppTest: score → register → twin in the fleet with derived state |
| 6.5 | Twin panel exercised, not just rendered | Done | `test_el_panel_de_gemelos_documenta_y_elimina`, `test_reemplazar_el_gemelo_desde_la_pestana_en_vivo` (checkbox + replace keeps the truth) |
