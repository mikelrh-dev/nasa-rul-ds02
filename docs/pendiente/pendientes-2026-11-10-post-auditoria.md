# Pendientes tras la auditoría — 2026-11-10 (HEAD `c14d91b`)

> Foto de estado al cerrar la auditoría
> [`auditoria-2026-11-10-rubrica-post-cierre.md`](../informes/auditoria-2026-11-10-rubrica-post-cierre.md).
> Sustituye a `deuda-riesgo-7-2026-11-10.md` **solo en los recuentos**; ese documento sigue
> valiendo para el plan de adopción del bundle B y para la desversión de `mlruns/`.
> Rama `fix/auditoria-2026-11-10`. Nada de esto está commiteado: el árbol tiene 94 rutas
> sucias, todas bajo `mlruns/` (13 `M` + 81 `??`).

---

## 1. Qué funciona (verificado hoy)

| Comprobación | Resultado |
| --- | --- |
| Suite completa | **444 passed, 1 skipped, exit 0** (246,6 s) |
| Único skip | `tests/test_mia_rules.py:181` — `_p1_oof_cache.npz missing` (pendiente 3) |
| `compileall src app scripts tests` | exit 0 |
| `freeze_rules_evidence.py` | exit 0 |
| `freeze_oof_instrument.py --check` | exit 0 · cobertura 0.901643 · 14 915 filas puras |
| `backfill_mlflow.py --check` | exit 0 · 13 runs (9 fila + 4 ventana), export y store coinciden |
| Artefactos | `ensemble d6c70142…`, `bilstm bf9620a7…`, `scaler acccfab3…`, manifiesto `6089457c…`; sello de caché `True` |
| API / n8n | `POST /n8n-decision` con 9 tests; instancia n8n responde 200 |
| Rúbrica v5 | **SAA 10,0 · PIA 9,4 · MIA 10,0** (techo PIA 9,4) |

Lo único que separa el proyecto del 10 es **PIA-4**, por cómo está registrado MLflow
(pendientes 1 y 2). No hay ningún criterio roto por un fallo funcional.

---

## 2. Pendiente 1 — El store `mlruns/` no viaja en git (A, afecta a PIA-4)

**Síntoma.** 13 `meta.yaml` modificados y 81 runs sin seguimiento. `git ls-files mlruns`
devuelve 1010 ficheros, pero no los 81 nuevos; el árbol queda con 94 rutas sucias.

**Consecuencia.** Un clon limpio no reproduce los 13 runs que documenta
`docs/evidencia/mlflow/comparativa.csv`; `backfill_mlflow.py --check` depende de `./mlruns`
local. Es el motivo por el que PIA-4 se queda en 7 aunque el resto del criterio esté cubierto
(13 runs con params/métricas, comparativa y 3 capturas).

**Dos salidas posibles, excluyentes:**

- **A — Versionar los 13 runs.** Añadir al índice `mlruns/<exp>/<run>/{meta.yaml,metrics,params,tags}`
  de los 13 runs del export (sin `artifacts/`, que ya están ignorados) y commitear.
  Criterio de aceptación: `git status --porcelain mlruns/ | wc -l` = 0 y
  `git ls-files mlruns | wc -l` crece en ~65–80 ficheros.
- **B — Ignorar el store.** `git rm -r --cached mlruns` + `mlruns/` en `.gitignore` y conservar
  `docs/evidencia/mlflow/*` como evidencia congelada. Requiere sembrar `mlruns/` temporal en
  `tests/test_mlflow_backfill.py` (ver `deuda-riesgo-7-2026-11-10.md` §B5, riesgo 7).

El resto de runs del store (27 antiguos) no forman parte del entregable; si se elige A, se
versionan solo los 13 del export.

## 3. Pendiente 2 — La ablación `cyc_norm` no es una run de MLflow (M, PIA-4)

**Síntoma.** `README.md:286-292` publica la tabla de la ablación y
`resultados/ablacion_cycnorm_rmse.png` la dibuja, pero
`grep -ril "cyc_norm\|abla" mlruns --include=meta.yaml` → **0**.

**Datos ya medidos (no hay que reentrenar):** `cyc_norm ON (BiLSTM) + OFF (meta)` → BiLSTM
5.419 / meta 4.338; `OFF (BiLSTM) + OFF (meta)` → BiLSTM 6.513.

