---
tipo: notebook
status: sin-estudiar
tags:
  - nb01
  - datos
  - bases
---

# NB01 — Datos y bases

> [!abstract] En una frase
> Este cuaderno deja el terreno listo: datos partidos por motor, preproceso sin fuga y dos bases entrenadas.

## Antes de empezar

Requiere el HDF5 en `archive/CCMaps/N-CMAPSS_DS02-006.h5` y `pyproject.toml` en la raíz para fijar el `cwd`. Tarda unos minutos: LightGBM 0.27 s y BiLSTM unos 65 s en la corrida verificada.

Carga `ds02_rul` 4.1.0 con Python 3.12.10, Keras 3.15.1, LightGBM 4.7.0 y sklearn 1.9.1. La celda 1 imprime `cwd` y versiones; si el `cwd` no es la raíz, las rutas no resuelven.

Guarda en `notebooks/ds02_ensemble/artifacts/`: lo que NB02 recargará como `[LOAD NB1 OK]`.

## Recorrido celda a celda

| Celda | Qué entra | Qué hace | Qué sale | Por qué está ahí |
|---|---|---|---|---|
| 1 | Imports y `SEEDS [42,7,123]` | Fija entorno y versiones | `python 3.12.10`, `ds02_rul 4.1.0` | Sin entorno fijo no hay reproducibilidad |
| 2–3 | `viz.py` | Carga tablas y alias de presentación | `[VIZ OK]`, `[FASE A OK]` | Formato sin tocar el modelo |
| 4 | `load_ds02 stride 100` | Parte por motor | dev 52 635 filas, test 12 538 filas | El reparto honesto nace aquí |
| 5 | W y Xs de ajuste | Ajusta scaler y 14 ridges | 18 canales, 44 982 filas, medias `[21930.04, 0.62, 68.61, 475.01]` | Sin fuga desde el inicio |
| 6 | Prep congelado | Construye ventanas | dev `(17450, 50, 19)`, test `(6196, 50, 19)`, 93 tabulares | Doble lectura de la misma ventana |
| 7 | Sensores de ajuste | EDA de correlación e histograma | RUL medio 37.13 ciclos | Ojo humano antes del modelo |
| 8 | `X_tab` ajuste | Entrena LightGBM cuantil 0,35 | 0.27 s, RMSE 7.113 en esa ejecución | Base A lista |
| 9 | Media de train | Baseline y top rasgos | Baseline 38.08 ciclos y 20.022; top `[f21, f10, f11, f12, f0]` | El suelo contra el que todo compite |
| 10 | `X_seq` ajuste | Entrena BiLSTM triple pooling | 154 253 params, RMSE 5.839 en esa ejecución | Campeón listo |
| 11 | Todo NB01 | Guarda artefactos | `[NB1 OK]` en `artifacts/` | Puente hacia NB02 |

Las cifras de las celdas 8–10 son salida de esa ejecución, no resultado del bundle. El bundle vigente es ≈4.34 ± 0.10 con fila 4.251 ([[e00-cifras-autoritativas]]).

## Las 5 celdas que importan

1. Celda 4: el reparto por motor con sus `assert` de disjunción.
2. Celda 5: scaler con 44 982 filas y holdout aportando cero.
3. Celda 6: ventanas `(17450, 50, 19)` y `(6196, 50, 19)`.
4. Celda 9: baseline 20.022 que calibra la escala.
5. Celda 10: BiLSTM con 154 253 parámetros y su `summary`.

## Salidas que hay que saber leer

`dev X_seq (17450, 50, 19)` significa 17 450 ventanas de 50 pasos y 19 canales. `filas de ajuste 44982` confirma la defensa 1 de [[c03-fuga-de-informacion]].

`Baseline media train = 38.08` no es un modelo: es la constante que da 20.022. Todo modelo útil tiene que ganarle.

## Qué NO hace este cuaderno

No ablaciona, no elige `beta`, no combina y no calibra banda. Todo eso es NB02. NB01 termina con dos bases sueltas y artefactos guardados.

## Si falla algo

Si `load_ds02` no encuentra el HDF5, revisa `archive/CCMaps/N-CMAPSS_DS02-006.h5` y el `cwd` de la celda 1. Si el BiLSTM no recarga en NB02, el culpable suele ser `LastStepPooling` sin registrar ([[s06-bilstm-triple-pooling]]).

> [!quote] Di esto en el tribunal
> «En el primer cuaderno parto por motor, ajusto scaler y ridges solo con ajuste y construyo 17 450 ventanas dev y 6 196 test. Entreno LightGBM y BiLSTM sueltos y guardo artefactos para el segundo cuaderno.»

## Flashcards

> [!question]- ¿Qué imprime la celda 4?
> Motores dev y test con 52 635 y 12 538 filas, y 44 982 de ajuste.

> [!question]- ¿Qué imprime la celda 5?
> Scaler de 18 canales con 44 982 filas y 14 ridges.

> [!question]- ¿Qué formas salen de la celda 6?
> Dev `(17450, 50, 19)` y test `(6196, 50, 19)`, más 93 tabulares.

> [!question]- ¿Qué afirma esta nota en una frase?
> Este cuaderno deja el terreno listo: datos partidos por motor, preproceso sin fuga y dos bases entrenadas.

> [!question]- ¿Cómo la contarías en el tribunal?
> «En el primer cuaderno parto por motor, ajusto scaler y ridges solo con ajuste y construyo 17 450 ventanas dev y 6 196 test. Entreno LightGBM y BiLSTM sueltos y guardo artefactos para el segundo cuaderno.»

