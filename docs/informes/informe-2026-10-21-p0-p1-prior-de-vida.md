# P0 + P1 — el sesgo de vida alta no es densidad: es el prior de vida del motor 16

Fecha: 2026-10-21. Estado: **P1 no pasa el gate en `dev` y no se consolida**. No se
leyó test, no se regeneraron artefactos y el notebook no se volvió a ejecutar, porque
nada de lo que se envía cambió.

---

## P0 — control de densidad (motores 2, 5 y 10, `dev`)

Se re-ventanearon dos motores a **20,6 filas/ciclo** (la densidad del motor 14) dejando
todo lo demás fijo: mismo escalador, mismo BiLSTM, mismo LightGBM, mismo meta. La vida
total del motor no cambia; solo el espaciado de filas dentro de la ventana de 50.

| motor | vida (ciclos) | densidad | n (y>65) | sesgo p_lstm | sesgo p_lgb | sesgo meta | RMSE meta (y>65) |
|---|---|---|---|---|---|---|---|
| 2 | 75 | natural (~114/ciclo) | 486 | −7,90 | −5,35 | −13,20 | 13,30 |
| 2 | 75 | **20,6/ciclo** | 68 | −7,46 | −6,63 | −14,13 | 14,18 |
| 5 | 89 | natural (~116/ciclo) | 1328 | −18,57 | −17,35 | −24,52 | 24,64 |
| 5 | 89 | **20,6/ciclo** | 216 | −19,88 | −17,12 | −24,55 | 24,62 |
| 10 | 82 | natural (~116/ciclo) | 916 | −13,85 | −10,87 | −18,55 | 18,64 |
| 10 | 82 | **20,6/ciclo** | 143 | −13,72 | −10,58 | −18,21 | 18,28 |

**Δ sesgo del meta al distorsionar la densidad: −0,93 / −0,03 / +0,34 ciclos.** La
densidad de muestreo **no** explica el error de vida alta. Queda descartada como causa
principal, y con ella la premisa de que la ventana de 50 filas "mezcla 2,4 ciclos" en el
motor 14 como mecanismo del sesgo.

### Lo que sí lo explica: la vida total del motor

Sesgo en `y > 65` sobre las predicciones **fuera de fold** de `dev`, contra la vida
máxima de cada motor:

| motor | vida L | sesgo p_lstm | sesgo p_lgb |
|---|---|---|---|
| 18 | 71 | −9,0 | −6,9 |
| 2 | 75 | −10,5 | −9,6 |
| 10 | 82 | −16,9 | −16,0 |
| 5 | 89 | −22,5 | −22,4 |

Regresión lineal sobre esos cuatro puntos:

* `p_lgb`: pendiente **−0,870** ciclos de sesgo por ciclo de vida, **sesgo nulo en L = 63,4**
* `p_lstm`: pendiente **−0,779**, sesgo nulo en L = **60,3**

63 es exactamente la vida del **motor 16**, el motor del `EarlyStopping` del BiLSTM y
del ajuste del meta. La conclusión operativa: el ensemble implementa, sin declararlo,
`RUL ≈ L₁₆ − ciclo`; todo motor que vive más que el 16 se subestima en ≈ 0,87 ciclos por
cada ciclo de vida extra, y los que viven menos se sobreestiman.

---

## P1 — meta consciente de soporte, nivel y discrepancia

Instrumento honesto: **predicciones base fuera de fold** (`oof_base_predictions`,
3 folds agrupados, 14 915 ventanas de 5 motores). El meta se ajusta siempre en el motor
16. Un primer intento con predicciones in-sample se descartó: en ese instrumento el
árbol ha memorizado los motores puntuados y el meta parece catastrófico por construcción
(de hecho `p_lgb` "gana" con 6,17 solo por eso).

