# 02_decision_ablacion_oof_ensamble.ipynb — copia literal para NotebookLM

> Exportado de `notebooks/ds02_ensemble/02_decision_ablacion_oof_ensamble.ipynb`. Cada celda en orden, markdown y código sin resumir.

## Celda 1 (markdown)

# 02 · Decisión: ablación, beta OOF y ensamble

Parte 2 de 3. Mismo código que las secciones 6–8 del original.

**Requisito:** haber corrido el `01` (usa su `artifacts/`). No re-entrena la semilla 42.

## Celda 2 (code)

```python
# FIX ruta: los cuadernos viven en notebooks/ds02_ensemble pero los datos estan en la raiz.
# Se vuelve a la raiz para que archive/... y models/... resuelvan igual que en el original.
import pathlib as _pl
_ROOT = _pl.Path().resolve()
while not (_ROOT / "pyproject.toml").exists() and _ROOT != _ROOT.parent:
    _ROOT = _ROOT.parent
import os as _os
_os.chdir(_ROOT)
print("cwd:", _os.getcwd())
import os
import sys
import time
import warnings
warnings.filterwarnings('ignore')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')

import numpy as np
import pandas as pd

import ds02_rul
from ds02_rul import calculate_nasa_score, evaluate_predictions, macro_rmse
from ds02_rul.conformal import apply_conformal, empirical_coverage, fit_conformal
from ds02_rul.data import load_ds02
from ds02_rul.features import build_windows, fit_preprocessing
from ds02_rul.model import build_champion_bilstm
from ds02_rul.persistence import build_manifest, load_ensemble, save_ensemble
from ds02_rul.smoothing import causal_ema_by_unit
from ds02_rul.stacking import (
    fit_meta_learners, in_sample_beta_diagnostic, meta_predict, select_beta_grouped,
)
from ds02_rul.pipeline import (
    ablation_table, make_lgbm, oof_base_predictions, run_seed, seed_summary,
)

import keras
import lightgbm as lgb
import sklearn

SEEDS = [42, 7, 123]
PRIMARY_SEED = SEEDS[0]
WINDOW_SIZE = 50
STEP_TRAIN = 3
STEP_TEST = 2

print('python  :', sys.version.split()[0])
print('keras   :', keras.__version__)
print('lightgbm:', lgb.__version__)
print('sklearn :', sklearn.__version__)
print('ds02_rul:', ds02_rul.__version__, '->', os.path.dirname(ds02_rul.__file__))

```
> (2 outputs omitidos, solo código)

## Celda 3 (markdown)

### Glosario en 30 segundos (estilo clase)

| Nombre | Qué es | Dónde vive |
|---|---|---|
| `WINDOW=50` | 50 lecturas seguidas = 1 ventana | `features.py:build_windows` |
| `STEP 3/2` | Separación entre ventanas (train/test) | `pipeline.py:run_seed` |
| `BETA` | Cuánto manda el meta (mediana OOF, `1.0`) | `stacking.py:select_beta_grouped` |
| `EMA5` | Suavizado causal por motor | `smoothing.py:causal_ema_by_unit` |
| `L_inf` | Peor caso de la banda 90% | `conformal.py:apply_conformal` |
| `OOF` | Cada ventana la puntúa otro motor | `pipeline.py:oof_base_predictions` |
| `macro` | Cada motor pesa 1/3 | `metrics.py:macro_rmse` |


## Celda 4 (code)

```python
# 1. Presentacion estilo clase: 1 linea como `from sklearn... import ...`
#    Tablas y graficos viven en src/ds02_rul/viz.py; aqui solo se importan.
#    Nada de abajo entrena ni cambia metricas: es solo formato.
from ds02_rul.viz import *
print("[VIZ OK] tablas y graficos listos (solo formato, no entrenan)")

```
> (1 outputs omitidos, solo código)

## Celda 5 (code)

