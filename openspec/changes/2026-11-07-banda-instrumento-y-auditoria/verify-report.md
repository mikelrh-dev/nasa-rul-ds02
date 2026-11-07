# Verify report: banda contra instrumento congelado + retirada de Docker

**Change:** `2026-11-07-banda-instrumento-y-auditoria` · **Rama:** `clase-modelo-c` · **Fecha:** 2026-11-07
**Regla:** sin commit en este paso (no solicitado). El item 1.4 queda abierto por eso mismo.

## Gate

| Check | Resultado |
|---|---|
| `python -m pytest tests -q -rs` (suite completa) | **345 passed, 0 skipped, exit 0** — 226,02 s (pasadas previas: 159,35 / 174,92 / 294,10 s) |
| `python scripts/freeze_rules_evidence.py` (sin flags) | **exit 0** — verifica la banda contra el instrumento |
| `python scripts/freeze_rules_evidence.py --instrument` | **exit 0** |
| `python scripts/freeze_rules_evidence.py --cache _p1_oof_cache.npz` | **exit 5** — el refit no reproduce la tabla de 2026-10-26 (declarado, no oculto) |
| `python scripts/freeze_oof_instrument.py --check` | **exit 0** — el npz reproduce la banda a 4 decimales |
| `python -m compileall -q src app scripts tests` | exit 0 |
| Gate de la capa de reglas tras retirar Docker | **exit 0** |

## Cambios verificados

| Superficie | Evidencia |
|---|---|
| Instrumento `src/mia/instrumento_oof.npz` | 115 225 B, 14 915 filas, `units/cycles/y/pred_ema`; `git check-ignore` → 1 (no ignorado) |
| Bins y cuantiles | `[5125, 6094, 3135, 561]`, `q_low [-4.3621, -9.0949, -24.5658, -24.7372]`, `global [-21.2129, 19.7804]`, `n_calibration 14915` |
| Cobertura medida | **0,901643** (bin 0 0,9048 · bin 1 0,8906 · bin 2 0,8983 · bin 3 0,9533) |
| Tests re-apuntados | `test_rules_gate.py` 9 passed; con `test_mia_rules.py` 27 passed |
| Literal de UI | `test_live_eval.py` verde exigiendo `objetivo nominal 90 %` y `cobertura medida` |
| Docker | `git ls-files Dockerfile docker-compose.yml` → 0; `grep -rni docker` en ficheros vivos → solo la frase intencional de `README.en.md` y el método genérico del framework (bloque C, marcado NO APLICA) |

## Artefactos byte-compatibles

| Artefacto | SHA-256 | Cambió |
|---|---|---|
| `models/ds02_manifest.json` | `1085dd6…d3eb8c9` | **no** |
| `models/ensemble.joblib` | `d6c7014…1a952dd` | **no** |
| `models/bilstm_ds02.keras` | `bf9620a…cfe8434` | **no** |
| `src/mia/calibracion_banda.json` | sin cambios de contenido | **no** |
| `app/cache/*` | sello `manifest_sha256` intacto | **no** |

## Auditoría asociada

`docs/informes/auditoria-2026-11-07-ds02.md` + `auditoria-2026-11-07-cobertura.csv`
(732 filas, 0 sin tier). Veredicto **PASA CON RESERVAS** — 2 Altos, 3 Medios, 3 Bajos.

## Abierto (no bloquea el apply, sí el cierre)

| ID | Hallazgo | Qué falta |
|---|---|---|
| **A-01** | el instrumento no está en el índice | `git add src/mia/instrumento_oof.npz scripts/freeze_oof_instrument.py docs/decisions/ADR-012-*.md` |
| C-01 | `scripts/predict.py:24` apunta a `models/v3_bundle.joblib`, hoy en `archive/` | re-apuntar o retirar el CLI FD001 |
| M-01 | 2 tests se saltan sin `_p1_oof_cache.npz` | extender el npz con `p_lstm`/`p_lgb` o declarar el skip |
| G-01 | `4.368` publicado donde `e00` lo prohíbe | adoptar NB05 4.330 ± 0.053 |
| I-01 | cobertura 0,9012 no trazable en `project.md` | publicar 0,9016 con su comando |
| L-01 | `n8n/flujo.json` con `active: true` sin commitear | commitear con `active: false` |
| M-02 | un fallo aislado no reproducido en 6 pasadas | nombrar el test y dar holgura a la espera |
| B-01 / H-01 | `>=3.12` laxo; métricas en dos precisiones | `>=3.12,<3.13`; declarar redondeo en prosa |

## Cómo repetir esta verificación

```bash
PYTHONPATH=src .venv/Scripts/python.exe -m pytest tests -q -rs
PYTHONPATH=src .venv/Scripts/python.exe scripts/freeze_rules_evidence.py
PYTHONPATH=src .venv/Scripts/python.exe scripts/freeze_rules_evidence.py --cache _p1_oof_cache.npz
PYTHONPATH=src .venv/Scripts/python.exe scripts/freeze_oof_instrument.py --check
git ls-files Dockerfile docker-compose.yml | wc -l    # 0
```
