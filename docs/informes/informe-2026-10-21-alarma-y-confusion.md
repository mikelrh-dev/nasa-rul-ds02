# Matriz de confusión del artefacto enviado, leído como alarma de mantenimiento

**Fecha:** 2026-10-21
**Instrumento:** `scripts/probe_alarm_confusion.py`
**Sujeto:** el bundle que se envía (`models/ensemble.joblib`), semilla primaria, test
**Unidad de conteo:** ventana (paso 2, ventana 50) — 6 196 ventanas de 3 motores

La RUL es una regresión. Para tener matriz hay que elegir un umbral, y el único con
sentido operativo es **"fallo inminente": `RUL <= umbral`**. Falso negativo = se declara
sano y faltan ≤ `umbral` ciclos (el lado caro de la NASA). Falso positivo = alarma con
el motor sano (mantenimiento innecesario).

## 1. Matriz por ventana

| umbral | TP | FP | FN | TN | precisión | recall | F1 | FPR | balAcc | MCC |
|---|---|---|---|---|---|---|---|---|---|---|
| 20 | 1 973 | 17 | 169 | 4 037 | 0,99 | 0,92 | 0,95 | 0,00 | 0,96 | 0,93 |
| **30** | **2 898** | **61** | **207** | **3 030** | **0,98** | **0,93** | **0,96** | **0,02** | **0,96** | **0,91** |
| 40 | 3 766 | 162 | 240 | 2 028 | 0,96 | 0,94 | 0,95 | 0,07 | 0,93 | 0,86 |
| 50 | 4 644 | 201 | 364 | 987 | 0,96 | 0,93 | 0,94 | **0,17** | 0,88 | 0,72 |

## 2. Por motor (umbral 30)

| motor | n | reales+ | TP | FP | FN | TN | recall | precisión |
|---|---|---|---|---|---|---|---|---|
| 11 | 3 293 | 1 761 | 1 559 | **0** | **202** | 1 532 | 0,89 | 1,00 |
| 14 | 760 | 334 | 329 | 0 | 5 | 426 | 0,99 | 1,00 |
| 15 | 2 143 | 1 010 | 1 010 | **61** | 0 | 1 072 | 1,00 | 0,94 |

Todos los FN están en el motor que se **sobre**estima (+3,06) y todos los FP en el que se
**sub**estima (−2,20). El motor con peor RMSE (14, sesgo −5,14) clasifica casi perfecto.

## 3. Dónde vive el error (sesgo y RMSE por tramo de RUL real)

| motor | 0–20 | 20–40 | 40–60 | 60+ |
|---|---|---|---|---|
| 11 | +1,0 / 1,36 | +3,7 / 4,08 | +4,7 / 5,04 | — |
| **14** | +1,1 / 1,24 | −0,6 / 2,42 | **−10,2 / 10,49** | **−13,8 / 13,84** |
| 15 | −0,6 / 0,88 | −1,9 / 2,22 | −3,5 / 3,68 | −4,4 / 4,44 |

(formato: sesgo / RMSE; n = 1 174 / 1 035 / 1 084 en el 11, 216 / 198 / 208 / 138 en el 14,
648 / 652 / 650 / 193 en el 15)

## 4. Antelación de la alarma (umbral 30)

| motor | cruce real | primer aviso | antelación | veredicto |
|---|---|---|---|---|
| 11 | ciclo 29 | ciclo 31 | **−2** | tarde |
| 14 | ciclo 46 | ciclo 46 | 0 | a tiempo |
| 15 | ciclo 37 | ciclo 34 | **+3** | a tiempo |

## 5. Gravedad de cada fallo

| umbral | FN | RUL real media | predicha | error medio | peor | FN con error > 10 |
|---|---|---|---|---|---|---|
| 20 | 169 | 19,1 | 20,9 | +1,8 | **+3,4** | **0** |
| 30 | 207 | 28,5 | 33,3 | +4,8 | **+9,1** | **0** |
| 40 | 240 | 37,4 | 42,7 | +5,3 | +6,8 | **0** |

| umbral | FP | RUL real media | predicha | error medio |
|---|---|---|---|---|
| 20 | 17 | 21,0 | 19,9 | −1,1 |
| 30 | 61 | 31,8 | 29,1 | −2,6 |
| 40 | 162 | 44,0 | 37,2 | −6,8 |

## 6. Lectura

1. **Como alarma a 30 ciclos, el modelo es bueno**: MCC 0,91, recall 0,93, precisión 0,98,
   y **ningún falso negativo con error mayor de 10 ciclos**. No hay fallo catastrófico: el
   peor FN acierta la RUL con +9,1 de error y todavía deja ~19 ciclos de margen.
2. **La matriz no mejora el veredicto de regresión; lo esconde.** El umbral cae en la
   banda donde el modelo es casi exacto (0–20: RMSE 0,88–1,36). El defecto vive en 40–70,
   donde el modelo se equivoca 10–14 ciclos **y la decisión binaria no cambia**: ambos
   lados están lejos del umbral. Un error grande puede ser un TN. La calibración de §7.5
   lo confirma: en el tramo 40–60 el sesgo es +0,12 pero el 10,7 % de las ventanas se
   equivoca en más de 10 ciclos.
3. **Los FN/FP no miden precisión, miden el signo del sesgo.** Los 202 FN del motor 11 y
   los 61 FP del 15 son el mismo mecanismo con signos opuestos. El motor 14 —el peor
   modelo— clasifica casi perfecto porque su sesgo aparece por encima del umbral.
4. **La antelación es correcta por suerte, no por diseño**: −2 / 0 / +3 ciclos sobre un
   horizonte de 30 (7 % de margen). Si el sesgo de cada motor hubiera caído del otro lado,
   los FN serían FP sin cambiar nada del modelo.
