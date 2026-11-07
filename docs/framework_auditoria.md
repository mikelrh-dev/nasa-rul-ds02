# Framework de auditoría — integral, verificable y reutilizable

> **Qué es:** el método con el que se audita un proyecto de IA/ML de punta a punta
> sin reescribir el plan cada vez. Los bloques A–Q son el checklist; las fases
> F0–F6 son el orden de ejecución; las plantillas son la salida.
>
> **Cómo se usa:** se rellena la tabla de parametrización (§0.1), se congelan las
> variables en F0 y se recorren los bloques marcando cada punto con evidencia
> (`path:línea` o comando con salida). Nada se da por bueno «porque los tests
> pasan».
>
> **Versión:** 1.0 · 2026-11-07 · nacido del proyecto N-CMAPSS DS02 (rama
> `clase-modelo-c`), pero independiente de él.

---

## 0. Contrato de la auditoría

### 0.1 Parametrización (rellenar antes de empezar)

| Variable | Valor en este repo | Para qué |
| --- | --- | --- |
| `REPO` | raíz del repositorio | todo se resuelve desde aquí |
| `STACK` | Python 3.12 · TF/Keras · LightGBM · scikit-learn · FastAPI · Streamlit | qué se instala y cómo se ejecuta |
| `PY` | `.venv/Scripts/python.exe` (Windows) | intérprete único de la auditoría |
| `TEST_CMD` | `python -m pytest tests -q -rs` | puerta G1 |
| `BUILD_CMD` | `docker compose build` | puerta G1 (opcional si hay Docker) |
| `ARTIFACTOS` | `models/ensemble.joblib`, `bilstm_ds02.keras`, `scaler.joblib`, `ds02_manifest.json` | tier C y puerta G3 |
| `MANIFIESTO` | `models/ds02_manifest.json` | fuente de cifras y hashes |
| `CIFRAS_AUTORITATIVAS` | `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md` | cruce número a número |
| `SERVICIOS` | API `:8000`, dashboard `:8501`, n8n | bloque J/L |
| `DATASET` | `data/raw/…h5` (~2,3 GB, fuera de git) | bloque E (no se versiona) |

### 0.2 Reglas de oro

1. **Solo lectura.** La auditoría no arregla, no commitea, no reentrena, no
   publica y no toca `models/`, `archive/` ni datos. Si encuentra un fallo,
   lo documenta con reproducción y una propuesta; el arreglo es otro trabajo.
2. **Evidencia o no existe.** Cada afirmación del informe lleva `path:línea`,
   comando + salida literal, o hash. «Lo he mirado» no es evidencia.
3. **Hipótesis antes de mirar.** Las sospechas se escriben y se fechan antes de
   comprobarlas, para que el informe no se redacte a conveniencia. Una hipótesis
   refutada se reporta como refutada.
4. **Lo que no se puede probar se declara límite**, no se maquilla como aprobado.
5. **La nota se baja, no se negocia.** Si un criterio exige X y solo hay Y, la
   nota es la de Y.
6. **Separar «funciona» de «lo demuestra».** Un modelo puede predecir bien y el
   repositorio no poder demostrarlo desde un clon limpio.
7. **Un solo intérprete y un solo comando de test.** Mezclar entornos produce
   hallazgos falsos (y tapa los verdaderos).

### 0.3 Alcance explícito

El informe abre con tres listas y no se sale de ellas:

- **Dentro:** qué se audita (bloques, rutas, criterios).
- **Fuera:** qué no (reentrenar, re-leer test, credenciales reales, desplegar).
- **Dependencias externas:** qué exige un servicio vivo y qué techo impone si no
  está disponible (p. ej. sin instancia n8n, MIA-3 máximo justificable = 7 con
  evidencia estática).

---

## 1. Fases y puertas

