"""Serializable last-timestep pooling.

Replaces the bare `Lambda(lambda z: z[:, -1, :])` used by the original notebook.
Keras serialises a bare lambda as marshalled Python bytecode, and `marshal`'s
code-object format changes between Python minor versions, so an artifact built
that way can only be loaded by the interpreter that wrote it. A Layer subclass
with an explicit `get_config` serialises by value and is portable.
"""
from __future__ import annotations

import keras
from keras import layers


@keras.saving.register_keras_serializable(package="ds02_rul")
class LastStepPooling(layers.Layer):
    """Return the last timestep of a (batch, time, features) tensor."""

    def call(self, inputs):
        """Devuelve la representación del último paso temporal."""
        return inputs[:, -1, :]

    def compute_output_shape(self, input_shape):
        """Forma `(batch, features)` tras descartar la dimensión temporal."""
        return (input_shape[0], input_shape[2])

    def get_config(self):
        """Configuración serializable de la capa sin parámetros."""
        return super().get_config()
