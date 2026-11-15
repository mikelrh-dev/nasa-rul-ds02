# Design: MLflow live in notebooks + timings

**Change:** `mlflow-live-notebooks`

```mermaid
flowchart LR
    subgraph nb [notebooks nb01_nb07]
        hdr[cell0_header]
        logcell[live_log_cell]
        hdr --> logcell
    end
    subgraph live [mlflow_live]
        setup[setup_mlflow]
        logrun[log_live_run]
        persist[persist_timings]
    end
    subgraph pipe [pipeline]
        rs[run_seed]
        abl[ablation_table]
        oof[oof_base_predictions]
    end
    subgraph store [mlruns]
        hist[historic 13 fuente historico]
        liverun[live runs fuente live_notebook]
    end
    logcell --> logrun
    logrun -->|log_param log_metric| store
    logrun --> persist
    persist --> files[(tiempos json csv)]
    rs -->|perf_counter timings| logcell
    abl -->|timing rows| logcell
    oof -->|fold timing| logcell
    classDef nb fill:#dbeafe,stroke:#1d4ed8
    classDef live fill:#fef3c7,stroke:#d97706
    classDef pipe fill:#dcfce7,stroke:#16a34a
    classDef store fill:#fee2e2,stroke:#dc2626
```

## Decisions

1. **Single helper module** `src/ds02_rul/mlflow_live.py` (rejected: inline
   `mlflow.start_run` per notebook — 7 copies drift; helper is testable).
   `log_live_run` uses `MlflowClient.log_param`/`log_metric` directly, tags
   `fuente=live_notebook`; `clean_metric` drops NaN/inf.
2. **Notebooks patched by script** `scripts/patch_mlflow_live_notebooks.py`
   (rejected: hand-edit 7 ipynb — violates build-output rule; script is
   idempotent and re-runnable; `build_07` synced so regeneration keeps it).
3. **Backfill historic-only by tag filter** (rejected: separate experiment —
   breaks the “one table from MLflow” rubric; tag filter keeps one store).
4. **`puente_c` NaN refreshed, not removed** (rejected: returning `None`
   would break `f"{out['t_lgb']:.1f}"` consumers) — legacy NaN keys stay,
   new `timing` dict carries `None`s + `fuente=bundle_congelado`.

## Known limitations
- Notebook log cells are written but NOT executed in this change; live runs
  only appear when the user re-executes NB01–07.
- NB07 `res` shape is used defensively (params-only run if shape differs).
