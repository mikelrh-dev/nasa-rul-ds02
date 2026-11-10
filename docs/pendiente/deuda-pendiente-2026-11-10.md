# Deuda diferida — cierre de la auditoría 2026-11-10

> **Veredicto: lo que queda pendiente no afecta al funcionamiento actual.**
> Se documenta aquí y se revisa más adelante. Nada de esta lista bloquea la
> app, la API, el modelo, los cuadernos ni la defensa.
> **Rama:** `fix/auditoria-2026-11-10` · **Fecha:** 2026-11-10

---

## 1. Qué se cerró (y ya está verificado)

| Tarea | Cambio | Verificación |
|---|---|---|
| T14 | `.gitignore` con `*.hermes-respaldo`; SHAP por contexto; entrypoint declarado wrapper | `git status` limpio |
| T04 / T08 / T12 | README de clase sin contradicción; frase del test de fila; tabla de coste del error | texto revisado |
| T07 | `pass` → `logging.warning` + `DS02_SECRETS_ERROR` | 31 tests de las piezas tocadas |
| T01 | Fixture idempotente y `exception-safe` (respaldo fuera de `app/`, `finally`) | `445 passed, 1 skipped`; dos pasadas con el registro intacto |

Gates al cerrar: `compileall` 0 · `freeze_rules_evidence --check` 0 ·
`freeze_oof_instrument --check` 0 · `backfill_mlflow --check` 0.

---

## 2. Qué SÍ cambia el comportamiento (intencional, no regresión)

1. **`app/streamlit_app.py` carga `.streamlit/secrets.toml`** en `os.environ`
   (`N8N_WEBHOOK_URL`, `N8N_WEBHOOK_TOKEN`) si el fichero existe y la variable
   no viene del shell. Antes el webhook solo llegaba por entorno.
2. **`/n8n-decision` acepta el token en `X-DS02-Token`** además del body
   (`x_ds02_token or req.token`). El contrato por body sigue intacto: los tests
   de 401/503/200 y el de idempotencia por `fingerprint` pasan.

Ninguna otra pieza de código de producción se ha tocado: `models/`, `src/`,
`notebooks/`, `resultados/` y `mlruns/` están intactos (SHA del bundle
`d6c70142…` y alias `5aab4d2a…` sin cambios).

---

## 3. Pendiente diferido

| ID | Qué queda | Riesgo | Beneficio | ¿Afecta hoy? | Si no se hace nunca |
|---|---|---:|---:|---|---|
| **T02** | Versionar `data/processed` (9 parquet, 30 MB) + `!` en `.gitignore` + checksum del H5 | 6 | 9 | **No**: la app y el modelo no leen esos parquet; solo 5 ficheros de test de clase | Un clon limpio no corre esa parte de la suite |
| **T13** | CI con `fix/*` + los 5 gates (depende de T02) | 4 | 7 | **No**: el CI actual sigue igual y no bloquea nada | La verificación sigue siendo manual |
| **T11-a** | Documentar el skip de `needs_oof` y borrar el guard muerto | 1 | 3 | **No**: 1 skip declarado | Un test no corre, pero se sabe |
| **T11-b** | Regenerar el instrumento OOF real (17.450 filas) | 8 | 6 | **No** | La regresión de NASA score sigue sin medirse |
| **T06** | 4ª salida del switch n8n | 5 | 6 | **No**: la app nunca envía `SIN_DECISION` | Una llamada externa con decisión rara se pierde en silencio |
| **T09** | Doc-only: 17 históricos + live instrumentado, 0 live | 2 | 6 | **No**: el store ya está coherente | La pregunta «¿lo trackeabas en vivo?» se responde de memoria |

**Aparcadas por otros subagentes:** T06 (n8n) y T09 (MLflow). No tocar
`n8n/flujo.json` ni `mlruns/` mientras estén trabajando.

---

## 4. Cuándo revisarlo

- Antes de abrir PR a `main` → **T13** (y T02 si el PR quiere CI verde).
- Si alguien necesita clonar el repo y correr la suite completa → **T02**.
- Si se re-ejecuta un cuaderno con MLflow en vivo → **T09** (documentar el run).
- Si se importa el flujo en otra instancia n8n → **T06**.

---

## 5. Cómo comprobar el estado sin tocar nada

```bash
python -m pytest tests -q -rs                 # 445 passed, 1 skipped
python scripts/freeze_rules_evidence.py --check
python scripts/freeze_oof_instrument.py --check
python scripts/backfill_mlflow.py --check
sha256sum models/ensemble.joblib              # d6c70142…
```
