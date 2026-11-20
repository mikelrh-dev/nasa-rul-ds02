"""Pooling serializable del último paso temporal.

Sustituye al `Lambda(lambda z: z[:, -1, :])` del notebook original. Keras
serializa un lambda suelto como bytecode de Python y el formato de `marshal`
cambia entre versiones menores, así que un artefacto creado así solo se puede
cargar con el intérprete que lo escribió. Una subclase de Layer con `get_config`
explícito se serializa por valor y es portable.
"""
from __future__ import annotations

import keras
from keras import layers


@keras.saving.register_keras_serializable(package="ds02_rul")
class LastStepPooling(layers.Layer):
    """Devuelve el último paso temporal de un tensor (lote, tiempo, rasgos)."""

    def call(self, inputs):
        """Devuelve la representación del último paso temporal."""
        return inputs[:, -1, :]

    def compute_output_shape(self, input_shape):
        """Forma `(batch, features)` tras descartar la dimensión temporal."""
        return (input_shape[0], input_shape[2])

    def get_config(self):
        """Configuración serializable de la capa sin parámetros."""
        return super().get_config()
