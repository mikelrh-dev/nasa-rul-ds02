---
tipo: concepto
status: sin-estudiar
tags:
  - ablacion
  - cyc-norm
  - diseno
---

# Ablación de cyc_norm

> [!abstract] En una frase
> Quitar una feature a propósito y medir cuánto duele: así se demuestra qué aporta cada pieza en vez de afirmarlo.

## La idea

Una **ablación** es el experimento control del modelado: se entrena con y sin el componente y se mide la diferencia en la misma métrica y el mismo test. Sin ablación, «esta feature ayuda» es una creencia; con ablación, es un número con signo.

## Lo que se ablacionó aquí

`cyc_norm` (ciclo normalizado) es una feature tabular del resumen por ventana. El experimento (NB03/NB05) la enciende y la apaga en dos sitios:

- **BiLSTM con `cyc_norm` ON**: la red la necesita como reloj interno de la secuencia.
- **Meta con `cyc_norm` OFF**: el meta-aprendiz solo mira `[p_lstm, p_lgb]`; darle el reloj le permitiría aprender un prior de nivel de vida en vez de reconciliar las dos ramas (el fallo medido del diseño OOF-pooled, `src/ds02_rul/stacking.py:161`, ADR-005).

El README raíz lo resume en una fila: `cyc_norm ON (BiLSTM) + OFF (meta) | 5.419 | 4.338`.

## Dónde aparece en este proyecto

- NB03 `03_feature_engineering_secuencial.ipynb` — experimento de ablación.
- `README.md` fila 180 — resultado compacto ON/OFF.
- `src/ds02_rul/stacking.py:161` — el comentario del fallo del meta con prior de vida.
- La decisión gemela en el meta: [[c11-shrinkage-beta]] y [[s10-stacking-hibrido]].

> [!warning] La trampa
> «Ablacioné y no cambió nada, así que la quité»: sin controlar semilla y test, «no cambió nada» puede ser ruido (±0.1 por no-determinismo CPU, [[c14-ruido-y-reproducibilidad]]). Una ablación sin protocolo de comparación es otro nombre para opinar.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Ablacionar es quitar a propósito y medir cuánto duele: con cyc_norm en la red y fuera del meta pasamos de 5.419 a 4.338, y el meta sin reloj no puede aprender un prior de vida, solo reconciliar ramas».

## Flashcards

> [!question]- ¿Qué es una ablación y qué demuestra?
> Entrenar con y sin un componente midiendo la diferencia en igual métrica y test: convierte «esta feature ayuda» de creencia en número con signo.

> [!question]- ¿Por qué cyc_norm está en la BiLSTM pero no en el meta?
> La red la necesita como reloj de la secuencia; al meta se le niega para que no aprenda un prior de nivel de vida y se limite a reconciliar `[p_lstm, p_lgb]` (fallo medido en `stacking.py:161`).
