# Plan de corrección del Reto 1 — 2026-11-06

**Origen:** `docs/informes/auditoria-2026-11-06-reto1-v2.md`
**Alcance:** cierra C1, A1, A2, A3, M1, M2, M3 y B1, más SAA-3.
**Excluido por decisión:** MLflow (C2/PIA-4) y n8n (A4/M4).
**Revisión 2:** tras medir mtimes, **P1 no re-ejecuta ningún notebook** (ver P1).

---

## 1. Reglas de la corrección

1. **El bundle C no se toca.** `models/` es de solo lectura; ninguna ficha lo abre
   para escribir. Su SHA `d6c701…` y su fila 4.338 no cambian. (`ds02_manifest.json`
   ya trae un diff previo de +38/−1 al empezar; se deja como está.)
2. **El test (uds 11/14/15) no se vuelve a medir.** Las cifras de test se citan,
   no se recalculan.
3. **Las bandas no se recalibran.** `calibracion_banda.json` y `conformal` quedan
   como están.
4. **Ninguna semilla se reentrena para «arreglar» una cifra.** Reentrenar mueve el
   resultado ±0,05 y multiplica las versiones del número.
5. **Una cifra, una fuente.** Si una ficha cambia un número, actualiza en el mismo
   commit la fuente que lo produce y toda la prosa que lo cita.
6. **Nada de `git push` ni despliegues.** Los commits son locales.

---

## 2. Orden y coste

| # | Ficha | Hallazgo | Tiempo | Riesgo |
| --- | --- | --- | --- | --- |
| P0 | Congelar el árbol actual | M2 | 15 min | 1 |
| P1 | Reconciliar multiseed (doc + 2 celdas) | C1 | 30 min | 2 |
| P2 | Versionar `docs/assets` | A1 | 5 min | 0 |
| P3 | Captura de la app en el README | A2 | 20 min | 2 |
| P4 | Tabla de campos en el README raíz | SAA-3 | 20 min | 1 |
| P5 | La tabla no elige campeón por test | A3 | 30 min | 2 |
| P6 | Comentario de la guarda de banda | M3 | 10 min | 0 |
| P7 | Salidas sin sello (opcional) | M1 | 10 min | 1 |

**Total: ~2 h 20 min, sin cómputo de entrenamiento.**

---

## P0 · Congelar el árbol (M2)

**Problema.** 49 modificados + 12 sin seguimiento; el informe audita un estado que
git no conserva.

**Línea base de artefactos (no cambia en ninguna ficha).**

| Artefacto | SHA-256 esperado |
| --- | --- |
| `models/ensemble.joblib` | `d6c701429eed8623a9d900d922aca1922427d08ff8b4ec00604b8116c1a952dd` |
| `models/bilstm_ds02.keras` | `bf9620a7de3bf9f8efa65c1993a96d8a95b903dc6fde72c772aa316f4c042219` |
| `models/ds02_manifest.json` | `1085dd67aed8179174996f3939bd7715f757f954a822d440a093dd847d3eb8c9` |

`models/ds02_manifest.json` ya viene modificado (+38/−1) al inicio; la puerta no es
«diff vacío» sino «hashes iguales a esta tabla».

**Acción.** Commitear por unidades, sin mezclar:

1. `docs/assets/` + informes y planes de auditoría.
2. Notebooks 01–07 + `models/ds02_manifest.json` + `app/cache/cache_manifest.json`.
3. `app/*` + `src/*` + `tests/*` modificados.

**Verificación.** `git status --porcelain` vacío salvo lo que se decida dejar fuera.

---

## P1 · Reconciliar la cifra multiseed (C1) — sin reentrenar

**Diagnóstico medido. No es markdown: son tres corridas distintas.**

