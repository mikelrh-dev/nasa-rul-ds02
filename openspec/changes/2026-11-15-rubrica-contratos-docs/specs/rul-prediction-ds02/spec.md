# Spec: Documentation and rubric contracts (no n8n)

**Capability:** `rul-prediction-ds02`
**Change:** `2026-11-15-rubrica-contratos-docs`

## MODIFIED Requirements

### Requirement: Multiseed evidence reconciliation

The system MUST reconcile multiseed citations without retraining. Seed 42 SHALL
come from `models/ds02_manifest.json` (RMSE 4.338 / MAE 3.227 / R2 0.9461 /
NASA 2336.2). Seeds 7 and 123 SHALL come from
`resultados/bundle_c_multiseed.csv` (`7=4.371`, `123=4.291`). The vigente
aggregation SHALL read RMSE `4.333 ± 0.040` and NASA `2335.1 ± 28.7` (sample
standard deviation, `ddof=1`). The value `4.324 ± 0.107 / NASA 2341.0 ± 54.1`
SHALL remain labelled historical. The value `4.368 ± 0.053 / NASA 2355.2 ± 24.6`
SHALL be labelled obsolete and MUST NOT be cited as vigente. Citations in
`README.md`, `README.en.md`, `AGENT.md`, `LEARNING_LOG` and
`MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md` MUST follow these
figures. NASA is a SUM and the DS02 path applies no 125-cycle clamp.

#### Scenario: Three-row table matches manifest

- GIVEN `resultados/bundle_c_multiseed.csv` with `7=4.371` and `123=4.291`
- AND the manifest row for seed 42
- WHEN the multisemilla table is read
- THEN the three rows are `[42, 7, 123]` with `4.338 / 4.371 / 4.291`
- AND the mean is `4.333 ± 0.040` (sample std)
- AND `4.324 ± 0.107` appears only as historical
- AND `4.368 ± 0.053` does not appear as vigente.

#### Scenario: Citations agree

- GIVEN the deployed documentation set
- WHEN the multiseed figures are grepped
- THEN every citation reads the vigente figures
- AND no notebook output is edited.

## ADDED Requirements

### Requirement: README rubric anchors

`README.md` MUST contain the section "Qué hemos construido" and explain that the
system is a weak AI by contrasting it with a strong AI, and that the learning is
supervised regression by contrasting it with unsupervised learning. The model
table MUST include a training-time column.

#### Scenario: Anchors present

- GIVEN the root `README.md`
- WHEN read
- THEN "Qué hemos construido" exists
- AND "IA fuerte" and "no supervisado" both appear
- AND the model table carries a time column.

### Requirement: Published thresholds match the decision code

Documentation MUST state the decision thresholds `apto=25` / `hangar=20`,
matching `app/lib/_constantes.py` and ADR-013. Any historical `30/25` mention
MUST be labelled superseded.

#### Scenario: Thresholds consistent

- GIVEN the code defaults `DEFAULT_AIRWORTHY=25.0` and `DEFAULT_AOG=20.0`
- WHEN the README and the English README are read
- THEN both state `25/20`
- AND neither instructs `≥30 -> APTO`.

### Requirement: Direct imports stay pinned

Every third-party module imported directly by `src/` or `scripts/` MUST be pinned
in `requirements.txt` and mirrored in `pyproject.toml`. `pyarrow`, imported by
`src/clase/dataset_clase.py`, MUST be pinned to the installed version.

#### Scenario: PyArrow pinned

- GIVEN `import pyarrow` in the dataset builder
- WHEN the dependency manifests are read
- THEN `requirements.txt` contains `pyarrow==<installed>`
- AND `pyproject.toml` mirrors the same pin.

### Requirement: Notebook instrumentation coverage

Every `notebooks/0*.ipynb` MUST satisfy the MLflow header contract: cell 0 sets
`MLFLOW_ALLOW_FILE_STORE`, `TF_ENABLE_ONEDNN_OPTS` before any TensorFlow import and
calls `setup_mlflow()`; no later cell sets `TF_ENABLE_ONEDNN_OPTS`; each notebook
logs a live run through `log_live_run` and persists timings through
`persist_timings`. The static contract test count MUST equal the number of
matching notebooks.

#### Scenario: NB00 complies

- GIVEN `notebooks/00_datos.ipynb`
- WHEN the static contract tests run
- THEN cell 0 carries the MLflow and TF environment setup
- AND no later cell mentions `TF_ENABLE_ONEDNN_OPTS`
- AND the notebook body references `log_live_run` and `persist_timings`
- AND `len(NOTEBOOKS) == 8`.

> Nota local (fuera de git): la corrección de
> `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md` queda en el vault
> personal, que está ignorado por git; el test asociado se salta si no existe.
