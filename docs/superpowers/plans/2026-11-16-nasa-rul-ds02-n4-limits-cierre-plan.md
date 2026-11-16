# NASA-RUL-DS02 — N4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build NotebookLM notebook **N4 — "Defensa DS02 · N4 — Límites y cierre"** that captures the system's boundaries (S27), final summary (S28), the missing slides from N1/N2 (05, 06, 11), the conceptual matrix (C09), and generates a slide deck (PDF) + explainer video (classic style) for the defense presentation.

**Architecture:** 
- N4 completes the arc that N1/N2 left open: after the model and metrics (N2), we land the three "separador" slides (S05 error asimétrico, S06 separador datos, S11 separador modelos) that mark transitions, plus S22/S27/S28 that frame what the system does not do and the closing.
- It also carries C09 (SAA / PIA / MIA evidence matrix, 19 indicators) so the defense can answer "where is this?" per subject.
- Content sources are the vault notes themselves; the deck is the slide narrative (not a re-teaching of the model), so the artifacts are lighter than N1/N2.
- Same pipeline as N1/N2: `notebook_create` → `source_add` (text mode via local HTTP serve, because `source_add(file, path=...)` is blocked without `NOTEBOOKLM_MCP_ALLOWED_ROOTS`) → `studio_generate(slide-deck, presenter)` → `studio_generate(video, classic)` → `studio_download`.

**Tech Stack:** NotebookLM v0.8.6 (profile `default`, account `mikel500500500@gmail.com`, `output_language: es`, tier 4), Python local `http.server` for serving vault notes as text sources, Markdown source notes from `MLProyectVault/vault-defensa/presentacion/`.

**Spec:** `docs/superpowers/plans/2026-11-16-nasa-rul-ds02-n3-decision-action-plan.md` (companion). Session artifact store: `engram` (Engram-backed; dispatcher not applicable). Delivery: direct inline. Conversation language: Spanish. Artifacts (decks, videos, notes) in Spanish, matching N1/N2.

## Global Constraints

