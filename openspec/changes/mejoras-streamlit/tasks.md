# Tasks: Streamlit P0+P1+P2 improvements

**Change:** `mejoras-streamlit`
**Status:** Implemented

| # | Task | Status | Acceptance |
|---|---|---|---|
| 1.1 | Create SDD change dir + artifacts | Done | `openspec/changes/mejoras-streamlit/` exists |
| 2.1 | Cache audit hash with `@st.cache_data` | Done | grep shows `_sha256_cached` + `@st.cache_data`; `artifact_hash_check` uses it; pytest target suite green |
| 2.2 | Cache + on-demand PDF | Done | grep shows `@st.cache_data` on PDF builder; PDF block generates only after button; `python -m pytest tests/test_dss_ui.py -q` green |
| 2.3 | Fragment each tab body | Done | `grep -c "@st.fragment" app/dashboard_ds02.py` >= 6 (3 tab + sandbox + muro + existing); `ast.parse` passes; AppTest tests green |
| 3.1 | Single `shap_panel` | Done | `grep -c "def shap_panel" app/dashboard_ds02.py` == 1; both old SHAP blocks call it; suite green |
| 3.2 | Remove `/tmp/shap_waterfall.png` | Done | `grep -rn "shap_waterfall.png" app/` shows no `/tmp` path; `ui_shap` uses `tempfile`; Plotly fig helper exists |
| 3.3 | Clean `PRUEBAHANGAR` + align banner vs wall | Done | `elements` in `app/registros_flota.json` has no `PRUEBAHANGAR`; banner metric uses wall numerator/denominator; no `Además, **.*motor(es) de los registrados` caption |
| 3.4 | PDF only on download press | Done | PDF block shows generate button pattern; no unconditional `_informe_auditoria_pdf(...)` call in render path |
| 4.1 | `help=` on multiselect/slider/selectbox | Done | script checks every `st.multiselect/slider/selectbox` call has `help=` |
| 4.2 | Reproducibility SHA + contract | Done | new-case result shows `artefacto_sha256` + window/step metrics |
| 4.3 | `score_table` timeout for 5000 rows | Done | `score_table` signature has `timeout_s`; `tests/test_live_eval.py` green |
| 4.4 | Friendly message when `ui_shap` missing | Done | `ImportError` branch shows `pip install shap` message |
| 5.1 | Full target suite | Done | `python -m pytest tests/test_dss_ui.py tests/test_live_eval.py tests/test_rules_gate.py -q` green |
