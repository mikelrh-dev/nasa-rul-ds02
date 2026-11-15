# Auditoría rúbrica v5 · 2026-11-15 · SAA + PIA + MIA

> **Modo:** solo lectura del proyecto. No se modificó código, artefactos, notebooks ni configuración.
> Únicos ficheros nuevos: este informe y los CSV en `resultados/_auditoria/auditoria-2026-11-15/` (ignorados por `.gitignore`).
> **Baseline:** HEAD `098d755` (rama `refactor/estructura-ds02-clase-2026-11-10`), 17 rutas sucias.
> **Rúbrica:** `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf`, escala 0 / 3 / 7 / 10.
> **Orquestación:** 3 olas de ≤3 subagentes con ventana deslizante + 2 jueces independientes (con reintento por límites de tasa del proveedor).

---

## 1. Veredicto

| Asignatura | Nota | Lectura |
|---|---|---|
| **SAA** | **10,00** (documentación completa) · **9,37** (solo `README.md` raíz) | SAA-1/SAA-2/SAA-9 dependen de `src/clase/README.md` |
| **PIA** | **9,65** | Techo real: PIA-2 = 7 por `pyarrow` no pineado |
| **MIA** | **10,00** (MIA-3 = 10 con Telegram) · **8,76** (si MIA-3 = 7) | El flujo versionado y el vivo incluyen Telegram |
| **Global (media igualitaria)** | **9,88** · **9,26** | Rango según qué material acepte el tribunal |

**Lo que más baja la nota:** las contradicciones documentadas (umbrales 30/25 publicados frente a 25/20 del código), `pyarrow` sin pinear y la pérdida de anclas en el README raíz.
**Lo que la sostiene:** modelos y métricas verificables en artefactos, 17 runs MLflow con params+métricas, app Streamlit funcionando, reglas reales y flujo n8n con ejecuciones reales.

---

## 2. Baseline F0 (congelado)

- HEAD `098d755`; árbol sucio: **17 rutas**. Intérprete: Python 3.12.10 (`.venv`).
- Artefactos íntegros: los 5 SHA-256 coinciden con el manifiesto (`ensemble d6c70142…`, `bilstm bf9620a7…`, `scaler acccfab3…`, `mejor_modelo_clase 5aab4d2a…`, `E2 3bebe67e…`); manifiesto `6089457c…`.
- Manifiesto: RMSE **4.338** · MAE **3.227** · R² **0.9461** · NASA **2336.2** · macro **5.0153**.
- Servicios vivos levantados: MLflow `127.0.0.1:5001` (17 runs) y n8n `localhost:5678` (workflow activo `hLlkHl3X33roWPEQ`).
- Suite pytest completa ejecutada: **495 passed / 3 failed** (exit 1). Los 3 fallos tienen causa única: `notebooks/00_datos.ipynb`.

---

## 3. Matriz de 20 criterios

Nota_raíz = leyendo solo `README.md`; nota_completo = con `src/clase/README.md` y el material del repo.

