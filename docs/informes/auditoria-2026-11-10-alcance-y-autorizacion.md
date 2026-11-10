# Alcance y autorización de las tareas — Auditoría 2026-11-10

> **Documento de decisión.** No ejecuta nada: sirve para que leas qué tocaría cada tarea
> antes de autorizarla. El análisis completo está en
> `docs/informes/auditoria-2026-11-10-rubrica-ejecutada.md` (§6.1).
> **Estado:** HEAD `10761e7b…` · 19 `M` + 3 `??` · 1.171 ficheros versionados.

---

## 1. Qué tienes que decidir

El backlog tiene **14 tareas**. La pregunta es si autorizas:

1. **Solo lo seguro** (tests, docs, CI, datos): 10 tareas sin tocar modelo ni núcleo.
2. **También lo crítico con guardrails**: T05 (alias), T06 (n8n) y T07 (entrypoint), con el
   alcance corregido de este documento.
3. **Nada todavía**: leer y posponer.

No se ha ejecutado ninguna tarea. Este documento y el informe son los únicos ficheros añadidos.

---

## 2. Resumen en 30 segundos

| Pregunta | Respuesta |
| --- | --- |
| ¿Alguna tarea edita los cuadernos? | **No.** Cero ediciones en `notebooks/01-07`. |
| ¿Alguna toca el modelo desplegado? | **No.** `ensemble.joblib`, `bilstm_ds02.keras`, `scaler.joblib` y `ds02_manifest.json` quedan intactos. |
| ¿Alguna toca un modelo? | **Solo T05**, y es el **alias de clase** `models/mejor_modelo.joblib`, no el bundle servido. |
| ¿Alguna toca código crítico? | **T06** (`n8n/flujo.json`) y **T07** (`app/streamlit_app.py`). **T05/T09** solo si eliges la variante de código. |
| ¿Alguna toca el núcleo de inferencia o reglas? | **No.** `src/ds02_rul/*`, `src/mia/*`, `app/dashboard_ds02.py`, `app/ui_modulos/*`, `app/api.py` quedan fuera. |

**Conclusión:** puedes autorizar 10 tareas sin riesgo para el modelo o el núcleo; 4 necesitan
que apruebes un alcance concreto, no la redacción original.

---

## 3. Tabla de decisión (14 tareas)

| ID | Tarea | ¿Notebooks? | ¿Modelo? | ¿Código crítico? | Riesgo | Beneficio | Decisión |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| T01 | Fixture de tests idempotente y exception-safe | No | No | No | Bajo | 10 | **Aprobar tal cual** |
| T02 | Versionar `data/processed` + checksum del HDF5 | No | No | No | Medio | 9 | **Aprobar opción A** (sin script nuevo) |
| T03 | Commitear la corrección 13→17 | No | No | No, pero índice | Bajo | 9 | **Aprobar con staging por ruta** |
| T04 | Corregir `src/clase/README.md:82` | No | No | No | Bajo | 7 | **Aprobar tal cual** |
| T05 | Procedencia de `mejor_modelo.joblib` | No | **Sí: alias de clase** | Opcional: `train_clasicos.py` | Bajo/Medio | 6 | **Solo copia byte a byte** |
| T06 | Rama de descarte en el switch n8n | No | No | **Sí: `n8n/flujo.json`** | Bajo/Medio | 6 | **Aprobar con validación** |
| T07 | Aviso de `secrets.toml` mal formado | No | No | **Sí: entrypoint** | Bajo/Medio | 5 | **Solo logging; banner aparte** |
| T08 | Ajustar la frase del test único | No | No | No | Bajo | 6 | **Aprobar tal cual** |
| T09 | Documentar MLflow histórico vs live | No | No | No (doc-only) | Bajo | 6 | **Solo doc** |
| T10 | Retirar o redirigir `scripts/predict.py` | No | No | No | Bajo | 5 | **Aprobar tal cual** |
| T11 | Re-apuntar `needs_oof` y borrar guard muerto | No | No | No | Bajo/Medio | 6 | **Aprobar tal cual** |
| T12 | Tabla de coste del error | No | No | No | Medio | 8 | **Aprobar tal cual** |
| T13 | Ampliar CI con los gates | No | No | No | Bajo | 7 | **Aprobar después de T01/T02** |
| T14 | SHAP, wrapper y `.gitignore` | No | No | No | Bajo | 3 | **Aprobar tal cual** |