| Fase | Qué se hace | Salida | Duración típica |
| --- | --- | --- | --- |
| **F0** | Congelar baseline: commit, árbol, hashes, entorno | bloque de trazabilidad | 15 min |
| **F1** | Mecánica: compila, suite, servicios arrancan, enlaces vivos | puertas G1–G2 | 40 min |
| **F2** | Inventario y cobertura (A) + código y arquitectura (B–D) | `cobertura.csv` | 90 min |
| **F3** | Datos, modelo, métricas y artefactos (E–H) | matriz de cifras | 90 min |
| **F4** | Decisión, API/seguridad, UI, integraciones (I–L) | pruebas de superficie | 90 min |
| **F5** | Tests, documentación, negocio, ética, deuda (M–Q) | hallazgos transversales | 60 min |
| **F6** | Síntesis: notas, severidad, límites, anexos | informe + CSV | 45 min |

**Puertas (si fallan, se para o se degrada la conclusión):**

| Puerta | Condición | Si falla |
| --- | --- | --- |
| **G0** | Baseline congelado (commit + `git status` + hashes) | no se auditan cifras |
| **G1** | Compila y la suite ejecuta; los skips son los esperados y están nombrados | hallazgo Crítico antes de seguir |
| **G2** | Toda figura, enlace y ruta citada existe y se abre | hallazgo Alto por enlace roto |
| **G3** | Toda cifra publicada es rastreable a manifiesto/CSV/test | hallazgo Crítico o Alto según cifra |
| **G4** | Cada criterio tiene evidencia para su nota | se baja la nota, no se maquilla |
| **G5** | La auditoría no modificó nada (`git status` idéntico a F0) | el informe no se publica |
| **G6** | `cobertura.csv` reconcilia el universo y ningún archivo queda sin tier | hallazgo Alto de cobertura |

---

## 2. F0 — Baseline obligatorio

```bash
git rev-parse HEAD
git status --porcelain
git log -1 --format='%H %ad %s' --date=iso
sha256sum models/* 2>/dev/null | head -40
python - <<'PY'
import json, hashlib, pathlib
p = pathlib.Path("models/ds02_manifest.json")
d = json.loads(p.read_text())
print("manifest_sha256:", hashlib.sha256(p.read_bytes()).hexdigest())
print("artifacts:", json.dumps(d.get("artifacts", d), indent=2)[:2000])
PY
```

- Si el árbol está sucio, el informe **fija el commit y la lista de archivos
  modificados** y audita ese estado. No se finge un commit limpio que no existe.
- Se registra la versión de Python y de las dependencias clave (`pip freeze` o
  el fichero pineado). Un artefacto solo es reproducible en su entorno.
- **G0:** si un SHA no coincide con manifiesto y caché, se detiene la auditoría
  de cifras y se reporta antes de seguir.

---

## 3. Bloques de auditoría, punto por punto

Cada bloque se puntúa igual: **PASA / PASA CON RESERVAS / FALLA / NO VERIFICABLE**,
y cada punto lleva su evidencia. «NO VERIFICABLE» es una respuesta legítima; el
silencio no.

### A. Inventario y cobertura

*Pregunta: ¿existe un mapa completo de lo que hay, y se ha clasificado todo?*

1. Universo total reconciliado: `git ls-files | wc -l` + no versionados
   relevantes. El número del informe debe cuadrar con el comando.
2. Tiers excluyentes por prioridad **C > B > A**:
   - **A (leer entero):** código que produce o demuestra algo (`src/`, `app/`,
     `tests/`, `scripts/`, `notebooks/`, configuración raíz).
   - **B (cotejar por afirmaciones):** documentación derivada (`docs/`,
     `openspec/`, vault, `archive/`).
   - **C (verificar por huella):** binarios, imágenes, joblib, parquet, logs.
   - Los `.ipynb` se inspeccionan como JSON de celdas, nunca como binarios.
3. `cobertura.csv` con una fila por archivo: `path,tier,veredicto,evidencia`.
4. Ningún archivo sin tier; toda exclusión con motivo escrito.
5. Duplicados y alias (`mejor_modelo.joblib` vs `mejor_modelo_clase.joblib`):
   ¿quién los escribe?, ¿se regeneran solos?, ¿cuál es el contrato?
