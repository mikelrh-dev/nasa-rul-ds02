# Verificación de ejecución — 3 cuadernos ds02_ensemble

Fecha de verificación: 2026-10-22.
Copias ejecutadas: `/tmp/nb01b.ipynb`, `/tmp/nb02b.ipynb`, `/tmp/nb03b.ipynb` (ejecutadas en este orden, sin petición previa).
Para consulta de las salidas de texto completas (filtrado de figuras y warnings): ver `verification_sources.py` al pie de este fichero.

## Resumen

Los tres cuadernos se ejecutaron **completos y en orden**, sin error de ejecución en ninguna celda:

| cuaderno | celdas código | ejecución secuencial | celdas con salida | celdas sin salida | errores |
|---|---|---|---|---|---|
| `01_datos_y_bases.ipynb` | 11 | 1 → 11 | 10 | 1 (import matplotlib) | 0 |
| `02_decision_ablacion_oof_ensamble.ipynb` | 17 | 1 → 17 | 16 | 1 (import matplotlib) | 0 |
| `03_evidencia_multisemilla_diagnostico.ipynb` | 24 | 1 → 14 → 24 | 23 | 1 (import matplotlib) | 0 |

Las celdas "sin salida" son exactamente la celda de import de `matplotlib` (la que dibuja los gráficos). Las celdas de control del notebook (NB01 celda 7, NB02 celda 5) imprimen `[FASE A OK]` confirmando que la función de evaluación está lista sin tocar el modelo.

## 1. La cadena de estado entre cuadernos funciona

Este es el chequeo que importa: los tres cuadernos no son autosuficientes; NB02 carga los artefactos que NB01 guarda, y NB03 carga los de NB01 + NB02. Que esto funcione es la prueba real de que el corte en tres cuadernos es correcto.

**Pruebas en las salidas:**

- **NB01 finale** — `[NB1 OK] artefactos en .../notebooks/ds02_ensemble/artifacts`, siguiente: abrir 02.
- **NB02 celda 3** — `[LOAD NB1 OK] dev (17450, 50, 19) | test (6196, 50, 19) | bilstm recargado`. Correcto.
- **NB02 celda 27 (finale)** — `[NB2 OK] beta = 1.0 | p_ens (6196,)`, siguiente: abrir 03.
- **NB03 celda 3** — `[LOAD NB2 OK] BETA = 1.0 | p_ens (6196,)`. Correcto.
- **NB03 celda 51 (save)** — escribe `models/` y 4 copias raíz, imprime el manifiesto de rutas.
- **NB03 celda 52 (RELOAD)** — `[RELOAD OK] RUL estimado 60.40 vs real 58.00`, paradigma Hybrid Stacking (BiLSTM triple-pooling + LGBM residualizado + RidgeCV/LGBM meta + EMA5), `recargado == en memoria: True`.

## 2. Contenido útil de cada cuaderno (síntoma textual, sin figuras ni warnings)

### 01_datos_y_bases.ipynb