| Evidencia | Fecha | Semillas 7 / 123 | Media 42/7/123 |
| --- | --- | --- | --- |
| `resultados/bundle_c_multiseed.csv` (script) | 2026-11-04 21:54 | 4.429 / 4.336 | **4.368 ± 0.053** |
| NB06 celda 43 (salida almacenada) | corrida anterior; guardado 11-06 11:34 | 4.376 / 4.252 | 4.322 ± 0.064 |
| NB05 celda 9 (protocolo OOF) | 11-06 | 4.274 / 4.379 | 4.330 ± 0.053 |
| `resultados/comparativa_c_multisemilla.csv` (`--desde-csv`) | 2026-11-06 15:25 | del CSV | **4.368 ± 0.053** |

El markdown solo reproduce lo que encuentra. La causa es que la salida guardada de
NB06 es **anterior** al CSV que la propia celda 43 escribe: el notebook se guardó el
6-N a las 11:34, pero `bundle_c_multiseed.csv` sigue siendo del 4-N a las 21:54 →
la celda 43 no se re-ejecutó al guardar. NB05 mide además con otro protocolo (OOF).

**Decisión.** Re-ejecutar NB06 ahora **empeora** el problema: reentrena 7/123,
reescribe el CSV y produce una cuarta media que obligaría a rehacer README, chuleta,
e00 y ADR. La autoridad es el CSV consolidado
`resultados/comparativa_c_multisemilla.csv`, reconstruible **sin cómputo**:

```bash
.venv/Scripts/python.exe -m src.clase.evaluar_c_multisemilla --desde-csv
```

(42 del manifiesto + 7/123 del CSV → 4.368 ± 0.053 · NASA 2355,2 ± 24,6.)

**Acción.**

1. **No** ejecutar `nbconvert` sobre NB06. Refrescar solo la celda 45 (lee CSV, no
   entrena) y **limpiar la salida de la celda 43**, que contradice el CSV que ella
   misma escribe:

```bash
.venv/Scripts/python.exe - <<'PY'
import nbformat
from nbclient import NotebookClient
p = "notebooks/06_evaluacion_produccion_comparativa.ipynb"
nb = nbformat.read(p, as_version=4)
with NotebookClient(nb, timeout=120, kernel_name="python3").setup_kernel() as c:
    c.execute_cell(nb.cells[45], 45)
nb.cells[43]["outputs"] = []
nbformat.write(nb, p)
PY
```

   La celda 45 es autocontenida (importa numpy/pandas y lee dos CSV). En kernel
   limpio queda con `execution_count=1`; es cosmético y no cambia ninguna cifra.

2. `README.md:98` y `:119`: cambiar la etiqueta «NB06» por
   «CSV `resultados/comparativa_c_multisemilla.csv`, grano ventana test 6 196».
3. `README.en.md:62` y `:179`: misma corrección en inglés.
4. `docs/chuleta-defensa.md:33`: añadir «(CSV multiseed)» junto a la cifra.
5. `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md`:
   - sustituir la fila «media NB06 4.322 ± 0.064» por el consolidado
     `4.368 ± 0.053 / NASA 2355,2 ± 24,6`;
   - reescribir «Reconciliación multiseed»: una sola media; NB05 es otro protocolo
     (OOF); la salida almacenada de NB06 es de una corrida anterior y no consolida;
   - **borrar** la fila de `4.368` de la lista negra;
   - mantener `4.347 ± 0.012` como histórico sustituido.
6. `docs/decisions/ADR-011-deploy-bundle-c-archive-bundle-b.md`: añadir la ruta
   del CSV junto a `4.368 ± 0.053`.
7. NB06 celda 42: nota de autoridad → «la corrida en vivo de la 43 no consolida;
   la cifra vigente es el CSV `comparativa_c_multisemilla.csv` (4.368)».

**Verificación.**

```bash
.venv/Scripts/python.exe -c "import pandas as pd;d=pd.read_csv('resultados/comparativa_c_multisemilla.csv');print(d);print(d.RMSE.mean(),d.RMSE.std(ddof=1))"
grep -rn "4\.322\|4\.330" README.md README.en.md docs/chuleta-defensa.md MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md
pytest tests/test_clase_c_multisemilla.py -q
git diff --stat notebooks/06_evaluacion_produccion_comparativa.ipynb
```

