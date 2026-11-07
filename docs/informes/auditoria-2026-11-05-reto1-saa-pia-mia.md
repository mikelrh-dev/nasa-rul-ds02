# Auditoría del Reto 1 (SAA + PIA + MIA) — 2026-11-05

> **Modo:** solo lectura. No se modificó código, artefactos, notebooks ni datos.
> **Rama:** `clase-modelo-c`
> **Artefacto auditado:** `models/ensemble.joblib` (bundle C, seed 42)
> **SHA-256:** `d6c701429eed8623a9d900d922aca1922427d08ff8b4ec00604b8116c1a952dd`
> — coincide con `models/ds02_manifest.json` y con `cache_manifest`.
> **Rúbrica:** `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (escala 0 / 3 / 7 / 10).

## 1. Resumen ejecutivo

**Veredicto: el reto está aprobado con holgura en SAA, aprobado con margen en PIA
y en riesgo en MIA.** El modelado y la honestidad metodológica son de sobresaliente;
lo que resta puntos no es el modelo, es la **narrativa** (el material sigue llamando
campeón al MLP E2 en varios sitios), la **evidencia multsemilla incompleta** y la
**capa de decisión**, que tiene 4 reglas donde la rúbrica pide 6.

Tres frases que resumen el estado:

1. **El modelo es sólido y está congelado**: 4.338 RMSE con huella verificada, sin
   fuga, con partición por motor y test leído una sola vez.
2. **La documentación no siempre dice lo mismo que el artefacto**: el campeón real
   es C, pero README de clase, chuleta y guion siguen coronando a E2/XGB.
3. **La banda conformal que muestra la app (14.915 filas) no es la que declara el
   manifiesto (17.450)**: la diferencia son las 2.535 filas del motor 16, que
   entrenó el meta-learner y por tanto no es out-of-sample limpio.

### Notas estimadas

| Bloque | Nota | Techo sin lo excluido | Qué la limita |
| --- | --- | --- | --- |
| **SAA** (modelado) | ~9,5 / 10 | 10 | Narrativa del campeón, evidencia multsemilla incompleta |
| **PIA** (pipelines) | ~6,7 / 10 | 8,0 | Falta MLflow (PIA-4); reproducibilidad del manifiesto incompleta |
| **MIA** (implantación) | 4,0 – 5,2 / 10 | 6,5 | 4 reglas de decisión en vez de 6 (MIA-2); n8n es un placeholder |

El rango de MIA depende de un solo criterio: si el tribunal acepta las 4 reglas
existentes como "capa de decisión suficiente" (5,2) o aplica literalmente RULES-08
(4,0). **Es el punto de mayor retorno por hora invertida de todo el reto.**

---

## 2. Alcance y método

**Leído:** `README.md`, `README.en.md`, `src/clase/README.md`, `docs/chuleta-defensa.md`,
`docs/defensa/guiones-15min.md`, specs y proposals de `openspec/changes/`,
`src/clase/*`, `src/mia/*`, `src/ds02_rul/*` (incl. `shap_c.py`), `app/*`,
notebooks 01–07, CSVs de `resultados/`, manifiesto, `calibracion_banda.json`,
ADR-011, informes y guiones de defensa.

**Ejecutado:** suite completa (`pytest tests -q -rs -p no:cacheprovider`),
verificación de huellas SHA, comprobación de particiones y nulos, y contraste de
cada cifra publicada contra su CSV o su código.

**No ejecutado (por decisión del usuario):** MLflow, flujo n8n, la app en navegador
y un clone limpio. No se reentrenó nada.

---

## 3. Evidencia que sostiene el veredicto

| Comprobación | Resultado |
| --- | --- |
| Suite completa | **308 passed, 7 skipped**, 150,98 s, exit 0 |
| Notebooks con salida | 7 de 7, 0 errores |
| Huella del artefacto | SHA = manifiesto = `cache_manifest` ✅ |
| Partición por motor | train 52.635 (2/5/10/16/18/20) · test 12.538 (11/14/15) · sin solape |
| Calidad de datos | 0 nulos tras imputar, 0 duplicados |
| Nulos MAR | 1.185 (1,82 % global, 2,01 % train), racha máx. 3, 0 unidades con racha > 3 |
| Métricas C (test) | RMSE 4.338 · MAE 3.227 · R² 0.9461 · NASA 2336.2 |
| Macro-RMSE | 5.0153 (U11 3.6328 · U14 8.5761 · U15 2.8371) |
| SHAP-C | 3 ramas, 200 filas de validación fold-0, unidad 5, aditividad ~1e-6 |

Los 7 skips: 6 por falta de `_p1_oof_cache.npz` y 1 por el CSV multsemilla.

---

## 4. Hallazgos

### 4.1 Críticos (comprometen una nota entera)

| ID | Hallazgo | Evidencia |
| --- | --- | --- |
| **C1** | La app y el manifiesto declaran bandas distintas: 14.915 vs 17.450 filas | `src/mia/calibracion_banda.json` (`n_calibration: 14915`, bins 5125/6094/3135/561) vs `models/ds02_manifest.json` (`n_calibration: 17450`, bins 5730/6070/4663/987) |
| **C2** | Las 2.535 filas extra son el motor 16, que **entrenó** el meta-learner | `meta_protocol.fitted_on: "holdout unit 16 (adaptada)"`, `rows: 2535` |
| **C3** | La captura del README es de la app antigua (híbrido 4,25 / SVM 9,06 / MLP E1 7,70) | `resultados/app_clase.png`, citada en `README.md` línea 13 |
| **C4** | El multsemilla publicado no existe como CSV: solo seeds 7 y 123, sin 42 | `resultados/bundle_c_multiseed.csv`; README anuncia 4.322±0.064 sobre [42, 7, 123] |
| **C5** | El test multsemilla **nunca corre**: busca un nombre de archivo distinto | `tests/test_clase_c_multisemilla.py` lee `comparativa_c_multisemilla.csv`; el real es `bundle_c_multiseed.csv` |
| **C6** | Cuatro sitios siguen coronando a E2/XGB como campeón | `src/clase/README.md:112,120`; `docs/chuleta-defensa.md:5`; `docs/defensa/guiones-15min.md:20` |

### 4.2 Altos (restan credibilidad)

| ID | Hallazgo |
| --- | --- |
| A1 | `src/mia/reglas.py` tiene **4** reglas de decisión (R1, R9, R8, R7); RULES-08 exige **6+** |
| A2 | `app/ui_shap.py` documenta "model B" y solo implementa la rama LightGBM |
| A3 | `models/ds02_manifest.json` declara `python: null` y no incluye `historical_reference` |
| A4 | `resultados/` está en `.gitignore`: las 4 figuras que cita el README no están versionadas |
| A5 | `scripts/freeze_rules_evidence.py` sale con código 3 ("cannot verify") por falta del caché OOF |
| A6 | `tests/test_clase_rubrica.py` compara XGB contra XGB y pasa aunque el campeón sea C |
| A7 | `train_clasicos.py:5` documenta "5k estratificada" sobre una base de 52k |
| A8 | `tabla_final.py:76–78` cae a `rmse_test` en grano ventana (mezcla de granularidades) |
| A9 | SHAP-C existe (`src/ds02_rul/shap_c.py`, NB07) pero no aparece en la superficie de defensa |
| A10 | La banda del bin 3 es negativa en ambos lados (`q_low −25,33`, `q_high −17,76`): el modelo se aplana en RUL alta |
| A11 | Multsemilla con tres cifras distintas: README 4.322±0.064, ADR-011 4.347±0.012, CSV 4.3825 media |

### 4.3 Medios y bajos

- **M1** Rachas de nulos: R1 no detecta rachas de T30 > 3 en `app/ui_rules.alertas_de_ventana` (no hay test de racha forzada de 4).
- **M2** `nasa_sin_clamp = 1387.3` no es comparable con 2336.2 (distinto recorte).
- **M3** Faltan 32 docstrings públicas de 261 (`app` 7/124, `src/clase` 7/36, `src/mia` 7/23, `src/ds02_rul` 11/78).
- **M4** `n8n/flujo.json` es un placeholder y `src/n8n.py` un stub.
- **M5** El README español no publica macro-RMSE ni desglose por motor; el inglés sí.
- **B1** Ruta de imágenes relativa a `resultados/`, que no se versiona.
- **B2** `src/clase/README.md` lista notebooks 01–06 y omite 07.
- **B3** El guion de 15 min está centrado en E2, no en C.
- **B4** Sin `historical_reference` en el manifiesto, la comparación con la baseline v4.1.0 no es auditable desde el artefacto.
- **B5** 4 archivos modificados sin commitear (notebooks 03–04 y 2 notas del vault); 01–02 y las specs se commitearon el 2026-11-05 (`b93884d`).

---

## 5. Plan por bloques: mejora y riesgo

**Cómo leer las dos escalas**

- **Mejora (0–10):** cuánto sube la nota esperada del Reto 1 si el bloque se cierra
  bien. **No es aditiva**: cada bloque se puntúa contra el techo de su criterio.
- **Riesgo (0–10):** probabilidad × impacto de invalidar algo ya medido, cambiar lo
  que muestra la demo o desalinear un artefacto congelado.

| ID | Bloque | Mejora | Riesgo | ¿Toca notebooks? | ¿Reentrena? |
| --- | --- | --- | --- | --- | --- |
| **BL-01** | Narrativa única: C es el campeón | **8** | **1** | Re-ejecutar NB06 (opcional) | No |
| **BL-02** | Banda conformal única (14.915) | **7** | **6** | Re-ejecutar NB05 si cambia | No |
| **BL-03** | Multsemilla completo + CSV correcto | **6** | **3** | Re-ejecutar NB05 y NB06 | **Sí (seeds 7 y 123)** |
| **BL-04** | 6 reglas de decisión (MIA-2) | **7** | **5** | No | No |
| **BL-05** | Evidencia visual versionada | **5** | **2** | No | No |
| **BL-06** | SHAP-C en primera línea | **6** | **1** | No (NB07 ya lo tiene) | No |
| **BL-07** | Contrato de artefacto y reproducibilidad | **5** | **2** | No | No |
| **BL-08** | Coherencia de la suite | **4** | **2** | No | No |
| **BL-09** | Docstrings + gate de evidencias | **3** | **3** | No | No |
| **BL-10** | MLflow + n8n (PIA-4, MIA-3) | **7** | **4** | No | No |

### La respuesta directa a "¿compromete notebooks o reentrenar?"

**Ningún bloque obliga a editar el código de un notebook, y solo uno reentrena.**

- **Reentrenar:** únicamente **BL-03**, y solo las seeds **7 y 123** (evidencia de
  estabilidad). El bundle de producción (seed 42) **no se reentrena**: se lee del
  manifiesto, porque TensorFlow en CPU no es determinista y otra corrida daría otra
  cifra, desalineando manifiesto y notebooks. Coste: 2 entrenamientos completos del
  ensemble (BiLSTM + LightGBM + meta), horas de cómputo.
- **Notebooks:** BL-01, BL-02 y BL-03 pueden exigir **re-ejecutar** NB05/NB06 si
  cambian las cifras que citan (no editarlos: re-ejecutarlos para refrescar salidas).
  NB06 es el único cuaderno que llama "campeón de clase" al MLP E2. Ningún notebook
  enumera las reglas de decisión, así que **BL-04 no toca cuadernos**.
- **Riesgo de tocar cuadernos ahora:** NB03 y NB04 están modificados sin commitear.
  Cualquier re-ejecución de esos dos mezclaría cambios previos con los nuevos.

---

## 6. Fichas por bloque

### BL-01 · Narrativa única: C es el campeón — mejora 8 / riesgo 1

**Qué cierra:** C6, A9, B2, B3, M5.
**Acción:** unificar en README, `src/clase/README.md`, chuleta y guion de 15 min la
misma frase: *el campeón de clase es E2 (7,72) para el track académico; el modelo de
producción es C (4,338)*. Añadir macro-RMSE y desglose por motor al README español.
Incluir NB07 en la lista de cuadernos.
**Verificación:** `grep -rn "XGBoost (elegido)\|campeón de clase" README.md src/clase/README.md docs/`.
**Riesgo:** casi nulo; es prosa. El único cuidado es no prometer que C es "el mejor
modelo de clase" cuando se eligió por otro protocolo: C es el **desplegado**.

### BL-02 · Banda conformal única — mejora 7 / riesgo 6

**Qué cierra:** C1, C2, A10.
**Acción:** decidir una sola fuente de verdad. Recomendado: la app usa
`src/mia/calibracion_banda.json` (14.915, OOF puro) y el manifiesto se corrige para
declarar esa banda, dejando 17.450 documentado como "variante con motor 16" y
explicando por qué no se usa. Alternativa: regenerar la banda con las 14.915 y
reemplazar el bloque `conformal` del manifiesto.
**Verificación:** `n_calibration` idéntico en JSON y manifiesto; un test que lo
imponga; decisión de la app sin cambios para un caso conocido.
**Riesgo 6:** recalibrar mueve `q_low`/`q_high`, y con ellos las decisiones
APTO/INSPECCIÓN/HANGAR de la demo. Cambia capturas, ejemplos de la defensa y
posiblemente el caso que se enseña en vivo. **Nunca recalibrar sobre test.**

### BL-03 · Multsemilla completo — mejora 6 / riesgo 3

**Qué cierra:** C4, C5, A11.
**Acción:** `python -m src.clase.evaluar_c_multisemilla` para generar
`resultados/comparativa_c_multisemilla.csv` con 3 filas (42 desde manifiesto, 7 y
123 entrenadas) y alinear el nombre que espera el test. Publicar **una** cifra
(media ± std con `ddof=1`) en README, ADR-011 y chuleta.
**Verificación:** `pytest tests/test_clase_c_multisemilla.py -q` deja de saltar y
pasa con 3 filas; la fila 42 coincide con el manifiesto a 1e-9.
**Riesgo 3:** las seeds 7 y 123 pueden dar cifras distintas de las publicadas y hay
que actualizar prosa; no toca el bundle. Coste real: cómputo.

### BL-04 · Seis reglas de decisión — mejora 7 / riesgo 5

**Qué cierra:** A1 (MIA-2), M1.
**Acción:** añadir dos reglas de decisión con prioridad, condición y traza a
`REGLAS_DECISION` en `src/mia/reglas.py`. Candidatas naturales, ya justificadas por
el dominio: **banda demasiado ancha** (no decidir con incertidumbre excesiva) y
**racha de datos perdidos > 3** (hoy R1 no la ve). Cada una con su test y su entrada
en la traza que enseña la app.
**Verificación:** `python -c "from src.mia.reglas import REGLAS_DECISION;print(len(REGLAS_DECISION))"` ≥ 6;
tests de prioridad (R1 gana siempre) y de cada regla nueva.
**Riesgo 5:** cambia decisiones sobre casos existentes y la traza que se muestra en
la demo. Mitigación: prioridades bajas (por debajo de R7) para que solo actúen
cuando las actuales no disparan.

### BL-05 · Evidencia visual versionada — mejora 5 / riesgo 2

**Qué cierra:** C3, A4, B1.
**Acción:** capturar el dashboard C actual y guardarlo en `docs/assets/`, citarlo
desde el README, y versionar las figuras que el README referencia (o moverlas a
`docs/assets/`). No hace falta des-ignorar todo `resultados/`.
**Verificación:** `git ls-files docs/assets` no vacío; los enlaces del README abren
en un clone limpio.
**Riesgo 2:** una captura nueva puede mostrar cifras distintas de las del texto si
la app lee otra banda (depende de BL-02). Hacer BL-02 antes.

### BL-06 · SHAP-C en primera línea — mejora 6 / riesgo 1

**Qué cierra:** A9, A2.
**Acción:** subir SHAP-C (3 ramas, aditividad verificada) al README de clase y a la
chuleta, y corregir el docstring de `app/ui_shap.py` ("model B" → el modelo que
realmente sirve).
**Verificación:** el docstring nombra el bundle correcto; el README enlaza NB07.
**Riesgo 1:** solo documentación y un string.

### BL-07 · Contrato de artefacto — mejora 5 / riesgo 2

**Qué cierra:** A3, B4, M2.
**Acción:** rellenar `python` (versión real) y añadir `historical_reference` con la
fila de baseline v4.1.0 y su procedencia, para que la comparación sea auditable
desde el manifiesto. Declarar explícitamente que `nasa_sin_clamp` no es comparable.
**Verificación:** `tests/test_artifact_contract.py` y el test de manifiesto pasan sin
cambios de cifras.
**Riesgo 2:** editar el manifiesto altera una huella documental; hay que hacerlo sin
tocar `metrics` para no invalidar las citas.

### BL-08 · Coherencia de la suite — mejora 4 / riesgo 2

**Qué cierra:** A6, A7, A8.
**Acción:** que `test_clase_rubrica` compare **C contra E2/XGB**, no XGB contra sí
mismo; corregir el docstring "5k" de `train_clasicos.py`; eliminar el fallback de
`tabla_final.py:76–78` o marcarlo como granularidad distinta en la salida.
**Verificación:** el test falla si se cambia el campeón; `pytest tests/test_clase_rubrica.py -q`.
**Riesgo 2:** un test más estricto puede destapar una inconsistencia real; eso es el
objetivo, no un problema.

### BL-09 · Docstrings y gate de evidencias — mejora 3 / riesgo 3

**Qué cierra:** M3, A5.
**Acción:** completar las 32 docstrings públicas y decidir qué hacer con
`freeze_rules_evidence.py`: o se genera `_p1_oof_cache.npz` y el gate pasa, o se
documenta el fail-closed como comportamiento intencional (hoy sale con 3).
**Verificación:** cobertura de docstrings y `python scripts/freeze_rules_evidence.py`
con salida 0 o con justificación escrita.
**Riesgo 3:** generar el caché OOF implica recomputar predicciones out-of-fold; mal
hecho, contamina la evidencia.

### BL-10 · MLflow + n8n — mejora 7 / riesgo 4

**Qué cierra:** PIA-4, MIA-3, M4. **Excluido por el usuario en esta fase.**
**Acción:** registrar el bundle C en MLflow (parámetros, métricas, artefacto y
huella) y sustituir `n8n/flujo.json` por un flujo real con el webhook de decisión.
**Verificación:** run de MLflow con el SHA del manifiesto; ejecución n8n de extremo
a extremo con un caso conocido.
**Riesgo 4:** un flujo real puede tomar decisiones sobre datos vivos; hay que
mantener el toggle apagado por defecto, como ya hace el diseño actual.

---

## 7. Orden recomendado y puertas

**Orden por retorno/riesgo:** BL-01 → BL-06 → BL-05 → BL-04 → BL-03 → BL-02 → BL-07
→ BL-08 → BL-09 → (BL-10 cuando se retome).

Motivo: BL-01 y BL-06 son prosa con riesgo 1 y recuperan la coherencia que más
puntos cuesta hoy. BL-04 es el mayor salto de MIA. BL-02 va después de BL-05 porque
la captura debe reflejar la banda definitiva. BL-03 es el único que consume cómputo,
así que se lanza cuando el resto esté cerrado.

**Puertas que no se cruzan**

1. El test (uds 11/14/15) es de **una sola lectura**; ninguna corrección lo re-mide.
2. El bundle seed 42 **no se reentrena** para "mejorar" una cifra.
3. La banda conformal **no se recalibra sobre test**.
4. Toda cifra que cambie exige actualizar manifiesto **y** prosa en el mismo commit.
5. NB03 y NB04 están sucios: no re-ejecutarlos hasta commitear o descartar lo previo.

---

## 8. Límites de esta auditoría

- No se ejecutó MLflow ni n8n; sus notas son las del techo por rúbrica, no una
  evaluación de funcionamiento.
- No se abrió la app en navegador: la revisión de UI es de código y de la captura.
- No se probó un clone limpio; el hallazgo de `resultados/` ignorado se verificó con
  `git ls-files`, no reproduciendo el clone.
- Las notas son estimaciones con la rúbrica v5, no una corrección oficial.
