# Informe — ejecución del cuaderno `02_DS02_ensemble_RUL.ipynb` y análisis de su salida

**Fecha:** 2026-10-20
**Cuaderno ejecutado:** `02_DS02_ensemble_RUL.ipynb` (71 celdas)
**Ejecución:** `nbconvert --execute --inplace`, 32 celdas de código, 0 errores, EXIT=0
**Duración:** 19:21 → 19:44 (~23 min)
**Artefactos regenerados:** `models/ensemble.joblib`, `models/scaler.joblib`, `models/bilstm_ds02.keras`, `models/ds02_manifest.json` y copias en raíz
**Verificación posterior:** `pytest tests -q` → 10 passed; `scripts/predict_ds02.py --unit 11 --window 0` → RUL 60.27

---

## 1. El cuaderno no arrancaba: faltaba un import

La primera ejecución murió en la celda 20 con:

```
NameError: name 'plt' is not defined
  Cell In[11], line 1  -> barras_ablacion(abl, metrica='RMSE')
  Cell In[2], line 142 -> fig, ax = plt.subplots(figsize=figsize)
```

La celda 4 define diez funciones de graficación que llaman a `plt.subplots`, pero el
único `import matplotlib.pyplot as plt` del cuaderno está en la celda 66 — la de
persistencia, que se ejecuta **después** de todos los gráficos.

**Arreglo aplicado.** Se añadió el import al principio de la celda 4, donde se definen
las funciones que lo necesitan:

```python
# --- utilidades de presentación: importaciones ---
# `plt` se importa aquí, no en la celda de persistencia: las funciones
# de abajo lo usan y esa celda se ejecuta después de todos los gráficos.
import matplotlib.pyplot as plt
```

Cambio mínimo: ninguna otra celda fue tocada. Copia de seguridad del cuaderno editado a
mano antes del cambio: `$TMPDIR/ds02_backup/notebook_hand_edited.ipynb`.

Tras el arreglo, la ejecución completa terminó limpia (EXIT=0).

---

## 2. Hallazgo estructural: el cuaderno no es lo que genera el builder

| | Celdas |
|---|---|
| Genera `scripts/build_02_notebook.py` | 34 |
| Tiene el cuaderno ejecutado | **71** |

Hay **37 celdas añadidas a mano** que el builder no emite:

- la sección de diagnósticos (celdas 33–65): comparación de modelos, dispersión por semilla, real vs predicho, residuos, error por tramo, tabla por motor, curva de entrenamiento, beta por fold;
- las diez funciones de presentación (celda 4);
- el comentario narrativo en español de toda la sección 10–12.

La regla del proyecto dice que *"el notebook es un output del builder; nunca editar el
.ipynb"*. El archivo contradice esa regla. **Si alguien ejecuta
`python scripts/build_02_notebook.py`, se destruyen las 37 celdas** y con ellas todo el
análisis de diagnóstico.

No toqué el cuaderno más allá del import: el arreglo del apartado anterior era el mínimo
necesario para que arrancara.

---

## 3. Hallazgo grave: el comentario escrito contradice sus propias salidas

Se comparó cada afirmación numérica del texto contra lo que imprimieron las celdas en
esta ejecución. Casi todas están **obsoletas**: describen la ejecución de las 16:14, no
la actual. Las salidas son correctas; la prosa no.

| Afirmación del texto | Dice | Sale ahora |
|---|---|---|
| Quitar `cyc_norm` cuesta al BiLSTM | 1,094 | **0,791** |
| (5,419 → 6,513) | 5,419 → 6,513 | **5,613 → 6,404** |
| Línea base: 6,513 → 5,998 vs 5,419 | 6,513 → 5,998 | **6,404 → 5,974** |
| MAE línea base vs con ciclo | 3,864 / 4,109 | **3,892 / 4,206** |
| Híbrido le saca al BiLSTM | 1,851 | **2,007** |
| ± del BiLSTM | 0,576 | **0,811** |
| Híbrido se mueve entre semillas | 0,136 | **0,045** |
| BiLSTM salta entre semillas | 1,134 | **0,811** |
| LightGBM, el más estable | 0,062 | **0,034** |
| Mejora vs LightGBM (RMSE / MAE) | 39,4 % / 42,9 % | **39,2 % / 42,5 %** |
| Mejora vs BiLSTM (RMSE / MAE) | 30,1 % / 33,0 % | **31,7 % / 35,2 %** |
| BiLSTM le saca al LightGBM | 13,3 % | **12,3 %** |
| Diferencia LightGBM − BiLSTM | 0,946 | **0,775** |
| Sesgo medio global | +0,369 | **+0,185** |
| MAE 1.er tramo / último | 1,204 / 5,264 | **1,126 / 5,356** |
| Factor entre tramos | 4,4× | **4,8×** |
| Motor 14 RMSE (11 / 15) | 7,833 / 3,847 / 2,688 | **8,044 / 3,724 / 2,882** |
| Sesgos por motor (11 / 14 / 15) | +3,098 / −4,757 / −2,006 | **+3,027 / −5,194 / −2,274** |
| Épocas / mejor val_loss | 8 / 8,664 | **15 / 6,786** |
| Semilla 42 / 7 / 123 (épocas, RMSE) | 8/5,642 · 13/6,037 · 18/6,776 | **15/5,566 · 16/6,222 · 8/7,179** |
| Fold 2: meta vs BiLSTM | 5,766 / 5,770 | **5,035 / 5,056** |