Debe quedar **una** media citada en README/chuleta/e00, con su archivo de origen, y
la media del CSV debe ser 4,368. El diff del notebook debe tocar solo: salida de la
celda 45, salida vaciada de la 43 y markdown de la 42.

**Riesgo 2.** Que alguien re-ejecute NB06 entero y vuelva a mover el CSV. La nota de
la celda 42 lo advierte; el test solo exige que la fila 42 del consolidado sea la del
manifiesto, así que una corrida nueva no rompe la suite, pero sí las citas.

---

## P2 · Versionar las figuras (A1)

```bash
git add docs/assets
git ls-files docs/assets | wc -l   # 9 antes de P3, 10 después
```

**Verificación.** Cada `docs/assets/*.png` citado en `README.md`, `README.en.md` y
`src/clase/README.md` existe y está en `git ls-files`.

---

## P3 · Captura de la app (A2)

**Problema.** El reto exige «Captura de la app (*)» arriba del README; hoy no hay
ninguna y el apartado literal baja PIA-1 a 3.

**Acción.**

```bash
.venv/Scripts/python.exe -m streamlit run app/streamlit_app.py --server.headless true \
  --server.port 8501 --browser.gatherUsageStats false &
# esperar /_stcore/health == 200
"/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu \
  --hide-scrollbars --window-size=1440,2200 --virtual-time-budget=20000 \
  --screenshot=docs/assets/dashboard_ds02.png http://127.0.0.1:8501
```

Añadir en `README.md`, justo después del título:

```markdown
## Captura de la app

![Dashboard DS02 — bundle C](docs/assets/dashboard_ds02.png)

*Dashboard de producción: métricas del bundle C (RMSE 4.338 / NASA 2336.2) y caso
nuevo con decisión APTO / INSPECCIÓN / HANGAR.*
```

**Verificación.** El PNG pesa > 100 KB y **se mira**: debe mostrar las 4 pestañas y
las cifras del bundle C. Si Chrome headless captura el esqueleto vacío, la captura
se toma a mano; no se acepta un archivo que no se vea.

---

## P4 · Tabla de campos en el README raíz (SAA-3)

**Acción.** Añadir `## Los datos` antes de `## Arquitectura`, con:

- 65 173 filas, 9 motores, split 52 635 / 12 538 por unidad (2/5/10/16/18/20 vs
  11/14/15).
- La tabla de 20 campos de `src/clase/README.md` (nombre, qué significa, tipo,
  % nulos antes/después).
- Una frase que hoy falta: **«No se descarta ningún campo del dataset. `unit` no
  entra como predictor (es el grupo del split) y `RUL` es el objetivo; `fase_vuelo`
  es la categórica nueva del track de clase y el bundle desplegado no la usa (93
  features sin ella).»**
- Calidad: 0 duplicados; Mach ∈ [0,33; 0,74], alt ∈ [10k; 35k]; T30 con 1,82 % MAR.

**Verificación.** La tabla existe en el README raíz y la frase de campos quitados
aparece; SAA-3 pasa de 7 a 10.

---

## P5 · La tabla no elige campeón por test (A3)

**Problema.** `src/clase/tabla_final.py:76–84` ordena el grano ventana por
`rmse_test` cuando no hay `rmse_val`, y NB06 celda 49 lo imprime.

**Acción.** Extraer una función pura y usarla en `main`:

```python
def campeon_por_grano(tab: pd.DataFrame) -> dict:
    """Campeón por grano; en ventana manda ADR-011, nunca el test."""
    fila = tab[tab["grano"] == "fila"]
    campeon_fila = fila.sort_values("rmse_val").iloc[0]["modelo"]
    return {
        "fila": campeon_fila,
        "ventana": "Híbrido-C (fijado por ADR-011, 4.338)",
    }
```