6. Archivos huérfanos: código que nadie importa, docs que nadie enlaza, scripts
   de una generación anterior conviviendo con la vigente.

### B. Entorno y reproducibilidad

*Pregunta: ¿se puede reproducir lo declarado en una máquina limpia?*

1. `requires-python` coherente con la realidad (pyproject vs `.python-version` vs
   CI vs Docker).
2. Dependencias **pineadas** y sin duplicidad divergente entre `pyproject.toml` y
   `requirements.txt`.
3. Instalación reproducible: `pip install -r requirements.txt` + `pip install -e .`
   (y por qué el `-e` es o no obligatorio).
4. Imports que solo funcionan por `sys.path.insert`: se localizan y se decide si
   son contrato o deuda.
5. Arranque real de cada superficie: API (`/health`), dashboard, CLI.
6. `PYTHONHASHSEED`, semillas y determinismo declarado (incluido lo que **no** es
   determinista, p. ej. una rama LSTM; se documenta, no se esconde).
7. Rutas relativas vs absolutas y comportamiento en Windows y Linux.
8. Variables de entorno documentadas y con default seguro (`.env.example`).

### C. Build, empaquetado y despliegue

*Pregunta: ¿lo que se despliega es lo que se audita?*

1. `Dockerfile`: base fijada, dependencias del sistema (p. ej. `libgomp1`),
   usuario no-root, `.dockerignore`, tamaño de contexto.
2. `docker-compose.yml`: puertos publicados, volúmenes de solo lectura,
   `depends_on` con healthcheck, secretos fuera del compose.
3. Exposición de red: `0.0.0.0` solo detrás de proxy TLS; loopback por defecto.
4. Healthchecks reales (devuelven 200 cuando el modelo está cargado).
5. El artefacto que se copia a la imagen es el mismo que se verificó por hash.
6. CI: versión de Python, instalación pineada, comando de test, artefactos
   congelados y **prohibición de reentrenar** en CI.
7. Reconstrucción desde cero: ¿el build pasa hoy o depende de caché local?

### D. Código y arquitectura

*Pregunta: ¿el código dice lo que hace y falla de forma audible?*

1. `compileall` sin errores y sin warnings relevantes.
2. Fronteras entre capas: datos → features → modelo → decisión → superficie.
   ¿Hay imports invertidos o capas que se saltan?
3. Duplicación de lógica crítica (dos implementaciones de la misma métrica, dos
   bandas, dos campeones): se busca explícitamente y se marca cuál manda.
4. Manejo de errores: `except` desnudos, `pass` silencioso, `NotImplementedError`
   en rutas que la UI llama.
5. Validación de entrada en cada frontera (no solo en la UI).
6. Mutabilidad global y estado compartido (`_cache` de módulo, singletons) y su
   efecto en tests concurrentes.
7. Docstrings en API pública y coherencia con la firma.
8. `TODO/FIXME/HACK/pendiente` inventariados y clasificados: ¿deuda declarada o
   promesa incumplida?
9. Nombres y unidades: `rul` en ciclos, no en días; umbrales con unidad explícita.
10. Dead code y compatibilidad hacia atrás sin dueño.

### E. Datos y fuga de información

*Pregunta: ¿el modelo aprende del fenómeno o del contador?*

1. Partición por **grupo físico** (motor/unidad), nunca por fila. Se verifica en
   el código, no en el README.
2. Construcción de la etiqueta: la RUL se calcula una vez y nunca se inyecta como
   feature.
3. Features derivadas del futuro: ventanas centradas, `ffill`/`bfill` no causal,
   normalización ajustada con test, medias globales que incluyen test.
4. `cycle` como predictor: se mide su aporte y se decide con ablación.
5. Nulos: patrón (MCAR/MAR/MNAR) justificado con evidencia, imputación declarada y
   su efecto medido. Nulos inyectados ≠ nulos reales: decirlo.
