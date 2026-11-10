---
title: NB01 · Nulos MAR y variable nueva
course: Reto 1 · SAA+PIA+MIA
block: 01 — NB01 EDA
node: B1.3
indicador: SAA-5
descriptor: 10
spine: false
status: en-curso
tags:
  - nb01
  - nulos
  - mar
  - rubrica/saa-5
---

# NB01 · Nulos MAR y variable nueva

> [!abstract] En una frase
> Los nulos no son un porcentaje: son un patrón. Aquí el patrón es «T30 se cae en crucero
> alto», y eso decide cómo se imputa y por qué no se puede borrar la fila.

## Qué digo

«T30 no falta al azar: falta cuando el avión va alto y rápido. Es un mecanismo MAR —la
probabilidad de faltar depende de variables observadas, altitud y Mach—, así que imputar con la
media global sería mentir y borrar la fila sesgaría el crucero, que es justo donde más datos
hay. Imputamos con la mediana de las unidades de ajuste y `ffill` causal: solo miro hacia
atrás.»

## El mecanismo, con números

| Dato | Valor |
|---|---|
| Condición de elegibilidad | `alt > 27 000` y `Mach > 0,68` |
| Tasa sobre filas elegibles | 10 % |
| Tasa global resultante | ≈ 2,1 % |
| Semilla del análisis | 7 |
| Nota importante | El 30 000/0,8 teórico no existe en DS02 (Mach máx ≈ 0,74): se ajustó al dato real |

## Variables nuevas

1. **`fase_vuelo`** — despegue / crucero / descenso por umbrales de altitud y Mach; entra como
   one-hot porque el efecto de un sensor cambia de régimen.
2. **`cyc_norm`** — el reloj normalizado; es la variable del reloj que después se ablaciona en
   [[30-nb03-ablacion-cyc-norm]].
3. **Residualización** — 14 regresiones (una por sensor) sobre condiciones operativas: el
   residuo es degradación, no pilotaje.

## Por qué se dice así

- El 7 exige explicar si los nulos son al azar o siguen un patrón. El 10 exige **además** una
  variable nueva útil. Aquí hay tres.
- Decir «10 % de los elegibles, 2,1 % global» demuestra que el nulo se diseñó y se midió, no se
  sufrió.

## Evidencia

- Inyección y auditoría: `src/clase/dataset_clase.py:11` (`elegibles_mar`, umbrales y seed).
- Imputación causal: `imputar_ffill` en el mismo módulo.
- Residualización: `src/ds02_rul/residualizer.py`, usada vía `fit_preprocessing`.
- Auditoría de nulos: `auditoria_nulos.json` y NB01 c8.

## Pregunta probable

**«¿Inyectaste los nulos tú?»**
→ «Sí, y está declarado: DS02 no trae nulos. Se inyecta un MAR realista en T30 para poder
demostrar el tratamiento; la semilla y la tasa están en el código, y la auditoría se guarda. Un
nulo inyectado y auditado es un experimento; uno escondido, una trampa.»

## Lo que NO digo

- No digo «imputé con la media»: no es lo que hace el código.
- No digo «los nulos son MCAR»: son MAR, y la diferencia es la que justifica el `ffill` causal.
- No digo que rellenar hacia delante sea gratis: introduce dependencia temporal, y por eso el
  split es por motor.

## Di esto en el tribunal

> «T30 se cae en crucero alto: es MAR, se imputa con mediana de ajuste y `ffill` causal, y no se
> borra la fila porque el crucero es donde está el dato bueno.»

## Flashcards #flashcards

- ¿Qué mecanismo tienen los nulos y con qué condición? :: MAR, cuando `alt > 27 000` y `Mach > 0,68`.
- ¿Qué tasa global resultante tiene? :: ≈2,1 % (10 % de las filas elegibles, seed 7).
- ¿Qué tres variables nuevas se crean? :: `fase_vuelo`, `cyc_norm` y la residualización de sensores.