- **celda 7 (FASE A OK)**: las funciones `evaluar_clase` / `mostrar_clase` están listas sin efecto en el modelo.
- **celda 9 (datos)**: dataset `archive/CCMaps/N-CMAPSS_DS02-006.h5`, canales operadores W = `[alt, Mach, TRA, T2]`, canales sensores Xs = los 14 sensores estándar; motores dev `[2,5,10,16,18,20]` (52635 filas), motores test `[11,14,15]` (12538 filas); filas de ajuste 44982, filas de holdout 7653.
- **celda 11 (escalador)**: ajustado con 18 canales, 44982 filas (solo motores de ajuste); media del escalador `[:4] = [21930.0395, 0.6249, 68.613, 475.0123]`; base polinómica `4 → 14`; ridges de residuos 14; el motor de holdout aportó 0 filas.
- **celda 13 (ventanas)**: dev X_seq `(17450, 50, 19)` / X_tab `(17450, 93)`; test X_seq `(6196, 50, 19)` / X_tab `(6196, 93)`; ventanas de ajuste 14915, ventanas de holdout 2535; huella X_seq 66.3 MB; construidas en 1.1 s.
- **celda 15 (LightGBM standalone)**: ajustado en 0.27 s, 93 características; `{'Modelo': 'LightGBM quantile 0.35 (standalone)', 'RMSE': 7.113, 'MAE': 5.585, 'R2': 0.8551, 'NASA_Score': 5794.9}`.
- **celda 17 (baseline)**: Baseline media train = 38.08 ciclos; tabla con LightGBM 7.113 frente al baseline 20.022; top-5 rasgos `[f21, f10, f11, f12, f0]`.
- **celda 20 (BiLSTM standalone)**: LightGBM 0.27 s | BiLSTM 65.1 s; épocas ejecutadas 9; mejor val_loss 8.317; `{'Modelo': 'BiLSTM triple pooling (standalone)', 'RMSE': 5.839, 'MAE': 4.491, 'R2': 0.9023, 'NASA_Score': 3984.8}`.
- **celda 21 (NB1 OK)**: guardado de artefactos, siguiente cuaderno.

### 02_decision_ablacion_oof_ensamble.ipynb

- **celda 5 (FASE A OK)**: funciones de evaluación listas.
- **celda 9 (ablación cyc_norm)**: RMSE BiLSTM con cyc_norm 6.006 vs sin 5.784; costo de quitarlo -0.222 RMSE; interpretación: el contador de ciclos es una entrada legítima de producción pero también un atajo (todas las unidades fallan con vida total parecida), el delta es el precio de no apoyarse en ese atajo.
- **celda 14 (OOF)**: OOF base predictions en 269.9 s; folds `[[2,10], [5,18], [20,16]]`; tiempos por fold 107.7 / 93.9 / 59.8 s.
- **celda 15 (beta_hat)**: beta_hat (mediana de los folds) = 1.00; dispersión `{min: 0.0, max: 1.0, iqr: 0.5, n_folds: 3}`; por fold: fold0 beta 1.00 rmse 6.326 (ref BiLSTM 9.271) nasa 3641.8 (ref 5703.2); fold1 beta 1.00 rmse 9.429 (ref 11.525) nasa 6248.5 (ref 8707.3); fold2 beta 0.00 rmse 5.572 (ref 5.580) nasa 3356.7 (ref 3360.4).
- **celda 16 (protocolo legado, solo diagnóstico)**: beta elegido 1.00; RMSE de validación 6.347 frente a referencia BiLSTM 9.335; cociente 0.680x; cociente muy por debajo de 1 = firma del defecto (el meta-aprendiz puntúa filas con las que fue ajustado).
- **celda 18 (meta)**: meta ajustado en 2535 ventanas del motor 16 (RUL 0.0 a 62.0); ridge alpha 7.848 | coef `[0.1368, 0.7672]`; beta = 1.00 (mediana fuera de fold, 3 folds agrupados); nota: el experimento de ajustar el meta sobre el OOF de los cinco motores de ajuste (14915 ventanas, RUL hasta 88) se midió y se rechazó: sobre el motor 16 el meta agrupado predice media 39.9 con RUL real 31.5 y el RMSE crece de 4.04 (beta 0) a 10.17 (beta 1): aprende un prior de nivel de los motores largos que no transfiere a un motor corto. Ver `docs/informes/informe-2026-10-21-motor16-vs-oof.md`.
- **celda 19 (tabla titular)**: LightGBM 7.113 / BiLSTM 5.839 / BiLSTM+EMA5 5.829 / Híbrido stacking (beta 1.00)+EMA5 4.276 con NASA 2322.4; ¿ensamble mejora al campeón en RMSE? True; ¿en NASA? True.
- **celda 21 (extra EMA)**: tabla extra EMA10/5/3 aparte; del BiLSTM al híbrido +1.563 ciclos de RMSE.
- **celda 23 (RMSE por motor)**: motor 11 3.8670, motor 14 8.0179, motor 15 2.6620; macro-RMSE (cada motor pesa 1/3) 4.849; RMSE ponderado por ventana 4.276; diferencia +0.573 (positiva = el global es más halagador que la realidad por motor); el motor con más ventanas pesa más en el global; el macro da voz igual a los tres.
- **celda 25 (banda calibrada)**: banda calibrada en 17450 ventanas fuera de fold (6 motores, beta 1.00), objetivo 90%, 5% por lado; bins: `[0,25) n=5759 q_low -6.3639 q_high 6.7448; [25,50) n=5750 -13.9416/16.4788; [50,75) n=5037 -24.3579/18.6595; [75,None) n=904 -24.4143/-16.9902`; fuera de fold (enviada) ancho medio 23.49 | tramo alto `[-24.41, -16.99] n=904`; motor 16 (diagnóstico) ancho medio 3.48 | tramo alto `[-1.87, +1.82] n=0`; fuera de fold sin sesgo (diagnóstico) ancho medio 23.49 | tramo alto `[-3.96, +3.46] n=904`.
- **celda 26 (cobertura)**: banda cobertura % / ancho medio / por debajo % / por encima %: fuera de fold (enviada) 100.0 / 25.92 / 0.0 / 0.0; motor 16 (diagnóstico) 31.9 / 3.36 / 42.0 / 26.0; fuera de fold sin sesgo (diagnóstico) 100.0 / 25.74 / 0.0 / 0.0; nominal 90 %; la banda enviada sobre-cubre porque la calibraron modelos de fold más débiles que el desplegado; estrecharla sería elegir sobre test, y por eso no se envía la más estrecha: se publica el trade-off; cobertura global en test (banda enviada) 100.0 % | ancho medio 25.92 ciclos; motor 11 3293 ventanas 100.0 % ancho 26.16 se pasa 0.0; motor 14 760 ventanas 100.0 % ancho 26.59 se pasa 0.0; motor 15 2143 ventanas 100.0 % ancho 25.31 se pasa 0.0.
- **celda 27 (NB2 OK)**: beta = 1.0 | p_ens (6196,), siguiente cuaderno.

