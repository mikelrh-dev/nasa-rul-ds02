# Spec: Cierre de auditoría de datos (sin notebooks ni n8n)

**Capability:** `ds02-datos-reproducibilidad`
**Change:** `2026-11-12-cierre-auditoria-datos`

## R1 — Cifras multisemilla vigentes

La documentación actual MUST publicar la media y la tabla calculadas desde el
CSV vigente más la fila 42 del manifiesto.

- Media RMSE: `4.333`
- Std RMSE: `0.040`
- Media NASA: `2335.1`
- Std NASA: `28.7`

La cifra `4.324 ± 0.107 / 2341.0 ± 54.1` MUST quedar marcada como histórica
(CSV anterior `72035c3`), nunca como vigente.

### Scenario: README coherente con el CSV

- **Given** `resultados/bundle_c_multiseed.csv` con `7=4.371` y `123=4.291`
- **And** el manifiesto con `42=4.338`
- **When** se lee la tabla multisemilla de `README.md`
- **Then** la tabla muestra esos tres valores
- **And** la media es `4.333 ± 0.040`
- **And** `4.324 ± 0.107` solo aparece como histórica/errata.

### Scenario: no se tocan notebooks

- **Given** el cambio aplicado
- **When** se ejecuta `git diff --name-only`
- **Then** no aparece ningún `.ipynb`.

## R2 — Test OOF sin skip

El test de corrección OOF MUST ejecutarse contra
`src/mia/instrumento_oof.npz` y MUST comprobar que la corrección baja el NASA
Score.

### Scenario: el test corre y mejora

- **Given** el instrumento congelado con `units`, `cycles`, `y`, `pred_ema`
- **When** se ejecuta `pytest tests/test_mia_rules.py -q`
- **Then** el test no se salta
- **And** `calculate_nasa_score(y, corregido) < calculate_nasa_score(y, pred_ema)`.

## R3 — Máscara MAR guardada

`auditoria_nulos.json` MUST incluir `mascara_version`, `mascara_columnas` y
`mascara_sha256`.

- La suma de posiciones MUST ser `nulos_inyectados` (1.185 en el dataset actual).
- Cada posición MUST ser `[fila, unit, cycle]`.
- No MUST haber índices de fila duplicados.
- `mascara_sha256` MUST coincidir con el JSON canónico de `mascara_columnas`.

### Scenario: máscara completa y verificable

- **Given** el build ejecutado
- **When** se lee `data/processed/auditoria_nulos.json`
- **Then** hay 1.185 posiciones en `T30`
- **And** el SHA coincide
- **And** `--check` sigue devolviendo 0.

## R4 — Manifiesto golden y comprobación rápida

El build MUST escribir `data/processed/dataset_manifest.json` con SHA-256 de
bytes, huella de contenido, filas, columnas, versiones y receta.

`--fast-check` MUST verificar el manifiesto y los artefactos sin cargar el
HDF5.

### Scenario: fast-check íntegro

- **Given** el manifiesto y los 8 parquet presentes
- **When** se ejecuta `python -m src.clase.dataset_clase --fast-check`
- **Then** devuelve 0 y no carga el HDF5.

### Scenario: fast-check detecta manipulación

- **Given** una copia del manifiesto y un parquet con un byte cambiado
- **When** se ejecuta `--fast-check` contra esa copia
- **Then** devuelve 1 y nombra el artefacto alterado.

## R5 — Límites duros

- El cambio MUST NOT modificar ningún `.ipynb`.
- El cambio MUST NOT modificar `n8n/`.
- El cambio MUST NOT modificar `models/`.
- El cambio MUST NOT afirmar que la suite completa pasa: quedan 4 fallos
  conocidos fuera de alcance.

## Success Criteria

- Tests focalizados en verde.
- `--check` y `--fast-check` en 0.
- `git diff --name-only` sin `.ipynb`, `n8n/` ni `models/`.
- README y documentación vigente sin `4.324` como cifra actual.
