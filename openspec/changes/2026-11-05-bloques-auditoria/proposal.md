# Propuesta: cerrar los bloques BL-01…BL-09 de la auditoría del Reto 1

**Change:** `2026-11-05-bloques-auditoria`
**Origen:** `docs/informes/auditoria-2026-11-05-reto1-saa-pia-mia.md`
**Estado:** aplicado

## Por qué

La auditoría de solo lectura dejó un veredicto: el modelo (bundle C) está bien y el
relato no siempre dice lo mismo que el artefacto. Nueve bloques con mejora y riesgo
medidos; MLflow y n8n quedan fuera por decisión explícita del usuario.

## Qué cambia

| Bloque | Cambio |
| --- | --- |
| BL-01 | Una sola narrativa: E2 es el campeón **de clase**; C es el **de producción** |
| BL-02 | El manifiesto declara dos bandas con papeles distintos (lectura del artefacto / corrección opcional R6) |
| BL-03 | Evidencia multisemilla completa (42 del manifiesto, 7 y 123 medidas) |
| BL-04 | Seis reglas de decisión (MIA-2), con R1 intacta |
| BL-05 | Figuras reales versionadas en `docs/assets/`; captura obsoleta retirada |
| BL-06 | SHAP del bundle C en primera línea; docstring de `ui_shap` corregido |
| BL-07 | Manifiesto con versión de Python y referencia histórica |
| BL-08 | La suite mira al campeón real; docstring 5k y criterio de tabla corregidos |
| BL-09 | Docstrings públicas y política fail-closed del gate, documentada |

## Qué NO cambia

- El bundle C **no se reentrena**: sigue siendo `models/ensemble.joblib`, seed 42,
  SHA `d6c701…a952dd`, RMSE 4.338.
- El test (uds 11/14/15) no se vuelve a mirar: ninguna métrica de test se recalcula.
- Las bandas conformales no se recalibran sobre test.
- `data/`, `resultados/` y `models/` conservan su política de versionado.

## Riesgos

- La banda R6 y la del artefacto ahora conviven en el manifiesto: el riesgo
  es que alguien lea la primera como si fuera la segunda. Mitigado con un test que
  ata `conformal_decision` al JSON que consume el motor.
- Las reglas nuevas solo actúan donde antes había silencio (ficha incompleta o
  umbrales invertidos): no cambian ninguna decisión existente.
