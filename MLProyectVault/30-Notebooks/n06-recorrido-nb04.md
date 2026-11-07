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

32 celdas. Requiere la base de NB01–NB03 y `src/ds02_rul` 4.1.0. Lo pesado es el entreno BiLSTM (EPOCHS 22) más el OOF de 3 folds (EPOCHS_OOF 15 por fold). Tarda en CPU; los prints de OOF y conformal se materializan al ejecutar.

## Recorrido celda a celda

| Bloque | Qué entra | Qué hace | Qué sale |
|---|---|---|---|
| Carga Puente C + OOF en vivo (no "entreno seed 42") | base adaptada MAR T30+ffill + bundle desplegado en `models/` | `puente_c.puente_c()` carga BiLSTM/LGBM ya desplegados, reconstruye ventanas dev/test y calcula OOF en vivo (`select_beta_grouped` + meta en holdout-16) | dev (17450,50,19) · test (6196,50,19) · beta y meta en memoria, sin reentrenar la red |
| OOF agrupado | base + 6 motores dev | `oof_base_predictions` por motor, 3 folds | predicciones fuera de fold + `selection` |
| `select_beta_grouped` | OOF | ajusta el meta por fold | beta 1.00, folds [1.00, 1.00, 0.00], mediana 1.0 |
| Meta en vivo | holdout-16 | ridge + LGBM sobre `[p_lstm, p_lgb]`, sin `cyc_norm` | pesos del juez (se fía más del árbol) |
| Híbrido + EMA5 | test 11/14/15 | `HybridStackingEnsemble` + EMA causal span 5 | scatter real vs predicho |
| Banda | `selection['oof_calib']` | `fit_conformal` 90% | intervalo honesto por bin |
| Sensibilidad EMA10 vs EMA5 (celdas 22-23) | `p_lstm_test` | EMA causal span 3/5/10 sin reentrenar | EMA10 5.574 gana a EMA5 5.618 en esa lectura, pero no se reelige: EMA5 venía fijado y el desplegado usa span 5 |
| Ancho conformal 27.12 (celda 29) | banda enviada fuera de fold | cobertura 100% en test | ancho medio 27.12 ciclos. No es el 26.41 de [[e00-cifras-autoritativas]] (otra lectura de la banda); aquí manda el 27.12 impreso en vivo por NB04 |
| Artefactos `artifacts_c` (celda 30) | meta, banda, `p_ens`, `lo/hi` | guarda `nb2_selection.joblib`, `nb2_conformal.joblib`, `nb2_eval.joblib`, `nb2_p_ens.npy`, `nb2_lo.npy`, `nb2_hi.npy` en `notebooks/artifacts_c/` | lo que el 05 necesita sin reentrenar nada |

## Las 5 celdas que importan

1. Puente C: carga el bundle desplegado y calcula OOF en vivo (sin entreno seed 42 en este cuaderno).
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
