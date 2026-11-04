# Tasks: adopción del bundle C

**Change:** `2026-11-04-adopcion-bundle-c` · **Rama:** `clase-modelo-c`

Regla del change: **no se reentrena y no se ejecutan celdas de notebook**. La verificación es
estática (compileall, imports, pytest de contrato/caché/UI) más la regeneración de la caché
de la app, que no entrena nada. Los cuadernos quedan listos para que los ejecute el autor.

---

- [x] T1 · Rama y change abiertos
  - Acceptance: rama `clase-modelo-c` activa; `openspec/changes/2026-11-04-adopcion-bundle-c/` con proposal y tasks.
  - Verify: `git branch --show-current` → `clase-modelo-c`.
  - Resultado: OK.

- [x] T2 · Archivar B sin borrar carpetas
  - Acceptance: `notebooks/ds02_ensemble/` (3 ipynb + 2 md + 1 py), `scripts/build_02_notebook.py`,
    `src/clase/evaluar_b_en_adaptada.py` y `tests/test_clase_b_robusto.py` viven en `archive/`;
    `archive/models_b/` guarda los 4 artefactos de B con sus hashes.
  - Verify: `git status --porcelain` sin borrados en `notebooks/`; `ls archive/`.
  - Resultado: OK. `archive/notebooks-ds02-ensemble/`, `archive/scripts-bundle-b/`,
    `archive/src-clase/`, `archive/tests/`, `archive/models_b/`, `archive/cache_b/`.
    `archive/` sigue en `.gitignore` (75 ficheros ya trackeados): versionar lo archivado
    requiere `git add -f`.

- [x] T3 · Instalar C en `models/`
  - Acceptance: los 4 ficheros de `src/clase/models/` copiados a `models/`; `dataset` del manifiesto
    pasa a `"DS02"` con `dataset_variant`; hashes de artefacto intactos.
  - Verify: script de comprobación SHA-CASAN contra el manifiesto instalado.
  - Resultado: OK. `ensemble d6c701429eed8623…` y `bilstm bf9620a7de3bf9f8…` CASA.
    Añadidos `dataset_variant`, `historical_reference` (B, 4.251 / 2305.1) y el bloque
    `macro_rmse` que el contrato de la UI exige (leído de la caché, no transcrito).

- [x] T4 · Reestructurar `src/clase`
  - Acceptance: `train_ensemble_adaptado` escribe en `models/`, expone `entrenar(..., guardar=)`
    y `evaluar_semilla()`; `evaluar_c_multisemilla.py` agrega seeds y escribe su CSV;
    `tests/test_clase_c_multisemilla.py` cubre la agregación con datos sintéticos.
  - Verify: `python -m pytest tests/test_clase_c_multisemilla.py tests/test_clase_bundle_c.py -q`.
  - Resultado: OK. Nuevo `src/clase/puente_c.py` reconstruye `raw/dev/test/result` desde el
    bundle desplegado sin entrenar (lo consumen los cuadernos 03–06).

- [x] T5 · Caché desde la base imputada
  - Acceptance: `build_ui_cache.py --base adaptada` (por defecto) construye ventanas desde
    `data/processed/test_con_nulos.parquet` con el mismo grid (6.196) y registra la procedencia
    de la base; `--base limpia` reproduce el comportamiento anterior.
  - Verify: `python scripts/build_ui_cache.py --help` y revisión de `_raw_adaptada()`.
  - Resultado: OK y **ejecutado**. 3.293 + 760 + 2.143 = 6.196 ventanas; RMSE ponderado
    4.3382 y macro 5.0153, que es lo que firma el manifiesto. `source` declara `base` +
    SHA de los dos parquet; `h5`/`h5_sha256` solo en la rama `limpia`.
    El manifiesto viejo de B en `app/cache/` bloqueaba la carga (el verificador exige que el
    SHA case con *todos* los manifiestos); se retiró con copia previa en `archive/cache_b/`.

- [x] T6 · Notebooks 03/04/05 sin B
  - Acceptance: el puente ya no apunta a `notebooks/ds02_ensemble/artifacts/`; usa
    `models/ensemble.joblib` y `data/processed/*`; el orden didáctico no cambia. Sin ejecutar.
  - Verify: barrido de referencias muertas vacío; `json.tool` válido en cada `.ipynb`.
  - Resultado: OK. Cadena de estado propia en `notebooks/artifacts_c/` (ignorada por git);
    cada celda puente se busca la raíz del repo, así no depende del orden de ejecución.

- [x] T7 · Notebook 06 coherente con C desplegado
  - Acceptance original: veredicto "C cumple el umbral 4.25"; tabla multiseed por semilla;
    recarga bit-idéntica; nota de no-determinismo; rutas a `models/`.
  - **Desviación registrada:** C mide 4.338 > 4.25, así que el cuaderno **no** afirma que
    cumpla el umbral. Se despliega C con las cifras factuales y B como referencia histórica.
    Tabla multiseed por semilla (42 del manifiesto + 7 y 123 en vivo), celda de recarga
    reproducible y nota de no-determinismo de TF: sí.
  - Verify: `json.tool` válido; sin "B sigue en producción" ni "puerta D11".

- [x] T8 · Documentación y ADR
  - Acceptance: ADR-011 con la decisión y las alternativas; `AGENT.md` y README citan C como
    campeón; banner de histórico donde siguen apareciendo 4.251.
  - Verify: `ls docs/decisions | tail`; `grep -n "4.251" AGENT.md README.md`.
  - Resultado: `docs/decisions/ADR-011-deploy-bundle-c-archive-bundle-b.md`; actualizados
    `AGENT.md`, `README.md`, `README.en.md`, `src/clase/README.md` y `scripts/README.md`.

- [ ] T9 · Gate final
  - Acceptance: T1–T8 verdes; `compileall` limpio; suite de contrato/caché/UI verde;
    `verify-report.md` con lo ejecutado y los comandos que quedan al autor.
  - Estado: **parcial**. `compileall` 0; contrato + bundle C + multiseed 17 passed / 1 skipped;
    suite completa **16 failed / 260 passed / 7 skipped**. Los 16 caen en dos clases descritas
    en `verify-report.md`: 9 por la banda/reglas aún calibradas sobre B y 7 por un re-ejecutado
    del dashboard (`key='vista_modo'` duplicado). Ninguno toca el contrato del artefacto.
