# Evaluación general del modelo predictivo — DS02 hybrid stacking

**Fecha:** 2026-10-21
**Sujeto:** el bundle que se envía (`models/ensemble.joblib` + `bilstm_ds02.keras`)
**Pregunta:** ¿cómo de bueno es prediciendo, con todas las métricas disponibles?
**Regla de esta evaluación:** todo lo que sigue sale del artefacto en disco, de su
manifiesto o de un sondeo reproducible con script. Nada se ha re-ajustado para esta
medida y ningún hiperparámetro se eligió mirando test.

---

## 1. Qué se está evaluando

| campo | valor |
|---|---|
| dataset | N-CMAPSS **DS02** |
| versiones de código | `4.1.0` |
| python / TF / Keras / sklearn / LightGBM | 3.12.10 / 2.21.0 / 3.15.1 / 1.9.1 / 4.7.0 |
| semilla primaria | 42 |
| partición | ajuste `[2, 5, 10, 18, 20]` · holdout del meta `[16]` · **test `[11, 14, 15]`** |
| contrato de inferencia | ventana 50 filas · `beta = 1.0` · EMA 5 · canal de ciclo activo · meta de 2 columnas |
| forma | 18 canales escalados · 4 condiciones operativas · 93 features tabulares · BiLSTM `(None, 50, 19)`, 154 253 parámetros |
| meta-aprendiz | ajustado en el motor 16: 2 535 filas, RUL 0–62 |
| objetivo tabular | `quantile`, `alpha = 0.35` (ADR-003; el 0,50 se midió y se rechazó en ADR-007) |
| tamaño | `ensemble` 468 862 B · `bilstm` 1 935 767 B · **2 404 629 B (2,29 MiB)** |
| sha256 ensemble | `0acd795b0906389d46b7dc433249438e15b3ee899b1a5bc2cbd8624a6fe6d502` |
| sha256 bilstm | `5923d2a1548837929620a7fbb2bbc8284bc29cfe4f18ec94ef5417d291c9e9de` |

## 2. Protocolo y unidad de medida

Test: **6 196 ventanas** (paso 2, ventana 50) sobre **3 motores**, **76 ciclos únicos**,
RUL real de 0 a 73 (mediana 30).

Tres denominadores que no son intercambiables:

| denominador | n | qué informa |
|---|---|---|
| ventanas solapadas | 6 196 | cobertura temporal (cuenta la misma información ~25×) |
| ventanas **sin solape** | 248 | recuento honesto de aciertos y fallos |
| motores | **3** | lo único que generaliza a flota |

## 3. Métricas de regresión — las cifras de cabecera

### 3.1 Tres semillas (42, 7, 123) — media ± desviación

| modelo | RMSE | MAE | R² | NASA |
|---|---|---|---|---|
| LightGBM solo | 7,098 ± 0,034 | 5,572 ± 0,034 | 0,8557 ± 0,0014 | 5 772,5 ± 50,1 |
| BiLSTM solo | 6,233 ± **0,485** | 4,777 ± 0,485 | 0,8882 ± 0,0174 | 4 307,0 ± 604,9 |
| **híbrido + EMA5 (enviado)** | **4,352 ± 0,055** | **3,221 ± 0,036** | **0,9458 ± 0,0013** | **2 342,3 ± 28,0** |

El ensemble gana **1,88** de RMSE a la mejor rama y **2,75** a la tabular. Su varianza
entre semillas (±0,055) es **casi 9× menor** que la del BiLSTM (±0,485): el stacking también
estabiliza.

### 3.2 Artefacto concreto, semilla 42 (lo que se mide en el resto del informe)

