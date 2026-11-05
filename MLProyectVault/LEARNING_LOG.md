---
source: learn-teacher
mode: repo
repo: nasa
created: 2026-10-23
updated: 2026-11-01
version: 2
---

# LEARNING_LOG — MLProyectVault

Vault de estudio del proyecto **DS02 — RUL con ensamble híbrido** (N-CMAPSS).
Objetivo: entender los tres cuadernos, entender el proyecto y sus conceptos, y defenderlo en voz alta.

## Estado actual

**Modo:** repo · **Tema activo:** proyecto completo · **Idioma:** español.

| | |
|---|---|
| Notas activas | 64 (23 conceptos · 23 sistema · 8 notebooks · 7 defensa · 3 evidencia) — plan C + auditoría 2026-11-04 |
| Consolidadas | 0 |
| Sin estudiar | 44 |
| Última reestructuración | 2026-11-01 (v2) |

### Cómo se usa este vault

1. **Entender un concepto** → `10-Conceptos/`. Cada nota termina en flashcards plegables: contestalas sin abrir.
2. **Entender cómo se implementó** → `20-Sistema/`. Cada nota cita `archivo:línea` del repo.
3. **Entender qué hace un cuaderno** → `30-Notebooks/`. Celda por celda, con la salida real.
4. **Ensayar la defensa** → `40-Defensa/`. Se lee **en voz alta**, no se estudia en silencio.
5. **Verificar un dato** → `50-Evidencia/`. Una sola página tiene decimales.

### Ruta de estudio sugerida

| Tramo | Qué leer | Criterio para avanzar |
|---|---|---|
| 1 | `c01` → `c07` | podés explicar ventana, cuantil, BiLSTM y pooling sin mirar |
| 2 | `c08` → `c14` + `s01` → `s07` | podés contar el pipeline de punta a punta |
| 3 | `s08` → `s14` + `n01` → `n05` | podés abrir cualquier cuaderno y decir qué hace cada celda |
| 4 | `d01` → `d07` | decís el guion de 30 s sin leer y respondés 30 de las 40 preguntas |

**Bucle por nota:** leer → contestar flashcards con el callout cerrado → decir la frase de `Di esto en el tribunal` en voz alta → marcar `status`. Si no sale hablando, no está consolidada.

### Perfil del estudiante

- `preferencia_quiz: cada_nodo` · `formato: adaptativo` · `ritmo: normal` · idioma: español.
- Pedir sesión de estudio: "hazme quiz de `c03`" → dos preguntas, tres opciones cada una, con "No lo sé".

### Nivel del estudiante

- `nivel: sin calibrar` · `evidencia: 0/0`. Se recalcula con los veredictos, no con impresiones.

## Reglas del vault

1. **Una idea, un lugar.** Las notas de concepto explican el mecanismo; las de sistema dicen cómo aterriza; las de notebook dicen qué hace la celda. Si un tema aparece en dos, una enseña y la otra enlaza.
2. **Una cifra, una fuente.** Solo [[e00-cifras-autoritativas]] tiene decimales. El resto redondea o cita.
3. **Toda nota termina hablando.** El bloque `Di esto en el tribunal` es la salida real del estudio.
4. **Nada de plugins.** Las flashcards son callouts plegables nativos (`> [!question]-`): funcionan en cualquier Obsidian.
5. **El repo manda sobre el vault.** Si la nota y el código discrepan, se corrige la nota.

## Índice

### 10-Conceptos — qué es y por qué funciona así

- [[c00-glosario]] — 40 términos en una línea
- [[c01-que-es-rul]] · [[c02-ventanas-y-horizonte]] · [[c03-fuga-de-informacion]]
- [[c04-metricas-y-baseline]] · [[c05-regresion-cuantilica]]
- [[c06-bilstm-y-secuencias]] · [[c07-pooling-temporal]]
- [[c08-residualizacion]] · [[c09-ensembles]] · [[c15-grano-fila-vs-ventana]] · [[c16-groupkfold-por-motor]] · [[c17-nulos-mar-e-imputacion-causal]] · [[c18-fase-vuelo-y-onehot]] · [[c19-ablacion-cyc-norm]] · [[c20-multisemilla-y-ruido]] · [[c21-shap-e-ia-debil]] · [[c22-cuanto-vale-acertar]]
- [[c10-oof-y-validacion-agrupada]] · [[c11-shrinkage-beta]]
- [[c12-conformal-prediction]] · [[c13-ema-causal]] · [[c14-ruido-y-reproducibilidad]]

