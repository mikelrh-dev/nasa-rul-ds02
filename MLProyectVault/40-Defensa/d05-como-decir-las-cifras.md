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

En voz redondeas (`≈4.3`, `≈7.1`, `≈6.2`) y en pantalla muestras la tabla de [[e00-cifras-autoritativas]]. Nunca recitas decimales de memoria: los lees.

Si te piden la fuente, dices: «Sale del manifiesto y está compilado en e00». Si discrepan, gana el manifiesto.

## Qué decir para cada bloque

| Bloque | Decís | No decís |
|---|---|---|
| Híbrido | «4.34 de media, 4.25 en disco» | 4.352 ni 4.289 |
| Bases | «7.10 el árbol, 6.22 el BiLSTM» | 6.233 suelto sin dispersión |
| Macro | «4.84 macro frente a 4.25 ponderado» | Solo el ponderado |
| Banda | «100 % con 26.4 de ancho» | «Precisión del 90 %» |
| Beta | «1.0 con un fold en 0» | «Unánime» |
| Holdout | «16 con 2 535 ventanas» | «Validación amplia» |
| Hashes | «7acba335 y d0c5ed7f en disco» | Hashes viejos |

La tabla completa con MAE, R² y NASA vive en [[e00-cifras-autoritativas]]. Aquí solo practicas cómo contarla.

## La lista negra (no se dicen)

`4.352`, `4.344`, `4.301` son corridas históricas; `4.289` es fila vieja reemplazada por `4.251`; `4.9026` es macro viejo reemplazado por `4.8433`; `051e0af4` y `0acd795b` son hashes viejos; `6.233` y `6.347` son BiLSTM de otras corridas.

Si el tribunal cita una, respondes: «Esa es de una corrida anterior; el artefacto en disco da 4.251».

## Frases hechas que funcionan

«El híbrido da cuatro tres en media y cuatro veinticinco en disco.» «El árbol da siete uno y el BiLSTM seis dos con medio punto de dispersión.» «La banda cubre todo porque es ancha donde debe serlo: veintiséis ciclos.»

Nada de «nuestro modelo alcanza una precisión del…»: no es precisión, es RMSE y cobertura.

## Di esto en el tribunal

> [!quote]
> «Toda cifra que digo sale de una sola página y del manifiesto. En voz redondeo y en pantalla muestro exacto. Si me citas una cifra vieja, te digo de qué corrida era y cuál la reemplaza.»

## Flashcards

> [!question]- ¿Cómo dices el híbrido?
> 4.34 de media y 4.25 en disco, desde e00.

> [!question]- ¿Cómo dices la banda?
> 100 % de cobertura con 26.4 de ancho, nunca precisión.

> [!question]- ¿Qué haces si citan 4.352?
> Dices que es corrida anterior y das 4.251 de disco.

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