El sesgo global se verificó a mano a partir de la tabla por motor:

```
(3293 × 3,027 + 760 × (−5,194) + 2143 × (−2,274)) / 6196 = +0,185
```

### Una afirmación quedó falsa por el propio arreglo

Las conclusiones dicen:

> *"La dispersión es el ancho honesto del estimador, y es mayor que la ventaja híbrido-campeón en RMSE."*

Con el reloj eso era cierto. Sin él: el BiLSTM tiene ±0,811 y la ventaja del híbrido es
2,007. **La dispersión ya no es mayor que la ventaja.** La frase sobrevivió a un cambio
que la invalidó.

### Lo que sí coincide

- La fila del LightGBM en la ablación: 6,297 → 8,667 (exacta).
- La mención histórica de `±0,001` en las conclusiones (correcta como descripción de la configuración anterior).
- El título de la sección 0 y la tabla de "qué cambió en esta revisión" (describen el cambio de protocolo, siguen siendo válidos).

### No verificables desde la salida

Estas cifras aparecen solo como anotación dentro de las figuras, no como texto impreso, así
que no pude contrastarlas: predicción máxima 60,64; RUL real 73; correlación +0,669;
rango de residuos −14,76 a +9,52; 58,8 % de ventanas que se pasan; 4,3 % con error > 10
ciclos.

---

## 4. Resultados reales de esta ejecución

### Meta-learner: el arreglo sigue en pie

| | Antes del fix | Ahora |
|---|---|---|
| `ridge_meta.n_features_in_` | 3 | **2** |
| `ridge coef` | `[0.0019, 0.0124, -98.4065]` | **`[0.1613, 0.7316]`** |
| `lgb_meta.feature_importances_` | `[0, 0, 720]` | **`[230, 490]`** |
| `ridge alpha` | 0.01 | 14.38 |

El meta-aprendiz reparte peso entre las dos ramas. Ya no es un reloj.

### Métricas en test (motores 11/14/15, 6 196 ventanas, media ± desviación en semillas [42, 7, 123])

| Modelo | RMSE | MAE | R² | NASA |
|---|---|---|---|---|
| LightGBM solo | 7,098 ± 0,034 | 5,572 ± 0,034 | 0,8557 ± 0,0014 | 5772,5 ± 50,1 |
| BiLSTM solo | 6,322 ± 0,811 | 4,941 ± 0,720 | 0,8843 ± 0,0297 | 4490,5 ± 1066,0 |
| **Híbrido + EMA5** | **4,315 ± 0,045** | **3,203 ± 0,024** | **0,9466 ± 0,0011** | **2326,3 ± 29,6** |

Semilla 42: Híbrido 4,263 · MAE 3,177 · R² 0,9479 · NASA 2293,2.
Detalle por semilla: 42 → 4,263 · 7 → 4,344 · 123 → 4,338.

### Mejora frente a cada base

| Frente a | Δ RMSE | Mejora RMSE | Δ MAE | Mejora MAE |
|---|---|---|---|---|
| LightGBM solo | −2,783 | 39,2 % | −2,369 | 42,5 % |
| BiLSTM solo | −2,007 | 31,7 % | −1,737 | 35,2 % |

El orden es LightGBM < BiLSTM < híbrido, sin cruces. La ventaja sobre el BiLSTM (2,007)
es 2,5 veces su ± (0,811): no es empate.

### `beta` fuera de fold

```
beta_hat (mediana) = 1,00
folds: [[2, 10], [5, 18], [20, 16]]
  fold 0: beta=1,00 | rmse 6,243 (ref BiLSTM 9,205) | nasa 3610,9 (ref 5736,1)
  fold 1: beta=1,00 | rmse 8,733 (ref BiLSTM 10,821) | nasa 5602,3 (ref 7750,5)
  fold 2: beta=0,00 | rmse 5,035 (ref BiLSTM  5,056) | nasa 2893,8 (ref 2902,7)
```

`beta = 1,00` se mantiene, con el mismo matiz: una de tres folds no ve valor en el
meta-aprendiz. El protocolo legado dentro de muestra da cociente 0,695× (firma del defecto).

### Ablación de `cyc_norm` (semilla 42)

| Variante | BiLSTM | BiLSTM+EMA | LGBM |
|---|---|---|---|
| `cyc_norm` ON (baseline) | 5,613 | 5,576 | 7,113 |
| `cyc_norm` OFF | 6,404 | 6,308 | **6,297** |
| `cyc_norm` OFF + línea base | 5,974 | 5,920 | 8,667 |
| `cyc_norm` ON + línea base | 6,003 | 5,990 | 8,578 |

Quitar el contador a los **base** cuesta al BiLSTM **+0,791 RMSE** (en la ejecución de las
16:14 daba +1,094 — el texto del cuaderno cita este último). El LightGBM *mejora* sin él
(7,113 → 6,297), pero se degrada con la línea base por motor.