```python
# Puente: recupera lo calculado en NB1 (no re-entrena la semilla 42)
import pathlib, joblib, numpy as np, pandas as pd
from ds02_rul.data import load_ds02
ART = _ROOT / "notebooks" / "ds02_ensemble" / "artifacts"
assert (ART / "nb1_dev.npz").exists(), "Falta NB1: ejecuta primero 01_datos_y_bases.ipynb"
d = np.load(ART / "nb1_dev.npz"); t = np.load(ART / "nb1_test.npz")
aux = joblib.load(ART / "nb1_aux.joblib")
ra = joblib.load(ART / "nb1_result_arrays.joblib")
from keras.models import load_model
FIT_UNITS = [2.0, 5.0, 10.0, 18.0, 20.0]
HOLDOUT_UNITS = [16.0]; TEST_UNITS = [11.0, 14.0, 15.0]
raw = load_ds02(stride=100)
prep = aux["prep"]; fit_idx = aux["fit_idx"]; hold_idx = aux["hold_idx"]
dev_units = aux["dev_units"]; lgbm = aux["lgbm"]
p_lgb_hold = aux["p_lgb_hold"]; p_lgb_test = aux["p_lgb_test"]
dev = {"X_seq": d["X_seq"], "X_tab": d["X_tab"], "y": d["y"], "X_raw": d["X_raw"],
       "meta": pd.DataFrame({"unit": d["meta_unit"], "cycle": d["meta_cycle"]})}
test = {"X_seq": t["X_seq"], "X_tab": t["X_tab"], "y": t["y"], "X_raw": t["X_raw"],
        "meta": pd.DataFrame({"unit": t["meta_unit"], "cycle": t["meta_cycle"]})}
bilstm = load_model(ART / "bilstm_seed42.keras")
result = {"bilstm": bilstm, "lgbm": lgbm, "prep": prep, "dev": dev, "test": test,
          "fit_idx": fit_idx, "hold_idx": hold_idx,
          "p_lstm_hold": ra["p_lstm_hold"], "p_lstm_test": ra["p_lstm_test"],
          "p_lgb_hold": ra["p_lgb_hold"], "p_lgb_test": ra["p_lgb_test"],
          "t_lgb": ra["t_lgb"], "t_lstm": ra["t_lstm"], "history": type("H", (), {"history": ra["history"]})()}
print("[LOAD NB1 OK] dev", dev["X_seq"].shape, "| test", test["X_seq"].shape, "| bilstm recargado")

```
> (2 outputs omitidos, solo código)

## Celda 6 (markdown)

### Compatibilidad estilo clase (solo presentacion)

`evaluar_clase` y `mostrar_clase` son alias de lo que ya usas (`evaluate_predictions`, `tabla_modelos`).
No entrenan nada ni cambian numeros: solo devuelven la misma fila y la pintan redondeada, como el `evaluar()/mostrar()` de RequisitosClase.


## Celda 7 (code)

```python
# 2. Alias estilo clase (solo lectura: no entrenan, no cambian numeros).
#    evaluar_clase/mostrar_clase ya vienen de viz (ver src/ds02_rul/viz.py).
print("[FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)")

```
> (1 outputs omitidos, solo código)

## Celda 8 (markdown)

<details><summary><b>Para entenderlo (estilo clase)</b></summary>

- **OOF agrupado:** cada ventana la puntua un meta ajustado en *otros* motores. Asi la nota no se mide sobre su propio ajuste.
- **beta:** cuanto de la opinion del meta reemplaza a la del BiLSTM. `beta=0` = campeon intacto (sin riesgo).
- **Conformal:** banda calibrada sobre residuales fuera de fold, con cuantiles asimetricos por tramo (la penalizacion NASA tampoco es simetrica).
- **Regla de empate (como en clase):** si dos modelos se diferencian menos que su `±` entre semillas, es empate y se elige el simple.
</details>


## Celda 9 (markdown)

## 6 · Ablación de `cyc_norm` — medida, no afirmada

La revisión anterior citaba *13,349* como el costo de quitar el contador de
ciclos. Ese número venía de la iteración 3, que tenía 78 características, ningún
ciclo acumulado **y ninguna residualización**: otro diseño, no este menos una
columna. Así que la tabla de abajo se calcula acá, y lo que diga es la respuesta.

La alternativa al contador de ciclos es una **línea base sana por motor**: la
media del vector de sensores residualizado en los tres primeros ciclos de ese
motor, restada del resto de su vida. Es causal (solo lee la vida temprana de ese
mismo motor) y es lo que una flota real registraría en la puesta en marcha.


## Celda 10 (code)

