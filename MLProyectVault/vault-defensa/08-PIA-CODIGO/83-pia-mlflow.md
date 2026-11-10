---
title: PIA · MLflow
course: Reto 1 · SAA+PIA+MIA
block: 08 — PIA código
node: C4
indicador: PIA-4
descriptor: 7
spine: true
status: en-curso
tags:
  - pia
  - mlflow
  - rubrica/pia-4
  - hueco
---

# PIA · MLflow

> [!abstract] En una frase
> MLflow tiene 13 runs con parámetros y métricas, export y capturas; lo que **no** tiene es la
> ablación del reloj. Ese hueco es lo único que hoy impide el 10.

## Qué digo

«Todos los experimentos están registrados: 13 runs, nueve de grano fila y cuatro de ventana, con
hiperparámetros y métricas. La comparativa está exportada a CSV y hay capturas de la interfaz. El
run que falta —y lo digo yo antes de que lo preguntéis— es la ablación de `cyc_norm`, que está
medida en el notebook y en el README pero no registrada como run.»

## Por qué se dice así

- PIA-4 vale el 20 % de PIA y su 10 exige «compara los modelos en MLflow y lo enseña con
  capturas». Enseñar el hueco convierte una resta en una decisión consciente.
- El store está en `mlruns/`: es texto, no guarda binarios. Eso también se dice.

## Evidencia

- `mlruns/` (13 runs con `meta.yaml`, `params`, `metrics`, `tags`) y
  `docs/evidencia/mlflow/comparativa.csv`.
- `scripts/backfill_mlflow.py --check` → exit 0: el export y el store coinciden en 13 runs.
- Capturas en `docs/evidencia/mlflow/`.
- Hueco declarado: 0 runs con `cyc_norm` (`grep -ril cyc_norm mlruns --include=meta.yaml` → 0).

## Pregunta probable

**«¿Por qué no está la ablación en MLflow?»**
→ «Porque se midió desde el notebook antes de cerrar el registro y quedó fuera del backfill. Está
en el plan de cierre: registrar la run con los parámetros de las dos ramas y sus dos RMSE. No lo
maquillo: hoy son 13 runs y la ablación no está entre ellos.»

## Lo que NO digo

- No digo «todos los experimentos» sin aclarar que la ablación es la excepción.
- No digo que el store esté completo en git (hay 94 rutas sin versionar).
- No cito un número de runs distinto de 13.

## Di esto en el tribunal

> «Trece runs con parámetros, métricas y capturas; la ablación del reloj es el único experimento
> que no está registrado como run, y está declarado.»

## Flashcards #flashcards

- ¿Cuántos runs hay y de qué tipos? :: 13: nueve de fila y cuatro de ventana.
- ¿Qué experimento falta en MLflow? :: la ablación de `cyc_norm`.
- ¿Qué comprueba que el export cuadra? :: `backfill_mlflow.py --check`, exit 0.
