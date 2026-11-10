---
title: NB03 · Ablación de cyc_norm
course: Reto 1 · SAA+PIA+MIA
block: 03 — NB03 ablación
node: B3.1
indicador: SAA-6
descriptor: 10
spine: true
status: en-curso
tags:
  - nb03
  - ablacion
  - rubrica/saa-6
---

# NB03 · Ablación de cyc_norm

> [!abstract] En una frase
> El reloj (`cyc_norm`) ayuda a la rama que **lee la secuencia** y estorba a la que **resume la
> ventana**. Ese resultado contraintuitivo es el «algo no visto en clase» que pide la rúbrica.

## La tabla

| Variante | BiLSTM | LightGBM |
|---|---|---|
| Con reloj (ON) | **5,796** | 7,067 |
| Sin reloj (OFF) | 6,563 | **6,297** |
| Con línea base delta | 6,394 | 8,765 |

Fuente: `notebooks/03_feature_engineering_secuencial.ipynb` (celda de conclusiones) y
`resultados/ablacion_cycnorm_rmse.png`.

## Qué digo

«Quité el reloj y medí las dos ramas por separado. El BiLSTM empeora casi un ciclo: sin `cycle`
no puede situar la ventana en la vida del motor. LightGBM mejora: para un resumen tabular, el
reloj es una fuga de conveniencia que le deja memorizar la posición. La conclusión es que el
reloj ayuda a la secuencia, no al resumen. Y eso no lo vimos en clase: en clase se añaden
features porque suenan bien.»

## Por qué se dice así

- SAA-6 pide, para el 10, «probar algo que no hayamos visto en clase y demostrar si mejora o
  no». Una ablación **negativa en una rama** es más defendible que una feature que mejora todo:
  demuestra que se midió, no que se buscó el número.
- La línea base delta está para descartar que la mejora viniera de añadir cualquier columna.

## Evidencia

- Notebook: `notebooks/03_feature_engineering_secuencial.ipynb`, celda `abl` (`ablation_table`).
- Escritor del CSV: `src/clase/train_ensemble_adaptado.py` genera la tabla que consume el README.
- La variante con meta fijo está en `README.md:286` y da la misma dirección (5,419 → 6,513 con
  el meta en 4,338): dos tablas, una conclusión.

## Pregunta probable

**«Entonces, ¿el reloj sobra?»**
→ «Sobra para el resumen tabular y falta para la secuencia. Como el sistema desplegado usa las
dos ramas, el reloj se queda: quitarlo subiría el error del BiLSTM casi un ciclo, y el BiLSTM
es el componente que más aporta.»

## Lo que NO digo

- No digo «la ablación demuestra causalidad»: demuestra que ese canal cambia el error en ese
  protocolo.
- No mezclo las dos tablas (la del notebook y la del README) como si fueran la misma corrida.
- No cito la ablación como run de MLflow: **no lo es** (ver [[111-huecos-declarados]]).

## Di esto en el tribunal

> «El reloj ayuda a la secuencia y no al resumen: quitarlo sube el BiLSTM de 5,8 a 6,6 y baja
> LightGBM de 7,07 a 6,30.»

## Flashcards #flashcards

- ¿Qué le pasa al BiLSTM sin reloj? :: empeora de 5,796 a 6,563: necesita situar la ventana.
- ¿Qué le pasa a LightGBM sin reloj? :: mejora de 7,067 a 6,297: el reloj era atajo para el resumen.
- ¿Por qué esta ablación cubre el «no visto en clase»? :: porque mide una feature por rama y admite que en una empeora.
