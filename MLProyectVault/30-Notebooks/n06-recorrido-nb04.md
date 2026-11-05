---
tipo: notebook
status: sin-estudiar
tags:
  - nb04
  - bilstm
  - oof
  - beta
---

# NB04 — BiLSTM, OOF y beta

> [!abstract] En una frase
> La BiLSTM triple pooling aprende la trayectoria, el OOF agrupado calibra cuánta red sustituye el meta y beta sale 1.00: el meta manda.

## Antes de empezar

30 celdas. Requiere la base de NB01–NB03 y `src/ds02_rul` 4.1.0. Lo pesado es el entreno BiLSTM (EPOCHS 22) más el OOF de 3 folds (EPOCHS_OOF 15 por fold). Tarda en CPU; los prints de OOF y conformal se materializan al ejecutar.

## Recorrido celda a celda

| Bloque | Qué entra | Qué hace | Qué sale |
|---|---|---|---|
| Entreno seed 42 | base adaptada | BiLSTM triple pooling + early stopping en holdout-16 | curva de pérdida, 154 253 params |
| OOF agrupado | base + 6 motores dev | `oof_base_predictions` por motor, 3 folds | predicciones fuera de fold + `selection` |
| `select_beta_grouped` | OOF | ajusta el meta por fold | beta 1.00, folds [1.00, 1.00, 0.00], mediana 1.0 |
| Meta en vivo | holdout-16 | ridge + LGBM sobre `[p_lstm, p_lgb]`, sin `cyc_norm` | pesos del juez (se fía más del árbol) |
| Híbrido + EMA5 | test 11/14/15 | `HybridStackingEnsemble` + EMA causal span 5 | scatter real vs predicho |
| Banda | `selection['oof_calib']` | `fit_conformal` 90% | intervalo honesto por bin |

## Las 5 celdas que importan

1. Entreno: la curva train/val juntas hasta el corte (sin brecha = sin overfit grosero).
2. OOF: `beta` por folds con su spread; el 0.00 es información, no ruido ([[c10-oof-y-validacion-agrupada]]).
3. Meta en vivo: solo holdout-16, sin `cyc_norm` a propósito ([[c19-ablacion-cyc-norm]]).
4. Pesos Ridge: la barra más alta es la rama en la que más confía el juez.
5. Scatter vivo: la nube pegada a la diagonal; el RMSE resume, el por-motor explica.

## Qué NO hace este cuaderno

No multisemilla (eso es NB05), no compara contra clásicos (eso fue NB02), no congela el artefacto (eso es NB06). NB04 produce beta y el ensamble en memoria.

## Conexiones

- OOF y beta: [[c10-oof-y-validacion-agrupada]] · [[s09-oof-y-beta]] · cyc_norm: [[c19-ablacion-cyc-norm]] · EMA: [[c13-ema-causal]] · cifras: [[e00-cifras-autoritativas]]

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «En el 04 la red aprende la trayectoria, el OOF calibra cuánta red le creemos al meta, y beta sale uno: el juez sustituye a la red del todo».

## Flashcards

> [!question]- ¿Qué produce NB04 y qué deja para NB05?
> Beta calibrado (1.00), meta ajustado en holdout-16 y ensamble en memoria con su banda; deja la evidencia multisemilla y la congelación del artefacto para NB05/NB06.

> [!question]- ¿Por qué el meta de NB04 no mira cyc_norm?
> Para no aprender un prior de nivel de vida: solo reconcilia `[p_lstm, p_lgb]`; el reloj es de la red, no del juez ([[c19-ablacion-cyc-norm]]).
