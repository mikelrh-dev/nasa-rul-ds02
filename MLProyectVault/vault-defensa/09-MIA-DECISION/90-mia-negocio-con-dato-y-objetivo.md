---
title: MIA · Negocio con dato y objetivo
course: Reto 1 · SAA+PIA+MIA
block: 09 — MIA decisión
node: D1
indicador: MIA-1
descriptor: 10
spine: false
status: en-curso
tags:
  - mia
  - negocio
  - rubrica/mia-1
---

# MIA · Negocio con dato y objetivo

> [!abstract] En una frase
> No es «predecir RUL»: es **decidir cuándo sacar un motor de servicio** con antelación
> suficiente. El dato que lo justifica es el error frente al margen de actuación.

## Qué digo

«El objetivo es priorizar mantenimiento: dado un motor y su telemetría, estimar cuántos ciclos le
quedan y convertirlo en apto, inspección programada o derivación a hangar. Lo usa quien planifica
el taller, no el piloto. El dato que lo sostiene: el error típico es 3,2 ciclos y el aviso llega
entre 9 y 23 ciclos antes del umbral, según el motor. Es decir, el sistema avisa con margen
suficiente para programar, que es justo lo que hoy no existe.»

## Lo que mejora para la empresa

| Hoy | Con el sistema |
|---|---|
| Inspección por calendario o por síntoma | Inspección por estado, con antelación medida |
| Inmovilizar de más por precaución | Hangar solo cuando el límite inferior lo exige |
| Decisión no auditable | Seis reglas con prioridad y porqué, y un registro por decisión |

## Evidencia

- Macro-RMSE 5,0153 y motor 14 con 8,576 ([[62-nb06-macro-y-motor-14]]).
- Lead time por motor: 9 / 23 / 17 por media, 13 / 23 / 18 por peor ventana.
- Umbrales: `L_inf ≥ 30` apto · `25 ≤ L_inf < 30` inspección · `< 25` hangar.
- `README.md:21` (necesidad de negocio) y `src/mia/reglas.py`.

## Pregunta probable

**«¿Quién usa esto exactamente?»**
→ «Planificación de mantenimiento: recibe una lista priorizada por motor y ciclo, con la regla que
la justifica. No es una alerta al piloto en vuelo: el sistema no está certificado para eso, y lo
declaramos.»

## Lo que NO digo

- No invento euros: el coste se argumenta con el margen de actuación, no con una cifra de ahorro
  que no hemos medido.
- No digo «evita fallos»: prioriza inspecciones.

## Di esto en el tribunal

> «Convierte telemetría en una lista de motores priorizada: error típico 3,2 ciclos y aviso 9–23
> ciclos antes, para que el taller programe en vez de improvisar.»

## Flashcards #flashcards

- ¿Qué se predice, para qué y quién lo usa? :: el RUL, para priorizar mantenimiento, y lo usa planificación de taller.
- ¿Cuál es el dato que justifica el sistema? :: 3,2 ciclos de error frente a 9–23 de margen de aviso.
