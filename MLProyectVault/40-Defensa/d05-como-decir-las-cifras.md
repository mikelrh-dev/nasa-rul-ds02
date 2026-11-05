---
tipo: defensa
status: sin-estudiar
tags:
  - cifras
  - como-decir
  - lista-negra
---

# Cómo decir las cifras — qué número, cómo y qué no

> [!abstract] En una frase
> Decís redondeado en voz y exacto en pantalla, siempre desde la única fuente.

## Regla de oro

En voz redondeas (`≈4.3`, `≈7.1`, `≈5.7`, `≈7.7` el MLP de fila) y en pantalla muestras la tabla de [[e00-cifras-autoritativas]]. Nunca recitas decimales de memoria: los lees.

Si te piden la fuente, dices: «Sale del manifiesto y está compilado en e00». Si discrepan, gana el manifiesto.

## Qué decir para cada bloque

| Bloque | Decís | No decís |
|---|---|---|
| Híbrido-C | «4.32 de media, 4.34 en disco» | 4.352, 4.289, 4.251 (bundle B) |
| Bases C | «7.07 la LGBM adaptada, 5.65 el BiLSTM» | 6.22/7.10 del bundle B sin avisar |
| Macro C | «5.02 macro frente a 4.34 ponderado» | Solo el ponderado |
| Banda | «100 % con 26.4 de ancho» | «Precisión del 90 %» |
| Beta | «1.0 con un fold en 0» | «Unánime» |
| Holdout | «16 con 2 535 ventanas» | «Validación amplia» |
| Hashes | «d6c70142 y bf9620a7 en disco» | Hashes viejos (7acba335/d0c5ed7f eran B) |

La tabla completa con MAE, R² y NASA vive en [[e00-cifras-autoritativas]]. Aquí solo practicas cómo contarla.

## La lista negra (no se dicen)

`4.352`, `4.344`, `4.301` son corridas históricas; `4.340 ± 0.101` y `4.251` son bundle B reemplazado por el C (`4.322 ± 0.064`, fila `4.338`); `4.9026` y `4.8433` son macros viejos reemplazados por `5.0153`; `051e0af4` y `0acd795b` son hashes viejos; `6.233`, `6.347` y `6.22` son BiLSTM de otras corridas.

Si el tribunal cita una, respondes: «Esa es del bundle B o de una corrida anterior; el artefacto en disco (bundle C) da 4.338».

## Frases hechas que funcionan

«El híbrido-C da cuatro treinta y dos en media y cuatro treinta y ocho en disco.» «La LGBM adaptada da siete cero siete y el BiLSTM cinco sesenta y cinco.» «La fila da siete siete con el MLP E2.» «La banda cubre todo porque es ancha donde debe serlo: veintiséis ciclos.»

Nada de «nuestro modelo alcanza una precisión del…»: no es precisión, es RMSE y cobertura.

## Di esto en el tribunal

> [!quote]
> «Toda cifra que digo sale de una sola página y del manifiesto. En voz redondeo y en pantalla muestro exacto. Si me citas una cifra vieja, te digo de qué corrida era y cuál la reemplaza.»

## Flashcards

> [!question]- ¿Cómo dices el híbrido?
> 4.32 de media y 4.34 en disco (bundle C), desde e00.

> [!question]- ¿Cómo dices la banda?
> 100 % de cobertura con 26.4 de ancho, nunca precisión.

> [!question]- ¿Qué haces si citan 4.352?
> Dices que es del bundle B o de una corrida anterior y das 4.338 de disco (bundle C).

> [!question]- ¿Qué afirma esta nota en una frase?
> Decís redondeado en voz y exacto en pantalla, siempre desde la única fuente.

> [!question]- ¿Cómo la contarías en el tribunal?
> «Toda cifra que digo sale de una sola página y del manifiesto. En voz redondeo y en pantalla muestro exacto. Si me citas una cifra vieja, te digo de qué corrida era y cuál la reemplaza.»

> [!question]- ¿A qué nota vas si fallas esta idea?
[[e00-cifras-autoritativas]]

> [!question]- ¿A qué nota vas si fallas esta idea?
[[e00-cifras-autoritativas]]

> [!question]- ¿A qué nota vas si fallas esta idea?
[[e00-cifras-autoritativas]]

> [!question]- ¿A qué nota vas si fallas esta idea?
[[e00-cifras-autoritativas]]