```python
abl = ablation_table(raw, seeds=(PRIMARY_SEED,), window=WINDOW_SIZE,
                    step_train=STEP_TRAIN, step_test=STEP_TEST, epochs=22,
                    fit_units=FIT_UNITS, holdout_units=HOLDOUT_UNITS,
                    include_bilstm=True)
print('Ablación medida sobre los motores de test 11/14/15 (una sola semilla = 42)')
print()
print(abl.pivot(index='variant', columns='model',
                values=['RMSE', 'NASA_Score']).round(3).to_string())
print()
print(abl.to_string(index=False))

```
> (2 outputs omitidos, solo código)

## Celda 11 (code)

```python
baseline_rmse = float(abl.loc[(abl.variant == 'cyc_norm ON  (baseline)') & (abl.model == 'BiLSTM'), 'RMSE'].iloc[0])
no_cycle_rmse = float(abl.loc[(abl.variant == 'cyc_norm OFF') & (abl.model == 'BiLSTM'), 'RMSE'].iloc[0])
delta_rmse = no_cycle_rmse - baseline_rmse

print(f'RMSE del BiLSTM con cyc_norm : {baseline_rmse:.3f}')
print(f'RMSE del BiLSTM sin          : {no_cycle_rmse:.3f}')
print(f'costo medido de quitarlo     : {delta_rmse:+.3f} RMSE')
print()
print('Interpretación: el contador de ciclos es una entrada legítima de producción')
print('(una flota sabe cuántos ciclos voló un motor), pero también es un atajo:')
print('todas las unidades de entrenamiento fallan con una vida total parecida, así')
print('que el ciclo por sí solo casi determina la RUL. El delta de arriba es el')
print('precio de no apoyarse en ese atajo.')

```
> (1 outputs omitidos, solo código)

## Celda 12 (markdown)

**Cómo leer el gráfico:** cada grupo es una variante de la ablación y dentro de
cada grupo hay una barra por modelo, con el RMSE de test. Más corta es mejor.
Lo que importa es la diferencia **dentro de un grupo** (qué modelo gana con ese
diseño) y la diferencia **entre grupos** (cuánto cuesta cambiar el diseño).


## Celda 13 (code)

```python
barras_ablacion(abl, metrica='RMSE')
```
> (2 outputs omitidos, solo código)

## Celda 14 (markdown)

**Qué vemos.** Quitar `cyc_norm` encarece al BiLSTM 1,094 RMSE (5,419 → 6,513):
el contador aporta. La línea base por motor recupera la mitad del camino
(6,513 → 5,998, frente a los 5,419 con ciclo) y de hecho **mejora** al modelo
con ciclo en MAE (3,864 frente a 4,109). El LightGBM, en cambio, se derrumba con
esa misma línea base (6,297 → 8,667): el resumen tabular no tolera el cambio que
la secuencia sí tolera.


## Celda 15 (markdown)

> TIP En resumen (para presentar): Dos especialistas ven mejor que uno. BiLSTM lee la pelicula temporal de la ventana (inercia, triple-pooling: ultimo+media+maximo) y LightGBM evalua estadisticas del residuo. El meta-modelo los combina con `beta` elegido fuera de fold (mediana agrupada, `beta=1.0`) y el filtro EMA causal (`ema_span=5`) evita que la alarma parpadee. El OOF agrupado garantiza que cada ventana la puntua un meta ajustado en *otros* motores.


## Celda 16 (markdown)

## 7 · Calibración fuera de fold de `beta`

`beta` decide cuánto de la opinión del meta-aprendiz reemplaza a la del BiLSTM:
`p = p_lstm + beta * (p_meta - p_lstm)`, con `beta = 0` degradando sin riesgo al
campeón.

Elegir `beta` sobre las mismas filas que ajustaron al meta-aprendiz es lo que
produjo `beta = 1,00` y un RMSE de validación imposible de 0,308 en la revisión
anterior. Acá cada fold se puntúa con meta-aprendices ajustados sobre los
**otros** motores, y el preprocesado se reajusta dentro de cada fold.

Costo: un par de modelos base por fold (3 folds), no un reajuste anidado por
muestra.


## Celda 17 (code)

```python
t0 = time.time()
oof = oof_base_predictions(raw, dev_units, n_splits=3, seed=PRIMARY_SEED,
                           window=WINDOW_SIZE, step_train=STEP_TRAIN, epochs=15,
                           use_cycle=True)
print(f'OOF base predictions in {time.time() - t0:.1f} s')
print('folds:', oof['unit_folds'])
print('timing:', oof['timing'])

```
> (1 outputs omitidos, solo código)