6. Duplicados, rangos físicamente imposibles y outliers: qué se hace con ellos.
7. Split train/dev/test congelado y **una sola lectura** del test; si se releyó,
   se declara.
8. Tamaño y procedencia del dataset: qué está en git y qué se regenera; hashes de
   los ficheros procesados.
9. Fuga por identificador: `unit` no entra como feature; se comprueba.
10. Reproducibilidad del preprocesado: el mismo input produce el mismo output.

### F. Modelo y metodología

*Pregunta: ¿las decisiones de modelado están medidas o son folclore?*

1. Baseline honesto antes del modelo complejo (media, mediana, lineal, árbol).
2. Selección por validación; el test solo confirma.
3. Validación agrupada y out-of-fold cuando hay stacking: el meta-learner no ve
   predicciones in-sample.
4. Ablaciones documentadas: cada componente (canal extra, smoothing, shrinkage,
   residualización) con y sin él, misma métrica.
5. Hiperparámetros registrados y buscados con el mismo protocolo.
6. Estabilidad entre semillas: media **y** desviación; se dice qué diferencia es
   ruido.
7. Métrica alineada con el coste: RMSE para fallos gordos, MAE para error medio,
   asimetría del negocio (subestimar RUL es peor que sobreestimar).
8. Bandas/intervalos: cobertura empírica medida, no supuesta; calibración
   separada de la del despliegue y rotulada como tal.
9. Sesgo por subgrupo: el error no está repartido (macro-RMSE por unidad). Se
   publica el peor caso, no solo la media.
10. Limitaciones del modelo escritas: dominio, extrapolación, datos que no vio.

### G. Métricas, cifras y trazabilidad

*Pregunta: ¿cada número publicado sale de un artefacto?*

1. Pirámide de fuentes: artefacto/manifiesto → CSV de resultados → test →
   README/notebooks/docs.
2. Cruce número a número: RMSE, MAE, R², score compuesto, número de filas,
   número de ventanas, semillas.
3. Un score que es **suma** no se compara entre conjuntos con distinto número de
   filas; el informe lo dice al lado del número.
4. Redondeos: se publica lo mismo que mide el artefacto (o se declara el
   redondeo).
5. Cifras históricas marcadas como históricas, no borradas; una tabla vieja sin
   rótulo es un hallazgo.
6. Contradicciones entre README, notebook, informe y CSV: se listan todas, con
   la fuente que manda.
7. Cifras en presentaciones/chuletas/guiones: también se cruzan.
8. Ninguna cifra «de memoria»: si no está en un fichero, no se publica.

### H. Artefactos y procedencia

*Pregunta: ¿el binario que sirve es el que se entrenó y se verificó?*

1. Manifiesto con: versión, fecha, semilla, partición, features, métricas y
   SHA-256 de cada artefacto.
2. Verificación de hash **antes** de deserializar (`joblib`, `keras`).
3. `load_*` único: nadie carga un joblib por su cuenta saltándose la verificación.
4. Escritor declarado por artefacto (`script:función:línea`) y comando para
   regenerarlo; si un artefacto no tiene escritor, se marca como copia manual.
5. Caché derivada (`app/cache/`) con su propio manifiesto y sello del manifiesto
   fuente: si divergen, la app sirve algo que el manifiesto no describe.
6. Guardas de deserialización: allowlist de rutas, rechazo de rutas absolutas
   fuera del repo, `joblib` con `mmap` desactivado si aplica.
7. Tamaños y fechas coherentes entre artefacto, manifiesto y commit.
8. Artefactos legacy (FD001, `v3_*`) separados y rotulados; jamás citados como
   vigentes.

### I. Reglas y lógica de decisión

*Pregunta: ¿la decisión es determinista, priorizada y auditable?*

