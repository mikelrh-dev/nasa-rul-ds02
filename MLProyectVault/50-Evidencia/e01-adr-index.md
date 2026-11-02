---
tipo: evidencia
status: sin-estudiar
tags:
  - adr
  - decisiones
  - trazabilidad
---

# ADR index — 10 decisiones que sostienen el proyecto

> [!abstract] En una frase
> Cada decisión difícil está escrita con qué se probó, qué se rechazó y con qué número.

## Cómo leer esta tabla

Cada fila enlaza al ADR en `docs/decisions/`. La tercera columna es el número que respalda la decisión, compilado en [[e00-cifras-autoritativas]].

| ADR | Qué decide | Número que lo respalda |
|---|---|---|
| ADR-001 | Stacking aprendido frente a blending lineal | Blending 8.091 y 7.180 vs híbrido ≈4.34 |
| ADR-002 | Residualizar sensores con Ridge grado 2 | Holdout limpio con 44 982 filas |
| ADR-003 | Cuantil asimétrico `alpha` 0,35 en LightGBM | LGBM ≈7.10 que complementa, no que gana |
| ADR-004 | Boosting y Ridge frente a clásicos | Clásicos no capturan secuencia ni cuantil |
| ADR-005 | Reservar la 16 como holdout de stacking | Meta en 2 535 ventanas, RUL 0–62 |
| ADR-006 | EMA causal por motor con span 5 | Estabiliza sin mirar futuro |
| ADR-007 | Rechaza mover el objetivo a la mediana | Mediana precisa sola, peor combinada |
| ADR-008 | Triaje sobre `L_inf` con 30 y 25 | APTO, INSPECCIÓN y HANGAR operativos |
| ADR-009 | R2b es ajuste isotónico, no regla | R2b 9.623 frente a R2 10.737 |
| ADR-010 | Rechaza simulador desacoplado por polling | Servir es recargar el bundle |

ADR-007 y ADR-010 son rechazos explícitos: también cuentan. Rechazar a tiempo es decidir.

## Dónde están los originales

`docs/decisions/ADR-001-reject-linear-blending-adopt-learned-stacking.md` hasta `ADR-010-reject-decoupled-fleet-simulator-n8n-polling.md`. Extractos literales en la ground truth de la reestructuración.

La lógica de negocio de ADR-008 vive además en `docs/defensa_ds02_explicacion_logica_negocio.md`.

## Qué responder con esta página

Si preguntan «¿por qué stacking y no promedio?», vas a ADR-001 con 8.091 en la mano. Si preguntan «¿por qué cuantil 0,35?», vas a ADR-003 y ADR-007. Si preguntan «¿por qué EMA?», vas a ADR-006.

Ninguna decisión es gusto: todas tienen medición contraria descartada.

## Di esto en el tribunal

> [!quote]
> «Cada decisión difícil está escrita: blending medido y rechazado, mediana medida y rechazada, simulador medido y rechazado. Lo que queda está porque midió mejor.»

## Flashcards

> [!question]- ¿Qué rechaza ADR-001?
> El blending lineal con 8.09 y 7.18 frente al stacking.

> [!question]- ¿Qué fija ADR-005?
> La unidad 16 como holdout puro del meta.

> [!question]- ¿Qué aclara ADR-009?
> Que R2b es ajuste isotónico, no regla de monotonía.

> [!question]- ¿Qué afirma esta nota en una frase?
> Cada decisión difícil está escrita con qué se probó, qué se rechazó y con qué número.

> [!question]- ¿Cómo la contarías en el tribunal?
> «Cada decisión difícil está escrita: blending medido y rechazado, mediana medida y rechazada, simulador medido y rechazado. Lo que queda está porque midió mejor.»

> [!question]- ¿Qué archivo respalda esta nota?
`docs/decisions/`
En `docs/decisions/` y `docs/informes/` con índice vivo en sus README.

> [!question]- ¿Qué archivo respalda esta nota?
`docs/decisions/ADR-001-reject-linear-blending-adopt-learned-stacking.md`


> [!question]- ¿Qué archivo respalda esta nota?
`docs/defensa_ds02_explicacion_logica_negocio.md`

> [!question]- ¿Qué archivo respalda esta nota?
`docs/decisions/`


> [!question]- ¿A qué nota vas si fallas esta idea?
[[e00-cifras-autoritativas]]

> [!question]- ¿A qué nota vas si fallas esta idea?
[[e00-cifras-autoritativas]]


> [!question]- ¿A qué nota vas si fallas esta idea?
[[e02-informes-index]]

> [!question]- ¿A qué nota vas si fallas esta idea?
[[s10-stacking-hibrido]]

## Conexiones

Cifras: [[e00-cifras-autoritativas]] · Informes: [[e02-informes-index]] · Sistema: [[s10-stacking-hibrido]]
