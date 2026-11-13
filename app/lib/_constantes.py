"""Constantes puras compartidas por `app/` (sin Streamlit ni cargador de datos).

Los umbrales de decisión (ADR-013) eran literales duplicados y ahora vivían en
`ui_data_loader`, que arrastra Streamlit. Este módulo los define una sola vez
para que la lógica de `app/lib/` pueda leerlos sin importar el cargador.
"""
from __future__ import annotations

# ADR-013: apto si L_inf >= 25; inspección si 20 <= L_inf < 25; hangar si
# L_inf < 20. Son un acuerdo de negocio, no un hiperparámetro del modelo.
# La validación OOF deja 20/15 fuera del defecto: 6/125 ciclos críticos
# terminaban en APTO y U20 concentraba el fallo.
DEFAULT_AIRWORTHY = 25.0
DEFAULT_AOG = 20.0