### 03_evidencia_multisemilla_diagnostico.ipynb

- **celda 5 (FASE A OK)**: funciones listas.
- **celda 8 (métricas sobre semillas [42,7,123])**: tabla con BiLSTM solo 6.3467 ± 0.7483 RMSE_mean, MAE_mean 5.0090 ± 0.8483, R2_mean 0.8836 ± 0.0281, NASA_Score_mean 4530.5000 ± 797.7900; Híbrido+EMA5 4.2777 ± 0.0505 / 3.1827 ± 0.0491 / 0.9476 ± 0.0013 / 2315.0667 ± 45.9411; LightGBM solo 7.0977 ± 0.0337 / 5.5720 ± 0.0335 / 0.8557 ± 0.0014 / 5772.5000 ± 50.1075.
- **celda 9 (tabla redondeada)**: LightGBM solo 7.098 ± 0.034 / 5.572 ± 0.034 / 0.8557 ± 0.0014 / 5772.5 ± 50.1; BiLSTM solo 6.347 ± 0.748 / 5.009 ± 0.848 / 0.8836 ± 0.0281 / 4530.5 ± 797.8; Híbrido+EMA5 4.278 ± 0.051 / 3.183 ± 0.049 / 0.9476 ± 0.0013 / 2315.1 ± 45.9.
- **celda 18 (tabla final test 11/14/15)**: Híbrido+EMA5 4.278 ± 0.051 / 3.183 ± 0.049 / 0.9476 ± 0.0013 / 2315.1 ± 45.9; BiLSTM solo 6.347 ± 0.748 / 5.009 ± 0.848 / 0.8836 ± 0.0281 / 4530.5 ± 797.8; LightGBM solo 7.098 ± 0.034 / 5.572 ± 0.034 / 0.8557 ± 0.0014 / 5772.5 ± 50.1.
- **celda 26 (mejora frente a base)**: frente a LightGBM solo → Híbrido+EMA5 -2.820 RMSE (39.7 %), BiLSTM solo -0.751 (10.6 %); frente a BiLSTM solo → Híbrido+EMA5 -2.069 (32.6 %), LightGBM solo +0.751 (-11.8 %).
- **celda 40 (por motor, híbrido)**: motor 11 3293 ventanas RMSE 3.867 MAE 3.189 Sesgo 3.131; motor 14 760 ventanas 8.018 / 6.138 / -4.888; motor 15 2143 ventanas 2.662 / 2.117 / -1.999.
- **celda 46 (folds beta NB03)**: fold0 `[2,10]` beta 1.0 rmse_val 6.3264 rmse_lstm_ref 9.2714; fold1 `[5,18]` beta 1.0 9.4287 / 11.5251; fold2 `[16,20]` beta 0.0 5.5719 / 5.5800.
- **celda 52 (RELOAD OK)**: RUL estimado 60.40 vs real 58.00; paradigma Hybrid Stacking; recargado == en memoria: True.

