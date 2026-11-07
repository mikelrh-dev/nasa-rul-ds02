# Plan de auditoría v2 — Reto 1 (SAA + PIA + MIA)

**Fecha:** 2026-11-06 · **Rama:** `clase-modelo-c` · **Modo:** solo lectura
**Antecedente:** `docs/informes/auditoria-2026-11-05-reto1-saa-pia-mia.md` (v1)
y change `openspec/changes/2026-11-05-bloques-auditoria/` (BL-01…BL-09 aplicados).
**Rúbrica:** `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (escala 0 / 3 / 7 / 10).

---

## 1. Pregunta de auditoría

¿El repositorio, **tal como está hoy**, demuestra por sí solo un 10 en cada criterio
de las tres rúbricas, y lo que no demuestra está declarado como límite?

No se vuelve a preguntar «¿funciona el modelo?»: v1 ya lo midió y el bundle C no ha
cambiado. La pregunta v2 es de **evidencia**: que exista, que se abra desde un clone
limpio, que diga lo mismo que el artefacto y que cubra el 10, no el 7.

**Criterio de éxito:** 20 celdas (10 SAA + 6 PIA + 4 MIA) con nota 0/3/7/10,
cada una con una prueba reproducible (`path:línea` o comando con salida), y un
anexo de cobertura con una fila por archivo del repositorio.

---

## 2. Qué cambió desde v1 (y por qué no se repite)

| Hallazgo v1 | Estado hoy | Qué audita la v2 |
| --- | --- | --- |
| C1/C2 · dos bandas (14 915 vs 17 450) | BL-02: `conformal` y `conformal_decision` separadas | Que la app use la correcta y que el test las ate |
| C3 · captura obsoleta | Retirada; `docs/assets/` con 9 figuras | Que ningún README prometa captura inexistente |
| C4/C5/A11 · multiseed | CSV generado; **`e00` veta 4.368 y el README lo publica** | Reconciliación de la cifra (contradicción nueva) |
| C6 · campeón duplicado | BL-01 aplicado | 0 residuos de «E2 campeón» fuera de contexto |
| A1 · 4 reglas | 6 de decisión + 2 de corrección | Conteo, prioridad y regla de seguridad |
| M4 · n8n placeholder | Flujo real (webhook + switch 3 ramas), `active: false` | Estructura, payload y límite de credenciales |
| PIA-4 · MLflow | **Sigue ausente**: no está en `requirements.txt` | Techo real de PIA-4 y su declaración |
| — | Módulos nuevos: `app/api.py`, `twin.py`, `pdf_partes.py`, `ui_alta.py`, `flota.py`, `hangar.py`, `simulacion.py` | Superficie nueva, no auditada en v1 |

No se repiten las comprobaciones invariantes de v1 (partición por motor, MAR,
huellas, 308/315 tests) salvo **spot-check**: solo se re-miden las que dependen de
archivos que hoy están modificados.

**Estado del árbol al planificar:** 49 archivos modificados y 11 rutas sin
seguimiento (`git status --porcelain`; 12 con este plan), incluidos
`models/ds02_manifest.json`, los 7 notebooks y `docs/assets/`. Eso obliga a F0
antes de cualquier conclusión.

---

## 3. Alcance

**Dentro**

- 20 criterios de rúbrica (SAA 1–10, PIA 1–6, MIA 1–4).
- Coherencia de cifras: manifiesto ↔ `e00` ↔ README ↔ notebooks ↔ `resultados/`.
- Reproducibilidad: suite, arranque de app/API, enlaces y figuras desde clone limpio.
- Contratos nuevos: manifiesto/caché, `src/n8n.py`, reglas, `app/api.py`.
- n8n: auditoría **estática** del JSON + una ejecución si hay instancia disponible.

**Fuera**

- Reentrenar el bundle, recalibrar bandas, re-leer el test (uds 11/14/15).
- Corregir hallazgos: la auditoría **no arregla**; produce informe y propuesta.
- Publicar, desplegar, usar credenciales reales o datos vivos de n8n.
- Re-ejecutar notebooks 03 y 04 mientras sigan sucios (mezclaría cambios previos).

---

## 4. F0 — Línea base obligatoria (15 min)

Sin esto, el informe no es auditable.

```bash
git rev-parse HEAD
git status --porcelain
sha256sum models/ensemble.joblib models/bilstm_ds02.keras models/ds02_manifest.json
python -c "import json;d=json.load(open('models/ds02_manifest.json'));print(d['artifacts'])"
```

- Si hay árbol sucio: el informe declara **commit + lista de archivos modificados**
  y audita ese estado, no un commit que no existe.
- **Puerta G0:** si un SHA no coincide con manifiesto y `cache_manifest`, se detiene
  la auditoría de cifras y se reporta antes de seguir.

---

## 5. Fases

| Fase | Qué se hace | Duración |
| --- | --- | --- |
| F0 | Congelar baseline (commit, status, hashes) | 15 min |
| F1 | Mecánica: `compileall`, suite, notebooks con salida, `git ls-files` | 40 min |
| F2 | SAA 1–10 contra evidencia | 60 min |
| F3 | PIA 1–6 contra evidencia | 45 min |
| F4 | MIA 1–4 (reglas + n8n) | 45 min |
| F5 | Síntesis, notas, hallazgos y límites | 30 min |

**F1 — comandos base**

```bash
.venv/Scripts/python.exe -m compileall -q src app scripts tests
.venv/Scripts/python.exe -m pytest tests -q -rs -p no:cacheprovider
git ls-files docs/assets | wc -l
git ls-files resultados | wc -l
```

Notas de lectura:

- Baseline declarado en el último commit: `336 passed, 6 skipped` (commit `5579346`).
  Hoy hay 329 funciones `test_` por grep; la diferencia es parametrización.
- Los 6 skips esperados son los que exigen `_p1_oof_cache.npz`. Un skip nuevo es
  hallazgo, no ruido.
- Notebooks: contar celdas con `outputs` y `cell_type == "code"` sin ejecutar;
  un `execution_count: null` con salida es señal de salida pegada a mano.

### 5.1 Cobertura: qué significa «100 %»

**Este plan no lee los 683 archivos línea a línea por defecto: audita criterios.**
Si se exige cobertura total, el contrato es el siguiente, y es el que hace
verificable la palabra «100 %».

Universo hoy: **683 archivos versionados + 12 sin seguimiento = 695**.

| Tier | Regla | Volumen | Método |
| --- | --- | --- | --- |
| **A** | Todo lo que produce o demuestra una nota | ~200 | Lectura completa (código, tests, notebooks, README, informes, ADR) |
| **B** | Material derivado o de proceso | ~450 | Inventario + búsqueda dirigida de contradicciones (cifras, claims, enlaces) |
| **C** | Binarios y artefactos | ~70 | SHA-256, carga y forma; no se leen |

- **Tier A:** raíz, `src/`, `app/`, `tests/`, `scripts/`, `notebooks/`, `n8n/`,
  `docClase/`, textos de `models/` y `docs/`.
- **Tier B:** `MLProyectVault/` (208), `openspec/` (123), `notebooksMD/` (40),
  `archive/` (75), configuración de editor/CI.
- **Tier C:** 34 PNG, 9 joblib, 14 NPY, 2 NPZ, 2 parquet, 8 logs y el
  `.keras` (70 archivos).
- Los `.ipynb` se inspeccionan como JSON de celdas, nunca como binarios.

Los tiers son **excluyentes por prioridad C > B > A**; el reparto exacto lo fija
`cobertura.csv`, no la estimación de esta tabla.

**Regla de cierre:** `cobertura.csv` con una fila por archivo
(`path,tier,veredicto,evidencia`), reconciliado a **695**, y **ningún archivo sin
tier**. Eso es el 100 % archivo por archivo: 100 % inventariado y clasificado,
100 % del tier A leído, tier B cotejado por afirmaciones y tier C verificado por
huella.

Lo que un barrido línea a línea añadiría: las 208 notas del vault y los 75 archivos
de `archive/` (material retirado). Coste ~4–6 h y **0 puntos de rúbrica**; se
excluye con motivo escrito, no por olvido.

---

## 6. Matriz de verificación (20 criterios)

Cada fila se puntúa 0/3/7/10 y **exige** evidencia abrible. «Qué demuestra el 10» es
la condición de cierre, no una sugerencia.

### SAA (10 criterios)

| # | Criterio (peso) | Evidencia esperada | Dónde | Qué demuestra el 10 |
| --- | --- | --- | --- | --- |
| 1 | IA débil (5 %) | Párrafo + comparación con IA fuerte | `README.md` «Qué hemos construido» | Nombra la AGI y razona por qué esta IA no transfiere |
| 2 | Tipo de aprendizaje (10 %) | Supervisado + regresión + diferencia con no supervisado | `README.md`, `src/clase/README.md` | Razona el «por qué», no solo etiqueta |
| 3 | Dataset y campos (5 %) | Tabla con tipo, % nulos y campos descartados | `src/clase/README.md`, NB01 | La tabla incluye nulos por campo y por qué se quita |
| 4 | ≥5 gráficos comentados (5 %) | Barras, histograma, boxplot, dispersión, heatmap | NB01 + `docs/assets/` | 5 tipos, cada uno con «qué veo / conclusión» |
| 5 | Nulos + variable nueva (5 %) | MAR justificado, imputación causal, `fase_vuelo` | `dataset_clase.py`, `auditoria_nulos.json`, NB01 | Patrón físico + por qué la variable aporta |
| 6 | 5 modelos + extra (30 %) | Ridge/KNN/RF/XGB/SVR + algo no visto | `train_clasicos.py`, `comparativa.csv`, híbrido C | Los 5 con GridSearchCV y el extra medido |
| 7 | MLP base + 3 experimentos (20 %) | Hipótesis escrita antes del resultado | `train_mlp.py`, NB02 | Cada experimento con su hipótesis y veredicto |
| 8 | Métricas y errores (10 %) | RMSE/MAE/R² + real-vs-predicho + lectura de negocio | `tabla_final.py`, README | Traduce el error a coste/hangar |
| 9 | Elección + SHAP (5 %) | Elección por negocio, desempate simple, SHAP en val | `train_*.py`, `shap_clase_e2.py`, `shap_c.py` | SHAP con aditividad y variables top |
| 10 | Pregunta individual (5 %) | Guion con respuesta y `path:línea` | `docs/defensa/guiones-15min.md` | Respuesta defendible, no memorizada |

### PIA (6 criterios)

| # | Criterio (peso) | Evidencia esperada | Dónde | Qué demuestra el 10 |
| --- | --- | --- | --- | --- |
| 1 | README + docstrings (10 %) | 6 apartados + apartados propios + funciones documentadas | `README.md`, gate de docstrings | 0 públicas sin docstring y README con extras |
| 2 | Carpetas y funciones (10 %) | Estructura del reto + `requirements.txt` | árbol, `requirements.txt` | Estructura reconocible y deps pinneadas |
| 3 | Pipeline sklearn (20 %) | `ColumnTransformer` compartido y guardado en el joblib | `pipeline_clase.py`, `models/mejor_modelo.joblib` | Carga y predice un caso nuevo con el pipeline dentro |
| 4 | MLflow (20 %) | Runs con params/métricas/tiempo + capturas | `requirements.txt`, `src/clase/train_*.py` | **Hoy no existe**: techo 0 en este criterio |
| 5 | App Streamlit (25 %) | Métricas test + caso nuevo + reglas + n8n + control de errores | `app/dashboard_ds02.py`, `ui_data_loader.py`, `src/n8n.py` | Envía decisión y rechaza datos vacíos/erróneos |
| 6 | Pregunta individual de código (15 %) | Respuesta con archivo:línea | guiones | Enseña el código y explica el porqué |

### MIA (4 criterios)

| # | Criterio (peso) | Evidencia esperada | Dónde | Qué demuestra el 10 |
| --- | --- | --- | --- | --- |
| 1 | Negocio con dato y objetivo (20 %) | Dato € + qué predice + para qué + quién + mejora | `README.md`, `costes_reales_aeronauticos.md` | Cuantifica qué supone para la empresa |
| 2 | ≥6 reglas (30 %) | Prioridad, decisión, porqué, regla de seguridad | `src/mia/reglas.py` | 6 de decisión + R1 y traza visible |
| 3 | n8n (35 %) | Webhook + rama por decisión + acción distinta a clase | `n8n/flujo.json`, `app/ui_n8n.py` | Recibe decisión y actúa distinto por rama |
| 4 | Pregunta individual (15 %) | Respuesta con `path:línea` | guiones | Explica la decisión, no solo el modelo |

---

## 7. Hipótesis a confirmar o refutar

Se declaran antes de mirar, para que el informe no se escriba a conveniencia.

| ID | Hipótesis | Cómo se falsa |
| --- | --- | --- |
| H1 | **Multiseed está en contradicción**: README publica `4.368 ± 0.053`; `e00` lo pone en lista negra y cita NB05 4.330 / NB06 4.322 | Comparar `comparativa_c_multisemilla.csv`, NB05/NB06 y manifiesto; si coinciden, H1 falsa |
| H2 | **PIA-4 vale 0**, no 3: sin `mlflow` en requirements ni runs, no hay «solo algunos modelos» | `grep -i mlflow requirements.txt` + `grep -rn "import mlflow" src/` |
| H3 | **n8n llega a 7, no a 10**: flujo real, pero `active:false` y credenciales sin probar | Validar JSON importable, nodos y conexiones; ¿acción distinta a Sheets/Postgres/Calendar/Gmail de clase? |
| H4 | **Manifiesto y caché pueden haberse desalineado** al editarse el manifiesto sin regenerar el sello | `manifest_sha256` del caché vs SHA del manifiesto |
| H5 | **Los notebooks sucios no reflejan el código actual** | `execution_count` y cifras de salida vs `resultados/` |
| H6 | **`docs/assets/` no está versionado**: los enlaces del README rompen en clone limpio | `git ls-files docs/assets` (hoy vacío) |
| H7 | **La app declara más de lo que muestra** (pestañas, SHAP, API, twin) | Arrancar `streamlit_app.py` y recorrer pestañas; `/health` y `/predict` |
| H8 | **Alguna cifra de README/chuleta no sale del manifiesto** | Cruce número a número contra `e00` y `ds02_manifest.json` |

**Regla de honestidad:** una hipótesis refutada se reporta como refutada; no se
reescribe el plan para que parezca que se confirmó.

---

## 8. Severidad y puertas

**Severidad** (misma escala que v1, para poder comparar)

- **C — Crítico:** invalida una nota entera o una cifra publicada.
- **A — Alto:** resta credibilidad o rompe un criterio de 10.
- **M — Medio:** inconsistencia que el tribunal puede no ver.
- **B — Bajo:** pulido, enlaces, redacción.

**Puertas**

| Puerta | Condición | Si falla |
| --- | --- | --- |
| G0 | Baseline congelado (commit + hashes) | No se auditan cifras |
| G1 | Suite ejecuta y los skips son los 6 esperados | Hallazgo C antes de seguir |
| G2 | Toda figura/enlace citado existe y se abre | Hallazgo A por enlace |
| G3 | Toda cifra publicada es rastreable a manifiesto o CSV | Hallazgo C/A según cifra |
| G4 | Cada criterio tiene evidencia para su nota | Se baja la nota, no se maquilla |
| G5 | La auditoría no modificó código, artefactos ni datos | El informe no se publica |
| G6 | `cobertura.csv` reconcilia 695 archivos y ninguno queda sin tier | Hallazgo A de cobertura |

---

## 9. Entregables

1. `docs/informes/auditoria-2026-11-06-reto1-v2.md`
   - Veredicto por asignatura y nota estimada.
   - Tabla de 20 criterios: nota, evidencia (`path:línea`), qué falta para el 10.
   - Hallazgos C/A/M/B con reproducción.
   - Anexo: comandos y salidas literales.
   - Límites (n8n sin credenciales, app sin navegador, etc.).
2. `resultados/auditoria-v2/criterios.csv` (no versionado) con la matriz en crudo.
3. `resultados/auditoria-v2/cobertura.csv` con una fila por archivo
   (`path,tier,veredicto,evidencia`), reconciliado a 695.
4. Si hay arreglos: **propuesta** openspec nueva; no se aplica en la auditoría.

---

## 10. Orden y duración

`F0 → F1 → F2 → F3 → F4 → F5`, con F2/F3/F4 independientes entre sí.

- **Auditoría por criterio:** ~4 h de lectura y ejecución, más ~3 min de suite.
- **Barrido 100 % (tier A completo + cobertura):** ~8–10 h; en este modo el
  anexo de cobertura es obligatorio.
- **Sin cómputo pesado:** no se reentrena ni se recalibra.
- **Dependencia externa:** MIA-3 en vivo exige instancia n8n. Si no hay, se audita el
  JSON, se declara el límite y la nota máxima justificable es 7 con evidencia estática.

---

## 11. Riesgos y límites declarados de antemano

1. **Árbol sucio:** 49 modificados + 11 sin seguimiento. El informe fija commit y lista;
   no se commitea nada durante la auditoría.
2. **TensorFlow no determinista:** cualquier re-ejecución mueve ±0.1 RMSE. No se
   re-ejecuta nada que entrene.
3. **Test de una sola lectura:** no se re-mide; se cita la lectura existente.
4. **n8n:** sin credenciales no hay ejecución real; se distingue «estructura válida»
   de «flujo probado».
5. **Entorno Windows/bash:** rutas con `/`, comandos POSIX, `.venv/Scripts/python.exe`.
6. **v1 no es verdad eterna:** si un hallazgo v1 se reabre, se cita la evidencia nueva.

---

## 12. Checklist de ejecución

- [ ] F0 · commit, `git status`, hashes y `manifest_sha256` del caché
- [ ] F1 · `compileall` + suite + conteo de skips + salidas de notebooks
- [ ] F1 · `git ls-files docs/assets` y `git ls-files resultados`
- [ ] F1 · `cobertura.csv` con 695 filas y 0 archivos sin tier (G6)
- [ ] F2 · SAA 1–10 con evidencia por criterio
- [ ] F3 · PIA 1–6, incluido el techo real de MLflow
- [ ] F4 · MIA 1–4, reglas contadas y n8n validado estáticamente
- [ ] H1–H8 resueltas (confirmadas o refutadas)
- [ ] F5 · informe con veredicto, matriz de 20 celdas y límites
- [ ] G5 · `git status` idéntico al de F0 (la auditoría no tocó nada)

---

## Conexiones

- Auditoría previa: `docs/informes/auditoria-2026-11-05-reto1-saa-pia-mia.md`
- Resultado de bloques: `docs/informes/informe-2026-11-05-bloques-auditoria-resultado.md`
- Cifras autoritativas: `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md`
- Rúbrica y enunciado: `docs/plans/reto_texto.txt`
