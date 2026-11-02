---
title: API — Modelo BiLSTM y pooling
course: DS02-RUL
block: B7 — Funciones y API
node: N23
status: en-curso
tags:
  - api
  - bilstm
  - pooling
  - keras
---

# API — Modelo BiLSTM y pooling

## Idea central

El campeón secuencial: BiLSTM(64)×2 con triple pooling (last/avg/max), registrado como capa propia para que el `.keras` sea portable. `src/ds02_rul/model.py` + `pooling.py`.

> Lee la ventana al derecho y al revés, y resume con tres miradas.

## ¿Qué problema resuelve?

Un `Lambda` de pooling ataría el artefacto a una versión de Python (marshal). `LastStepPooling` se registra con `get_config`, así el `.keras` carga en cualquier entorno.

## Las piezas del modelo mental

### `build_champion_bilstm(input_shape=(50, N_CHANNELS), dense_units=32, seed=42)` (`model.py:19`)
- **Firma:** `build_champion_bilstm(input_shape=(50, 19), dense_units: int = 32, seed: int = 42)`.
- **Qué hace:** construye el modelo Keras: Input → BatchNorm → BiLSTM(64, return_sequences) → Dropout 0.2 → BiLSTM(64) → Dropout → concat[LastStep, GlobalAvg, GlobalMax] → Dropout → Dense(32, relu) → Dense(1).
- **Retorno:** `tf.keras.Model` compilado (Huber, Adam 1e-3).
- **Llamado desde:** NB01 celda 20, NB03 celda 8.
- **Gotcha:** `N_CHANNELS=19` (18 + cyc_norm). Si cambias input_shape sin reentrenar, falla al cargar.

### `fit_bilstm(X_seq, y, fit_idx, val_idx, seed, epochs=22, batch_size=128)` (`pipeline.py:50`)
- **Firma:** `fit_bilstm(X_seq, y, fit_idx, val_idx, seed: int, epochs=22, batch_size=128)`.
- **Qué hace:** entrena el BiLSTM con EarlyStopping (patience 5) sobre `val_idx` (motor 16), ReduceLROnPlateau.
- **Retorno:** `(model, history)` con RMSE de validación.
- **Llamado desde:** NB01 celda 20, NB03 celda 8 (vía `run_seed`).
- **Gotcha:** solo el holdout (motor 16) valida; no usar test para early stopping.

### `LastStepPooling` (`pooling.py:16`)
- **Clase:** `layers.Layer` registrada.
- **Métodos:**
  - `call(inputs)`: devuelve `inputs[:, -1, :]` (último paso).
  - `compute_output_shape(input_shape)`: `(batch, features)`.
  - `get_config()`: serializable (permite guardar/cargar).
- **Llamado desde:** `build_champion_bilstm` (como capa).
- **Gotcha:** si usas `Lambda` en su lugar, el `.keras` no carga en otra versión de Python.

## El proceso completo, sin centrarnos en las cuentas

```mermaid
flowchart LR
    SEQ[50x19] --> BN[BatchNorm]
    BN --> B1[BiLSTM 64 x2]
    B1 --> P3[last+avg+max]
    P3 --> D[Dense 32]
    D --> RUL[RUL]
```

## Qué no debemos confundir

| Concepto | Qué significa | Qué no significa |
|---|---|---|
| Bidireccional | Lee pasado y futuro de la ventana | Ver el futuro real del motor |
| Triple pooling | Tres resúmenes complementarios | Tres modelos |
| LastStepPooling | Capa registrada portable | Lambda (frágil) |

## Conexión con los notebooks del repositorio

- `notebooks/ds02_ensemble/01_datos_y_bases.ipynb` celdas 20, 21.
- `notebooks/ds02_ensemble/03_evidencia_multisemilla_diagnostico.ipynb` celda 8.
- `src/ds02_rul/model.py:19` + `pooling.py:16`.

## Resumen para recordar

> Input(50,19) → BiLSTM×2 → concat[last,avg,max] → Dense(32) → Dense(1). RMSE semilla 42: 5.637 (single) / 6.218±0.541 (3 semillas).

## Autoevaluación

1. ¿Por qué triple pooling y no solo último paso?
2. ¿Por qué Huber y no MSE?
3. ¿Por qué LastStepPooling y no Lambda?

## Estado

- [ ] En curso
