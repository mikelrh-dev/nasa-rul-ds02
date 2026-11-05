---
tipo: notebook
status: sin-estudiar
tags:
  - nb03
  - features
  - cyc-norm
  - ablacion
---

# NB03 — Features secuenciales y ablación de cyc_norm

> [!abstract] En una frase
> Trece celdas que responden una pregunta con un número: ¿el reloj `cyc_norm` ayuda o es trampa?

## Antes de empezar

13 celdas. Requiere NB02 (el reloj se ablaciona sobre el mejor pipeline). Es el cuaderno corto y quirúrgico: una hipótesis, un experimento, una conclusión escrita.

## Recorrido celda a celda

| Bloque | Qué entra | Qué hace | Qué sale |
|---|---|---|---|
| Glosario 30 segundos | vocabulario | tabla nombre → qué es → dónde vive | leer sin perderse |
| Ablación `cyc_norm` | con/sin reloj | mide, no afirma | ON en red + OFF en meta: 5.419 → 4.338 |
| Siguiente | enlace | continúa en NB04 | la arquitectura que usa el reloj bien |

## La celda que importa

La ablación: un número que circula en la documentación se reproduce aquí con protocolo. El reloj ayuda a la red (secuencia necesita tiempo) y corrompe al meta (prior de vida que no transfiere). La decisión queda escrita en `stacking.py:161` y ADR-005.

## Qué NO hace este cuaderno

No entrena el híbrido final (eso es NB04), no calibra banda (NB04/NB05), no multisemilla (NB05). NB03 decide dónde vive el reloj.

## Conexiones

- Mecanismo: [[c19-ablacion-cyc-norm]] · el fallo del meta: [[s09-oof-y-beta]] · sigue en [[n06-recorrido-nb04]]

> [!quote] Di esto en el tribunal
> «En el tercero hago una sola pregunta y la respondo con un número: el reloj se queda en la red y se prohíbe en el meta, y la diferencia entre un sitio y otro está medida».

## Flashcards

> [!question]- ¿Qué decide NB03?
> Dónde vive `cyc_norm`: ON en la BiLSTM (la secuencia necesita reloj), OFF en el meta (para que no aprenda un prior de vida y solo reconcilie ramas).

> [!question]- ¿Por qué un cuaderno entero para una feature?
> Porque «esta feature ayuda» sin ablación es una creencia; con ablación y protocolo es un número con signo que el tribunal no puede discutir.