| métrica | pooled | motor 11 | motor 14 | motor 15 |
|---|---|---|---|---|
| n (ventanas) | 6 196 | 3 293 | 760 | 2 143 |
| RMSE | **4,289** | 3,77 | **8,17** | 2,76 |
| MAE | 3,179 | 3,10 | 6,13 | 2,26 |
| mediana del error absoluto | 2,504 | 2,74 | 3,50 | 1,82 |
| p90 del error absoluto | 6,36 | — | — | — |
| p95 del error absoluto | 8,34 | 6,64 | **14,25** | 4,99 |
| peor error absoluto | **16,1** | — | — | — |
| sesgo | **+0,236** | **+3,06** | **−5,14** | **−2,20** |
| R² | 0,9473 | 0,952 | **0,861** | 0,979 |
| NASA score | 2 310,6 | 1 302 | 581 | 428 |

### 3.3 Media y macro

| métrica | valor |
|---|---|
| RMSE ponderado por ventana | **4,289** |
| **macro-RMSE (cada motor pesa 1/3)** | **4,903** |
| RMSE por motor | 3,773 / 8,175 / 2,760 |
| brecha ponderado↔macro | **+0,61** |

La brecha es la diferencia entre "lo que promedia la flota" y "lo que sufre un motor al
azar". El motor 14 aporta el 12 % de las ventanas y el **44,6 %** del error cuadrático.

## 4. Métrica de negocio: NASA score

`d = pred − real`; `score = Σ [exp(−d/13) − 1 si d<0; exp(d/10) − 1 si d>0]`

- **Es una suma**, no una media: escala con el número de filas (6 196) y solo es
  comparable entre modelos medidos en las mismas filas.
- **Es asimétrica**: sobreestimar cuesta ~1,3× más por ciclo que subestimar.
- Valor del híbrido: **2 310,6** (semilla 42) · **2 342,3 ± 28,0** (tres semillas).
  Frente a las ramas: 5 772,5 (tabular) y 4 307,0 (BiLSTM).

## 5. Exactitud operativa por tolerancia (6 196 ventanas)

| tolerancia | acierta | fuera | interpretación |
|---|---|---|---|
| ±5 ciclos | **79,7 %** | 1 259 | error mediano 2,5 ciclos |
| ±10 ciclos | **95,9 %** | 256 | lo que un planificador puede usar |
| ±15 ciclos | **99,8 %** | 14 | |
| ±20 ciclos | **100,0 %** | **0** | no hay error mayor de 16,1 |

Sobre vidas de 59–76 ciclos, el error mediano es un **3–4 % de la vida del motor**.

## 6. Lectura como alarma de mantenimiento (positivo = `RUL ≤ umbral`)

### 6.1 Ventanas sin solape (248) — la cifra defendible

| umbral | TP | FP | FN | TN | acierta | recall | precisión |
|---|---|---|---|---|---|---|---|
| 20 | 80 | 1 | 5 | 162 | 97,6 % | 0,94 | 0,99 |
| **30** | **116** | **2** | **8** | **122** | **96,0 %** | **0,94** | **0,98** |
| 40 | 150 | 6 | 10 | 82 | 93,5 % | 0,94 | 0,96 |

### 6.2 Barrido completo (6 196 ventanas solapadas)

| umbral | acierta | recall | precisión | F1 | FPR | kappa |
|---|---|---|---|---|---|---|
| 10 | 98,4 % | 0,92 | 0,99 | 0,96 | 0,00 | 0,95 |
| 20 | 97,0 % | 0,92 | 0,99 | 0,95 | 0,00 | 0,93 |
| **30** | **95,7 %** | **0,93** | **0,98** | **0,96** | **0,02** | **0,91** |
| 40 | 93,5 % | 0,94 | 0,96 | 0,95 | 0,07 | 0,86 |
| 45 | 91,1 % | 0,93 | 0,95 | 0,94 | 0,14 | 0,78 |
| 50 | 90,9 % | 0,93 | 0,96 | 0,94 | **0,17** | 0,72 |
| 60 | 94,5 % | 0,99 | 0,96 | 0,97 | **0,91** | 0,11 |

Rango útil: **10–40 ciclos**. A 45+ el sesgo del motor 14 genera falsas alarmas; a 60 el
94 % de las ventanas son positivas y kappa/FPR se degeneran por desbalance.

