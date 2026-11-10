---
title: PIA · Streamlit, test y caso nuevo
course: Reto 1 · SAA+PIA+MIA
block: 08 — PIA código
node: C5
indicador: PIA-5
descriptor: 10
spine: false
status: en-curso
tags:
  - pia
  - streamlit
  - rubrica/pia-5
---

# PIA · Streamlit, test y caso nuevo

> [!abstract] En una frase
> La app hace las dos cosas que pide la rúbrica y una tercera que solo pide el 10: enseña el
> test, predice un caso nuevo **y muestra el valor predicho junto a la decisión**.

## Qué digo

«La app tiene dos partes. Una evalúa el modelo congelado contra test: métricas, real frente a
predicho y desglose por motor. La otra toma un motor y un ciclo, construye su ventana y predice
un caso nuevo: muestra el RUL estimado, el límite inferior de la banda y la decisión que sale de
las reglas, con la regla que la disparó. El valor predicho y la decisión se ven juntos, no en
pestañas distintas.»

## Por qué se dice así

- PIA-5 da 10 por «muestra la p del caso nuevo junto a la decisión». En regresión, la `p` es el
  valor predicho: aquí es el RUL con su `L_inf`.
- Enseñar la regla que disparó la decisión convierte la app en auditable, que es el argumento de
  MIA.

## Evidencia

- `app/dashboard_ds02.py` (pestaña de motor: gauge, `L_inf`, decisión y traza de reglas).
- `app/ui_modulos/_tab_motor.py` (`traza_decision`, columna de decisión junto al gauge).
- `app/ui_inference.py` (caso nuevo, `regla_decision`).
- Test una sola vez: métricas del artefacto en la pestaña de auditoría.

## Pregunta probable

**«¿La app reentrena o carga el artefacto?»**
→ «Carga el artefacto congelado y su manifiesto. Si reentrenara, cada demo daría un número
distinto y el test dejaría de ser único.»

## Lo que NO digo

- No digo «la app evalúa con test» sin decir que el modelo está congelado.
- No presento la banda como intervalo de confianza.
- No prometo que la app funcione sin red: todo es local, pero se comprueba antes.

## Di esto en el tribunal

> «La app evalúa el artefacto congelado con test y, para un caso nuevo, enseña el RUL, el límite
> inferior y la decisión con la regla que la disparó.»

## Flashcards #flashcards

- ¿Qué tres cosas enseña la app para un caso nuevo? :: RUL estimado, límite inferior de la banda y decisión con su regla.
- ¿La app reentrena? :: no: carga el artefacto congelado y su manifiesto.
