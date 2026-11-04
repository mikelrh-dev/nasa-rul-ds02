# Verify report — adopción del bundle C

**Change:** `2026-11-04-adopcion-bundle-c` · **Rama:** `clase-modelo-c` · **Fecha:** 2026-11-04

Regla respetada: **no se ha reentrenado y no se ha ejecutado ninguna celda de notebook**.
Única ejecución de datos: `scripts/build_ui_cache.py`, que no entrena (carga el bundle
congelado y puntúa ventanas ya existentes).

---

## 1. Lo que queda desplegado

| Pieza | Estado |
|---|---|
| `models/{ensemble,bilstm_ds02,scaler,ds02_manifest}` | bundle **C**, seed 42: RMSE 4.338 / MAE 3.227 / R² 0.9461 / NASA 2336.2 |
| `models/ds02_manifest.json` | `dataset="DS02"`, `dataset_variant` (base imputada), `historical_reference` de B, bloque `macro_rmse` |
| `app/cache/` | regenerada desde la base imputada: 6.196 ventanas, RMSE ponderado **4.3382**, macro **5.0153** |
| `archive/models_b/`, `archive/cache_b/` | B completo con sus hashes (4.251 / 2305.1) |
| `archive/notebooks-ds02-ensemble/` | cadena de evidencia de B (3 ipynb + 2 md + 1 py + artifacts) |
| `archive/{scripts-bundle-b,src-clase,tests}/` | `build_02_notebook.py`, `evaluar_b_en_adaptada.py`, `test_clase_b_robusto.py` |
| `src/clase/puente_c.py` | nuevo: reconstruye `raw/dev/test/result` desde `models/` sin entrenar |
| `src/clase/evaluar_c_multisemilla.py` | nuevo: seeds 42 (del manifiesto) + 7 y 123 |
| `notebooks/03–06` | reconectados al bundle C, orden didáctico intacto, sin ejecutar |
| `docs/decisions/ADR-011-deploy-bundle-c-archive-bundle-b.md` | decisión, alternativas, coste medido y rollback |

Ninguna carpeta se ha borrado: lo retirado está en `archive/` (que sigue en `.gitignore`).

## 2. Comprobaciones ejecutadas

| Comprobación | Comando | Resultado |
|---|---|---|
| Sintaxis de todo el árbol | `python -m compileall -q src app scripts tests` | **exit 0** |
| Contrato del artefacto + bundle C + multiseed | `python -m pytest tests/test_clase_c_multisemilla.py tests/test_artifact_contract.py tests/test_clase_bundle_c.py -q` | **17 passed, 1 skipped** |
| SHA de los artefactos contra el manifiesto | script de hashing | ensemble **CASA**, bilstm **CASA** |
| Manifiesto contra sí mismo | `dataset`, `dataset_variant`, `historical_reference` | OK |
| Caché desde la base imputada | `python scripts/build_ui_cache.py` | **OK**: 3.293 + 760 + 2.143 = 6.196 ventanas; RMSE 4.3382 = manifiesto |
| CLI de la caché | `python scripts/build_ui_cache.py --help` | exit 0 |
| CLI multiseed | `python -m src.clase.evaluar_c_multisemilla --help` | exit 0 |
| Formato de los cuadernos | `python -m json.tool notebooks/*.ipynb` | 6/6 válidos |
| Referencias muertas en cuadernos | barrido de `ds02_ensemble/artifacts`, `aux[`, `nb1_`, `src/clase/models`, "B sigue en producción", "puerta D11" | **vacío** |
| Suite completa | `python -m pytest tests/ -q` | **16 failed, 260 passed, 7 skipped** ← ver §3 |

Multiseed reproducible con lo que hay en disco: seed 42 del manifiesto (4.338) y seeds 7 y 123
de `resultados/bundle_c_multiseed.csv` → media **4.347 ± 0.012 / NASA 2338.9 ± 10.7**.
La cifra 4.314 ± 0.042 que figuraba en las notas de trabajo no tiene fichero que la
respalde en este árbol: se sustituye por la medible en disco.

