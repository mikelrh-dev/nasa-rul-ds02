# Design: Cierre de auditoría de datos (sin notebooks ni n8n)

**Change:** `2026-11-12-cierre-auditoria-datos`
**Date:** 2026-11-12

## D1 — Multisemilla: el CSV vigente manda

El CSV `resultados/bundle_c_multiseed.csv` contiene solo las semillas 7 y 123.
La fila 42 se toma del manifiesto (`4.338 / 2336.2`). La media y la desviación
se calculan con `statistics.mean` y `statistics.stdev` (muestral, n=3):

```text
RMSE:  (4.338 + 4.371 + 4.291) / 3 = 4.333333...
std:   0.0402...
NASA:  (2336.2 + 2363.3 + 2305.9) / 3 = 2335.133...
std:   28.71...
```

Se publica `4.333 ± 0.040` y `2335.1 ± 28.7`.

Archivos que se actualizan (solo documentación vigente):

- `README.md` (tabla de estabilidad y texto de la media).
- `README.en.md` (misma tabla en inglés).
- `AGENT.md` (resumen de una línea).
- `src/clase/README.md` (sección de estabilidad).
- `docs/framework_auditoria.md` (§9, cifra citada).
- `docs/decisions/ADR-011-...md`: **no** se reescribe la decisión; se añade
  una sección `## Errata 2026-11-12` al final.

No se tocan:

- `notebooks/05_meta_ensemble_y_conformal.ipynb`.
- `notebooks/06_evaluacion_produccion_comparativa.ipynb`.
- `docs/informes/auditoria-*` (son registros históricos; la errata va en el
  informe nuevo, no en los antiguos).

## D2 — Test OOF contra el instrumento congelado

`src/mia/instrumento_oof.npz` tiene `units`, `cycles`, `y`, `pred_ema`, `beta`.
El test actual usa `_p1_oof_cache.npz` y las claves `p_lstm` / `p_lgb`, que no
existen en el instrumento.

Nuevo flujo del test:

1. Cargar `src/mia/instrumento_oof.npz`.
2. Filtrar las unidades puras `[2, 5, 10, 18, 20]`.
3. Ordenar por unidad/ciclo y aplicar `R.pava_causal_no_creciente` sobre
   `pred_ema`.
4. Comparar `calculate_nasa_score(y, corregido)` contra
   `calculate_nasa_score(y, pred_ema)`.

Comprobación previa (solo lectura): el NASA Score baja de `24863.07` a
`24778.61`; la aserción se mantiene.

Se elimina el `needs_oof` basado en `_p1_oof_cache.npz`. Si se quiere un
guard, se usa `src/mia/instrumento_oof.npz` y se comprueban sus claves.

## D3 — Máscara MAR en `auditoria_nulos.json`

`inyectar_nulos_mar` ya devuelve `(df, audit)`. Se añaden tres claves al audit,
sin cambiar la firma:

```json
{
  "mascara_version": 1,
  "mascara_columnas": {
    "T30": [[0, 2.0, 1], [3, 2.0, 1]]
  },
  "mascara_sha256": "..."
}
```

- `mascara_columnas`: solo las columnas tocadas (hoy `T30`); cada posición es
  `[fila, unit, cycle]`. `unit`/`cycle` solos no bastan: hay varias muestras
  por ciclo (1.185 nulos, 273 pares únicos). `fila` es el índice del frame de
  entrada, cuyo orden fija el builder.
- `mascara_sha256`: SHA-256 de `json.dumps(mascara_columnas, sort_keys=True,
  separators=(",", ":"))`, para comparar sin recorrer la lista.
- `nulos_inyectados` debe seguir siendo igual a la suma de longitudes.

Tests nuevos en `tests/test_clase_dataset.py`:

- longitud total de la máscara == `audit["nulos_inyectados"]`;
- solo aparece la columna `T30`;
- no hay índices de fila duplicados;
- el SHA coincide con el contenido;
- `--check` sigue OK tras regenerar el JSON.

## D4 — Manifiesto golden y `--fast-check`

Nuevo `data/processed/dataset_manifest.json` (ignorado por git):

```json
{
  "format_version": 1,
  "pandas": "3.0.6",
  "pyarrow": "26.0.1",
  "artefactos": {
    "train.parquet": {
      "sha256": "...",
      "huella_contenido": "...",
      "filas": 52635,
      "columnas": 23
    }
  },
  "auditoria_sha256": "...",
  "mascara_sha256": "...",
  "receta": {
    "seed": 7,
    "test_units": [11.0, 14.0, 15.0],
    "medianas": {"T24": 0.0}
  }
}
```

- `sha256`: bytes exactos del parquet. Es la identidad del artefacto congelado.
- `huella_contenido`: la misma `_huella_contenido` que ya usa el builder.
- `pandas` / `pyarrow`: versiones que condicionan la estabilidad de la huella.
- `receta`: seed, unidades de test y medianas de train; permite detectar un
  cambio de receta aunque el parquet se reescriba.

`--fast-check`:

1. Lee `dataset_manifest.json`; si falta, devuelve 1 con mensaje claro.
2. Verifica que cada artefacto existe y su SHA-256 de bytes coincide.
3. Verifica `auditoria_sha256` y `mascara_sha256`.
4. No carga el HDF5 ni reconstruye nada.

`--check` sigue siendo la reconstrucción completa desde el HDF5 y compara
**contenido**, no bytes: el parquet no es canónico y una reescritura del mismo
DataFrame cambia el SHA. Por eso `--check` no compara el manifiesto; la
integridad de bytes es responsabilidad de `--fast-check`.

## D5 — Verificación

Comandos focalizados:

```bash
python -m pytest tests/test_mia_rules.py tests/test_clase_dataset.py -q -p no:cacheprovider
python -m src.clase.dataset_clase --check
python -m src.clase.dataset_clase --fast-check
git diff --check
```

La suite completa **no** se pone verde con este cambio: quedan los 3 fallos
del `00_datos` y el fallo de `n8n/flujo.json`, ambos fuera de alcance. El
informe de verificación debe decirlo con esas palabras.

## D6 — Boundaries

- **Always:** ejecutar los tests focalizados; comprobar que ningún `.ipynb` ni
  `n8n/` aparece en `git diff`; conservar los hashes de los parquet.
- **Ask first:** cambiar la fuente multisemilla, tocar `models/`, cambiar el
  esquema del manifiesto de forma incompatible.
- **Never:** editar notebooks, editar `n8n/`, reentrenar, borrar `mlruns/`.