---

## 4. Las cuatro que necesitan alcance corregido

### T05 — toca el alias, no el bundle servido

**Qué tocaría:** `models/mejor_modelo.joblib` (526.049 B, SHA `5aab4d2a…`), `models/README.md` y,
si se elige la variante de código, `src/clase/train_clasicos.py`.

**Por qué no vale la redacción original:** el «manifiesto» que citaba ya contiene el SHA del
clásico en `models/ds02_manifest.json:199` (`clase_xgb_sha256`). Volver a serializar con
`joblib.dump` puede cambiar los bytes y obligaría a reescribir el manifiesto; eso invalidaría
`seal_ok` y `app/cache/cache_manifest.json`, que son la puerta G0 del bundle servido.

**Alcance seguro:**

- Copiar **byte a byte** con `shutil.copy2` desde `models/mejor_modelo_clase.joblib`.
- **No** tocar `models/ds02_manifest.json`.
- **No** ejecutar `train_clasicos.py` completo: reentrenaría los 5 modelos y reescribiría
  `resultados/comparativa.csv` y el joblib canónico.
- Verificar `sha256` idéntico y `tests/test_clase_rubrica.py::test_mejor_modelo_alias_paridad`.

**Alternativa aún más conservadora:** dejar T05 en **doc-only** (explicar en `models/README.md`
que el alias es copia manual). No toca el modelo; beneficio 4, no 6.

---

### T06 — el fallback no cubre el camino de la app

**Qué tocaría:** `n8n/flujo.json` (switch con 3 salidas: APTO, INSPECCION, HANGAR).

**Por qué no vale la redacción original:** la app **nunca envía** `SIN_DECISION`.
`app/ui_n8n.py:52` (`debe_notificar`) solo deja pasar HANGAR, INSPECCION y APTO. El fallback
protege llamadas externas o malformadas, no el flujo de la app. Además, la evidencia de
**29 ejecuciones** (25 success / 4 error, 2026-11-07) ya está documentada en
`docs/defensa/guiones-15min.md:6` y `src/clase/README.md:19`; no hace falta re-ejecutar n8n.

**Alcance seguro:**

- Añadir 4ª salida (NoOp/Set) y su conexión para decisión desconocida.
- Actualizar `tests/test_n8n_decision.py` para cubrirla.
- **No** re-ejecutar el flujo para «generar evidencia»; si se quiere artefacto, exportar el
  historial existente.
- Validar el JSON con el validador de n8n o, como mínimo, con un test de estructura.

---

### T07 — el banner rompería el arranque de Streamlit

**Qué tocaría:** `app/streamlit_app.py` (entrypoint) y, si se quiere banner visible,
`app/dashboard_ds02.py`.

**Por qué no vale la redacción original:** el entrypoint **no importa `st`**; la app real llama a
`st.set_page_config` en `app/dashboard_ds02.py:510`, y ese debe ser el primer comando de Streamlit.
Un `st.warning` en el entrypoint rompería el arranque o exigiría tocar el dashboard, que es código
crítico de UI.

**Alcance seguro:**

- Sustituir el `pass` por `logging.warning` + un flag de entorno (p. ej. `DS02_SECRETS_ERROR`).
- **No** poner `st.warning` en `streamlit_app.py`.
- El banner visible, si se quiere, va en **tarea aparte** dentro de `dashboard_ds02.py`, después de
  `set_page_config`, con su propio test.

---

### T09 — el tracking live ya existe; lo que falta es doc

**Qué tocaría:** README/guion; en la variante de código, `src/clase/train_*.py`.

**Por qué no vale la redacción original:** `src/ds02_rul/mlflow_live.py` existe, los NB01-07 están
instrumentados y `tests/test_mlflow_backfill.py::test_notebooks_instrument_mlflow_live` lo exige.
Lo que no hay es **ningún run live**: `grep -rl live_notebook mlruns` = 0; los 17 canónicos son
`fuente=historico`. Añadir logging a los scripts de entrenamiento crearía runs mal etiquetados y
podría reescribir `models/` si alguien los ejecuta.

