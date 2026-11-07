# Informe de resultado — bloques BL-01…BL-09

**Fecha:** 2026-11-05
**Change SDD:** `openspec/changes/2026-11-05-bloques-auditoria/`
**Rama de trabajo:** `clase-modelo-c`
**Modelo de producción:** ensemble C, `models/ensemble.joblib`, semilla 42
**Alcance cumplido:** BL-01 a BL-09. BL-10 (MLflow y n8n) quedó fuera por decisión del usuario.

## Resultado principal

Los nueve bloques están aplicados y verificados:

```text
.venv/Scripts/python.exe -m compileall -q src app scripts tests
.venv/Scripts/python.exe -m pytest tests -q -rs -p no:cacheprovider

315 passed, 6 skipped en 136,17 s (exit 0)
```

El bundle C **no se reentrenó**, el test de las unidades 11/14/15 **no se volvió a medir**
y ninguna métrica de despliegue cambió por recalcular nada. Los cambios corrigen
documentación, contratos, reglas defensivas, evidencia y tests.

## Estado por bloque

| Bloque | Resultado | Evidencia |
| --- | --- | --- |
| BL-01 · Narrativa única de C | Completado | README, `src/clase/README.md`, chuleta, guion, README inglés, `AGENT.md` y tabla autorizada del vault distinguen E2 como campeón de clase y C como despliegue |
| BL-02 · Dos bandas con papeles distintos | Completado | `conformal` del artefacto frente a `conformal_decision` R6; la app muestra ambas etiquetadas |
| BL-03 · Multisemilla completa | Completado | CSV con las tres semillas y prueba que ya no se salta |
| BL-04 · Seis reglas de decisión | Completado | R10 y R11 añadidas sin alterar decisiones existentes |
| BL-05 · Evidencia visual versionada | Completado con límite | Nueve figuras reales en `docs/assets/`; falta solo la captura automática en vivo |
| BL-06 · SHAP del bundle C | Completado | Documentación del híbrido y corrección del docstring de la app |
| BL-07 · Contrato del artefacto | Completado | Python declarado y referencia histórica B trazable |
| BL-08 · Coherencia de la suite | Completado | El test de rúbrica verifica al campeón real |
| BL-09 · Docstrings y gate | Completado con límite | 0 funciones/clases públicas sin docstring; el gate OOF sigue en fail-closed documentado |

## BL-01 — Qué significa ahora “campeón”

La redacción vigente es:

- **MLP E2:** mejor modelo del **track de clase**, RMSE 7,72 en test.
- **Ensemble C:** **modelo desplegado y defendido**, RMSE 4,338 y macro-RMSE 5,0153.
- **XGBoost:** mejor clásico del track, no campeón general.

También se corrigieron las cifras multisemilla en README español e inglés,
`src/clase/README.md`, `AGENT.md` y la tabla autorizada del vault:

```text
C (semillas [42, 7, 123]): RMSE 4,368 ± 0,053 | NASA 2.355,2 ± 24,6
```

El guion de defensa incorpora una pregunta específica sobre el modelo desplegado.
`src/clase/README.md` ya incluye NB07 y los enlaces de figuras apuntan a
`docs/assets/`, no a rutas rotas o no versionadas.

## BL-02 — Las bandas no eran “la app contra el manifiesto”

La auditoría inicial planteó el hallazgo como una contradicción; la implementación
precisó la semántica real:

- `conformal`, 17 450 filas: banda interna del artefacto, incluida la unidad 16.
  Es la lectura por defecto de `ensemble.predict_interval`, la caché y los casos nuevos.
- `conformal_decision`, 14 915 filas: banda opcional R6 para la pasada de corrección
  de reglas, sobre unidades 2, 5, 10, 18 y 20. Solo sustituye los límites cuando
  `aplicar_reglas` está activado.

El panel de auditoría muestra ambas con su papel. El test añadido impide volver a
confundirlas:

```text
test_la_banda_de_decision_es_la_del_json_de_calibracion
```

## BL-03 — Multisemilla medido, no reentrenado en este change

Se generó el archivo que el test esperaba:

```text
resultados/comparativa_c_multisemilla.csv
```

Contiene:

- Semilla 42 desde `models/ds02_manifest.json`.
- Semillas 7 y 123 desde la medición ya existente en `resultados/bundle_c_multiseed.csv`.
- Agregación con el mismo código de agregación existente.

Se añadió la opción:

```text
python -m src.clase.evaluar_c_multisemilla --desde-csv
```

Así se repara la tabla y el test sin gastar horas de CPU ni tocar el bundle.
El modo normal sigue entrenando como antes.

## BL-04 — Seis reglas sin cambiar el comportamiento operativo

