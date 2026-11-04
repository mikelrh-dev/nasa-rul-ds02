# Informe — ajustar el meta sobre el OOF de los cinco motores: medido y rechazado

> **Banner — bundle A obsoleto, bundle B vigente:** este informe 2026-10-21 describe el bundle A (histórico/pre-B, 4.289 / sha `0acd795b…`) y ya no es vigente como referencia de producción. Vigente: bundle B (ref 4.251; media 4.340 ± 0.101). Las métricas B no se cambian en este diff; las cifras de abajo se conservan como histórico.


**Fecha:** 2026-10-21
**Alcance:** `scripts/build_02_notebook.py`, `src/ds02_rul/stacking.py`
**Resultado:** la hipótesis se implementó, se midió y **se revirtió**. El pipeline
vuelve al meta ajustado sobre el motor 16; se conservan las dos mejoras que sí
pasaron la prueba (macro-RMSE e intervalos conformales).

---

## 1. La hipótesis

El meta-aprendiz se ajustaba con las 2 535 ventanas del motor 16 (RUL 0–62). La
hipótesis era que, al no haber visto nunca una RUL alta, comprimía el rango y
ponía un techo artificial en ~61 ciclos. Medición que la motivaba, sobre el
artefacto anterior:

| En unit 14, y>65 (n=76, real media 69.4) | media | sesgo |
|---|---|---|
| `p_lstm` | 53.69 | −15.70 |
| `p_lgb` | **64.29** | −5.10 |
| `ridge_meta` | 55.38 | −14.01 |
| `lgb_meta` | 55.37 | −14.02 |
| final (blend) | 55.38 | −14.02 |

El meta descartaba ~9 ciclos que el LightGBM ya ofrecía. La corrección propuesta:
ajustarlo sobre el vector OOF de los cinco motores de ajuste (14 915 ventanas,
RUL 0–88) y puntuar `beta` en el motor 16, que así queda libre.

## 2. Lo que se implementó

- `fit_meta_learners(Z, y, seed)` y `meta_predict(...)` en `stacking.py`: mismo
  diseño de 2 columnas, misma pareja RidgeCV + LGBM 50/50.
- `score_beta_holdout(...)`: puntúa la rejilla de `beta` sobre filas que el meta
  no vio, con el mismo criterio (RMSE y NASA normalizados).
- El meta se ajustó sobre `oof['pred_lstm']/['pred_lgb']` restringido a los cinco
  motores de ajuste; el motor 16 se usó solo para puntuar `beta`.

## 3. Lo que salió

El meta agrupado **no combinaba peor**, pero **desplazaba el nivel**:

| Medición | Valor |
|---|---|
| `ridge_meta` | alpha **545.6** (antes 4.28), coef `[0.8303, 0.3501]`, intercept −0.518 |
| Motor 16: RUL real media | **31.5** |
| Motor 16: `p_lstm` / `p_lgb` medias | 33.5 / 36.2 |
| Motor 16: media del meta agrupado | **39.9** (máx 75.4) |

Curva de `beta` sobre el motor 16 (con EMA5):

| `beta` | RMSE | NASA |
|---|---|---|
| 0.00 | **4.041** | **974.0** |
| 0.20 | 5.035 | 1354.5 |
| 0.40 | 6.210 | 1891.9 |
| 0.60 | 7.481 | 2578.4 |
| 0.80 | 8.807 | 3410.1 |
| 1.00 | 10.166 | 4410.6 |

El selector eligió `beta = 0.00` — correctamente. En test el "híbrido" quedó
siendo el BiLSTM con EMA: `5.768` en la semilla 42 y `6.453 ± 0.716` en las tres,
frente a `4.301 ± 0.068` de la línea base. **Regresión de ~1.5 RMSE.**

## 4. Por qué falla: el prior de nivel no transfiere

No es que el meta no sepa combinar. Sobre las mismas 14 915 filas de los motores
de ajuste (predicciones de los modelos finales, en muestra para las bases) el meta
agrupado da **RMSE 5.02** frente a 8.06 del BiLSTM y 6.19 del LightGBM: combina.

Lo que falla es el **nivel**. Los motores de desarrollo viven más que los de test
(RUL máximas 88, 81, 74, 70, 65, 62 frente a 75/66/58 en test), así que el
aprendiz agrupado aprende una media de objetivos alta y la aplica a motores
cortos. Sobre el motor 16 eso son +8.4 ciclos de sesgo sistemático, y ningún
coeficiente lo corrige porque el intercepto se ajusta al conjunto agrupado.

Consecuencia de diseño: **la muestra de ajuste del meta debe tener el mismo
perfil de vida que los motores donde se aplica**. Un solo motor es poco, pero al
menos está centrado; cinco motores largos son más datos y peor calibración.

## 5. Estado final

| Elemento | Decisión |
|---|---|
| Meta sobre OOF de 5 motores | **Rechazado** (este informe) |
| `beta` puntuado en el motor 16 | Revertido con él: vuelve la mediana agrupada fuera de fold |
| `fit_meta_learners`, `score_beta_holdout` | Se conservan como instrumento reproducible del experimento |
| Macro-RMSE por motor | **Se queda** |
| Intervalos conformales | **Se queda**, calibrados sobre residuales fuera de fold |

Queda anotado como línea de trabajo futura, no como pendiente: corregir el nivel
exigiría un ancla disponible en inferencia (por ejemplo, normalizar por la vida
temprana del motor) — y esa ancla es exactamente el tipo de atajo que la revisión
del reloj ya retiró del stacking.
