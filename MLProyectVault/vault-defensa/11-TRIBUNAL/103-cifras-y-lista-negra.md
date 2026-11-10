---
title: Cifras y lista negra
course: Reto 1 · SAA+PIA+MIA
block: 11 — Tribunal
node: F4
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - tribunal
  - cifras
---

# Cifras y lista negra

> [!abstract] En una frase
> Ocho cifras se dicen; quince no se dicen nunca. Confundirlas es el error más caro de la defensa.

## Las ocho que se dicen

| Cifra | Qué es | Fuente |
|---|---|---|
| **4,338** | RMSE test del bundle C, semilla 42 en disco | manifiesto, `reference_row` |
| **3,227** | MAE test del bundle C | manifiesto |
| **0,9461** | R² test del bundle C | manifiesto |
| **5,0153** | Macro-RMSE (motor 14: 8,576) | manifiesto |
| **7,067 → 4,338** | Cascada del híbrido | `comparativa_bundle_c.csv` |
| **9 / 23 / 17** | Lead time por motor (media) | capa de reglas |
| **30 / 25** | Umbrales de `L_inf` (apto / hangar) | `ADR-008`, `reglas.py` |
| **17** | Runs en MLflow | `mlruns/`, export |

## La lista negra

| Cifra | Qué era | Por qué no |
|---|---|---|
| 4,368 | media de `comparativa_c_multisemilla.csv` | CSV obsoleto: el vigente da 4,324 |
| 4,340 ± 0,101 | media del bundle B | B archivado |
| 4,251 | fila histórica del bundle B | artefacto no en disco |
| 4,352 / 4,344 / 4,301 | corridas antiguas | no determinismo y revisiones previas |
| 4,347 ± 0,012 | multiseed citada en un ADR | sustituida por 4,324 ± 0,107 |
| 4,9026 | macro anterior | sustituido por 5,0153 |
| 4,289 | test de una revisión previa | reemplazado |
| 6,233 / 6,347 / 4,278 | otras corridas | ruido de ejecución |
| hashes viejos | `051e0af4`, `0acd795b`, `7acba335` | no son los de disco |

## La respuesta si el tribunal cita una cifra negra

> «Esa cifra es de una corrida anterior o del bundle B; el artefacto en disco es el C y da 4,338.
> La media de semillas es 4,324 ± 0,107.»

Nunca se discute: se corrige con la fuente y se sigue.

## Cómo verificarlo en 30 segundos

```bash
python -c "import json;d=json.load(open('models/ds02_manifest.json'));print(d['metrics']['reference_row']['rmse'], d['macro_rmse'])"
```

## Lo que NO digo

- No doy dos cifras distintas para lo mismo en la misma frase.
- No redondeo a la baja para que suene mejor.
- No cito una media si me preguntan por el artefacto.

## Flashcards #flashcards

- ¿Cuál es la cifra oficial del bundle C? :: 4,338 (semilla 42 en disco).
- ¿Qué cifra está prohibida y por qué? :: 4,368, media de un CSV obsoleto.
- ¿Qué dos cifras miden lo mismo de forma distinta? :: 4,338 global y 5,0153 macro.
