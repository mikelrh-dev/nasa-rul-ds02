---
tipo: defensa
status: sin-estudiar
tags:
  - preguntas
  - tribunal
  - respuestas
---

# Banco de preguntas — 56 con respuesta corta

> [!abstract] En una frase
> Si respondes estas 56 sin leer, el tribunal no te saca del mapa.

## Cómo usar este banco

Respondés en voz alta: respuesta corta, por qué funciona y seguimiento probable. Si fallas, vas a la nota dueña, no te quedas aquí.

| # | Pregunta | Respuesta corta | Seguimiento |
|---|---|---|---|
| 1 | ¿Qué predices? | RUL en ciclos por ventana | ¿Por qué regresión? [[c01-que-es-rul]] |
| 2 | ¿Por qué no clasificación? | El objetivo es continuo | Umbrales después [[s13-capa-de-reglas-y-decision]] |
| 3 | ¿Qué es una ventana? | 50 filas de un motor | ¿Cuánto cubre? 0,44 ciclos |
| 4 | ¿Qué es stride? | 1 de cada 100 filas | ¿Y step? 3 train, 2 test |
| 5 | ¿Qué trae W y Xs? | 4 régimen, 14 sensores | Nombres en [[s02-datos-ds02-y-reparto]] |
| 6 | ¿Cómo partes? | 5 ajuste, 16 holdout, 11/14/15 test | ¿Por qué por motor? Solape 94 % |
| 7 | ¿Qué es fuga? | Entrenar con lo que no tendrás | 4 defensas [[c03-fuga-de-informacion]] |
| 8 | ¿Con qué ajustas scaler? | 44 982 filas de ajuste | ¿Y holdout? Cero filas |
| 9 | ¿Qué es OOF? | Predicción de quien no te vio | Folds por motor [[c10-oof-y-validacion-agrupada]] |
| 10 | ¿Qué hace beta? | Contrae campeón hacia meta | Fórmula en [[s09-oof-y-beta]] |
| 11 | ¿Cuánto vale beta? | 1.0, mediana 1.0, IQR 0.5 | ¿Unanimidad? No, un fold pide 0 |
| 12 | ¿Qué es el meta? | RidgeCV más LGBM somero en la 16 | 2 535 ventanas |
| 13 | ¿Qué da LightGBM? | 7.067 adaptada solo, cuantil 0,35 | ¿Por qué sigue? Complementa, y prueba la base [[s18-lgbm-adaptada]] |
| 14 | ¿Qué da BiLSTM-C? | 5.65 solo | ¿Por qué varía? TF en CPU [[c20-multisemilla-y-ruido]] |
| 15 | ¿Qué da el híbrido-C? | 4.322 ± 0.064, disco 4.338 | Fuente [[e00-cifras-autoritativas]] |
| 16 | ¿Qué es pinball? | Pérdida cuyo mínimo es el cuantil | Alpha 0,35 [[c05-regresion-cuantilica]] |
| 17 | ¿Qué es triple pooling? | Last, media y máximo | Evita Lambda [[s06-bilstm-triple-pooling]] |
| 18 | ¿Qué es EMA? | Media exponencial causal por motor | Span 5 [[c13-ema-causal]] |
| 19 | ¿Por qué causal? | No mira futuro | Centrada sería trampa |
| 20 | ¿Qué es cyc_norm? | Ciclo dividido por 100 | Canal 19 y feature |
| 21 | ¿Aporta el ciclo? | Sí, ~1 ciclo en híbrido | Solo reloj da 14.33 |
| 22 | ¿Qué es NASA score? | Suma asimétrica, sobreestimar cuesta más | 1/10 vs 1/13 [[c04-metricas-y-baseline]] |
| 23 | ¿Qué es macro-RMSE? | Promedio por motor sin ponderar | 5.0153 vs 4.338 (bundle C) |
| 24 | ¿Por qué macro? | El 14 esconde el ponderado | 8.02 con 760 filas |
| 25 | ¿Qué es baseline? | Media de train, 20.022 | Suelo, no modelo |
| 26 | ¿Qué es conformal? | Punto más banda con residuales no vistos | 90 pedido, 100 medido |
| 27 | ¿Con qué calibras? | 17 450 ventanas OOF | Ancho 26.41 |
| 28 | ¿Por qué por tramos? | El error crece con RUL | Bins en manifiesto |
| 29 | ¿Qué pasó en la 16? | Colapsa a 3.35 con 31 % | Se rechazó |
| 30 | ¿Qué es L_inf? | Borde inferior, decide estado | 30 y 25 |
| 31 | ¿Qué es R2b? | Isotónica causal, sube 1.33 máx | Mejor que R2 |
| 32 | ¿Qué guardas? | Joblib, keras, manifiesto | Hashes en [[s12-persistencia-y-contrato]] |
| 33 | ¿Qué es reload? | Recargar y predecir igual | `load_ensemble` verifica SHA |
| 34 | ¿Qué es lead time? | Ciclos de aviso antes del fallo | 9/23/17 en media |
| 35 | ¿Por qué tres semillas? | TF en CPU mueve ±0.1 | Media y dispersión [[c20-multisemilla-y-ruido]] |
| 36 | ¿Qué es NB04? | OOF, beta y ensamble vivo | beta 1.0 y p_ens [[n06-recorrido-nb04]] |
| 37 | ¿Qué es NB05? | Multisemilla, diagnóstico y LGBM adaptada | 7.067 puente [[n07-recorrido-nb05]] |
| 38 | ¿Qué no decide? | La RUL sola | Decide L_inf |
| 39 | ¿Qué cifras no dices? | Las de la lista negra de corridas viejas | Detalle en [[d05-como-decir-las-cifras]] |
| 40 | ¿Qué manda si discrepan? | El manifiesto | Repo manda [[s12-persistencia-y-contrato]] |
| 41 | ¿Qué es el grano? | Fila o ventana: lo que puntúa el modelo | Nunca ranking mixto [[c15-grano-fila-vs-ventana]] |
| 42 | ¿Quién gana en fila? | MLP E2, test 7.72, elegido por val | SAA-9: cada grano su campeón |
| 43 | ¿Por qué GroupKFold por motor? | Filas vecinas no son independientes | Validar memoria si no [[c16-groupkfold-por-motor]] |
| 44 | ¿Cómo tratas T30? | ffill causal + mediana de train | MAR con patrón físico [[c17-nulos-mar-e-imputacion-causal]] |
| 45 | ¿Qué es fase_vuelo? | Ascenso/Crucero/Descenso de alt/Mach | OneHot, sin orden [[c18-fase-vuelo-y-onehot]] |
| 46 | ¿Dónde vive cyc_norm? | ON en red, OFF en meta | Medido: 5.419→4.338 [[c19-ablacion-cyc-norm]] |
| 47 | ¿Qué es la tabla final? | Una tabla, dos campeones por grano | `tabla_final.py:18` [[s19-tabla-final-y-grano]] |
| 48 | ¿Qué es el bundle C? | Híbrido sobre base adaptada, 4.338 | Fila 42, media 4.322 [[s20-ensemble-adaptado-y-bundle-c]] |
| 49 | ¿Qué explica SHAP? | Contribución por feature, no métrica | `shap_xgb_top.joblib` [[c21-shap-e-ia-debil]] |
| 50 | ¿IA débil o fuerte? | Débil: solo RUL de DS02 | Barata y auditable, a propósito |
| 51 | ¿Dónde está el flujo n8n? | Pendiente declarado (MIA-3) | HANGAR → Postgres+Calendar+correo; diseño previsto en `s14` |
| 52 | ¿Dónde está MLflow? | Pendiente declarado (PIA-4) | Tabla y tiempos en CSV + captura app; tracking completo, siguiente change |
| 53 | ¿Por qué sin SMOTE? | Regresión: sin clases | El desbalance es el motor 14 → macro-RMSE [[c21-shap-e-ia-debil]] |
| 54 | ¿Por qué IA débil? | Solo RUL de DS02; fuerte no existe aquí | Barata, rápida, auditable: la estrechez es la virtud [[c21-shap-e-ia-debil]] |
| 55 | ¿Qué aprendizaje usas? | Supervisado de regresión | Etiqueta RUL; sin ella no hay error ni elección [[c21-shap-e-ia-debil]] |
| 56 | ¿Dónde está el pipeline? | `pipeline_clase.py:22`, un ColumnTransformer | Incluye preproceso y predice caso nuevo [[s16-pipeline-de-clase]] |

## Di esto en el tribunal

> [!quote]
> «Pregúntame por reparto, fuga, beta, banda y decisión: cada una tiene número, archivo y límite. Si no lo sé decir en dos frases, me voy a la nota dueña.»

## Flashcards

> [!question]- ¿Cuánto da cada modelo?
> LGBM adaptada 7.07, BiLSTM-C 5.65, híbrido-C 4.32 con disco 4.34.

> [!question]- ¿Qué tres números de protocolo no fallan?
> 44 982 filas de ajuste, beta 1.0, 17 450 de banda.

> [!question]- ¿Qué dos cifras viejas te tienden trampas?
> Las de la lista negra: corridas anteriores, no bundle (detalle en [[d05-como-decir-las-cifras]]).

> [!question]- ¿Qué afirma esta nota en una frase?
> Si respondes estas 40 sin leer, el tribunal no te saca del mapa.

> [!question]- ¿Cómo la contarías en el tribunal?
> «Pregúntame por reparto, fuga, beta, banda y decisión: cada una tiene número, archivo y límite. Si no lo sé decir en dos frases, me voy a la nota dueña.»