1. Conteo real de reglas y su tipo (corrección vs decisión), contra el requisito.
2. Prioridad explícita y una sola aplicación por pasada; sin contradicciones
   simultáneas.
3. Regla de seguridad por encima de todo: dato imposible → no se decide, con
   motivo legible.
4. Casos límite cubiertos: faltan umbrales, umbrales invertidos, `NaN`,
   `None`, unidad desconocida.
5. Traza: cada ficha guarda qué regla actuó y por qué.
6. Umbrales en un solo sitio y con unidad; cambiarlos no exige tocar código en
   tres archivos.
7. Coherencia banda → decisión: se decide sobre el límite inferior, no sobre el
   punto.
8. Test que ata los números congelados a la evidencia (gate de reglas).

### J. API y seguridad

*Pregunta: ¿la superficie de servicio aguanta lo que promete?*

1. Contrato: esquema de entrada/salida, códigos de error, versión.
2. Validación estricta: rangos, tipos, `NaN`/`Inf` rechazados explícitamente.
3. Autenticación opcional pero real (`hmac.compare_digest`, no `==`).
4. Rate limiting y su semántica (por IP, ventana fija, memoria compartida).
5. CORS restringido; cabeceras de seguridad en todas las respuestas.
6. `docs/openapi` desactivados en producción; `/health` público y barato.
7. Secretos por entorno, sin default peligroso y sin eco en logs.
8. Errores que no filtran rutas internas ni stack traces.
9. Carga del modelo en `lifespan`, con fallo ruidoso si el hash no cuadra.
10. Prueba real: `curl` de `/health`, `/predict` sin clave, con clave, con payload
    inválido y con exceso de peticiones.

### K. UI / UX

*Pregunta: ¿la pantalla dice la verdad y aguanta al usuario?*

1. Arranque limpio del entry point declarado; pestañas que existen de verdad.
2. Estados vacíos, de error y de carga; nunca una excepción cruda en pantalla.
3. Números de la UI = números del artefacto (misma fuente, no copia).
4. Ninguna captura o promesa en README que la app no muestre.
5. Accesibilidad básica: contraste, etiquetas, unidades visibles.
6. Persistencia (registros de sesión) con escritura atómica y sin corrupción.
7. Rendimiento percibido: caché de datos/modelo, no recomputar en cada rerun.
8. Coherencia de vocabulario con el negocio (APTO/INSPECCIÓN/HANGAR, no jerga).

### L. Integraciones (n8n y terceros)

*Pregunta: ¿el flujo existe, hace algo distinto por rama y está probado?*

1. JSON válido e importable; nodos, conexiones y credenciales referenciadas.
2. Webhook con autenticación y payload con contrato explícito.
3. Una rama por decisión y **acción distinta** por rama.
4. Estado real (`active: false`) y qué implica.
5. Idempotencia, reintentos y qué pasa si el destino cae.
6. Datos personales en el payload: minimización y retención.
7. Distinguir «estructura válida» de «flujo ejecutado»; sin instancia viva, el
   techo de nota se declara.

### M. Tests y calidad de la suite

*Pregunta: ¿la suite prueba el contrato o solo el camino feliz?*

1. Suite completa ejecutada hoy, con salida y código de salida preservados.
2. Skips nombrados y esperados; un skip nuevo es hallazgo, no ruido.
3. Contrato vs implementación: hay tests que fallarían si el artefacto cambia.
4. Tests de borde: nulos, unidades vacías, umbrales invertidos, payload inválido.
5. Tests que dependen de caché externa y se saltan en silencio: se declaran.
6. Determinismo de los tests (semillas, orden, red).
7. Tiempo de suite razonable y sin reentrenar.
8. Cobertura declarada con honestidad (0 % declarado es mejor que 100 % falso).

### N. Documentación y consistencia editorial

*Pregunta: ¿se puede seguir el proyecto leyendo, desde cero?*

