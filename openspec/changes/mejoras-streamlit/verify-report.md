# Verify report: mejoras-streamlit

**Date:** 2026-11-03
**Change:** `mejoras-streamlit`

## Verification command

`python -m pytest tests/test_dss_ui.py tests/test_live_eval.py tests/test_rules_gate.py -q`

## Result

`78 passed, 3 skipped` (exit 0). Additional checks:

- `tests/test_mejoras_streamlit.py`: `11 passed` (RED first, then GREEN).
- `tests/test_dss_interaction.py::test_el_informe_de_auditoria_es_un_pdf_descargable`: updated
  to press `btn_gen_pdf` first, then `1 passed`.
- Combined bag: `89 passed, 3 skipped`.

## Scope checked

- `grep -c "@st.fragment" app/dashboard_ds02.py` = 6 (sandbox, muro + 4 tabs).
- `@st.cache_data` on `_sha256_cached` (dashboard + ui_data_loader) and
  `_informe_pdf_cached`.
- Single `shap_panel`; no `/tmp/shap_waterfall.png`; `ui_shap` uses `tempfile`
  + Plotly `shap_waterfall_fig`.
- `PRUEBAHANGAR` removed from `app/registros_flota.json`; banner counter counts
  wall cards (`hangar_en_muro / _total_muro`).
- PDF behind generate button (`btn_gen_pdf` / `_pdf_generado`).
- `help=` on every `multiselect`/`slider`/`selectbox`; SHA + contract metrics
  next to new-case prediction; `score_table(timeout_s=120.0)`; friendly
  `pip install shap` message on `ImportError`.

## Full gate

`python scripts/verify_gate.py` → `6 failed, 251 passed` before the fix;
`5 failed` of those are pre-existing on the clean tree (verified with
`git stash` + re-run of `tests/test_dss_interaction.py`: `5 failed` without
the change, all expecting the removed `Modo historia` UI). The 6th (audit PDF)
was this change's intentional behaviour move and is fixed by the updated test
above. The change introduces no new failures in the target suite.
Frozen artifacts untouched (`models/`, `app/cache/` byte-identical).
