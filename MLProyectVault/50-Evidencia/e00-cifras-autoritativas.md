---
tipo: evidencia
status: consolidado
tags:
  - cifras
  - manifiesto
  - fuente-unica
---

# Cifras autoritativas

> [!abstract] En una frase
> Todo número que se diga en la defensa sale de acá, y todo lo que hay acá sale de `models/ds02_manifest.json`.

> [!warning] Regla del vault
> Esta es la **única** nota con decimales. Si otra nota cita un resultado del bundle, lo redondea (`≈4.25`) o enlaza a esta página. Si hay discrepancia entre el vault, la prosa de un cuaderno y el manifiesto, **gana el manifiesto**.

## Dónde está cada cifra (índice)

| Si buscas | Ve a |
|---|---|
| RMSE, MAE, R² y NASA por modelo | Bundle B |
| Macro-RMSE y el motor 14 | Macro-RMSE |
| Cobertura y ancho de banda | Banda conformal |
| Ventanas, filas, splits y formas | Formas, conteos y protocolo |
| Hashes y bytes del artefacto | Huellas de los artefactos |
| Reglas, umbrales y lead time | Capa de reglas |
| Qué cifras no decir nunca | Lista negra |
| Cómo re-verificar en 30 s | Cómo verificar |

## Bundle C — el desplegado (autoritativo desde 2026-11)

El bundle en disco es **C** (`code_version: clase-bundle-C` en el manifiesto): híbrido BiLSTM + LightGBM + stacking + EMA5 sobre la **base adaptada** (MAR T30 + ffill causal con medianas de fit-units). Test: unidades 11 / 14 / 15, 6 196 ventanas. Semillas `[42, 7, 123]`.

| Modelo | RMSE | MAE | R² | NASA score |
|---|---|---|---|---|
| LGBM adaptada (solo) | 7.067 | — | — | — |
| BiLSTM-C (solo) | 5.654 | — | — | — |
| BiLSTM-C + EMA5 | 5.618 | — | — | — |
| **Híbrido-C + EMA5, fila oficial (semilla 42, en disco)** | **4.338** | **3.227** | **0.9461** | **2336.2** |
| **Híbrido-C + EMA5, media multiseed NB06 (grano ventana test)** | **4.322 ± 0.064** | — | — | **2342.3 ± 43.4** |
| Híbrido-C, media NB05 (protocolo OOF) | 4.330 ± 0.053 | — | — | — |
| MLP E2 de clase (grano fila, 22 feats) | 7.72 test (val 7.34) | 5.81 | 0.83 | — |

**Por qué hay tres filas del híbrido-C.** La de `4.338` es la corrida de la semilla 42, cuyo artefacto está en disco (`models/ds02_manifest.json → metrics.reference_row`): es la que reproduce el servicio. Las de `4.322 ± 0.064` (NB06, ventanas de test) y `4.330 ± 0.053` (NB05, protocolo OOF) son medias de tres semillas: miden la estabilidad, no el artefacto. Si difieren en centésimas, es ruido TensorFlow en CPU ([[c14-ruido-y-reproducibilidad]]), no contradicción.

**Macro-RMSE del bundle C:** 5.0153 (motor 11: 3.6328 · 14: 8.5761 · 15: 2.8371). El motor 14 sigue siendo el que más sufre con menos ventanas.

**La cascada se lee en orden:** 7.067 (LGBM) → 5.654 (BiLSTM) → 5.618 (+EMA5) → 4.338 (híbrido). Ninguna etapa sobra.

## Bundle B — lo que sirvió antes (histórico, ya no desplegado)

Test: unidades 11 / 14 / 15, 6 196 ventanas. Media ± desviación sobre semillas `[42, 7, 123]`.

| Modelo | RMSE | MAE | R² | NASA score |
|---|---|---|---|---|
| LightGBM cuantil 0,35 (solo) | 7.098 ± 0.034 | 5.572 ± 0.034 | 0.8557 ± 0.0014 | 5772.5 ± 50.1 |
| BiLSTM triple pooling (solo) | 6.218 ± 0.541 | 4.820 ± 0.477 | 0.8887 ± 0.0191 | 4397.8 ± 550.9 |
| **Híbrido + EMA5** | **4.340 ± 0.101** | **3.235 ± 0.054** | **0.9460 ± 0.0025** | **2347.7 ± 49.4** |
| Híbrido, fila de referencia en disco | 4.251 | 3.183 | 0.9482 | 2305.1 |

**Por qué hay dos filas del híbrido.** La de `4.340 ± 0.101` es la media de tres semillas. La de `4.251` es la corrida concreta cuyo artefacto está en disco: es la que reproduce `scripts/predict_ds02.py`. No son contradictorias; miden lo mismo en dos poblaciones distintas (tres corridas vs. una).

**El NASA score es una suma, no una media.** Crece con la cantidad de ventanas evaluadas, así que solo es comparable entre modelos medidos sobre estas mismas 6 196 filas. No lo compares con un paper.

## Macro-RMSE — lo que el promedio ponderado esconde

| Motor | RMSE | Ventanas |
|---|---|---|
| 11 | 3.7874 | 3 293 |
| 14 | 7.9974 | 760 |
| 15 | 2.7451 | 2 143 |
| **Macro (cada motor pesa 1/3)** | **4.8433** | — |
| Ponderado por ventana | 4.2515 | 6 196 |

La diferencia de `+0.6` es el costo de que el motor 14 tenga el peor error **y** la menor cantidad de ventanas: 760 filas concentran el 43,7 % del error cuadrático. El promedio de flota es más amable que lo que sufre un motor elegido al azar.

## Banda conformal