1. README de raíz: qué es, para qué, cómo se ejecuta, qué mide y qué no.
2. Un solo «campeón» vigente; lo histórico rotulado y separado.
3. Enlaces internos y figuras: todos abren (G2).
4. Diagramas coherentes con el código (nombres de módulos y flujo real).
5. READMEs de subcarpeta con su contrato (`models/`, `scripts/`, `src/clase/`).
6. ADRs con decisión, alternativas rechazadas y consecuencia.
7. Idioma y tono consistentes; sin promesas de futuro escritas como presente.
8. Fecha y versión de cada informe; lo caducado se marca, no se borra.

### O. Negocio, coste y riesgo

*Pregunta: ¿el número se traduce en una decisión que alguien pagaría?*

1. Dato de coste con fuente y **credibilidad declarada**; rango, no falsa
   precisión.
2. Qué decisión cambia el sistema y quién la toma.
3. Umbrales traducidos a consecuencia (parada no planificada vs inspección).
4. Cálculo de retorno reproducible (una parada evitada al año).
5. Riesgo de falsos negativos (motor que vuela cuando no debe) y su mitigación.
6. Dependencias operativas: quién mantiene, qué pasa si el modelo envejece.
7. Plan de monitorización y deriva (PSI u otro), con umbral de actuación.

### P. Ética, legal y límites de la IA

*Pregunta: ¿el sistema declara lo que no puede hacer?*

1. Tipo de IA y por qué no transfiere fuera de su dominio.
2. Datos personales, licencias del dataset y condiciones de uso.
3. Traza de decisiones automatizadas y posibilidad de revisión humana.
4. Sesgos conocidos por subgrupo/unidad y su comunicación.
5. Limitaciones escritas en el sitio donde se usa, no enterradas en un anexo.
6. Reproducibilidad como requisito ético: sin ella no hay rendición de cuentas.

### Q. Operación, mantenibilidad y deuda

*Pregunta: ¿esto se puede mantener seis meses sin el autor original?*

1. Tiempo de arranque en frío y de una predicción; cuello de botella.
2. Dependencias abandonadas o con versión imposible (p. ej. pin que no existe).
3. Puntos únicos de fallo (un joblib, una caché, una credencial).
4. Deuda inventariada con coste estimado y prioridad, no una lista de deseos.
5. Onboarding: de clonar a predecir en cuántos pasos y cuántos fallan.
6. Rollback: cómo se vuelve a la versión anterior del artefacto.
7. Registro de cambios y quién decide qué se despliega.

---

## 4. Severidad y veredicto

**Escala (comparable entre auditorías):**

| Nivel | Criterio | Efecto |
| --- | --- | --- |
| **C — Crítico** | Invalida una cifra publicada, un criterio entero o la seguridad | Bloquea la conclusión de ese bloque |
| **A — Alto** | Resta credibilidad o rompe el nivel máximo de un criterio | Se reporta antes que el resto |
| **M — Medio** | Inconsistencia que un lector atento detectaría | Se corrige en la siguiente iteración |
| **B — Bajo** | Pulido, enlaces, redacción | Se agrupa en un anexo |

Cada hallazgo lleva: **ID · bloque · severidad · síntesis · reproducción ·
evidencia · impacto · propuesta (no aplicada)**.

**Veredicto por bloque:** PASA / PASA CON RESERVAS / FALLA / NO VERIFICABLE.
El veredicto global es la peor puerta fallida, no el promedio.

---

## 5. Plantillas de salida

### 5.1 Hallazgos

```markdown
| ID | Bloque | Sev. | Hallazgo | Reproducción | Evidencia | Impacto | Propuesta |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | G | C | README publica 4.368 y el manifiesto dice 4.338 | `grep -n 4.368 README.md` | `README.md:112` vs `models/ds02_manifest.json:…` | cifra no trazable | alinear con manifiesto |
```

### 5.2 Matriz de criterios (si hay rúbrica)

```markdown
| # | Criterio | Peso | Nota (0/3/7/10) | Evidencia | Qué falta para el 10 |
| --- | --- | --- | --- | --- | --- |
```

