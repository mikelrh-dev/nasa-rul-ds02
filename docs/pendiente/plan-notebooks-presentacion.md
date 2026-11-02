# Pendiente: notebooks de track_clase/ no explican el modelo entero

## Problema

Los notebooks de `track_clase/` (02-05) no explican el modelo entero: muestran
resultados precomputados (tablas CSV + 1 figura) pero no el proceso (código
ejecutado, outputs intermedios, diagnósticos). Los notebooks de
`ds02_ensemble/` (01-03) sí muestran el proceso completo.

### Notas de presentabilidad (subagente, 2026-11-02)

| Notebook | Nota | Motivo |
|---|---|---|
| 01_eda | 9 | EDA completo con código + outputs intermedios, 5 figuras, markdown rico |
| 02_modelos_A | 6 | Solo lee comparativa.csv (proceso oculto en scripts), 1 figura, markdown escaso |
| 03_modelos_B | 7 | Reentrena MLP en vivo + importancia/SHAP, pero mayor parte es lectura de CSV |
| 04_lgbm_adaptada | 7 | Markdown excelente, pero solo 2 celdas de código |
| 05_ensemble_adaptado | 8 | Narrativa muy buena, multiseed en vivo, veredicto honesto; salida ruidosa (TF) |

### Debilidades comunes
- Sin kernelspec (Jupyter pedirá elegir kernel al "Run All")
- Dependencia de rutas relativas `../`
- 05 incluye warnings de TensorFlow en la salida
- 03 reentrena un MLP completo (costoso)
- 05 tiene una celda markdown antes del título principal
- 02 es el más débil (6): solo tablas y una figura

## Lo que ds02_ensemble/ tiene y track_clase/ no

- Narrativa de clase integrada (glosario, "Cómo leerlo", regla de empate, TIPs)
- Ablación medida de cyc_norm y alternativa de línea base por motor
- Calibración honesta de beta por OOF agrupado + diagnóstico del protocolo degenerado
- Banda conformal asimétrica por tramo y análisis de cobertura/trade-off
- Evidencia multisemilla (media ± desviación) y estabilidad entre semillas
- Diagnósticos extensos (real vs predicho, residuos, error por tramo/motor, curvas)
- Puente de artefactos entre notebooks y verificación de recarga desde disco

## Lo que track_clase/ tiene y ds02_ensemble/ no

- Inyección/imputación MAR, fase_vuelo
- 5 clásicos + GridSearch, MLP base+3 experimentos
- LGBM adaptada, ensemble adaptado (bundle C)
- SHAP TreeExplainer
- Tabla final entre familias
- Robustez B bajo dropout
- Tests y app/reglas/n8n

## Opciones

### Opción A: Mejorar notebooks de track_clase/ para que sean autosuficientes
1. 02_modelos_A: añadir código de entrenamiento (no solo lectura de CSV), mostrar GridSearchCV en vivo, añadir 2-3 figuras de diagnóstico
2. 03_modelos_B: reducir reentrenamiento del MLP (usar cache), añadir más figuras (residuos, error por tramo)
3. 04_lgbm_adaptada: añadir código de entrenamiento en vivo (no solo 2 celdas), mostrar importancia, añadir diagnóstico
4. 05_ensemble_adaptado: limpiar warnings de TF, añadir gráficas de diagnóstico (real vs predicho, residuos, por motor), añadir kernelspec
- Esfuerzo: 3-4 horas | Riesgo: 3/10

### Opción B: Usar notebooks de ds02_ensemble/ para la defensa + track_clase/ como complemento
- Pros: ya están completos y presentables (8.5, 8.0, 9.0)
- Contras: no cubren la parte de clase (nulos, clásicos, MLP, LGBM adaptada, ensemble adaptado, SHAP, robustez)
- Requiere explicar en la defensa por qué hay dos conjuntos de notebooks

### Opción C: Combinar ambos
- Usar 01_eda de track_clase/ (9/10) para la parte de clase
- Usar 01-03 de ds02_ensemble/ para la parte del modelo (BiLSTM, LightGBM, conformal)
- Usar 04_lgbm_adaptada y 05_ensemble_adaptado de track_clase/ para la parte de robustez
- Pros: aprovecha lo mejor de ambos
- Contras: requiere explicar la relación entre los dos conjuntos

## Recomendación del subagente

Opción A con mejoras mínimas (bajo riesgo, alto impacto):
1. Unificar kernelspec en 02-05
2. Limpiar warnings de TF en 05
3. Añadir una figura más de diagnóstico en 02/04
4. Mover la celda markdown que está antes del título en 05

## Archivos de referencia

- track_clase/ notebooks: `notebooks/01_eda.ipynb` ... `notebooks/05_ensemble_adaptado.ipynb`
- ds02_ensemble notebooks: `notebooks/ds02_ensemble/01_datos_y_bases.ipynb` ... `03_evidencia_multisemilla_diagnostico.ipynb`
- Scripts de track_clase: `track_clase/train_clasicos.py`, `train_mlp.py`, `train_lgbm_adaptada.py`, `train_ensemble_adaptado.py`
- Funciones de inferencia: `app/ui_inference.py` (example_window, window_ending_at, demo_presets)
- Datos: `data/processed/` (parquet, ignorado en git, regenerable)
- Resultados: `resultados/` (CSV, PNG, ignorado en git, regenerable)

## Verificación post-mejora

Tras cada mejora, ejecutar:
```bash
.venv/Scripts/python -m nbconvert --execute notebooks/0X_*.ipynb --to notebook --inplace
.venv/Scripts/python -m pytest tests -q
```
