# Plan — vault-defensa (orden NB01→NB07 + rúbrica v5)

> Estado: **propuesta**, pendiente de autorización. No se ha creado ningún vault.
> Rúbrica leída del PDF `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (9 págs., 12 451
> caracteres, extraída con `pdfplumber` a `.hermes/scratch/rubrica_v5.txt`).
> Vault técnico existente: `MLProyectVault` (71 notas) — **no se toca ni se duplica**.

## 1. Lo que dice la rúbrica (resumen operativo)

19 indicadores con descriptores 0/3/7/10, más **3 preguntas individuales** (una por
asignatura). La defensa son **15 minutos y se corta en seco**; después, preguntas
individuales.

| Bloque | Indicadores | Pesos internos |
|---|---|---|
| SAA | 10 (1–9 + pregunta individual) | RA1 5 % · RA2 10 % · RA3 45 % · RA5 20 % · RA6 20 % |
| PIA | 6 (1–5 + pregunta individual) | RA1 10 % · RA2 90 % |
| MIA | 4 (1–3 + pregunta individual) | RA1 20 % · RA5 80 % |

Consecuencia de diseño: **SAA manda en el tiempo** (75 % de su nota está en RA3+RA5+RA6,
que son modelos) y por eso el recorrido NB01→NB07 es la espina correcta. Pero PIA y MIA
se juegan en 3 indicadores concretos (pipeline, Streamlit, MLflow / reglas, n8n) y en las
preguntas individuales, que valen 35 % sumando las tres.

## 2. Regla que gobierna el vault

- **Espina = orden de notebooks.** Se explica en el orden en que se construyó el sistema:
  NB01 datos → NB02 modelos → NB03 ablación → NB04 BiLSTM → NB05 meta/conformal →
  NB06 producción → NB07 SHAP. Es además el orden en que la rúbrica SAA los pide.
- **Cada nota declara a qué indicador sirve y con qué descriptor** (0/3/7/10). Si una nota
  no cubre ningún indicador, no entra.
- **Una nota = un minuto de voz.** Las que se dicen llevan `spine: true`; el resto es
  soporte y no se abre en vivo.
- **Autocontenido**: Obsidian no resuelve wikilinks entre vaults distintos, así que no se
  enlaza a `MLProyectVault`; al mecanismo profundo se llega por `path:línea` del repo.

## 3. Estructura

```
vault-defensa/
├── LEARNING_LOG.md                          índice + estado + plan aprobado
├── 00-ARRANQUE/
│   ├── 00-guion-15-min.md                   ★ tabla minuto|bloque|nota|qué digo|indicador
│   ├── 01-guion-3-min.md                    versión si recortan
│   ├── 02-apertura-30s.md                   negocio con dato + IA débil (SAA-1/2, MIA-1)
│   └── 03-checklist-dia-D.md                puertos, pestañas, plan B
├── 01-NB01-EDA/                             SAA-3 · SAA-4 · SAA-5
│   ├── 10-nb01-dataset-y-tabla-de-campos.md
│   ├── 11-nb01-cinco-graficos-comentados.md
│   └── 12-nb01-nulos-mar-y-variable-nueva.md
├── 02-NB02-CINCO-MODELOS/                   SAA-6 · SAA-7 · SAA-8 · SAA-9
│   ├── 20-nb02-cinco-modelos-y-tiempos.md
│   ├── 21-nb02-mlp-base-y-tres-experimentos.md
│   ├── 22-nb02-metricas-y-error-de-negocio.md
│   └── 23-nb02-eleccion-y-desempate.md
├── 03-NB03-ABLACION/                        SAA-6 → 10 ("algo no visto en clase")
│   └── 30-nb03-ablacion-cyc-norm.md
├── 04-NB04-BILSTM/                          puente al track DS02
│   ├── 40-nb04-ventana-y-fuga.md
│   ├── 41-nb04-bilstm-y-pooling.md
│   └── 42-nb04-oof-y-beta.md
├── 05-NB05-META-CONFORMAL/                  ADR-001 · ADR-005 · ADR-006 · ADR-008
│   ├── 50-nb05-stacking-y-holdout-16.md
│   ├── 51-nb05-multisemilla.md
│   └── 52-nb05-banda-conformal.md
├── 06-NB06-PRODUCCION/                      cascada, dos ligas, macro
│   ├── 60-nb06-cascada-bundle-c.md
│   ├── 61-nb06-dos-ligas-y-tabla-final.md
│   └── 62-nb06-macro-y-motor-14.md
├── 07-NB07-SHAP/                            SAA-9 → 10
│   └── 70-nb07-shap-aditividad.md
├── 08-PIA-CODIGO/                           PIA-1 … PIA-5
│   ├── 80-pia-readme-y-funciones.md
│   ├── 81-pia-estructura-de-carpetas.md
│   ├── 82-pia-pipeline-sklearn.md
│   ├── 83-pia-mlflow.md
│   └── 84-pia-streamlit-test-y-caso-nuevo.md
├── 09-MIA-DECISION/                         MIA-1 · MIA-2 · MIA-3
│   ├── 90-mia-negocio-con-dato-y-objetivo.md
│   ├── 91-mia-seis-reglas.md
│   ├── 92-mia-n8n-rama-propia.md
│   └── 93-mia-demo-de-la-accion.md
├── 10-DECISIONES/                           el "por qué" transversal (3 notas, no 12)
│   ├── 94-como-contar-una-decision.md
│   ├── 95-catalogo-de-12-decisiones.md
│   └── 96-lo-que-descartamos.md
├── 11-TRIBUNAL/
│   ├── 100-tres-preguntas-individuales.md   ★ SAA-10 · PIA-6 · MIA-4
│   ├── 101-banco-de-preguntas.md
│   ├── 102-objeciones-duras.md
│   ├── 103-cifras-y-lista-negra.md
│   └── 104-frases-prohibidas.md
├── 12-RUBRICA/
│   ├── 110-mapa-indicador-evidencia.md      ★ 19 filas
│   ├── 111-huecos-declarados.md
│   └── 112-como-subir-de-7-a-10.md
├── 00-Definiciones-del-Autor/               tus frases (teachme)
└── visuals/                                 *.mmd, mismo bloque embebido en su nota
```

42 notas + `LEARNING_LOG.md`. Esquemas (`-esquema.md`) solo en las 12 del spine.
Detalle: **no** hay `index.md`/`Home.md`/`README.md`; el índice es el log.

## 4. Reparto de los 15 minutos

| Min | Bloque | Qué demuestra | Indicadores |
|---|---|---|---|
| 0:00–1:15 | Apertura | problema con dato, quién usa, IA débil | SAA-1, SAA-2, MIA-1 |
| 1:15–3:00 | NB01 | datos, calidad, 5 gráficos, nulos y variable nueva | SAA-3/4/5 |
| 3:00–5:00 | NB02 | 5 modelos con tiempo, MLP 3 exp., métricas, elección | SAA-6/7/8/9 |
| 5:00–5:45 | NB03 | ablación: lo que no se vio en clase | SAA-6 (10) |
| 5:45–7:15 | NB04–NB05 | ventana, fuga, OOF, stacking, banda | SAA-9, PIA-3 |
| 7:15–8:30 | NB06 | cascada 7,07→4,34, dos ligas, macro | SAA-9 |
| 8:30–9:15 | NB07 | SHAP con validación | SAA-9 (10) |
| 9:15–10:45 | PIA | estructura, pipeline guardado, MLflow, Streamlit | PIA-2/3/4/5 |
| 10:45–13:30 | MIA | 6 reglas, n8n con acción propia, demo | MIA-2/3 |
| 13:30–15:00 | Cierre | límites y qué falta | — |

Si recortan: `01-guion-3-min.md` = apertura → cascada → reglas → límite.

## 5. Cobertura verificada de los 19 indicadores

| # | Indicador | Nota | Evidencia que ya existe hoy | Nota |
|---|---|---|---|---|
| SAA-1 | IA débil | 02 | `README.md:29` compara con AGI | 10 |
| SAA-2 | Tipo de aprendizaje | 02 | supervisado/regresión + diferencia con no supervisado | 10 |
| SAA-3 | Dataset y campos | 10 | `notebooks/01` tabla de sensores + MAR T30 | 10 |
| SAA-4 | 5 gráficos comentados | 11 | 6 PNG `resultados/eda_*.png` + "QUÉ VEO"/"CONCLUSIÓN" en NB01 | 10 |
| SAA-5 | Nulos + variable nueva | 12 | MAR elegible (alt>27k, Mach>0,68, seed 7) + fase_vuelo/cyc_norm | 10 |
| SAA-6 | Cinco modelos | 20 | `resultados/comparativa.csv` (5 filas, train+val+`tiempo_s`) | 10 |
| SAA-7 | MLP base + 3 exp. | 21 | `mlp_comparativa.csv` con columna `hipotesis` (el porqué) | 10 |
| SAA-8 | Métricas | 22 | MAE/RMSE/R² train+val + real-vs-predicho | 10 |
| SAA-9 | Mejor modelo + SHAP | 23 + 70 | tabla con tiempos, elección por `rmse_val`, SHAP en validación | 10 |
| SAA-10 | Pregunta individual | 100 | guion propio por asignatura | — |
| PIA-1 | README + docstrings | 80 | 6 apartados obligatorios; 0 funciones públicas sin docstring | 10 |
| PIA-2 | Estructura | 81 | `src/`, `app/`, `models/`, `n8n/`, `resultados/`, `data/` | 10 |
| PIA-3 | Pipeline sklearn | 82 | `src/clase/pipeline_clase.py:27`; joblib incluye pipeline | 10 |
| PIA-4 | MLflow | 83 | 17 runs (9 fila + 4 ventana + 4 ablación) + `comparativa.csv` + capturas | 10 |
| PIA-5 | Streamlit | 84 | test + caso nuevo + `L_inf` junto a la decisión | 10 |
| PIA-6 | Pregunta individual | 100 | — | — |
| MIA-1 | Negocio con dato | 90 | macro 5,0153 · motor 14 8,576 · lead time 9/23/17 | 10 |
| MIA-2 | 6 reglas | 91 | `src/mia/reglas.py` (6 tuplas, prioridad, porqué, R1_SEGURIDAD) | 10 |
| MIA-3 | n8n con acción propia | 92 | `n8n/flujo.json` → `POST /n8n-decision` (`app/api.py:262`) | 10 |
| MIA-4 | Pregunta individual | 100 | — | — |

## 6. Huecos que el vault debe declarar (no maquillar)

1. **PIA-4 = 10 (cerrado 2026-11-10).** La ablación `cyc_norm` son 4 runs registradas y el
   store de 17 runs viaja en git. El hueco que este plan declaraba ya está cerrado.
   → `111-huecos-declarados.md` + `112-como-subir-de-7-a-10.md`.
2. **PIA-2 y la estructura prescrita.** La rúbrica dibuja `src/utils.py`, `src/reglas.py`,
   `src/n8n.py`, `app/streamlit_app.py`, `models/mejor_modelo.joblib`. Nuestro repo usa
   `src/mia/`, `src/clase/`, `src/ds02_rul/`, `app/dashboard_ds02.py`. La nota 81 lleva la
   tabla de equivalencias para responder sin titubear.
3. **SAA-8 y el test.** En `comparativa.csv` solo XGB tiene columnas de test: es correcto
   (test una sola vez, con el elegido), pero hay que decirlo antes de que lo pregunten.
4. **El test del track de clase y el bundle.** E2 (7,72 test) y C (4,338) son dos
   campeonatos distintos; el guion debe fijar cuál se cita en cada momento.

## 7. Orden de construcción

1. **Fase A** — `LEARNING_LOG`, `00-ARRANQUE` (guion 15/3, apertura, checklist), `12-RUBRICA`.
   Con esto ya hay guion seguible y mapa de cobertura.
2. **Fase B** — `01` a `07` (las 18 notas del recorrido NB01→NB07) + visuals del arco.
3. **Fase C** — `08-PIA`, `09-MIA`, `10-DECISIONES`, `11-TRIBUNAL` + esquemas del spine.

## 8. Criterio de aceptación del vault

- El guion se puede seguir sin abrir otra nota que la que enlaza.
- Los 19 indicadores tienen fila en `110` con `path:línea` o cifra verificable.
- Un ensayo de 15 min se completa sin leer (solo títulos y "Di esto").
- 0 enlaces rotos; todo mermaid con fuente gemela en `visuals/`.
