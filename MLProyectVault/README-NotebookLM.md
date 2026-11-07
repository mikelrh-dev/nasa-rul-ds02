# Cuadernos NotebookLM del vault

Enlace directo a cada cuaderno de NotebookLM con lo que explica. Para estudiar el vault poco a poco.

## DS02 (proyecto)

| Cuaderno | Enlace | Fuentes | Qué explica |
|---|---|---|---|
| DS02 - NB01-NB06 La cadena que congela C | [Abrir](https://notebooklm.google.com/notebook/0813ce57-8421-4c00-9ab6-85122ca902b9) | 16 | Los 6 notebooks en cadena: EDA, clásicos y MLP, feature engineering secuencial, BiLSTM OOF, meta-ensamble y conformal, y evaluación final en producción. |
| DS02 - src/ds02_rul contrato por modulo | [Abrir](https://notebooklm.google.com/notebook/59611f3d-5011-40ac-8785-4c8bff83d44b) | 8 | El contrato del código: protocolo honesto, datos y preproceso sin fuga, ventanas, LightGBM cuantil, BiLSTM, EMA, OOF y stacking, banda conformal y persistencia. |
| DS02 - Conceptos base c00-c07 | [Abrir](https://notebooklm.google.com/notebook/6967fe72-3e73-4790-84b3-b7c0202000a2) | 8 | Glosario, qué es RUL, ventanas, fuga de información, métricas y baseline, regresión cuantil, BiLSTM y pooling. Video y presentación listos. |
| DS02 - Conceptos avanzados c08-c16 | [Abrir](https://notebooklm.google.com/notebook/9bd5718d-1366-4ab0-bd96-271c0c68e75d) | 9 | Residualización, ensembles, OOF y validación agrupada, shrinkage beta, conformal, EMA causal, ruido y reproducibilidad, grano fila vs ventana y GroupKFold. Video y presentación listos. |

## MLProyect N0-N6 (bloques del vault, octubre)

| Cuaderno | Enlace | Fuentes | Qué explica |
|---|---|---|---|
| MLProyect N0 — Mapa maestro | [Abrir](https://notebooklm.google.com/notebook/83e383d8-0269-429c-8e64-b0665874180e) | 8 | Mapa general: los diagramas B1-B6 y el índice del vault. |
| MLProyect N1 — B1 Protocolo honesto | [Abrir](https://notebooklm.google.com/notebook/cd538db2-bdc3-45de-a139-a45d2337bef7) | 7 | Qué predecimos (RUL por ventanas), reparto por motor sin fuga y baseline de media train. |
| MLProyect N2 — B2 Prepro y features | [Abrir](https://notebooklm.google.com/notebook/e1113484-2271-498e-ba94-08a9fbdb17da) | 7 | Preproceso y features del DS02. |
| MLProyect N3 — B3 Modelos base | [Abrir](https://notebooklm.google.com/notebook/1fc5da84-69ea-4a6c-9e19-63024be98c90) | 7 | Modelos base del proyecto. |
| MLProyect N4 — B4 Ablación, OOF y beta | [Abrir](https://notebooklm.google.com/notebook/1429e229-ecca-4321-ac77-4e944ef79f74) | 7 | Ablación, OOF y beta. |
| MLProyect N5 — B5 Ensamble y conformal | [Abrir](https://notebooklm.google.com/notebook/bfd4a5ff-8201-4820-adcf-eff0126e98c8) | 7 | Ensamble híbrido y banda conformal. |
| MLProyect N6 — B6 Evidencia y diagnóstico | [Abrir](https://notebooklm.google.com/notebook/54ab9848-1195-4fe4-a81c-25e0a18f807c) | 9 | Evidencia, diagnóstico y cifras finales. |

## Pendientes de crear en NotebookLM (plan poco a poco)

Faltan cuadernos por crear para el resto del vault. No tienen enlace todavía: se crean al estudiar cada tramo, sin inventar IDs.

| Falta | Qué cubriría |
|---|---|
| c17–c26 | Nulos/maru, fase one-hot, ablación, multisemilla, SHAP, negocio, validez UI, gemelo/hangar, seguridad API, deriva |
| s15–s23 | Dataset/pipeline de clase, clásicos/MLP, LGBM adaptada, tabla final, ensemble/bundle C, puente/multisemilla, SHAP/app de clase, DSS por pestañas |
| NB07 | SHAP por ramas sobre bundle C ([[n09-recorrido-nb07]]) |
| n8n | Flujo MIA-3 `ds02/decision` ([[s24-n8n-mia3]]): webhook, Switch, Sheets/Postgres/Calendar/Gmail; flujo inactivo esperando credenciales |
