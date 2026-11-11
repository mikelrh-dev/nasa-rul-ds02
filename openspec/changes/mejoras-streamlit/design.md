# Design: Streamlit P0+P1+P2 improvements

**Change:** `mejoras-streamlit`
**Status:** Implemented

```mermaid
accTitle: Streamlit P0 P1 P2 caching and fragmentation
accDescr: Four fragment tabs, cached hash and PDF, single SHAP panel.

flowchart TB
    main["dashboard_ds02.py"] --> frag_flota["@st.fragment<br/>tab_flota"]
    main --> frag_motor["@st.fragment<br/>tab_motor"]
    main --> frag_auditoria["@st.fragment<br/>tab_auditoria"]
    main --> frag_casos["@st.fragment<br/>tab_casos"]
    frag_auditoria --> hash_cache["@st.cache_data<br/>_sha256_cached"]
    frag_auditoria --> pdf_cache["@st.cache_data<br/>_informe_pdf_cached"]
    frag_motor --> shap_panel["shap_panel"]
    frag_casos --> shap_panel
    shap_panel --> ui_shap["ui_shap<br/>tempfile + Plotly fig"]
```

## Decisions

- **Fragment shape: inline `with tab` + inner fragment function.**
  Alternative rejected: hoisting tab bodies to top-level functions before
  `st.tabs` — it changes the `tab_*` lookup and risks breaking `st.rerun`
  order. Keeping `with tab_*:` outer and defining the fragment inside it
  preserves rendering targets and session-state order.
- **Hash cache key: path + size + mtime_ns.**
  Alternative rejected: a no-arg `@st.cache_data` hash of the whole file —
  it would serve stale results after the artifact is replaced. The triple
  invalidates exactly when the file changes.
- **PDF cache key: thresholds + SHA + cache signature, not DataFrames.**
  Alternative rejected: passing `windows` / `curves` DataFrames straight to
  `@st.cache_data` — Streamlit hashes frames by value and can error on mixed
  types. Scalar keys are cheap and deterministic; the builder reads globals.
- **SHAP panel: one function, caller-suffixed button keys.**
  Alternative rejected: two independent call sites with the same key — Streamlit
  rejects duplicate widget keys across tabs. `shap_panel(unit, suffix)` keeps
  one definition with unique keys (`btn_shap_<suffix>`,
  `btn_shap_wf_<suffix>` grouped into one button).
- **Waterfall: Plotly first, tempfile fallback.**
  `ui_shap.shap_waterfall_fig(unit)` returns a `go.Figure` from
  `shap_waterfall_data()` (already exact). `shap_waterfall_png(unit,
  out_path=None)` creates a `tempfile.NamedTemporaryFile` when `out_path` is
  `None`. Alternative rejected: keeping a fixed `/tmp` path — it collides on
  shared hosts and leaks state between sessions.
- **Banner alignment: wall = banner.**
  `hangar_en_muro = grounded + derivados_gemelos`; denominator =
  `len(tarjetas_cache) + len(tarjetas_gemelos)`. The separate `Además...`
  caption is removed because its set is now inside the metric itself.
- **Timeout: `score_table(..., timeout_s=...)` with `time.monotonic`.**
  Checked before loading the bundle and after prediction; on expiry it raises
  `TimeoutError` with the row-cap context. The pre-existing `> MAX_FILAS`
  rejection stays the first guard.

## Known limitations

- `@st.fragment` keeps the initial script run rendering all four tabs; the win
  is on interactions (only the owning tab reruns). Evidence: Streamlit docs.
- PDF caching is per-process (`@st.cache_data`): a second Streamlit process
  rebuilds once. Evidence: same docs; acceptable for a single-process app.
- `app/registros_flota.json` is gitignored; removing `PRUEBAHANGAR` is a local
  cleanup, not a tracked diff. The `conftest.py` backup/restore still protects
  it during tests.
