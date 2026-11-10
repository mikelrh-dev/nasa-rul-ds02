# Plan de cierre de rúbrica (sin MLflow ni n8n) — SUPERSEDED

> **SUPERSEDED (2026-11-09).** Este plan queda cerrado como histórico: MLflow
> (PIA-4) ya está implementado en `openspec/changes/2026-11-09-mlflow-pia4/` y
> `docs/plans/plan-mlflow-pia4-10.md` (13 runs en `mlruns/`, export y capturas).
> No usar sus cifras de techo ni su lista de tareas excluidas como estado actual.

Documento de trabajo para un agente que cierre las lagunas menores identificadas
en la evaluación 0-10 de SAA, PIA y MIA (sin implementar MLflow ni n8n).

## Contexto

- Rama: `clase-experimental`
- Notas actuales: SAA 9.5/10, PIA 6.7/10, MIA 5.5/10
- Techo sin MLflow/n8n: SAA 9.5, PIA 7.3, MIA 5.5
- Con las tareas de este plan: SAA 9.8, PIA 7.1, MIA 6.0

## Prioridades (alto impacto, bajo riesgo)

### P1 — SAA: comparación IA débil vs fuerte (Markdown)
- **Archivo:** `track_clase/01_eda.ipynb` (celda Markdown al inicio)
- **Acción:** Añadir celda Markdown:
  "IA fuerte haría X (fijar precios, atender llamadas, razonar sobre cualquier dominio). Esta IA débil solo predice RUL DS02 a partir de telemetría aprendida. Ventaja: barata, rápida, auditable."
- **Impacto:** +0.3 (7→10) | **Esfuerzo:** 10 min | **Riesgo:** 0

### P2 — SAA: expandir tabla de sensores
- **Archivo:** `track_clase/01_eda.ipynb` (celda Markdown de dataset)
- **Acción:** Expandir tabla para listar los 14 sensores individualmente (T24, T30, T48, T50, P15, P2, P21, P24, Ps30, P40, P50, Nf, Nc, Wf) con rango observado
- **Impacto:** +0.1 (9→10) | **Esfuerzo:** 15 min | **Riesgo:** 0

### P3 — PIA: captura de app
- **Archivo:** `resultados/dashboard_ds02.png` (nuevo) + `README.md` / `track_clase/README.md`
- **Acción:** Ejecutar `streamlit run app/dashboard_ds02.py`, sacar screenshot, guardar en resultados/, referenciar en README
- **Impacto:** +0.3 (8→9) | **Esfuerzo:** 5 min | **Riesgo:** 0

### P4 — MIA: cuantificar mejora en README
- **Archivo:** `README.md` (raíz) + `track_clase/README.md`
- **Acción:** Añadir en sección "La necesidad de negocio": "Con el modelo, se estima reducir paradas no planificadas en X% y ahorrar Y €/motor/año (estimación basada en coste de AOG 10.000–15.000 USD/h, rango Boeing)"
- **Impacto:** +0.5 (7→9) | **Esfuerzo:** 15 min | **Riesgo:** 0

### P5 — MIA: sección negocio en README raíz
- **Archivo:** `README.md` (raíz)
- **Acción:** Añadir sección "La necesidad de negocio" (ya está en track_clase/README.md, falta en raíz)
- **Impacto:** +0.3 (7→8) | **Esfuerzo:** 10 min | **Riesgo:** 0

### P6 — SAA: CV score separado
- **Archivo:** `track_clase/02_modelos_A.ipynb`, `03_modelos_B.ipynb`, `04_lgbm_adaptada.ipynb`
- **Acción:** Añadir CV score (GroupKFold) con media±std en cada notebook
- **Impacto:** +0.1 (9→10) | **Esfuerzo:** 20 min | **Riesgo:** 1

### P7 — PIA: docstrings
- **Archivo:** `app/ui_shap.py`, `app/ui_inference.py`, `app/ui_data_loader.py`
- **Acción:** Añadir docstrings a funciones públicas sin docstring
- **Impacto:** +0.2 (8→9) | **Esfuerzo:** 30 min | **Riesgo:** 1

### P8 — PIA: documentar scripts legacy
- **Archivo:** `README.md` (raíz) o `scripts/README.md`
- **Acción:** Documentar qué scripts son legacy y cuáles son vigentes, o mover a legacy/
- **Impacto:** +0.1 (8→9) | **Esfuerzo:** 15 min | **Riesgo:** 1

## Tareas de alto riesgo (NO recomendadas sin justificación)

### P9 — PIA: refactorizar dashboard monolítico
- **Archivo:** `app/dashboard_ds02.py` (~3.7k líneas)
- **Impacto:** +0.5 (8→9) | **Esfuerzo:** 4-6 h | **Riesgo:** 7
- **Recomendación:** Saltar. Impacto marginal para la rúbrica, alto riesgo de romper tests y app.

## Tareas excluidas (fuera de alcance actual)

- MLflow (PIA criterio 4, 20%): logging de experimentos, capturas
- n8n (MIA criterio 3, 35%): flujo real con webhook, rama por decisión, acción
- Estas se desarrollarán en un change posterior

## Orden de ejecución recomendado

1. P1 (10 min, riesgo 0)
2. P2 (15 min, riesgo 0)
3. P3 (5 min, riesgo 0)
4. P4 (15 min, riesgo 0)
5. P5 (10 min, riesgo 0)
6. P6 (20 min, riesgo 1)
7. P7 (30 min, riesgo 1)
8. P8 (15 min, riesgo 1)

**Total: ~2h, riesgo global 1/10. Notas esperadas: SAA 9.8, PIA 7.1, MIA 6.0.**

## Verificación

Tras cada tarea, ejecutar:
```bash
.venv/Scripts/python -m pytest tests -q
streamlit run app/dashboard_ds02.py  # verificar que arranca
```

## Archivos de referencia

- Rúbrica: `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf`
- README raíz: `README.md` (español, default)
- README clase: `track_clase/README.md`
- App: `app/dashboard_ds02.py`
- Notebooks: `track_clase/01_eda.ipynb` ... `05_ensemble_adaptado.ipynb`
- MIA: `mia/reglas.py`, `mia/motor.py`, `mia/modelo.py`, `mia/casos.py`
- Tests: `tests/test_clase_*.py`, `tests/test_live_eval.py`, `tests/test_mia_rules.py`
