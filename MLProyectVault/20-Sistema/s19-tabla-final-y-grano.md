---
tipo: sistema
status: sin-estudiar
tags:
  - tabla-final
  - grano
  - saa
---

# Tabla final — una tabla, dos campeones

> [!abstract] En una frase
> `tabla_final.py` junta todos los modelos en una tabla con columna `grano` y prohíbe ordenarlos juntos: cada grano corona al suyo.

## Contrato

| Entra | Sale |
|---|---|
| Métricas de clásicos, MLP, LGBM adaptada y bundle C | Una fila por modelo con `grano` explícito para el README |

## Cómo está implementado

| Pieza | Dónde | Qué hace |
|---|---|---|
| `COLUMNAS` | `src/clase/tabla_final.py:18` | modelo, familia, **grano**, rmse_val/test, mae, r2, nasa, tiempo, n_test |
| Regla SAA-9 | cabecera de `tabla_final.py` | filas `grano=fila` y `grano=ventana` nunca se ordenan juntas |
| Campeón fila | MLP E2 (7.72) | mejor de su grano por validación |
| Campeón ventana | Híbrido-C (4.338, media 4.322±0.064) | desplegado, bundle C |

## Conexiones

- La regla: [[c15-grano-fila-vs-ventana]] · fila: [[s17-clasicos-y-mlp]] · ventana: [[s20-ensemble-adaptado-y-bundle-c]] · cifras: [[e00-cifras-autoritativas]]

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Una tabla, dos podios: la columna grano impide que la ventana compita contra la fila. El MLP gana su liga con 7.72 y el híbrido la suya con 4.338».

## Flashcards

> [!question]- ¿Qué impide la tabla final y cómo?
> El ranking mixto: cada fila lleva su `grano` (`tabla_final.py:18`) y los campeones se eligen por grano separado (MLP E2 en fila, híbrido-C en ventana).
