---
title: Huecos declarados
course: Reto 1 · SAA+PIA+MIA
block: 12 — Rúbrica
node: G2
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - rubrica
  - huecos
---

# Huecos declarados

> [!abstract] En una frase
> Cinco cosas que el proyecto no tiene y que se dicen **antes** de que las pregunten. Declararlas
> cuesta menos que negarlas.

## 1. PIA-4 no llega a 10

- **Qué falta**: la ablación de `cyc_norm` no es una run de MLflow (`grep -ril cyc_norm mlruns
  --include=meta.yaml` → 0).
- **Además**: el store `mlruns/` tiene 94 rutas sin versionar (13 modificadas + 81 nuevas).
- **Cómo se dice**: «trece runs registrados; la ablación está medida en el notebook y en el README,
  pero no registrada como run».

## 2. La estructura no es literal

- La rúbrica dibuja `src/reglas.py`, `src/n8n.py`, `app/streamlit_app.py` y `data/processed/`.
  Nosotros usamos `src/mia/`, `app/dashboard_ds02.py` y `app/cache/*.parquet`.
- **Cómo se dice**: con la tabla de equivalencias de [[81-pia-estructura-de-carpetas]].

## 3. El test solo aparece en el elegido

- En `comparativa.csv` solo XGB tiene columnas de test; es correcto (se lee una vez).
- **Cómo se dice**: «las columnas vacías son la prueba de que no se eligió mirando el test».

## 4. n8n no está en producción

- El flujo versionado está `active:false` por diseño; la instancia local sí ejecutó (29 veces el
  2026-11-07). No hay ejecución atribuible a la app.
- **Cómo se dice**: «instancia local con ejecuciones reales; el envío desde la app está cableado,
  pero no hay ejecución atribuible, y no la vendo».

## 5. Sin monitorización de deriva

- No hay alerta automática de cambio de distribución; el gemelo permite simular escenarios.
- **Cómo se dice**: «es el siguiente paso, no una propiedad del sistema».

## Lo que NO es un hueco

| Parece hueco | Por qué no |
|---|---|
| Dos campeones (7,72 y 4,338) | Son dos granos distintos, y se explican |
| Banda que cubre el 100 % | Es una cota; el ancho es el precio declarado |
| Sin reentreno en producción | El artefacto está congelado por diseño |
| Nulos inyectados | Es un experimento auditado, no un dato sucio |

## Di esto en el tribunal

> «Lo que falta lo digo yo: la ablación no está en MLflow, la estructura usa nombres propios y no
> hay monitorización de deriva. Todo lo demás está medido.»

## Flashcards #flashcards

- ¿Qué falta exactamente en MLflow? :: la run de la ablación `cyc_norm`.
- ¿Por qué el flujo versionado está inactivo? :: por diseño: un test exige esa configuración.
