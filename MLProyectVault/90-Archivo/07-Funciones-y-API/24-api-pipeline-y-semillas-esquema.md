---
title: Esquema — API Pipeline y semillas
course: DS02-RUL
block: B7 — Funciones y API
node: N24
type: esquema
status: en-curso
tags:
  - esquema
  - api
  - pipeline
---

# Esquema — API Pipeline y semillas

> Teoría completa: [[24-api-pipeline-y-semillas]]

## La idea en una frase

> `run_seed(semilla)` → LGBM + BiLSTM + métricas. `seed_summary` agrega. OOF da predicciones honestas.

## Las 7 piezas

| Función | Qué hace |
|---|---|
| make_lgbm | LightGBM cuantil (alpha=0.35) |
| fit_bilstm | entrena BiLSTM (EarlyStopping motor 16) |
| _row | construye fila de resultados |
| run_seed | pipeline completo para una semilla (~65 s) |
| oof_base_predictions | OOF agrupado (~270 s, cobertura 1) |
| seed_summary | agrega semillas (media ± std) |
| ablation_table | 4 variantes cyc_norm/baseline (+0.355) |
| nasa | NASA score asimétrico |

## Sí / No

- ✅ run_seed encapsula una corrida entera.
- ❌ No ejecutar en render (65 s por semilla).

## Flashcards #flashcards

- ¿Qué hace run_seed? :: Pipeline completo para una semilla.
- ¿Qué mide ablation_table? :: Efecto de quitar cyc_norm (+0.355).
- ¿OOF cobertura? :: Exactamente 1.

## Estado

- [ ] En curso
