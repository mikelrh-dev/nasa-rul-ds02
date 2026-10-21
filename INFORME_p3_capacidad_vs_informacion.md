# P3 — ¿capacidad del modelo o información ausente? (`dev` para decidir; lecturas descriptivas de test en §4.ter y §4.quater)

Fecha: 2026-10-21. Pregunta: el sesgo de vida alta, ¿se arregla con otra clase de
modelo (XGBoost, más capacidad) o falta información en las features?

Instrumento: ventanas `dev` puntuadas **fuera de fold** por motor (3 folds
agrupados, preprocesado reajustado dentro de cada fold). Solo rama tabular, para
que la comparación aísle el estimador. La alineación del caché se verificó: el
reajuste con `alpha=0.35` reproduce la columna cacheada con diferencia máxima
**0,0**, así que todos los brazos se puntúan en las mismas filas.

Las secciones 1–3 y la §4.bis deciden con `dev` y no tocan test. Las §4.ter y
§4.quater son las **dos únicas** excepciones, y están declaradas: describen el
artefacto ya enviado (cuánto hay en juego, y si su error sigue la ley de vida).
Ninguna se usó para elegir un brazo y ninguna autoriza a ajustar contra test;
son diagnóstico sobre lo que ya está desplegado, no banco de pruebas.

Scripts: `scripts/probe_capacity_vs_information.py`,
`scripts/probe_quantile_sweep.py`, `scripts/probe_alpha_hybrid_gate.py`,
`scripts/probe_p33_information_ceiling.py` (§4.bis), `scripts/probe_density_shift.py`
(§4.quater).

## 1. Clase de modelo

| brazo | macro | RMSE | RMSE>65 | sesgo>65 | RMSE≤62 | NASA |
|---|---|---|---|---|---|---|
| A0 LGB q0.35 `cyc_norm` (enviado) | 8,36 | 9,11 | 17,79 | −16,78 | 6,89 | 18 129 |
| A2 **XGB** q0.35 `cyc_norm` | 8,23 | **9,10** | 18,46 | −17,47 | 6,58 | 17 698 |
| A3 LGB + fracción de vida (oráculo) | 7,06 | 7,86 | 15,75 | −14,83 | 5,85 | 14 116 |
| A4 **XGB** + fracción de vida (oráculo) | 6,92 | **7,84** | 16,23 | −15,35 | 5,61 | 13 786 |
| A7 LGB + **vida total L** (oráculo) | 4,70 | **4,90** | 7,84 | −5,86 | 4,34 | 8 462 |
| A8 LGB q0.50 + fracción de vida | 6,33 | 6,75 | 11,95 | −10,92 | 5,59 | 12 099 |

**XGBoost no aporta nada**: 9,10 contra 9,11 de RMSE, macro 0,13 mejor, y en la
banda que duele es peor (18,46 contra 17,79). Con el oráculo pasa lo mismo
(7,84 contra 7,86). La clase de modelo no es el cuello de botella.

## 2. De dónde viene el sesgo

| fuente | efecto en el sesgo de `y>65` | efecto en RMSE |
|---|---|---|
| objetivo `quantile 0.35` | **−3,4 ciclos** | −0,93 (con α=0,50) |
| representación (fracción de vida) | −2,0 | −1,25 |
| **vida total L** | **−10,9** | 9,11 → **4,90** |
| residual | −1,9 | — |

Dos comprobaciones que acotan el resultado:

* Una regresión **`[cycle, L]` da RMSE 0,00**. Es una tautología (`RUL = L − cycle`),
  y por eso es informativa: el problema de vida alta no tiene estructura
  no-lineal que aprender, se reduce a **un escalar por motor**.
* La fracción de vida (`cycle/L`) sola recupera poco (−1,25) porque a una fracción
  dada, motores de vida distinta tienen RUL distinta; los árboles no pueden
  deshacer esa ambigüedad sin el valor de L.

## 3. El objetivo cuantílico, medido

Barrido sobre las mismas filas (`dev` OOF, rama tabular):

