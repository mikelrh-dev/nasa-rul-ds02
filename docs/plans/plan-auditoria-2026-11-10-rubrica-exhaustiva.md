# Plan de auditoría exhaustiva — Rúbrica Reto 1 v5 (SAA + PIA + MIA)

**Fecha:** 2026-11-10 · **Rama:** `fix/auditoria-2026-11-10` · **HEAD:** `10761e7b960f2404adb8cfea93b82072ec4cb213`
**Commit HEAD:** `test(mlflow): alinea la aserción de backfill con los 17 runs` (2026-11-10 15:43:45 +0100)
**Modo:** SOLO LECTURA. No se arregla, no se commitea, no se reentrena, no se reejecutan notebooks, no se despliega.
**Rúbrica:** `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (9 págs., 20 criterios, extraída con `pdfplumber` y citada literal en §5).
**Framework:** `docs/framework_auditoria.md` v1.0 (bloques A–Q, fases F0–F6, puertas G0–G6).
**Antecedentes:** `docs/plans/plan-auditoria-2026-11-10-rubrica-post-cierre.md` y su informe; `docs/informes/auditoria-2026-11-10-rubrica-integral.md`.
**Intérprete único:** `.venv/Scripts/python.exe` (Python 3.12.10). **Shell:** bash (git-bash, Windows).
**Skills cargadas para esta auditoría:** `code-review-and-quality` (revisión de 5 ejes: corrección, legibilidad, arquitectura, seguridad, rendimiento) y `planning-and-task-breakdown` (troceado verificable, ventana deslizante, jueces independientes).

> **Regla de honestidad (no negociable).** Toda cifra y toda nota del informe final llevan `path:línea` o comando con salida literal. Lo que no se pueda probar se declara **límite**, nunca «PASA». La nota se baja, no se negocia. Este documento es un **plan**: sus tablas de nota son el **protocolo de decisión**, no resultados.
>
> **Garantía de solo lectura.** La auditoría **no modifica nada**: ni código, ni artefactos, ni datos, ni notebooks, ni configuración. No crea ni aplica changes de openspec. Lo único que escribe son el informe y sus CSV de evidencia; cualquier arreglo propuesto queda como texto y se ejecuta en otro trabajo, con autorización aparte.

---

## 1. Pregunta de auditoría y criterio de éxito

**Pregunta.** ¿En qué grado cumple el repositorio, **en el estado exacto de hoy** (`10761e7` + 1 fichero modificado sin commitear), cada uno de los **20 criterios** de la rúbrica v5, qué evidencia lo demuestra y qué falta exactamente para el 10?

**Segunda pregunta (la que pidió el usuario).** ¿Qué errores potenciales, incoherencias o mejoras existen, aunque no resten nota, en cada archivo y a lo largo del flujo completo `dato → modelo → artefacto → regla → API → UI → n8n → acción`?

**Criterio de éxito.**

1. 20 celdas con nota anclada `0 / 3 / 7 / 10`, cita literal del criterio, evidencia reproducible y columna `qué_falta_para_10`.
2. Nota ponderada por asignatura calculada con los pesos de la propia rúbrica, y techo declarado cuando una dependencia externa impide verificar.
3. `cobertura.csv` con **una fila por cada uno de los 1171 archivos versionados** (0 sin tier) más los artefactos locales no versionados que el flujo necesita.
4. Hallazgos C/A/M/B con reproducción, impacto y propuesta **no aplicada**.
5. Hipótesis pre-registradas resueltas como confirmadas o refutadas, incluidas las que se refuten.
6. Firma G5: `git status --porcelain` idéntico a F0 (solo se añaden el informe y los CSV de salida).

---

## 2. Baseline F0 — verificado hoy (no heredado)

| Variable | Valor medido | Comando |
| --- | --- | --- |
| Rama | `fix/auditoria-2026-11-10` | `git rev-parse --abbrev-ref HEAD` |
| HEAD | `10761e7b960f2404adb8cfea93b82072ec4cb213` | `git rev-parse HEAD` |
| Último commit | `10761e7` · 2026-11-10 15:43:45 +0100 · `test(mlflow): alinea la aserción de backfill con los 17 runs` | `git log -1 --format='%H %ad %s' --date=iso` |
| Árbol | **1 ruta al abrir el plan** (`M app/streamlit_app.py`, +17 líneas); **≥14 `M` + 1 `??` al cerrarlo** (18 `M` en la última comprobación: corrección 13→17 runs en curso + este plan) | `git status --porcelain --untracked-files=all` |
| Versionados | **1171** | `git ls-files \| wc -l` |
| `mlruns/` | **668** ficheros versionados; **19** `meta.yaml` en disco | `git ls-files mlruns \| wc -l`; `find mlruns -name meta.yaml \| wc -l` |
| `requirements.txt` vs `pyproject.toml` | **22 = 22**, sin dependencias divergentes | script de §6.2 |
| `models/mejor_modelo.joblib` | `5aab4d2a…4652615f` = `mejor_modelo_clase.joblib` (byte-idénticos) | `sha256sum models/mejor_modelo*.joblib` |
| `models/mejor_modelo_clase_E2.joblib` | `3bebe67e…aa376` | idem |
| `.streamlit/secrets.toml` | existe en local, **no versionado**; clave `N8N_WEBHOOK_URL` | `git ls-files .streamlit` → solo `config.toml` |
| `data/` | existe en disco (raw 2,3 GB + processed 9 ficheros); **0 ficheros versionados** | `git ls-files data \| wc -l` → `0` |
| `n8n/flujo.json` | 15 nodos, `active:false`, 2 × `REEMPLAZAR_CREDENCIAL` | script §6.5 |
| `resultados/auditoria-2026-11-10/` | 3 CSV de la auditoría anterior, **no versionados** | `git ls-files resultados/auditoria-2026-11-10` → vacío |

### 2.1 Divergencias con las auditorías anteriores (hay que explicarlas, no ocultarlas)

| Dato | Auditoría `c14d91b` | Hoy `10761e7` | Lectura |
| --- | --- | --- | --- |
| HEAD | `c14d91b` | `10761e7` | 2 commits después: se alineó el test de MLflow a 17 runs |
| Versionados | 1761 | **1171** | 590 rutas menos (poda de `mlruns/` y/o datos); hay que reconciliar el universo, no asumir |
| Árbol | 94 rutas (`mlruns/`) | **1 ruta al abrir**; **14 `M` + 1 `??` al cerrar** | El árbol se movió durante la planificación: F0 debe re-congelarse justo antes de F1 |
| `mlruns` en disco | 109 `meta.yaml` | **19** | La poda del store es real y cambia el alcance de PIA-4 |
| Suite | 444 passed / 1 skipped | **por medir en F1** | No se hereda el dato |
| Runs declarados | 13 (informe) | README **17**, `src/clase/README` **13** | Contradicción documental viva |

> **Nota de concurrencia (importante).** Mientras se redactaba este plan, el árbol pasó de 1 a 14 ficheros modificados: alguien está corrigiendo el desfase 13→17 runs en `src/clase/README.md`, `openspec/config.yaml`, `docs/pendiente/` e informes. Por tanto, **la foto de arriba caduca**: F0 se toma de nuevo inmediatamente antes de F1 y se anota el delta (`git diff --numstat`). La auditoría puntúa el estado congelado en ese instante, no el de este párrafo.

**G0.** Se congela el estado del momento F0 (commit + lista exacta de modificados) y se audita **tal cual**. Todo cambio sin commitear **entra en el alcance**: describe comportamiento o documentación que un clon limpio no tiene.

---

## 3. Alcance, exclusiones y límites

### 3.1 Dentro

- Los **20 criterios** de la rúbrica v5, con su texto literal y sus cuatro anclas.
- El **flujo completo** en 12 estaciones (§4), incluyendo la trazabilidad inversa (de la cifra publicada al artefacto).
- **Todos** los archivos versionados (1171) clasificados y con veredicto; lectura entera del código de tier A.
- Coherencia de cifras entre manifiesto, CSVs, README, README.en, AGENT.md, notebooks, vault, informes y defensa.
- Artefactos: hashes, manifiesto, sello de caché, allowlist de deserialización.
- Reglas, API, UI, n8n (estructura + payload + tests), tests y gates.
- Seguridad y datos personales versionados.
- Deuda y documentación caducada.

### 3.2 Fuera

- Reentrenar, recalibrar bandas, releer el test (uds 11/14/15), reejecutar notebooks.
- Corregir hallazgos: la auditoría **solo lee y documenta**. No edita código, artefactos, datos, notebooks ni configuración, y **no crea ni aplica** changes de openspec; las propuestas van como texto en el informe.
- `git add/commit/push`, desplegar, credenciales reales, inspeccionar la base de datos de n8n.
- Docker: el proyecto no lleva contenedores (decisión 2026-11-07) → bloque C = **n/a** declarado.

### 3.3 Dependencias externas y techo que imponen

| Dependencia | Estado | Efecto en la nota |
| --- | --- | --- |
| Instancia n8n | `active:false` + credencial placeholder en el JSON | MIA-3 se puntúa por **estructura + ramas + acción novedosa + tests**; «flujo ejecutado de punta a punta» = **NO VERIFICABLE** y se declara |
| API `:8000` | se intenta arrancar; si no responde, J y el endpoint de MIA-3 son NO VERIFICABLE | no se convierte en «PASA» |
| Dashboard `:8501` | idem | PIA-5 se puntúa por código + tests si no hay proceso |
| Dataset HDF5 (2,3 GB, fuera de git) | presente en local, ausente en clon | toda la reproducibilidad desde clon limpio queda limitada y se declara |
| Defensa oral (SAA-10, PIA-6, MIA-4) | fuera del repositorio | se puntúa el **guion con `path:línea`**; la nota final queda «sujeta a defensa» |

---

## 4. El flujo completo: 12 estaciones que la auditoría recorre en orden

Cada estación tiene archivos, una sonda y los criterios que alimenta. Si una estación falla, las siguientes se marcan «no verificable» en lo que dependa de ella, no se dan por buenas.

| # | Estación | Archivos núcleo | Sonda | Criterios |
| --- | --- | --- | --- | --- |
| 1 | Dato crudo | `data/raw/README.md`, `src/ds02_rul/data.py`, `src/clase/dataset_clase.py` | filas/columnas/unidades, hash del HDF5, reparto de motores | SAA-3, SAA-5, E |
| 2 | Dataset de clase (nulos + categórica) | `dataset_clase.py`, `data/processed/auditoria_nulos.json` | MAR documentado, ffill causal, `fase_vuelo`, X/y | SAA-3/4/5, PIA-3 |
| 3 | Features y ventanas | `src/ds02_rul/features.py`, `residualizer.py`, `src/clase/ventanas_adaptadas.py` | sin fuga: `unit` fuera, `RUL` fuera, normalización solo train | E, F |
| 4 | Modelos base | `train_clasicos.py`, `train_mlp.py`, `model.py` | 5 clásicos + GridSearchCV + GroupKFold; MLP base + 3 | SAA-6, SAA-7 |
| 5 | Ensemble y suavizado | `train_ensemble_adaptado.py`, `stacking.py`, `smoothing.py` | OOF agrupado, beta, EMA causal | F, SAA-6 (extra) |
| 6 | Banda conformal | `conformal.py`, `src/mia/calibracion_banda.json` | cobertura empírica, dos bandas rotuladas | F, MIA-2 |
| 7 | Artefacto y manifiesto | `models/*`, `persistence.py`, `app/cache/cache_manifest.json` | SHA antes de deserializar, sello, allowlist | H, G |
| 8 | Reglas | `src/mia/reglas.py`, `motor.py`, `src/reglas.py` | 6+ reglas, prioridad, seguridad, traza | MIA-2, I |
| 9 | API | `app/api.py`, `tests/test_security_api.py` | `/health`, `/predict`, auth, límites, errores | J, MIA-3 |
| 10 | UI | `app/streamlit_app.py`, `dashboard_ds02.py`, `ui_*.py` | métricas test + caso nuevo + `p` junto a decisión | PIA-5, SAA-8/10 |
| 11 | n8n | `n8n/flujo.json`, `src/n8n.py`, `app/ui_n8n.py` | webhook, 3 ramas, acción distinta a clase | MIA-3 |
| 12 | Evidencia y acción | `README.md`, `docs/`, `resultados/`, `MLProyectVault/`, `docs/defensa/` | toda cifra trazable; toda figura abre | G, N, SAA-8/9/10, PIA-1/6, MIA-1/4 |

**Trazabilidad inversa obligatoria.** Para cada cifra publicada (`4.338`, `3.227`, `0.9461`, `2336.2`, `5.0153`, `4.324`, `7.72`, `11.03`, `7.067`, `5.654`, `0.9016`, `17 runs`) se recorre: fichero que la publica → CSV/objeto que la mide → manifiesto/comando que la sella. Si la cadena se rompe, es hallazgo G.

---

## 5. La rúbrica, criterio por criterio (texto literal)

> Extraído de `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf`. La cita es la fuente de la nota: si el informe no cita, no puntúa.

### 5.1 Requisitos transversales (págs. 1-4)

- Dataset: «Datos en tabla, con valores nulos y al menos una variable categórica» y «Problema de clasificación o de regresión».
- Entrega: «un único proyecto en un único repositorio»; defensa de 15 minutos; «cada alumno/a responde individualmente a 3 preguntas».
- README, apartados obligatorios (*): 1 Título y una frase · 2 Captura de la app · 3 La necesidad de negocio más desarrollada · 4 Qué hemos construido (esquema modelo→reglas→n8n→acción + IA débil + tipo de aprendizaje) · 5 Los datos · 6 Resultados.
- Estructura pedida (pág. 3): `README.md`, `requirements.txt`, `data/raw`, `data/processed` (X_train, X_test, y_train, y_test), `notebooks/01_eda.ipynb` + `02/03_modelos`, `src/utils.py`, `src/reglas.py`, `src/n8n.py`, `app/streamlit_app.py`, `models/mejor_modelo.joblib`, `n8n/flujo.json`, `resultados/`.

### 5.2 SAA — 10 criterios, 100 %

| # | Criterio (RA · peso) | 0 | 3 | 7 | 10 |
| --- | --- | --- | --- | --- | --- |
| 1 | «Presenta su sistema explicando por qué es una IA débil» (RA1 · 5 %) | No lo menciona | Dice que es IA débil, sin explicar por qué | Explica con sus palabras por qué su sistema es IA débil | Además lo compara con una IA fuerte y razona la respuesta |
| 2 | «Explica el tipo de aprendizaje de su problema» (RA2 · 10 %) | No lo indica | Solo dice si es clasificación o regresión | Dice que es aprendizaje supervisado y si es clasificación o regresión | Además razona el tipo de aprendizaje y en qué se diferencia del no supervisado |
| 3 | «Describe el dataset y sus campos» (RA3 · 5 %) | No describe el dataset | Dice de dónde salen los datos, sin describir los campos | Tabla con todos los campos: nombre, qué significa y tipo | Además la tabla indica los nulos de cada campo y qué campos quita y por qué |
| 4 | «Analiza los datos con gráficos comentados» (RA3 · 5 %) | No hay gráficos | Gráficos sin comentar | 3 o 4 gráficos comentados | Al menos 5 gráficos comentados: barras, histograma, boxplot, dispersión y heatmap |
| 5 | «Trata los nulos y crea variables nuevas» (RA3 · 5 %) | No trata los nulos | Rellena o quita los nulos sin explicar por qué | Explica cómo trata los nulos y por qué (si son al azar o siguen un patrón) | Además crea alguna variable nueva útil y explica por qué. Si no se puede crear, explica la razón |
| 6 | «Entrena y valida los cinco modelos» (RA3 · 30 %) | Ningún modelo funciona | Menos de 5 modelos | Los 5 modelos | Además prueba algo no visto en clase y demuestra si mejora o no |
| 7 | «Experimenta con una red MLP de 3 experimentos» (RA5 · 20 %) | No hay MLP | Modelo base con menos experimentos, sin explicar por qué | Modelo base y 3 experimentos, sin explicar por qué realiza cada experimento | Modelo base y 3 experimentos, explicando por qué realiza cada experimento |
| 8 | «Valida los modelos con las métricas adecuadas a su problema» (RA6 · 10 %) | No calcula métricas | Usa una sola métrica sin explicar por qué | Varias métricas adecuadas, en train y validación. Regresión: MAE, RMSE, R² y gráfico real frente a predicho | Además explica qué significan los errores del modelo para la empresa |
| 9 | «Elige el mejor modelo para el negocio» (RA6 · 5 %) | No compara los modelos | Elige el de mejor métrica, sin ninguna explicación | Tabla con las métricas y el tiempo de cada modelo. Elige la métrica según el negocio y, si hay empate, el modelo más simple | Además explica con SHAP, calculado con validación, qué variables pesan más en el modelo elegido |
| 10 | «Responde a una pregunta individual sobre su proyecto» (· 5 %) | No responde o no tiene que ver | Responde de forma general, sin referirse a su proyecto | Responde bien sobre su proyecto | Además lo enseña en su código o en sus resultados y explica el porqué |

**Exigencias de cuerpo (pág. 2) que la tabla no repite:** los cinco modelos son «regresión, KNN, Random Forest, XGBoost, SVM» con «GridSearchCV con validación cruzada (si es necesario)»; «si las clases están desbalanceadas, aplicad SMOTE y comparad»; el test se lee «una sola vez, con el modelo elegido, en la app de Streamlit»; SHAP «calculado con validación (no con test)».

### 5.3 PIA — 6 criterios, 100 %

| # | Criterio (RA · peso) | 0 | 3 | 7 | 10 |
| --- | --- | --- | --- | --- | --- |
| 1 | «Documenta el código y el README» (RA1 · 10 %) | Sin README ni comentarios | README incompleto o funciones sin documentar | README con los apartados obligatorios y funciones documentadas | Además añade apartados propios a los obligatorios |
| 2 | «Organiza el código en carpetas y funciones» (RA2 · 10 %) | Todo en un único notebook | Código repetido en cada notebook | Sigue la estructura de carpetas y usa funciones comentadas | Además `requirements.txt` correcto |
| 3 | «Programa el preprocesado con un pipeline de sklearn» (RA2 · 20 %) | No hay preprocesado | Preprocesa a mano, repitiendo el código en cada modelo | Un pipeline con StandardScaler y OneHotEncoder que usan todos los modelos | Además el modelo guardado incluye el pipeline y predice un caso nuevo |
| 4 | «Registra los experimentos en MLflow» (RA2 · 20 %) | No usa MLflow | Solo algunos modelos | Todos los modelos y experimentos, con hiperparámetros y métricas | Además compara los modelos en MLflow y lo enseña con capturas |
| 5 | «Programa una app en Streamlit» (RA2 · 25 %) | No hay app o no carga el modelo | Hace solo una de las dos cosas: evalúa con test o predice un caso nuevo | Hace las dos: muestra las métricas de test con matriz de confusión o real-vs-predicho, y predice un caso nuevo con la decisión de las reglas | Además muestra la p del caso nuevo (probabilidad o valor predicho) junto a la decisión |
| 6 | «Responde a una pregunta individual sobre su código» (· 15 %) | No responde o no tiene que ver | Responde de forma general | Responde bien sobre su proyecto | Además lo enseña en su código o en sus resultados y explica el porqué |

### 5.4 MIA — 4 criterios, 100 %

| # | Criterio (RA · peso) | 0 | 3 | 7 | 10 |
| --- | --- | --- | --- | --- | --- |
| 1 | «Contextualiza el problema de negocio con un objetivo claro» (RA1 · 20 %) | No hay contextualización | Describe el problema, sin objetivo ni datos | Problema con un dato y objetivo claro: qué se predice, para qué y quién lo usa | Además indica qué mejora supondría para la empresa |
| 2 | «Crea reglas que convierten la predicción en una decisión» (RA5 · 30 %) | No hay reglas | Menos de 6 reglas, o sin decisión | Menos de 6 reglas con prioridad, porqué y una regla de seguridad | 6 reglas o más con prioridad, decisión y una regla de seguridad |
| 3 | «Conecta la decisión con un flujo de n8n» (RA5 · 35 %) | No hay flujo | El flujo no recibe la decisión o hace siempre lo mismo | Recibe la decisión por webhook y hace una acción distinta según la decisión | Recibe la decisión por webhook y hace una acción distinta a las vistas en clase según la decisión |
| 4 | «Responde a una pregunta individual sobre su proyecto» (· 15 %) | No responde o no tiene que ver | Responde de forma general | Responde bien sobre su proyecto | Además lo enseña en su código o en sus resultados y explica el porqué |

> **Nota de lectura (criterio 7 SAA).** La extracción literal del PDF pone «sin explicar por qué» en el ancla 7 y «explicando por qué» en el 10. Se respeta al pie de la letra: el 10 exige la justificación de cada experimento; si el repo solo tiene los 4 modelos sin justificación, la nota es **7**, no 10.

---

## 6. Fases F0–F8, puertas y comandos

### 6.1 Orquestación

```
F0  baseline congelado                         1 agente
F1  mecánica y gates (G0-G2)                   1 agente
F2  inventario y cobertura (A)                 1 agente
F3  SAA 1-10                                   1 agente
F4  PIA 1-6                                    1 agente
F5  MIA 1-4                                    1 agente
F6  transversales: cifras, artefactos, seguridad, deuda   3 agentes en ventana deslizante (máx. 3 vivos)
F7  2 jueces independientes                    J1 (SAA+PIA+G) · J2 (MIA+H+I+Q)
F8  síntesis y firma G5                        1 coordinador
```

**Ventana deslizante:** nunca más de 3 subagentes vivos; se lanza el siguiente al terminar uno. Los subagentes escriben en scratch (`$TMPDIR`), no en el repo. Solo el coordinador escribe el informe.

### 6.2 F0 — Baseline (15 min) · puerta G0

```bash
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
git log -1 --format='%H %ad %s' --date=iso
git status --porcelain --untracked-files=all | tee "$TMPDIR/f0_status.txt" | wc -l   # NO fijar: el árbol se mueve; registrar el valor real
git diff --numstat | tee "$TMPDIR/f0_numstat.txt"
git ls-files | wc -l                                                                 # esperado 1171
sha256sum models/ensemble.joblib models/bilstm_ds02.keras models/scaler.joblib \
          models/ds02_manifest.json models/mejor_modelo*.joblib
.venv/Scripts/python.exe - <<'PY'
import json, hashlib
m = json.load(open("models/ds02_manifest.json"))
c = json.load(open("app/cache/cache_manifest.json"))
h = hashlib.sha256(open("models/ds02_manifest.json","rb").read()).hexdigest()
print("manifest_sha256 real:", h)
print("sello cache:         ", c["artifact"]["manifest_sha256"])
print("seal_ok:", h == c["artifact"]["manifest_sha256"])
for k, v in m["artifacts"].items():
    if k.endswith("_sha256"):
        print(k, v)
PY
git diff -- app/streamlit_app.py     # el cambio sin commitear entra en el alcance
```

**G0 PASA** si el sello coincide y los hashes de `ensemble`, `bilstm` y `scaler` coinciden con el manifiesto. Si no, se detiene la puntuación de cifras.

### 6.3 F1 — Mecánica, gates y superficies (45 min) · puertas G1-G2

```bash
.venv/Scripts/python.exe -m compileall -q src app scripts tests; echo "compileall=$?"
.venv/Scripts/python.exe scripts/freeze_rules_evidence.py;        echo "rules=$?"
.venv/Scripts/python.exe scripts/freeze_oof_instrument.py --check; echo "oof=$?"
.venv/Scripts/python.exe scripts/backfill_mlflow.py --check;       echo "mlflow=$?"
.venv/Scripts/python.exe -m pytest tests -q -rs -p no:cacheprovider; echo "pytest=$?"

# Superficies (si no están vivas, se declara NO VERIFICABLE; nunca PASA)
curl -fsS http://127.0.0.1:8000/health; echo "api=$?"
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8501; echo "ui=$?"

# Enlaces y figuras (G2)
git ls-files | grep -E '\.(md|ipynb|html)$' > "$TMPDIR/docs.txt"
.venv/Scripts/python.exe - <<'PY'
import re, pathlib, subprocess
root = pathlib.Path(".")
files = subprocess.run(["git","ls-files"],capture_output=True,text=True).stdout.split()
bad = []
for f in files:
    if not f.endswith((".md",".ipynb",".html")): continue
    try: txt = pathlib.Path(f).read_text(encoding="utf-8", errors="ignore")
    except Exception: continue
    for m in re.finditer(r'!?\[[^\]]*\]\(([^)#]+)', txt):
        t = m.group(1).strip()
        if t.startswith(("http","mailto:","data:")) or t.startswith("#"): continue
        p = (pathlib.Path(f).parent / t).resolve()
        if not p.exists(): bad.append((f, t))
print("enlaces rotos:", len(bad))
for b in bad[:50]: print(" ", b)
PY
```

**G1** exige `compileall` limpio y suite ejecutada con su exit code. Todo skip se nombra: el histórico es `tests/test_mia_rules.py:181` (`_p1_oof_cache.npz` ausente). Un skip nuevo es hallazgo.
**G2** exige que toda figura/enlace citado abra; las imágenes se verifican por existencia + dimensiones, no por contenido visual, salvo las 3 capturas que sostienen PIA-4.

### 6.4 F2 — Inventario y cobertura archivo por archivo (60 min) · puerta G6

```bash
git ls-files > "$TMPDIR/universe.txt"
git ls-files | awk -F/ '{print ($2=="" ? "(raiz)" : $1)}' | sort | uniq -c | sort -rn
git ls-files data | wc -l
```

Construir `cobertura.csv` con **una fila por ruta versionada** (`1171`) y estas columnas:

```csv
path,tier,veredicto,evidencia,observacion
```

- `tier`: `C > B > A` excluyente.
- `veredicto`: `leido` / `cotejado` / `hash_ok` / `estructura_ok` / `n/a` / `no_verificable`.
- `evidencia`: `path:línea`, hash o comando. Nunca «visto».
- Universo adicional (fuera de `git ls-files`) declarado aparte, sin contarlo como versionado: `data/raw/*.h5`, `data/processed/*.parquet`, `data/processed/auditoria_nulos.json`, `.streamlit/secrets.toml` (solo claves), `_p1_oof_cache.npz` (ausente), `resultados/*`.

**G6** exige 1171 filas reconciliadas y 0 sin tier. Las rutas históricas (`archive/`, `mlruns/` antiguos, `docs/informes/` viejos) son tier B/C con veredicto `cotejado`, no se omiten.

### 6.5 F3 — SAA 1-10 (90 min)

```bash
grep -n "IA débil\|IA fuerte\|supervisado\|no supervisado" README.md src/clase/README.md
.venv/Scripts/python.exe - <<'PY'
import json, re
nb = json.load(open("notebooks/01_eda_y_contexto.ipynb"))
md = [ "".join(c["source"]) for c in nb["cells"] if c["cell_type"]=="markdown" ]
code = [ "".join(c["source"]) for c in nb["cells"] if c["cell_type"]=="code" ]
print("celdas md/code:", len(md), len(code))
for kw in ("bar","hist","box","scatter","heatmap","corr","conclusi","qué veo","que veo"):
    print(kw, sum(1 for s in md if kw.lower() in s.lower()))
PY
cat resultados/comparativa.csv
cat resultados/mlp_comparativa.csv
cat resultados/tabla_final_clase.csv
grep -n "GridSearchCV\|GroupKFold\|param_grid\|tiempo" src/clase/train_clasicos.py
grep -n "EXPS\|porque\|hipótesis\|hipotesis" src/clase/train_mlp.py
grep -n "masker\|fondo\|valid\|fold" src/clase/shap_clase.py src/clase/shap_clase_e2.py
```

Se puntúa cada criterio con su ancla (§5.2) y se registra la evidencia exacta. Trampas conocidas: (a) los granos fila vs ventana no son comparables — se exige el rótulo; (b) el gráfico real-vs-predicho debe existir, no bastan las métricas; (c) SHAP debe ser **de validación**, y del **modelo elegido** para el 10.

### 6.6 F4 — PIA 1-6 (75 min)

```bash
grep -n "^## \|^### " README.md
.venv/Scripts/python.exe - <<'PY'
import ast, pathlib
missing=[]
for area in ("src","app"):
    for p in pathlib.Path(area).rglob("*.py"):
        if "__pycache__" in p.parts: continue
        t=ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(t):
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and not n.name.startswith("_") and ast.get_docstring(n) is None:
                missing.append(f"{p}:{n.lineno}:{n.name}")
print("públicas sin docstring:", len(missing)); print("\n".join(missing[:40]))
PY
grep -n "ColumnTransformer\|StandardScaler\|OneHotEncoder" src/clase/pipeline_clase.py
.venv/Scripts/python.exe - <<'PY'
import joblib
for p in ("models/mejor_modelo.joblib","models/mejor_modelo_clase_E2.joblib"):
    m=joblib.load(p); print(p, type(m).__name__, hasattr(m,"named_steps"), list(getattr(m,"named_steps",{})))
PY
.venv/Scripts/python.exe scripts/backfill_mlflow.py --check
.venv/Scripts/python.exe - <<'PY'
import csv, collections
rows=list(csv.DictReader(open("docs/evidencia/mlflow/comparativa.csv")))
print("filas export:", len(rows)); print("columnas:", list(rows[0]))
print(collections.Counter(r.get("familia") or r.get("grano") for r in rows))
PY
grep -n "st.tabs\|st.metric\|RUL p35\|L_inf\|enviar_decision\|matriz\|real_vs_pred" app/dashboard_ds02.py | head -40
```

Trampas: (a) `models/mejor_modelo.joblib` es alias del **mejor clásico**, no del modelo elegido — el criterio PIA-3 pide que el modelo guardado incluya el pipeline y prediga un caso nuevo, y ambos lo cumplen, pero hay que decir cuál es cuál; (b) PIA-4 exige **todos** los modelos y experimentos: 5 clásicos + 4 MLP + 4 ventana + 4 ablación = 17; verificar que cada run tiene params, métricas y tiempo, y que el export coincide con el store; (c) PIA-5 exige la `p` del caso nuevo **junto** a la decisión, no en otra pestaña.

### 6.7 F5 — MIA 1-4 (60 min)

```bash
sed -n '20,30p' README.md; sed -n '1,40p' costes_reales_aeronauticos.md
sed -n '240,280p' src/mia/reglas.py
.venv/Scripts/python.exe - <<'PY'
from src.mia.reglas import REGLAS_DECISION, REGLAS_CORRECCION
print("decision:", len(REGLAS_DECISION), "correccion:", len(REGLAS_CORRECCION))
for r in REGLAS_CORRECCION + REGLAS_DECISION:
    print(r[0], "| prio", r[3], "| porque:", bool(r[4]))
PY
.venv/Scripts/python.exe - <<'PY'
import json
d=json.load(open("n8n/flujo.json"))
print("active:", d["active"], "nodos:", len(d["nodes"]))
print("webhook auth:", [n.get("parameters",{}).get("authentication") for n in d["nodes"] if n["type"].endswith("webhook")])
for n in d["nodes"]:
    if n["type"].startswith("n8n-nodes-base.") and "sticky" not in n["type"]:
        print("-", n["name"], "|", n["type"], "| cred:", n.get("credentials"))
print("conexiones:", list(d["connections"]))
PY
grep -n "DECISIONES_QUE_NOTIFICAN\|def enviar_decision\|timeout" src/n8n.py app/ui_n8n.py
python -m pytest tests/test_n8n_propia.py tests/test_n8n_decision.py tests/test_mia_rules.py -q -rs
```

Trampas: (a) 6 reglas **de decisión** más reglas de corrección: el conteo que vale es el que produce decisión; (b) la regla de seguridad debe ser explícita y con la prioridad más alta; (c) MIA-3 exige acción **distinta a las vistas en clase**: Sheets/Postgres/Calendar/Gmail son de clase; la API propia es la novedosa y hay que demostrar que se ejecuta (nodo + endpoint + test), no solo que existe; (d) `active:false` y `REEMPLAZAR_CREDENCIAL` impiden declarar «flujo probado de punta a punta».

### 6.8 F6 — Transversales (90 min, 3 agentes)

**F6.a Cifras (G3).** Cruzar manifiesto ↔ caché ↔ `resultados/*.csv` ↔ README/README.en/AGENT ↔ `src/clase/README` ↔ vault/`e00` ↔ notebooksMD ↔ defensa. Comando base:

```bash
grep -rn "4\.338\|3\.227\|0\.9461\|2336\.2\|5\.0153\|4\.324\|4\.368\|7\.72\|11\.03\|7\.067\|5\.654\|0\.9016\|0\.9012" \
  README.md README.en.md AGENT.md src/clase/README.md docs MLProyectVault notebooks --include=*.md --include=*.ipynb | head -200
```

**F6.b Artefactos y seguridad (H/J).** Hashes, `persistence.py` (SHA antes de deserializar, allowlist, rutas absolutas), `app/cache/cache_manifest.json`, `instrumento_oof.npz`, joblib guard. Además: secretos y datos personales versionados.

```bash
grep -rn "joblib.load\|keras.models.load_model" src app scripts | grep -v pyc
grep -n "verify_artifact_sha256\|allowlist\|resolve_within_repo\|sha256" src/ds02_rul/persistence.py | head -30
git ls-files | grep -Ei 'secret|token|\.env|registros|respaldo|\.bak|\.pem|\.key' || echo "sin ficheros sensibles versionados"
```

**F6.c Tests, deuda y documentación (M/N/Q).**

```bash
ls tests/test_*.py | wc -l
grep -rn "TODO\|FIXME\|HACK\|XXX" src app scripts tests --include=*.py | wc -l
grep -rn "skip\|xfail" tests --include=*.py | head -40
cat docs/pendiente/deuda-riesgo-7-2026-11-10.md
git ls-files resultados | wc -l
```

### 6.9 F7 — Jueces independientes (60 min)

Dos revisores que **no leen el transcript del otro**:

- **J1:** reproduce SAA 1-10 + PIA 1-6 + G. Propone notas y lista discrepancias.
- **J2:** reproduce MIA 1-4 + H (artefactos) + I (reglas) + Q (deuda). Propone notas y discrepancias.

Cada juez clasifica **cada afirmación** previa como `confirmada` / `refutada` / `no verificable`, con su propio comando. Una nota de juez sin rúbrica o un recuento de tests que mezcle skips se marca como no verificable. El coordinador arbitra con evidencia y lo documenta en el informe.

### 6.10 F8 — Síntesis y firma (45 min)

- Matriz de 20 celdas + nota ponderada + techo.
- Hallazgos ordenados C/A/M/B.
- Límites de la auditoría.
- Anexo de comandos con salidas literales.
- **G5:** `git status --porcelain --untracked-files=all` = F0 + informe + CSV nuevos. Nada más.

---

## 7. Archivo por archivo — tier A (lectura entera)

> Columnas: **archivo** · **qué se verifica** · **criterios/bloque**. Los 1171 archivos se clasifican en `cobertura.csv`; aquí se enumeran **todos** los que pueden mover una nota.

### 7.1 `src/` (39 ficheros Python)

| Archivo | Qué se verifica | Criterio |
| --- | --- | --- |
| `src/__init__.py` | paquete vacío; no oculta imports | D |
| `src/clase/__init__.py` | docstring de paquete; exports | PIA-1 |
| `src/clase/dataset_clase.py` | MAR, ffill causal, `fase_vuelo`, split por motor, X/y, campos excluidos | SAA-3/5, E |
| `src/clase/pipeline_clase.py` | `ColumnTransformer` con StandardScaler + OneHotEncoder; mismas columnas para todos | PIA-3 |
| `src/clase/train_clasicos.py` | 5 modelos, GridSearchCV, GroupKFold(`unit`), tiempos, escritura del joblib | SAA-6/8/9 |
| `src/clase/train_mlp.py` | base + E1/E2/E3; justificación por experimento; CSV | SAA-7 |
| `src/clase/tabla_final.py` | una fila por modelo, grano declarado, orden por validación | SAA-9, G |
| `src/clase/shap_clase.py` | explainer/masker/fondo de **validación**, no test | SAA-9 |
| `src/clase/shap_clase_e2.py` | SHAP del modelo **elegido** (E2) | SAA-9 |
| `src/clase/ventanas_adaptadas.py` | ventanas honestas, sin fuga, contrato 93/19 | E, F |
| `src/clase/train_lgbm_adaptada.py` | LGBM cuantil 0.35; escribe CSV + joblib | SAA-6 (extra) |
| `src/clase/train_ensemble_adaptado.py` | escritor del bundle C; reproduce 4.338 con seed 42 | H, G |
| `src/clase/evaluar_c_multisemilla.py` | semillas 42/7/123; CSV; ± como cota de ruido | G, F |
| `src/clase/puente_c.py` | contrato clase→bundle C; sin duplicar inferencia | D, H |
| `src/clase/README.md` | 6 apartados, cifras, contradicción «13 runs»/«17 runs», «No se descarta ningún campo» | PIA-1, G |
| `src/ds02_rul/__init__.py` | exports del paquete instalable | PIA-2 |
| `src/ds02_rul/data.py` | ingestión HDF5, unidades, contrato de columnas | E |
| `src/ds02_rul/features.py` | preprocessing sin fuga; ventanas | E |
| `src/ds02_rul/residualizer.py` | residualización por régimen (ADR-002) | F, E |
| `src/ds02_rul/inference.py` | extracción de ventana cruda para un caso nuevo | K |
| `src/ds02_rul/model.py` | BiLSTM, triple pooling, canal 19 | F |
| `src/ds02_rul/pooling.py` | pooling serializable (sin Lambda) | H |
| `src/ds02_rul/stacking.py` | OOF agrupado, `beta`, sin in-sample | F |
| `src/ds02_rul/ensemble.py` | carga + inferencia del bundle; EMA | H, K |
| `src/ds02_rul/smoothing.py` | EMA causal por unidad (sin futuro) | F, E |
| `src/ds02_rul/conformal.py` | bandas asimétricas por bins; cobertura | F |
| `src/ds02_rul/metrics.py` | RMSE/MAE/R²/NASA; NASA = **suma**, sin clamp | G |
| `src/ds02_rul/persistence.py` | SHA antes de deserializar, allowlist, rutas dentro del repo | H, J |
| `src/ds02_rul/pipeline.py` | orquestación train/eval; no filtra test | F |
| `src/ds02_rul/shap_c.py` | SHAP por ramas del bundle C (LGBM/BiLSTM/meta) | SAA-9 |
| `src/ds02_rul/viz.py` | estilo de figuras; coherencia con `resultados/` | N |
| `src/ds02_rul/mlflow_live.py` | tracking live; no `log_model`/autolog | PIA-4 |
| `src/mia/__init__.py` | exports del motor | MIA-2 |
| `src/mia/reglas.py` | 6 de decisión + corrección; prioridad; seguridad; `porque` | MIA-2 |
| `src/mia/motor.py` | dos pasadas, una aplicación por pasada, traza | MIA-2, I |
| `src/mia/modelo.py` | carga el artefacto congelado; una sola ruta | H, D |
| `src/mia/casos.py` | casos con decisión esperada y borde | MIA-2, M |
| `src/n8n.py` | timeout, nunca lanza a la UI, contrato del payload | MIA-3 |
| `src/reglas.py` | fachada re-export; no duplica lógica | MIA-2, D |
| `src/utils.py` | fachada con nombres de rúbrica; re-export de pipeline/métricas | PIA-1/2/3 |

### 7.2 `app/` (21 ficheros Python)

| Archivo | Qué se verifica | Criterio |
| --- | --- | --- |
| `app/streamlit_app.py` | entrypoint de rúbrica; **cambio sin commitear** que carga `secrets.toml` en `os.environ` | PIA-5, J |
| `app/dashboard_ds02.py` | 4 pestañas; métricas test; caso nuevo; `p` + decisión; envío n8n; manejo de errores | PIA-5, SAA-8/10 |
| `app/api.py` | `/health`, `/predict`, `/n8n-decision`, auth `hmac`, límites, errores sin stack | J, MIA-3 |
| `app/dashboard_helpers.py` | helpers puros (sin Streamlit); testables | D |
| `app/flota.py` | registro de motores, etiquetas únicas | K |
| `app/hangar.py` | máquina de estados del hangar | K, MIA-2 |
| `app/pdf_partes.py` | parte de trabajo PDF; datos y formato | K |
| `app/simulacion.py` | simulador de turnos; determinismo | K |
| `app/twin.py` | gemelos digitales; persistencia atómica | K |
| `app/ui_alta.py` | alta rápida; mapeo perfil→(unidad,ciclo) | PIA-5 |
| `app/ui_batch.py` | lote de N motores y triaje | PIA-5 |
| `app/ui_data_loader.py` | capa de datos read-only; no recomputa en cada rerun | K, Q |
| `app/ui_inference.py` | evaluación de una unidad nueva | PIA-5 |
| `app/ui_n8n.py` | payload y dedupe; decisiones que notifican | MIA-3 |
| `app/ui_rules.py` | puente caché→reglas; sin lógica duplicada | MIA-2, D |
| `app/ui_shap.py` | SHAP global + waterfall; coherencia con el bundle | SAA-9 |
| `app/ui_modulos/__init__.py` | fachada del split | D |
| `app/ui_modulos/_tab_motor.py` | pestaña Motor extraída | K |
| `app/ui_modulos/_tab_flota.py` | pestaña Flota extraída | K |
| `app/ui_modulos/_tab_auditoria.py` | pestaña Auditoría extraída | K |
| `app/ui_modulos/_sandbox_estres.py` | sandbox de estrés | K |

### 7.3 `tests/` (49 ficheros) — se lee el contrato, no solo el verde

| Archivo | Contrato que fija | Criterio |
| --- | --- | --- |
| `tests/conftest.py` | aislamiento de registros de flota entre tests | M |
| `tests/test_api_limites.py` | IP, expiración, `/units`, `/predict`, lifespan | J |
| `tests/test_app_fixes1.py` | regresiones app-fixes-1 | PIA-5 |
| `tests/test_app_fixes2.py` | regresiones app-fixes-2 | PIA-5 |
| `tests/test_app_ux_bundle.py` | bundle UX de la app | PIA-5 |
| `tests/test_artifact_contract.py` | contrato del artefacto | H |
| `tests/test_audit_fixes.py` | regresiones de auditorías; **guard `needs_oof` muerto** (líneas 44-45) | M |
| `tests/test_cache_drift.py` | caché no se reutiliza con sello stale | H |
| `tests/test_ci_contract.py` | deps/CI | PIA-2, Q |
| `tests/test_clase_bundle_c.py` | parquet adaptado → raw honesto | E, H |
| `tests/test_clase_c_multisemilla.py` | evidencia multisemilla | G |
| `tests/test_clase_clasicos.py` | 5 clásicos + comparativa | SAA-6 |
| `tests/test_clase_dataset.py` | ffill causal, pureza de `fase_vuelo` | SAA-3/5 |
| `tests/test_clase_mlp.py` | base + 3 experimentos | SAA-7 |
| `tests/test_clase_pipeline.py` | mismo preprocesado, 1 caso nuevo | PIA-3 |
| `tests/test_clase_rubrica.py` | alias de rúbrica y tres campeones | PIA-2/3, H |
| `tests/test_clase_shap.py` | SHAP con explainer/masker/fondo explícitos | SAA-9 |
| `tests/test_clase_shap_e2.py` | SHAP del MLP elegido E2, no del XGB | SAA-9 |
| `tests/test_clase_tabla.py` | grano declarado, nunca mezcla fila/ventana | SAA-9, G |
| `tests/test_clase_ventanas.py` | adaptada sobre pipeline honesto | E |
| `tests/test_conformal_dual_band.py` | dos bandas rotuladas | F |
| `tests/test_ds02_viz_residual_smoothing.py` | viz, residualización, EMA causal | F, N |
| `tests/test_dss_interaction.py` | botones estrella sin romper la app | PIA-5 |
| `tests/test_dss_ui.py` | superficie DSS | PIA-5 |
| `tests/test_engine_flow.py` | flota + gemelo + hangar | K |
| `tests/test_fleet_registries_session.py` | sesiones: aislamiento, atomicidad, backup | K, Q |
| `tests/test_flota.py` | registro de motores | K |
| `tests/test_hangar.py` | máquina de estados del hangar | K |
| `tests/test_joblib_guard.py` | los 5 `joblib.load` guardados | H, J |
| `tests/test_live_eval.py` | evaluación de unidad nueva | PIA-5 |
| `tests/test_mejoras_streamlit.py` | mejoras P0/P1/P2 de la app | PIA-5 |
| `tests/test_mia_reglas_directas.py` | condiciones/efectos R1/R2b/R6–R11 | MIA-2 |
| `tests/test_mia_rules.py` | motor, corrección, decisión; **1 skip** `@needs_oof:181` | MIA-2, M |
| `tests/test_mlflow_backfill.py` | store real, completo, sin artefactos | PIA-4 |
| `tests/test_mlflow_live.py` | helpers y contrato de tiempos | PIA-4 |
| `tests/test_n8n_apto_post.py` | APTO 2xx ok; 500/timeout no; SIN_DECISION no POST | MIA-3 |
| `tests/test_n8n_decision.py` | flujo mínimo MIA-3 | MIA-3 |
| `tests/test_n8n_propia.py` | endpoint propio de la rama HANGAR | MIA-3 |
| `tests/test_persistence_manifest.py` | manifiesto, SHA, allowlist, huella | H |
| `tests/test_rules_gate.py` | gate de evidencias de reglas | MIA-2, M |
| `tests/test_security_api.py` | contrato de seguridad de la API | J |
| `tests/test_shap_c.py` | SHAP por ramas del bundle C | SAA-9 |
| `tests/test_shap_c_puras.py` | funciones puras de SHAP-C sin cómputo pesado | SAA-9 |
| `tests/test_simulacion.py` | simulador de turnos | K |
| `tests/test_twin.py` | registro de gemelos | K |
| `tests/test_ui_alta.py` | alta rápida | PIA-5 |
| `tests/test_ui_batch.py` | incorporación en lote | PIA-5 |
| `tests/test_ui_rules.py` | puente caché→reglas | MIA-2, PIA-5 |
| `tests/test_ux_round3.py` | tercera ronda UX | PIA-5 |

### 7.4 `scripts/` (22 ficheros)

| Archivo | Qué se verifica | Bloque |
| --- | --- | --- |
| `scripts/README.md` | contrato de scripts y orden de ejecución | PIA-1 |
| `scripts/ablate_meta_cycle.py` | sonda histórica del contador de ciclo; ¿reproducible? | Q, G |
| `scripts/anclar_raiz_pylance.py` | anclaje de raíz del repo en el venv | B |
| `scripts/backfill_mlflow.py` | 17 runs, idempotente, `--check` = store+export | PIA-4 |
| `scripts/build_07_shap_c_notebook.py` | builder de NB07 | N, Q |
| `scripts/build_ui_cache.py` | caché de la UI y su manifiesto | H |
| `scripts/evaluate_model_quality.py` | precisión del artefacto, no métrica de marketing | G, F |
| `scripts/freeze_oof_instrument.py` | instrumento OOF versionado; `--check` = 0.901643 | G, M |
| `scripts/freeze_rules_evidence.py` | evidencia de reglas sin drift | MIA-2 |
| `scripts/make_clase_checksums.py` | checksums de los joblib de clase | H |
| `scripts/p0_density_control.py` | sonda histórica P0 (densidad vs vida) | Q, G |
| `scripts/p1_meta_support.py` | sonda histórica P1 sobre `dev` | Q, G |
| `scripts/p1_oof_cache.py` | productor del `_p1_oof_cache.npz` ausente | Q, M |
| `scripts/patch_mlflow_live_notebooks.py` | parche de cabecera MLflow en NB01-07 | PIA-4, N |
| `scripts/predict.py` | CLI FD001 **legacy**: apunta a `models/v3_bundle.joblib` inexistente | H, Q |
| `scripts/predict_ds02.py` | inferencia DS02 vigente | K |
| `scripts/repackage_artifact.py` | reempaquetado sin entrenar | H |
| `scripts/run_nb06_0_25.py` | ejecutor parcial de NB06 | N, Q |
| `scripts/v3_core.py` | núcleo FD001 legacy (features, OOF, umbral) | Q |
| `scripts/v3_finalize.py` | bundle FD001 legacy; ya no escribe `v3_bundle` | Q |
| `scripts/v3_lstm.py` | rama LSTM FD001 legacy | Q |
| `scripts/v3_run.py` | fases 0-2 FD001 legacy | Q |
| `scripts/verify_gate.py` | gate global del repo | M |

### 7.5 `notebooks/` (7)

| Archivo | Qué se verifica | Criterio |
| --- | --- | --- |
| `01_eda_y_contexto.ipynb` | tabla de campos, 5 tipos de gráfico, cada uno con «qué veo / conclusión», nulos, `fase_vuelo` | SAA-3/4/5 |
| `02_modelos_clasicos_y_mlp.ipynb` | 5 clásicos, GridSearch, MLP base + 3, comparativa, real-vs-predicho | SAA-6/7/8 |
| `03_feature_engineering_secuencial.ipynb` | ventanas, residualización, ablación `cyc_norm` | E, F, G |
| `04_arquitectura_bilstm_oof.ipynb` | BiLSTM, OOF agrupado, sin fuga | F |
| `05_meta_ensemble_y_conformal.ipynb` | stacking, beta, banda, cobertura | F |
| `06_evaluacion_produccion_comparativa.ipynb` | test una vez, multiseed, rótulos de histórico | G, SAA-8 |
| `07_shap_c_bundle_c.ipynb` | SHAP de validación del modelo desplegado, aditividad | SAA-9 |

Se inspeccionan como **JSON de celdas**: tipo, outputs, si hay errores, si las cifras impresas coinciden con los CSV. Un notebook con outputs de otro entorno se declara (ya pasó: outputs bajo Python 3.10 del sistema).

### 7.6 Contratos, configuración y artefactos (raíz + `models/` + `n8n/`)

| Archivo | Qué se verifica | Criterio |
| --- | --- | --- |
| `README.md` | 6 apartados obligatorios, cifras, IA débil, tipo de aprendizaje, capturas, tabla MLflow | PIA-1, SAA-1/2/8/9, MIA-1 |
| `README.en.md` | coherencia con el español, cifras, enlaces | N, G |
| `AGENT.md` | punteros estables, no cifras caducadas | N |
| `pyproject.toml` | `requires-python`, deps pinneadas, `testpaths` | PIA-2, B |
| `requirements.txt` | 22 pins, sin divergencia con pyproject | PIA-2 |
| `uv.lock` | coherencia con requirements | B |
| `.gitignore` | `data/`, `resultados/`, `mlruns` artifacts, `secrets.toml`, registros | Q, J |
| `.github/workflows/ci.yml` | instala pinneado, corre tests, no entrena | PIA-2, Q |
| `.streamlit/config.toml` | tema; sin secretos | J |
| `n8n/flujo.json` | 15 nodos, webhook auth, switch 3 ramas, acción propia, `active:false` | MIA-3 |
| `models/ds02_manifest.json` | hashes, métricas, partición, contrato | H, G |
| `models/README.md` | escritor por artefacto, alias manual | H |
| `models/ensemble.joblib` / `bilstm_ds02.keras` / `scaler.joblib` | SHA contra manifiesto | H, G0 |
| `models/mejor_modelo.joblib` / `mejor_modelo_clase.joblib` | byte-idénticos; alias sin escritor | PIA-3, H |
| `models/mejor_modelo_clase_E2.joblib` | SHA contra manifiesto | H |
| `src/mia/calibracion_banda.json` | banda de decisión, 14 915 filas | F, MIA-2 |
| `models/alarm_policy.json` / `psi_reference.json` | política y deriva | O |
| `models/legacy/*` | rotulado histórico, no vigente | H, N |
| `app/cache/cache_manifest.json` + 2 parquet | sello del manifiesto, coherencia | H |
| `docClase/*.pdf` | rúbrica; `README_ejemplo_CV.md` como referencia de README | PIA-1 |

### 7.7 Tier B — documentación (136 en `docs/` + 143 en `openspec/` + vault)

- **Lectura entera (B1):** `docs/framework_auditoria.md`, `docs/defensa/guiones-15min.md`, `docs/chuleta-defensa.md`, `docs/informes/README.md`, `docs/decisions/ADR-001…012`, `openspec/project.md`, `openspec/config.yaml`, specs desplegadas en `openspec/specs/*`.
- **Cotejo por afirmaciones (B2):** los 22 informes de `docs/informes/`, los 21 planes previos de `docs/plans/`, los 15 pendientes de `docs/pendiente/`, el vault (`10-Conceptos`, `20-Sistema`, `30-Notebooks`, `50-Evidencia`), `docs/presentacion/*` (HTML y assets) y `openspec/changes/*` (histórico de changes).
- **Regla de cotejo:** toda cifra, enlace, nombre de fichero o promesa de estado se contrasta con la fuente vigente; lo caducado se marca como histórico, no se borra.
- **Riesgo específico:** `docs/presentacion/` y `docs/chuleta-defensa.md` son superficies de defensa: si publican una cifra muerta, es hallazgo **A** aunque no reste en la rúbrica.

### 7.8 Tier C — binarios y evidencias (verificación por huella)

`mlruns/` (668 ficheros, 19 `meta.yaml`), 53 PNG versionados, `models/*.joblib|*.keras`, `app/cache/*.parquet`, `src/mia/instrumento_oof.npz`, `data/processed/*.parquet` (local), `data/raw/*.h5` (local).

- **Regla:** hash o estructura, nunca «abrir a ojo». Para `mlruns/`: un `meta.yaml` por run, `params/`, `metrics/`, `tags/`, sin `artifacts/`.
- Para las 3 capturas de MLflow (`compare_fila.png`, `compare_ventana.png`, `run_prod.png`): se abren y se comprueba que muestran lo que el README dice (es la evidencia de PIA-4 → 10).

---

## 8. Protocolo de puntuación (cómo se pasa de evidencia a nota)

### 8.1 Anclas estrictas

| Nota | Regla |
| --- | --- |
| **0** | El requisito no existe, no carga o no tiene relación con el proyecto. |
| **3** | Existe una versión parcial o genérica que no llega al ancla 7. |
| **7** | El requisito del ancla 7 se cumple **completo** y verificable. |
| **10** | Se cumple el 7 **y además** el «además» literal de la rúbrica, demostrado. |

No hay 5, 8 ni 9 por criterio: si el «además» está a medias, la nota es **7**. Los decimales aparecen solo en la media ponderada.

### 8.2 Cálculo

```
SAA = (n1·5 + n2·10 + n3·5 + n4·5 + n5·5 + n6·30 + n7·20 + n8·10 + n9·5 + n10·5) / 100
PIA = (n1·10 + n2·10 + n3·20 + n4·20 + n5·25 + n6·15) / 100
MIA = (n1·20 + n2·30 + n3·35 + n4·15) / 100
```

Se publican las tres notas; **no se inventa una nota global**: la rúbrica no da peso inter-asignatura. Se publica el **techo global = min(SAA, PIA, MIA)** como lectura conservadora, rotulada como tal.

### 8.3 Reglas de techo y no verificable

1. Sin instancia n8n ejecutada, MIA-3 puede llegar a 10 por estructura + acción novedosa + tests, pero el informe declara «no ejecutado de punta a punta».
2. Sin API/UI vivas, J y la parte viva de PIA-5 se declaran NO VERIFICABLE; se puntúa por código + tests, y se dice.
3. SAA-10, PIA-6 y MIA-4 se puntúan por el **guion con `path:línea`**; la nota queda «sujeta a defensa oral».
4. Un criterio cuyo «además» dependa de un artefacto ausente en clon limpio (p. ej. `data/processed`) se puntúa por el estado en disco y se anota la limitación; si el «además» **solo** existe en local, no se da por demostrado → baja a 7.

### 8.4 Columnas de `criterios.csv`

```csv
id,asignatura,ra,criterio,peso,nota,ancla_7_cumplida,plus_10_cumplido,evidencia,que_falta_para_10,limite
SAA-1,SAA,RA1,"Presenta su sistema explicando por qué es una IA débil",5,10,si,si,"README.md:29","—","—"
```

`que_falta_para_10` vacío **solo** si la nota es 10; si es 10, se escribe `—` y se listan reservas.

---

## 9. Hipótesis pre-registradas (antes de ejecutar F1-F6)

> Estado `comprobado en planificación` = ya verificado hoy al escribir este plan; el resto se resuelve en la fase indicada. Una hipótesis refutada se publica como refutada.

| ID | Hipótesis | Falsación | Estado |
| --- | --- | --- | --- |
| H01 | El árbol de trabajo **está corrigiendo** el desfase 13→17 runs (`src/clase/README.md`, `openspec/config.yaml`, `docs/pendiente/*`, informes), pero la corrección **no está commiteada** y pueden quedar menciones residuales | `git diff --numstat`; `grep -rn "13 runs" README.md src docs openspec MLProyectVault` | **comprobado: 14 `M` en curso** |
| H02 | `backfill_mlflow.py --check` valida **17** runs y el export tiene 17 filas, pero en disco hay **19 `meta.yaml`** | `python scripts/backfill_mlflow.py --check`; `wc -l docs/evidencia/mlflow/comparativa.csv`; `find mlruns -name meta.yaml \| wc -l` | **comprobado (17 filas / 19 meta.yaml)** |
| H03 | `data/` **no está versionado**: un clon limpio no tiene `data/raw` ni `data/processed` | `git ls-files data \| wc -l` → 0 | **comprobado** |
| H04 | `app/streamlit_app.py` tiene un cambio sin commitear que inyecta `secrets.toml` en `os.environ` y **traga** `TOMLDecodeError` | `git diff app/streamlit_app.py` | **comprobado** |
| H05 | `.streamlit/secrets.toml` **no** está versionado (solo `config.toml`) y `.gitignore` lo cubre | `git ls-files .streamlit`; `grep -n streamlit .gitignore` | **comprobado** |
| H06 | `models/mejor_modelo.joblib` es copia byte-idéntica del XGB y **no tiene escritor** | `sha256sum models/mejor_modelo*.joblib`; `grep -rn "mejor_modelo.joblib" src scripts` | **comprobado (hash igual)** |
| H07 | `n8n/flujo.json` no es importable/ejecutable tal cual: `active:false` + 2 credenciales `REEMPLAZAR_CREDENCIAL` | script §6.7 | **comprobado** |
| H08 | El guard `needs_oof` sigue apuntando a `_p1_oof_cache.npz` y `test_audit_fixes.py:44-45` define un guard muerto | `grep -rn "@needs_oof\|_p1_oof_cache" tests` | **comprobado** |
| H09 | `src/clase/README.md` se contradice: afirma «No se descarta ningún campo» y arriba tabula 3 campos quitados | `grep -n "No se descarta" src/clase/README.md` | **comprobado** |
| H10 | `scripts/predict.py` (FD001) apunta a `models/v3_bundle.joblib`, inexistente | `sed -n '1,40p' scripts/predict.py`; `ls models/v3_bundle.joblib` | por verificar |
| H11 | `docs/assets/` duplica PNG de `resultados/` y ≥2 han divergido | bucle `cmp` de §6.3 | por verificar |
| H12 | La cobertura OOF se publica con dos precisiones (0.9012 vs 0.9016) sin rótulo de alcance | `grep -rn "0.9012\|0.9016" README.en.md MLProyectVault docs` | por verificar |
| H13 | PIA-4 cumple «todos los modelos» con 17 runs (5+4+4+4), pero alguna run no tiene tiempo (EMA5) | export + `mlruns/**/metrics` | por verificar |
| H14 | SAA-4: NB01 tiene los 5 tipos de gráfico, pero alguno no está comentado justo debajo | parse de celdas §6.5 | por verificar |
| H15 | SAA-7: los 4 MLP existen, pero la justificación por experimento no está en el código/notebook | `grep -n "EXPS" src/clase/train_mlp.py` | por verificar |
| H16 | SAA-9: el SHAP del modelo elegido se calcula con validación y no con test | `src/clase/shap_clase_e2.py` | por verificar |
| H17 | PIA-3: el joblib guardado contiene el pipeline completo y predice un caso nuevo | `joblib.load` + `named_steps` | por verificar |
| H18 | PIA-5: la `p` (RUL) aparece junto a la decisión en la misma vista | `grep -n "RUL p35\|L_inf\|st.metric" app/dashboard_ds02.py` | por verificar |
| H19 | MIA-2: 6 reglas de decisión + corrección, R1 seguridad con prioridad máxima | script §6.7 | por verificar |
| H20 | MIA-3: la rama HANGAR llama a la API propia y hay test que lo fija | `n8n/flujo.json` + `tests/test_n8n_propia.py` | por verificar |
| H21 | El import de `app/streamlit_app.py` **no** está cubierto por tests: el cambio sin commitear no tiene contrato | `grep -rn "streamlit_app" tests` | por verificar |
| H22 | `app/dashboard_ds02.py` y `app/ui_modulos/_tab_*.py` contienen **dos implementaciones** de la misma pestaña | comparar cabeceras y `grep -n "def render"` | por verificar |
| H23 | `resultados/auditoria-2026-11-10/*.csv` (auditoría previa) no está versionado y puede contradecir el estado actual | `git ls-files resultados/auditoria-2026-11-10` | **comprobado (vacío)** |
| H24 | La suite sigue con **1 skip** (`test_mia_rules.py:181`) y ningún fallo | `pytest -q -rs` | por verificar |
| H25 | `requirements.txt` y `pyproject.toml` están sincronizados (22 = 22) | script §6.2 | **comprobado** |
| H26 | Un `git archive HEAD` en directorio limpio **no** puede ejecutar la suite (faltan `data/`, `resultados/`, `app/cache` si no se versionan) | `git archive HEAD \| tar -x -C "$TMPDIR/clean"` + `pytest` | por verificar |

---

## 10. Señales ya observadas al planificar (candidatas a hallazgo, **no confirmadas como defecto**)

| ID | Señal | Por qué importa | Sev. preliminar |
| --- | --- | --- | --- |
| S-01 | `app/streamlit_app.py` modificado sin commitear (+17 líneas) | El estado auditado no es el de ningún commit; un clon no reproduce el comportamiento de la app | M |
| S-02 | El loader de secretos captura `(OSError, TOMLDecodeError)` y hace `pass` | Un TOML malformado deja la app sin webhook **en silencio**; el fallo es mudo en la superficie que importa (MIA-3) | M |
| S-03 | El loader muta `os.environ` globalmente al importar | Puede contaminar tests y otras importaciones del mismo proceso | B |
| S-04 | README (17) vs `src/clase/README` (13 en HEAD, 17 en árbol) vs export (17) | La corrección existe pero **no está commiteada**: un clon limpio sigue publicando 13 | A |
| S-05 | `src/clase/README` afirma «No se descarta ningún campo» y tabula 3 quitados | Contradicción interna en la primera página que lee el tribunal (SAA-3) | M |
| S-06 | `data/` y `resultados/` fuera de git | PIA-2 («estructura de carpetas») y la reproducibilidad desde clon quedan en evidencia solo local | A |
| S-07 | `models/mejor_modelo.joblib` sin escritor | Puede divergir del joblib real sin que nadie lo detecte (hoy son idénticos) | B |
| S-08 | `REEMPLAZAR_CREDENCIAL` ×2 y `active:false` | MIA-3 no puede declararse «flujo probado»; el 10 se sostiene en estructura + test | A (techo declarado) |
| S-09 | Guard `needs_oof` muerto + skip permanente | G1 pide cero skips; el skip está nombrado, pero el instrumento versionado no se usa | M |
| S-10 | `docs/assets/` duplica `resultados/` | Dos copias de la misma figura; una puede quedar caducada | B |
| S-11 | Auditorías previas con cifras que ya no aplican (109 `meta.yaml` → 19; 1761 → 1171 ficheros) | Un lector que abra `docs/pendiente/` se lleva datos falsos | M |
| S-12 | `resultados/auditoria-2026-11-10/` no versionado | El entregable de la auditoría anterior no viaja con el repo | B |

---

## 11. Registro de hallazgos

```csv
id,bloque,severidad,hallazgo,reproduccion,evidencia,impacto,propuesta,estado
```

- **Severidad:** C (invalida cifra/criterio/seguridad) · A (rompe el 10 o resta credibilidad) · M (incoherencia visible) · B (pulido).
- **Propuesta:** se redacta, **no se aplica**. Si exige reentrenar, se dice y se saca del alcance.
- Cada hallazgo con `path:línea` o comando + salida literal. Sin reproducción no entra en el informe.

---

## 12. Entregables (rutas exactas)

| # | Entregable | Ruta |
| --- | --- | --- |
| 1 | Este plan | `docs/plans/plan-auditoria-2026-11-10-rubrica-exhaustiva.md` |
| 2 | Informe | `docs/informes/auditoria-2026-11-10-rubrica-exhaustiva.md` |
| 3 | Criterios (20 filas) | `resultados/auditoria-2026-11-10-v2/criterios.csv` |
| 4 | Cobertura (1171 filas) | `resultados/auditoria-2026-11-10-v2/cobertura.csv` |
| 5 | Hallazgos | `resultados/auditoria-2026-11-10-v2/hallazgos.csv` |
| 6 | Hipótesis | `resultados/auditoria-2026-11-10-v2/hipotesis.csv` |
| 7 | Propuestas de arreglo (solo texto, dentro del informe) | sin fichero aparte: la auditoría **no crea ni aplica** ningún change |

El informe llevará, en este orden: veredicto · baseline · alcance · hipótesis resueltas · matriz de 20 celdas · notas ponderadas · hallazgos C/A/M/B · comparación con auditorías previas · límites · anexo de comandos · firma G5.

---

## 13. Orden de ejecución, duración y checkpoints

| Fase | Qué | Duración | Checkpoint |
| --- | --- | --- | --- |
| F0 | Baseline y hashes | 15 min | G0: sello y SHA |
| F1 | compileall, gates, suite, superficies, enlaces | 45 min | G1/G2 |
| F2 | Inventario y `cobertura.csv` | 60 min | G6: 1171 filas, 0 sin tier |
| F3 | SAA 1-10 | 90 min | 10 celdas con evidencia |
| F4 | PIA 1-6 | 75 min | 6 celdas con evidencia |
| F5 | MIA 1-4 | 60 min | 4 celdas con evidencia |
| F6 | Cifras, artefactos, seguridad, deuda | 90 min | G3: cadena de cada cifra |
| F7 | 2 jueces independientes | 60 min | discrepancias arbitradas |
| F8 | Síntesis y firma | 45 min | G5: árbol idéntico + informes |

**Total:** ~9 h de auditoría, sin cómputo pesado. Checkpoints humanos: tras F1 (¿sigue verde?), tras F2 (¿cuadra el universo?), tras F3-F5 (¿alguna nota depende de un artefacto local?), antes de F8 (¿los jueces coinciden?).

---

## 14. Riesgos y mitigación

| Riesgo | Impacto | Mitigación |
| --- | --- | --- |
| Árbol con 1 fichero sin commitear | El estado no es reproducible | Se congela en F0 y se audita; se declara en el veredicto |
| `data/` y `resultados/` solo en local | Falsos «PASA» de reproducibilidad | H03/H26; todo lo que dependa de datos locales se marca límite |
| Store MLflow podado (19 `meta.yaml`) | PIA-4 cambia de base | Se audita el store **actual** y se contrasta con el export de 17 |
| n8n sin ejecución real | MIA-3 no demuestra acción | Techo declarado; estructura + test + acción novedosa |
| Notebooks con outputs de otro entorno | Cifras no reproducibles | Se comparan con CSV/manifiesto; se rotula |
| Jueces contaminados por el mismo transcript | Sesgo de confirmación | J1/J2 no se leen; arbitraje con comando |
| Arreglar durante la auditoría | Rompe G5 | Prohibido; propuesta separada |
| Nota inflada por cercanía | Informe no defendible | Anclas estrictas; «la nota se baja, no se negocia» |

---

## 15. Reglas de honestidad y antipatrones (recordatorio operativo)

1. **Evidencia o no existe.** Sin `path:línea`/comando/hash, no hay afirmación.
2. **Separar «funciona» de «lo demuestra».** Un modelo puede predecir bien y el repo no poder probarlo desde un clon.
3. **No confundir granos.** Fila (7.72 / 11.03) y ventana (4.338) no se comparan; el informe lo dice al lado de cada cifra.
4. **NASA es suma.** No se compara entre conjuntos con distinto número de filas.
5. **Cifras históricas rotuladas**, no borradas.
6. **Un skip nombrado** sigue siendo un skip: se cuenta y se explica.
7. **No reentrenar para «verificar»**.
8. **No maquillar** el techo de n8n ni la ausencia de datos en el clon.

---

## 16. Anexo — comandos de referencia rápida

```bash
# Identidad y estado
git rev-parse --abbrev-ref HEAD; git rev-parse HEAD
git status --porcelain --untracked-files=all | wc -l

# Conteos del universo
git ls-files | wc -l
git ls-files | awk -F/ '{print ($2=="" ? "(raiz)" : $1)}' | sort | uniq -c | sort -rn

# Gates
.venv/Scripts/python.exe -m compileall -q src app scripts tests; echo $?
.venv/Scripts/python.exe scripts/freeze_rules_evidence.py; echo $?
.venv/Scripts/python.exe scripts/freeze_oof_instrument.py --check; echo $?
.venv/Scripts/python.exe scripts/backfill_mlflow.py --check; echo $?
.venv/Scripts/python.exe -m pytest tests -q -rs -p no:cacheprovider; echo $?

# Cifras y artefactos
sha256sum models/*.joblib models/*.keras models/ds02_manifest.json
.venv/Scripts/python.exe -c "import json;print(json.load(open('models/ds02_manifest.json'))['metrics'])"
.venv/Scripts/python.exe -c "import json;print(json.load(open('app/cache/cache_manifest.json'))['metrics'])"

# Docstrings públicas
.venv/Scripts/python.exe -m pydocstyle src app 2>/dev/null | head -40

# n8n
.venv/Scripts/python.exe -c "import json;d=json.load(open('n8n/flujo.json'));print(d['active'],len(d['nodes']))"

# Secretos y datos personales
git ls-files | grep -Ei 'secret|token|\.env|registros|respaldo|\.bak|\.pem|\.key' || echo "ninguno versionado"
```

---

## Conexiones

- Rúbrica: `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (págs. 1-9).
- Framework: `docs/framework_auditoria.md` (A-Q, F0-F6, G0-G6).
- Plan e informe previos: `docs/plans/plan-auditoria-2026-11-10-rubrica-post-cierre.md` · `docs/informes/auditoria-2026-11-10-rubrica-post-cierre.md`.
- Cifras autoritativas: `models/ds02_manifest.json` (manda) · `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md`.
- Deuda: `docs/pendiente/pendientes-2026-11-10-post-auditoria.md` · `docs/pendiente/deuda-riesgo-7-2026-11-10.md`.
- Defensa: `docs/defensa/guiones-15min.md` · `docs/chuleta-defensa.md`.