| variante | macro RMSE | RMSE | RMSE y>65 | sesgo y>65 | RMSE y≤62 | NASA |
|---|---|---|---|---|---|---|
| M0 `free` 50/50 (**enviado**) | 11,23 | 13,15 | 24,46 | −23,75 | 9,71 | 26 355 |
| M1 `sum_to_one` 50/50 | 11,15 | 13,06 | 23,98 | −23,24 | 9,78 | 26 057 |
| M2 `sum_to_one` solo ridge | 11,25 | 13,05 | 23,64 | −22,93 | 9,93 | 26 180 |
| M3 M1 + gate 2 | 11,61 | 13,04 | 23,36 | −22,37 | 9,98 | 26 329 |
| M4 M1 + `relu(p_lgb−p_lstm)` | 11,38 | 13,34 | 25,02 | −24,33 | 9,68 | 26 896 |
| M6 `p_lgb` passthrough (referencia) | 8,40 | 9,26 | 17,75 | −16,74 | 6,61 | 15 077 |
| M7 `convex` (sin intercepto) | 9,50 | 10,93 | 21,03 | −20,16 | 7,76 | 18 898 |
| M8 `convex` + gate 2 | 9,78 | 10,97 | 20,66 | −19,63 | 7,96 | 19 292 |

### Veredicto del gate

* **M1 (nivel sum_to_one): falla.** −0,09 de RMSE total y −0,48 en `y>65` son ruido;
  `y≤62` empeora y la macro empeora en un motor.
* **M3 (gate de soporte): falla.** Mejora `y>65` (−1,10) pero **la macro empeora**
  (11,23 → 11,61) y el motor 20 pasa de 1,88 a 4,95. El gate dispara en el 6,9 % de las
  filas y no donde está el error.
* **M4 (discrepancia): falla.** Empeora la macro (11,38), el pooled (13,34), la banda alta
  (25,02) y NASA (26 896); en `y≤62` mejora 0,10, que no compensa nada de lo anterior.
* **A2 con cuantil 0.50:** no se implementó, porque M4 ya muestra que la información de
  discrepancia no ayuda al meta en este régimen.

**Nada se consolida.** `ensemble.py`, los artefactos y el notebook no se tocaron.
`pytest tests -q` → **10 passed** (la librería solo ganó un `MetaSpec` cuyo valor por
defecto reproduce el comportamiento enviado).

### Dos hallazgos que sí valen

1. **El meta enviado arrastra un desplazamiento de nivel, y está medido.** `free` tiene
   coeficientes [0,334, 0,613] (suma 0,947) y **intercepto −3,936**, ajustados sobre el
   sesgo del motor 16. La descomposición en la banda `y≤62` de los cinco motores:
   `p_lgb` −1,70, `p_lstm` −2,96, **meta −7,33**. El mapa afín convierte un sesgo de
   rama de −1,7 en −7,3, y eso cuesta **3,9 de RMSE** frente a usar solo `p_lgb` en
   14 915 filas honestas. Quitar el intercepto (M7 `convex`) mejora **todas** las
   métricas: macro −1,73, RMSE −2,22, `y>65` −3,43, `y≤62` −1,95. Nótese que
   `sum_to_one` **no** lo arregla: al reajustar el intercepto sobre las mismas filas del
   motor 16 lo empeora a −5,936, y por eso M1 gana tan poco.
2. **El gate en `dev` no puede arbitrar los pesos del meta.** En `dev` OOF las dos ramas
   están casi empatadas (`p_lstm` 9,62 vs `p_lgb` 9,29); en test el orden se invierte
   (`p_lstm` 5,69 vs `p_lgb` 7,09). Cualquier ajuste de mezcla aprendido en `dev`
   elige la rama equivocada para test: M7 pesa 0,96 en `p_lgb`, y enviarlo así
   reemplazaría el híbrido de 4,30 por ≈`p_lgb`. **Por eso M7 no se envía aunque gane en
   `dev`.** El gate puede arbitrar *estructura* (nivel, monotonía, soporte), no *reparto*.

También: `beta` sigue mal determinado (folds 1,00 / 1,00 / 0,00 en las tres variantes
probadas), y el fold que vota 0 es justamente el de los motores cortos (16 y 20), los
más parecidos a test.

---

## P3 — diseño propuesto: ¿el prior de vida es estimable o irreducible?

