# src/ds02_rul/model.py — copia literal para NotebookLM

> Copia literal de `src/ds02_rul/model.py`. No resumido, no adaptado. Para pegar en NotebookLM.

```python
"""The sequential champion: 2-layer BiLSTM with triple temporal pooling.

The architecture is weight-order-compatible with the graph trained in the
original notebook (2 x Bidirectional(LSTM(64)) -> last step + average + max ->
Dense(32) -> Dense(1)); the only change is that the last-step slice is a
registered Layer instead of a bare `Lambda`, so the model serialises by value.
"""
from __future__ import annotations

import keras
import tensorflow as tf
from keras import layers, models

from .pooling import LastStepPooling

N_CHANNELS = 19  # 18 scaled signals + normalised cycle


def build_champion_bilstm(input_shape=(50, N_CHANNELS), dense_units: int = 32, seed: int = 42):
    """Compile the champion BiLSTM.

    `input_shape` is `(window, channels)`; with the cycle channel included the
    second dimension is 19, and dropping it yields 18.
    """
    tf.keras.backend.clear_session()
    tf.random.set_seed(seed)

    inp = layers.Input(shape=input_shape, name="input_window")
    x = layers.BatchNormalization(name="batch_norm_input")(inp)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=True), name="bilstm_layer_1")(x)
    x = layers.Dropout(0.2, name="dropout_1")(x)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=True), name="bilstm_layer_2")(x)
    x = layers.Dropout(0.2, name="dropout_2")(x)
    pooled = layers.Concatenate(name="temporal_pooling")(
        [
            LastStepPooling(name="last_step")(x),
            layers.GlobalAveragePooling1D(name="global_avg_pool")(x),
            layers.GlobalMaxPooling1D(name="global_max_pool")(x),
        ]
    )
    x = layers.Dropout(0.2, name="dropout_pooled")(pooled)
    x = layers.Dense(dense_units, activation="relu", name="dense_proj")(x)
    out = layers.Dense(1, name="rul_output")(x)

    model = models.Model(inp, out, name="BiLSTM_TriplePooling_RUL")
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss=keras.losses.Huber(delta=10.0),
        metrics=["mae"],
    )
    return model

```