## 3. Coherencia de cifras frente al artefacto congelado (publicado)

> **Banner — bundle A obsoleto, bundle B vigente:** las cifras 4.289 / sha `0acd795b…` citadas en esta sección son del bundle A (histórico/pre-B) y no son vigentes. Vigente: bundle B (ref 4.251; media 4.340 ± 0.101). No se cambian las métricas B en este diff.

El artefacto congelado es `models/ds02_manifest.json` (actualmente == `HEAD:models/ds02_manifest.json`, sha `051e0af40613e09ff87aeccacb1209e8b1fe10b99800c73277b0c79dc301a65332`), y `app/cache/cache_manifest.json` cita su sha exactamente (`ensemble_sha256 0acd795b0906389d46b7dc433249438e15b3ee899b1a5bc2cbd8624a6fe6d502`, `manifest_sha256 051e0af4...`). `git status models/ app/cache/` está limpio.

**Cifra publicada (HEAD/manifiesto + cache + README + informes):**
- LightGBM solo: 7.098 ± 0.034
- BiLSTM solo: 6.233 ± 0.485
- Híbrido + EMA5: 4.352 ± 0.055 (fila de test del manifiesto: RMSE 4.289, MAE 3.179, R² 0.9473, NASA 2310.6)
- macro-RMSE: 4.9026

**Cifra del rerun (nb01b/nb02b/nb03b):**

| modelo | rerun | publicado | misma? |
|---|---|---|---|
| LightGBM solo | 7.098 ± 0.034 | 7.098 ± 0.034 | ✅ idéntico |
| BiLSTM solo | 6.347 ± 0.748 | 6.233 ± 0.485 | ❌ difiere |
| Híbrido + EMA5 | 4.278 ± 0.051 | 4.352 ± 0.055 | ❌ difiere |
| Híbrido fila test | 4.276 / 3.180 / 0.9476 / 2322.4 | 4.289 / 3.179 / 0.9473 / 2310.6 | ❌ difiere |
| macro-RMSE | 4.849 | 4.9026 | ❌ difiere |

**Por qué difieren (no es un error de los cuadernos):**
La diferencia lleva en el propio `README.md` del ensemble (`README.md:45-47`): *"The 4.301 → 4.344 → 4.352 differences are TensorFlow CPU non-determinism between..."*, donde se enlistan tres reejecuciones que dan cifras distintas, todas "on disk". Es decir, el pipeline no es bit-a-bit determinista en CPU de TensorFlow porque las operaciones unidas por oneDNN dan redondeos distintos en cada ejecución; el BiLSTM —y por tanto el híbrido que lo contiene— cambia ligeramente; el LightGBM (que no pasa por TF) sí reproduce.