## 3. Lo que NO está verde (y por qué)

Durante la verificación aparecieron 18 fallos. Dos eran del contrato del manifiesto y **están
arreglados**: el manifiesto de C no traía el bloque `macro_rmse` que la UI lee
(`test_dss_ui::test_metrics_are_recomputed_from_the_cache` y
`test_ui_rules::test_el_tablero_sigue_entregando_las_mismas_metricas_crudas`). Se reconstruyó
leyendo los valores de la caché nueva (no transcribiéndolos) y ambos pasan.

Quedan **16**, en dos clases independientes del contrato del artefacto:

**A. Deriva de banda/reglas (9 tests).** La capa de reglas sigue calibrada sobre el OOF de B
(riesgo nº1 declarado en la propuesta) y la banda del bundle C mueve los `L_inf`, así que los
estados y los ciclos que estos tests fijan ya no coinciden:

- `test_simulacion::test_ciclos_hasta_fallo_coincide_con_la_cache` — U14 entra en hangar en el
  ciclo **24**, no en el 28.
- `test_live_eval` (3) — casos que daban INSPECCION ahora dan HANGAR.
- `test_engine_flow::test_la_ventana_que_decide_es_la_de_menor_limite_inferior` — 1.175 vs 1.177.
- `test_ui_alta` (4) — perfiles y ciclos críticos derivados de la banda.

No se han reescrito a la ligera: son instantáneas de la decisión del bundle anterior. Para
ponerlas verdes hay dos caminos legítimos, ninguno trivial: recalibrar R6 sobre OOF de C
(change propio) o actualizar cada instantánea a los valores de C verificando que el caso sigue
ejerciendo lo que el test dice medir.

**B. Re-ejecutado del dashboard (7 tests de `test_dss_interaction`).** Falla con
`There are multiple elements with the same key='vista_modo'`: el script se ejecuta dos veces en
un mismo `AppTest.run()`, es decir, algún camino llama `st.rerun()` al arrancar. `app/` **no
tiene cambios respecto a HEAD** en este change, así que no lo introducen los cuadernos ni la
documentación; es un fallo del panel que merece su propio arreglo.

## 4. Lo que queda en manos del autor

Nada de esto se ha ejecutado (por indicación explícita):

1. **Cuadernos, en orden** `03 → 04 → 05 → 06`. El `04` crea `notebooks/artifacts_c/`; el `05`
   lo exige y aborta con mensaje claro si falta. No hay que editar nada.
2. **App**: `streamlit run app/dashboard_ds02.py` — debe mostrar el SHA `d6c70142…` y
   6.196 ventanas. La caché ya está regenerada, así que arranca sin más.
3. **Consolidador multiseed**: `python -m src.clase.evaluar_c_multisemilla` escribe
   `resultados/comparativa_c_multisemilla.csv` (el que citan los README). Actualmente ese CSV
   todavía no existe; las cifras 4.347 ± 0.012 se sostienen con el manifiesto + `bundle_c_multiseed.csv`.
4. **Versionar lo archivado**, si se quiere: `archive/` está en `.gitignore`, así que hace falta
   `git add -f archive/...` antes del commit. No se ha hecho ningún commit en este change.
5. **Banda de reglas**: recalibrar R6 con OOF de C es lo que cerraría la clase A de fallos.

## 5. Desviación registrada

`tasks.md` T7 pedía un veredicto del tipo «C cumple el umbral 4.25». C mide **4.338 > 4.25**, así
que el cuaderno 06 no lo afirma: despliega C y deja escritas las cifras y el coste frente a B
(+0.087 RMSE, +31.1 NASA en las mismas 6.196 ventanas), con B como referencia histórica
auditable. Escribir lo contrario sería falso y no se ha hecho.

## 6. Rollback

Copiar los cuatro ficheros de `archive/models_b/` a `models/`, restaurar
`archive/cache_b/cache_manifest.json` en `app/cache/`, regenerar la caché y devolver los
cuadernos desde `archive/notebooks-ds02-ensemble/`. Sin reentrenar nada.