### 20-Sistema — cómo está hecho aquí

- [[s01-protocolo-honesto]] · [[s02-datos-ds02-y-reparto]] · [[s03-preproceso-sin-fuga]] · [[s04-ventanas-y-features]]
- [[s05-lightgbm-cuantilico]] · [[s06-bilstm-triple-pooling]] · [[s07-ema-por-motor]]
- [[s08-ablacion-cyc-norm]] · [[s09-oof-y-beta]] · [[s10-stacking-hibrido]] · [[s11-banda-conformal]] · [[s15-dataset-de-clase]] · [[s16-pipeline-de-clase]] · [[s17-clasicos-y-mlp]] · [[s18-lgbm-adaptada]] · [[s19-tabla-final-y-grano]] · [[s20-ensemble-adaptado-y-bundle-c]] · [[s21-puente-c-y-multisemilla]] · [[s22-shap-y-app-de-clase]] · [[s23-dss-por-pestanas]]
- [[s12-persistencia-y-contrato]] · [[s13-capa-de-reglas-y-decision]] · [[s14-app-y-despliegue]]

### 30-Notebooks — qué hace cada celda

- [[n01-recorrido-nb01]] · [[n02-recorrido-nb02]] · [[n03-recorrido-nb03]]
- [[n04-cadena-de-estado]] · [[n05-api-src-ds02-rul]] · [[n06-recorrido-nb04]] · [[n07-recorrido-nb05]] · [[n08-recorrido-nb06]]

### 40-Defensa — guion y performance

- [[d01-guion-30s]] · [[d02-guion-5min]]
- [[d03-banco-de-preguntas]] · [[d04-objeciones-duras]]
- [[d05-como-decir-las-cifras]] · [[d06-demo-y-plan-b]] · [[d07-checklist-la-noche-antes]]

### 50-Evidencia — trazabilidad

- [[e00-cifras-autoritativas]] · [[e01-adr-index]] · [[e02-informes-index]]

## Historia

- **2026-11-04 — repaso de rúbrica v5 (autorizado).** Leída la rúbrica oficial (9 págs). Añadidos: SAA2/SMOTE en `c21`, 5 clásicos nombrados + métrica-negocio en `s17`, MIA-1 quién-usa en `c22`, banco 50→56 (Q51 n8n, Q52 MLflow, Q53 SMOTE, Q54 IA débil, Q55 aprendizaje, Q56 pipeline+caso nuevo), checklist 43/53→46/56. Cobertura: SAA 1-10, PIA 1-6, MIA 1-4 con material estudiable; pendientes n8n/MLflow con respuesta declarada.
- **2026-11-04 — auditoría post-plan (autorizada).** Des-decimalizado el bundle B en 12 notas (regla «una cifra, una fuente» restaurada), hashes C en e00/s12/d02/d04/d05/d07, `s23` DSS por pestañas, `c22` negocio AOG + pendientes n8n/MLflow en `s14`, objeción 5 a ±0.1. Queda: 90-Archivo intacto; NB06 en ejecución 2.º plano.
- **2026-11-04 — plan C ejecutado (alcance completo).** 18 notas nuevas (c15–c21, s15–s22, n06–n08) + 10 actualizadas (e00, n01–n05, d01–d03, d05–d07, d04). Bundle C autoritativo en e00 (fila 4.338, media 4.322±0.064). `visuals/n04-cadena-estado.mmd` a 6 eslabones. NB06 celdas 11/23/25 en ejecución 2.º plano (log `nb06_exec.log`). Sin commits.
- **2026-11-01 — v2 (reestructuración).** El vault v1 tenía 120 notas, tres copias del mismo contenido y cifras desactualizadas en la propia nota que decía "el manifiesto manda". Se archivó completo en `90-Archivo/` (incluido el log v1: [[LEARNING_LOG-v1]] desde la raíz del archivo) y se reconstruyó por ejes: conceptos, sistema, notebooks, defensa, evidencia. Ninguna nota se borró.
- **2026-10-26 — v1.** Bloque B0 de guion de defensa (10 notas + 3 anexos celda a celda) y variante "refactor novato".
- **2026-10-23 — v1.** Cartografía del repo y 6 bloques B1–B7 (31 nodos, formato teoría + esquema).