---

## 5. Análisis del modelo

**Dónde acierta: cerca del fallo.** MAE de 1,126 ciclos con RUL < 25, que es exactamente
la zona donde se decide el mantenimiento. El error por tramo:

| Tramo de RUL real | Ventanas | MAE |
|---|---|---|
| [0, 25) | 2 521 | 1,126 |
| [25, 50) | 2 402 | 4,174 |
| [50, 75) | 1 273 | 5,356 |

**Dónde falla: a vida alta.** El MAE se multiplica por 4,8 entre el primer y el último
tramo. El modelo acierta cuando el motor está por fallar y se queda corto cuando le queda
vida.

**El hallazgo más interesante está en la tabla por motor.** El sesgo global es +0,185,
aparentemente nulo, pero está compuesto de tres errores grandes y opuestos que se cancelan:

| Motor | Ventanas | RMSE | MAE | Sesgo |
|---|---|---|---|---|
| 11 | 3 293 | 3,724 | 3,056 | **+3,027** |
| 14 | 760 | **8,044** | 6,080 | **−5,194** |
| 15 | 2 143 | 2,882 | 2,333 | **−2,274** |

El motor 14 concentra el error con solo 760 ventanas, y los sesgos tienen signo distinto:
el 11 se pasa, el 14 y el 15 se quedan cortos. Un promedio global bueno describe mal a
cada motor por separado. Eso es lo que la tabla por motor revela y el promedio esconde.

**Sobre el nombre "híbrido".** Con `beta = 1,00` la predicción **es** `p_meta`: el BiLSTM y
el LightGBM solo entran como columnas del meta-aprendiz. El fold 2 lo dice claro: sin
meta-aprendiz el RMSE es 5,056 y con él 5,035. El nombre describe la arquitectura, no una
mezcla.

---

## 6. Comparación con la ejecución de las 16:14

| Métrica | 16:14 | 19:44 | Delta |
|---|---|---|---|
| Híbrido RMSE | 4,301 ± 0,068 | 4,315 ± 0,045 | +0,014 |
| BiLSTM RMSE | 6,152 ± 0,576 | 6,322 ± 0,811 | +0,170 |
| MAE híbrido | 3,181 | 3,203 | +0,022 |
| R² híbrido | 0,9470 | 0,9466 | −0,0004 |
| NASA híbrido | 2315,6 | 2326,3 | +10,7 |

Consistente. El híbrido se mueve 0,014 y el BiLSTM 0,170 — dentro del ruido no
determinista de oneDNN en CPU ya documentado en el spec §6.9. **La conclusión no cambia
entre ejecuciones.**

---

## 7. Verificación ejecutada

| Comprobación | Resultado |
|---|---|
| Ejecución completa del cuaderno | ✅ 32 celdas, 0 errores, EXIT=0 |
| `ridge_meta.n_features_in_` | ✅ 2 |
| Pesos repartidos entre ambas ramas | ✅ coef `[0.1613, 0.7316]`, importances `[230, 490]` |
| Recarga bit-idéntica a memoria | ✅ `recargado == en memoria: True` |
| `load_ensemble` en proceso limpio | ✅ `[RELOAD OK] RUL 60,27 vs real 58,00` |
| `pytest tests -q` | ✅ 10 passed |
| `scripts/predict_ds02.py --unit 11 --window 0` | ✅ RUL 60,27 |
| `models/ds02_manifest.json` → `meta_features` | ✅ 2 en `model_shape` y en `inference_contract` |
| `docker compose config` / build de la imagen | ⬜ no ejecutado |

---

## 8. Veredicto

El cuaderno ahora ejecuta limpio y los números son reproducibles entre ejecuciones. Pero no
puede ser el registro del proyecto en este estado, por dos razones independientes:

1. **El comentario escrito contradice sus propias salidas** en unas 14 cifras, y una
   afirmación de las conclusiones quedó falsa por el propio arreglo del reloj.
2. **El builder y el cuaderno se han divergido**: la próxima regeneración destruye 37 celdas
   de narrativa y diagnóstico.

### Caminos, en el orden recomendado

1. **Corregir el comentario contra las salidas reales.** Mejor todavía: generar el texto
   desde las salidas (una celda que rellene las cifras) para que no pueda desincronizarse.
2. **Decidir el estatus del cuaderno editado a mano**: portar las 37 celdas al builder, o
   declararlo un artefacto aparte. Hoy la regla dice una cosa y el archivo otra.
3. **Nombrar con precisión**: con `beta = 1,00` el híbrido es el meta-aprendiz; los modelos
   base aportan sus predicciones como columnas.

### Pendiente único

Construir y ejecutar la imagen Docker. Sigue siendo el único hueco de verificación real: hoy
solo `docker compose config` parsea.

---

*No se commiteó nada. No se tocó ningún archivo ajeno: `.atl/`, `copiaSeguridad.zip`,
`copiaSeguridad/`, `copiacuadernos/` y `uv.lock` aparecieron como untracked durante la
sesión y se dejaron como estaban.*
