---
tipo: concepto
status: sin-estudiar
tags:
  - nulos
  - mar
  - imputacion
  - rubrica
---

# Nulos MAR e imputación causal

> [!abstract] En una frase
> Los nulos de T30 no son aleatorios: el sensor se cae en crucero alto, y solo se puede rellenar con pasado, nunca con futuro.

## La idea

Un nulo **MAR** (*missing at random*: la ausencia depende de variables observadas) no se trata igual que uno MCAR (caída aleatoria). Aquí el sensor T30 hace dropout en crucero alto (régimen observable en alt/Mach): el patrón es físico y conocido. Imputar con la media global mezclaría regímenes; imputar con futuro (interpolar) filtraría información que en producción no existe todavía.

## La receta causal

1. **ffill por unidad**: el último valor válido del mismo motor viaja hacia adelante (solo pasado).
2. **Mediana de train** para el primer NaN de cada motor (donde no hay pasado): calculada solo con motores de ajuste, nunca con test.
3. El split por motor se hace antes: la mediana y el ffill no ven ni una fila de test.

Después del tratamiento, T30 queda en 0% de nulos sin haber mirado el futuro ni el test (`src/clase/README.md`, tabla de calidad).

## Dónde aparece en este proyecto

- `src/clase/dataset_clase.py` — construcción de la base con el tratamiento de T30 (~1.8% MAR en crucero alto).
- `src/clase/train_ensemble_adaptado.py:67` — `construir_raw_adaptado` reconstruye la base adaptada con el mismo protocolo.
- `src/clase/README.md` — tabla «Nulos antes / Nulos después» por columna.
- La prueba de que no degrada: la LGBM adaptada da 7.067 sobre la base imputada (NB05, [[e00-cifras-autoritativas]]).

> [!warning] La trampa
> «Imputé con la mediana»: ¿de qué población? Si la mediana se calculó con todo el dataset incluido el test, hay fuga por la puerta de atrás. La pregunta del tribunal es siempre el *con qué* y el *cuándo* de cada estadística.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Los nulos de T30 son MAR con patrón físico: el sensor se cae en crucero alto. Rellenamos solo con pasado del mismo motor, y la mediana de respaldo sale únicamente de los motores de ajuste».
> «Interpolar sería usar el futuro para explicar el pasado: en vuelo no hay futuro disponible».

## Flashcards

> [!question]- ¿Qué significa que los nulos de T30 sean MAR?
> Que la ausencia depende de variables observadas (régimen alt/Mach: dropout en crucero alto), no es aleatoria; por eso se imputa por régimen y por motor, no con una media global.

> [!question]- ¿Por qué el ffill es causal y la interpolación no?
> El ffill solo propaga valores pasados del mismo motor (disponibles en producción); interpolar usa lecturas futuras que en vuelo todavía no existen: fuga temporal.
