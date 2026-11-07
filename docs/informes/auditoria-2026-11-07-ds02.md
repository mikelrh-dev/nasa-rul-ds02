# Auditoría integral DS02 — 2026-11-07

> **Framework usado:** `docs/framework_auditoria.md` v1.0 (2026-11-07), §1 fases F0–F6,
> §3 bloques A–Q, §4 severidad C/A/M/B, §5 plantillas.
> **Veredicto global:** **PASA CON RESERVAS** — 2 hallazgos Altos, 3 Medios, 3 Bajos
> (C-02 retirado: el proyecto no llevará Docker, decisión del 2026-11-07); ninguna cifra
> publicada del bundle defendido queda invalidada.

---

## 1. Pregunta de auditoría y criterio de éxito

¿Se sostiene, con evidencia y desde el estado actual del repo, que el artefacto DS02
desplegado está descrito por lo que hay en disco, que las cifras publicadas salen de un
artefacto, y que el repositorio puede demostrarlo? Éxito = cada bloque A–Q con veredicto y
evidencia, y toda cifra publicada rastreada a su fuente.

## 2. Baseline (F0)

| Variable | Valor |
| --- | --- |
| Rama | `clase-modelo-c` |
| HEAD | `835fc583562e3bfd0d4adc519313c20af8c3dbfd` |
| Fecha commit | 2026-11-07 19:21:25 +0100 — `fix(mia3): Switch body.decision + Postgres sin id + APTO alcanzable + dedup solo si ok (gate 336+6)` |
| Árbol | **sucio: 23 rutas** (se audita este estado, no un commit limpio inexistente) |
| Intérprete | `.venv/Scripts/python.exe` — Python 3.12.10 |
| Deps clave | tensorflow 2.21.0 · keras 3.15.1 · lightgbm 4.7.0 · scikit-learn 1.9.1 · numpy 2.5.4 · pandas 3.0.6 · fastapi 0.151.0 · streamlit 1.66.0 · pytest 9.1.1 · pyarrow 26.0.1 |

Árbol en F0 (23): 6 modificados de código/tests (`app/dashboard_ds02.py`,
`app/ui_modulos/_tab_flota.py`, `scripts/freeze_rules_evidence.py`, 4 tests), 5
renombrados `models/* -> archive/fd001-legacy-20261107/*`, 4 docs, `n8n/flujo.json`, y 4
sin seguimiento (`ADR-012`, `plan-mlflow-pia4-10.md`, `freeze_oof_instrument.py`,
`src/mia/instrumento_oof.npz`).

### Hashes y sellos

| Artefacto | SHA-256 | Contra manifiesto |
| --- | --- | --- |
| `models/ensemble.joblib` | `d6c7014…1a952dd` | `artifacts.ensemble_sha256` **coincide** |
| `models/bilstm_ds02.keras` | `bf9620a…cfe8434` | `artifacts.bilstm_sha256` **coincide** |
| `models/ds02_manifest.json` | `1085dd6…d3eb8c9` | sellado en `cache_manifest.artifact.manifest_sha256` **coincide** |
| `archive/fd001-legacy-20261107/v3_bundle.joblib` | `47d809b…19b401f3c` | `artifacts.v3_bundle_sha256` coincide, **pero no está en `models/`** (C-01) |

**G0:** PASA. El bundle que sirve es el que el manifiesto firma.

## 3. Alcance

- **Dentro:** bloques A–Q sobre el árbol en F0; suite; gate de reglas; artefactos y bandas;
  API estática; UI viva; estructura n8n; documentación y cifras.
- **Fuera:** reentrenar cualquier modelo, releer el HDF5 de 2,45 GB, desplegar, `git push`,
  credenciales reales y **Docker**: el proyecto no llevará contenedores (decisión del
  2026-11-07). El bloque C queda fuera de alcance y el hallazgo C-02 se retira.
- **Dependencias externas:** API **caída** (`/health` → 000) y sin instancia n8n → J y L
  quedan **NO VERIFICABLE** en su parte viva, con techo declarado, no “PASA”.

## 4. Hipótesis (escritas antes de comprobar)

