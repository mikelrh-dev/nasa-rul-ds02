# Proposal: banda verificada contra un instrumento congelado, y retirada de Docker

**Change:** `2026-11-07-banda-instrumento-y-auditoria`
**Status:** Applied — ver `verify-report.md`
**Capability:** `ds02-rules-engine` (MODIFIED) y `ds02-dss-ui` (MODIFIED). Sin delta en
`rul-prediction-ds02` ni en `ds02-live-evaluation`; la retirada de Docker no toca
requisitos de ninguna capacidad.
**Rama:** `clase-modelo-c`
**Fecha:** 2026-11-07

---

## Why

Tres problemas, uno de fondo:

1. **El gate comparaba dos instrumentos distintos.** `mia/calibracion_banda.json` se
   re-congeló el 2026-11-04 (commit `d02ff2d`, "recalibration banda R6 a bundle C") a
   partir de `notebooks/artifacts_c/nb2_selection.joblib`, que está git-ignored. El gate
   (`scripts/freeze_rules_evidence.py`) reconstruía su propio instrumento desde
   `_p1_oof_cache.npz` —las filas step-1, 17 450— y lo comparaba con una banda calibrada
   sobre 14 915 filas step-3. Reportaba **drift que no existía en el JSON** y dejaba 5
   tests en rojo. Un gate rojo por un error de contabilidad enseña a ignorar el gate.
2. **La UI prometía más de lo que dice.** El rótulo decía `Banda 90 %`, que se lee como
   cobertura conseguida, cuando 0,90 es el **objetivo nominal**.
3. **El proyecto no llevará contenedores.** `Dockerfile`, `docker-compose.yml` y las notas
   SEC-DOCK-ST-01 describen un despliegue que no se va a usar ni se ha construido nunca.

## Scope

**In scope**

- Instrumento out-of-fold **versionado**: `src/mia/instrumento_oof.npz` (115 225 B,
  14 915 filas: `units`, `cycles`, `y`, `pred_ema`).
- Escritor/verificador: `scripts/freeze_oof_instrument.py` (`--write` / `--check` /
  `--from-joblib`; exit 0/2/3/4).
- Gate con dos modos: por defecto **verifica la banda** contra el instrumento;
  `--cache PATH` re-deriva (camino de desarrollo) y sale 5 en este árbol.
- La tabla OOF de §13 queda `reported`, no `asserted`, en el camino por defecto.
- Tests re-apuntados al instrumento (5) y cobertura pura medida sobre él.
- Literal de UI: `objetivo nominal 90 % · cobertura medida empíricamente` y leyenda
  `objetivo 90 % · cobertura medida`.
- Retirada de Docker: los dos ficheros, los docstrings que los citan y las filas del
  framework de auditoría.

**Out of scope**

- Reentrenar, refit o recalibrar: la banda **no se toca** (`calibracion_banda.json` queda
  byte a byte igual) y `models/ds02_manifest.json` tampoco.
- Abrir o cerrar la banda. Se midió el bin de cola y está **sobre-cubierto** (0,9533); la
  propuesta anterior de ensancharla se retira.
- `_p1_oof_cache.npz`: sigue git-ignored y solo lo usa el camino de desarrollo.

## Capability

- **`ds02-rules-engine`** — requisito nuevo: la banda publicada MUST ser verificable
  desde un clon, y el camino de refit MUST declarar qué cifras no puede sostener.
- **`ds02-dss-ui`** — requisito modificado: la pantalla MUST nombrar el 90 % como objetivo
  nominal y la cobertura como medida.
- Docker: retirada operativa, sin delta de capacidad.

## What changes

| # | Superficie | Cambio |
| --- | --- | --- |
| 1 | `src/mia/instrumento_oof.npz` | nuevo, 14 915 filas, no ignorado |
| 2 | `scripts/freeze_oof_instrument.py` | nuevo; deriva, escribe y comprueba |
| 3 | `scripts/freeze_rules_evidence.py` | `--instrument`, `INSTRUMENT_KEYS`, default por instrumento, tabla `reported` |
| 4 | `tests/` | 5 tests re-apuntados, cobertura pura sobre el npz, 3 tests nuevos |
| 5 | `app/dashboard_ds02.py`, `app/ui_modulos/_tab_flota.py` | literal nuevo |
| 6 | `docs/decisions/ADR-012-…md` | decisión y alternativas rechazadas |
| 7 | `Dockerfile`, `docker-compose.yml` | **retirados** |

## Artifacts that stay byte-compatible

- `models/ds02_manifest.json` — `1085dd67aed8179174996f3939bd7715f757f954a822d440a093dd847d3eb8c9`
- `models/ensemble.joblib` — `d6c701429eed8623a9d900d922aca1922427d08ff8b4ec00604b8116c1a952dd`
- `models/bilstm_ds02.keras` — `bf9620a7de3bf9f8efa65c1993a96d8a95b903dc6fde72c772aa316f4c042219`
- `src/mia/calibracion_banda.json` — sin cambios: `n_calibration 14915`, bins
  `[5125, 6094, 3135, 561]`, `q_low [-4.3621, -9.0949, -24.5658, -24.7372]`,
  `global_quantiles [-21.2129, 19.7804]`
- `app/cache/*` — sin regenerar; su sello `manifest_sha256` sigue apuntando al mismo
  manifiesto.

## Rollback plan

- **Instrumento y gate:** borrar `src/mia/instrumento_oof.npz` y
  `scripts/freeze_oof_instrument.py`, y revertir `freeze_rules_evidence.py`; el gate vuelve
  al camino de caché y a salir 5. Nada de `models/` se mueve.
- **Tests:** revertir el commit del change; los 5 tests vuelven a medir sobre la caché y a
  fallar por el desajuste de instrumentos (estado conocido, documentado en ADR-012).
- **UI:** una línea en dos ficheros; revertir el literal no afecta a ningún cálculo.
- **Docker:** `git checkout <commit> -- Dockerfile docker-compose.yml` restaura ambos; no
  había build verificado, así que no se pierde evidencia.

## Open item before closing

`src/mia/instrumento_oof.npz` está en el árbol pero **sin commitear** (hallazgo A-01 de
`docs/informes/auditoria-2026-11-07-ds02.md`). Hasta que se añada al índice, el change no
puede declararse cerrado: en un clon el gate no encuentra instrumento.
