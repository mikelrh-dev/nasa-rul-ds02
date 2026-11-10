---
title: Frases prohibidas
course: Reto 1 · SAA+PIA+MIA
block: 11 — Tribunal
node: F5
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - tribunal
  - frases
---

# Frases prohibidas

> [!abstract] En una frase
> Hay frases que bajan la nota solas, porque delatan que no se entiende lo que se hizo. Se
> sustituyen antes de que salgan.

| No digo | Digo |
|---|---|
| «El modelo predice la vida útil exacta» | «Estima el RUL con un error de ~3 ciclos» |
| «Elegí el mejor por test» | «Elegí por validación; el test se leyó una vez» |
| «Normalicé el dataset» | «El escalado se ajusta solo en train, dentro del pipeline» |
| «El intervalo de confianza al 90 %» | «Una cota calibrada con residuales fuera de fold» |
| «SHAP demuestra que…» | «SHAP describe qué pesó en esta predicción» |
| «Evita los fallos» | «Prioriza inspecciones con antelación medida» |
| «Está en producción» | «Instancia local con ejecuciones reales» |
| «Lo hizo mi compañero» | «Esa parte la defiende él; la mía es esta» |
| «No dio tiempo» | «Lo descartamos porque…» (con razón técnica) |
| «Es un modelo muy potente» | La cifra y el coste |
| «Todos los experimentos están en MLflow» | «Trece runs; falta la ablación y lo declaro» |
| «Funciona bien en todos los motores» | «El 14 concentra el 48 % del error» |

## Las tres que más duelen

1. **«Predecimos exactamente»** → niega el error, y el error es el argumento.
2. **«Elegí por test»** → invalida todo el protocolo en una frase.
3. **«Está en producción»** → una afirmación comprobable y falsa.

## Regla de oro

Si una frase no la puedo respaldar con `path:línea`, una cifra del manifiesto o un run, no la
digo. La defensa se gana por lo que se calla, no solo por lo que se dice.

## Di esto en el tribunal

> «No digo que acierte siempre: digo cuánto se equivoca y con qué margen decide.»

## Flashcards #flashcards

- ¿Qué digo en vez de «intervalo de confianza»? :: una cota calibrada con residuales fuera de fold.
- ¿Qué frase invalida el protocolo entero? :: «elegí por test».
