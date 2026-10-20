"""Cierra la v3: vuelca la ejecución al notebook final y regenera COMPARACION_NASA.md."""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
RUN, OUT = ROOT / '_run_v3.ipynb', ROOT / 'notebook_nasa_fd001.ipynb'
RES = json.loads((ROOT / 'models' / 'v3_results.json').read_text(encoding='utf-8'))
POL = json.loads((ROOT / 'models' / 'alarm_policy.json').read_text(encoding='utf-8'))

fd1 = RES['FD001']['models']


def g(key):
    return fd1[key]


filas = []
for fd, d in RES.items():
    for k, v in d['models'].items():
        filas.append((fd, v['features'], v['modelo'],
                      v.get('rmse_oof_mean', v.get('rmse_val')), v['rmse_test'], v['mae_test'],
                      v['T'], v['alarma_T']['recall'], v['alarma_T']['precision'],
                      v['alarma_T']['alarmas'], v['alarma_15']['recall']))

tabla = '\n'.join(
    f'| {fd} | {fe} | {mo} | {oo:.2f} | {te:.2f} | {ma:.2f} | {T:.1f} | {rc:.1f} % ({al}) | {pr:.1f} % | {r15:.1f} % |'
    for fd, fe, mo, oo, te, ma, T, rc, pr, al, r15 in filas)

reglas = '\n'.join(
    f"| {k} | {v['alarmas']} | {v['recall']} % | {v['precision']} % | **{v['coste']}** |"
    for k, v in POL['reglas'].items())