En los folds de beta también hay ligera diferencia: en el rerun los dos primeros folds dan beta 1.0 y el tercero beta 0.0; en la ejecución que generó el manifiesto HEAD, el tercer fold también da beta 1.0 (rmse_val 5.5719, rmse_lstm_ref 5.5800, ambos ~5.58). Eso cambia la distribución de beta y, por tanto, la cifra del híbrido. En todo caso la decisión (híbrido gana) no cambia: en el rerun híbrido 4.278 vs BiLSTM 6.347, diferencia 2.069, mayor que ±0.748 → empate descartado.

**Conclusión de coherencia:** las cifras del rerun son coherentes con el estilo y la magnitud de los cuadernos; no hay nada raro en ellos ni en la cadena de estado. Pero no reproducen exactamente las cifras publicadas, porque el rerun recalendaría `models/` si lo dejara ahí. Por eso el artefacto que cuelga de las cifras publicadas (`models/`) se mantiene en HEAD (congelado y coherente con `app/cache/`), y los cuadernos ejecutados viven en `/tmp` con sus artefactos en `notebooks/ds02_ensemble/artifacts/` (ruta git-ignorada).

## 4. Decisión

- Los cuadernos **son correctos en ejecución y en cadena de estado**: esta es la respuesta a "¿se ejecutaron correctamente?".
- La **incongruencia entre rerun y cifra publicada es esperada** (no determinista de TF en CPU), documentada en el propio README del ensemble, y **no es un fallo de los cuadernos**.
- Si se quiere **consistencia total**, hay que congelar `models/` con las cifras del rerun (reescribir `models/ds02_manifest.json`, regenerar `app/cache/cache_manifest.json`, y actualizar README, docs/informes/informe-2026-10-21-reglas-oof.md y los tasks.md/specs que citan la cifra). Eso es una decisión de auditoría, no un bug a corregir.

## Verificación de ejecución de los cuadernos — evidencia crujiente

La siguiente función reabre las tres copias ejecutadas y escupe el texto útil (solo salidas `text/plain`, saltando figuras y warnings de keras/tensorflow). Se puede volver a ejecutar para auditar las salidas textuales:

```python
import json, os, re

def text_outputs(nb_path):
    nb = json.load(open(nb_path, encoding="utf-8"))
    out = []
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        chunks = []
        for o in c.get("outputs", []):
            if "text" in o:
                chunks.append("".join(o["text"]))
            for k, v in c.get("data", {}).items():
                if k == "text/plain":
                    chunks.append("".join(v))
        text = "\n".join(chunks or [""]).strip()
        if not text:
            continue
        if re.search(r"\bFigure size\b", text):
            continue
        if any(w in text for w in ["WARNING:", "iopub.status", "keras", "tensorflow", "lightgbm", "sklearn", "ds02_rul", "cwd:"]):
            continue
        out.append((i, c.get("execution_count"), text))
    return out

T = os.path.join(os.environ["LOCALAPPDATA"], "Temp")
for tag, f in [("NB01", "nb01b.ipynb"), ("NB02", "nb02b.ipynb"), ("NB03", "nb03b.ipynb")]:
    print("\n" + "=" * 32, tag)
    for idx, ec, text in text_outputs(os.path.join(T, f)):
        print(f"celda {idx} (exec {ec})")
        for ln in text.splitlines():
            if ln.strip():
                print(" ", ln)
```

Ejecutar con:

```
.venv/Scripts/python notebooks/ds02_ensemble/verification_sources.py
```

o con el fragmento incrustado. Los resultados reproducibles que produce son los que figuran en la sección 2 de este informe.

## 5. Ejecución de los cuadernos en el repo (2026-10-22, kernel del venv)

Los tres cuadernos están ejecutados **en el propio repo** (`--inplace`, en orden 01 → 02 → 03). `01` ya estaba ejecutado (11/11, `[NB1 OK]`, artefactos de las 10:55) y de él parten los puentes: `02` imprime `[LOAD NB1 OK]` y `03` imprime `[LOAD NB2 OK]`.

Comando usado (los dos detalles que importan van en los comentarios):