| α | macro | RMSE | RMSE>65 | sesgo>65 | RMSE≤62 | NASA |
|---|---|---|---|---|---|---|
| 0,35 | 8,36 | 9,11 | 17,79 | −16,78 | 6,89 | 18 129 |
| 0,40 | 8,21 | 8,85 | 17,04 | −16,01 | 6,82 | 17 817 |
| 0,45 | 7,97 | 8,44 | 15,76 | −14,78 | 6,74 | 16 944 |
| **0,50** | **7,79** | 8,18 | 14,40 | −13,35 | 6,83 | **16 649** |
| 0,55 | 7,81 | 8,16 | 13,27 | −12,06 | 7,13 | 17 187 |
| 0,60 | 7,79 | 8,13 | 12,29 | −10,94 | 7,34 | 17 544 |

α=0,50 es el óptimo conjunto de macro, RMSE, NASA y banda normal, y los vecinos
están a menos de una décima, así que no es un punto de suerte. Con oráculo de L,
α=0,40 es el mejor (macro 4,57).

Gate del **híbrido** (no solo la rama), reutilizando el `p_lstm` cacheado y
reseleccionando β:

| α | β | macro | RMSE | RMSE>65 | RMSE≤62 | NASA | folds |
|---|---|---|---|---|---|---|---|
| 0,35 | 1,00 | 11,23 | 13,15 | 24,46 | 9,71 | 26 355 | 1,00 / 1,00 / 0,00 |
| **0,50** | 1,00 | **10,31** | **12,09** | **22,94** | **8,76** | **22 518** | 1,00 / 1,00 / 0,00 |

Pasa en las cinco métricas. β no cambia y sus votos por fold son idénticos, así
que la ganancia no es un artefacto de reponderación. Decisión registrada en
`ADR-007`, que supersede `ADR-003`.

## 4. Qué significa

* **No hay techo de modelo.** XGBoost empata; añadir capacidad no compra nada
  medible. Cualquier plan de "escalar el modelo" tiene que justificarse con otra
  medición, no con la intuición.
* **Sí hay una variable ausente**: la vida total del motor explica 10,9 de los
  16,8 ciclos de sesgo. No es "más filas" —P0 ya midió que la densidad no mueve
  el sesgo— es un escalar que el dataset no entrega en inferencia.
* **Y hay un techo de datos para estimarla**: 6 motores dev de 63 a 89 ciclos,
  ninguno fuera de ese rango. Es el objeto de P3.1, y con n=6 debe reportarse como
  indeterminado si no supera un criterio declarado de antemano.

## 4.bis P3.3 ejecutado — la media condicional por k-NN no bate a `p_lgb`

Instrumento: `scripts/probe_p33_information_ceiling.py`, sobre las 17 450 filas
OOF del caché P1 (alineación verificada fila a fila: objetivos y motores
idénticos, cobertura de folds exactamente 1). `E[y|X]` por k-NN (k=50) en el
espacio estandarizado de cada fold, ajustado solo con motores de otros folds.

| brazo | macro | RMSE | RMSE>65 | sesgo>65 | RMSE≤62 | NASA |
|---|---|---|---|---|---|---|
| `p_lgb` (enviado) | 8,36 | 9,11 | 17,79 | −16,78 | 6,89 | 18 129 |
| k-NN `E[y|X]`, 93 col | 11,73 | 11,89 | 22,11 | −20,87 | 9,68 | 34 592 |
| k-NN sin reloj, 92 col | 12,45 | 12,59 | 23,34 | −22,13 | 10,27 | 39 155 |

**El resultado no decide lo que P3.3 debía decidir.** El k-NN pierde por 2,78 de
RMSE, pero eso es compatible con dos lecturas y este instrumento no las separa:
(a) las features ya no contienen más, o (b) un promedio local en 93 dimensiones no
puede explotar lo que sí contienen (maldición de la dimensionalidad).

Sí aporta dos datos laterales: quitar el reloj empeora 0,70, así que el ciclo
sí transporta señal; y el sesgo de vida alta del k-NN es **todavía más negativo**
(−20,87), lo que es consistente con que las features no separen filas de vida
alta, pero está confundido con el sesgo propio del estimador. Para cerrar P3.3
haría falta un vecindario de pocas dimensiones (ciclo + magnitud de residuo), no
uno de 93.

## 4.ter ¿Cuánto hay realmente en juego en test?

Descomposición del SSE del artefacto enviado (6 196 ventanas, RMSE 4,289 de la
semilla primaria, SSE 113 988). Se mide una vez, con el bundle que se envía.

| subconjunto | n | % filas | RMSE | sesgo | % del SSE |
|---|---|---|---|---|---|
| todo | 6 196 | 100 % | 4,29 | −0,44 | 100 % |
| `y > 65` | **76** | **1,2 %** | 14,36 | **−14,34** | 13,8 % |
| `y > 40` | 2 190 | 35,3 % | 6,29 | −0,93 | 76,1 % |