CONCLUSION = f"""## 10. Conclusiones (v3 — OOF por motor, alarma por coste y transferencia)

Esta sección sustituye como titular a las conclusiones v2 (que siguen en las tablas de §7).
Todo lo de aquí está medido con **validación por motor** y umbral **calibrado por coste**.

### 10.1 Tabla completa (5 folds × 3 seeds en FD001, 3 folds × 1 seed en FD002/FD004)

| Dataset | Features | Modelo | RMSE val/OOF | RMSE test | MAE test | T* | Recall @T* | Prec @T* | Recall @15 fijo |
|---|---|---|---|---|---|---|---|---|---|
{tabla}

### 10.2 El número honesto: 7.34 no valía

El in-sample 7.34 de la v2 era una ilusión estadística: con OOF por motor el mismo modelo da
**{g('health/LightGBM')['rmse_oof_mean']:.2f}**, y en test {g('health/LightGBM')['rmse_test']:.2f}. La conclusión práctica es que **el OOF por ventana
es más pesimista que el test por motor** (mide todas las ventanas, incluidas las primeras de vida,
donde RUL está recortado a 125 y es intrínsecamente ambiguo).

### 10.3 Features de salud: ganan en OOF, casi nada en test

| | RMSE OOF | RMSE test |
|---|---|---|
| LightGBM sin features de salud | {g('raw/LightGBM')['rmse_oof_mean']:.2f} | {g('raw/LightGBM')['rmse_test']:.2f} |
| LightGBM con features de salud | **{g('health/LightGBM')['rmse_oof_mean']:.2f}** | {g('health/LightGBM')['rmse_test']:.2f} |
| Random Forest sin / con | {g('raw/RandomForest')['rmse_oof_mean']:.2f} / **{g('health/RandomForest')['rmse_oof_mean']:.2f}** | {g('raw/RandomForest')['rmse_test']:.2f} / **{g('health/RandomForest')['rmse_test']:.2f}** |

Las features causales (z-score por motor, deltas 10/30, std rolling, media 5) **sí mejoran la
predicción a lo largo de la vida** (OOF {g('raw/LightGBM')['rmse_oof_mean']:.2f} → {g('health/LightGBM')['rmse_oof_mean']:.2f}), pero en la última ventana el GBDT ya extraía casi todo
de los valores crudos. Es el resultado más incómodo del proyecto: **la métrica que mejoras no es
siempre la métrica que se reporta**.

### 10.4 El recall se gana con la política, no con el modelo

| Regla de alarma (test FD001) | Alarmas | Recall | Precisión | Coste (FN×20+FP) |
|---|---|---|---|---|
{reglas}

Pasar del umbral fijo 15 (recall {g('health/LightGBM')['alarma_15']['recall']:.1f} %) a la regla calibrada
`{POL['regla_elegida']}` sube el recall a **{POL['reglas'][POL['regla_elegida']]['recall']:.1f} %** con coste {POL['reglas'][POL['regla_elegida']]['coste']}. La regla de incertidumbre pura
(`q90 < 30`) **no dispara nunca**: el intervalo del 80 % mide {POL['cobertura_80']:.0f} % de cobertura pero ~65 ciclos de ancho.

### 10.5 LSTM vs GBDT bajo el mismo protocolo

| | FD001 (val/OOF → test) | FD002 |
|---|---|---|
| LightGBM + features de salud | {g('health/LightGBM')['rmse_oof_mean']:.2f} → **{g('health/LightGBM')['rmse_test']:.2f}** | {RES['FD002']['models']['health/LightGBM']['rmse_oof_mean']:.2f} → {RES['FD002']['models']['health/LightGBM']['rmse_test']:.2f} |
| LSTM 2×100-50 (holdout por motor) | {g('health/LSTM holdout')['rmse_val']:.2f} → {g('health/LSTM holdout')['rmse_test']:.2f} | {RES['FD002']['models']['health/LSTM holdout']['rmse_val']:.2f} → {RES['FD002']['models']['health/LSTM holdout']['rmse_test']:.2f} |

La RNN no gana en FD001 (ni con features de salud ni escaladas), y en FD002 empata con el GBDT
({RES['FD002']['models']['health/LSTM holdout']['rmse_test']:.2f} vs {RES['FD002']['models']['health/LightGBM']['rmse_test']:.2f}). Aviso de honestidad: la LSTM v3 entrena con 80 de los 100 motores
(holdout) y con Dropout 0.2, así que parte de su desventaja frente al 15.14 de la v2 es menos dato
y regularización, no solo el protocolo; aun así, **bajo validación honesta la RNN no justifica su
coste** (≈4 min por entrenamiento frente a 2 min de todo el GBDT).

### 10.6 Transferencia: el pipeline aguanta, el umbral no

| Dataset | Condiciones | Mejor RMSE test | T* |
|---|---|---|---|
| FD001 | 1 | {g('health/LightGBM')['rmse_test']:.2f} | {g('health/LightGBM')['T']:.1f} |
| FD002 | 6 | {RES['FD002']['models']['health/LinearRegression']['rmse_test']:.2f} (regresión lineal) | {RES['FD002']['models']['health/LinearRegression']['T']:.1f} |
| FD004 | 6 + 2 modos de fallo | {RES['FD004']['models']['health/LinearRegression']['rmse_test']:.2f} (regresión lineal) | {RES['FD004']['models']['health/LinearRegression']['T']:.1f} |

Dos hallazgos: (1) el error crece con las condiciones (13.5 → 15.4 → 17.8 con el mejor modelo),
y (2) **en multi-condición la regresión lineal gana al GBDT** — con 6 regímenes de operación y
normalización por motor, el problema se vuelve más lineal que interactivo. El T* óptimo pasa de 22
a 42.5 y 45: **el umbral hay que recalibrarlo por planta, no se hereda**.

### 10.7 Sistema (v3.0.0)

- `models/v3_bundle.joblib` — modelo + quantiles + lista de features + ventana + versión.
- `models/alarm_policy.json` — T_crit={POL['T_crit']}, T_warn={POL['T_warn']}, regla elegida,
  tabla de reglas con coste, cobertura real del intervalo.
- `scripts/predict.py` — `predict(historial)` devuelve RUL, q10/q90, alarma y coste esperado;
  `report(fd)` genera el informe batch; `drift_batch(fd)` calcula PSI de flota y `out_of_range()`
  el % de valores fuera del rango de train por motor.
- Drift medido en FD001: PSI máximo de flota 0.077, sin alerta (umbral 0.25).

### 10.8 Lo que sigue faltando para el 9-10

1. **Barra de error real**: LightGBM con esta configuración no usa bagging ni submuestreo, así que
   las 3 seeds dan desviación 0.00. La variabilidad hay que medirla cambiando folds e hiperparámetros.
2. **FD002/FD004 con 1 seed y 3 folds**: sirven para ver que transfiere, no para decidir.
3. **Umbral con datos de planta**: el 20:1 es supuesto; con un ratio distinto, T* cambia.
4. **Normalización por régimen de operación** en FD002/FD004 antes de volver a probar GBDT.
5. **Serving**: falta despliegue, monitorización en producción y reentrenamiento periódico.
"""

