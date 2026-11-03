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
    

**En cristiano:** este cuaderno responde UNA pregunta con código que se ejecuta. Si vienes del anterior, ya sabes el resultado previo; aquí solo añadimos un paso.



```python
# 2. Alias estilo clase (solo lectura: no entrenan, no cambian numeros).
#    evaluar_clase/mostrar_clase ya vienen de viz (ver src/ds02_rul/viz.py).
print("[FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)")

```

    [FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)
    

# 03 · Ablación cyc_norm — ¿el reloj ayuda o es trampa?

Parte 2 de 3. Mismo código que la sección 6 del original.

**Requisito:** haber corrido el `01` (usa su `artifacts/`). No re-entrena la semilla 42.



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

    WARNING:tensorflow:TensorFlow GPU support is not available on native Windows for TensorFlow >= 2.11. Even if CUDA/cuDNN are installed, GPU will not be used. Please use WSL2 or the TensorFlow-DirectML plugin.
    

    [LOAD NB1 OK] dev (17450, 50, 19) | test (6196, 50, 19) | bilstm recargado
    


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
from ds02_rul.viz import evaluar_clase, mostrar_clase

```

    cwd: C:\Users\mikel\Desktop\Pruebas\nasa
    python  : 3.12.10
    keras   : 3.15.1
    lightgbm: 4.7.0
    sklearn : 1.9.1
    ds02_rul: 4.1.0 -> C:\Users\mikel\Desktop\Pruebas\nasa\src\ds02_rul
    

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
# 2. Alias estilo clase (solo lectura: no entrenan, no cambian numeros).
#    evaluar_clase/mostrar_clase ya vienen de viz (ver src/ds02_rul/viz.py).
print("[FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)")

```

    [FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)
    


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
    

## 6 · Ablación de `cyc_norm` — medida, no afirmada

La revisión anterior citaba *13,349* como el costo de quitar el contador de
ciclos. Ese número venía de la iteración 3, que tenía 78 características, ningún
ciclo acumulado **y ninguna residualización**: otro diseño, no este menos una
columna. Así que la tabla de abajo se calcula acá, y lo que diga es la respuesta.

La alternativa al contador de ciclos es una **línea base sana por motor**: la
media del vector de sensores residualizado en los tres primeros ciclos de ese
motor, restada del resto de su vida. Es causal (solo lee la vida temprana de ese
mismo motor) y es lo que una flota real registraría en la puesta en marcha.



## Siguiente
Continúa en `04_arquitectura_bilstm_oof.ipynb`.