## Celda 18 (code)

```python
selection = select_beta_grouped(oof['units'], oof['cycles'], oof['y'],
                                oof['pred_lstm'], oof['pred_lgb'],
                                span=5, use_cycle_feature=False)

print(f"beta_hat (mediana de los folds) = {selection['beta']:.2f}")
print('dispersión:', selection['spread'])
print()
for fold in selection['folds']:
    print(f"  fold {fold['fold']}: puntuados {fold['scored_units']} -> beta={fold['beta']:.2f} "
          f"| rmse {fold['rmse_val']:.3f} (ref BiLSTM {fold['rmse_lstm_ref']:.3f}) "
          f"| nasa {fold['nasa_val']:.1f} (ref {fold['nasa_lstm_ref']:.1f})")

```
> (1 outputs omitidos, solo código)

## Celda 19 (code)

```python
# El protocolo legado, conservado a propósito: ajustar y puntuar sobre las mismas filas.
diag = in_sample_beta_diagnostic(oof['units'], oof['cycles'], oof['y'],
                                 oof['pred_lstm'], oof['pred_lgb'])
print('Protocolo legado de un solo motor (SOLO DIAGNÓSTICO — no usar para elegir beta)')
print(f"  beta elegido = {diag['beta']:.2f}")
print(f"  RMSE de validación {diag['rmse_val']:.3f} frente a la referencia BiLSTM {diag['rmse_lstm_ref']:.3f}")
print(f"  cociente {diag['rmse_val'] / diag['rmse_lstm_ref']:.3f}x")
print()
print('Un cociente muy por debajo de 1 es la firma del defecto: el meta-aprendiz')
print('está puntuando filas con las que fue ajustado. Compáralo con los folds de arriba.')

```
> (1 outputs omitidos, solo código)

## Celda 20 (markdown)

## 8 · Evaluación híbrida sobre los motores de test

Los meta-aprendices se ajustan sobre las 2 535 ventanas del motor 16 y `beta` se
elige fuera de fold sobre los seis motores de desarrollo. **Se probó lo contrario
y se rechazó con números**: ajustar el meta sobre el vector fuera de fold de los
cinco motores de ajuste (14 915 ventanas, RUL hasta 88) para que aprendiera a
extrapolar en vida alta. Sobre el motor 16 ese meta predice una media de 39.9
cuando la RUL real media es 31.5, y el error crece de forma monótona con `beta`:
RMSE 4.04 con `beta = 0`, 7.48 con 0.6 y 10.17 con 1. La razón es que los motores
de ajuste viven más que los de test, así que el aprendiz agrupado aprende un
**prior de nivel** que no transfiere. El experimento queda documentado en
`INFORME_motor16_vs_oof.md`; las funciones que lo reproducen siguen en
`ds02_rul.stacking` (`fit_meta_learners`, `score_beta_holdout`).

Las meta-características son **`[p_lstm, p_lgb]`**: dos columnas. `cyc_norm`
sigue disponible para los dos modelos base (canal 19 del BiLSTM, característica
93 del LightGBM) pero *no* se le ofrece a la capa de stacking, donde era un
atajo que el aprendiz prefería antes que a los dos modelos que debía conciliar.


## Celda 21 (code)

```python
hold_cycles = dev['meta']['cycle'].values[hold_idx]
hold_units = dev['meta']['unit'].values[hold_idx]
y_hold = dev['y'][hold_idx]

# El reloj esta ausente de esta capa a proposito: con `cyc_norm` disponible el
# aprendiz ponia ~100 % del peso en el contador y descartaba las dos ramas.
Z_hold = np.column_stack([result['p_lstm_hold'], result['p_lgb_hold']])

ridge_meta, lgb_meta = fit_meta_learners(Z_hold, y_hold, seed=PRIMARY_SEED)
p_meta_hold = meta_predict(ridge_meta, lgb_meta, Z_hold)

BETA = selection['beta']
print(f'meta ajustado en : {len(y_hold)} ventanas del motor 16 (RUL 0.0 a {y_hold.max():.1f})')
print(f'ridge            : alpha {ridge_meta.alpha_:.4g} | coef {np.round(ridge_meta.coef_, 4).tolist()}')
print(f'beta = {BETA:.2f}  (mediana fuera de fold, 3 folds agrupados)')
print()
print('Nota: el experimento de ajustar el meta sobre el OOF de los cinco motores de')
print('ajuste (14 915 ventanas, RUL hasta 88) se midio y se rechazo. Sobre el motor 16')
print('el meta agrupado predice media 39.9 con RUL real 31.5 y el RMSE crece de 4.04')
print('(beta=0) a 10.17 (beta=1): aprende un prior de nivel de los motores largos que')
print('no transfiere a un motor corto. Ver INFORME_motor16_vs_oof.md.')

```
> (1 outputs omitidos, solo código)

