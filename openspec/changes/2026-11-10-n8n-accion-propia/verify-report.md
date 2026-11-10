# verify-report — 2026-11-10-n8n-accion-propia

- **Fecha:** 2026-11-10
- **Rama:** `fix/auditoria-2026-11-10`
- **Entorno:** `C:/Users/mikel/Desktop/Pruebas/nasa` · `.venv/Scripts/python.exe` (Python 3.12.10, pytest 9.1.1)

## Resultado por fase

| Fase | Tarea | Estado | Evidencia |
|---|---|---|---|
| 1.2 | `app/registros_n8n.json` en `.gitignore` | ✅ | línea añadida junto a los otros registros |
| 2.1 | `tests/test_n8n_propia.py` RED | ✅ | 9 tests; colección correcta (`--collect-only`: 9 tests collected in 8.20s) |
| 2.3 | `POST /n8n-decision` en `app/api.py` | ✅ | +115 líneas: token `compare_digest`, 400/401/503, idempotencia por `fingerprint` |
| 2.4 | GREEN | ✅ | `9 passed in 9.28s` (exit 0) |
| 2.5 | Nodo `HANGAR API propia` | ✅ | `n8n/flujo.json`: 15 nodos, `HANGAR Gmail → HANGAR API propia` |
| 2.6 | JSON válido | ✅ | `json.load` ok, `active: false`, 3 ramas del switch intactas |
| 3.1 | Línea en guiones de defensa | ✅ | bullet «Acción propia en n8n (MIA-3)» |
| 3.2 | Línea en `src/clase/README.md` | ✅ | sección «Acción propia en n8n (MIA-3)» |
| 4.1 | Suite focal | ✅ | `36 passed in 8.80s` (exit 0) |
| 4.2 | Artefactos protegidos | ✅ | ver tabla de hashes |
| 4.3 | Este informe | ✅ | — |
| 1.1 | Snapshot previo de hashes | ⚠️ | no se tomó «antes»; los hashes de abajo son posteriores y coinciden con HEAD |

## Fase 2.4 — el bloqueo que dejó la sesión anterior

El subagente previo dejó el endpoint implementado pero **colgado**: `pytest tests/test_n8n_propia.py` no terminaba (`exit 124` tras 200 s) y el primer `POST` no respondía.

Diagnóstico real con `faulthandler.dump_traceback_later(20)`:

```
app/api.py:247  in _guardar_n8n_registros   ->  with _N8N_LOCK:
app/api.py:296  in n8n_decision
```

**Causa:** `_N8N_LOCK = threading.Lock()` no es reentrante, y `n8n_decision` ya lo toma (línea 291) antes de llamar a `_guardar_n8n_registros`, que vuelve a pedir el mismo lock (línea 247). Autodeadlock en el primer POST: no era el modelo, ni FastAPI, ni el entorno.

**Fix (una línea):** `_N8N_LOCK = threading.RLock()`.

| Antes | Después |
|---|---|
| `timeout 100 pytest tests/test_n8n_propia.py` → `exit 124` | `pytest tests/test_n8n_propia.py -q` → `9 passed in 9.28s` |

## Fase 4.1 — suite focal

```bash
.venv/Scripts/python.exe -m pytest \
  tests/test_n8n_propia.py tests/test_n8n_decision.py \
  tests/test_n8n_apto_post.py tests/test_security_api.py \
  -q -p no:cacheprovider
```

```
....................................                                     [100%]
36 passed in 8.80s
```

Exit code: **0**

## Fase 4.2 — artefactos protegidos

`git status --porcelain -- models/` devuelve solo `models/README.md` y `models/ds02_manifest.json`, **ambos ya modificados antes de este change** (estaban sucios al inicio de la sesión). Ningún binario bajo `models/` cambió respecto a HEAD.

| Artefacto | sha256 |
|---|---|
| `models/ensemble.joblib` | `d6c701429eed8623a9d900d922aca1922427d08ff8b4ec00604b8116c1a952dd` |
| `models/bilstm_ds02.keras` | `bf9620a7de3bf9f8efa65c1993a96d8a95b903dc6fde72c772aa316f4c042219` |
| `models/scaler.joblib` | `acccfab34dd15d248ba2ee507e345955bcc91cb62a8c4be6f6aa34c639541f8d` |

## Cambios de este change

| Fichero | Cambio |
|---|---|
| `app/api.py` | +115 líneas: `POST /n8n-decision` + `RLock` |
| `n8n/flujo.json` | +69 líneas: nodo `HANGAR API propia` y su conexión |
| `tests/test_n8n_propia.py` | nuevo, 9 tests |
| `.gitignore` | `app/registros_n8n.json` |
| `docs/defensa/guiones-15min.md` | bullet de la acción propia |
| `src/clase/README.md` | sección de la acción propia |

## Pendiente / notas

- **Commit:** pendiente de decisión del usuario (el change no autoriza commits).
- **Runtime:** el endpoint responde 503 si `N8N_WEBHOOK_TOKEN` no está configurado en el servidor; es el comportamiento contratado y está cubierto por test.
- **Tarea 1.1:** el snapshot «antes» de hashes no se llegó a tomar; los de arriba son posteriores y los binarios coinciden con HEAD.
