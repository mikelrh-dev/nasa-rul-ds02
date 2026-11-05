---
tipo: concepto
status: sin-estudiar
tags:
  - features
  - fase-vuelo
  - onehot
  - rubrica
  - pia
---

# Fase de vuelo y OneHot

> [!abstract] En una frase
> El régimen de vuelo (ascenso/crucero/descenso) se deriva de alt/Mach y entra al modelo como categórica con OneHot: el sensor crudo manda régimen, la fase deja ver degradación.

## La idea

Los sensores crudos (T48, presiones) responden sobre todo al régimen: a más empuje, más temperatura, esté el motor sano o degradado. Sin desacoplar, el modelo aprende pilotaje en vez de salud (ADR-002). La **fase de vuelo**, derivada de altitud y Mach (Ascenso 26% / Crucero 30% / Descenso 44%), le dice al modelo *en qué contexto* se midió cada lectura, y la RUL media difiere por fase: la categórica tiene señal propia.

## Por qué OneHot y no un número

Ascenso/Crucero/Descenso no tienen orden numérico (Crucero no es «el doble» de Ascenso). Codificarlas como 0/1/2 inventaría una distancia falsa. El **OneHot** crea una columna binaria por fase sin imponer orden, y `handle_unknown=ignore` evita que una fase no vista en ajuste rompa la predicción.

## Dónde aparece en este proyecto

- `src/clase/dataset_clase.py` — deriva `fase_vuelo` de alt/Mach.
- `src/clase/pipeline_clase.py:22-24` — `NUM_COLS` (19 numéricas con StandardScaler) + `CAT_COLS = ["fase_vuelo"]` con OneHot en un solo `ColumnTransformer` (PIA 3).
- `src/clase/README.md` — el EDA muestra T48 separada por fase: el sensor crudo manda régimen.
- Justifica el OneHot que pide la rúbrica PIA 3: sin fase no hay categórica que codificar.

> [!warning] La trampa
> «Metí la fase como 0/1/2 y funciona»: funciona hasta que el modelo extrapola la falsa escala (¿qué es fase 1.5?). El orden inventado es deuda que se paga en producción.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Derivamos la fase de vuelo de altitud y Mach porque el sensor crudo cuenta régimen, no salud; sin contexto de fase, el modelo aprendería a distinguir pilotaje en vez de degradación».
> «Es categórica nominal y entra con OneHot: tres columnas binarias, sin distancias inventadas».

## Flashcards

> [!question]- ¿Por qué se crea la variable fase_vuelo?
> Porque los sensores crudos responden al régimen de vuelo más que a la degradación; la fase (de alt/Mach) da contexto a cada lectura y su RUL media difiere por fase, así que aporta señal propia.

> [!question]- ¿Por qué OneHot en vez de 0/1/2?
> Porque las fases son nominales sin orden: codificarlas como números inventaría distancias falsas (¿fase 1.5?). OneHot crea una binaria por fase, con `handle_unknown=ignore` para fases no vistas.
