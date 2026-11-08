# Tasks: banda verificada contra instrumento congelado + retirada de Docker

**Change:** `2026-11-07-banda-instrumento-y-auditoria`
**Status:** Applied (cerrado 2026-11-08: 1.4 verificado — `git ls-files --error-unmatch src/mia/instrumento_oof.npz` → 0; `--check` exit 0, 14915 filas)

Cada tarea cierra con su acceptance. Comandos desde la raíz del repo, con
`PYTHONPATH=src` y `.venv/Scripts/python.exe`. Nada escribe en `models/` ni en `app/cache/`.

## Review workload guard

```
Decision needed before apply: No (usuario autorizó el loop SDD y la retirada de Docker)
Chained PRs recommended: No (un change, tareas por fase)
400-line budget risk: Low (el npz es binario; el código son 3 ficheros)
```

---

## Fase 1 — Instrumento

### [x] 1.1 Derivar y congelar el instrumento
`scripts/freeze_oof_instrument.py --write` deriva desde `nb2_selection.joblib`: puras
(2/5/10/18/20) → cada 3.ª fila por unidad → EMA5 sobre `pred_meta` → `pred_ema`; escribe
`src/mia/instrumento_oof.npz`.
Acceptance: `--write` sale 0 y reproduce bins `[5125, 6094, 3135, 561]`, `q_low`
`[-4.3621, -9.0949, -24.5658, -24.7372]`, `global_quantiles [-21.2129, 19.7804]`,
`n_calibration 14915`.

### [x] 1.2 Verificar el npz contra el JSON publicado
`python scripts/freeze_oof_instrument.py --check`.
Acceptance: exit 0; el fichero tiene 14 915 filas y 115 225 B.

### [x] 1.4 Añadir el npz al índice (hallazgo A-01 de la auditoría)
`git add src/mia/instrumento_oof.npz scripts/freeze_oof_instrument.py docs/decisions/ADR-012-*.md`.
Acceptance: `git ls-files --error-unmatch src/mia/instrumento_oof.npz` → 0.
**Bloqueante para cerrar el change:** sin esto, un clon no tiene instrumento.

## Fase 2 — Gate

### [x] 2.1 Modo instrumento y autodetección
`INSTRUMENT_KEYS = ("units","cycles","y","pred_ema")`, `INSTRUMENT_EXPECTED = {"pure_rows": 14915}`,
`load_cache` marca `_mode`, `recompute` no re-deriva en modo instrumento.
Acceptance: `python scripts/freeze_rules_evidence.py --instrument` → 0.

### [x] 2.2 Default por instrumento y `--cache` explícito
`main()` prefiere el npz si existe; `--cache PATH` conserva la re-derivación.
Acceptance: sin flags → 0; `--cache _p1_oof_cache.npz` → 5.

### [x] 2.3 `_compare`/`_print_check_block` tolerantes y `reported`
Los campos ausentes en `expected` no se comparan; la tabla OOF no se imprime como contrato
en modo instrumento.
Acceptance: los 9 tests de `tests/test_rules_gate.py` verdes.

## Fase 3 — Tests

### [x] 3.1 Re-apuntar los 5 tests al instrumento
`test_el_gate_reproduce_la_banda_comprometida`, `test_el_gate_detecta_drift`,
`test_la_escritura_es_idempotente`, `test_el_gate_no_toca_el_json_si_las_cifras_derivan`,
`test_la_cobertura_pura_es_la_nominal`.
Acceptance: `pytest tests/test_rules_gate.py tests/test_mia_rules.py tests/test_audit_fixes.py -q` verde.

### [x] 3.2 Eliminar `needs_oof` de `test_rules_gate.py`
Acceptance: `grep -n "needs_oof" tests/test_rules_gate.py` vacío.

## Fase 4 — UI y documentación

### [x] 4.1 Literal de la banda
`app/dashboard_ds02.py` → `objetivo nominal 90 % · cobertura medida empíricamente`;
`app/ui_modulos/_tab_flota.py` → leyenda `objetivo 90 % · cobertura medida`.
Acceptance: `tests/test_live_eval.py` verde exigiendo `objetivo nominal 90 %` y `cobertura medida`.

### [x] 4.2 ADR y documentación del gate
`docs/decisions/ADR-012-verify-the-band-against-a-frozen-instrument.md`; docstring del gate,
`scripts/README.md`, `openspec/project.md` y los tres documentos de
`poda-redundancias-streamlit-2` actualizados al literal nuevo.
Acceptance: `grep -rn "Banda 90" openspec/changes/poda-redundancias-streamlit-2/` vacío.

## Fase 5 — Retirada de Docker

### [x] 5.1 Borrar los ficheros de contenedor
`git rm Dockerfile docker-compose.yml`.
Acceptance: `git ls-files Dockerfile docker-compose.yml` vacío.

### [x] 5.2 Limpiar las referencias
`app/api.py:27` (nota del Dockerfile) y `app/streamlit_app.py:18-22` (bloque SEC-DOCK-ST-01)
pasan a comandos locales; `README.md:35` y `README.en.md:20,389` dejan de proponer
`docker compose up`; `docs/framework_auditoria.md` marca C y `BUILD_CMD` como no aplicables.
Acceptance: `grep -rn "docker" AGENT.md README.md README.en.md app/*.py openspec/ docs/framework_auditoria.md`
sin coincidencias ejecutables.

## Fase 6 — Verificación y auditoría

### [x] 6.1 Auditoría integral según `docs/framework_auditoria.md` v1.0
Informe y cobertura en `docs/informes/auditoria-2026-11-07-ds02.md` y
`auditoria-2026-11-07-cobertura.csv` (732 filas, 0 sin tier).
Acceptance: los 18 bloques con veredicto y evidencia; 2 Altos, 3 Medios, 3 Bajos.

### [x] 6.2 Suite completa tras la retirada de Docker
Acceptance: `pytest tests -q -rs` → **345 passed, 0 skipped, exit 0** en 226,02 s; el gate de
reglas sigue en 0. Ver `verify-report.md`.

## Pendiente declarado (no bloquea el change)

- `C-01` (auditoría): `models/v3_bundle.joblib` archivado y `scripts/predict.py:24` sigue
  apuntando a `models/`.
- `M-01`: 2 tests se saltan sin `_p1_oof_cache.npz`.
- `G-01`, `I-01`, `L-01`, `M-02`, `B-01`, `H-01`: ver el informe de auditoría.
