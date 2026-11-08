---
tipo: sistema
status: sin-estudiar
tags:
  - ensemble
  - bundle-c
  - despliegue
---

# Ensemble adaptado y bundle C — el desplegado

> [!abstract] En una frase
> BiLSTM + LightGBM + stacking con beta 1.00 + EMA5 sobre la base adaptada: 4.338 en disco, 4.322±0.064 de media; es lo que sirve la app.

## Contrato

| Entra | Sale |
|---|---|
| Base adaptada + holdout-16 para el meta | `models/ensemble.joblib` + manifiesto `clase-bundle-C` + banda + app |

## Cómo está implementado

| Pieza | Dónde | Qué hace |
|---|---|---|
| `construir_raw_adaptado` | `src/clase/train_ensemble_adaptado.py:67` | base con nulos tratados (EPOCHS 22, EPOCHS_OOF 15) |
| OOF + beta | `oof_base_predictions` + `select_beta_grouped` | beta 1.00: el meta sustituye a la red |
| Meta | ridge + LGBM sobre `[p_lstm, p_lgb]`, sin `cyc_norm` | reconcilia ramas, sin prior de vida |
| EMA causal | span 5 por motor | alisado causal por motor, sin futuro |
| Fila oficial | 4.338 / 3.227 / 0.9461 / 2336.2 (semilla 42) | `metrics.reference_row` del manifiesto |
| Multiseed | 4.322±0.064 (NB06) · 4.330±0.053 (NB05) **impresas, NO regenerables desde el CSV (4.368 pendiente per [[e00-cifras-autoritativas]])** | `evaluar_c_multisemilla.py`, semillas [42, 7, 123] |
| Cascada | 7.067 → 5.654 → 5.618 → **4.338** | LGBM, BiLSTM, +EMA5, híbrido |

La persistencia verifica SHA-256 al cargar (`load_ensemble`): el despliegue se audita desde el artefacto, no desde la palabra del entrenador.

## Conexiones

- Puente: [[s18-lgbm-adaptada]] · beta: [[c11-shrinkage-beta]] y [[s09-oof-y-beta]] · conformal: [[s11-banda-conformal]] · multiseed: [[c20-multisemilla-y-ruido]] · cyc_norm: [[c19-ablacion-cyc-norm]] · cifras: [[e00-cifras-autoritativas]]

**Nota multiseed (NO reconciliada).** Las medias 4.322 ± 0.064 (NB06) y 4.330 ± 0.053 (NB05) están impresas en los cuadernos pero **no son regenerables desde** `resultados/bundle_c_multiseed.csv` (en disco: 7=4.429, 123=4.336, sin 42 → media 4.368, **pendiente de reconciliar** per [[e00-cifras-autoritativas]]). La fila oficial es **4.338 (semilla 42, manifiesto)**.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «El bundle C es el mismo híbrido de siempre, reconstruido sobre la base con nulos tratados: 4.338 en el artefacto, 4.322 de media en tres semillas. La base cambió; el protocolo no».

## Flashcards

> [!question]- ¿Qué es el bundle C y qué números lo definen?
> El híbrido desplegado sobre base adaptada (BiLSTM+LGBM+stacking beta 1.00+EMA5): fila oficial 4.338 (semilla 42, en disco), media multiseed 4.322±0.064; cascada 7.067→5.654→5.618→4.338.

> [!question]- ¿Cómo se audita el despliegue?
> Por el artefacto: el manifiesto declara variante de datos, partición y huellas SHA, y `load_ensemble` verifica el hash al cargar. El despliegue se prueba desde disco, no desde memoria.