| Propiedad | Valor |
|---|---|
| Objetivo | 90 % |
| Cobertura realizada (test) | **100 %** |
| Ancho medio | **26.41** ciclos |
| Por motor | 11 → 26.92 · 14 → 26.03 · 15 → 25.75 |
| Filas de calibración | 17 450 (fuera de fold, 6 motores de desarrollo) |
| Falsos fuera de banda | 0 por abajo, 0 por arriba |

Es **cota conservadora, no intervalo de decisión**: se calibró con modelos de fold más débiles que el desplegado. Recalibrarla en la unidad 16 colapsa a **3.35 ciclos de ancho con 31.4 % de cobertura** (41.4 % por debajo, 27.2 % por arriba), porque el meta-aprendiz se ajusta en esa unidad y ninguna fila suya supera los 62 ciclos. Se midió y se rechazó.

> [!warning] No confundir 14 915 con 17 450
> `17 450` = calibración de la banda conformal que se envía. `14 915` = filas OOF puras (unidades 2, 5, 10, 18, 20; unidad 16 excluida) sobre las que se calibró la banda de la **capa de reglas** (`src/mia/calibracion_banda.json`). Son dos bandas distintas para dos usos distintos.

## Formas, conteos y protocolo

| Dato | Valor |
|---|---|
| Ventanas dev / test | 17 450 / 6 196 |
| Filas dev / test | 52 635 / 12 538 |
| Filas de ajuste / holdout | 44 982 / 7 653 |
| Ventanas de ajuste / holdout | 14 915 / 2 535 |
| Unidades de ajuste | `[2, 5, 10, 18, 20]` |
| Unidad de holdout | `[16]` |
| Unidades de test | `[11, 14, 15]` |
| Scaler | 18 canales |
| Features tabulares | 93 |
| Entrada BiLSTM | `(None, 50, 19)` · 154 253 parámetros |
| Ventana / stride | 50 filas / 100 |
| Step train / test | 3 / 2 |
| `beta` | 1.0 · folds `[1.00, 1.00, 0.00]` · mediana 1.0 · IQR 0.5 |
| `ema_span` | 5 |
| `alpha` LightGBM | 0.35 |

## Huellas de los artefactos

| Archivo | SHA-256 | Bytes |
|---|---|---|
| `models/ensemble.joblib` | `d6c70142…` | 469 620 |
| `models/bilstm_ds02.keras` | `bf9620a7…` | 1 935 767 |

(Los hashes `7acba335…` / `d0c5ed7f…` eran del bundle B: ver lista negra.)

## Capa de reglas (`src/mia/`)

| Dato | Valor |
|---|---|
| Cobertura OOF (banda de reglas) | 0.9012 |
| Cobertura test | 1.0000 |
| Filas de calibración | 14 915 |
| R2b (isotónica causal) OOF | 9.623 RMSE / 18 713.9 NASA |
| R2 (monótona estricta) OOF | 10.737 / 21 053.0 |
| Subida máxima permitida por R2b | +1.328848 ciclos |
| Umbrales de decisión | `L_inf ≥ 30` APTO · `25 ≤ L_inf < 30` INSPECCIÓN · `< 25` HANGAR |
| Lead time por motor | 9 / 23 / 17 (corte por media) · 13 / 23 / 18 (peor ventana) |
| Saturación de la predicción | ≈60.6 ciclos |
| L_inf máximo alcanzable | ≈36 ciclos |

## Lista negra — cifras que NO se dicen

Estas aparecen en material viejo del repo y del vault anterior. Son de corridas anteriores o de protocolos distintos:

| Cifra | Qué era | Por qué no se usa |
|---|---|---|
| `4.352`, `4.344`, `4.301` | corridas históricas del híbrido | no determinismo de TensorFlow y revisiones previas |
| `4.289` | fila de test de una revisión anterior | reemplazada por `4.251` (y luego por `4.338` del bundle C) |
| `4.340 ± 0.101`, `4.251`, `5772.5`, `4397.8` | bundle B completo | reemplazados por el bundle C (fila `4.338`, media `4.322 ± 0.064`) |
| `4.301 ± 0.068` | media de una revisión intermedia | reemplazada por `4.322 ± 0.064` (NB06) |
| `4.9026` | macro-RMSE anterior | reemplazada por `4.8433` |
| `051e0af4`, `0acd795b` | hashes de artefactos viejos | no son los que están en disco |
| `6.233`, `6.347`, `4.278` | BiLSTM/híbrido de otras corridas | ruido de ejecución, no resultado del bundle |

Si alguien del tribunal cita una de estas, la respuesta correcta es: *"esa cifra es del bundle B o de una corrida anterior; el artefacto en disco (bundle C) da 4.338"*.

## Cómo verificar (30 segundos)

```bash
python -c "import json; d=json.load(open('models/ds02_manifest.json')); print(d['metrics']['reference_row']); print(d['macro_rmse'])"
```

```bash
python -c "import json; d=json.load(open('models/ds02_manifest.json')); print(d['artifacts'])"
```

Comparar con lo que imprime `notebooks/ds02_ensemble/EVALUACION_EJECUCION.md`. Si el manifiesto y esta página difieren, actualizá **solo esta página**.

## Qué hacer si re-ejecutás un cuaderno

1. Las cifras se mueven ±0.1 en RMSE por no-determinismo de TensorFlow en CPU ([[c14-ruido-y-reproducibilidad]]).
2. No edites las demás notas: están escritas para sobrevivir al ruido.
3. Actualizá esta tabla, el manifiesto y nada más.

## Conexiones

- Mecanismo del ruido: [[c14-ruido-y-reproducibilidad]]
- Cómo se mide: [[s10-stacking-hibrido]] · [[s11-banda-conformal]]
- Cómo se cuenta: [[d05-como-decir-las-cifras]]