### 5.3 Cobertura

```csv
path,tier,veredicto,evidencia
src/ds02_rul/model.py,A,leido,"contrato de predicción; sin fuga"
docs/informes/README.md,B,cotejado,"índice completo; fechas correctas"
models/bilstm_ds02.keras,C,hash_ok,"sha256 coincide con manifiesto"
```

### 5.4 Estructura del informe

1. Pregunta de auditoría y criterio de éxito.
2. Baseline (commit, árbol, hashes, entorno).
3. Alcance: dentro / fuera / dependencias externas.
4. Hipótesis y su veredicto (confirmada / refutada).
5. Resultado por bloque (A–Q), con veredicto y evidencia.
6. Hallazgos ordenados por severidad.
7. Notas por criterio (si hay rúbrica) y techo justificado.
8. Límites de la propia auditoría.
9. Anexo: comandos y salidas literales.
10. Firma de no modificación (`git status` idéntico a F0).

---

## 6. Comandos de referencia

```bash
# F0 — baseline
git rev-parse HEAD && git status --porcelain
sha256sum models/*.joblib models/*.keras models/*.json

# F1 — mecánica
python -m compileall -q src app scripts tests
python -m pytest tests -q -rs -p no:cacheprovider
echo "exit=$?"

# F1 — inventario
git ls-files | wc -l
git ls-files docs/assets | wc -l
git ls-files resultados | wc -l

# F1 — superficies
curl -fsS http://127.0.0.1:8000/health
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8501

# F3 — cifras
grep -RIn "RMSE\|R²\|R2\|NASA" README.md docs/ src/ | head -100
python - <<'PY'
import json
d = json.load(open("models/ds02_manifest.json"))
print(json.dumps(d, indent=2)[:3000])
PY

# F4 — seguridad de API
curl -s -X POST localhost:8000/predict -H 'content-type: application/json' -d '{}'
curl -s -X POST localhost:8000/predict -H 'content-type: application/json' \
     -d '{"unit": 11, "window": 0}' -H "X-API-Key: $DS02_API_KEY"
```

> En Windows con Git Bash, `python` debe ser el del venv
> (`.venv/Scripts/python.exe`). Un `python` del sistema convierte la auditoría
> en una medición de otro entorno.

---

## 7. Antipatrones (cómo se maquilla un informe)

- **Verde por suite:** «pasan los tests» sin decir que el test no toca el
  artefacto ni la cifra discutida.
- **Skip silencioso:** saltarse tests que exigen caché y contarlos como éxito.
- **Promedio que esconde el fallo:** publicar la media sin el peor subgrupo.
- **Captura caducada:** una imagen que ya no corresponde al modelo desplegado.
- **Dos fuentes de verdad:** README y manifiesto discrepan y se elige la cómoda.
- **Reentrenar para «verificar»:** mueve las cifras y destruye la comparación.
- **Arreglar durante la auditoría:** invalida la línea base y la puerta G5.
- **Nota inflada por cercanía:** puntuar la intención y no la evidencia.

---

## 8. Checklist de cierre

- [ ] F0 congelado: commit, `git status`, hashes, entorno.
- [ ] `compileall` limpio y suite ejecutada con su código de salida.
- [ ] Skips nombrados y esperados (o hallazgo).
- [ ] Superficies arrancadas: API, dashboard, CLI.
- [ ] `cobertura.csv` reconciliado; 0 archivos sin tier.
- [ ] Bloques A–Q recorridos con veredicto y evidencia.
- [ ] Toda cifra publicada cruzada con su fuente.
- [ ] Toda figura y enlace abierto (G2).
- [ ] Hipótesis resueltas, incluidas las refutadas.
- [ ] Hallazgos con severidad, reproducción y propuesta.
- [ ] Límites declarados (servicios sin credenciales, binarios no legibles…).
- [ ] `git status` idéntico al de F0 (G5).
- [ ] Informe con veredicto por bloque y global.