**Alcance seguro:**

- **Doc-only:** «17 runs históricos + instrumentación live disponible, 0 runs live hasta
  re-ejecutar un notebook».
- **No** tocar `src/clase/train_*.py` ni `models/`.
- Si se quiere un run live, se ejecuta un notebook concreto y se etiqueta como tal; eso es una
  decisión aparte y no forma parte de T09.

---

## 5. Las diez que no tocan nada crítico

| ID | Ficheros | Nota de ejecución |
| --- | --- | --- |
| T01 | `tests/conftest.py` | **Cuidado:** manipula `app/registros_flota.json` y `app/registros_sesiones/`. Usar `try/finally`, no borrar hasta verificar la copia y limpiar respaldos obsoletos. |
| T02 | `data/processed`, `.gitignore`, `data/raw/README.md` | **Opción A:** versionar `processed` (30 MB) + checksum. **No** crear `scripts/build_dataset.py` todavía; sería una segunda fuente de verdad. |
| T03 | índice de git | **Trampa:** hay 19 `M`, incluido `app/streamlit_app.py`; `git add -A` commitearía código sin revisar. Stage por ruta. |
| T04 | `src/clase/README.md` | Solo texto; comprobar que tabla (`:73`) y frase (`:82`) coinciden. |
| T08 | `README.md` | Solo texto; la frase debe cuadrar con `resultados/mlp_comparativa.csv`. |
| T10 | `scripts/predict.py` | Legacy; retirar o lanzar error accionable hacia `predict_ds02.py`. |
| T11 | `tests/test_mia_rules.py`, `tests/test_audit_fixes.py` | Tests; adaptar claves a `src/mia/instrumento_oof.npz`. Verificar que el test corre de verdad, no solo que desaparece el skip. |
| T12 | README/defensa | Solo análisis; citar AOG 10-15k USD/h y `costes_reales_aeronauticos.md`, sin inventar una cifra única. |
| T13 | `.github/workflows/ci.yml` | **Orden:** después de T01/T02; si no, el CI nace rojo. Incluir `fix/*` o PR. |
| T14 | `README.md`, `.gitignore` | Texto + `*.hermes-respaldo`; no toca código. |

---

## 6. Lo que queda intacto con cualquier opción

- **Cuadernos:** `notebooks/01_eda_y_contexto.ipynb` … `07_shap_c_bundle_c.ipynb` (7 ficheros).
- **Modelo servido:** `models/ensemble.joblib` (`d6c70142…`), `models/bilstm_ds02.keras`,
  `models/scaler.joblib`, `models/ds02_manifest.json`.
- **Núcleo de inferencia:** `src/ds02_rul/*`.
- **Reglas y motor:** `src/mia/reglas.py`, `src/mia/motor.py`.
- **Dashboard y UI:** `app/dashboard_ds02.py`, `app/ui_modulos/*`, `app/api.py`.
- **Caché:** `app/cache/cache_manifest.json`.
- **Datos crudos:** `data/raw/` (2,3 GB) no se toca; T02 solo documenta su checksum.

---

## 7. Tres trampas que debes conocer antes de autorizar

1. **T03 no es “solo commitear”**: el árbol tiene 19 `M`; entre ellos `app/streamlit_app.py`
   (código) y un `M` externo aparecido durante la sesión en
   `docs/pendiente/plan-cierre-rubrica.md`. Hay que hacer `git add` por ruta, nunca `-A`.
2. **T13 puede nacer rojo**: si se añade `pytest` al CI antes de T01, el fixture seguirá fallando
   en este árbol; y si se añaden los gates antes de T02, un clon limpio no tendrá `data/processed`.
   Orden: T01 → T02 → T13.
3. **T01 toca estado de usuario**: el fixture mueve/borra `app/registros_flota.json` y
   `app/registros_sesiones/`. Aunque no es código crítico, un fallo a mitad puede perder la flota.
   Exigir `try/finally`, copia verificada y respaldos idempotentes.

---

## 8. Autorización recomendada (marca lo que quieras)