5. **El defecto empieza a verse cuando el horizonte se acerca a la zona sesgada**: FPR
   0,02 a umbral 30 y **0,17 a umbral 50**. Para compra de repuestos de plazo largo
   (horizonte 50) el modelo alarma en falso el 17 % del tiempo sano.
6. **Aviso estadístico**: 6 196 ventanas solapadas de **3 motores**. El `n` real es 3; la
   matriz mide cobertura temporal, no muestra independiente. Un F1 de 0,96 aquí no es
   evidencia de fiabilidad de flota.

## 7. Cifras de calidad completas

Instrumento: `scripts/evaluate_model_quality.py` (mismo bundle, misma semilla).

### 7.1 Regresión

| ámbito | n | RMSE | MAE | mediana AE | p90 | p95 | peor | sesgo | R² | NASA |
|---|---|---|---|---|---|---|---|---|---|---|
| pooled | 6 196 | 4,289 | 3,179 | 2,504 | 6,36 | 8,34 | 16,1 | +0,236 | 0,9473 | 2 310,6 |
| motor 11 | 3 293 | 3,77 | 3,10 | 2,74 | — | 6,64 | — | **+3,06** | 0,952 | 1 302 |
| motor 14 | 760 | **8,17** | 6,13 | 3,50 | — | 14,25 | — | **−5,14** | 0,861 | 581 |
| motor 15 | 2 143 | 2,76 | 2,26 | 1,82 | — | 4,99 | — | **−2,20** | 0,979 | 428 |

### 7.2 Exactitud por tolerancia (6 196 ventanas)

| tolerancia | acierta | ventanas fuera |
|---|---|---|
| ±5 ciclos | **79,7 %** | 1 259 |
| ±10 ciclos | **95,9 %** | 256 |
| ±15 ciclos | **99,8 %** | 14 |
| ±20 ciclos | **100,0 %** | 0 |

### 7.3 Ventanas sin solape (248 ventanas, 50 filas sin compartir)

RMSE **4,34** | MAE 3,19 | sesgo +0,24 | R² 0,946

| umbral | TP | FP | FN | TN | acierta | recall | precisión |
|---|---|---|---|---|---|---|---|
| 20 | 80 | 1 | 5 | 162 | 97,6 % | 0,94 | 0,99 |
| 30 | 116 | 2 | 8 | 122 | **96,0 %** | 0,94 | 0,98 |
| 40 | 150 | 6 | 10 | 82 | 93,5 % | 0,94 | 0,96 |

**La matriz solapada no estaba inflada**: a umbral 30 da 96,0 % aquí y 95,7 % allí.

### 7.4 Intervalos por bloque bootstrap (bloques de 5 ciclos, 2 000 remuestreos)

| métrica | valor | IC 95 % |
|---|---|---|
| RMSE | 4,29 | **[3,51 · 5,03]** |
| MAE | 3,18 | **[2,49 · 3,89]** |
| recall @30 | 0,93 | **[0,83 · 1,00]** |
| precisión @30 | 0,98 | **[0,92 · 1,00]** |

El intervalo del **nivel** es ±0,76, que corresponde a un error estándar de ≈0,39. Una
mejora de 0,4 está por tanto en el límite de lo detectable con tres motores; solo un
diseño pareado (mismas ventanas, dos modelos) resolvería por debajo de eso.

### 7.5 Calibración por tramo de RUL predicha

| predicho | n | real medio | sesgo | mediana AE | % con \|e\| > 10 |
|---|---|---|---|---|---|
| 0–20 | 1 990 | 9,3 | +0,38 | 0,86 | 0,0 % |
| 20–40 | 1 938 | 29,6 | +0,19 | 2,66 | 1,2 % |
| 40–60 | 2 170 | 50,6 | +0,12 | 4,73 | **10,7 %** |
| 60+ | 98 | 59,4 | +0,84 | 3,20 | 0,0 % |

El sesgo **por tramo** es casi nulo (+0,12 a +0,84): el modelo está bien calibrado
en media y mal distribuido. El sesgo que duele es **por motor** (+3,06 / −5,14 /
−2,20), y se cancela en el pooled hasta +0,24. Por eso un recalibrado global no
arregla nada y solo sirve información específica del motor.

### 7.6 Barrido de umbral y dónde se rompe

| umbral | acierta | recall | precisión | FPR | kappa |
|---|---|---|---|---|---|
| 10 | 98,4 % | 0,92 | 0,99 | 0,00 | 0,95 |
| 20 | 97,0 % | 0,92 | 0,99 | 0,00 | 0,93 |
| **30** | **95,7 %** | **0,93** | **0,98** | **0,02** | **0,91** |
| 40 | 93,5 % | 0,94 | 0,96 | 0,07 | 0,86 |
| 45 | 91,1 % | 0,93 | 0,95 | 0,14 | 0,78 |
| 50 | 90,9 % | 0,93 | 0,96 | 0,17 | 0,72 |
| 55 | 91,3 % | 0,95 | 0,95 | 0,37 | 0,56 |
| 60 | 94,5 % | 0,99 | 0,96 | **0,91** | 0,11 |

Desde 45 el kappa cae en picado. **No es solo el sesgo**: a umbral 60 el 94 % de las
ventanas son positivas y la clase se degenera, así que kappa y FPR dejan de informar.
El rango útil de umbral es **10–40**.

## 8. Predicción falsable

Si se quita el reloj absoluto (P3.2), esta tabla debería **empeorar en 0–30 y mejorar en
40–70**: la banda donde hoy clasifica perfecto es justo la que sostiene el atajo
`RUL ≈ 63 − ciclo`. Si al quitar el reloj la matriz no se mueve, el atajo no era el
mecanismo.