Pregunta: dado que el sesgo es −0,87 por ciclo de vida, ¿existe alguna función **causal**
de los datos del propio motor (ventanas ≤ t) que aporte información sobre su vida total
o su tasa de degradación, o el sesgo es irreducible con esta representación?

Restricción dura: hay **6 motores dev** (63–89 ciclos) y 3 de test. Cualquier regresión
de `L` sobre features tiene n = 6; el error estándar de `L` es ≈ 9,4 ciclos. Con esa `n`
no se puede demostrar nada por validación cruzada de `L`, así que P3 se ordena de lo
barato y decisivo a lo caro:

### P3.3 (minutos, sin reentrenar) — ¿estamos en el techo de información de las features actuales?

Para las filas OOF con `y>65`, estimar la **media condicional** `E[y | features]` con
k-NN (k=50) dejando fuera el motor de la fila, y comparar:

* `RMSE(p_lgb, y)` frente a `RMSE(E[y|features], y)`.

Si el modelo ya está pegado a la media condicional, ningún meta puede mejorarlo: el
problema es de **representación**, no de estimador. Coste: minutos sobre el caché OOF.
Este número decide si P3.4 vale la pena o no, y va primero por eso.

### P3.1 (1 h) — ¿alguna feature de vida temprana ordena a los motores por vida?

* Features: agregados causales de los primeros 10/20/30 ciclos (nivel residual, pendiente,
  varianza) por motor.
* Validación: leave-one-engine-out con **6 puntos**, y como referencia obligatoria el
  predictor trivial `L̄ = 77,7`.
* Criterio explícito de señal: `RMSE_LOOCV(L) < 7` ciclos **y** Spearman ρ > 0,5. Con
  n = 6 un resultado peor que eso **no es evidencia** y se reportará como indeterminado,
  no como "casi".

### P3.2 (1–2 h, un reentrenamiento, sin test) — quitar el reloj absoluto, no añadir features

Sustituir `cyc_norm` (= ciclo/100, que es lo que codifica el prior del motor 16) por un
índice de **estado** causal y comparable entre motores: magnitud del residuo sensor
normalizada por la línea base sana del propio motor, con EMA de 5 y 15 ciclos. La RUL
deja de poder inferirse del reloj y tiene que inferirse del desgaste.

Predicción falsable: si el prior de vida era la causa, el sesgo en `y>65` deja de ser
∝ (L − 63). Gate: sesgo al menos a la mitad hacia cero **y** RMSE OOF pooled sin
degradarse. Coste: un `run_seed` por semilla sobre `dev`, comparado contra el mismo
instrumento.

### P3.4 (solo si P3.1 da señal) — inyectar la fracción de vida

Una columna más en `X_tab` y un canal más en `X_seq`. Cambia el contrato
(`input_shape` 19→20, tabular 93→94, `bilstm_params`), así que exige actualizar
`tests/`, builder, artefactos y regenerar el notebook — el paquete caro. **No se lanza
antes de P3.3 y P3.1.**

### Si P3.3 dice "techo de información"

Entonces el sesgo es irreducible con DS02 tal como está: la media condicional en vida
alta está anclada en 63 porque ningún motor de ajuste aporta filas de vida alta
informativas. La única salida honesta es **más datos** (motores que vivan 60–120 ciclos),
no otro meta. Fingir vida alargando motores sintéticos queda descartado por fabricación.

---

## Qué quedó en el repo

* `src/ds02_rul/stacking.py`: `MetaSpec`, `meta_design`, `fit_meta`, `predict_meta` y
  `select_beta_grouped(..., meta_spec=...)`. Por defecto (`MetaSpec()`) el
  comportamiento es **idéntico** al enviado; no está cableado en `ensemble.py` ni en el
  notebook.
* `scripts/p0_density_control.py`, `scripts/p1_meta_support.py`,
  `scripts/p1_oof_cache.py`: los instrumentos, reproducibles.
* Cachés `_p1_*.npz` (predicciones dev in-sample y OOF) para no repetir el pase BiLSTM.
