---
tipo: sistema
status: sin-estudiar
tags:
  - lightgbm
  - base-adaptada
  - puente
  - saa
---

# LGBM adaptada — el puente honesto al bundle C

> [!abstract] En una frase
> El mismo LightGBM cuantil 0.35, reentrenado sobre la base con nulos tratados: demuestra que la imputación no degrada antes de construir el híbrido encima.

## Contrato

| Entra | Sale |
|---|---|
| Base adaptada (MAR T30 + ffill, `construir_raw_adaptado`) | LGBM cuantil 7.067 + prototipo honesto del bundle C |

## Cómo está implementado

| Pieza | Dónde | Qué hace |
|---|---|---|
| Base adaptada | `src/clase/train_ensemble_adaptado.py:67` | `construir_raw_adaptado`: misma base + protocolo de nulos |
| LGBM cuantil | `src/clase/train_lgbm_adaptada.py` | 93 features tabulares residualizadas por ventana, alpha 0.35 |
| Número | 7.067 (NB05, base adaptada) | comparable al de la base original: el MAR+ffill no degrada |
| Rol | prototipo antes del bundle C (SAA 8) | si la base imputada rindiera menos, el híbrido nacería cojo |

Es el «extra no visto en clase» del criterio SAA 6 en su primer peldaño: la LGBM sola no es el despliegue, es la prueba de que la base adaptada aguanta.

## Conexiones

- Base: [[c17-nulos-mar-e-imputacion-causal]] · encima: [[s20-ensemble-adaptado-y-bundle-c]] · el cuantil como idea: [[c05-regresion-cuantilica]] · cifras: [[e00-cifras-autoritativas]]

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Antes del híbrido, reentrenamos la LGBM sola sobre la base con nulos tratados: 7.067, sin degradación. El puente se prueba antes de cruzarlo».

## Flashcards

> [!question]- ¿Qué demuestra la LGBM adaptada (7.067)?
> Que la base con T30 imputado (MAR + ffill) rinde igual que la original: la imputación no degrada, así que el híbrido-C se construye sobre una base sana.
