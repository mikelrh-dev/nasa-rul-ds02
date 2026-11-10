# Auditoría extensa vs Rúbrica Reto 1 v5 (SAA + PIA + MIA)

> **Rubrica:** `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (9 págs., 20 criterios,
> extraída con pdfplumber; las citas de §4 son literales).
> **Framework:** `docs/framework_auditoria.md` v1.0 (bloques A–Q, fases F0–F6, puertas G0–G6).
> **Estado de partida:** rama `fix/auditoria-2026-11-10`, árbol limpio, 5 commits locales.
> **Escala de nota:** la de la rúbrica — 0 / 3 / 7 / 10 — con decimales solo cuando el ancla
> superior está cubierta en parte.

---

## 0. Contrato

**Dentro:** los 20 criterios, el flujo `dato → modelo → artefacto → regla → API → UI → n8n → acción`,
los 1.174 ficheros versionados, la suite (445 tests + 1 skip), los 4 gates.

**Fuera:** reentrenar, reejecutar cuadernos, tocar `models/`, `data/raw`, `mlruns/` o credenciales
reales, desplegar.

**Límites que la auditoría declara de entrada:**

| Límite | Efecto |
|---|---|
| n8n sin instancia viva en la auditoría | MIA-3 se puntúa con evidencia estática + historial documentado, no con ejecución observada |
| 3 de los 4 criterios «pregunta individual» dependen de la persona | No auditables desde el repo: techo declarado 10, nota real no verificable |
| `costes_reales_aeronauticos.md` no está versionado | MIA-1 cita un rango (10-15k USD/h) cuya fuente no viaja en el clon |
| Sin HDF5 de 2,3 GB en git (`data/`) | PIA-3/5 se verifican en local, no desde un clon limpio (T02 abierto) |

---

## 1. Hipótesis previas (se escriben antes de comprobar)

- **H1.** La suite corre entera tras el arreglo del fixture (T01).
- **H2.** Los 4 SHA del bundle y el alias siguen intactos.
- **H3.** Los 20 criterios siguen cubiertos; lo que bajó no es la rúbrica sino la *demostrabilidad*.
- **H4.** El punto más frágil es MIA-3 (flujo versionado `active:false`, ejecución no atribuible a la app).
- **H5.** La frase «test una sola vez» es el único desvío de proceso de SAA.
- **H6.** MLflow cumple el criterio (17 runs) aunque sea backfill, no tracking en vivo.

---

## 2. Fases y salidas

| Fase | Qué se hace | Salida | Tiempo |
|---|---|---|---|
| **F0** | Baseline: commit, árbol, 5 hashes, manifiesto, sello, intérprete | tabla de trazabilidad | 15 min |
| **F1** | Mecánica: `compileall`, suite `-q -rs`, 4 gates, arranque API `:8000/docs`, dashboard `:8501`, rutas y enlaces | puertas G1–G2 | 45 min |
| **F2** | SAA-3/4/5: dataset 65.173 filas × 20 campos, tabla de nulos, 5 gráficos de NB01, MAR T30, `fase_vuelo` | matriz de campos | 60 min |
| **F3** | SAA-6/7/8/9: 5 clásicos + grids + GroupKFold, MLP base+E1/E2/E3, 17 runs, elección por `rmse_val`, SHAP validación, real vs predicho | tabla de modelos | 90 min |
| **F4** | PIA-1..5: README (6 obligatorios + propios), estructura de carpetas vs rúbrica, docstrings por AST, pipeline en joblib, app (test + caso nuevo + p) | checklist PIA | 75 min |
| **F5** | MIA-1..3: negocio con dato, 8 reglas con prioridad/porqué/seguridad, flujo n8n (webhook, 3 ramas, 4 acciones) | checklist MIA | 60 min |
| **F6** | Defensa: los 3 criterios individuales contra `docs/defensa/guiones-15min.md` | simulacro | 30 min |
| **F7** | Síntesis: notas, severidad, límites, `cobertura.csv`, informe | informe | 45 min |

**Puertas:** G0 baseline congelado · G1 compila y la suite ejecuta (skips nombrados) · G2 toda ruta y
enlace citado existe · G3 toda cifra rastreable a manifiesto/CSV/test · G4 cada criterio con evidencia
· G5 la auditoría no modifica nada · G6 `cobertura.csv` sin ficheros sin tier.

---

## 3. Matriz de los 20 criterios (rúbrica literal + nota)

### 3.1 SAA — 10 criterios

| # | Criterio (peso) · ancla 10 literal | Dónde se prueba | Nota | Estricta |
|---|---|---|---:|---:|
| 1 | *«Además lo compara con una IA fuerte y razona la respuesta»* (5 %) | `README.md:29` | 10 | 10 |
| 2 | *«Además razona el tipo de aprendizaje y en qué se diferencia del aprendizaje no supervisado»* (10 %) | `README.md:29` | 10 | 10 |
| 3 | *«Además la tabla indica los nulos de cada campo y qué campos quita y por qué»* (5 %) | `README.md:49-84`, NB01 | 10 | 10 |
| 4 | *«Al menos 5 gráficos comentados: barras, histograma, boxplot, dispersión y heatmap»* (5 %) | NB01, celdas MD 10-32 | 10 | 10 |
| 5 | *«Además crea alguna variable nueva útil y explica por qué»* (5 %) | `dataset_clase.py:11-18`, `auditoria_nulos.json` | 10 | 10 |
| 6 | *«Además prueba algo no visto en clase… y demuestra si mejora o no»* (30 %) | `train_clasicos.py:38-70,128-150`; híbrido 4,338 vs LGBM 7,067 | 10 | 10 |
| 7 | *«Modelo base y 3 experimentos, explicando por qué realiza cada experimento»* (20 %) | `train_mlp.py:38-44`, `mlp_comparativa.csv` | 10 | 10 |
| 8 | *«Además explica qué significan los errores del modelo para la empresa»* (10 %) | `README.md:140-160`, `_tab_auditoria.py:169-180` | 10 | 9,0 |
| 9 | *«Además explica con SHAP, calculado con validación, qué variables pesan más»* (5 %) | `shap_clase_e2.py:123-124,178`; `app/ui_shap.py` | 10 | 10 |
| 10 | *«Además lo enseña en su código o en sus resultados y explica el porqué»* (5 %) | `guiones-15min.md` §1 | 10 | 10 |

### 3.2 PIA — 6 criterios

| # | Criterio (peso) · ancla 10 literal | Dónde se prueba | Nota | Estricta |
|---|---|---|---:|---:|
| 1 | *«Además añade apartados propios a los obligatorios»* (10 %) | `README.md`, docstrings por AST | 10 | 10 |
| 2 | *«Además requirements.txt correcto»* (10 %) | estructura vs rúbrica; 22 pins = 22 de `pyproject.toml` | 10 | 10 |
| 3 | *«Además el modelo guardado incluye el pipeline y predice un caso nuevo»* (20 %) | `pipeline_clase.py:27,43`; joblib predice 66,29 (XGB) y 6,58 (E2) | 10 | 10 |
| 4 | *«Además compara los modelos en MLflow y lo enseña con capturas»* (20 %) | 17 runs + 3 capturas + `backfill_mlflow --check` | 10 | 9,5 |
| 5 | *«Además muestra la p del caso nuevo junto a la decisión»* (25 %) | `dashboard_ds02.py:1975-1997`, `_tab_motor.py:463-490` | 10 | 10 |
| 6 | *«Además lo enseña en su código o en sus resultados y explica el porqué»* (15 %) | `guiones-15min.md` §2 | 10 | 10 |

### 3.3 MIA — 4 criterios

| # | Criterio (peso) · ancla 10 literal | Dónde se prueba | Nota | Estricta |
|---|---|---|---:|---:|
| 1 | *«Además indica qué mejora supondría para la empresa»* (20 %) | `README.md:23-25`, tabla de coste del error | 10 | 9,5 |
| 2 | *«6 reglas o más con prioridad, decisión y una regla de seguridad»* (30 %) | `reglas.py:246-262` (8 reglas, R1 prioridad 10) | 10 | 10 |
| 3 | *«Recibe la decisión por webhook y hace una acción distinta a las vistas en clase según la decisión»* (35 %) | `n8n/flujo.json` (15 nodos, 3 ramas, 4 acciones + API propia) | 10 | 8,0 |
| 4 | *«Además lo enseña en su código o en sus resultados y explica el porqué»* (15 %) | `guiones-15min.md` §3 | 10 | 10 |

---

## 4. Puntuación

```text
Lectura normal   SAA = 10,00 · PIA = 10,00 · MIA = 10,00 · Techo 10,00
Lectura estricta SAA = (10·5+10·10+10·5+10·5+10·5+10·30+10·20+9·10+10·5+10·5)/100 = 9,90
                 PIA = (10·10+10·10+10·20+9,5·20+10·25+10·15)/100                    = 9,80
                 MIA = (9,5·20+10·30+8·35+10·15)/100                                   = 9,20
                 Techo = min(SAA, PIA, MIA)                                            = 9,20
