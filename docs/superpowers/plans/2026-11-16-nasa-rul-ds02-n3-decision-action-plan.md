# NASA-RUL-DS02 — N3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build NotebookLM notebook **N3 — "Defensa DS02 · N3 — Decisión y acción"** that captures the decision engine, rule application, webhook flow, SHAP analysis, and generates a slide deck (PDF) + explainer video (classic style) for the defense presentation.

**Architecture:** 
- Decision engine runs two passes: Corrector (B) fixes misaligned rows; Decider (A) applies 8 rules (R1–R7, security priority 10) and selects action based on `L_inf` thresholds (20 hangar / 20–25 inspection / ≥25 approved).
- Input: webhook `POST /ds02/decision`. 
- Streams: JSON versioned (no secrets), no HTTP node, 29 manual executions on 2026‑11‑07 (25 success / 4 error).
- Outputs: 
  - Deck PDF (slide‑deck, presenter format, default length)
  - Videos (explainer, classic style) for N1/N2 patterns → N3 video.
  - SHAP metrics, SHA, RUL band.
- Tools: NotebookLM (Python), streamlit, n8n (4 branches APTO/INSPECCION/HANGAR/FALLBACK), Postgres/Calendar/Gmail/Telegram, HDF5, MLflow.

**Tech Stack:** NotebookLM v0.8.6, Python (pandas, scikit-learn, mlflow), streamlit, n8n, PostgreSQL, Google Sheets, Telegram, HDF5, MLflow Vault.

**Spec References:**
- `MLProyectVault/vault-defensa/presentacion/notebooklm/N1`, `N2`
- `conceptos/07-reglas-y-decision.md`, `08-n8n-y-app.md`, `09-saa-pia-mia.md`
- Slide map S25–S28, deck entries, video files.
- Audit: 19 indicators rubric (110-mapa-indicador-evidencia).

## Global Constraints
- **Account:** `mikel500500500@gmail.com`, tier 4, output_language `es`, output_language_is_default `false`.
- **Limits:** source_limit 100, notebook_limit 200, available true.
- **Env:** `NOTEBOOKLM_MCP_ALLOWED_ROOTS` must be set for `source_add(source_type="file", path=...)` (local repo root allowed).
- **Dry run:** 15 min with cut-seco; current deck sums 18:37 for 20 min.
- **Quota:** 17 MLflow runs (confirmed), 54 PIA tests, 12 carpetas.
- **Data freshness:** MAR/T30 gaps, 1.185 holes (MAR in T30, cruise pattern high); slide 08 covers nulls.
- **No HTTP node:** webhook triggers, no direct API calls.
- **Security:** JSON versioned, no secrets, no public widening without confirmation.

## Review Focus
1. **Source import failure** – dead link / soft‑404 / paywall → expect `error` label; test `source_wait(status="error")`.
2. **Webhook entry invalid** – empty payload → `R1 returns SIN_DECISION`; verify response shape.
3. **Data gaps (MAR)** – missing values treated as noise vs. physical gap; slide 08 explains.
4. **MLflow run count mismatch** – expected 17 runs; verify `resultados/mlflow_runs.json`.
5. **n8n branch activation** – `active:false` safety; confirm HANGAR encodes Postgres→Calendar→Gmail→Telegram.
6. **Deck video missing** – video generation artifact type `video` with `style: classic`; check `studio_generate(artifact_type="video", style="classic")`.
7. **Presentation timing** – total deck duration ~18:37 vs target 20 min; adjust slide timing if needed.

---

### Tasks

#### T3-1: Create notebook N3
- **Create:** `notebook_create({title: "Defensa DS02 · N3 — Decisión y acción"})` → id `0e4cda68-c8c6-4be4-b61e-4a3afd061739`.
- **Modify:** none yet.
- **Test:** `notebook_list()` contains N3 row.
- **Step 1:** Write failing test asserting notebook exists and title matches.
- **Step 2:** Run test → FAIL.
- **Step 3:** Implement `create_notebook()` wrapper (if needed) in `src/nasa/rul_ds02_n3.py`.
- **Step 4:** Run test → PASS.
- **Step 5:** Commit.

#### T3-2: Add decision sources & deck
- **Sources:** 
  - `deck-N3-decision.pdf` (placeholder path `presentacion/notebooklm/N3/deck-N3-decision.pdf`).
  - `video-N3-escalera.mp4` (classic style).
  - `source_add(source_type="file", path="C:/Users/mikel/Desktop/Pruebas/nasa/presentacion/notebooklm/N3/deck-N3-decision.pdf")` (after setting env).
  - `source_add(source_type="file", path="C:/Users/mikel/Desktop/Pruebas/nasa/presentacion/notebooklm/N3/video-N3-escalera.mp4")`.
- **Interfaces:** consumes `notebook_id`, `sources_count`; produces `deck_pdf_path`, `video_path`.
- **Steps:** write test for source addition returning `source_id`; run wait; commit.

#### T3-3: Generate slide deck (PDF) via studio_generate
- **Task:** `studio_generate({notebook: "0e4cda68...", artifact_type: "slide-deck", deck_format: "presenter", deck_length: "default", source_ids: ["<source ids>"], instructions: "...")`.
- **Artifacts:** `presentacion/notebooklm/N3/deck-N3-decision.pdf`.
- **Video:** `studio_generate({notebook: ..., artifact_type: "video", video_format: "explainer", style: "classic", source_ids: [...]}, ...)`.

#### T3-4: Create explainer video
- **Task:** same as above but video artifact.

#### T3-5: Verify deck & video exist & readable
- **Run:** `studio_status(notebook, task_id)` until `is_complete`.
- **Check:** `studio_list(kind="slide-deck")` shows PDF; `studio_list(kind="video")` shows MP4.

#### T3-6: Run integration smoke test (mock webhook)
- **Mock:** POST `/ds02/decision` with `{prediction: 27, band: [19,31]}` → expect `SIN_DECISION`/`RUL` output.
- **Verify:** `chat_status(task_id)` → completed.

#### T3-7: Review & sign off

*(Subsequent tasks for N4 omitted here.)*

---
*Created: 2026-11-16*