| ID | Peso | Nota raíz | Nota completo | Evidencia |Qué falta para el 10 |
|---|---:|---:|---:|---|---|
| SAA-1 IA débil | 5 % | 7 | 10 | `README.md:90-92` explica IA débil; comparación con IA fuerte solo en `src/clase/README.md:43` | Recuperar la comparación con IA fuerte en el README raíz |
| SAA-2 Tipo de aprendizaje | 10 % | 7 | 10 | Raíz: supervisado + regresión; diferencia con no supervisado solo en `src/clase/README.md:43` | Razonar la diferencia con el no supervisado en el raíz |
| SAA-3 Dataset y campos | 5 % | 10 | 10 | Tabla de campos con tipo/nulos + tabla de campos quitados y por qué | — |
| SAA-4 ≥5 gráficos | 5 % | 10 | 10 | NB01 Fig. 1–6 con "Qué veo / Qué concluyo"; PNG versionados | — |
| SAA-5 Nulos + variable nueva | 5 % | 10 | 10 | MAR T30 (1.185 nulos) + imputación causal + `fase_vuelo` justificada | — |
| SAA-6 5 modelos + extra | 30 % | 10 | 10 | 5 clásicos + MLP base/E1/E2/E3 + bundle C como extra | Matizar grano fila vs ventana al comparar |
| SAA-7 MLP base + 3 exp | 20 % | 10 | 10 | Hipótesis por experimento (`train_mlp.py:38-44`) + tabla de 4 filas | — |
| SAA-8 Métricas | 10 % | 10 | 10 | RMSE/MAE/R² en train y validación + real-vs-predicho + explicación de negocio | — |
| SAA-9 Elección + SHAP | 5 % | 7 | 10 | Tabla con métricas y tiempo + desempate al simple + SHAP con validación (fold-0) | Incluir la columna de tiempo en el README raíz |
| SAA-10 Pregunta individual | 5 % | n/p | n/p | No puntuable desde el repo | — |
| PIA-1 README + docstrings | 10 % | 10 | 10 | READMEs por capa; 345/350 funciones públicas con docstring (98,6 %) | — |
| PIA-2 Carpetas + requirements | 10 % | 7 | 7 | Estructura y pines OK; **`pyarrow` importado y no pineado** | Pinear `pyarrow` |
| PIA-3 Pipeline sklearn | 20 % | 10 | 10 | `Pipeline[ColumnTransformer(StandardScaler+OneHotEncoder)+reg]`; predice caso nuevo: 72,83 / 71,32 | — |
| PIA-4 MLflow | 20 % | 10 | 10 | 17 runs con params+métricas; `backfill --check` OK; capturas Compare | Juez 2 disiente (7) por los 3 tests MLflow-live que fallan |
| PIA-5 Streamlit | 25 % | 10 | 10 | AppTest real: `RUL p35` junto a `R7_APTO` y "APTO PARA VUELO" | — |
| PIA-6 Pregunta individual | 15 % | n/p | n/p | No puntuable | — |
| MIA-1 Negocio con dato | 20 % | 10 | 10 | AOG 10–15k USD/h (cita secundaria), objetivo, usuario y mejora | — |
| MIA-2 ≥6 reglas | 30 % | 10 | 10 | 8 reglas con prioridad y porqué; R1 seguridad prioridad 10 | — |
| MIA-3 Flujo n8n | 35 % | 10 | 10 | Webhook + switch 4 salidas con Telegram (novedoso) y Postgres/Calendar/Gmail/Sheets; ejecuciones reales | Juez 2 disiente (7): la "acción propia POST /n8n-decision" del vault no existe |
| MIA-4 Pregunta individual | 15 % | n/p | n/p | No puntuable | — |

### Notas ponderadas (fuera las preguntas individuales)

```
SAA 1-9 : 10,00 (completo) · 9,37 (solo README raíz)
PIA 1-5 : 9,65   (9,70 si PIA-6 = 10)
MIA 1-3 : 10,00  (8,76 si MIA-3 = 7)
Global  : media igualitaria 9,88 (completo) · 9,26 (conservador)
```

---

## 4. Hallazgos

### Críticos (afectan a la defensa)

| ID | Hallazgo | Evidencia |
|---|---|---|
| **C-01** | Umbrales publicados **30/25** frente al código **25/20** (ADR-013 Accepted) | `app/lib/_constantes.py:13-14`; `README.md:252`; `README.en.md:102-104`; `e00:151`; la app muestra "(25 / 20)" |
| **C-02** | La "acción propia" `POST /n8n-decision` que presenta el vault **no existe** | 0 nodos `httpRequest` en `flujo.json`; `api.py` solo `/health,/units,/predict`; `tests/test_n8n_propia.py` inexistente |

### Altos

| ID | Hallazgo | Evidencia |
|---|---|---|
| A-01 | El README raíz perdió los anclas SAA-1/SAA-2/SAA-9 | `grep` de "IA fuerte", "no supervisado", "Qué hemos construido" en `README.md` = 0; sin columna de tiempo |
| A-02 | `pyarrow` importado y no pineado | `dataset_clase.py:45`; ausente en `requirements.txt`/`pyproject.toml`; pandas solo lo declara como *extra* |
| A-03 | Suite no verde y gate caído | 495 passed / 3 failed; `verify_gate.py` exit 1; causa única `00_datos.ipynb` |
| A-04 | `data/` ignorado: el repo no reproduce la suite | `git ls-files data` = 0; 21 tests dependen de `data/processed/*.parquet`; en copia limpia: **24 failed / 474 passed** |
| A-05 | Store MLflow: portable para leer, con dos avisos | Verificado en clon limpio (`git archive HEAD`): `backfill_mlflow.py --check` → **OK 17 runs (exit 0)**. Los 17 dirs `artifacts/` están vacíos e ignorados (no rompen la lectura); las 19 `meta.yaml` traen rutas absolutas de esta máquina (inertes sin artefactos); hace falta `MLFLOW_ALLOW_FILE_STORE=true` |
| A-06 | Flujo n8n versionado ≠ vivo; webhook vivo sin auth | `flujo.json`: 20 nodos, `active:false`, `headerAuth`; vivo: 16 nodos, `active:true`, sin autenticación |
| A-07 | Cifras obsoletas | `e00:47` con entradas inexistentes; `openspec/specs/rul-prediction-ds02/spec.md:600` ordena 4.368; vigente real: **4.333 ± 0,040** (ddof=1) y fila oficial 4.338 |

