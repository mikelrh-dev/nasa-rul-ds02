---
tipo: notebook
status: sin-estudiar
tags:
  - nb06
  - bundle-c
  - produccion
  - comparativa
---

# NB06 — Evaluación en producción y comparativa

> [!abstract] En una frase
> El bundle C se evalúa como se despliega (ventana de test, una lectura), se compara por grano y se cierra con la tabla final: 4.338 en disco, 4.322 de media.

## Antes de empezar

61 celdas. Requiere todo lo anterior: es el cierre, no un experimento. Lo pesado es el entreno vivo seed 42 (curva de pérdida) + OOF; las celdas de banda y residuales son ligeras pero dependen de esos estados.

## Recorrido celda a celda

| Bloque | Qué entra | Qué hace | Qué sale |
|---|---|---|---|
| Entreno C vivo (seed 42) | base adaptada | `run_seed` completo | curva de pérdida + `test`, `p_ens` en memoria |
| OOF + beta | `raw` | `oof_base_predictions` + `select_beta_grouped` | print OOF (n_ventanas, beta, span) |
| Scatter vivo | `p_ens` vs `test['y']` | nube real vs predicho | la diagonal manda; RMSE 4.338 resume |
| Pesos del bundle instalado | `models/ensemble.joblib` | `load_ensemble` (verifica SHA) + Ridge | reparto 28/72, beta 1.00, EMA span 5 |
| Componentes | CSV comparativa | cascada 7.067→5.654→5.618→**4.338** | ninguna etapa sobra |
| Conformal 90% | `selection['oof_calib']` | `fit_conformal` | print calibración (n_calib, cobertura objetivo) |
| Residuales | `p_ens`, `test` | RMSE + diagnóstico | print residuales |
| Comparativa por grano | tabla final | fila vs ventana, campeones separados | MLP E2 7.72 · Híbrido-C 4.338 |

## Las 5 celdas que importan

1. Curva de pérdida seed 42: train y val juntas hasta el corte.
2. Scatter vivo: la nube en la diagonal en todo el rango (sin tramo ciego).
3. Pesos del instalado: se carga por el mismo camino que la app (`load_ensemble` verifica SHA).
4. Cascada de componentes: cada etapa recorta RMSE y NASA sobre las mismas ventanas.
5. Comparativa por grano: la tabla que el tribunal va a mirar primero.

## Qué NO hace este cuaderno

No inventa modelos nuevos: evalúa el C como se despliega y lo compara con lo ya medido. Es evidencia, no experimento.

## Conexiones

- Bundle C: [[s20-ensemble-adaptado-y-bundle-c]] · tabla y grano: [[s19-tabla-final-y-grano]] y [[c15-grano-fila-vs-ventana]] · multiseed: [[c20-multisemilla-y-ruido]] · cifras: [[e00-cifras-autoritativas]]

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «El 06 no entrena nada nuevo: coge el bundle instalado por el mismo camino que la app, lo mide en la ventana de test de una sola lectura y lo pone en su tabla con su grano: 4.338».

## Flashcards

> [!question]- ¿Por qué NB06 carga el bundle con load_ensemble en vez de usar el de memoria?
> Porque es el mismo camino que la app (con verificación SHA): mide lo desplegado, no lo recordado. Si memoria y disco discrepan, manda el disco.

> [!question]- ¿Qué cierra la tabla comparativa de NB06?
> Un modelo por grano con su campeón: MLP E2 (7.72, fila) e Híbrido-C (4.338, ventana); la cascada 7.067→5.654→5.618→4.338 demuestra que cada etapa aporta.
