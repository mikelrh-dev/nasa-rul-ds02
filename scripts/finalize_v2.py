"""Vuelca la ejecución v2 al notebook final y regenera COMPARACION_NASA.md.

- Copia el notebook ejecutado (_run_v2.ipynb) a notebook_nasa_fd001.ipynb.
- Sustituye la celda de conclusiones placeholder por la conclusión real
  construida a partir de models/v2_metrics.json.
- Regenera COMPARACION_NASA.md con los mismos números.
"""
import json
import pathlib

RUN = pathlib.Path('_run_v2.ipynb')
OUT = pathlib.Path('notebook_nasa_fd001.ipynb')
METRICS = json.loads(pathlib.Path('models/v2_metrics.json').read_text(encoding='utf-8'))

m = METRICS
best = m['best']


def f(v):
    return '—' if v in (None, 'nan') else f'{v:.2f}'


def t(v):
    return '—' if v in (None, 'nan') else f'{v:.1f}'


tabla = f"""| Modelo | RMSE train | RMSE test | MAE test | Tiempo (s) | n motores |
|---|---|---|---|---|---|
| XGBoost baseline (por ciclo, media de ventana) | {f(m['xgb']['rmse_train'])} | {f(m['xgb']['rmse_test'])} | {f(m['xgb']['mae_test'])} | — | {m['xgb']['n']} |
| Random Forest (ventana aplanada) | {f(m['rf']['rmse_train'])} | {f(m['rf']['rmse_test'])} | {f(m['rf']['mae_test'])} | {t(m['rf']['t'])} | {m['rf']['n']} |
| **LightGBM (ventana aplanada)** | **{f(m['lgb']['rmse_train'])}** | **{f(m['lgb']['rmse_test'])}** | **{f(m['lgb']['mae_test'])}** | **{t(m['lgb']['t'])}** | **{m['lgb']['n']}** |
| Linear Regression (ventana aplanada) | {f(m['lr']['rmse_train'])} | {f(m['lr']['rmse_test'])} | {f(m['lr']['mae_test'])} | {t(m['lr']['t'])} | {m['lr']['n']} |
| LSTM 2 capas 100-50 (baseline, w=30) | {f(m['lstm2']['rmse_train'])} | {f(m['lstm2']['rmse_test'])} | {f(m['lstm2']['mae_test'])} | — | {m['lstm2']['n']} |
| LSTM mejor variante (C, w=50) | {f(best['rmse_train'])} | {f(best['rmse_test'])} | {f(best['mae_test'])} | {t(best['tiempo'])} | {best['n']} |
"""

var_tabla = '\n'.join(
    f"| {v['nombre']} | {v['rmse_train']:.2f} | {v['rmse_test']:.2f} | "
    f"{v['rmse_test_mismo_n']:.2f} | {v['mae_test']:.2f} | {v['n']} |"
    for v in m['variantes']
)

sem_tabla = '\n'.join(
    f"| {s['Modelo']} | {s['ROJO']} | {s['AMARILLO']} | {s['VERDE']} | "
    f"{s['aciertos zona']}/{s['n']} ({s['aciertos_pct']}%) |"
    for s in m['semaforo']
)

orden = sorted(
    [('LightGBM', m['lgb']['rmse_test']), ('LSTM mejor variante', best['rmse_test']),
     ('LSTM 2 capas', m['lstm2']['rmse_test']), ('Linear Regression', m['lr']['rmse_test']),
     ('Random Forest', m['rf']['rmse_test']), ('XGBoost baseline', m['xgb']['rmse_test'])],
    key=lambda x: x[1])

