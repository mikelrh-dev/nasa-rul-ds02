# Informes y auditorías — N-CMAPSS DS02

Mediciones del proyecto, una por pregunta. Cada documento es el acta de un
experimento o de una auditoría: qué se midió, con qué instrumento, y si la
hipótesis pasó o se rechazó. Los que deciden lo hacen con `dev`; el test solo
comprueba.

Los ADR viven aparte, en [`../decisions/`](../decisions/). Las specs desplegadas,
en [`../../openspec/specs/`](../../openspec/specs/). Los planes, en
[`../plans/`](../plans/).

---

## Por fecha

| Fecha | Documento | Qué responde | Instrumento |
| --- | --- | --- | --- |
| 2026-10-18 | [informe-2026-10-18-comparacion-nasa-fd001.md](informe-2026-10-18-comparacion-nasa-fd001.md) | Comparación de modelos sobre **C-MAPSS FD001** — otro dataset, no el flujo DS02 | `notebook_nasa_fd001.ipynb` (ejecutado completo) |
| 2026-10-20 | [informe-2026-10-20-ejecucion-cuaderno.md](informe-2026-10-20-ejecucion-cuaderno.md) | Ejecución del cuaderno de 71 celdas y análisis de su salida | `nbconvert --execute` + `scripts/predict_ds02.py` |
| 2026-10-20 | [informe-2026-10-20-meta-cycle-fix.md](informe-2026-10-20-meta-cycle-fix.md) | Acta del arreglo "quitar el reloj al meta-learner" | builder + notebook regenerado + 10 tests |
| 2026-10-21 | [informe-2026-10-21-motor16-vs-oof.md](informe-2026-10-21-motor16-vs-oof.md) | Ajustar el meta sobre el OOF de los cinco motores: **medido y rechazado** | `ds02_rul.stacking` (`fit_meta_learners`, `score_beta_holdout`) |
| 2026-10-21 | [informe-2026-10-21-p0-p1-prior-de-vida.md](informe-2026-10-21-p0-p1-prior-de-vida.md) | El sesgo de vida alta no es densidad, es el prior de vida del motor 16. **P1 no pasa el gate** | re-ventaneo a 20,6 filas/ciclo + folds agrupados (`dev`) |
| 2026-10-21 | [informe-2026-10-21-p3-capacidad-vs-informacion.md](informe-2026-10-21-p3-capacidad-vs-informacion.md) | ¿Capacidad del modelo o información ausente? Solo rama tabular, fuera de fold (`dev`) | `scripts/probe_capacity_vs_information.py` |
| 2026-10-21 | [informe-2026-10-21-alarma-y-confusion.md](informe-2026-10-21-alarma-y-confusion.md) | El bundle leído como alarma de mantenimiento: matriz de confusión por umbral | `scripts/probe_alarm_confusion.py` |
| 2026-10-21 | [informe-2026-10-21-evaluacion-general.md](informe-2026-10-21-evaluacion-general.md) | ¿Cómo de bueno es prediciendo? Todas las métricas sobre el artefacto en disco | `scripts/evaluate_model_quality.py` y cuatro sondeos |
| 2026-10-21 | [informe-2026-10-21-reglas-oof.md](informe-2026-10-21-reglas-oof.md) | Medidor de las reglas de corrección (R2–R5) y coherencia de banda (R6). Solo lectura | scratch de Hermes sobre `_p1_oof_cache.npz` |
| 2026-10-21 | [auditoria-2026-10-21-reglas.md](auditoria-2026-10-21-reglas.md) | Los 18 hallazgos de la auditoría: ¿alguna reparación exige reentrenar? **No** | lectura y recomputación |
| 2026-10-22 | [pendientes-2026-10-22-traspaso.md](pendientes-2026-10-22-traspaso.md) | Documento de traspaso: qué quedó cerrado, qué falta y cuánto cuesta | `pytest`, servidor real, gate de evidencias |

`pendientes-2026-10-22-traspaso.md` es evidencia de estado de una sesión, no un
informe de medición: se conserva y se indexa, pero caduca. Los tres documentos que
**no** son del flujo DS02 (FD001, y los planes de `../plans/`) van marcados como
tales en la tabla.

---

## Equivalencias: nombre antiguo → nombre nuevo

Estos documentos vivían sueltos en la raíz del repositorio. Se agruparon el
2026-10-22. Si buscas un nombre antiguo —en un informe histórico, en un commit
viejo, o en la prosa de los cuadernos de `notebooks/`— el mapeo es este:

| Nombre antiguo (raíz) | Ubicación nueva |
| --- | --- |
| `INFORME_ejecucion_cuaderno.md` | `docs/informes/informe-2026-10-20-ejecucion-cuaderno.md` |
| `INFORME_meta_cycle_fix_aplicado.md` | `docs/informes/informe-2026-10-20-meta-cycle-fix.md` |
| `INFORME_motor16_vs_oof.md` | `docs/informes/informe-2026-10-21-motor16-vs-oof.md` |
| `INFORME_p0_p1_prior_de_vida.md` | `docs/informes/informe-2026-10-21-p0-p1-prior-de-vida.md` |
| `INFORME_p3_capacidad_vs_informacion.md` | `docs/informes/informe-2026-10-21-p3-capacidad-vs-informacion.md` |
| `INFORME_alarma_y_confusion.md` | `docs/informes/informe-2026-10-21-alarma-y-confusion.md` |
| `INFORME_evaluacion_general_modelo.md` | `docs/informes/informe-2026-10-21-evaluacion-general.md` |
| `INFORME_reglas_oof.md` | `docs/informes/informe-2026-10-21-reglas-oof.md` |
| `AUDITORIA_ds02_2026-10-21.md` | `docs/informes/auditoria-2026-10-21-reglas.md` |
| `PENDIENTES_ds02_2026-10-22.md` | `docs/informes/pendientes-2026-10-22-traspaso.md` |
| `COMPARACION_NASA.md` | `docs/informes/informe-2026-10-18-comparacion-nasa-fd001.md` |
| `planificaci_n_de_desarrollo_ui_streamlit.md` | `docs/plans/planificacion_desarrollo_ui_streamlit.md` |
| `gemini211026.md` | `docs/plans/gemini-2026-10-21-evolucion-predictiva.md` |

**Citas que conservan el nombre antiguo a propósito.** La prosa de los cuadernos
(`02_DS02_ensemble_RUL.ipynb` celdas 11, 26, 27 y 38; `01_datos_y_bases.ipynb`
celda 14; `02_decision_ablacion_oof_ensamble.ipynb` celdas 17 y 18;
`03_evidencia_multisemilla_diagnostico.ipynb` celda 15) sigue citando el nombre
viejo. No son enlaces y ningún cuaderno lee un `.md`, así que no se rompe nada, y
el repositorio prohíbe editar cuadernos a mano
(`openspec/config.yaml`: *never modify notebooks in place; regenerate them from
`scripts/build_*.py`*). `scripts/build_02_notebook.py` sí quedó actualizado, de
modo que la próxima regeneración emitirá el nombre nuevo. Hasta entonces, esta
tabla es el puente.
