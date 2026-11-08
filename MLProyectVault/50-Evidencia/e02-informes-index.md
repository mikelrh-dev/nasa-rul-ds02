---
tipo: evidencia
status: sin-estudiar
tags:
  - informes
  - evidencia
  - indice
---

# Informes index — qué pregunta responde cada uno

> [!abstract] En una frase
> Veinte informes miden lo que el vault afirma: nada se dice sin su medición (trece originales más siete de noviembre; ver tabla).

## Cómo leer esta tabla

Cada fila es un informe en `docs/informes/`. La tercera columna dice qué pregunta cierra para la defensa.

| Informe | Qué mide | Pregunta que responde |
|---|---|---|
| `informe-2026-10-18-comparacion-nasa-fd001` | FD001 frente a DS02 | Por qué DS02 y no el clásico |
| `informe-2026-10-20-ejecucion-cuaderno` | Ejecución de cuadernos | Si la cadena NB01→NB03 funciona |
| `informe-2026-10-20-meta-cycle-fix` | Arreglo del ciclo en el meta | Por qué el meta lleva `cyc_norm` OFF en meta (sin reloj) |
| `informe-2026-10-21-alarma-y-confusion` | Alarmas y confusión | Cuánto anticipa y cuánto confunde |
| `informe-2026-10-21-evaluacion-general` | Evaluación global | El 4.34 con su dispersión |
| `informe-2026-10-21-motor16-vs-oof` | Meta en 16 frente a OOF | Por qué no se ajusta en OOF |
| `informe-2026-10-21-p0-p1-prior-de-vida` | Prior de vida P0/P1 | Si el nivel medio transfiere |
| `informe-2026-10-21-p3-capacidad-vs-informacion` | Capacidad frente a información | Si más parámetros dan más señal |
| `informe-2026-10-21-reglas-oof` | Reglas sobre OOF | Cobertura 0.9012 de la capa de reglas |
| `informe-2026-10-23-fallos-y-usabilidad-app` | Fallos y uso de la app | Qué rompe el DSS en manos reales |
| `informe-2026-10-24-anticipacion-al-fallo` | Anticipación al fallo | Lead time 9/23/17 y su lectura |
| `auditoria-2026-10-21-reglas` | Auditoría de reglas | Si R2b es isotónica y no regla |
| `informe-auditoria-2026-10-31` | Auditoría global | Qué queda por blindar |
| `informe-auditoria-2026-11-04-datos-mongo` | Auditoría datos + Mongo (2026-11-04) | Estado de datos, Mongo y reproducibilidad |
| `informe-2026-11-05-bloques-auditoria-resultado` | Bloques BL-01…BL-09 (2026-11-05) | Qué se aplicó y se verificó (315 passed) |
| `auditoria-2026-11-05-reto1-saa-pia-mia` | Auditoría Reto 1 SAA/PIA/MIA (2026-11-05) | Dónde está el reto frente a la rúbrica |
| `informe_de_auditoria_ux_y_modelo_streamlit_ds02` | Auditoría UX + Streamlit DS02 | Riesgos de UX y conexión modelo-app |
| `auditoria-2026-11-06-reto1-v2` | Auditoría Reto 1 v2 (2026-11-06) | Estado del reto frente a la rúbrica v2 |
| `auditoria-2026-11-07-ds02` | Auditoría DS02 (2026-11-07) | Estado del bundle DS02 |
| `auditoria-2026-11-07-cobertura` | Cobertura 2026-11-07 (CSV) | Matriz de cobertura de rúbrica |

El índice vivo está en `docs/informes/README.md`. Si un informe y esta nota discrepan, manda el informe.

## El informe que más te defiende

`motor16-vs-oof` demuestra con números que ajustar el meta en OOF da media 39.9 frente a real 31.5 y el RMSE sube de 4.04 a 10.17. Es la prueba de que el holdout de una unidad, con su techo de 62, es mejor que un OOF que no transfiere.

`evaluacion-general` sostiene el titular: híbrido ≈4.34 con su dispersión frente a bases.

## Di esto en el tribunal

> [!quote]
> «Nada de lo que afirmo es palabra: cada punto tiene su informe con medición contraria incluida. El que más me protege es el que demuestra que el OOF no transfiere a la 16.»

## Flashcards

> [!question]- ¿Qué prueba motor16-vs-oof?
> Que el meta en OOF da 39.9 vs 31.5 real y sube a 10.17.

> [!question]- ¿Qué sostiene evaluacion-general?
> El 4.32 con dispersión (bundle C) frente a 7.07 y 5.65.

> [!question]- ¿Dónde está el índice vivo?
> En `docs/informes/README.md`; esta nota lo resume.

> [!question]- ¿Qué afirma esta nota en una frase?
> Veinte informes miden lo que el vault afirma: nada se dice sin su medición.

> [!question]- ¿Cómo la contarías en el tribunal?
> «Nada de lo que afirmo es palabra: cada punto tiene su informe con medición contraria incluida. El que más me protege es el que demuestra que el OOF no transfiere a la 16.»

> [!question]- ¿Qué archivo respalda esta nota?
`docs/informes/`
En `docs/decisions/` y `docs/informes/` con índice vivo en sus README.

> [!question]- ¿Qué archivo respalda esta nota?
`docs/informes/README.md`


> [!question]- ¿Qué archivo respalda esta nota?
`docs/informes/README.md`

> [!question]- ¿Qué archivo respalda esta nota?
`docs/decisions/`


> [!question]- ¿A qué nota vas si fallas esta idea?
[[e00-cifras-autoritativas]]

> [!question]- ¿A qué nota vas si fallas esta idea?
[[e01-adr-index]]


> [!question]- ¿A qué nota vas si fallas esta idea?
[[s13-capa-de-reglas-y-decision]]

> [!question]- ¿Qué afirma esta nota en una frase?
> Trece informes miden lo que el vault afirma: nada se dice sin su medición.

## Conexiones

Cifras: [[e00-cifras-autoritativas]] · Decisiones: [[e01-adr-index]] · Reglas: [[s13-capa-de-reglas-y-decision]]