---

## 9. Instanciación en este repositorio (N-CMAPSS DS02)

Rutas que el framework debe mirar aquí, sin sustituir los bloques:

| Bloque | Dónde mirar |
| --- | --- |
| A | `git ls-files`, `app/`, `src/{clase,ds02_rul,mia}`, `tests/`, `scripts/`, `notebooks/`, `docs/`, `MLProyectVault/`, `archive/` |
| B | `pyproject.toml`, `requirements.txt`, `.python-version`, `.venv`, `.github/workflows/ci.yml` |
| C | `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.github/workflows/ci.yml` |
| D | `src/ds02_rul/*`, `src/clase/*`, `app/ui_modulos/*`, `src/utils.py`, `src/reglas.py` |
| E | `src/clase/dataset_clase.py`, `src/ds02_rul/{data,features,residualizer,pipeline}.py`, `data/processed/auditoria_nulos.json` |
| F | `src/ds02_rul/{model,stacking,ensemble,smoothing,conformal,metrics}.py`, `src/clase/train_*` |
| G | `models/ds02_manifest.json`, `resultados/*.csv`, `README.md`, `docs/informes/`, `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md` |
| H | `models/README.md`, `src/ds02_rul/persistence.py`, `app/cache/cache_manifest.json` |
| I | `src/mia/{reglas,motor,casos,modelo}.py`, `src/mia/calibracion_banda.json`, `models/alarm_policy.json` |
| J | `app/api.py`, `tests/test_security_api.py` |
| K | `app/{dashboard_ds02,streamlit_app,ui_*}.py`, `app/ui_modulos/*`, `app/registros_sesiones*` |
| L | `n8n/`, `src/n8n.py`, `app/ui_n8n.py`, `tests/test_n8n_decision.py` |
| M | `tests/` (37 ficheros), `scripts/verify_gate.py`, `scripts/freeze_rules_evidence.py` |
| N | `README.md`, `README.en.md`, `docs/`, `openspec/`, `src/clase/README.md`, `scripts/README.md` |
| O | `costes_reales_aeronauticos.md`, `docs/informe_estrat_gico_y_arquitectura_mro_ds02.md`, `models/psi_reference.json` |
| P | `README.md` («Qué hemos construido»), ADRs, `docs/defensa/` |
| Q | `docs/pendiente/`, `docs/plans/`, `archive/`, `models/legacy/` |

**Cifras vigentes que cualquier auditoría debe reconciliar con el manifiesto:**
RMSE 4.338 · MAE 3.227 · R² 0.9461 · NASA 2336.2 (semilla 42, bundle C);
multisemilla 4.368 ± 0.053 · NASA 2355.2 ± 24.6 ([42, 7, 123]);
macro-RMSE por motor 5.0153 (U11 3.6328 · U14 8.5761 · U15 2.8371).
Si el manifiesto dice otra cosa, **manda el manifiesto**.

**Puertas específicas de este repo:**

- G0 incluye `manifest_sha256` de `app/cache/cache_manifest.json` contra el
  SHA real de `models/ds02_manifest.json`.
- G1 espera que los únicos skips sean los que exigen `_p1_oof_cache.npz`.
- G3 incluye la lista negra de cifras de `e00-cifras-autoritativas.md`.
- MIA-3 sin instancia n8n: techo 7, declarado.

---

## 10. Cómo adaptar el framework a otro proyecto

1. Rellenar §0.1 con el stack y los comandos reales.
2. Sustituir §9 por la tabla de rutas del nuevo repo (misma estructura A–Q).
3. Mantener intactos los bloques, la severidad y las puertas: son el método.
4. Si el proyecto no tiene rúbrica, eliminar §5.2 y puntuar solo por bloque.
5. Si no hay servicio desplegado, J/L se marcan «NO VERIFICABLE» con motivo —
   nunca «PASA».
6. Versionar este documento y anotar en cada auditoría qué versión del framework
   se usó.
