# data/

- `data/raw/` — HDF5 original (2,3 GB): **no versionado**. Origen, SHA-256 y
  comprobación en [`../docs/DATA.md`](../docs/DATA.md).
- `data/processed/` — 8 parquet del track de clase: **versionados por Git LFS**
  (30 MB). Tras clonar: `git lfs install && git lfs pull`.

Regeneración, verificación e integridad: [`../docs/DATA.md`](../docs/DATA.md).
