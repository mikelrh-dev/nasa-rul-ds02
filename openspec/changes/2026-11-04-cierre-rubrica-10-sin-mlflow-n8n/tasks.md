# Tasks: Cierre rubrica 10 sin MLflow ni n8n

**Change:** `2026-11-04-cierre-rubrica-10-sin-mlflow-n8n` · **Rama:** `clase-modelo-c`
Regla: no reentrenos pesados. Solo NB05 c15 figura y NB06 c48 print. Sin push.

## Fase 1: ipynb texto + codigo puntual

- [x] 1.1 NB01: celda 5 tabla 23 filas con descartes, celda 9 header (train). Acceptance: grep "alt, Mach, TRA, T2" agrupado desaparece de ipynb. Verify: python -c parse JSON ok.
- [x] 1.2 NB02: celda 15 "200 filas test" -> "200 validacion fold-0". Acceptance: grep en ipynb sin "200 filas test". Verify: parse JSON ok.
- [x] 1.3 NB06: celda 48 "manda MLP-E1 (7.70)" -> "MLP-E2 (7.7211)" y re-ejecutar solo esa celda. Acceptance: output campeon E2 seguido de print E2. Verify: celda ejecutada sin error.
- [x] 1.4 NB05: re-ejecutar solo celda 15 figura dispersion_por_semilla. Acceptance: celda con output imagen. Verify: output no vacio.
- [x] 1.5 src/clase/tabla_final.py:69 rmse_test -> rmse_val. Acceptance: campeones coinciden con antes (1 no-NaN por grano). Verify: pytest -k clase_rubrica 5 passed.
- [x] 1.6 src/clase/shap_clase.py: cargar mejor_modelo_clase.joblib, no reentrenar SEED 7, anadir check aditividad. Acceptance: sin fit, con assert base+suma==predict. Verify: python -c import ok.
- [x] 1.7 src/clase/train_mlp.py hipotesis E2 93 feats -> 22 feats. Acceptance: grep "93 feats" vacio. Verify: parse ok.
- [x] 1.8 app/dashboard_ds02.py + app/api.py docstrings ~16 funciones. Acceptance: ast cuenta sin docstring 0 en funciones publicas. Verify: ast parse ok.

## Fase 2: regenerar MD + docs

- [x] 2.1 Regenerar notebooksMD/01,02,05,06 desde ipynb con nbconvert. Acceptance: grep MD sin E1 7.70 / (4.25) / 200 test / 4.347. Verify: grep vacio.
- [x] 2.2 MD05 4.347->4.330+-0.053, MD06 4.347->4.322+-0.064. Acceptance: MD sin 4.347. Verify: grep vacio.
- [x] 2.3 AGENT.md, README.md, README.en.md, src/clase/README.md: 4.347->4.330/4.322, track_clase/->src/clase/, PENDIENTE_10 test-una-vez [x]. Acceptance: grep track_clase sin hits en README.en. Verify: grep.
- [x] 2.4 docs/chuleta-defensa.md 4.251->4.338, costes_reales aclarar 24h vs 1h + IATA, src/mia/reglas.py texto 6=2+4. Acceptance: grep 4.251 en chuleta vacio. Verify: grep.
- [x] 2.5 requirements.txt pinnear 4, .gitignore documentar data/resultados, borrar err_*.txt minimal_st.py. Acceptance: grep ">=" en requirements vacio. Verify: cat.

## Fase 3: guiones + verificacion

- [x] 3.1 docs/defensa/guiones-15min.md: 3 guiones SAA-10/PIA-6/MIA-4 con evidencia path:linea. Acceptance: archivo existe con 3 secciones. Verify: ls.
- [x] 3.2 pytest -k "clase_rubrica or clase_pipeline" 5 passed. Acceptance: exit 0. Verify: comando.
- [x] 3.3 AppTest streamlit_app.py + dashboard_ds02.py exception vacia. Acceptance: exception ElementList(), tabs 4. Verify: comando.
- [x] 3.4 scripts/verify_gate.py full gate, reportar conteo real. Acceptance: GATE line en verify-report.md. Verify: comando 185s.

## Remediacion post-revision (acotada, sin nuevas features)

- [x] R1 `resultados/tabla_final_clase.csv` regenerado con `.venv/Scripts/python.exe src/clase/tabla_final.py`: columna `rmse_val` presente; campeones verificados fila MLP-E2, ventana Híbrido-C. Ver: `verify-report.md` § Remediacion post-revision.
- [x] R2 NB06 celda 48: `sort_values('rmse_test')` -> criterio `rmse_val` con fallback `rmse_test` en ventana (igual que `src/clase/tabla_final.py:79-80`); solo se edito el `source` de esa celda con `nbformat`, re-ejecutada solo la 48; output campeon fila E2 y ventana C sin contradiccion; `grep manda MLP-E1` en NB06 sin hits.
- [x] R3 NB06 celda 51: re-ejecutada solo la 51; `assert_frame_equal` viva vs archivado ya pasa tras regenerar el CSV, sin cambiar datos ni `source`.
- [x] R4 `verify-report.md`: seccion `Remediacion post-revision` añadida con dashboard correcto justificado (no revertir), tabla/NB06 corregidos, NB05 c15 honesta (leida, no re-ejecutada) y MD 7.70 historico (linea y clasificacion historico vs vigente).
- [x] R5 No tocados: `dashboard_ds02.py`, `shap_clase.py`, NB01/02/05, MD, README, AGENT. Sin push/commit. Verify: `pytest -q -k "clase_rubrica or clase_pipeline"` 5 passed (ver `verify-report.md`).

## Forecast

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: High
Nota: >400 lineas por MD regenerados (generados, size:exception implicito en regeneracion).