MD = f"""# Comparación NASA CMAPSS — resultados medidos (v3)

Todo sale de `notebook_nasa_fd001.ipynb` ejecutado de punta a punta, de `models/v3_results.json`,
`models/alarm_policy.json` y de los scripts `scripts/v3_*.py`. Métricas crudas, sin editar.

## Protocolo v3

- **Validación**: `GroupKFold` por motor (5 folds × 3 seeds en FD001; 3 folds × 1 seed en FD002/FD004).
  La RNN usa holdout por motor (20 %) porque 5 folds × LSTM no es viable.
- **Test**: última ventana de cada motor contra `RUL_FDxxx.txt`, clip 125.
- **Alarma**: umbral calibrado por coste (FN × 20 + FP × 1) sobre OOF de train, jamás en test.
- **Features de salud**: causales (solo pasado): z-score por motor, deltas 10/30, std rolling 15,
  media 5 sobre 7 sensores clave. Escaladas adicionalmente solo para la RNN.

## Tabla completa

| Dataset | Features | Modelo | RMSE val/OOF | RMSE test | MAE test | T* | Recall @T* | Prec @T* | Recall @15 fijo |
|---|---|---|---|---|---|---|---|---|---|
{tabla}

## Reglas de alarma comparadas (FD001)

| Regla | Alarmas | Recall | Precisión | Coste |
|---|---|---|---|---|
{reglas}

Regla elegida por coste: **{POL['regla_elegida']}**. Cobertura del intervalo 80 %: {POL['cobertura_80']:.1f} %.

## Qué cambió respecto a la v2

| Aspecto | v2 | v3 |
|---|---|---|
| Métrica de train | in-sample (7.34) | OOF por motor ({g('health/LightGBM')['rmse_oof_mean']:.2f}) |
| Umbral | fijo 15/30 | calibrado por coste (T*={POL['T_crit']}) |
| Recall ROJO (LightGBM) | 78 % @15 | {g('health/LightGBM')['alarma_T']['recall']:.1f} % @T* / {POL['reglas'][POL['regla_elegida']]['recall']:.1f} % con {POL['regla_elegida']} |
| Features | 24 crudas | 49 de salud (evaluadas contra las crudas) |
| Incertidumbre | — | quantile q10/q90 (cobertura {POL['cobertura_80']:.1f} %) |
| Datasets | FD001 | FD001 + FD002 + FD004 |
| Sistema | — | bundle + política + inferencia + PSI de flota |

## Conclusiones

1. **El 7.34 in-sample no valía**: con validación por motor el mismo modelo da
   {g('health/LightGBM')['rmse_oof_mean']:.2f} (OOF) y {g('health/LightGBM')['rmse_test']:.2f} en test.
2. **Las features de salud mejoran el OOF** ({g('raw/LightGBM')['rmse_oof_mean']:.2f} → {g('health/LightGBM')['rmse_oof_mean']:.2f}) **pero no la última ventana**
   ({g('raw/LightGBM')['rmse_test']:.2f} → {g('health/LightGBM')['rmse_test']:.2f}): miden poblaciones distintas y hay que reportar ambas.
3. **El recall se gana con la política de alarma**: de {g('health/LightGBM')['alarma_15']['recall']:.1f} % (umbral fijo 15) a
   {POL['reglas'][POL['regla_elegida']]['recall']:.1f} % (regla calibrada), manteniendo el coste bajo.
4. **La RNN no gana bajo protocolo honesto** (FD001 {g('health/LSTM holdout')['rmse_test']:.2f}; FD002 {RES['FD002']['models']['health/LSTM holdout']['rmse_test']:.2f} vs {RES['FD002']['models']['health/LightGBM']['rmse_test']:.2f} del GBDT).
5. **En multi-condición gana lo simple**: regresión lineal {RES['FD002']['models']['health/LinearRegression']['rmse_test']:.2f} (FD002) y {RES['FD004']['models']['health/LinearRegression']['rmse_test']:.2f} (FD004).
6. **El umbral no se hereda**: T* = {g('health/LightGBM')['T']:.1f} / {RES['FD002']['models']['health/LinearRegression']['T']:.1f} / {RES['FD004']['models']['health/LinearRegression']['T']:.1f} según dataset.

## Artefactos

- `models/v3_results.json`, `models/alarm_policy.json`, `models/v3_bundle.joblib`,
  `models/psi_reference.json`, `models/v3_quantile_FD001.csv`, `models/informe_batch.csv`
- `models/lstm_FD001_v3_holdout.h5`, `models/lstm_FD002_v3_holdout.h5`
- `scripts/v3_core.py`, `v3_run.py`, `v3_lstm.py`, `v3_finalize.py`, `predict.py`
"""


def main():
    nb = json.loads(RUN.read_text(encoding='utf-8'))
    assert nb['cells'][-1]['cell_type'] == 'markdown'
    nb['cells'][-1]['source'] = CONCLUSION
    OUT.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
    (ROOT / 'COMPARACION_NASA.md').write_text(MD, encoding='utf-8')
    print('notebook final:', OUT, '| celdas:', len(nb['cells']))
    print('COMPARACION_NASA.md regenerado')


if __name__ == '__main__':
    main()
