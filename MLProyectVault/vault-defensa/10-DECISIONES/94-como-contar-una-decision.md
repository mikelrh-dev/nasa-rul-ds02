---
title: Cómo contar una decisión
course: Reto 1 · SAA+PIA+MIA
block: 10 — Decisiones
node: E1
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - decisiones
  - metodo
---

# Cómo contar una decisión

> [!abstract] En una frase
> Una decisión se cuenta con **la alternativa que rechazaste**, no con la que elegiste. Sin
> alternativa no hay decisión: hay una descripción.

## La plantilla de seis líneas

1. **Qué decidimos.** Una frase, en presente.
2. **Qué rechazamos.** La alternativa real, con su nombre.
3. **Con qué criterio.** La métrica o el coste que desempata.
4. **Qué costó.** Lo que perdimos al elegir (tiempo, complejidad, cobertura).
5. **Qué evidencia lo sostiene.** `path:línea`, cifra o ADR.
6. **Cuándo la revertiría.** La condición que la invalidaría.

## Ejemplo completo

> «Elegimos un meta-aprendizaje en vez de un promedio fijo. Rechazamos el blend lineal porque
> cuando una rama falla, el promedio arrastra a la otra. El criterio fue el RMSE OOF sobre cinco
> unidades puras. Nos costó una unidad entera de datos —la 16— para ajustar el meta. Está en
> `ADR-001` y en `src/ds02_rul/stacking.py`. La revertiría si el meta no bajara el error de ambas
> ramas por separado en una flota nueva.»

## Por qué se dice así

- El tribunal no pregunta «¿qué hiciste?», pregunta «¿por qué así?». La sexta línea —cuándo la
  revertiría— es la que demuestra que la decisión es una hipótesis y no una preferencia.
- Seis líneas caben en 25 segundos: es el formato correcto para una defensa de 15 minutos.

## Errores que delatan

| Error | Por qué delata |
|---|---|
| Contar solo lo elegido | Parece que no había alternativa |
| «Porque funcionaba mejor» | Sin métrica ni conjunto, no es un criterio |
| Ocultar el coste | Toda decisión tiene uno; negarlo suena a desconocimiento |
| No saber qué la revertiría | Convierte la decisión en dogma |

## Di esto en el tribunal

> «Cada elección la cuento con la alternativa que descarté y con la condición que la revertiría:
> si no sé eso, no es una decisión, es una costumbre.»

## Flashcards #flashcards

- ¿Qué seis líneas tiene una decisión? :: qué, qué rechacé, criterio, coste, evidencia y cuándo la revertiría.
- ¿Cuál es la línea que más delata? :: la de cuándo la revertiría: sin ella es dogma.