| motor | n | RMSE | sesgo | % del SSE |
|---|---|---|---|---|
| 11 | 3 293 | 3,77 | **+3,06** | 41,1 % |
| **14** | 760 | **8,17** | **−5,14** | **44,6 %** |
| 15 | 2 143 | 2,76 | −2,20 | 14,3 % |

Dos consecuencias que reordenan el plan:

1. **La cola de vida alta pesa poco en la métrica de test.** Son 76 filas: aunque
   se arreglaran hasta el nivel del resto (RMSE 4,01), el RMSE global iría de
   4,289 a **4,008** — 0,28, un 6,6 %. El sesgo de vida alta es un problema real
   de seguridad, pero **no** el que mueve el titular.
2. **El error está en el motor 14**, con el 44,6 % del SSE y un sesgo de **−5,14**.
   Si el 14 bajara al nivel del 11 (3,77), el RMSE global caería a ≈3,46 (−0,83).
   Ese es el tamaño real de la carta que queda.

Y el patrón de signos confirma el mecanismo de P1: el motor 11 —el más corto— se
**sobre**estima (+3,06), el 14 —el más largo— se **sub**estima (−5,14), el 15 queda
en medio (−2,20). Es `RUL ≈ L₁₆ − ciclo` visto desde test, con tres motores y tres
signos ordenados por vida.

## 4.quater La densidad de la ventana no es el defecto del motor 14

La ventana es de **50 filas**, no de N ciclos. En los motores de ajuste (114–125
filas/ciclo) cubre **0,40–0,44 ciclos**; en el motor 14 de test, con 20,6
filas/ciclo, cubre **2,42 ciclos**. Eso sugería un desplazamiento de
representación justo en el motor que concentra el 44,6 % del SSE.

Instrumento: `scripts/probe_density_shift.py`. Se diezman motores de ajuste a la
densidad del 14 (~19–20 filas/ciclo) y se predicen las dos versiones con el
**mismo ensemble enviado**.

| motor | densidad | filas/ciclo | ventanas | RMSE | sesgo |
|---|---|---|---|---|---|
| 2 | natural | 113,8 | 2 828 | 6,97 | −5,30 |
| 2 | diezmado | 19,0 | 458 | **6,44** | −4,23 |
| 5 | natural | 116,1 | 3 429 | 15,65 | −12,70 |
| 5 | diezmado | 19,4 | 558 | **15,08** | −11,88 |
| 10 | natural | 116,2 | 3 160 | 11,58 | −9,63 |
| 10 | diezmado | 19,4 | 513 | **10,95** | −8,67 |

**Diezmar mejora el RMSE en los tres motores (−0,54 / −0,57 / −0,63) y reduce el
sesgo negativo en ~+0,95.** La densidad laxa del 14 no es lo que le hace daño; si
acaso, una ventana que abarca más tiempo es menos ruidosa. Queda descartada como
mecanismo, y con ella el rejillado por ciclos como carta.

Lo que sí queda en pie es la ley de sesgo de P1, comprobada ahora contra test:

| motor | vida L | sesgo medido | ley `−0,87·(L − 63)` |
|---|---|---|---|
| 11 | 59 | **+3,06** | +3,48 |
| 15 | 67 | **−2,20** | −3,48 |
| 14 | 76 | **−5,14** | −11,31 |

El signo y el orden se cumplen en los tres; la magnitud acierta en los dos cortos
y se queda corta en el 14, así que la ley predice la **dirección**, no el tamaño.

## 5. Limitaciones

* Los brazos con L son **oráculos no desplegables**: miden el techo, no un modelo.
* Salvo §4.ter y §4.quater, todo es `dev`; las cifras no son comparables con test
  (motores distintos, y test tiene 76 filas con `y>65` frente a 2 041 en `dev`).
  Esas dos secciones describen el artefacto enviado y **no** son banco de
  pruebas: cualquier cambio que se derive de ellas tiene que pasar el gate en
  `dev` antes de tocar el modelo, o es selección sobre test.
* La rama tabular aislada no es el sistema: el híbrido incluye el BiLSTM, el meta
  ajustado en el motor 16 y la EMA. El gate del híbrido (§3) es la cifra que
  autoriza el cambio.
