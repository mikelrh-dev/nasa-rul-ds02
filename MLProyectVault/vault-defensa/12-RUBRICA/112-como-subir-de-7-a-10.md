---
title: Cómo subir de 7 a 10
course: Reto 1 · SAA+PIA+MIA
block: 12 — Rúbrica
node: G3
indicador: PIA-4
descriptor: 7
spine: false
status: en-curso
tags:
  - rubrica
  - plan
---

# Cómo subir de 7 a 10

> [!abstract] En una frase
> Solo hay un indicador por debajo del 10 y se arregla en dos pasos: registrar la ablación como
> run y decidir el destino de `mlruns/`.

## Paso 1 — Registrar la ablación (30 min)

```
run: ablacion__cyc_norm
params:  canal_19 = on | off,  meta_cycle = off,  semilla = 42
metrics: rmse_bilstm_on = 5.796,  rmse_bilstm_off = 6.563
         rmse_lgbm_on   = 7.067,  rmse_lgbm_off   = 6.297
```

- Escritor natural: `scripts/ablate_meta_cycle.py` (ya produce los números).
- Verificación: `grep -ril cyc_norm mlruns --include=meta.yaml | wc -l` ≥ 1 y la fila aparece en
  `docs/evidencia/mlflow/comparativa.csv`.

## Paso 2 — Decidir qué pasa con `mlruns/` (15 min)

Dos salidas, excluyentes:

| Opción | Qué hace | Efecto |
|---|---|---|
| A · Versionar | Añadir los 17 runs (sin `artifacts/`) | `git status mlruns/` limpio; clon reproducible |
| B · Ignorar | `git rm -r --cached mlruns` + `.gitignore` | Evidencia congelada en `docs/evidencia/mlflow/`; hay que sembrar `mlruns/` en tests |

Recomendada **A** si la defensa exige «enseñar MLflow desde el repo».

## Paso 3 — Captura

Una captura de la run nueva en `docs/evidencia/mlflow/`, porque PIA-4 pide «lo enseña con capturas».

## Lo que NO hace falta

- Reentrenar nada: los números ya están medidos.
- Cambiar el modelo, la banda ni las reglas.
- Tocar la app: PIA-5 ya está en 10.

## Después del arreglo

| Asignatura | Antes | Después |
|---|---|---|
| PIA | 9,4 | **10,0** |
| SAA | 10,0 | 10,0 |
| MIA | 10,0 | 10,0 |

Verificación final: `python scripts/backfill_mlflow.py --check` → 14 runs.

## Di esto en el tribunal

> «Trece runs y la ablación pendiente de registrar; está en el plan de cierre y es lo único que
> separa PIA del 10.»

## Flashcards #flashcards

- ¿Cuántos runs habría tras registrar la ablación? :: 14 (13 + la ablación).
- ¿Hace falta reentrenar para subir PIA-4? :: no: los números ya están medidos.
