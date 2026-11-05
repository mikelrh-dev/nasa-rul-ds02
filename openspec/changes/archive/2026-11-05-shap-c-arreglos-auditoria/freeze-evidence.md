# Freeze evidence — `_p1_oof_cache.npz` (CACHE-DRIFT-01, Fase 2.3)

**Fecha:** 2026-11-05 · **Unidad:** 2-A · **Estado:** instrumento generado, gate con drift documentado (no silencioso).

## Instrumento

| Campo | Valor |
|---|---|
| Fichero | `_p1_oof_cache.npz` (gitignored, `_p1_*.npz`) |
| `sha256` | `f4650d8e03e0eb3603ad8efd68144322f18ccbafd077af18d892a283999e784d` |
| Bytes | 195721 |
| Filas | 17450 (units/cycles/y/p_lstm/p_lgb, sin NaN) |
| Ordenador | `python scripts/p1_oof_cache.py` desde `.venv` (372.4 s, 3 folds) |
| HDF5 origen | `data/raw/N-CMAPSS_DS02-006.h5` (2.4 GB, presente) |

## Gate: `python scripts/freeze_rules_evidence.py --check`

| Situación | Exit | Salida |
|---|---|---|
| Sin instrumento (antes de regenerar) | **3** | `freeze-rules-evidence: cannot verify` — `missing instrument: …\_p1_oof_cache.npz` + `rebuild it with: python scripts/p1_oof_cache.py` + RULES-06 |
| Con instrumento regenerado | **5** | `the frozen JSON violates RULES-05` — los conteos `bins[<i>].n` (5104/5804/3502/505 esperados vs 5125/6094/3135/561 observados) y cada figura OOF driftan (RMSE 9.491→9.940107, NASA 19257.1→20705.939, coverage 0.9012→0.944351; envelope y pure-rows OK) |

El exit **no es 0** y la salida nunca dice `skip`: el instrumento falta o driftan las cifras, el gate lo declara y para.

## Causa probable del drift

El instrumento se regeneró dentro de `.venv` (TF 2.21.0 / LightGBM 4.7.0 / sklearn 1.9.1) mientras que `mia/calibracion_banda.json` y las cifras `EXPECTED` del gate proceden del intérprete histórico de los notebooks (sistema 3.10: TF 2.21.0 / LightGBM 4.6.0 / sklearn 1.5.1, `openspec/config.yaml`). `freeze_rules_evidence.py` documenta que la tolerancia de `5e-3` del camino BiLSTM no determinista se excluyó para no ocultar drifts reales: las divergencias observadas son mayores que eso y no se aceptan en silencio.

## Qué NO se hizo en esta unidad

- No se re-froze `src/mia/calibracion_banda.json` (con `--write` o a mano): fuera de los ficheros autorizados de la unidad 2-A y exige una decisión del padre (re-freezar tras revisión vs. regenerar con el intérprete histórico). Las cifras EXPECTED tampoco se tocaron.
- No se tocó `models/`, `notebooks/` NB01-06, `src/clase/` ni `scripts/predict.py`. El `git diff` de `models/ds02_manifest.json` va a cargo del agente paralelo (clase); la caché se re-firmó tras su firma para que `cache_available()` quede vigente.

## Próximo paso propuesto (fuera de esta unidad)

Decidir con el padre: (a) re-freezar `mia/calibracion_banda.json` tras revisión de los nuevos bins/cifras, o (b) regenerar el OOF con el intérprete histórico y re-verificar. Hasta entonces el gate sigue en exit 5 explícito.

## Decision padre 2026-11-05 (verify)

Generar `_p1_oof_cache.npz` con `.venv` (3.12) des-skippea 5 tests de reglas que FALLAN por drift venv vs interprete historico de notebooks (system 3.10, ver openspec/config.yaml caveat). Sin el fichero: 3 passed + 5 skipped y GATE PASSED. Con el fichero: 5 failed. Decision: NO se deja el fichero generado en el repo (queda en scratch); freeze queda exit 3 en clon limpio y exit 5 documentado con OOF de venv. No se re-congela calibracion_banda.json (fuera de alcance, cambiaria las reglas).
