# Plan de auditoría 2026-11-10 (post-cierre) — Rúbrica Reto 1 v5

**Fecha:** 2026-11-10 · **Rama:** `fix/auditoria-2026-11-10` · **HEAD:** `c14d91b`
**Modo:** solo lectura (no arregla, no commitea, no reentrena, no reejecuta notebooks)
**Rúbrica:** `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (20 criterios, escala 0/3/7/10)
**Framework:** `docs/framework_auditoria.md` v1.0 (bloques A–Q, fases F0–F6, puertas G0–G6)
**Antecedentes:** `docs/plans/plan-auditoria-2026-11-10-rubrica-integral.md` + su informe,
`docs/informes/auditoria-2026-11-07-ds02.md`
**Intérprete:** `.venv/Scripts/python.exe` (3.12.10) · **Shell:** bash (git-bash)

---

## 1. Pregunta

Tras cerrar el change `2026-11-10-n8n-accion-propia` y commitear el árbol (11 commits),
¿qué nota da la rúbrica v5 **al estado actual**, y qué hallazgos de la auditoría anterior
siguen abiertos, se han cerrado o han aparecido nuevos?

La auditoría anterior midió el árbol sucio en `025dcb2`. Esta mide `c14d91b` con el árbol
limpio salvo `mlruns/`, así que la comparación entre ambas es parte del resultado.

## 2. Baseline (F0)

| Dato | Valor |
| --- | --- |
| HEAD | `c14d91b5fbb1bd92736e452cf1784990911dee42` |
| Árbol | 94 rutas: 13 `M` + 81 `??`, todas bajo `mlruns/` |
| Versionados | 1761 |
| Sellos | `ensemble d6c70142…`, `bilstm bf9620a7…`, `scaler acccfab3…`, manifiesto `6089457c…`; sello de caché `True` |
| `mlruns` versionado | 1010 ficheros; 109 `meta.yaml` en disco |

## 3. Alcance

**Dentro:** los 20 criterios; coherencia de cifras (manifiesto ↔ e00 ↔ README/README.en ↔
AGENT ↔ framework ↔ notebooksMD); artefactos y sellos; suite y gates; flujo n8n (estructura,
ramas, acción novedosa, credenciales); store MLflow y export.

**Fuera:** reentrenar, recalibrar, releer test, desplegar, `git push`, credenciales reales,
Docker (n/a por decisión 2026-11-07).

**Dependencias externas:** instancia n8n en `127.0.0.1:5678` (responde 200); no se inspecciona
su base de datos ni se lanzan ejecuciones nuevas → todo lo que exija flujo ejecutado se declara
límite.

## 4. Fases

| Fase | Qué se comprueba | Puerta |
| --- | --- | --- |
| F0 | commit, árbol, hashes, sello de caché | G0 |
| F1 | `compileall`, gates (`freeze_rules`, `freeze_oof --check`, `backfill_mlflow --check`), suite completa con `-rs` | G1 |
| F2 | SAA 1-10: README, NB01, `train_clasicos`, `train_mlp`, SHAP, `tabla_final` | G2/G3 |
| F3 | PIA 1-6: README, docstrings, pipeline, MLflow, app | G3/G4 |
| F4 | MIA 1-4: negocio, reglas, flujo n8n, guion | G4 |
| F5 | revalidar los hallazgos de la auditoría anterior uno a uno (abierto/cerrado) | G3 |
| F6 | matriz de 20 celdas, nota ponderada, techo, hallazgos y firma G5 | G5 |

## 5. Hipótesis de esta pasada

| ID | Hipótesis | Falsación |
| --- | --- | --- |
| H1 | G-01 (4.368 como «regenerable») está **cerrado**: todas las fuentes lo rotulan obsoleto | `grep -rn 4.368` en README/README.en/AGENT/e00/framework/notebooksMD |
| H2 | N-02 (resultados sin versionar) está **cerrado** | `git ls-files resultados \| wc -l` > 0 |
| H3 | L-01 (flujo sin commitear) está **cerrado** | `git status --porcelain n8n/flujo.json` vacío |
| H4 | P-01 (store MLflow sin versionar) sigue **abierto** | 94 rutas sucias, todas `mlruns/` |
| H5 | M-01 (`needs_oof` → `_p1_oof_cache.npz`) sigue **abierto** | `ls _p1_oof_cache.npz` falla; suite con 1 skip |
| H6 | MIA-3 sube a 10: el flujo tiene una acción **no vista en clase** (API propia) en HANGAR | `HANGAR Gmail -> HANGAR API propia` en `n8n/flujo.json` + test que lo fija |
| H7 | PIA-4 sigue en 7: ninguna run registra la ablación `cyc_norm` | `grep -ril cyc_norm mlruns --include=meta.yaml` sin hits |
| H8 | H-02 sigue abierto: `instrumento_oof.npz` sin hash en el manifiesto | `grep -c instrumento_oof models/ds02_manifest.json` = 0 |
| H9 | Deuda documental nueva: `app/registros_flota.json.hermes-respaldo` está versionado | `git ls-files \| grep hermes-respaldo` |

## 6. Entregables

1. Este plan.
2. `docs/informes/auditoria-2026-11-10-rubrica-post-cierre.md`: veredicto, matriz de 20 celdas,
   hallazgos con severidad y propuesta, comparación con la auditoría anterior, límites y firma G5.
3. Sin CSV de cobertura fila a fila: la cobertura se declara **por muestreo** (límite explícito),
   para no fabricar 1761 veredictos que nadie ha leído.

## 7. Regla de honestidad

Cada nota lleva `path:línea` o comando con salida. Lo no verificable desde el repo se declara
límite. La nota se baja, no se negocia.
