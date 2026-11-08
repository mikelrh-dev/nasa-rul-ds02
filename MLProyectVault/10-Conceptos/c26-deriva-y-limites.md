---
tipo: concepto
status: consolidado
tags:
  - deriva
  - limites
  - u14
---

# Deriva y límites — lo que el despliegue no promete

> [!abstract] En una frase
> El bundle no detecta mundo nuevo, el motor 14 es frágil por densidad y la ventana no son ciclos: decirlo es parte del contrato.

## La idea

Tres límites medidos, no modestia:

1. **Sin monitor de deriva**: régimen no visto predice igual sin avisar (`s14`). Próxima frontera, no prestación. No vender `observed_envelope ±5%` como detector.
2. **U14 frágil**: 20.6 filas/ciclo vs 112 U11; RMSE 8.5761 (bundle C) vs 3.633/2.837; bias −5.09 del bundle B (retirado, sin valor C). Macro C 5.0153 esconde que un motor al azar sufre más que la media ponderada 4.338 (`e00`, informe 2026-11-04 P1-1).
3. **Ventana ≠ ciclos + stride**: 50 filas strided = 0.44 ciclos U11 / 0.77 U15 / 2.4 U14. STRIDE 100 descarta 99% sin análisis sensibilidad (`data.py:55`). Decir “50 ciclos” es error de interpretación, no numérico.

## Dónde aparece en este proyecto

- `s14-app-y-despliegue` límite, `e00 macro-RMSE`, `models/ds02_manifest.json macro_rmse`
- `src/ds02_rul/data.py:55 [::stride]`, `src/ds02_rul/features.py:79-163`
- `docs/informes/informe-auditoria-2026-11-04-datos-mongo.md §1 P1-1/P1-2`

> [!warning] La trampa
> «Macro 5.02 ≈ micro 4.34, da igual»: no. 760 filas concentran 47,9% del error cuadrático (bundle C). El promedio de flota es más amable que un motor al azar.

## Di esto en el tribunal

> [!quote]
> «Sin deriva vigilada, U14 frágil por densidad y ventana de 0.44 ciclos: el 4.338 es media ponderada, el macro 5.02 es lo que sufre un motor al azar.»

## Flashcards

> [!question]- ¿Cuáles son tus tres no-promesas?
> Sin deriva, U14 frágil, ventana 0.44 ciclos y stride 100 sin sensibilidad medida.