### Medios

| ID | Hallazgo | Evidencia |
|---|---|---|
| A-08 | Cobertura e00 desactualizada | `e00:145` = 0,9012; `freeze_rules_evidence.py --check` = 0,901643; tablas `e00:148-150` no coinciden |
| A-09 | `src/clase/README.md` con rutas muertas | `app/ui_shap.py`, `app/dashboard_ds02.py` no existen; "~35 tests" (hay 498); `evaluar_c_multisemilla.py` no existe (solo `.pyc`) |
| M-01 | PNG duplicados y divergentes | 13 pares exactos docs↔resultados (17 en la unión); 12–19 nombres divergentes |
| M-02 | `src/clase/README.md` dice 15 nodos / 3 ramas; hoy son 20 nodos / 4 salidas | `flujo.json` |
| M-03 | Captura `run_prod.png` desacoplada del store actual | `docs/evidencia/mlflow/run_prod.png` |
| M-04 | Ablación `cyc_norm` solo con la rama BiLSTM+EMA5 (4×3) | `mlruns` 4 runs de ablación |

### Bajos

B-01 confusión 436 vs **498** tests · B-02 13 errores n8n sin documentar · B-03 hash `v3_bundle` no comprobable (fichero no está en disco) · B-04 deuda declarada sin cerrar (T02, alias A1-B, 21 changes openspec).

---

## 5. Controversias entre jueces (y resolución)

| Tema | Juez 1 | Juez 2 | Resolución |
|---|---|---|---|
| PIA-4 MLflow | 10 | 7 | **10**: los 17 runs están registrados con params+métricas y hay capturas; los 3 tests que fallan son de instrumentación de notebooks, no de registro |
| MIA-3 n8n | fuera de lente | 7 | **10 condicionado**: el flujo versionado y el vivo incluyen Telegram (novísimo respecto al flujo de clase); el 7 de J2 responde a la "acción propia" que el vault sí que sobreclama |
| Ponderado SAA solo raíz | 9,37 | — | **9,37** (J1 refutó el 9,53: con solo raíz caen SAA-1, SAA-2 y SAA-9) |
| 4.368 "no regenerable" | — | matiza | **Matizado**: 4,368 ± 0,053 se regenera desde `comparativa_c_multisemilla.csv`, pero ese CSV es el que `e00` declara obsoleto; la vigente es 4,333 ± 0,040 |
| PNG duplicados | — | 13/17 | Se toman los números de J2 (reproducidos con hashes) |

---

## 6. Límites de esta auditoría

1. **Árbol sucio:** el contenido auditado no está íntegramente en git (17 rutas). El baseline describe el árbol de trabajo en `098d755`, no un commit limpio.
2. **Suite:** ejecutada una vez en el árbol de trabajo (495/3). El juez 1 la replicó en copia limpia sin `data/` → 24 failed / 474 passed.
3. **No se reentrenó nada** ni se recalibró; las cifras se reprodujeron desde caché/artefactos versionados.
4. **Ningún notebook se ejecutó**; su evidencia se leyó de CSV/PNG versionados y del código de celdas.
5. Las preguntas individuales (SAA-10, PIA-6, MIA-4) no son puntuables desde el repo.
6. Subagentes y jueces escribieron solo en el scratch (`$TMPDIR`); el repo sigue con las mismas 17 rutas sucias.

---

## 7. Anexo — comandos clave y salidas

```bash
sha256sum models/*.joblib models/*.keras models/ds02_manifest.json   # coinciden con el manifiesto
python scripts/operativo/backfill_mlflow.py --check                 # OK: 17 runs (9 fila + 4 ventana + 4 ablacion)
python -m pytest tests -q -rs                                       # 495 passed, 3 failed in 328.87s
python scripts/operativo/verify_gate.py                            # 3 failed, 495 passed -> GATE FAILED
git ls-files data | wc -l                                           # 0
git ls-tree -r HEAD mlruns | grep -c artifacts                      # 0
git status --porcelain | wc -l                                      # 17 (sin cambios durante la auditoría)
```

CSV generados: `resultados/_auditoria/auditoria-2026-11-15/criterios.csv` y `hallazgos.csv`.