`main` imprime ese diccionario y deja de ordenar ventana por test. En NB06 celda 49,
sustituir el bucle de campeones por la llamada a `campeon_por_grano` y **limpiar su
salida** (se regenera al ejecutar `python -m src.clase.tabla_final`, sin entrenar).

**Test nuevo** en `tests/test_clase_tabla.py`:

```python
def test_ventana_no_se_ordena_por_test():
    """Aunque el híbrido sea el peor en test, el campeón ventana es C (ADR-011)."""
    tab = pd.DataFrame([
        {"modelo": "Híbrido-C", "grano": "ventana", "rmse_val": float("nan"), "rmse_test": 9.9},
        {"modelo": "LGBM-C",    "grano": "ventana", "rmse_val": float("nan"), "rmse_test": 1.0},
        {"modelo": "E2",        "grano": "fila",    "rmse_val": 7.34, "rmse_test": 7.72},
    ])
    from src.clase.tabla_final import campeon_por_grano
    assert campeon_por_grano(tab)["ventana"].startswith("Híbrido-C")
```

**Verificación.** `pytest tests/test_clase_tabla.py -q`; la tabla sigue declarando el
grano y no mezcla fila con ventana.

---

## P6 · Comentario de la guarda de banda (M3)

**Problema.** `src/mia/reglas.py` dice que el tramo `[75, ∞)` tiene 419 filas; el
JSON trae **561** y `q_high = −17,45`. Con `MIN_FILAS_TRAMO = 500` la guarda no se
activa, y el código deja `upper = max(punto + q_high, punto)`.

**Acción.** Solo comentario: 419 → 561 y explicar que la guarda no aplica a ese
tramo; el límite superior queda en el punto (banda de una cara, conservadora).

**Verificación.** `pytest tests/test_mia_rules.py -q`; ninguna decisión cambia.

---

## P7 · Salidas sin sello (M1) — opcional

**Problema.** NB02 celdas 5 y 22, y NB03 celda 9, tienen salida con
`execution_count: null`. **No afecta a ninguna cifra publicada** (las cifras salen
de los CSV).

**Acción (elegir una).**

- Barata: vaciar esas tres salidas y anotar que se regeneran con el notebook; o
- Completa: re-ejecutar NB02 y NB03 (~15 min), solo si se quiere conservar la salida.

**Verificación.** 0 celdas con salida y `execution_count` nulo, o 0 salidas en esas
celdas. Si se re-ejecuta y las cifras vivas difieren de `mlp_comparativa.csv`, manda
el CSV (autoridad declarada) y se anota la diferencia.

---

## 3. Verificación final (todo junto)

```bash
.venv/Scripts/python.exe -m compileall -q src app scripts tests
.venv/Scripts/python.exe -m pytest tests -q -rs -p no:cacheprovider
sha256sum models/ensemble.joblib models/bilstm_ds02.keras models/ds02_manifest.json
git ls-files docs/assets | wc -l   # >= 10
grep -rn "4\.322\|4\.330" README.md README.en.md docs/chuleta-defensa.md \
  MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md
```

Puertas: suite verde; los tres hashes de `models/` iguales a la tabla de P0; una sola
media multiseed citada; todos los enlaces de figuras resuelven; la captura se ve.

---

## 4. Qué queda fuera (y por qué)

- **MLflow (C2 / PIA-4):** decisión del usuario. Deja PIA en 7,7–8,0.
- **n8n (A4 / M4):** decisión del usuario. Deja MIA en 9,0; el 10 exige enviar
  también APTO o demostrar la rama con un POST manual.
- **Reentrenar la semilla 42 o las 7/123:** prohibido; movería el manifiesto o el CSV
  y multiplicaría las versiones del número.
- **Recalibrar bandas:** prohibido; cambiaría decisiones y capturas.
