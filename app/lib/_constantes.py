"""Constantes puras compartidas por `app/` (sin Streamlit ni cargador de datos).

Los umbrales de decisión (ADR-008) eran literales duplicados y ahora vivían en
`ui_data_loader`, que arrastra Streamlit. Este módulo los define una sola vez
para que la lógica de `app/lib/` pueda leerlos sin importar el cargador.
"""
from __future__ import annotations

# ADR-008: apto si L_inf >= 30; inspección si 25 <= L_inf < 30; hangar si
# L_inf < 25. Son un acuerdo de negocio, no un hiperparámetro del modelo.
DEFAULT_AIRWORTHY = 30.0
DEFAULT_AOG = 25.0
