---
tipo: concepto
status: sin-estudiar
tags:
  - residualizacion
  - condiciones-operativas
  - preprocessing
  - ridge
---

# Residualización: quitar el vuelo, quedarse el desgaste

> [!abstract] En una frase
> Un sensor mide dos cosas superpuestas —cuánto se gastó el motor y cómo lo están volando—, y residualizar es restar la segunda para que el modelo solo vea la primera.

## El problema que resuelve

DS02 registra en cada ciclo cuatro canales de condición operativa `W = [alt, Mach, TRA, T2]` y catorce sensores físicos `Xs`. El valor medido de un sensor es la suma de dos procesos que no tienen nada que ver entre sí:

- **Degradación propia de la unidad**, monótona, y el único componente correlacionado con la RUL.
- **Punto operativo**: altitud, Mach, empuje y temperatura total. Se mueve con la maniobra del piloto y cambia de signo y de magnitud dentro de la vida de un mismo motor.

Sin separarlos, el modelo no puede distinguir "el motor se está rompiendo" de "lo están volando distinto". Un árbol que parte sobre el altímetro está partiendo sobre una decisión del piloto, y esa decisión no predice nada sobre la falla.

## Cómo funciona

La separación se hace antes de que cualquiera de los dos modelos vea los sensores, en cinco pasos:

1. Se estandarizan los 4 canales de `W` con su propio escalador (`src/ds02_rul/features.py:39`).
2. Se expanden a un polinomio de grado 2 sin término independiente: 4 términos lineales, 4 cuadrados y 6 interacciones, **14 términos** (`src/ds02_rul/features.py:42`).
3. Para **cada uno de los 14 sensores por separado** se ajusta una `Ridge(alpha=1.0)` que predice ese sensor a partir de los 14 términos del régimen (`src/ds02_rul/features.py:48`).
4. El residuo de cada sensor es la resta entre el valor medido y lo que el régimen explica:

$$Xs_{res} = Xs - \widehat{Ridge}_{j}\big(Poly_2(W_{std})\big)$$

5. Los 14 residuales se estandarizan con un escalador propio (`src/ds02_rul/features.py:52`), porque tienen mucha menos varianza que los sensores crudos y sin eso el sensor de mayor magnitud dominaría los cortes del árbol y los coeficientes del meta-aprendiz.

**Qué quita.** El régimen del vuelo: altitud, Mach, empuje y temperatura. **Qué deja.** El desgaste acumulado, que es lo que correlaciona con la RUL.

Tres decisiones que sostienen el método:

| Decisión | Razón |
|---|---|
| grado 2 | el acoplamiento entre Mach y la temperatura de entrada es genuinamente no lineal, y 14 términos sobre 4 entradas es un costo mínimo |
| una ridge por sensor | el modelo físico es "cada sensor responde al régimen con su propia ganancia"; una regresión conjunta volvería a mezclar los 14 procesos |
| `alpha = 1.0` | encoge los términos cuadráticos: una unidad con poca diversidad de maniobra no puede sobreajustar su propio modelo de régimen |

## Dónde aparece en este proyecto

- `src/ds02_rul/features.py:25` — `fit_preprocessing` ajusta escaladores, base polinómica y las 14 ridges **solo con las unidades de ajuste**; el docstring lo declara en `features.py:5`.
- `src/ds02_rul/residualizer.py:32` — `SensorResidualizer.transform` reproduce el mismo cálculo en inferencia: expande `W`, resta la predicción y estandariza.
- `src/ds02_rul/features.py:105` — el residual se calcula antes de cortar ventanas, así que la rama tabular y la recurrente parten del mismo preproceso.
- Quién consume qué: la rama tabular lee **solo** los residuales; la rama recurrente recibe los 18 canales escalados globalmente más el ciclo como canal 19. El reparto completo está en [[s04-ventanas-y-features]].
- El ajuste sin fuga de este paso es el tema de [[s03-preproceso-sin-fuga]].

## Qué alternativa se rechazó

| Alternativa | Por qué no |
|---|---|
| Ignorar `W` por completo | El modelo no puede distinguir degradación de maniobra; la rama tabular no tiene forma de normalizar el régimen |
| Pasar `W` al árbol como estadísticas | Máximos, mínimos, desviaciones y diferencias sobre `W` meten ruido de maniobra directamente en los candidatos de corte |
| Podar `W` a media y último valor | Recupera parte del rendimiento, pero nunca alcanza a la rama secuencial: el árbol sigue sin poder separar maniobra de falla |
| Una sola regresión multivariada de los 14 sensores | Vuelve a mezclar los procesos de degradación que se querían separar |

> [!warning] La trampa
> Residualizar no es gratis. Si parte del desgaste real depende del régimen —un motor que siempre vuela exigido se degrada más rápido—, el residuo también se lleva esa señal, porque la resta no distingue causa de coincidencia. Además, el polinomio se ajusta en las unidades de ajuste: si en test el régimen cae fuera del rango visto, la extrapolación cuadrática no está garantizada. Y el residuo sigue siendo el residuo de un modelo de grado 2: si el acoplamiento real es de orden mayor, queda estructura sin quitar.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Un sensor mide dos cosas a la vez: cuánto se gastó el motor y cómo lo están volando. Antes de entrenar nada, resto la segunda».
> «Para cada sensor ajusto una ridge sobre un polinomio de grado 2 de los cuatro canales operativos, y lo que queda es el desgaste».
> «Es una por sensor y no una multivariada, porque el modelo físico es que cada sensor responde al régimen con su propia ganancia».

## Flashcards

> [!question]- ¿Qué dos componentes contiene el valor medido de un sensor en DS02?
> La degradación propia de la unidad —monótona y correlacionada con la RUL— y el punto operativo, que depende de altitud, Mach, empuje y temperatura y no correlaciona con el desgaste.

> [!question]- ¿Cuántos términos tiene el polinomio de grado 2 sobre 4 canales y cómo se reparten?
> Catorce: 4 lineales, 4 cuadrados y 6 interacciones entre pares distintos.

> [!question]- ¿Por qué una ridge por sensor en lugar de una regresión conjunta?
> Porque cada sensor responde al régimen con su propia ganancia. Una regresión conjunta volvería a mezclar los 14 procesos de degradación que la residualización intenta separar.

> [!question]- ¿Por qué se estandariza el residual con un escalador aparte?
> Porque su varianza es mucho menor que la de los sensores crudos. Sin ese escalado, el canal de mayor magnitud dominaría los cortes del árbol y los coeficientes del meta-aprendiz.

## Conexiones

Antes: [[c03-fuga-de-informacion]] · Después: [[s03-preproceso-sin-fuga]]
