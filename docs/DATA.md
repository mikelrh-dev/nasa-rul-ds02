# Datos: qué hay en git y qué no

Este repo está pensado para que un `git clone` **ejecute la app y toda la suite
sin descargar nada más**. El único dato que no viaja en git es el HDF5 original.

## Versionado en git

| Ruta | Qué es | Cómo viaja |
|---|---|---|
| `data/processed/*.parquet` | 8 parquet del track de clase (30 MB) | **Git LFS** (`filter=lfs` en `.gitattributes`) |
| `data/processed/dataset_manifest.json` | SHA-256, filas y columnas de cada parquet | git normal |
| `data/processed/auditoria_nulos.json` | máscara MAR inyectada (posiciones y SHA) | git normal |
| `app/cache/*` | caché de solo lectura de la UI (`ds02_rows`, `ds02_windows`, manifiesto) | git normal |
| `models/*` | bundle C, scaler, BiLSTM, manifiesto y artefactos de clase | git normal |

Con eso, un clon limpio puede arrancar Streamlit, la API y pasar la suite
completa **sin** `data/raw/`.

> Git LFS: instálalo una vez (`git lfs install`). Si clonaste antes de que
> existiera el LFS, ejecuta `git lfs pull` para materializar los parquet.

## No versionado: HDF5 original

| Campo | Valor |
|---|---|
| Ruta esperada | `data/raw/N-CMAPSS_DS02-006.h5` |
| Tamaño | 2 450 472 504 bytes (2,28 GiB) |
| SHA-256 | `47971a68b239ecb756833218a95d68ded6eb7e63ee84e86671c8b188de1ca765` |
| Origen | NASA N-CMAPSS (DS02-006), repositorio público de prognósticos |

Se descarga aparte y se coloca en `data/raw/`. `src/ds02_rul/data.py`
(`resolve_ds02`) lo busca ahí; si falta, el pipeline y los notebooks fallan con
un mensaje explícito, pero la app y los tests no lo tocan.

Comprobación de integridad:

```bash
python - <<'PY'
import hashlib
p = "data/raw/N-CMAPSS_DS02-006.h5"
h = hashlib.sha256()
with open(p, "rb") as f:
    for b in iter(lambda: f.read(1 << 20), b""):
        h.update(b)
print(h.hexdigest())
PY
# esperado: 47971a68b239ecb756833218a95d68ded6eb7e63ee84e86671c8b188de1ca765
```

## Regenerar lo derivado (opcional)

Solo hace falta si cambias el HDF5, la receta de imputación o el bundle:

```bash
# data/processed/ (idempotente; --check no escribe, --fast-check valida el manifiesto)
python -m src.clase.dataset_clase
python -m src.clase.dataset_clase --fast-check

# app/cache/ a partir de models/ + data/processed/
python scripts/build/build_ui_cache.py
```

Los SHA resultantes deben coincidir con `data/processed/dataset_manifest.json`
y `app/cache/cache_manifest.json`; si no, el test de contrato lo detecta.
