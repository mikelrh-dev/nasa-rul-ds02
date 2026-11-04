# Proposal: Cierre rubrica 10 sin MLflow ni n8n

**Change:** `2026-11-04-cierre-rubrica-10-sin-mlflow-n8n`
**Status:** Proposed
**Capability:** modifica `clase-track` (notebooks, README, tabla, SHAP)
**Rama:** `clase-modelo-c`
**Fecha:** 2026-11-04

## Intent

Llevar cada criterio de la rubrica Reto 1 a 10 salvo PIA-4 MLflow (0) y MIA-3 n8n (0), explicitamente fuera de este change a peticion del usuario. El resto de gaps son texto desincronizado (MD vs ipynb), una linea de codigo que reintroduce seleccion por test, SHAP que reentrena, y docstrings/config.

## Scope

### In Scope
- Notebooks ipynb: NB01 celda 5 tabla 23 filas + celda 9 header, NB02 celda 15 texto SHAP, NB06 celda 48 E1->E2, NB05 celda 15 re-ejecutar figura.
- Regenerar notebooksMD 01/02/05/06 desde ipynb vigente.
- `src/clase/tabla_final.py:69` rmse_test -> rmse_val, `src/clase/shap_clase.py` cargar joblib + aditividad, `src/clase/train_mlp.py` hipotesis 22 feats.
- `app/dashboard_ds02.py` + `app/api.py` docstrings, `requirements.txt` pinnear 4, `.gitignore` documentar data/resultados, borrar basura untracked.
- Docs: AGENT.md, README.md, README.en.md, src/clase/README.md, PENDIENTE_10.md, docs/chuleta-defensa.md, costes_reales_aeronauticos.md, src/mia/reglas.py texto.
- Multiseed: 4.347 -> 4.330+-0.053 (NB05) / 4.322+-0.064 (NB06), o dejar solo 4.338.
- Guiones 15 min para SAA-10/PIA-6/MIA-4 en docs/defensa.
- Verificacion: pytest acotado clase + AppTest + verify_gate.

### Out of Scope
- PIA-4 MLflow entero (0). MIA-3 n8n entero (0). PIA-5 envia a n8n (queda en 7).
- Reentrenos pesados de 5 modelos/MLP/hibrido. Solo NB05 c15 figura y NB06 c48 print.

## Approach

TDD estricto segun openspec/config.yaml: tasks con acceptance check, test_command python -m pytest tests -q. Ondas de 2 subagentes con archivos disjuntos, padre consolida y re-ejecuta suite focal antes de siguiente onda. Notebook es build output pero en clase no hay builder: editar ipynb con script nbformat, regenerar MD con nbconvert.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| notebooks/*.ipynb | Modified | celdas texto NB01/02/06 |
| notebooksMD/*.md | Regenerated | espejo desde ipynb |
| src/clase/tabla_final.py, shap_clase.py, train_mlp.py | Modified | rmse_val, SHAP joblib, hipotesis |
| app/dashboard_ds02.py, app/api.py | Modified | docstrings |
| requirements.txt, .gitignore | Modified | pin 4, documentar data/resultados |
| README*, AGENT.md, PENDIENTE_10.md, chuleta | Modified | cifras C, rutas, test-una-vez hecho |
| docs/defensa/guiones-15min.md | New | 3 guiones individuales |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Editar ipynb a mano rompe JSON | Med | script nbformat + json.tool + re-parse tras cada cambio |
| Regenerar MD pisa ediciones | Med | regenerar solo tras ipynb final, un solo agente |
| Gate rojo preexistente 16 fallos | High | no bloquear cierre por ellos, reportar como preexistentes con diff |
| Cambiar tabla_final altera campeones | Low | verificar campeones coinciden (1 no-NaN por grano) |

## Rollback Plan

Git diff por archivo; cada onda commitea solo sus archivos (sin push, commits locales). Revertir con git checkout -- <archivo> antes de commitear, o revert del commit de la onda.

## Success Criteria

- [ ] Cada criterio != PIA-4/MIA-3/PIA-5-n8n en 10 segun tabla de auditoria actualizada.
- [ ] notebooksMD == ipynb vigente (grep E1 7.70 / 4.25 / 200 test vacio).
- [ ] pytest -k clase_rubrica + clase_pipeline 5 passed, AppTest exception vacia.
- [ ] verify_gate ejecutado y reportado con conteo real, sin ocultar los 16 preexistentes.