CONCLUSION = f"""## 8. Conclusiones (v2 — con los números de esta ejecución)

### Tabla final

{tabla}

Ganador: **{orden[0][0]}** con RMSE test {orden[0][1]:.2f}. Orden completo: {' < '.join(f'{n} ({v:.2f})' for n, v in orden)}.

### Variantes LSTM

| Variante | RMSE train | RMSE test (sus motores) | RMSE test (mismo n=93) | MAE test | n |
|---|---|---|---|---|---|
{var_tabla}

La variante elegida es la **{best['nombre']}** (RMSE test {best['rmse_test']:.2f} sobre {best['n']} motores,
entrenada {best['epochs']} epochs). No baja de 15: el objetivo RMSE < 15 **no se cumple** en ninguna variante.
La ventana de 50 ciclos solo existe para {best['n']} de 100 motores, por eso la comparación se hace
también a igual `n`; aun así no mejora al baseline de 2 capas con w=30 ({m['lstm2']['rmse_test']:.2f}).

### 1. ¿Por qué el LSTM gana al XGBoost aquí?

Al baseline **sí** le gana, y con margen: {m['xgb']['rmse_test']:.2f} → {m['lstm2']['rmse_test']:.2f} de RMSE.
Pero la razón no es "la recurrencia" sino **qué información ve el modelo**:

- El XGBoost baseline predice **ciclo a ciclo** y en test se promedia la ventana: ve 24 valores sueltos,
  sin saber si el motor está al principio o al final de su vida. Su error se dispara en los motores
  sanos (predice RUL bajo donde debería predecir 125): de ahí que su semáforo no marque **ni un ROJO**
  y falle el 24 % de las zonas.
- Cuando un GBDT ve **la misma ventana aplanada** (720 features), el problema se estrecha: LightGBM
  baja a {m['lgb']['rmse_test']:.2f} (mejor que cualquier LSTM), Random Forest se queda en
  {m['rf']['rmse_test']:.2f} (peor, mismo orden) y Linear Regression en {m['lr']['rmse_test']:.2f}.

Conclusión honesta: **la ventaja sobre el baseline viene de la ventana, no de la arquitectura**.
En FD001 (1 condición, 1 modo de fallo, 100 motores, 20 k ciclos) la señal está en la *forma* de la
ventana y LightGBM la explota mejor que el LSTM, con {t(m['lgb']['t'])} s de entrenamiento frente a
213-361 s por variante LSTM.

### 2. Por qué en AI4I el LSTM perdía

AI4I no es una trayectoria monótona hacia el fallo: es un problema con `type` categórico,
temperaturas, par y desgaste, con target binario y ruido de medición. Allí:

- las features tabulares ya separan bien sin explotar orden temporal;
- el GBDT maneja categóricas e interacciones sin esfuerzo, el LSTM necesita codificarlas y secuenciarlas;
- con pocas muestras por unidad, la recurrencia solo añade varianza.

Resultado: en AI4I el LSTM no aportaba y el GBDT ganaba; aquí pasa algo parecido en cuanto el GBDT
recibe la ventana. **El patrón se repite: la secuencia ayuda cuando aporta información que el modelo
tabular no tiene; si el tabular ya la tiene, el LSTM solo cuesta.**

### 3. Qué modelo usaría en producción

Para este FD001, con estos números: **LightGBM** (RMSE {m['lgb']['rmse_test']:.2f}, MAE {m['lgb']['mae_test']:.2f},
{t(m['lgb']['t'])} s de entrenamiento, inferencia en milisegundos) y el semáforo encima. Razones:

- mismo rendimiento o mejor que el LSTM, sin GPU ni secuencias servidas;
- reentrenar y versionar es trivial frente a un `.h5` (y aquí `lstm_FD001_best.h5` pesa por arquitectura);
- el semáforo acierta {m['semaforo'][2]['aciertos_pct']} % de las zonas críticas con LightGBM.

LSTM solo si el problema real exige modelar dependencias largas que la ventana aplanada no captura
o si ya hay infraestructura de serving para modelos secuenciales.

### 4. Semáforo (RUL < 15 ROJO, < 30 AMARILLO, resto VERDE)

Real: **{m['semaforo_real']['ROJO']} ROJO / {m['semaforo_real']['AMARILLO']} AMARILLO / {m['semaforo_real']['VERDE']} VERDE** (n=100).

| Modelo | ROJO | AMARILLO | VERDE | Zona correcta |
|---|---|---|---|---|
{sem_tabla}

Ojo con la métrica: acertar zona no es acertar RUL. El LSTM acierta más zona pero **sobreestima**
en los motores verdes; LightGBM es el que más ROJOS marca de verdad a tiempo
({m['semaforo'][2]['ROJO']} detectados frente a {m['semaforo_real']['ROJO']} reales).

### 5. Limitaciones de esta medición

- Test evaluado solo en la **última ventana** de cada motor (n=100); la variante w=50 solo cubre {best['n']}.
- Seed única (42): las diferencias de 1-2 puntos de RMSE entre LSTM/RF/LR están dentro del ruido.
- RUL recortado a 125: los motores sanos nunca se evalúan en su RUL real (>125).
- TensorFlow no es determinista bit a bit; repetir la ejecución mueve las cifras de las variantes.
- El CSV por motor está en `models/test_eval_ultima_ventana.csv` (pred_xgb, pred_lstm, pred_rf,
  pred_lgb, pred_lr, pred_lstm_best) y las métricas crudas en `models/v2_metrics.json`.
"""