## Celda 22 (code)

```python
from ds02_rul import HybridStackingEnsemble

ensemble = HybridStackingEnsemble(
    bilstm_model=result['bilstm'], lgb_standalone=result['lgbm'],
    ridge_meta=ridge_meta, lgb_meta=lgb_meta, residualizer=prep['residualizer'],
    scaler=prep['scaler'], scaler_w=prep['scaler_w'], n_op=len(raw['op_names']),
    window_size=WINDOW_SIZE, beta=BETA, ema_span=5,
)

p_ens = ensemble.predict(test['X_raw'], test['meta']['cycle'].values, test['meta']['unit'].values)
p_lstm_ema = causal_ema_by_unit(result['p_lstm_test'], test['meta']['unit'].values,
                               test['meta']['cycle'].values, span=5)

rows = [
    evaluate_predictions(test['y'], result['p_lgb_test'], 'LightGBM (cuantil 0.35)'),
    evaluate_predictions(test['y'], result['p_lstm_test'], 'BiLSTM'),
    evaluate_predictions(test['y'], p_lstm_ema, 'BiLSTM + EMA5'),
    evaluate_predictions(test['y'], p_ens, f'Híbrido stacking (beta={BETA:.2f}) + EMA5'),
]
res = pd.DataFrame(rows)
print(res.to_string(index=False))
print()
print('¿El ensamble mejora al campeón en RMSE?:', rows[3]['RMSE'] < rows[2]['RMSE'])
print('¿El ensamble mejora al campeón en NASA?:', rows[3]['NASA_Score'] < rows[2]['NASA_Score'])

```
> (1 outputs omitidos, solo código)

## Celda 23 (markdown)

### Baseline en la tabla titular (estilo clase)

En clase la comparativa que decide siempre empieza por el modelo más tonto. Aquí es
`Baseline (media train)`: predecir siempre la media del RUL de los motores de ajuste
(38.08 ciclos). Solo lectura: no entra en la elección, solo calibra la tabla.

## Celda 24 (code)

```python
# Baseline en la tabla titular (SOLO lectura: usa predicciones ya calculadas)
pred_media_nb2 = np.full_like(np.asarray(test["y"]), float(np.asarray(dev["y"])[fit_idx].mean()), dtype=float)
fila_base_nb2 = evaluar_clase("Baseline (media train)", test["y"], pred_media_nb2)
res_con_base = pd.DataFrame([fila_base_nb2] + rows)
display(res_con_base.round(3))
print("Cualquier modelo útil tiene que ganarle al baseline; no entra en la elección.")

```
> (2 outputs omitidos, solo código)

## Celda 25 (markdown)

**Fijate:** la cascada de abajo dice cuanto aporta cada pieza. Los extras van en tabla `extra` aparte, como en clase.

## Celda 26 (code)

```python
# Fase A+B — extras separados + cascada de la decision (SOLO lectura, sin re-entrenar)
# Extra estilo clase: sensibilidad al suavizado EMA sobre el BiLSTM (barato, sin ajustar nada)
from ds02_rul.smoothing import causal_ema_by_unit
units_t = test["meta"]["unit"].values; cycles_t = test["meta"]["cycle"].values
extra = []
for span in [3, 5, 10]:
    pe = causal_ema_by_unit(result["p_lstm_test"], units_t, cycles_t, span=span)
    r = evaluar_clase(f"BiLSTM + EMA{span}", test["y"], pe)
    extra.append(r)
mostrar_clase(extra)
print("Nota: van en tabla `extra` aparte para no mezclar con la tabla titular, como en clase.")

# Cascada RMSE: BiLSTM -> +EMA5 -> hibrido (usa `rows`, ya calculado arriba)
import matplotlib.pyplot as plt
orden = ["BiLSTM", "BiLSTM + EMA5", rows[3]["Modelo"]]
vals = [rows[1]["RMSE"], rows[2]["RMSE"], rows[3]["RMSE"]]
plt.figure(figsize=(7, 3.2))
plt.barh(orden, vals, color=["#4C72B0", "#7FB3D5", "#1FA098"])
plt.xlabel("RMSE en test (ciclos, menos es mejor)")
for i, v in enumerate(vals):
    plt.text(v, i, f" {v:.3f}", va="center")
plt.tight_layout(); plt.show()
print(f"Del BiLSTM al hibrido: {rows[1]['RMSE'] - rows[3]['RMSE']:+.3f} ciclos de RMSE")

```
> (4 outputs omitidos, solo código)

