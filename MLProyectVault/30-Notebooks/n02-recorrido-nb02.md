---
tipo: notebook
status: sin-estudiar
tags:
  - nb02
  - ablacion
  - ensamble
---

# NB02 — Decisión, ablación y ensamble

> [!abstract] En una frase
> Este cuaderno decide: mide el contador de ciclos, elige beta fuera de fold y combina con banda.

## Antes de empezar

Requiere los artefactos de NB01: `[LOAD NB1 OK] dev (17450, 50, 19)` y BiLSTM recargado. Sin ese puente no hay nada que ablacionar ni combinar.

Tarda lo más pesado del proyecto: el OOF ronda 270–600 s según máquina porque reentrena por fold. La celda final deja `beta = 1.0` y `p_ens (6196,)`.

## Recorrido celda a celda

| Celda | Qué entra | Qué hace | Qué sale | Por qué está ahí |
|---|---|---|---|---|
| 3 | Artefactos NB01 | Recarga dev, test y BiLSTM | `[LOAD NB1 OK]` con formas intactas | Verifica la cadena de estado |
| 5 | `cyc_norm` on/off | Ablación del contador | BiLSTM 6.006 con y 5.784 sin en esa ejecución | Mide el atajo del reloj |
| 7 | Ventanas dev | OOF agrupado por motor | Folds `[[2,10],[5,18],[20,16]]`, ~270 s | Predicciones que ningún modelo vio |
| 8 | OOF y grid | Elige `beta` | `beta_hat = 1.00`, IQR 0.5 | Shrinkage honesto |
| 9 | Protocolo legado | Diagnóstico del fallo viejo | RMSE 6.347 vs 9.335, cociente 0.68 | Enseña la fuga para no repetirla |
| 10 | Unidad 16 | Ajusta meta RidgeCV + LGBM | 2 535 ventanas, RUL 0–62, coefs `[0.14, 0.77]` | Meta pequeño en holdout puro |
| 11 | Test 11/14/15 | Tabla titular | Híbrido 4.276 con NASA 2322.4 en esa ejecución | El número que se defiende |
| 13 | Banda OOF | Calibra por tramo | 17 450 ventanas, objetivo 90 % | Cota antes de decidir |
| 14 | Test + banda | Mide cobertura | 100 % con ~25.9 de ancho en esa ejecución | Conservadora y medida |
| 15 | Todo NB02 | Guarda estado | `[NB2 OK] beta = 1.0` | Puente hacia NB03 |

Las cifras de las celdas 11–14 son salida de esa ejecución. El bundle vigente es ≈4.34 ± 0.10 con fila 4.251 ([[e00-cifras-autoritativas]]).

## Las 5 celdas que importan

1. Celda 5: la ablación que impide mitificar el ciclo.
2. Celda 7: el OOF que separa motores enteros.
3. Celda 8: `beta_hat = 1.00` con su dispersión.
4. Celda 10: el meta ajustado solo en la 16.
5. Celda 11: la tabla donde el híbrido gana al campeón.

## Salidas que hay que saber leer

`beta_hat = 1.00` con `{min: 0.0, max: 1.0, iqr: 0.5}` significa mayoría con un disidente: dos folds piden meta completo y uno pide campeón ([[s09-oof-y-beta]]).

`banda 100.0 / 25.92 / 0.0 / 0.0` significa cobertura total con 25.9 de ancho y cero filas fuera. Ancha y honesta, no precisa y falsa.

## Qué NO hace este cuaderno

No prueba multisemilla ni diagnostica por motor fino: eso es NB03. No persiste el bundle final en `models/`: eso también es NB03.

## Si falla algo

Si el OOF tarda demasiado, baja `epochs` a 15 como en `oof_base_predictions`: es diagnóstico, no final. Si la banda colapsa a 3.4 de ancho, recalibraste en la 16: vuelve a 17 450 ([[s11-banda-conformal]]).

> [!quote] Di esto en el tribunal
> «En el segundo cuaderno ablaciono el ciclo, calculo OOF por motor y elijo beta 1.0 fuera de fold. Combino con meta en la 16 y calibro banda con 17 450 residuales. El híbrido da 4.28 en esa ejecución.»

## Flashcards

> [!question]- ¿Qué deja la celda 3?
> `[LOAD NB1 OK]` con dev y test intactos más BiLSTM recargado.

> [!question]- ¿Qué elige la celda 8?
> `beta_hat = 1.00` con IQR 0.5 y un fold en 0.0.

> [!question]- ¿Qué mide la celda 10?
> Meta en 2 535 ventanas de la 16 con RUL 0 a 62.

> [!question]- ¿Qué deja la celda final?
> `[NB2 OK] beta = 1.0` y `p_ens (6196,)` para NB03.

> [!question]- ¿Qué afirma esta nota en una frase?
> Este cuaderno decide: mide el contador de ciclos, elige beta fuera de fold y combina con banda.

> [!question]- ¿Cómo la contarías en el tribunal?
> «En el segundo cuaderno ablaciono el ciclo, calculo OOF por motor y elijo beta 1.0 fuera de fold. Combino con meta en la 16 y calibro banda con 17 450 residuales. El híbrido da 4.28 en esa ejecución.»