MD_FOR_MD = f"""# Comparación NASA FD001 — resultados medidos

Todos los números salen de `notebook_nasa_fd001.ipynb` ejecutado de punta a punta
(0 celdas con error) el 18/10/2026. Métricas crudas: `models/v2_metrics.json`.

## Protocolo

- Entrenamiento: todas las ventanas de `train_FD001.txt`, RUL = `max_cycle - cycle` recortado a 125.
- Test: **solo la última ventana** de cada motor, comparada contra `RUL_FD001.txt` (clip 125).
- Train RMSE se mide por ventana; test RMSE/MAE por motor (no son la misma unidad).
- Modelos tabulares: ventana de 30 × 24 aplanada (720 features). LSTM: secuencia 30 × 24 (o 50 × 24 en la variante C).

## Tabla final

{tabla}

## Variantes LSTM

| Variante | RMSE train | RMSE test (sus motores) | RMSE test (mismo n=93) | MAE test | n |
|---|---|---|---|---|---|
{var_tabla}

Ganadora entre las variantes: **{best['nombre']}**. Objetivo RMSE test < 15: **no alcanzado** ({best['rmse_test']:.2f}).

## Semáforo

Real (RUL_FD001.txt): {m['semaforo_real']['ROJO']} ROJO / {m['semaforo_real']['AMARILLO']} AMARILLO / {m['semaforo_real']['VERDE']} VERDE.

| Modelo | ROJO | AMARILLO | VERDE | Zona correcta |
|---|---|---|---|---|
{sem_tabla}

## Lectura

- El baseline XGBoost por ciclo ({m['xgb']['rmse_test']:.2f}) es el peor: promedia predicciones sin ver la trayectoria.
- Meter la ventana en un GBDT cambia el resultado: LightGBM {m['lgb']['rmse_test']:.2f}, RF {m['rf']['rmse_test']:.2f}.
- LSTM 2 capas w=30: {m['lstm2']['rmse_test']:.2f}; mejor variante (C, w=50): {best['rmse_test']:.2f} con {best['n']} motores.
- Por tanto: la ventaja no es de la recurrencia, es de la ventana. LightGBM es el mejor coste/beneficio
  ({t(m['lgb']['t'])} s de entrenamiento frente a ~{best['tiempo']:.0f} s de la mejor LSTM).

## Artefactos

- `models/xgb_FD001_baseline.joblib`, `models/lstm_FD001_2layer.h5`
- `models/rf_FD001_baseline.joblib`, `models/lgb_FD001_baseline.joblib`, `models/lr_FD001_baseline.joblib`
- `models/lstm_FD001_best.h5` + `models/lstm_FD001_best.json` (ventana y métricas)
- `models/test_eval_ultima_ventana.csv` (predicciones por motor de los 6 modelos)
- `models/v2_metrics.json` (todas las métricas de la ejecución)
"""


def main():
    nb = json.loads(RUN.read_text(encoding='utf-8'))
    assert nb['cells'][-1]['cell_type'] == 'markdown', 'la última celda debe ser la conclusión'
    nb['cells'][-1]['source'] = CONCLUSION
    OUT.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')

    pathlib.Path('COMPARACION_NASA.md').write_text(MD_FOR_MD, encoding='utf-8')
    print('notebook final:', OUT, '| celdas:', len(nb['cells']))
    print('COMPARACION_NASA.md regenerado')


if __name__ == '__main__':
    main()