| # | Hipótesis | Veredicto |
| --- | --- | --- |
| H1 | La suite está verde y sin skips ocultos | **Confirmada con reserva**: 345 passed / 0 skips, pero 2 tests saltarían sin un fichero git-ignored (M-01) |
| H2 | Archivar el legacy FD001 no rompe nada vivo | **Refutada**: rompe `scripts/predict.py` (C-01) |
| H3 | El instrumento del gate está versionado | **Refutada**: existe, no está ignorado, y **no está trackeado** (A-01) |
| H4 | Las cifras publicadas son trazables al manifiesto | **Confirmada** para 4.338/3.227/0.9461/2336.2/5.0153; **refutada** para 0.9012 y para 4.368 (G-01, I-01) |

## 5. Resultado por bloque

| Bloque | Veredicto | Evidencia principal |
| --- | --- | --- |
| **A** Inventario | PASA CON RESERVAS | 732 ficheros versionados, **0 sin tier** (A 136 / B 423 / C 173); 677 sin inspeccionar (92,5 %) declarado |
| **B** Entorno | PASA CON RESERVAS | `compileall` exit 0; pins idénticos en `pyproject.toml` y `requirements.txt`; `requires-python >=3.12` laxo (B-01) |
| **C** Build/despliegue | **NO APLICA** | El proyecto no llevará Docker (decisión 2026-11-07). `Dockerfile` y `docker-compose.yml` siguen en el árbol: o se retiran, o se rotulan como no mantenidos |
| **D** Código/arquitectura | PASA CON RESERVAS | `compileall` 0; 0 marcadores TODO/FIXME/HACK; frontera capas respetada; referencia muerta a `models/v3_bundle.joblib` (C-01) |
| **E** Datos/fuga | PASA CON RESERVAS | escalers solo en fit-units (`features.py:5-7`); `ffill` causal por unidad (`dataset_clase.py:157-172`); sin `unit` como feature; cotejado por docstrings y grep, no releído el HDF5 |
| **F** Modelo | PASA CON RESERVAS | banda medida sobre el instrumento: **0,901643** (bins 0,9048/0,8906/0,8983/0,9533); disputa multiseed (G-01) |
| **G** Cifras | PASA CON RESERVAS | 4.338 / 3.227 / 0.9461 / 2336.2 / 5.0153 = manifiesto y `e00`; **0.9012 no trazable** (I-01); **4.368 en disputa** (G-01) |
| **H** Artefactos | PASA CON RESERVAS | hashes de ensemble y bilstm verificados antes de deserializar (`persistence.py`); instrumento **sin trackear** (A-01); ruta v3 muerta (C-01) |
| **I** Reglas | PASA | gate default **exit 0**; `--cache` **exit 5** (honesto); `n_calibration 14915`; bins `[5125, 6094, 3135, 561]`; `q_low [-4.3621, -9.0949, -24.5658, -24.7372]` |
| **J** API/seguridad | **NO VERIFICABLE** (viva) / PASA (estática) | `/health` → 000: sin proceso. Estático: `hmac.compare_digest`, 10 req/min por IP, CORS solo 4 orígenes localhost, `docs/redoc/openapi` off con `ENVIRONMENT=production`, `lifespan` carga con hash verificado |
| **K** UI | PASA | dashboard `:8501` → **200**; 0,901643 rotulado como cobertura medida; suite de UI verde |
| **L** n8n | **NO VERIFICABLE** | JSON válido, 14 nodos, webhook `POST ds02/decision`, 3 ramas con acción distinta (log / Sheets / Postgres+Calendar+Gmail). `active: true` en fichero **sin commitear** (L-01). Sin instancia: no hay ejecución probada |
| **M** Tests | PASA CON RESERVAS | **345 passed, 0 skips, exit 0** (294,10 s); 2 tests con guarda de caché ignorada (M-01); 1 fallo aislado no reproducido (M-02) |
| **N** Documentación | PASA CON RESERVAS | `ADR-001…012` con decisión/alternativas/consecuencia; README enlaza y abre (G2); ADR-012 sin commitear; contradicciones G-01/I-01 |
| **O** Negocio/coste | **NO VERIFICABLE** | no se auditó `costes_reales_aeronauticos.md` contra fuente externa en esta pasada |
| **P** Ética/límites | PASA CON RESERVAS | ADR-009 rectifica una afirmación falsa; e00 prohíbe citar 4.368 hasta reconciliar; limitaciones del artefacto escritas |
| **Q** Operación/deuda | PASA CON RESERVAS | 0 TODO/FIXME; rollback documentado (ADR-011); **punto único de fallo**: el instrumento sin versionar (A-01) |