**Propuesta.** Una run `ablacion__cyc_norm` en el experimento de MLflow con
`params={canal_19: on/off, meta_cycle: off}` y `metrics={rmse_bilstm, rmse_meta}`, más una
captura. El script `scripts/ablate_meta_cycle.py` ya produce los números; falta registrarlos.

**Criterio de aceptación.** `grep -ril cyc_norm mlruns --include=meta.yaml` ≥ 1 y la fila
aparece en `docs/evidencia/mlflow/comparativa.csv`.

## 4. Pendiente 3 — El guard `needs_oof` apunta a un fichero inexistente (A)

`tests/test_mia_rules.py:181` usa `@needs_oof`, que comprueba `_p1_oof_cache.npz`
(gitignored, ausente) en vez del instrumento versionado `src/mia/instrumento_oof.npz`
(ADR-012). El guard definido en `tests/test_audit_fixes.py` no lo usa nadie: **guard muerto**.

**Propuesta.** Re-apuntar la fixture al instrumento (claves distintas: hay que adaptar el
test, no solo la ruta) y borrar el guard muerto.

**Criterio de aceptación.** Suite con **0 skips** (`-q -rs`) y 445 passed.

## 5. Pendiente 4 — `scripts/predict.py` apunta a un bundle archivado (M)

`scripts/predict.py:22` resuelve `models/v3_bundle.joblib`, que no existe: el manifiesto lo
declara archivado (`historical_reference:180-181`) y `scripts/v3_finalize.py` ya no lo escribe.
El CLI FD001 queda fuera de servicio y muere con `RuntimeError` (honesto, pero opaco).

**Propuesta.** Mensaje explícito («el CLI FD001 está fuera de servicio; usa
`scripts/predict_ds02.py`») o retirar el script.

## 6. Pendiente 5 — Respaldo de Hermes versionado dentro de `app/` (M)

`app/registros_flota.json.hermes-respaldo` (49 B) está en el índice desde `fbec2d2`.

**Propuesta.** `git rm app/registros_flota.json.hermes-respaldo` y añadir
`*.hermes-respaldo` a `.gitignore`. El directorio gemelo
`app/registros_sesiones.hermes-respaldo/` ya está fuera del índice.

## 7. Pendiente 6 — `deuda-riesgo-7-2026-11-10.md` estaba obsoleto (M)

Decía «28 `meta.yaml` versionados (106 en disco)» y citaba `tests/test_mlflow_ui.py`, que no
existe. **Corregido en este mismo commit de documentación** (recuentos reales y test
existente); el resto del documento sigue vigente.

## 8. Menores (B) — no afectan a ninguna nota

- Cobertura en dos valores sin alcance: `e00:145` y `README.en:365` dicen 0.9012; el
  instrumento mide 0.901643.
- `docs/assets/` duplica 9 PNG de `resultados/`: 7 idénticos y 2 divergentes
  (`real_vs_predicho_bundle_c.png`, `shap_importancia.png`).
- Manifiesto 4.338/3.227 vs caché 4.3382/3.2266 (dos precisiones).
- `freeze_oof_instrument.py:46,80` carga `notebooks/artifacts_c/nb2_selection.joblib`
  (gitignored) sin verificar hash.
- `n8n/flujo.json` lleva 2 × `REEMPLAZAR_CREDENCIAL` y `active:false`: no es importable y
  ejecutable tal cual (documentado en el propio flujo con sticky notes).

---

## 9. Orden recomendado

1. **Pendientes 1 + 2** (los únicos con impacto en nota): PIA-4 pasaría de 7 a 10 → PIA 10,0.
2. **Pendiente 3**: deja la suite sin skips.
3. **Pendientes 5 y 6**: higiene, 10 minutos.
4. **Pendiente 4 y menores**: cuando toque tocar esas zonas.

## 10. Verificación al cerrar

```bash
.venv/Scripts/python.exe -m pytest tests -q -rs -p no:cacheprovider   # esperado: 0 skips
.venv/Scripts/python.exe scripts/backfill_mlflow.py --check           # 14 runs tras la ablación
git status --porcelain | wc -l                                        # 0 rutas sucias
grep -ril cyc_norm mlruns --include=meta.yaml | wc -l                 # >= 1
```
