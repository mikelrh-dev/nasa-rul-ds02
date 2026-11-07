# Planificación: flujo notebook -> .py más intuitivo

Fecha: 2026-11-06
Estado: PLAN, sin ejecutar. Esperando confirmación del usuario para el grupo seguro.

## Objetivo

Que en auditoría el flujo notebook -> .py -> artefacto -> siguiente notebook se siga sin perderse, sin re-ejecutar entrenos ni romper outputs guardados.

## Punto de partida (auditoría con evidencia)

- NB04 y NB07 se siguen de un vistazo.
- NB01, NB02, NB03, NB05 y NB06 se siguen con dificultad.
- NB02 no llama a entrenar_mlp(): importa constantes y funciones privadas y duplica el loop en vivo (celdas 4 y 18).
- NB05 celda 29 re-entrena LGBM adaptada duplicando train_lgbm_adaptada.py.
- NB03 celda 12 puede dibujar con números literales si abl no está en memoria.
- Alias: evaluar_clase/mostrar_clase (src/ds02_rul/viz.py:318-322), make_pipeline (src/clase/pipeline_clase.py:38 vía src/utils.py:23), re-exports src/utils.py, src/reglas.py y ds02_rul/__init__.py.
- Doble grafía de import: from src.ds02_rul.* y from ds02_rul.* conviven, dependientes de sys.path y del cwd (celda 0 de cada notebook).
- Artefactos sin escritor visible en notebooks:
  - models/ensemble.joblib + bilstm_ds02.keras + ds02_manifest.json <- src/clase/train_ensemble_adaptado.py entrenar (183-222), save_ensemble persistence.py:202.
  - resultados/comparativa_ventanas.csv + src/clase/models/lgbm_adaptada.joblib <- src/clase/train_lgbm_adaptada.py:60-61.
  - models/mejor_modelo.joblib <- copia manual de mejor_modelo_clase.joblib (train_clasicos.py:158), sin escritor en código.
  - resultados/tabla_final_clase.csv <- src/clase/tabla_final.py, NB06 celda 51 solo verifica.
- La cadena de la app a n8n es la más limpia, salvo decision_en_vivo -> traza_decision -> M.motor.

## Grupo SEGURO (impacto 9/10, riesgo cero, solo Markdown y docs)

Hoy, tras confirmación. No toca código, outputs ni execution_count.

1. Cabecera de trazabilidad de 7 líneas tras la celda 0 en cada notebook 01-07:
   - celda 0 = bootstrap, no es lógica del modelo.
   - imports: ds02_rul.* = src/ds02_rul/ (ruta corta), src.clase.* / src.ds02_rul.* = misma carpeta con prefijo src.
   - alias usados en ese notebook con fichero:línea.
   - artefactos que ESCRIBE y que solo LEE.
   - escritor .py de cada artefacto, con la frase NBxx NO lo invoca donde aplique.
   - celdas display/plt.show sin lógica: solo presentación.
2. Tabla de alias en NB02, NB03 y NB04: evaluar_clase, mostrar_clase, make_pipeline, make_pre, FEATURE_COLS, evaluate_predictions, HybridStackingEnsemble y re-exports de ds02_rul/__init__.py.
3. Aviso doble grafía de import en los 7 notebooks.
4. Aviso Ridge tiene 3 significados (físico NB01, fila NB02, meta NB06), copiado de NB02 a NB01 y NB06.
5. Marcar celdas display como solo presentación: NB01 (10,12,14,16,28), NB02 (10,28), NB04 (16,22), NB06 (20,31,36,38,52), NB07 (4).
6. Procedencia de artefactos:
   - nota en vault junto a n05 y e00.
   - models/README.md nuevo (hoy no existe) con escritor y comando de cada artefacto.
   - celdas Procedencia en NB02 (mejor_modelo.joblib) y NB07 (bundle C), siguiendo el patrón NB05/NB06.
7. Verificación: JSON válido, nº celdas +1 por notebook (solo Markdown), hashes de celdas code idénticos, git diff solo .ipynb Markdown + docs.

## Grupo MEDIO (impacto 6/10, riesgo medio)

Fin de semana, tras revisar el seguro. Decidir caso a caso.

1. Unificar imports solo dentro de notebooks, manteniendo doble path. Actualizar vault n05 y test_shap_c. Riesgo: si se olvida un path, imports rotos.
2. NB05 celda 29 a función .py: cuesta 0.3s, pero entrenar() escribiría CSV de 2 filas (hoy 1) y pisaría lgbm_adaptada.joblib que carga la celda 36. Alternativa menor: comentario espejo + assert, sin tocar disco.
3. NB03 fallback: no borrar literales. Sustituir por lectura de resultados/ablacion_cycnorm.csv archivado desde la celda 8 + assert contra abl si existe. Normalizar etiqueta cyc_norm ON (baseline) a la doble espacio de pipeline.py:256 o normalizar con strip() para no romper reindex.
4. Test que solo avisa (no falla) sobre imports src.ds02_rul nuevos, para frenar que el dual crezca.
5. Verificación por caso: pytest del scope tocado + verify_gate.py completo antes de commitear.

## Grupo ALTO (impacto teórico 10/10, riesgo alto, no hacer hoy)

Requiere re-ejecutar los notebooks enteros. Solo si el usuario decide que vale la pena tras el fin de semana.

1. NB02 celdas 4 y 18 a entrenar_todo() y entrenar_mlp(): re-escribirían comparativa.csv, mlp_comparativa.csv y los joblib, cambiarían tiempo_s (RF 79.6s vs 50s en vivo), invalidarían hashes del manifiesto, harían segunda lectura del test y tardarían >185s a ~1000s por notebook. Las figuras y el texto descrito quedarían inválidos.
2. Unificar todo a src.* quitando sys.path: rompe paquete instalado (pyproject packages.find where=src), pickle de HybridStackingEnsemble y test_artifact_contract en proceso limpio. Para hacerlo habría que re-picklar el bundle y re-testear Docker + SHAP-C.
3. Re-ejecutar train_ensemble_adaptado.py para refrescar: TF en CPU no es determinista, desalineas cifras defendidas y manifiesto.
4. Borrar bloques _ROOT/chdir/sys.path de golpe: no hay conftest ni editable install que los reemplace.
5. Renombrar/mover src/clase/models/lgbm_adaptada.joblib: el escritor usa la ruta literal src.clase/models y NB05 carga src/clase/models, cualquier limpieza la rompe.

## Cronograma propuesto

- Hoy: grupo seguro, tras confirmación del usuario. Un subagente por notebook o en cadena, solo Markdown, con verificación de hashes de código.
- Fin de semana: usuario revisa el seguro y decide si compensa el riesgo medio/alto.
- Si se decide el medio/alto: SDD loop completo con TDD, gate verify_gate.py y un commit por fase, sin push sin orden.

## Qué NO se toca en ninguna fase sin orden explícita

- Código de entrenamiento, outputs guardados, execution_count, CSVs, joblibs, keras y manifiesto.
- Notebooks completos (no re-ejecutar).
- MLProyectVault/90-Archivo.
- Git push sin orden explícita.

## Criterio de aceptación

- Auditor puede seguir notebook -> .py -> artefacto -> siguiente notebook sin perderse en NB01-NB07.
- Cero re-ejecuciones de entreno en el grupo seguro.
- Gate verify_gate.py en verde tras cada grupo que toque código.
