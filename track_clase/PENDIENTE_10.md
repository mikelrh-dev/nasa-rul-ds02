# Pendiente para el 10 — Reto 1 SAA + PIA + MIA (rúbrica v5)

> Foto a 2026-11-03. Marcar `[x]` al completar cada ítem **con su evidencia**.
> Leyenda: ✅ hecho · ⚠️ parcial · ❌ pendiente.

---

## SAA — Sistemas de Aprendizaje Automático

- [x] **SAA-2 (10%) — tipo de aprendizaje.** Supervisado-regresión + diferencia con no supervisado en `track_clase/README.md`. Solo defenderlo.
- [x] **SAA-5 (5%) — nulos + variable nueva.** MAR auditado + ffill causal + `fase_vuelo`. Hecho.
- [x] **SAA-6 (30%) — cinco modelos + extra.** Ridge/KNN/RF/XGB/SVR + GridSearchCV GroupKFold + híbrido como extra. Hecho.
- [x] **SAA-7 (20%) + coherencia val en MLP.** Hecho 2026-11-03 (slice 2a): OOF por motor para los 4; elegido **E2 (val 7.34)** — E1 memoriza train (5.23) y pierde en val (7.48); test solo en E2 (7.72); NB02 13/15/16/18/20/26 retejido; tests verdes.
- [x] **SAA-1 (5%) — comparar con IA fuerte.** Hecho: NB01 celda 2 ya lo trae + párrafo explícito en `track_clase/README.md`. Solo saber decirlo.
- [x] **SAA-3 (5%) — qué campos se quitan y por qué.** Verificado: NB01 celda 5 ya trae **Descartes** (nada se descarta; unit→grupo, RUL→objetivo). Sin cambios.
- [x] **SAA-4 (5%) — 5 gráficos comentados.** Verificado: las 5 figuras llevan QUÉ VEO + CONCLUSIÓN en celdas 8/10/12/14. Sin cambios.
- [x] **SAA-8 (10%) — métricas en train y VALIDACIÓN + significado empresa.** Hecho 2026-11-03: CSV con train/val, NB02 retejido, párrafo negocio en README (RMSE=gordos caros, MAE=margen taller).
- [ ] **SAA-9 (5%) — SHAP en validación + captura MLflow.** Falta: (a) `track_clase/shap_clase.py` hoy explica TEST → pasar a validación; (b) captura MLflow en README. Evidencia: `shap_importancia.png/csv` desde validación (HECHO 2026-11-03 slice 2b: fold-0, top cycle/T50/Nc, tests verdes) + captura (queda para PIA-4, fuera de este change).
- [ ] **SAA-transversal — test una sola vez.** Falta: elegir mejor modelo por validación, no por `rmse_test` (`train_clasicos.py:103`); reservar test como lectura única final. Evidencia: código + CSV coherente.
- [ ] **SAA-10 — pregunta individual.** Preparación + corte de 15 min (nuevo en v5).

## PIA — Programación de IA

- [x] **PIA-1 (10%) — README + funciones.** 6 apartados + extras + docstrings. Hecho (repasar antes de entregar).
- [x] **PIA-3 (20%) — pipeline compartido.** `ColumnTransformer` + joblib con pipeline. Hecho.
- [x] **PIA-2 (10%) — estructura + requirements.** Hecho: Estructura mapea nombres reales contra spec del reto; requirements pinnea todo lo usado (sin mlflow a propósito: nada lo importa).
- [ ] **PIA-4 (20%) — MLflow.** ❌ Falta entero: loguear 5 clásicos + MLP (hiperparámetros y métricas) + captura de la comparativa en MLflow para el README §6. Evidencia: `mlruns/` + capturas en `resultados/`.
- [x] **PIA-5 (25%) — app Streamlit.** Hecho en texto: app↔bundle B (test + caso nuevo con decisión, p=RUL junto a decisión) y notebooks+README↔MLP-E2 (test lectura única). Resta captura manual si la app cambia.
- [ ] **PIA-6 — pregunta individual.** Preparación.

## MIA — Modelos de IA

- [x] **MIA-2 (30%) — 6 reglas.** R2b+R6+R1+R9+R8+R7 con prioridad, porqué y seguridad R1. Hecho (sabed explicar prioridad y R1).
- [x] **MIA-1 (20%) — mejora cuantificada.** Hecho: ≈50 k€ por cada AOG evitado en `track_clase/README.md`.
- [ ] **MIA-3 (35%) — flujo n8n.** ❌ Falta entero: webhook que recibe la decisión + una rama por decisión (HANGAR→Postgres+Calendar+correo, INSPECCIÓN→Sheets, APTO→log); para el 10, acción distinta a las vistas en clase. Evidencia: `n8n/flujo.json` real + `src/n8n.py` sin stub + prueba end-to-end.
- [ ] **MIA-4 — pregunta individual.** Preparación.

---

## Orden sugerido (por peso × esfuerzo)

1. MIA-3 (n8n) + PIA-4 (MLflow) — los dos ceros que más ponderan.
2. SAA-8 + SAA-9 + test-una-vez — barato, desbloquea dos 10.
3. Remates de 1 frase/celda — SAA-1, SAA-3, SAA-4 (verificar), MIA-1, PIA-2, PIA-5.
