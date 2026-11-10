---
title: Catálogo de 12 decisiones
course: Reto 1 · SAA+PIA+MIA
block: 10 — Decisiones
node: E2
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - decisiones
  - adr
---

# Catálogo de 12 decisiones

> [!abstract] En una frase
> Doce decisiones, una línea cada una: qué se eligió, qué se rechazó y por qué. Es la munición
> para cualquier «¿por qué así?» del tribunal.

| ADR | Elegimos | Rechazamos | Por qué (una línea) |
|---|---|---|---|
| 001 | Meta-aprendizaje sobre dos predicciones | Promedio lineal fijo | El promedio arrastra el error de la rama que falla |
| 002 | Residualizar sensores sobre condiciones | Usar sensores crudos | El sensor mide pilotaje, no degradación |
| 003 | Cuantil asimétrico 0,35 | RMSE simétrico | El coste de predecir tarde es mayor |
| 004 | Boosting + Ridge sobre clásicos | SVM/KNN como modelo final | Precisión con el mismo pipeline y menos coste |
| 005 | Unidad 16 como holdout del meta | Ajustar el meta en el OOF | Sin unidad reservada, el 4,34 estaría contaminado |
| 006 | EMA causal de la predicción | Predicción cruda por ventana | Reduce el ruido sin mirar el futuro |
| 007 | Mantener el cuantil 0,35 | Objetivo mediana | La mediana mejora en dev y empeora en test |
| 008 | Banda conformal como cota inferior | Intervalo del modelo | Necesitamos una cota para decidir, no una promesa |
| 009 | R2b como ajuste isotónico causal | Regla de monotonía estricta | Corrige tendencias que no suben, no impone monotonía |
| 010 | Gemelo en proceso + push a n8n | Simulador desacoplado y polling | No hay infraestructura pub/sub y el polling añade latencia |
| 011 | Bundle C desplegado, B archivado | Mantener dos bundles vivos | Un solo artefacto reproducible y un histórico declarado |
| 012 | Verificar la banda con instrumento congelado | Recalibrar en test | Recalibrar en la 16 colapsa a 31 % de cobertura |

## Cómo se usa en vivo

- Si preguntan por mezcla → 001.
- Por features → 002 y 006.
- Por métrica → 003, 007 y 008.
- Por validación → 005 y 012.
- Por la acción → 010.

## Evidencia

- `docs/decisions/ADR-001…ADR-012` (cada uno con contexto, decisión, alternativas, consecuencias
  y verificación).

## Pregunta probable

**«¿Cuál fue la decisión más difícil?»**
→ «La 007: la mediana ganaba en desarrollo por unanimidad y perdía en test. Mantener el cuantil
fue aceptar que el desarrollo se equivocaba, y está escrito con la evidencia de los dos lados.»

## Lo que NO digo

- No cuento una decisión sin su alternativa.
- No digo «lo probamos todo»: doce decisiones, no cien experimentos.

## Di esto en el tribunal

> «Doce decisiones documentadas; en cada una sé qué rechacé y por qué, y en dos de ellas el
> desarrollo se equivocó y lo dejé escrito.»

## Flashcards #flashcards

- ¿Qué decisión se equivocó en desarrollo y acertó en test? :: la 007: mediana en dev, cuantil 0,35 en test.
- ¿Qué decide la 005? :: reservar la unidad 16 como holdout del meta-aprendiz.
- ¿Qué rechaza la 010? :: el simulador desacoplado y el polling a n8n.