**Global:** la peor puerta es **G3 parcial** (I-01) → **PASA CON RESERVAS**. G1, G2 y G0
pasan; G4 se respeta bajando notas donde la evidencia es cotejada y no ejecutada; G6 pasa
con 0 ficheros sin tier.

## 6. Hallazgos

| ID | Bloque | Sev. | Hallazgo | Reproducción | Evidencia | Impacto | Propuesta (no aplicada) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **A-01** | A/H/Q | **A** | El instrumento que el gate usa por defecto no está versionado | `git ls-files --error-unmatch src/mia/instrumento_oof.npz` → 1; `git check-ignore …` → 1 | fichero existe (115 225 B, 14 915 filas) pero `??`; ADR-012 afirma “a clone can verify” | un clon recibe exit 3 en el camino por defecto | `git add src/mia/instrumento_oof.npz` y commitearlo con ADR-012 |
| **C-01** | C/D/H | **A** | `models/v3_bundle.joblib` se archivó pero tres scripts y el manifiesto lo siguen esperando | `python -c "import os;print(os.path.exists('models/v3_bundle.joblib'))"` → False | `scripts/predict.py:24`, `scripts/v3_finalize.py:80`, `scripts/make_clase_checksums.py:37`, `manifest.artifacts.v3_bundle_sha256` | `scripts/predict.py --fd FD001` falla al predecir (`--help` sale 0 porque la carga es perezosa: no es prueba de salud) | redirigir `BUNDLE` al archivo o declarar el CLI fuera de servicio |
| **M-01** | M/G1 | **A** | “0 skips” depende de un fichero git-ignored | `grep -n needs_oof tests/test_mia_rules.py tests/test_audit_fixes.py` | guardas en `test_mia_rules.py:31` y `test_audit_fixes.py:44` sobre `_p1_oof_cache.npz` (196 KB, ignorado) | en un clon limpio 2 tests se saltan en silencio; la línea de §9 corregida hoy (“cero skips”) solo es cierta aquí | nombrar el skip como esperado y declararlo en G1, o re-apuntar esos 2 tests al instrumento |
| **G-01** | G/N | **M** | `4.368 ± 0.053` se publica como autoritativo mientras el vault prohíbe citarlo | `grep -n "4.368" docs/framework_auditoria.md MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md` | framework §9: “multisemilla 4.368 ± 0.053 · NASA 2355.2 ± 24.6”; e00: “hay que reconciliarlo … antes de citar 4.368 como cerrada”; README usa 4.330 | tres medias coexistentes (4.330 / 4.322 / 4.368) y la publicada es la prohibida | citar NB05 4.330 y NB06 4.322 con la discrepancia declarada, o regenerar el CSV |
| **I-01** | G/I | **M** | `openspec/project.md` publica cobertura 0,9012 que ningún artefacto registra | `grep -n "0.9012" openspec/project.md` | `calibracion_banda.json` no tiene campo de cobertura; medido sobre el instrumento: **0,901643** | cifra no rastreable (G3) | publicar 0,9016 con su comando, o registrar `coverage` en el JSON |
| ~~C-02~~ | C | **retirado** | Docker queda fuera de alcance por decisión del proyecto (2026-11-07): la imagen root y la base por tag dejan de ser hallazgos | — | — | no se mantiene contenedor alguno | retirar `Dockerfile` y `docker-compose.yml` del repo, o rotularlos como no mantenidos |
| **L-01** | L | **M** | El flujo n8n se declara activo en un fichero sin commitear | `python -c "import json;print(json.load(open('n8n/flujo.json'))['active'])"` → True | `git status` → `M n8n/flujo.json` | el estado “activo” no es reproducible desde el repo; nadie sabe qué versión corre | commitear el flujo y fijar `active` según el entorno |
| **M-02** | M | **B** | Un fallo aislado no reproducido | 1 de 6 pasadas completas | “1 failed, 344 passed” (232 s) frente a 345/159 s, 174 s, 294 s; subconjunto AppTest 86/120/116 s | ruido de espera temporal en AppTest, no lógica | añadir marca de tiempo máxima a la espera o repetir el test en CI |
| **B-01** | B | **B** | `requires-python = ">=3.12"` frente a `.python-version` 3.12.10 | `grep -n requires-python pyproject.toml` | pin laxo; el manifiesto declara `python: 3.12.10` | un 3.13 instalado “cumple” el requisito y no es el entorno del artefacto | `>=3.12,<3.13` |
| **H-01** | H | **B** | Las mismas métricas viven en dos formatos y dos precisiones | comparar los dos JSON | manifiesto `metrics.reference_row.RMSE 4.338` / `MAE 3.227`; caché `metrics.rmse 4.3382` / `mae 3.2266` | un lector puede leerlo como contradicción | declarar en ambos el redondeo (G.4) |

