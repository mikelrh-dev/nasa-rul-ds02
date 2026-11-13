"""Paquete MIA: motor de reglas sobre la predicción de RUL del DS02.

Dos familias de reglas (medidas en `docs/informes/informe-2026-10-21-reglas-oof.md`):

* **Corrección (pasada B)** — modifican el número antes de evaluarlo:
  `R2b_ISOTONICO_CAUSAL` (ajuste isotonico causal del historial) y `R6_BANDA`
  (recalibrado de la banda conformal sobre el punto corregido).
* **Decisión (pasada A)** — traducen el número en una acción:
  `R1_SEGURIDAD` (dato imposible → no decidir) y los umbrales conformales
  25/20 de ADR-013 (`R7_APTO`, `R8_INSPECCION`, `R9_HANGAR`).

`predict()` de `src/ds02_rul/` y todo `models/` quedan intactos: el motor es una
capa de post-procesado independiente que no reentrena nada.
"""