### 6.3 Por motor (umbral 30) y antelación

| motor | TP | FP | FN | recall | cruce real | primer aviso | antelación |
|---|---|---|---|---|---|---|---|
| 11 | 1 559 | 0 | **202** | 0,89 | ciclo 29 | ciclo 31 | **−2** |
| 14 | 329 | 0 | 5 | 0,99 | ciclo 46 | ciclo 46 | 0 |
| 15 | 1 010 | **61** | 0 | 1,00 | ciclo 37 | ciclo 34 | **+3** |

Todos los FN están en el motor sobreestimado (+3,06) y todos los FP en el subestimado
(−2,20). La clasificación mide **el signo del sesgo**, no la precisión.

### 6.4 Gravedad de cada fallo

| umbral | FN | RUL real media | predicha | peor error | FN con error > 10 |
|---|---|---|---|---|---|
| 20 | 169 | 19,1 | 20,9 | **+3,4** | **0** |
| 30 | 207 | 28,5 | 33,3 | **+9,1** | **0** |
| 40 | 240 | 37,4 | 42,7 | +6,8 | **0** |

No existe el fallo catastrófico: ningún falso negativo se equivoca en más de 10 ciclos.

## 7. Calibración: qué significa cada predicción

| RUL predicha | n | real medio | sesgo | mediana AE | % con error > 10 |
|---|---|---|---|---|---|
| 0–20 | 1 990 | 9,3 | +0,38 | **0,86** | 0,0 % |
| 20–40 | 1 938 | 29,6 | +0,19 | 2,66 | 1,2 % |
| 40–60 | 2 170 | 50,6 | +0,12 | **4,73** | **10,7 %** |
| 60+ | 98 | 59,4 | +0,84 | 3,20 | 0,0 % |

**Por tramo el modelo está bien calibrado** (sesgo +0,12 a +0,84). **Por motor no**
(+3,06 / −5,14 / −2,20), y los sesgos se cancelan en el agregado hasta +0,24. Consecuencia:
ningún recalibrado global puede arreglarlo; solo información del motor.

## 8. Incertidumbre de estas cifras

Bootstrap por bloques (41 bloques de 5 ciclos, 2 000 remuestreos, motor estratificado):

| métrica | valor | IC 95 % |
|---|---|---|
| RMSE | 4,29 | **[3,51 · 5,03]** |
| MAE | 3,18 | **[2,49 · 3,89]** |
| recall @30 | 0,93 | **[0,83 · 1,00]** |
| precisión @30 | 0,98 | **[0,92 · 1,00]** |

El intervalo del nivel es ±0,76 (error estándar ≈0,39): una mejora de 0,4 de RMSE está en
el límite de lo detectable con tres motores, y solo un diseño pareado resolvería por debajo.

## 9. Banda de predicción (split conformal)

| campo | valor |
|---|---|
| método | split conformal por tramo de RUL predicha, cuantiles asimétricos |
| tramos | `[0, 25) [25, 50) [50, 75) [75, ∞)` |
| cuantiles globales | [−22,48 · +17,94] ciclos |
| calibración | 17 450 ventanas fuera de fold de los 6 motores de desarrollo |
| objetivo | 90 % (5 % por lado) |
| **cobertura en test** | **100,0 %** (0 % por debajo, 0 % por encima) |
| **ancho medio** | **26,41 ciclos** → 26,92 / 26,03 / 25,75 por motor |
| rango de ancho | 7,85 – 46,29 ciclos |

Sobre-cubre por construcción: los residuales de calibración vienen de modelos de fold más
débiles que el enviado. Recalibrar en el motor 16 se midió y **se rechazó**: 3,35 de ancho
con **31,4 %** de cobertura. Una banda de ~12 ciclos al 90 % no es alcanzable honestamente
en esta partición.

## 10. Coste computacional y despliegue