## 7. Notas por criterio

No aplica: el repo no tiene rúbrica versionada en esta pasada (§5.2 se omite).

## 8. Límites de esta auditoría

1. **92,5 % del universo (677/732) no se inspeccionó**; el `cobertura.csv` lo dice fichero
   a fichero en vez de fingir cobertura total.
2. **API caída** (`/health` → 000): J se puntúa por lectura de código, no por `curl` real.
   El techo de J es “PASA estático”, no “verificado en vivo”.
3. **Sin instancia n8n**: L no tiene prueba de ejecución; solo estructura.
4. **Docker fuera de alcance por decisión del proyecto** (2026-11-07): C no se puntúa y los
   ficheros de contenedor quedan como candidatos a retirada, no como deuda técnica.
5. **E y F cotejados, no re-medidos**: no se releyó el HDF5 ni se reentrenó nada.
6. **O no verificado**: los costes no se cruzaron con fuente externa.
7. La suite se ejecutó con `_p1_oof_cache.npz` **presente**; con el árbol de un clon los
   números de M cambiarían (M-01).

## 9. Anexo — comandos y salidas literales

```bash
git rev-parse HEAD            # 835fc583562e3bfd0d4adc519313c20af8c3dbfd
git status --porcelain | wc -l # 23
python -m compileall -q src app scripts tests   # exit 0
python -m pytest tests -q -rs -p no:cacheprovider
#   345 passed, 110 warnings in 294.10s ; exit 0 ; 0 SKIPPED
python scripts/freeze_rules_evidence.py                 # exit 0
python scripts/freeze_rules_evidence.py --cache _p1_oof_cache.npz  # exit 5
sha256sum models/ensemble.joblib models/bilstm_ds02.keras
#   d6c7014… *models/ensemble.joblib
#   bf9620a… *models/bilstm_ds02.keras
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8501   # 200
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/health  # 000
python -c "import os;print(os.path.exists('models/v3_bundle.joblib'))"  # False
git ls-files --error-unmatch src/mia/instrumento_oof.npz        # exit 1 (no trackeado)
```

Cobertura del universo: `docs/informes/auditoria-2026-11-07-cobertura.csv`
(732 filas; A 136 / B 423 / C 173; 0 sin tier).

## 10. Firma de no modificación (G5)

Estado en F0: 23 rutas. Estado en F6: **25** — las 23 originales **sin cambios** más los
dos artefactos de esta auditoría:

- `docs/informes/auditoria-2026-11-07-ds02.md` (este informe)
- `docs/informes/auditoria-2026-11-07-cobertura.csv` (anexo)

Ningún fichero del repo se arregló, renombró ni revirtió durante la pasada. Los diez
hallazgos quedan **documentados, no aplicados**: `A-01` y `C-01` son los dos que deben
cerrarse antes de defender el repositorio como reproducible desde un clon.

## Addendum (2026-11-07, posterior a la firma)

- **C-02 retirado y ejecutado:** tras la auditoría se eliminaron `Dockerfile` y
  `docker-compose.yml` (`git rm`) y se limpiaron sus referencias en `app/api.py`,
  `app/streamlit_app.py`, `README.md`, `README.en.md` y las filas C de
  `docs/framework_auditoria.md`. Verificación posterior: `git ls-files` → 0 y suite
  **345 passed, exit 0**. Queda en el change `2026-11-07-banda-instrumento-y-auditoria`.
- Los nueve hallazgos restantes siguen **abiertos**; este addendum no los toca.
- El árbol ya no es el de F0: la firma de G5 aplica solo hasta este addendum.