## Celda 27 (markdown)

### 8b · Qué esconde el RMSE global, y cuánto no sabemos

Dos cosas que un único número no dice: si el error está repartido o concentrado
en un motor, y cuál es la banda dentro de la que la predicción es defendible.

## Celda 28 (code)

```python
macro = macro_rmse(test['y'], p_ens, test['meta']['unit'].values)
per_unit = pd.DataFrame([{'motor': int(k), 'RMSE': v}
                        for k, v in macro['per_unit_rmse'].items()])
print('RMSE por motor')
print(per_unit.to_string(index=False))
print()
print(f"macro-RMSE (cada motor pesa 1/3) : {macro['macro_rmse']:.3f}")
print(f"RMSE ponderado por ventana       : {rows[3]['RMSE']:.3f}")
print(f"diferencia                       : {macro['macro_rmse'] - rows[3]['RMSE']:+.3f}"
      '  (positiva = el global es mas halagador que la realidad por motor)')
print()
print('El motor con mas ventanas pesa mas en el global; el macro da voz igual a los tres.')

```
> (2 outputs omitidos, solo código)

## Celda 29 (markdown)

> TIP En resumen (para presentar): En aviacion, predecir de mas cuesta un motor en vuelo; predecir de menos solo adelanta una revision. Por eso decidimos sobre `L_inf`, el limite inferior de la banda conformal calibrada fuera de fold al 90% (asimetrica por tramo, `alpha_each_side=0.05`). Si la banda sobre-cubre, se publica el trade-off en vez de estrecharla eligiendo sobre test.


## Celda 30 (markdown)

**Cómo leer la banda.** El intervalo es *split conformal* sobre los residuales
**fuera de fold** de los seis motores de dev, con cuantiles **asimétricos** por
tramo de RUL predicha, porque la penalización NASA tampoco es simétrica.

Calibrar sobre el motor 16, que es lo que pide la intuición, se midió y se
descarta por dos razones concretas: el meta-aprendiz se ajusta en el 16, así que
sus residuales ahí son de *ajuste* y no de uso; y el 16 no tiene ni una fila por
encima de 62 ciclos, de modo que ninguna banda calibrada en él puede cubrir el
régimen de vida alta, que es justo donde el error se concentra. La celda siguiente
publica las tres variantes para que la diferencia sea un número y no una opinión;
la que viaja en el artefacto es la de fuera de fold.

## Celda 31 (code)

```python
# Calibracion sobre los residuales FUERA DE FOLD de los seis motores de dev:
# cada fila la puntuo un meta ajustado en los otros motores, asi que la banda no
# se mide sobre el propio ajuste del meta.
calib = selection['oof_calib']
conformal = fit_conformal(calib['y'], calib['pred_ema'], target=0.90)
ensemble.conformal = conformal

print(f"banda calibrada en {conformal['n_calibration']} ventanas fuera de fold "
      f"({len(np.unique(calib['units']))} motores, beta={calib['beta']:.2f}) "
      f"(objetivo {conformal['target_coverage']:.0%}, {conformal['alpha_each_side']:.0%} por lado)")
print(pd.DataFrame(conformal['bins']).to_string(index=False))

# Dos diagnosticos, no candidatos: se publican para que la eleccion sea explicita.
# (a) sobre el motor 16 con el modelo final: mide el ajuste del meta, no su uso.
p16 = ensemble.predict(dev['X_raw'][hold_idx], dev['meta']['cycle'].values[hold_idx],
                       dev['meta']['unit'].values[hold_idx])
conformal_16 = fit_conformal(dev['y'][hold_idx], p16, target=0.90)
# (b) fuera de fold sin el sesgo de nivel: mide solo la dispersion.
conformal_debiased = fit_conformal(calib['y'], calib['pred_ema'], target=0.90, debias=True)

print()
for nombre, banda in (('fuera de fold (enviada)', conformal),
                      ('motor 16 (diagnostico)', conformal_16),
                      ('fuera de fold sin sesgo (diagnostico)', conformal_debiased)):
    anchos = [b['q_high'] - b['q_low'] for b in banda['bins']]
    alto = banda['bins'][-1]
    print(f"{nombre:40s} ancho medio {np.mean(anchos):6.2f} | "
          f"tramo alto [{alto['q_low']:+.2f}, {alto['q_high']:+.2f}] n={alto['n']}")

```
> (2 outputs omitidos, solo código)