```

**Qué separa el 10 del 9,20:** no la rúbrica, sino la *demostrabilidad*: n8n ejecutado y atribuible a
la app (MIA-3), tracking MLflow en vivo (PIA-4), fuente del coste dentro del repo (MIA-1) y la
disciplina de «test una sola vez» (SAA-8).

---

## 5. Pruebas negativas (qué haría bajar la nota)

| Si se comprueba que… | Baja |
|---|---|
| El flujo n8n importado no recibe `decision` o hace lo mismo en las 3 ramas | MIA-3 a 3 |
| SHAP se calculó con test y no con validación | SAA-9 a 7 |
| El joblib no contiene el pipeline (solo el regresor) | PIA-3 a 7 |
| Los 5 clásicos no están todos en MLflow | PIA-4 a 7 |
| La app no muestra la `p` junto a la decisión | PIA-5 a 7 |
| Menos de 6 reglas o sin regla de seguridad | MIA-2 a 7 |
| El README no tiene los 6 apartados obligatorios | PIA-1 a 7 |

---

## 6. Anexo — comandos de la auditoría

```bash
python -m compileall -q src app scripts tests
python -m pytest tests -q -rs
python scripts/freeze_rules_evidence.py --check
python scripts/freeze_oof_instrument.py --check
python scripts/backfill_mlflow.py --check
sha256sum models/ensemble.joblib models/bilstm_ds02.keras models/scaler.joblib \
          models/mejor_modelo.joblib models/mejor_modelo_clase.joblib
git ls-files notebooks | grep -c ipynb
```