```bash
.venv/Scripts/python.exe -m nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=ds02-venv \
  --ExecutePreprocessor.timeout=3600 \
  notebooks/ds02_ensemble/<NB>.ipynb
```

- `PYTHONPATH=src` **no funciona**: jupyter resuelve el kernel por nombre (`python3` / `ds02-venv`) y el kernel hijo no hereda el entorno del proceso nbconvert; el `env PYTHONPATH=...` solo afecta a nbconvert. Aquí se usa el kernelspec `ds02-venv`, que apunta a `.venv\Scripts\python.exe` (3.12.10) y ese entorno sí tiene `ds02_rul` 4.1.0 (editable desde `src/`).
- **No** usar `.venv\Scripts\jupyter nbconvert`: ese lanzador reejecuta el subcomando buscándolo en `PATH` y coge `jupyter-nbconvert.exe` de Python310 (nbconvert correría en 3.10 mientras el kernel va en 3.12). Con `python -m nbconvert` toda la cadena va en 3.12 (comprobado con `Win32_Process`: nbconvert y kernel ambos en `Python312\python.exe`).

| cuaderno | celdas código | ejecución secuencial | con salida | errores |
|---|---|---|---|---|
| `01_datos_y_bases.ipynb` | 11 | 1 → 11 | 10 | 0 |
| `02_decision_ablacion_oof_ensamble.ipynb` | 17 | 1 → 17 | 16 | 0 |
| `03_evidencia_multisemilla_diagnostico.ipynb` | 24 | 1 → 24 | 23 | 0 |

**Cifras de esta ejecución** (02 = semilla 42; 03 = media ± desv sobre las semillas 42, 7 y 123):

- **02**: `beta_hat = 1.00` (fold0 `[2,10]` 1.0, fold1 `[5,18]` 1.0, fold2 `[16,20]` 0.0); ablación `cyc_norm` 5.625 frente a 5.980 (coste +0.355 RMSE); LightGBM 7.113; Híbrido stacking (beta 1.00) + EMA5 **4.275**; macro-RMSE **4.878**; RMSE ponderado por ventana 4.275; banda calibrada 100 % de cobertura con ancho medio 26.09 ciclos.
- **03**: LightGBM solo 7.098 ± 0.034; BiLSTM solo 6.437 ± 0.757; **Híbrido + EMA5 4.352 ± 0.099** (MAE 3.225 ± 0.055, R² 0.9457 ± 0.0025, NASA 2347.7 ± 53.3); por motor 11 → 3.785, 14 → 8.044, 15 → 2.804; `[RELOAD OK] RUL estimado 60.34 vs real 58.00`, `recargado == en memoria: True`.
- Mejora del híbrido: −2.746 RMSE (38.7 %) frente a LightGBM solo y −2.085 (32.4 %) frente a BiLSTM solo.

**Estado de `models/` tras la ejecución.** El cuaderno 03 reescribe `models/ensemble.joblib`, `models/scaler.joblib`, `models/bilstm_ds02.keras`, `models/ds02_manifest.json` y las dos copias de raíz (`ensemble.joblib`, `scaler.joblib`). Tras verificar la ejecución se restauró `models/` y las copias de raíz a HEAD (`git checkout --`), de modo que el artefacto publicado sigue siendo el congelado: sha256 del manifiesto `051e0af40613e09ff87aeccb1209e8b1fe10b99800c73277b0c79dc301a65332`. La copia de esta ejecución queda en `C:\Users\mikel\AppData\Local\Temp\ds02_backup\` (`models\` + las dos copias de raíz).

**Coherencia con la cifra publicada (sección 3).** LightGBM idéntico (7.098 ± 0.034); el híbrido con la misma media (4.352) pero otra dispersión (± 0.099 frente a ± 0.055); BiLSTM distinto (6.437 ± 0.757 frente a 6.233 ± 0.485). Es el no determinismo de TF en CPU ya documentado en el README del ensemble, no un fallo de los cuadernos; la decisión no cambia (el híbrido gana por ~2 RMSE, muy por encima de cualquier ±).