### Lote A — seguro, sin modelo ni núcleo

- [ ] **T01** Fixture idempotente y exception-safe.
- [ ] **T04** Corregir la contradicción del README de clase.
- [ ] **T08** Ajustar la frase del test único.
- [ ] **T10** Retirar o redirigir el CLI legacy.
- [ ] **T11** Re-apuntar `needs_oof` y borrar el guard muerto.
- [ ] **T12** Tabla de coste del error.
- [ ] **T14** SHAP, wrapper y `.gitignore`.

### Lote B — datos y git

- [ ] **T02** Versionar `data/processed` (30 MB) + checksum; sin script nuevo.
- [ ] **T03** Commit selectivo de la corrección 13→17.

### Lote C — crítico con guardrails

- [ ] **T05** Copia byte a byte del alias; sin manifiesto, sin reentrenar.
- [ ] **T06** 4ª salida del switch n8n + test; sin re-ejecutar.
- [ ] **T07** Solo `logging.warning` + flag; banner en tarea aparte.
- [ ] **T09** Doc-only de MLflow histórico vs live.

### Lote D — después

- [ ] **T13** CI con gates, una vez T01/T02 estén verdes.

**Si solo quieres el mínimo riesgo:** autoriza **Lote A + B**. Deja C para después de leer el
informe completo y D para cuando la suite esté verde.

---

## 9. Evidencia verificada para este documento

```text
$ git ls-files notebooks | wc -l
7                         # ninguna tarea los edita

$ sha256sum models/mejor_modelo.joblib models/mejor_modelo_clase.joblib
5aab4d2a050163c9d9db0d0d3f769c198fe2e47a1bf2959fb355ca6f4652615f  models/mejor_modelo.joblib
5aab4d2a050163c9d9db0d0d3f769c198fe2e47a1bf2959fb355ca6f4652615f  models/mejor_modelo_clase.joblib

$ grep -n 'clase_xgb_sha256' models/ds02_manifest.json
199:    "clase_xgb_sha256": "5aab4d2a050163c9d9db0d0d3f769c198fe2e47a1bf2959fb355ca6f4652615f",

$ grep -n 'set_page_config' app/dashboard_ds02.py
510:st.set_page_config(

$ grep -rl 'live_notebook' mlruns | wc -l
0                         # 19 meta.yaml = 17 runs + 2 metadatos de experimento
```

```text
$ grep -n 'DECISIONES_QUE_NOTIFICAN' app/ui_n8n.py
12:DECISIONES_QUE_NOTIFICAN = ("HANGAR", "INSPECCION", "APTO")

$ grep -rn '29 veces' docs/defensa/guiones-15min.md src/clase/README.md
# 29 ejecuciones (25 success / 4 error, 2026-11-07) ya documentadas
```

```text
$ git status --porcelain | awk '{print substr($0,1,2)}' | sort | uniq -c
     19  M
      3  ??
# 18 M preexistentes + docs/pendiente/plan-cierre-rubrica.md (externo)
# 3 ??: plan, respaldo vacío y este informe
```

---

## 10. Estado del árbol y qué he tocado yo

- **Informe principal:** `docs/informes/auditoria-2026-11-10-rubrica-ejecutada.md`
  (9 secciones, 14 tareas, §6.1 de radio de impacto).
- **Este documento:** `docs/informes/auditoria-2026-11-10-alcance-y-autorizacion.md`.
- **Código/modelo/notebooks/datos:** **sin cambios** por esta revisión.
- **`M` externo:** `docs/pendiente/plan-cierre-rubrica.md` apareció modificado durante la sesión;
  no lo he tocado. No afecta al análisis de alcance.

---

## 11. Lectura relacionada

- Informe completo: `docs/informes/auditoria-2026-11-10-rubrica-ejecutada.md` (§6.1).
- Procedencia de artefactos: `models/README.md`.
- Contrato de paridad del alias: `tests/test_clase_rubrica.py:73`.
- Flujo n8n: `n8n/flujo.json`; filtro de la app: `app/ui_n8n.py:52`.
- MLflow live: `src/ds02_rul/mlflow_live.py`; test: `tests/test_mlflow_backfill.py:184`.
