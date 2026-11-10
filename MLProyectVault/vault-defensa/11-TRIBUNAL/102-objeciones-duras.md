---
title: Objeciones duras
course: Reto 1 · SAA+PIA+MIA
block: 11 — Tribunal
node: F3
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - tribunal
  - objeciones
---

# Objeciones duras

> [!abstract] En una frase
> Diez objeciones que no se contestan con «depende»: cada una tiene una respuesta corta y una
> concesión honesta.

| # | Objeción | Respuesta | Concesión |
|---|---|---|---|
| 1 | «Beta 1 significa que el árbol sobra» | Beta es peso condicionado al fold; sin el árbol el híbrido no baja a 4,34 | La mediana sí carga al BiLSTM |
| 2 | «Una banda que cubre el 100 % es inútil» | Es una cota para decidir, no un intervalo; el ancho informa | Cubre de más y se declara |
| 3 | «La unidad 16 es un holdout de juguete» | Es una unidad entera de un motor no visto, reservada | Con 9 unidades, todo holdout es pequeño |
| 4 | «4,34 ventanas no es comparable con 7,72 filas» | Correcto: son dos ligas y no se comparan | El README lo dice desde el principio |
| 5 | «El BiLSTM varía medio punto entre semillas» | 4,324 ± 0,107 sobre tres semillas | La varianza es real y se publica |
| 6 | «LightGBM 7,07 no aporta» | Aporta donde la secuencia falla; el meta lo usa | Solo, es peor que el BiLSTM |
| 7 | «Esto predice, no decide» | Decide: seis reglas sobre el límite inferior | No certifica aeronavegabilidad |
| 8 | «¿4,34 o 5,02, cuál es la verdad?» | Las dos: global y macro miden cosas distintas | El macro es el que sufre un motor al azar |
| 9 | «¿Por qué no reentrenáis en producción?» | El artefacto está congelado y versionado por SHA | Sin reentreno no hay adaptación a deriva |
| 10 | «¿Y la deriva de distribución?» | Está declarada como límite; el gemelo permite simularla | No hay monitorización automática |

## La estructura de una buena respuesta a objeción

1. **Acepta la parte verdadera** («sí, cubre de más»).
2. **Da el criterio** (por qué se eligió así).
3. **Cierra con el límite** (qué no resuelve).

Sin el paso 1 la respuesta suena defensiva; sin el 3 suena ingenua.

## Frases de emergencia

- «Eso está declarado en el ADR correspondiente.»
- «No lo medimos; no lo afirmo.»
- «Si me dejas enseñarte el código, lo ves en una línea.»

## Di esto en el tribunal

> «La banda cubre de más a propósito y lo declaro: prefiero una cota ancha que una decisión de
> hangar que falle por abajo.»

## Flashcards #flashcards

- ¿Qué tres pasos tiene responder a una objeción? :: aceptar lo verdadero, dar el criterio y declarar el límite.
- ¿Qué respondes a «cubre el 100 %, es inútil»? :: es una cota para decidir; se calibró con folds más débiles.
