# Informe — Medidor de reglas de corrección (R2-R5) y coherencia de banda (R6)

Proyecto: N-CMAPSS DS02, predicción de RUL (Hybrid Stacking BiLSTM + LightGBM cuantil + meta + EMA5)
Fecha: 2026-10-21
Modo: solo lectura. No se modificó ningún fichero del repositorio. Todo el cálculo se hizo en el
scratch de Hermes (`C:\Users\mikel\AppData\Local\hermes\cache\scratch\`).

---

## 1. Instrumento y anclas

### 1.1 Baseline OOF

El baseline OOF **no** es "el meta enviado aplicado al cache OOF". La banda conformal del artefacto
se calibró con:

```
selection = select_beta_grouped(oof_units, oof_cycles, oof_y, oof_p_lstm, oof_p_lgb,
                                span=5, use_cycle_feature=False)      # build_02_notebook.py:627
calib     = selection['oof_calib']                                    # build_02_notebook.py:751
conformal = fit_conformal(calib['y'], calib['pred_ema'], target=0.90)
```

Es decir: **metas por fold** (cada fold se puntúa con un meta ajustado en los otros motores), 3 folds
agrupados, `beta_hat` = mediana de los folds. Ese es el instrumento que se usa aquí.

- Filas: 17 450 (6 motores de dev: 2, 5, 10, 16, 18, 20)
- Betas por fold: `[1.00, 1.00, 0.00]` → coincide con el vector documentado en el spec
- Subconjunto "5 puras" (sin motor 16): 14 915 filas
- Valores negativos en el baseline OOF: 109 (el `predict()` enviado recorta a 0; el instrumento de
  calibración no)

### 1.2 Anclas

| Ancla | Qué | Resultado |
| --- | --- | --- |
| A | Cuantiles globales de residuo OOF vs `manifest.conformal.global_quantiles` | **NO cuadra exacta** (ver 1.3) |
| B | Fila de test del cache vs `manifest.metrics.reference_row` | **Exacta**: RMSE 4.289, MAE 3.179, R² 0.9473, NASA 2310.6 (6 196 filas) |
| C | Banda enviada vs `lower`/`upper` del cache de test | **Exacta**: diferencia máxima 0.0; cobertura 1.000 |

El bloque `conformal` del artefacto cargado es idéntico al del manifest.

### 1.3 La ancla A no puede cerrarse exacta: el BiLSTM no es determinista

Se reconstruyó el cache OOF en scratch dos veces con los mismos parámetros
(`oof_base_predictions(..., n_splits=3, seed=42, window=50, step_train=3, epochs=15, use_cycle=True)`),
374.7 s y 345.9 s:

| Comparación | `p_lstm` max abs diff | `p_lgb` max abs diff | `y`, `cycles` |
| --- | --- | --- | --- |
| corrida 1 vs corrida 2 | **26.26** | **0.0** | 0.0 |
| corrida 1 vs cache del repo | **19.58** | **0.0** | 0.0 |

La rama LightGBM es bit-idéntica entre corridas; la rama BiLSTM no. Los bins del manifest son,
por tanto, **una extracción ruidosa** y no reproducibles bit a bit:

| Instrumento | bins n | global q05/q95 |
| --- | --- | --- |
| manifest / artefacto | 5829 / 6152 / 4467 / 1002 | [-22.4834, +17.9404] |
| corrida 1 (scratch) | 5746 / 5732 / 5031 / 941 | [-22.1474, +17.0177] |
| corrida 2 (scratch) | 5771 / 6020 / 4725 / 934 | [-21.9839, +17.3317] |
| cache del repo | 5789 / 5580 / 5263 / 818 | [-21.2460, +15.6823] |

Conclusión: la ancla A se reporta como **coincidencia estadística** (misma forma, mismos betas de
fold, magnitud de cuantiles equivalente). El panel OOF de abajo hereda ese ruido de ±1-2 %. El
panel de test queda anclado exacto.

Este hallazgo es relevante por sí mismo: la banda conformal enviada está calibrada sobre una
extracción ruidosa del OOF, así que sus bins no son reproducibles y la cobertura publicada descansa
sobre una calibración no determinista.

---

## 2. Constantes de dominio medidas

| Unidad dev | Vida (y + ciclo) |
| --- | --- |
| 2 | 75 |
| 5 | 89 |
| 10 | 82 |
| 16 | 63 |
| 18 | 71 |
| 20 | 66 |

`L_max_dev = 89` ciclos · RUL máximo observado = 88.
(La impresión anterior de "177" era una suma incorrecta de `y_máx + ciclo_máx`; la vida es
`y + ciclo` por fila.)

---

## 3. Panel OOF — 5 unidades puras (14 915 filas)

| Regla | RMSE | macro-RMSE | MAE | R² | NASA | filas cambiadas |
| --- | --- | --- | --- | --- | --- | --- |
| **Baseline** | 9.491 | 8.726 | 7.172 | 0.8260 | 19257.1 | 0 |
| R2 running-min | 10.737 | 10.115 | 8.583 | 0.7773 | 21053.0 | 13000 |
| R2b PAVA causal | 9.623 | 8.746 | 7.316 | 0.8211 | 18713.9 | 10715 |
| R3 (3-fold, 5 puras) | **8.722** | **8.336** | **6.928** | **0.8531** | **15014.1** | 14915 |
| R3 (curva 6 unidades) | 9.538 | 8.653 | 7.188 | 0.8243 | 21338.3 | 14915 |
| R4i techo 88 | 9.491 | 8.726 | 7.172 | 0.8260 | 19257.1 | **0** |
| R4ii techo L_max − ciclo | 9.459 | 8.701 | 7.157 | 0.8272 | 19057.6 | 227 |
| R5 δ = −0.50 | 9.558 | 8.825 | 7.309 | 0.8235 | 19102.3 | 14915 |
| R2+R3 | 11.278 | 10.701 | 9.285 | 0.7543 | 22258.7 | 14915 |
| R2+R3+R4i | 11.278 | 10.701 | 9.285 | 0.7543 | 22258.7 | 14915 |
| R2+R3+R4ii | 11.278 | 10.701 | 9.285 | 0.7543 | 22258.7 | 14915 |
| R2+R3+R4ii+R5 | 11.527 | 10.949 | 9.579 | 0.7434 | 22859.5 | 14915 |

## 4. Panel OOF — 6 unidades (17 450 filas)

| Regla | RMSE | macro-RMSE | MAE | R² | NASA |
| --- | --- | --- | --- | --- | --- |
| **Baseline** | 10.645 | 9.908 | 8.188 | 0.7714 | 29763.8 |
| R2 running-min | 11.299 | 10.789 | 9.182 | 0.7425 | 29279.1 |
| R3 (6 unidades) | 11.092 | 10.153 | 8.443 | 0.7518 | 34881.0 |
| R4i techo 88 | 10.645 | 9.908 | 8.188 | 0.7714 | 29763.8 |
| R4ii techo L_max − ciclo | 10.621 | 9.887 | 8.176 | 0.7724 | 29563.3 |

## 5. Panel TEST — 3 unidades (6 196 filas)

| Regla | RMSE | macro-RMSE | MAE | R² | NASA | filas cambiadas |
| --- | --- | --- | --- | --- | --- | --- |
| **Baseline** | 4.289 | 4.903 | 3.179 | 0.9473 | 2310.6 | 0 |
| R2 running-min | **3.964** | **4.733** | **2.795** | **0.9550** | **1906.6** | 4751 |
| R2b PAVA causal | 4.173 | 4.864 | 3.075 | 0.9501 | 2182.9 | 3911 |
| R3 (curva 5 puras) | 4.387 | 5.221 | 3.113 | 0.9449 | 2183.7 | 6196 |
| R4i techo 88 | 4.289 | 4.903 | 3.179 | 0.9473 | 2310.6 | **0** |
| R4ii techo L_max − ciclo | 4.289 | 4.903 | 3.179 | 0.9473 | 2310.6 | **0** |
| R5 δ = −1.00 | 4.350 | 5.155 | 3.145 | 0.9458 | 2194.1 | 6196 |
| R2+R3 | 4.326 | 5.112 | 2.799 | 0.9464 | **1899.7** | 6196 |
| R2+R3+R4i | 4.326 | 5.112 | 2.799 | 0.9464 | 1899.7 | 6196 |
| R2+R3+R4ii | 4.326 | 5.112 | 2.799 | 0.9464 | 1899.7 | 6196 |
| R2+R3+R4ii+R5 | 4.788 | 5.550 | 3.121 | 0.9343 | 2106.7 | 6196 |

### 5.1 TEST — RMSE por motor (11 / 14 / 15)

| Regla | Motor 11 | Motor 14 | Motor 15 |
| --- | --- | --- | --- |
| **Baseline** | 3.773 | 8.175 | 2.760 |
| R2 running-min | 2.427 | 8.441 | 3.332 |
| R2b PAVA causal | 3.352 | 8.274 | 2.966 |
| R3 (curva 5 puras) | 2.828 | 9.072 | 3.763 |
| R5 δ = −1.00 | 3.018 | 8.838 | 3.608 |
| R2+R3 | 1.617 | 9.357 | 4.363 |
| R2+R3+R4ii+R5 | 1.321 | 10.077 | 5.252 |

Todas las reglas mejoran el motor 11 y empeoran el 14 y el 15. El motor 14 es el de mayor error
y el que define el macro-RMSE.

---

## 6. R5 — curva completa δ ∈ [−4, +2]

### OOF 5 puras (baseline RMSE 9.491, NASA 19257.1)

| δ | RMSE | NASA | | δ | RMSE | NASA |
| --- | --- | --- | --- | --- | --- | --- |
| −4.00 | 10.695 | 20560.0 | | +0.00 | 9.491 | 19257.1 |
| −3.00 | 10.262 | 19712.7 | | +0.25 | 9.467 | 19374.9 |
| −2.00 | 9.911 | 19204.4 | | +0.50 | 9.449 | 19520.7 |
| −1.00 | 9.652 | **19045.1** | | +1.00 | **9.434** | 19898.2 |
| −0.75 | 9.602 | 19062.3 | | +1.25 | 9.436 | 20130.9 |
| −0.50 | 9.558 | 19102.3 | | +1.50 | 9.445 | 20392.6 |
| −0.25 | 9.521 | 19166.3 | | +2.00 | 9.483 | 21003.2 |

- δ* (NASA mínima sin restricción) = **−1.00** → RMSE 9.652 (+0.161)
- δ* con RMSE ≤ baseline + 0.10 = **−0.50** → RMSE 9.558 (+0.067), NASA 19102.3 (−154.8)
- El RMSE se minimiza en δ ≈ **+1.00** (9.434): RMSE y NASA tiran en direcciones opuestas.

### TEST (baseline RMSE 4.289, NASA 2310.6)

| δ | RMSE | NASA | | δ | RMSE | NASA |
| --- | --- | --- | --- | --- | --- | --- |
| −4.00 | 5.702 | 2950.9 | | +0.00 | 4.289 | 2310.6 |
| −3.00 | 5.097 | 2551.9 | | +0.25 | 4.310 | 2371.4 |
| −2.00 | 4.632 | 2290.1 | | +0.50 | 4.345 | 2444.0 |
| −1.00 | 4.350 | **2194.1** | | +1.00 | 4.457 | 2623.7 |
| −0.75 | 4.313 | 2203.1 | | +1.50 | 4.621 | 2853.8 |
| −0.50 | 4.291 | 2226.8 | | +2.00 | 4.831 | 3125.9 |
| −0.25 | **4.283** | 2263.0 | | | | |

- δ* (NASA mínima) = **−1.00** → RMSE 4.350 (+0.061, dentro de la restricción +0.10)
- δ* con restricción = **−1.00** (también la sin restricción)

---

## 7. R6 — coherencia de la banda conformal

### Cobertura en OOF

| Punto · banda | Cobertura |
| --- | --- |
| baseline · banda enviada (6u) | 0.9391 |
| baseline · banda enviada (5 puras) | 0.9578 |
| R2+R3+R4ii · banda enviada (6u) | 0.9469 |
| **R2+R3+R4ii · banda enviada (5 puras)** | **0.8558** ← bajo el objetivo 0.90 |
| R2+R3+R4ii · recalibrada en 17 450 (6u) | 0.9062 |
| R2+R3+R4ii · recalibrada en 14 915 (5 puras) | 0.8977 |

### Cobertura en TEST

| Punto · banda | Cobertura |
| --- | --- |
| baseline · banda enviada | 1.0000 |
| R2+R3+R4ii · banda enviada | 1.0000 |
| R2+R3+R4ii · recalibrada en 17 450 | 0.9995 |
| R2+R3+R4ii · recalibrada en 14 915 | 1.0000 |

**Lectura:** corregir el punto sin recalibrar la banda baja la cobertura al **0.856** en el conjunto
OOF puro (objetivo 0.90). En test la banda es tan conservadora (cobertura 1.000) que el desplazamiento
no la rompe. Recalibrar devuelve la cobertura a 0.898-0.906. R6 no es opcional: es la condición para
que cualquier regla de corrección sea honesta.

---

## 8. R4 — filas tocadas

| Panel | R4i (`pred ≤ 88`) | R4ii (`pred ≤ 89 − ciclo`) |
| --- | --- | --- |
| test | 0 | 0 |
| OOF 5 puras | 0 | 227 |
| OOF 6 unidades | 0 | 230 |

R4i nunca dispara: ninguna predicción supera el RUL máximo observado (88). R4ii dispara en 227-230
filas de dev y en ninguna de test. Es una regla **guardabarrinos**: no demostrable con estos datos,
útil solo si entra un motor más longevo.

---

## 9. Diagnóstico por regla

**R2 running-min causal** — Restricción física (RUL no crece con el ciclo), pero implementada como
mínimo acumulado es un **desplazamiento descendente acotado por el pasado**. Por eso ayuda cuando el
modelo sobre-estima y perjudica cuando subestima:
- OOF: RMSE 9.491 → 10.737 (**+1.25**), NASA 19257 → 21053. Los motores dev son largos (vida hasta
  89) y el modelo los subestima (residuo medio +1.4 a +10), así que bajar el punto empeora todo.
- Test: RMSE 4.289 → 3.964 (**−0.33**), NASA 2310.6 → 1906.6 (−403.9). Los motores de test son
  cortos (59-76) y el modelo los sobreestima en el tramo alto (bins q_low negativos).
- Efecto por motor: mejora el 11, empeora el 14 y el 15.
No es una mejora robusta: es un **cambio de signo del sesgo** que depende del régimen de la flota.

**R2b PAVA causal (isotónico)** — Es el ajuste monótono por mínimos cuadrados, no un desplazamiento:
- NASA: −543 en OOF, −128 en test (mejora en **ambos**).
- RMSE: +0.132 en OOF, −0.116 en test.
- MAE: +0.144 en OOF, −0.104 en test.
Es la versión defendible de la monotonía: misma restricción física, sin el sesgo descendente
sistemático. Coste pequeño en RMSE y ganancia de NASA en los dos paneles.

**R3 desfase de ciclo** — El meta enviado no lleva el ciclo (2 features); el ciclo entra por el canal
19 del BiLSTM, así que R3 corrige el sesgo ciclo-dependiente de la tubería completa.
- Curva `b(ciclo)` (5 puras, bin = 10): 5:+1.49, 15:+1.25, 25:+1.60, 35:+0.96, 45:−0.02, 55:+0.36,
  65:+1.30, 75:+1.52, 85:+1.72. Prácticamente constante ≈ **+1.5**: el modelo subestima ~1.5 ciclos.
- Curva de 6 unidades: b global = **−1.17** (el motor 16 invierte el signo).
- Folds: [[5], [10,20], [2,18]].
- Con la curva de 5 puras estimada en 3-fold honesto: **gana mucho en OOF** (RMSE −0.77, NASA −4243).
- En test: RMSE +0.098, macro +0.318, MAE −0.066, NASA −126.9. No transfiere.
- Con la curva de 6 unidades: **empeora en los dos paneles** (OOF RMSE +0.047, NASA +2081).
La causa es la misma que la documentada al rechazar el meta agregado sobre OOF: los motores dev son
largos y el test cortos, y una corrección de nivel aprendida en dev no transfiere. El "nivel" es el
problema, no el mecanismo.

**R4 techo** — No dispara (0 filas en R4i, 227-230 en R4ii). No es medible con estos datos. Puede
quedarse como regla de seguridad, pero no cuenta como mejora.

**R5 sesgo asimétrico** — La curva muestra el trade-off completo: NASA lo minimiza en δ = −1.00 y el
RMSE en δ ≈ +1.00. Es **política, no exactitud**: hay que declararla y decidir la métrica que manda.
δ* = −1.00 cuesta +0.061 RMSE en test (−116.5 NASA) y +0.161 en OOF.

**R6 coherencia de banda** — Necesaria si se adopta cualquier corrección. Dejar la banda enviada
sobre el punto corregido hunde la cobertura OOF pura a 0.856, por debajo del 0.90 prometido.

---

## 10. Síntesis

Ninguna regla mejora las cuatro métricas en los dos paneles. Los puntos de equilibrio son claros:

| Objetivo | Regla | Test RMSE | Test NASA | OOF RMSE | OOF NASA |
| --- | --- | --- | --- | --- | --- |
| Mejor RMSE en test | R2 | 3.964 | 1906.6 | 10.737 (peor) | 21053 (peor) |
| Mejor NASA, robusto | R2b | 4.173 | 2182.9 | 9.623 (algo peor) | 18713.9 (mejor) |
| Mejor NASA y MAE en test | R2+R3 | 4.326 | **1899.7** | — | — |
| Mejor RMSE y NASA en test | R2+δ | — | — | — | — |

La única combinación que baja NASA en dos dígitos sin coste serio en test es **R2+R3**
(−17.8 % NASA, −11.9 % MAE, +0.9 % RMSE), pero empeora los motores 14 y 15 y **necesita R6**.

---

## 11. Recomendación de Paso 5 (pendiente de confirmación)

Reglas que **pasan** a `mia/reglas.py`:

1. **R2b monotonía causal (PAVA)** — prioridad alta. Única regla que mejora NASA en los dos paneles.
2. **R6 coherencia de banda** — obligatoria como compañera de cualquier corrección.
3. **R1 seguridad** — dato imposible / ventana corta → sin decisión, con porqué (no mide métrica,
   pero es la regla de seguridad que pide la práctica).

Reglas que quedan **como política opcional** (no en la parrilla activa):

4. **R5 δ = −1.00** — política declarada, no exactitud. Decidir qué métrica manda.
5. **R4 techo** — guardabarrinos, no dispara con estos datos.

Reglas **no adoptadas** como mejora:

6. **R2 running-min** — ayuda en test y perjudica en OOF; depende del régimen de la flota.
7. **R3** — la ganancia OOF es un nivel que no transfiere (misma causa que el meta agregado).

Lo que habría que decidir para escribir `mia/reglas.py`:
(a) si la parrilla activa es **R2b + R6 + R1** o se coge **R2 + R3** como paquete de máxima NASA,
(b) si el motor de reglas va con la banda recalibrada dentro de la pasada B (R6 activa) o se publica
el recalibrado como artefacto nuevo.

---

## 12. Consecuencias y riesgo

- **No se tocó ningún fichero del repositorio.** `src/`, `models/`, `app/`, `tests/`, `openspec/` y los
  notebooks siguen intactos; `predict()` y `ds02_manifest.json` no se modificaron, así que los 50
  tests pasan igual.
- Riesgo de incorporar la capa de reglas como **post-procesado separado**, medida en OOF, con la banda
  recalibrada y el contrato intacto: **4/10**.
- Riesgo de meter cualquier regla dentro de `predict()` o de actualizar `models/` y el manifest para
  reflejar los nuevos números: **8/10** (test de recomputación del cache, violación de la regla de
  "no alterar métricas registradas" de `openspec/config.yaml`, y los notebooks se regeneran desde
  `scripts/build_02_notebook.py`, nunca se editan a mano).
- Riesgo del hallazgo de no determinismo del BiLSTM: la banda enviada no es reproducible bit a bit;
  cualquier cambio de código sobre el pipeline hereda esa no reproducibilidad.
