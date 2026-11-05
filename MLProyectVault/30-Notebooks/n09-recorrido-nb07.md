---
tipo: notebook
status: consolidado
tags:
  - nb07
  - shap-c
  - bundle-c
  - explicabilidad
---

# NB07 — SHAP por ramas sobre el bundle C

> [!abstract] En una frase
> Cuaderno fino de 6 celdas que no entrena nada: llama a `ejecutar_shap_c` y explica cada rama del híbrido con su explainer correcto.

## Antes de empezar

6 celdas. Requiere bundle C instalado (`models/ensemble.joblib` + `ds02_manifest.json`). No entrena, no recalibra: solo explica con validación fold-0, nunca test.

## Recorrido celda a celda

| # | Qué entra | Qué hace (.py:línea) | Qué sale |
|---|---|---|---|
| 0 | cwd robusto | fija raíz sin `../` relativo | imports `src` estables |
| 1 | prosa + `ejecutar_shap_c` | declara cuaderno fino | contrato: explicar, no entrenar |
| 2 | `ejecutar_shap_c` | `src/ds02_rul/shap_c.py:216` BiLSTM PermutationSHAP + LGBM TreeExplainer interventional `shap_c.py:289` + meta Permutation ancho real `shap_c.py:298` | `resultados/shap_bundle_C/` barras + waterfall |
| 3 | dump `OUT` | recorre `shap_bilstm/shap_lgbm/shap_meta` | `bar_{rama}.png` verificables |
| 4 | display | `Image/display` por rama | inspección visual en celda |
| 5 | lectura y límites | SHAP describe modelo en val fold-0, no causal, no BiLSTM completo vía Tree | límite escrito, no escondido |

Explainers por rama (`shap_c.py:12-18`): BiLSTM Permutation (Gradient da 3-11, se rechaza), LGBM TreeExplainer 93 feats con fondo reutilizado, meta Permutation sobre `build_meta_Z` ancho real (`shap_c.py:130`). Aditividad `validar_aditividad` (`shap_c.py:117`). Patrón heredado de `src/clase/shap_clase_e2.py` (funciones puras + ejecutora).

## Las 3 celdas que importan

1. Celda 2: el único cómputo — todo pasa por `ejecutar_shap_c`, nada duplicado en el cuaderno.
2. Celda 3-4: artefactos `shap_bundle_C/` + visualización por rama, auditables en disco.
3. Celda 5: límites — SHAP en validación fold-0, no test; describe decisión, no causa.

## Qué NO hace este cuaderno

No toca `train_*`, no ajusta meta/beta, no calibra banda. Si `ensemble.joblib` y manifiesto discrepan, `load_ensemble` falla antes de explicar.

## Si falla algo

Si falta el bundle, revisa `models/ensemble.joblib` + `ds02_manifest.json` (hashes `d6c70142/bf9620a7` en e00). Si falta `shap`, el cuaderno no lo instala: es dependencia `pyproject.toml`.

## Conexiones

- Código: `src/ds02_rul/shap_c.py:216/289/298/130/117` · patrón: `src/clase/shap_clase_e2.py` · sistema: [[s22-shap-y-app-de-clase]] · mecanismo: [[c21-shap-e-ia-debil]] · cifras: [[e00-cifras-autoritativas]]

> [!quote] Di esto en el tribunal
> «En el 07 no entreno nada: ejecuto una función que explica cada rama con su explainer —árbol exacto para LGBM, permutación para BiLSTM y meta— sobre validación, nunca test».

## Flashcards

> [!question]- ¿Por qué tres explainers distintos?
> Tree no cubre stacking ni BiLSTM completo; LGBM va exacto, BiLSTM y meta van por permutación sobre el ancho real.

> [!question]- ¿Qué deja NB07 en disco?
> `resultados/shap_bundle_C/` con barras y waterfall por rama, regenerable vía `ejecutar_shap_c`.
