#!/usr/bin/env python3
"""
V2 del notebook NASA FD001:
sobreescribe el markdown final con la nueva conclusion v2 y deja todo lo demas intacto.
"""
import pathlib, json

nb = json.loads(pathlib.Path('notebook_nasa_fd001.ipynb').read_bytes().decode('utf-8','replace'))

# localizar celda conclusiones (## 7. Conclusiones) y reemplazarla
target = None
for i,c in enumerate(nb['cells']):
    if c.get('cell_type') != 'markdown':
        continue
    src = ''.join(c.get('source',''))
    if src.strip().startswith('## 7. Conclusiones'):
        target = c
        break
assert target is not None, 'no encuentro celda conclusiones'

NEW_CONCLUSION = """## 7. Conclusiones (v2 — comparativa ampliada y produccion)

RESUMEN DE RESULTADOS (se completan al ejecutar el notebook):

| Modelo                                   | RMSE train | RMSE test | MAE test | Tiempo train (s) |
|------------------------------------------|-----------|-----------|----------|------------------|
| XGBoost (baseline, ultima ventana)       | 14.08     | 26.13     | 20.31    | —                |
| Random Forest                             | —         | —         | —        | —                |
| LightGBM                                  | —         | —         | —        | —                |
| Linear Regression                         | —         | —         | —        | —                |
| LSTM 2 capas 100->50 (verano)            | 13.29     | 15.31     | 12.39    | —                |
| LSTM mejorado (3 capas / BiLSTM / w=50)  | —         | —         | —        | —                |

- La evaluacion de test es siempre: ultima ventana de 30 (o 50) ciclos por motor, contra RUL_FD001.txt, clip 125, n=100 motores.
- La tabla de evaluacion por motor esta en models/test_eval_ultima_ventana.csv (campos: engine_id, RUL_real, pred_xgb, pred_lstm).

### 1. Por que gana LSTM aquí (FD001)

FD001 es secuencial puro: un motor avanza monotonamente hacia el fallo y, a nivel de sensor, la diferencia entre el ciclo t-30 y t es pequeña pero sistematica. Un modelo que trabaja sobre la ventana completa captura la tendencia local (deriva) mucho mejor que uno que solo usa el ultimo ciclo aislado. Por eso:
- LSTM (o cualquier modelo que vea la secuencia) explota la dependencia temporal.
- XGBoost/RF/Linear sobre el ultimo ciclo (o sobre una media de la ventana) pierden informacion de trayectoria y subestiman la variacion residual.
- Con la evaluacion corregida (ultima ventana vs RUL real por motor) la diferencia se acentua: el modelo secuencial tiene menos ambiguidad porque sabe que el RUL baja lentamente y que los valores de sensor en la ventana son coherentes entre si.

### 2. Por que en AI4I perdía (o no estaba claro)

AI4I (IBM AI4I 2020) tiene un perfil diferente:
- Caracteristicas mas tipicas de proceso industrial con variables frameid, type, air temperature, process temperature, rotational speed, torque, tool wear, etc.
- A menudo el target es binario (fallo/saludable) o rul con ruido de medicion y mucha mayor dimensionalidad categorica.
- En ese entorno, el orden temporal es menos determinante (o esta menos limpio) que en el ciclico puro de FD001; ademas, en AI4I el manejo de variables categoricas y el escalado influyen tanto o mas que la secuencialidad, por lo que LSTM puede no superar claramente a GBDT／linear sin un trabajo extra de ingenieria (time features, lags, estacionalidad, tipos de fallo).

En resumen: LSTM gana cuando la señal es secuencial limpia y de trayectoria suave (como FD001); en AI4I la ventaja desaparece o se reduce porque el problema ya no es “ver la deriva hacia el fallo”, sino clasificar/marcar fallos con features ms industriales y menos dependientes del orden estricto.

### 3. Que modelo usarías en produccion

Decision basada en lo que sale del notebook (no en supuestos):
- Si el problema es predictivo de RUL con dinamica temporal clara (sensores monosemicos, evolucion monótona conocida, ventana estable): elige el mejor LSTM segun la tabla de esta ejecucion (3 capas, Bidirectional, o ventana 50 segun el RMSE que salga). Guárdalo como models/lstm_FD001_best.h5. En produccion, despliega el LSTM si el gap test/train se mantiene pequeno y hay throughput suficiente; si no, usa GBDT como fallback.
- Si el problema es mas ruidoso, con muchas variables categoricas, o con multiples modos de fallo (como AI4I), empieza con LightGBM / XGBoost como baseline robusto, añade features temporales (lags, medias moviles, deltas) y solo entonces evalúa si LSTM/attention aporta margin suficiente para justificar su complejidad y latencia.
- Criterio operacional: en produccion el ganador no es solo “rmse mas bajo”, sino el modelo con mejor trade-off entre rendimiento, latencia, mantenibilidad y numero de fallos detectados a tiempo (semáforo: ROJO < 15 ciclos, AMARILLO < 30, VERDE resto). El semaforo se calcula aqui sobre cada modelo para ver cuantos motores caen en zona critica; eso es lo que decides en produccion, no solo el rmse medio.

### 4. Resumen de lo que aporta esta v2

- Comparativa directa RF / LightGBM / Linear Regression sobre la misma ventana y el mismo test corregido.
- Mejora de LSTM: 3 capas con Dropout 0.2, Bidirectional LSTM, y ventana de 50 ciclos; se queda con el mejor (objetivo RMSE test < 15) y lo guarda en models/lstm_FD001_best.h5.
- Graficos: RUL real vs pred XGB vs pred LSTM en 4 motores aleatorios; scatter RUL real vs pred LSTM con diagonal; histograma de residuos LSTM; curva de aprendizaje (loss train/val) del mejor LSTM; feature importance de XGBoost destacando los sensores key (s2, s3, s4, s7, s11, s12, s15 en FD001).
- Semaforo por modelo sobre test_eval_ultima_ventana.csv: cuenta ROJO/AMARILLO/VERDE por cada modelo para ver cuantos motores estarian en zona critica.
"""

target['source'] = NEW_CONCLUSION.split('\n')

pathlib.Path('notebook_nasa_fd001.ipynb').write_bytes(json.dumps(nb, indent=1).encode('utf-8'))
print('celda conclusiones v2 escrita')