## Celda 32 (code)

```python
point, lo, hi = ensemble.predict_interval(test['X_raw'], test['meta']['cycle'].values,
                                          test['meta']['unit'].values)

# Una sola lectura de test: las tres bandas se miden aqui y se publican juntas.
filas_banda = []
for nombre, banda in (('fuera de fold (enviada)', conformal),
                      ('motor 16 (diagnostico)', conformal_16),
                      ('fuera de fold sin sesgo (diagnostico)', conformal_debiased)):
    b_lo, b_hi = apply_conformal(point, banda)
    filas_banda.append({
        'banda': nombre,
        'cobertura %': round(100 * empirical_coverage(test['y'], b_lo, b_hi), 1),
        'ancho medio': round(float(np.mean(b_hi - b_lo)), 2),
        'por debajo %': round(100 * float(np.mean(test['y'] < b_lo)), 1),
        'por encima %': round(100 * float(np.mean(test['y'] > b_hi)), 1),
    })
print(pd.DataFrame(filas_banda).to_string(index=False))
print()
print('Nominal 90 %. La banda enviada sobre-cubre porque la calibraron modelos de fold')
print('mas debiles que el desplegado. Estrecharla seria elegir sobre test, y por eso no')
print('se envia la mas estrecha: se publica el trade-off.')
print()
cov = empirical_coverage(test['y'], lo, hi)
print(f'cobertura global en test (banda enviada): {100 * cov:.1f} % | ancho medio {np.mean(hi - lo):.2f} ciclos')
print()

cov_rows = []
for unit in np.unique(test['meta']['unit'].values):
    m = test['meta']['unit'].values == unit
    cov_rows.append({
        'motor': int(unit),
        'ventanas': int(m.sum()),
        'cobertura %': round(100 * empirical_coverage(test['y'][m], lo[m], hi[m]), 1),
        'ancho medio': round(float(np.mean((hi - lo)[m])), 2),
        'se pasa %': round(100 * float(np.mean(test['y'][m] > hi[m])), 1),
    })
print(pd.DataFrame(cov_rows).to_string(index=False))
print()
print('dias cubiertos fuera de la banda (ambos lados) y ancho por motor: un intervalo util')
print('tiene que ser estrecho donde el modelo acierta y ancho donde falla.')

```
> (1 outputs omitidos, solo código)

## Celda 33 (code)

```python
# Puente NB2 -> NB3: guarda decision (beta, metas, ensamble, bandas)
import pathlib, joblib, numpy as np
ART = _ROOT / "notebooks" / "ds02_ensemble" / "artifacts"
joblib.dump({"ridge_meta": ridge_meta, "lgb_meta": lgb_meta, "BETA": BETA,
             "selection_beta": float(selection["beta"]),
             "oof_calib": selection["oof_calib"], "folds": selection["folds"],
             "spread": selection.get("spread", None)},
            ART / "nb2_selection.joblib")
joblib.dump({"conformal": conformal, "conformal_16": conformal_16,
             "conformal_debiased": conformal_debiased}, ART / "nb2_conformal.joblib")
np.save(ART / "nb2_p_ens.npy", p_ens)
np.save(ART / "nb2_lo.npy", np.asarray(lo))
np.save(ART / "nb2_hi.npy", np.asarray(hi))
joblib.dump({"rows": rows, "macro": macro}, ART / "nb2_eval.joblib")
print("[NB2 OK] beta =", round(float(BETA), 2), "| p_ens", p_ens.shape)
print("siguiente: abrir 03_evidencia_multisemilla_diagnostico.ipynb")

```
> (1 outputs omitidos, solo código)
