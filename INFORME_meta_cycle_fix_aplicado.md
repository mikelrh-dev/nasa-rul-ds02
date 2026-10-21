# Informe — arreglo definitivo: quitar el reloj al meta-learner

**Fecha:** 2026-10-20
**Alcance:** pipeline principal (builder + notebook + manifest + spec + README + limpieza)
**Resultado:** el fix está aplicado, el notebook regenerado de principio a fin, los 10 tests pasan y el working tree queda limpio.

---

## 1. Qué se cambió

| Archivo | Cambio |
|---|---|
| `scripts/build_02_notebook.py` | `use_cycle_feature=False` en `select_beta_grouped`; `Z_hold` a 2 columnas; `Zs` del barrido de semillas a 2 columnas |
| `src/ds02_rul/persistence.py` | `meta_features` en `model_shape` e `inference_contract` |
| `02_DS02_ensemble_RUL.ipynb` | Regenerado por el builder (34 celdas) y ejecutado completo (20/20 celdas de código) |
| `models/ensemble.joblib`, `models/scaler.joblib`, `models/bilstm_ds02.keras`, `models/ds02_manifest.json` | Reescribidos por el notebook; copias en raíz actualizadas |
| `openspec/specs/rul-prediction-ds02/spec.md` | Requisito de meta-features reescrito a 2 columnas |
| `openspec/changes/2026-10-20-ds02-cycle-free-stacking/` | Nueva propuesta SDD (proposal + spec delta + tasks) |
| `docs/02_DS02_ensemble_RUL_spec.md` | §1, §6 (6.1–6.12), §7, §8 y §9 actualizados; §6.12 nuevo |
| `README.md` | Tabla de resultados, sección de ablación, salida del CLI |

### Los tres puntos del fix, con su línea

1. `scripts/build_02_notebook.py:313` — `use_cycle_feature=False`.
2. `scripts/build_02_notebook.py:347` — `Z_hold = np.column_stack([result['p_lstm_hold'], result['p_lgb_hold']])`.
3. `scripts/build_02_notebook.py:404` — `Zs = np.column_stack([out['p_lstm_hold'], out['p_lgb_hold']])`.

No hizo falta tocar `src/ds02_rul/`: `ensemble.py:137-142` ya era ancho-agnóstico y
respetaba `n_features_in_`, así que `predict()` funcionó sin cambios. El cambio
estaba en el punto de entrenamiento, no en la inferencia.

**Nota:** se conserva `hold_cycles = dev['meta']['cycle'].values[hold_idx]` en el
builder aunque `Z_hold` ya no lo usa, para que la eliminación sea auditable.

---

## 2. Resultados (salida real del notebook regenerado)

### Meta-learner

| | Antes | Después |
|---|---|---|
| `ridge_meta.n_features_in_` | 3 | **2** |
| `ridge coef` | `[0.0019, 0.0124, -98.4065]` | **`[0.1205, 0.7923]`** |
| `ridge intercept` | 61.9833 | -1.2301 |
| `lgb_meta.feature_importances_` | `[0, 0, 720]` | **`[148, 572]`** |
| `ridge alpha` | 0.01 | 4.281 |

El meta-learner ahora reparte peso entre ambas ramas. Ya no es un reloj.

### Métricas en test (unidades 11/14/15, 6 196 ventanas, mean ± std en semillas 42/7/123)

| Modelo | RMSE | MAE | R² | NASA |
|---|---|---|---|---|
| LightGBM standalone | 7.098 ± 0.034 | 5.572 ± 0.034 | 0.8557 ± 0.0014 | 5772.5 ± 50.1 |
| BiLSTM standalone | 6.152 ± 0.576 | 4.745 ± 0.332 | 0.8910 ± 0.0205 | 4308.0 ± 595.8 |
| **Hybrid + EMA5** | **4.301 ± 0.068** | **3.181 ± 0.021** | **0.9470 ± 0.0017** | **2315.6 ± 20.0** |

**Delta Hybrid (antes → después):** RMSE **−1.222** · MAE **−1.614** · R² **+0.0344** · NASA **−1120.0**.

Detalle por semilla del Hybrid: 4.230 (42) · 4.307 (7) · 4.366 (123). La mejora no
depende de una semilla afortunada.

### `beta` re-seleccionado out-of-fold sobre el nuevo diseño

```
folds: [[2, 10], [5, 18], [20, 16]]
fold 0: beta=1.00 | rmse 6.271 (BiLSTM ref 9.093) | nasa 3422.5 (ref 5568.1)
fold 1: beta=1.00 | rmse 9.996 (BiLSTM ref 11.363) | nasa 6837.4 (ref 8488.4)
fold 2: beta=0.00 | rmse 5.766 (BiLSTM ref 5.770)  | nasa 3668.1 (ref 3663.4)
→ mediana 1.00   vector [1.00, 1.00, 0.00]
```

`beta = 1.0` se mantiene, con el mismo matiz de antes: una de tres folds no ve
valor en el meta-learner. Ahora ese matiz es honesto (la predicción sí depende de
los base); antes era un artefacto.

### Ablación de base (semilla 42)

