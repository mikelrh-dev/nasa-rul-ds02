---
source: learn-teacher
mode: repo
repo: nasa
created: 2026-10-23
---

# LEARNING_LOG — MLProyectVault

Vault de estudio del proyecto DS02 (N-CMAPSS): ensamble híbrido de stacking para RUL.
Mapas, teorías y esquemas en español. El quiz interactivo queda pendiente (vault construido a petición directa, sin fase teach).

## Índice

- [[#Cartografía del repo (2026-10-23)]]
- [[#Plan aprobado — vault MLProyectVault (2026-10-23)]]
- B1: [[01-que-predecimos-rul]] · [[02-reparto-por-motor-y-fuga]] · [[03-baseline-media-train]]
- B2: [[04-prepro-solo-fit-motores]] · [[05-sensor-residualizado-regimen]] · [[06-ventanas-y-cyc-norm]]
- B3: [[07-lightgbm-cuantil]] · [[08-bilstm-triple-pooling]] · [[09-ema-causal]]
- B4: [[10-ablacion-cyc-norm]] · [[11-oof-agrupado]] · [[12-beta-mediana-y-diagnostico]]
- B5: [[13-stacking-hibrido]] · [[14-bandas-conformal]] · [[15-macro-rmse]]
- B6: [[16-multisemilla]] · [[17-regla-del-empate]] · [[18-diagnostico]] · [[19-persistencia-reload]]
- B7: [[20-indice-funciones-y-api]] · [[21-api-datos-e-ingestion]] · [[22-api-ventanas-e-inferencia]] · [[23-api-modelo-bilstm-y-pooling]] · [[24-api-pipeline-y-semillas]] · [[25-api-stacking-interno]] · [[26-api-ensamble-e-intervalos]] · [[27-api-conformal]] · [[28-api-persistencia-y-reload]] · [[29-api-metricas]] · [[30-api-visualizacion]] · [[31-api-residualizador-y-suavizado]]
- B0: [[00-guion-30-segundos]] · [[00-datos-prepro-ventanas]] · [[00-bases-lgbm-bilstm]] · [[00-oof-beta-stacking]] · [[00-ema-conformal-metricas]] · [[00-persistencia-notebooks]] · [[00-cifras-autoritativas]] · [[01-anexo-nb01-celdas]] · [[02-anexo-nb02-celdas]] · [[03-anexo-nb03-celdas]]
- [[#B0 Guion defensa — bloque núcleo (2026-10-26)]]

## Estado actual

- **Modo:** repo · **Tema activo:** proyecto DS02 completo · **Objetivo:** entender conceptos, código y desarrollo de los 3 notebooks para defender el proyecto.
- **Nodos firmes:** ninguno verificado con quiz todavía (pendiente).
- **Siguiente bloque:** B0 — Guion defensa (quiz pendiente, luego B1).

### Perfil del estudiante

- `preferencia_quiz: cada_nodo` · `formato: adaptativo` · `ritmo: normal` · idioma: español.

### Nivel del estudiante

- nivel: sin calibrar (probe pendiente) · evidencia: 0/0.

## Cartografía del repo (2026-10-23)

> [!quote] Estudiante
> Crear el vault MLProyectVault de los 3 notebooks: conceptos, código y desarrollo.

Mapa real del código (todo verificado en archivos):

```mermaid
flowchart LR
    H5[N-CMAPSS_DS02-006.h5] --> LOAD[data.py:load_ds02]
    LOAD --> PREP[features.py:fit_preprocessing]
    PREP --> WIN[features.py:build_windows]
    WIN --> LGBM[pipeline.py:make_lgbm]
    WIN --> BILSTM[model.py:build_champion_bilstm]
    LGBM --> OOF[pipeline.py:oof_base_predictions]
    BILSTM --> OOF
    OOF --> BETA[stacking.py:select_beta_grouped]
    BETA --> ENS[ensemble.py:HybridStackingEnsemble]
    ENS --> CONF[conformal.py:fit_conformal]
    ENS --> SAVE[persistence.py:save_ensemble]
```
Fuente: [[visuals/mlproyect-plan.mmd]]

**Fuentes:** `src/ds02_rul/{data,features,model,pooling,stacking,smoothing,pipeline,conformal,metrics,ensemble,residualizer,persistence,inference}.py` + `notebooks/ds02_ensemble/01`, `02`, `03`.

**Estado tras el bloque:** cartografía completa, 14 módulos leídos. Nodo firme: estructura del repo.

## Plan aprobado — vault MLProyectVault (2026-10-23)

> [!quote] Estudiante
> Plan con bloques y nombres de .md aprobado; crear el vault.

6 bloques, 19 nodos, formato triple (teoría + esquema + quiz pendiente): B1 Protocolo honesto · B2 Prepro y features · B3 Modelos base · B4 Ablación, OOF y beta · B5 Ensamble y conformal · B6 Evidencia y diagnóstico. Visuals: mapa del plan + uno por bloque.

## B0 Guion defensa — bloque núcleo (2026-10-26)

> [!quote] Estudiante
> Necesito entender los .py + los 3 notebooks completos, denso pero sencillo. Amplía el vault.

Carpeta `00-Guion-Defensa/`: 7 núcleo (guion, datos, bases, oof, ema, persistencia, cifras) + 3 anexos celda a celda (NB01 12, NB02 18, NB03 25 códigos) con snippets literales `archivo:línea`, entra/sale/por-qué y frase para contar. Visuals: `guion-defensa-plan.mmd`, `mapa-puente.mmd`, `anexos-celdas.mmd`.

```mermaid
flowchart LR
    GUION[guion 30s] --> DATOS[datos prepro ventanas]
    DATOS --> BASES[bases LGBM BiLSTM]
    BASES --> OOF[OOF beta stacking]
    OOF --> DEC[EMA conformal metricas]
    DEC --> PERS[persistencia notebooks]
    PERS --> CIFRAS[cifras manifiesto]
```
Fuente: [[visuals/guion-defensa-plan.mmd]]

**Fuentes:** `src/ds02_rul/{data:49, features:25/79, model:19, pipeline:46/88/157, stacking:161/184/234, smoothing:14, conformal:28/90, persistence:108/189, metrics:21/45}.py` + NB01/02/03 + `models/ds02_manifest.json` + `EVALUACION_EJECUCION.md`.

**Estado tras el bloque:** B0 creado (10 teorías + 9 esquemas + 3 visuals). Pendiente quiz y `00-Definiciones-del-Autor/` si el estudiante fija frases. Cifras autoritativas: manifiesto 2026-10-26 manda.
