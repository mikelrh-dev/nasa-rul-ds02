---
tipo: sistema
status: consolidado
tags:
  - shap
  - app
  - explicabilidad
---

# SHAP y app de clase — la decisión con su porqué

> [!abstract] En una frase
> Cada predicción lleva su descomposición SHAP por feature y la app la muestra junto a la decisión APTO/INSPECCIÓN/HANGAR.

## Contrato

| Entra | Sale |
|---|---|
| Modelo entrenado + caso nuevo | Predicción RUL + decisión por reglas + explicación por feature |

## Cómo está implementado

| Pieza | Dónde | Qué hace |
|---|---|---|
| SHAP producción (híbrido) | `src/ds02_rul/shap_c.py` sobre LGBM 93 feats | TreeExplainer global top-10 + waterfall local; explica rama tabular, no BiLSTM ni stacking |
| SHAP clase XGB | `src/clase/shap_clase.py` → `models/shap_xgb_top.joblib` | TreeExplainer fondo 200 train, 200 validación fold-0 nunca test |
| SHAP clase E2 | `src/clase/shap_clase_e2.py` | PermutationExplainer MLP campeón fila, fondo 200 fold-0, budget 2·n+1 |
| Caso nuevo | `predict_caso_nuevo` (`pipeline_clase.py:43`) | del formulario a la RUL en un paso |
| Reglas | `src/mia/` (6 con prioridad + seguridad R1) | RUL → APTO / INSPECCIÓN / HANGAR |
| App | `app/` + `app/dashboard_ds02.py` | métricas, caso nuevo, panel SHAP, modo historia |

La captura de la app va en `resultados/` y se referencia en los README (P3 del plan de rúbrica).

## Conexiones

- Mecanismo SHAP e IA débil: [[c21-shap-e-ia-debil]] · pipeline: [[s16-pipeline-de-clase]] · reglas: [[s13-capa-de-reglas-y-decision]] · despliegue DSS: [[s14-app-y-despliegue]]

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Ningún HANGAR sale sin su porqué: la app muestra la RUL, la regla que disparó y las features que más pesaron según SHAP».

## Flashcards

> [!question]- ¿Qué muestra la app por cada decisión y de dónde sale cada parte?
> RUL (modelo), decisión (reglas `src/mia/`), explicación (SHAP de `shap_clase.py`): las tres capas visibles juntas, auditables por separado.
