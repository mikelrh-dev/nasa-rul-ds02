```python
# Descubrimiento robusto de la raiz del proyecto (no usar ../ relativo)
import pathlib as _pl, os as _os, sys as _sys
_ROOT = _pl.Path().resolve()
while not (_ROOT / "pyproject.toml").exists() and _ROOT != _ROOT.parent:
    _ROOT = _ROOT.parent
_os.chdir(_ROOT)
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))
if str(_ROOT / "src") not in _sys.path:
    _sys.path.insert(0, str(_ROOT / "src"))
print("cwd:", _os.getcwd())

```

    cwd: C:\Users\mikel\Desktop\Pruebas\nasa
    

# 03 · Features secuenciales — ¿el reloj (`cyc_norm`) ayuda o es trampa?

Parte 2 de 3. Mismo código que la sección 6 del original.

**Requisito:** ninguno. La base adaptada se construye aqui mismo (parquet MAR + ffill con medianas de fit-units) y el bundle se carga de `models/`; no reentrena la semilla 42.


**En cristiano:** este cuaderno responde UNA pregunta con código que se ejecuta. Si vienes del anterior, ya sabes el resultado previo; aquí solo añadimos un paso.



```python
# 2. Alias estilo clase (solo lectura: no entrenan, no cambian numeros).
#    evaluar_clase/mostrar_clase ya vienen de viz (ver src/ds02_rul/viz.py).
print("[FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)")

```

    [FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)
    


```python
# Puente C: base adaptada (MAR T30 + ffill) + bundle desplegado en models/.
# Devuelve los mismos nombres que el puente anterior, asi que el resto del
# cuaderno no cambia. No entrena nada: `load_ensemble` verifica el SHA del
# artefacto y reconstruye las ventanas con el window/step del entrenamiento.
import os as _os
import pathlib as _pl
import sys as _sys

# Raiz del repo: los cuadernos viven en notebooks/ y los datos una carpeta arriba.
# La celda se busca la raiz sola, asi no depende del orden de ejecucion.
_ROOT = _pl.Path.cwd().resolve()
while not (_ROOT / "pyproject.toml").exists() and _ROOT != _ROOT.parent:
    _ROOT = _ROOT.parent
_os.chdir(_ROOT)
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from src.clase.puente_c import puente_c

P = puente_c()
raw, dev, test, prep = P["raw"], P["dev"], P["test"], P["prep"]
fit_idx, hold_idx, dev_units = P["fit_idx"], P["hold_idx"], P["dev_units"]
result = P["result"]
bilstm, lgbm = result["bilstm"], result["lgbm"]
p_lstm_hold, p_lstm_test = result["p_lstm_hold"], result["p_lstm_test"]
p_lgb_hold, p_lgb_test = result["p_lgb_hold"], result["p_lgb_test"]
FIT_UNITS = [2.0, 5.0, 10.0, 18.0, 20.0]
HOLDOUT_UNITS = [16.0]
TEST_UNITS = [11.0, 14.0, 15.0]
print("[PUENTE C OK] dev", dev["X_seq"].shape, "| test", test["X_seq"].shape,
      "| particiones", P["particiones"])

```

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



```python
PRIMARY_SEED=42; WINDOW_SIZE=50; STEP_TRAIN=3; STEP_TEST=2
# Ablación en vivo: ¿cuánto cuesta quitar el reloj? (4 variantes, 1 semilla=42)
# Cada variante re-entrena LGBM+BiLSTM con el mismo protocolo; lo barato tarda segundos, lo caro (BiLSTM) manda en el tiempo.
from ds02_rul.pipeline import ablation_table
abl = ablation_table(raw, seeds=(PRIMARY_SEED,), window=WINDOW_SIZE,
                    step_train=STEP_TRAIN, step_test=STEP_TEST, epochs=22,
                    fit_units=FIT_UNITS, holdout_units=HOLDOUT_UNITS,
                    include_bilstm=True)
print('Ablación medida sobre test 11/14/15 (semilla 42)')
print()
print(abl.pivot(index='variant', columns='model', values=['RMSE','NASA_Score']).round(3).to_string())
print()
print(abl.to_string(index=False))

```

    WARNING:tensorflow:From C:\Users\mikel\AppData\Local\Programs\Python\Python312\Lib\site-packages\keras\src\backend\common\global_state.py:82: The name tf.reset_default_graph is deprecated. Please use tf.compat.v1.reset_default_graph instead.
    
    

    Ablación medida sobre test 11/14/15 (semilla 42)
    
                                    RMSE                   NASA_Score                   
    model                         BiLSTM BiLSTM+EMA   LGBM     BiLSTM BiLSTM+EMA    LGBM
    variant                                                                             
    cyc_norm OFF                   6.308      6.261  6.297     3633.0     3597.4  4594.5
    cyc_norm OFF + baseline delta  5.577      5.521  8.667     3093.7     3051.4  8271.6
    cyc_norm ON  (baseline)        5.412      5.375  7.113     3406.6     3376.7  5794.9
    cyc_norm ON  + baseline delta  6.021      5.985  8.578     4150.1     4117.2  8079.2
    
                          variant      model  RMSE   MAE     R2  NASA_Score
          cyc_norm ON  (baseline)       LGBM 7.113 5.585 0.8551      5794.9
          cyc_norm ON  (baseline)     BiLSTM 5.412 4.059 0.9161      3406.6
          cyc_norm ON  (baseline) BiLSTM+EMA 5.375 4.021 0.9173      3376.7
                     cyc_norm OFF       LGBM 6.297 4.947 0.8864      4594.5
                     cyc_norm OFF     BiLSTM 6.308 3.911 0.8860      3633.0
                     cyc_norm OFF BiLSTM+EMA 6.261 3.890 0.8877      3597.4
    cyc_norm OFF + baseline delta       LGBM 8.667 7.060 0.7849      8271.6
    cyc_norm OFF + baseline delta     BiLSTM 5.577 3.700 0.9109      3093.7
    cyc_norm OFF + baseline delta BiLSTM+EMA 5.521 3.663 0.9127      3051.4
    cyc_norm ON  + baseline delta       LGBM 8.578 7.140 0.7892      8079.2
    cyc_norm ON  + baseline delta     BiLSTM 6.021 4.692 0.8961      4150.1
    cyc_norm ON  + baseline delta BiLSTM+EMA 5.985 4.652 0.8974      4117.2
    

## Ablación de `cyc_norm` — medida, no afirmada

Hay un número que circula en la documentación del proyecto —*13,349* ciclos de
costo por quitar el contador— y no sirve aquí: venía de la iteración 3, que tenía
78 características, ningún ciclo acumulado **y ninguna residualización**: otro
diseño, no este menos una columna. Así que la tabla de abajo se calcula acá, y lo
que diga es la respuesta.

La alternativa al contador de ciclos es una **línea base sana por motor**: la
media del vector de sensores residualizado en los tres primeros ciclos de ese
motor, restada del resto de su vida. Es causal (solo lee la vida temprana de ese
mismo motor) y es lo que una flota real registraría en la puesta en marcha.



## Siguiente
Continúa en `04_arquitectura_bilstm_oof.ipynb`.

