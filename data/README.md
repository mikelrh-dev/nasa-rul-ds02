# data/

- `data/raw/` — HDF5 original: **no versionado**. Se espera en
  `data/raw/N-CMAPSS_DS02-006.h5`, 2,28 GiB, SHA-256
  `47971a68b239ecb756833218a95d68ded6eb7e63ee84e86671c8b188de1ca765`.
- `data/processed/` — 8 parquet del track de clase: **versionados por Git LFS**
  (30 MB). Tras clonar: `git lfs install && git lfs pull`.

Regenerar: `python -m src.clase.dataset_clase` (verifica con `--fast-check`) y
`python scripts/build/build_ui_cache.py`. El SHA de cada parquet está en
`data/processed/dataset_manifest.json`.
