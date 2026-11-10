---
title: NB05 · Stacking y holdout 16
course: Reto 1 · SAA+PIA+MIA
block: 05 — NB05 meta y banda
node: B5.1
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - nb05
  - stacking
  - adr-001
  - adr-005
---

# NB05 · Stacking y holdout 16

> [!abstract] En una frase
> Mezclar dos modelos con un promedio es una opinión; dejar que un meta-aprendiz aprenda la
> mezcla es una decisión medible. Y para medirla hace falta una unidad que el meta no haya visto.

## Qué digo

«Probamos el blend lineal —promedio fijo de las dos ramas— y lo rechazamos: cuando una rama falla
mucho, el promedio arrastra a la otra. El meta es un Ridge sobre dos columnas, las predicciones
de cada rama; aprende cuánto pesar según el caso. Se ajusta solo en la unidad 16, que no entra en
el OOF ni en test. Pesos resultantes: 28 % red, 72 % árbol, `alpha` ≈ 88,6.»

## Por qué se dice así

- La rúbrica no lo pide, pero el tribunal sí: «¿por qué no un promedio?». La respuesta está en
  `ADR-001` y en que el meta baja el error de ambas ramas por separado.
- El holdout 16 es la pieza que impide el autoengaño: si el meta se ajustara en las mismas
  unidades del OOF, el 4,34 estaría contaminado.

## Evidencia

- Decisión: `docs/decisions/ADR-001-reject-linear-blending-adopt-learned-stacking.md` y
  `ADR-005-reserve-unit-16-as-stacking-holdout.md`.
- Implementación: `src/ds02_rul/stacking.py` (`fit_meta_learners`).
- Pesos del artefacto: `models/ensemble.joblib` (28/72, `alpha` 88,6).

## Pregunta probable

**«¿No es el meta otro modelo que puede sobreajustar?»**
→ «Con dos entradas y un Ridge regularizado, la capacidad es mínima; el riesgo no es sobreajustar,
es elegir mal el holdout. Por eso la 16 se reserva y se declara: cualquier número que la use para
elegir deja de ser test.»

## Lo que NO digo

- No digo «el stacking siempre gana»: aquí ganó porque las dos ramas se equivocan distinto.
- No digo que la 16 sea test: es holdout de ajuste del meta.

## Di esto en el tribunal

> «Rechazamos el promedio porque arrastra el error de la rama que falla; el meta aprende la mezcla
> en una unidad reservada y pesa 28 % red, 72 % árbol.»

## Flashcards #flashcards

- ¿Qué alternativa se rechazó y por qué? :: el blend lineal, porque arrastra el error de la rama mala.
- ¿Dónde se ajusta el meta? :: en la unidad 16, reservada como holdout.
- ¿Qué pesos salen? :: 28 % BiLSTM, 72 % árbol, con `alpha` ≈ 88,6.