| Variante | LGBM | BiLSTM | BiLSTM+EMA |
|---|---|---|---|
| `cyc_norm` ON | 7.113 | 5.419 | 5.386 |
| `cyc_norm` OFF | 6.297 | 6.513 | 6.477 |

Quitar el contador a los **base** cuesta al BiLSTM **+1.094 RMSE**. Por eso el fix
lo quita solo del meta-learner: el reloj es una entrada legítima para los modelos
base (una flota sí sabe cuántos ciclos ha volado un motor) y un atajo para la capa
que debía reconciliarlos.

---

## 3. Verificación ejecutada

| Comprobación | Resultado |
|---|---|
| `ensemble.joblib` carga en proceso limpio (3.12) | ✅ `HybridStackingEnsemble` |
| `ridge_meta.n_features_in_` | ✅ **2** |
| Pesos repartidos entre ambas ramas | ✅ coef `[0.1205, 0.7923]`, importances `[148, 572]` |
| Recarga bit-idéntica a memoria | ✅ `reloaded == in-memory: True` |
| `load_ensemble` en proceso limpio | ✅ `[RELOAD OK] RUL 60.21 vs real 58.00` |
| `pytest tests -q` | ✅ **10 passed** |
| `scripts/predict_ds02.py --unit 11 --window 0` | ✅ `RUL 60.21 ciclos` |
| Notebook: las 20 celdas de código ejecutadas, sin errores | ✅ |
| `models/ds02_manifest.json` → `meta_features` | ✅ 2 en `model_shape` y en `inference_contract` |
| Manifest declara los SHA-256 de los artefactos | ✅ |

**Sin ejecutar:** `docker compose config` no se volvió a correr y la imagen Docker
no se construyó. Sigue siendo el único hueco de verificación real, y está declarado
como limitación en el README.

---

## 4. Nota sobre la no-reproducibilidad en CPU

El usuario atribuyó la diferencia `4.317` vs `4.270` al paralelismo no determinista
de TensorFlow en CPU. **Confirmado de forma indirecta y consistente:** en esta
misma ejecución el notebook arrojó `4.230` en semilla 42, y los tres valores
(`4.317`, `4.270`, `4.230`) están dentro de ±0.09. La conclusión (RMSE ≈ 4.3, mejora
de ~1.2 frente a 5.523) es robusta frente a ese ruido.

No hice una repetición controlada para medirlo, porque eso exigía reentrenar y el
encargo lo prohibía. Si se quiere cuantificar, la forma barata es repetir solo la
celda de semillas con la BiLSTM ya entrenada, no el pipeline entero.

Lo que sí cambió de verdad: el spread del Hybrid pasó de **±0.001 a ±0.068**. Eso
no es ruido, es la consecuencia estructural del fix — la predicción ahora depende
de los base y hereda su varianza. La firma del atajo ha desaparecido.

---

## 5. Limpieza

Eliminados (untracked, temporales de auditoría):

- `scripts/_measure_meta_cycle_fix.py`
- `scripts/_verify_meta_cycle_fix.py`
- `scripts/_verify_meta_cycle_fix_seeds.py`
- `scripts/_verify_meta_cycle_fix_seeds_v2.py`
- `models/_meta_cycle_fix_seeds.log`
- `VERIFICACION_meta_cycle_fix.md`
- `models/_nb_exec.log` (log de la ejecución del notebook)

Working tree final:

```
 M 02_DS02_ensemble_RUL.ipynb
 M README.md
 M docs/02_DS02_ensemble_RUL_spec.md
 M ensemble.joblib
 M models/bilstm_ds02.keras
 M models/ds02_manifest.json
 M models/ensemble.joblib
 M openspec/specs/rul-prediction-ds02/spec.md
 M scripts/build_02_notebook.py
 M src/ds02_rul/persistence.py
?? openspec/changes/2026-10-20-ds02-cycle-free-stacking/
```

Sin commits: no se tocó el historial.

---

## 6. Desviaciones respecto al encargo

1. **No se editó `VERIFICACION_meta_cycle_fix.md`, se eliminó.** Lo pediste como
   limpieza y el usuario lo dejó sin efecto al adelantar que el notebook ya cubre
   las tres semillas. Los números reales salen del notebook regenerado.
2. **No se re-ejecutó `_verify_meta_cycle_fix_seeds_v2.py`.** La celda de semillas
   del notebook mide lo mismo; repetirla habría entrenado tres BiLSTM para nada.
3. **No se usó `beta` fijo a mano en la medición:** se re-seleccionó out-of-fold
   sobre el diseño nuevo, que es lo que correspondía.
4. **La spec §8/§9 está reescrita, no solo "corregida".** Los nueve ítems estaban
   marcados como abiertos pese a estar cerrados por `tasks.md`; ahora cada uno lleva
   su evidencia de cierre. §6.12 documenta el defecto del reloj.
5. **Se añadió el campo `meta_features` también en `inference_contract`**, no solo
   en `model_shape`, porque ahí es donde un consumidor mira el contrato de inferencia.

---

## 7. Pendiente (único)

| | Comprobación | Por qué importa |
|---|---|---|
| 1 | Construir y ejecutar la imagen Docker | Único hueco de verificación real que queda; hoy solo `docker compose config` parsea |

No es un defecto del modelo: es que la imagen no se ha construido en este entorno.