| medida | valor |
|---|---|
| carga del bundle | **0,20 s** |
| inferencia, 1 ventana (llamada en frío) | 46 ms (dominado por overhead) |
| inferencia, 100 ventanas | 0,855 ms/ventana |
| inferencia, 6 196 ventanas | **1,71 s** (0,276 ms/ventana) |
| entrenamiento | BiLSTM ≈165 s por ajuste en CPU; corrida completa del notebook ≈30 min (README §Reproduce) |
| artefactos | 2,29 MiB, sin pickling del grafo Keras (referenciado por ruta) |

Los tiempos son reloj de pared en esta máquina (Windows, CPU, TF 2.21) medidos con
`time.perf_counter` alrededor de `predict()`, con una llamada de calentamiento previa; no
hay script que los reproduzca y variarán en otro hardware. Lo que **sí** es reproducible
son los tamaños y los SHA-256, que salen del manifiesto.

## 11. Qué NO se puede afirmar con estos datos

1. **Fiabilidad de flota**: `n` efectivo = 3 motores. El recall real puede ser 0,83.
2. **Comparación con literatura** sobre otro split: el NASA score es una suma sobre 6 196
   filas de estos motores; no es comparable con FD001 ni con otros subconjuntos.
3. **Robustez a vida larga**: el único motor de test con RUL > 60 tiene 98 ventanas, y el
   holdout del meta no pasa de 62 ciclos.
4. **Generalización a otra densidad de muestreo**: los motores de ajuste traen 114–125
   filas/ciclo y el 14 trae 20,6 (ventana de 0,43 vs 2,42 ciclos).
5. **Mejoras pequeñas**: cualquier cambio por debajo de ~0,4 de RMSE no es distinguible con
   esta muestra sin diseño pareado.

## 12. Veredicto

| eje | nota | por qué |
|---|---|---|
| **Predicción puntual** | **7,0 / 10** | 4,35 ± 0,055 (≈6 % de la vida), 96 % dentro de ±10, pero p95 de 8,3 y el motor 14 con R² 0,861 |
| **Como alarma (20–40 ciclos)** | **8,5 / 10** | 96 % de acierto, kappa 0,91, cero fallos >10 ciclos, aviso dentro de ±3 ciclos |
| **Calibración global** | **8,0 / 10** | sesgo por tramo ≤0,84; se rompe al estratificar por motor |
| **Rigor de la evaluación** | **8,5 / 10** | tres denominadores, bootstrap por bloques, cuatro experimentos negativos documentados |
| **Despliegue** | **8,5 / 10** | 2,29 MiB, carga 0,2 s, 0,28 ms/ventana, artefacto auditable |
| **Cobertura de la muestra** | **4,0 / 10** | 3 motores de test, un holdout de 63 ciclos |

**Resumen en una frase:** el modelo está **bien calibrado en media, mal repartido entre
motores**; acierta la decisión de mantenimiento (96 %) y aproxima la RUL a ±10 ciclos en el
96 % de las ventanas, pero su error es un desplazamiento de nivel por motor —función de la
vida total, que no observa— y no ruido: por eso el RMSE es 4,29 y el peor motor 8,17.

---

### Reproducibilidad

| script | qué produce |
|---|---|
| `scripts/evaluate_model_quality.py` | §3.2, §5, §6.1–6.2, §7, §8 |
| `scripts/probe_alarm_confusion.py` | §6.3, §6.4 |
| `scripts/probe_p33_information_ceiling.py` | contraste k-NN (no concluyente) |
| `scripts/probe_density_shift.py` | efecto de la densidad de muestreo |
| `scripts/probe_band_coverage.py` | §9 (cobertura y ancho de la banda) |
| `02_DS02_ensemble_RUL.ipynb` | §3.1 (tres semillas) y §4 (NASA) |

Todas las cifras se obtienen con `.venv/Scripts/python.exe <script>` sobre el bundle
enviado; ninguna requiere reentrenar.