Las reglas de decisión pasan de cuatro a seis:

```text
R1_SEGURIDAD
R10_DATOS_INSUFICIENTES
R11_UMBRALES_INCOHERENTES
R9_HANGAR
R8_INSPECCION
R7_APTO
```

R10 y R11 solo actúan donde antes el motor caía en `SIN_DECISION` sin dejar traza:

- Ficha con datos sanos pero sin límite inferior o sin umbrales útiles.
- Umbrales presentes pero incoherentes, con `hangar >= apto`.

No modifican ninguna decisión anterior de `R1`, `R9`, `R8` o `R7`. Los tests cubren
la ficha incompleta, los umbrales invertidos y la prioridad intacta de seguridad.

## BL-05 — Figuras auditables

`docs/assets/` contiene nueve figuras reales ya existentes:

```text
bundle_c_cascada_rmse.png
bundle_c_rmse_por_motor.png
clasicos_real_vs_pred.png
eda_barras_fase.png
eda_scatter_alt_mach.png
importancia_permutacion.png
mlp_real_vs_pred.png
real_vs_predicho_bundle_c.png
shap_importancia.png
```

Los README enlazan esas copias versionadas. La antigua captura del dashboard,
con cifras que ya no existen, se retiró y fue sustituida por figuras medidas más
una nota con el comando para regenerar la captura real.

Límite: no se generó una captura automática en vivo porque aquí no hay
`playwright` instalado.

## BL-06 — SHAP del modelo que se despliega

La documentación de clase ahora presenta primero el SHAP del bundle C:

- Tres ramas del híbrido.
- Doscientas filas de validación del fold-0.
- Aditividad comprobada alrededor de `1e-6`.

El SHAP de XGBoost queda explícitamente descrito como explicación del track de
clase, no del artefacto desplegado. El docstring de `app/ui_shap.py` ya no dice
“model B”.

## BL-07 — El manifiesto declara Python y la historia correcta

`models/ds02_manifest.json` incluye ahora:

```text
python: 3.12.10
```

La referencia histórica no es la revisión intermedia v4.1.0 inicialmente prevista
en el plan: siguiendo ADR-011, es el **bundle B archivado**, con métricas,
multiseed, procedencia y su SHA:

```text
Modelo: Hybrid stacking + EMA causal 5, bundle B
Referencia: RMSE 4,251, NASA 2.305,1
Multiseed: 4,340 ± 0,101, semillas [42, 7, 123]
Procedencia: archive/models_b/ds02_manifest.json
```

El manifiesto declara el coste medido de desplegar C frente a B, sin convertir a B
en candidato y sin cambiar el campeón.

## BL-08 — La suite verifica al campeón real

El test de rúbrica fija:

```text
code_version = clase-bundle-C
seed = 42
reference_row RMSE = 4,338
```

Y comprueba que esa cifra es menor que el test del MLP E2. También se corrigió la
descripción de la submuestra del SVR: es aleatoria y uniforme con semilla 42, no
estratificada. La tabla final imprime el criterio usado en cada grano.

## BL-09 — Documentación completa y gate ruidoso

La auditoría posterior a los cambios encuentra:

```text
0 funciones/clases públicas sin docstring de 264
```

En `app`, `src/clase`, `src/mia` y `src/ds02_rul`.

El gate de reglas sigue en `exit 3` porque falta `_p1_oof_cache.npz`. Esa es su
conducta contractual: un instrumento ausente debe fallar de forma visible, no
pasar en silencio. Se documentó así en el change en lugar de fingir una evidencia
que no se generó.

## Verificación final

```text
315 passed, 6 skipped en 136,17 s
exit 0
```

Los seis skips corresponden a seis tests que exigen `_p1_oof_cache.npz`, ausente
por diseño hasta generar el instrumento OOF. No se saltó ningún test relacionado
con los cambios aplicados.

La caché de la app volvió a quedar vigente después de editar el manifiesto:
se reemitió su sello `manifest_sha256` una vez cerrados los cambios del manifiesto.
Las ventanas, filas y métricas de la caché no se regeneraron porque no cambiaron.

## Límites y trabajo que sigue abierto

1. **Captura automática del dashboard:** pendiente de un entorno con `playwright`.
2. **Instrumento OOF:** pendiente de generar `_p1_oof_cache.npz`, con HDF5 y tiempo
   de cálculo disponibles.
3. **MLflow y n8n:** fuera del alcance por decisión del usuario.
4. **Archivos ya modificados antes del change:** hay ediciones previas sin commitear
   en notebooks y notas del vault; este change no ejecutó celdas de notebook.
5. **Multiseed:** las semillas 7 y 123 se reutilizaron desde su medición existente;
   no se reentrenaron en este change.