- NotebookLM server: version 0.8.6, authenticated, `output_language: es` (not default), `source_limit: 100`, `notebook_limit: 200`.
- `source_add(source_type="file", path=...)` is **blocked** in this environment (no `NOTEBOOKLM_MCP_ALLOWED_ROOTS`). Serve vault notes over local `http.server` and add them as `text` sources, exactly like N1/N2 (per memory #3054).
- `slide-deck` accepts only `deck_format` (`presenter`) and `deck_length` (`default`). `video` accepts only `video_format` (`explainer`), `style` (`classic`), `style_prompt`, `video_format` — **not** `professional` nor `detail` (per memory #3054).
- Both decks/vídeos already shipped in N1/N2 include a known cosmetic defect: N2's last slide carries a decorative "MLFLOW RUN LOGS" panel with per-run metrics (4.340 / 4.335 / 4.350) not in the manifest. Do not project it without regenerating; the canonical anchor figures are 4.338 / 4.333 ± 0.040 / 3.227 MAE / 0.9461 R² / 5.0153 macro / 17 runs.
- Output language for all generated technical artifacts (deck copy, video script) is Spanish, neutral/professional register.
- No GitHub mutation, no push, no PR in this work; delivery is ordinary repository policy.
- Time budget: 15 min with corte seco; S27 and S28 are 35 s and 5 s respectively — do not inflate.
- Engram writes: after each task, `mem_save` with `project: "nasa-rul-ds02"`, topic `defensa/notebooklm-n4`. Never claim delivery from a memory save alone.

## Review Focus

1. **Per-run MLflow panel regression:** any deck that cites 4.340 / 4.335 / 4.350 as vigent figures must be regenerated; the canonical anchor is 4.338 / 4.333 ± 0.040 / 3.227 / 0.9461 / 5.0153 / 17 runs.
2. **Source count drift:** N4 must carry every note it promises (S05, S06, S11, S22, S27, S28, C09). A missing source silently shrinks the notebook's answers.
3. **`active:false` honesty:** S25 says the n8n flow is inactive by design; the deck must not claim production activation.
4. **15 vs 20 minute conflict:** the vault notes 15 min con corte seco but the guion sums 18:37; the plan must not resolve the conflict silently.
5. **`data/processed/` unversioned:** S27 declares this as a limit; the deck must keep it as a declared limit, not "trabajo futuro".

---

### Task N4-1: Create the notebook and add the nine sources

**Files:**
- Create: none (NotebookLM-side only)
- Modify: `docs/superpowers/plans/2026-11-16-nasa-rul-ds02-n4-limits-cierre-plan.md` (evidence appended)

**Interfaces:**
- Consumes: vault notes at `MLProyectVault/vault-defensa/presentacion/` (S05, S06, S11, S22, S27, S28) and `MLProyectVault/vault-defensa/presentacion/conceptos/09-saa-pia-mia.md`; anchor figures from `11-TRIBUNAL/103-cifras-y-lista-negra.md`.
- Produces: one notebook titled `Defensa DS02 · N4 — Límites, cierre y rúbrica` with 7 text sources (S05, S06, S11, S22, S27, S28, C09).

- [ ] **Step 1: Create the notebook**

```js
await tools.notebooklm.notebook_create({ title: "Defensa DS02 · N4 — Límites, cierre y rúbrica" })
// expect: { notebook_id: "<new-uuid>", title: "Defensa DS02 · N4 — Límites, cierre y rúbrica" }
```

- [ ] **Step 2: Serve the vault notes over local HTTP and add each as a text source**

Start `python -m http.server` rooted at `MLProyectVault/vault-defensa/presentacion/`, then for each note:

```js
await tools.notebooklm.source_add({ notebook: "<notebook_id>", source_type: "text", title: "<note title>", text: "<note body, ## Flashcards and ## Conexiones stripped>" })
```

Notes and titles, in order: `05-error-asimetrico` → "S05 · Equivocarse tarde cuesta más"; `06-separador-datos` → "S06 · Separador · Datos"; `11-separador-modelos` → "S11 · Separador · Modelos"; `22-separador-decision` → "S22 · Separador · Decisión"; `27-limites` → "S27 · Lo que este sistema no hace"; `28-cierre` → "S28 · Fin · Preguntas"; `conceptos/09-saa-pia-mia` → "C09 · SAA, PIA y MIA".

- [ ] **Step 3: Verify the source count is 7**

```js
await tools.notebooklm.source_list({ notebook: "<notebook_id>", detail: "compact" })
// expect: 7 entries, all status_label "ready"
```

- [ ] **Step 4: Commit the evidence**

```bash
git add docs/superpowers/plans/2026-11-16-nasa-rul-ds02-n4-limits-cierre-plan.md
git commit -m "docs: plan NotebookLM N4 limites y cierre"
```

---

### Task N4-2: Generate the slide deck (PDF, presenter format)

**Files:**
- Create: `MLProyectVault/vault-defensa/presentacion/notebooklm/N4/deck-N4-limites-y-cierre.pdf`

**Interfaces:**
- Consumes: `<notebook_id>` from N4-1.
- Produces: `deck-N4-limites-y-cierre.pdf` (presenter, default length).

- [ ] **Step 1: Generate the deck**

```js
await tools.notebooklm.studio_generate({ notebook: "<notebook_id>", artifact_type: "slide-deck", deck_format: "presenter", deck_length: "default", language: "es", instructions: "Presentación de cierre de la defensa DS02. Estructura: (1) transición desde la decisión, (2) los seis límites del sistema: determinismo CPU, coste AOG supuesto, n8n inactivo por diseño, SHAP agregado, transferencia no garantizada, data/processed no versionado, (3) los dos campeones: E2 7,721 en fila y el híbrido C 4,338 en ventana, (4) la matriz SAA/PIA/MIA: qué evidencia pide cada asignatura y dónde está, (5) cierre: preguntas sin abrir respaldo. No incluir paneles decorativos de logs MLflow con métricas por run. Cifras canónicas: 4.338, 4.333 ± 0.040, 3.227 MAE, 0.9461 R², 5.0153 macro, 17 runs." })
// expect: { task_id: "<id>" }
```

- [ ] **Step 2: Poll until complete**

```js
await tools.notebooklm.studio_status({ notebook: "<notebook_id>", task_id: "<task_id>" })
// expect: is_complete: true, url present
```

- [ ] **Step 3: Download the PDF**

```js
await tools.notebooklm.studio_download({ notebook: "<notebook_id>", artifact_type: "slide-deck", path: "MLProyectVault/vault-defensa/presentacion/notebooklm/N4/deck-N4-limites-y-cierre.pdf", output_format: "pdf" })
```

- [ ] **Step 4: Verify the file exists and is non-empty**

```bash
ls -la MLProyectVault/vault-defensa/presentacion/notebooklm/N4/deck-N4-limites-y-cierre.pdf
# expect: file present, size > 0
```

- [ ] **Step 5: Commit**

```bash
git add MLProyectVault/vault-defensa/presentacion/notebooklm/N4/deck-N4-limites-y-cierre.pdf
git commit -m "feat: deck N4 limites y cierre DS02"
```

---

### Task N4-3: Generate the explainer video (classic style)

**Files:**
- Create: `MLProyectVault/vault-defensa/presentacion/notebooklm/N4/video-N4-limites-y-cierre.mp4`

**Interfaces:**
- Consumes: `<notebook_id>` from N4-1.
- Produces: `video-N4-limites-y-cierre.mp4`.

- [ ] **Step 1: Generate the video**

```js
await tools.notebooklm.studio_generate({ notebook: "<notebook_id>", artifact_type: "video", video_format: "explainer", style: "classic", language: "es", instructions: "Vídeo explicativo de cierre de la defensa DS02. Recorrido: los seis límites que acotan lo que se puede afirmar, los dos campeones por grano (fila 7,721 y ventana 4,338), la matriz de evidencia SAA/PIA/MIA con sus 19 indicadores, y el cierre que remite al respaldo (cuadernos, sensores, residuo, rúbrica, MLflow, ejecuciones n8n). Tono didáctico, ritmo pausado, 6-10 minutos." })
// expect: { task_id: "<id>" }
```

- [ ] **Step 2: Poll until complete**

```js
await tools.notebooklm.studio_status({ notebook: "<notebook_id>", task_id: "<task_id>" })
// expect: is_complete: true, url present
```

- [ ] **Step 3: Download the MP4**

```js
await tools.notebooklm.studio_download({ notebook: "<notebook_id>", artifact_type: "video", path: "MLProyectVault/vault-defensa/presentacion/notebooklm/N4/video-N4-limites-y-cierre.mp4" })
```

- [ ] **Step 4: Verify the file exists and is non-empty**

```bash
ls -la MLProyectVault/vault-defensa/presentacion/notebooklm/N4/video-N4-limites-y-cierre.mp4
# expect: file present, size > 0
```

- [ ] **Step 5: Commit**

```bash
git add MLProyectVault/vault-defensa/presentacion/notebooklm/N4/video-N4-limites-y-cierre.mp4
git commit -m "feat: video N4 limites y cierre DS02"
```

---

### Task N4-4: Update the README index and close

**Files:**
- Modify: `MLProyectVault/vault-defensa/presentacion/notebooklm/README.md`

**Interfaces:**
- Consumes: `<notebook_id>` from N4-1, deck path and video path from N4-2/N4-3.
- Produces: updated README with N4 row.

- [ ] **Step 1: Add the N4 row to the Notebooks table**

```markdown
| N4 | Defensa DS02 · N4 — Límites, cierre y rúbrica | `<notebook_id>` | 7 |
```

- [ ] **Step 2: Add the N4 row to the Archivos descargados table**

```markdown
| N4 | `N4/deck-N4-limites-y-cierre.pdf` | `N4/video-N4-limites-y-cierre.mp4` |
```

- [ ] **Step 3: Update the Cobertura section**

```markdown
- **N4** — slides 05, 06, 11, 22, 27, 28. El error asimétrico, los separadores de acto, los seis límites, los dos campeones y la matriz SAA/PIA/MIA.
```

- [ ] **Step 4: Commit**

```bash
git add MLProyectVault/vault-defensa/presentacion/notebooklm/README.md
git commit -m "docs: index N4 in notebooklm README"
```

- [ ] **Step 5: Save to Engram**

```
mem_save(project="nasa-rul-ds02", type="config", topic_key="defensa/notebooklm-n4",
  title="NotebookLM N4 creado con deck y vídeo",
  content="N4 (7 fuentes: S05, S06, S11, S22, S27, S28, C09) creado en NotebookLM con deck PDF presenter y vídeo explainer classic. Notebook ID: <notebook_id>. Archivos en presentacion/notebooklm/N4/.")
```

---

## Self-Review

**1. Spec coverage:** The plan covers every section of the spec — notebook creation (N4-1), deck (N4-2), video (N4-3), README index (N4-4). The global constraints (anchor figures, `active:false` honesty, 15 vs 20 min conflict, `data/processed/` limit) are pinned in the generation instructions of N4-2/N4-3.

**2. Step scan:** Every step is one action with a checkable result. No step carries more than one reasonable thing. Code blocks appear only for exact tool calls whose signatures the executor cannot guess.

**3. Type consistency:** `<notebook_id>` is the only cross-task token; it is defined in N4-1 Step 1 and consumed in N4-2/N4-3/N4-4 consistently.

**4. Review Focus:** Each of the five Review Focus lines is pinned: (1) per-run MLflow panel → pinned in N4-2 Step 1 instructions ("No incluir paneles decorativos de logs MLflow"); (2) source count drift → pinned in N4-1 Step 3; (3) `active:false` honesty → pinned in N4-2 instructions ("n8n inactivo por diseño"); (4) 15 vs 20 min conflict → pinned in Global Constraints and the 5 s / 35 s slide times; (5) `data/processed/` unversioned → pinned in N4-2 instructions.

**5. Proportion:** The plan is roughly the same length as the spec section it implements. No code block exceeds a single tool call; bodies are signatures and exact instructions.

---

*Created: 2026-11-16*