---
title: NB01 · Dataset y tabla de campos
course: Reto 1 · SAA+PIA+MIA
block: 01 — NB01 EDA
node: B1.1
indicador: SAA-3
descriptor: 10
spine: false
status: en-curso
tags:
  - nb01
  - dataset
  - rubrica/saa-3
---

# NB01 · Dataset y tabla de campos

> [!abstract] En una frase
> El dataset no se describe por tamaño, se describe por **qué columna es la verdad, cuál es el
> reloj y qué campo se cae**. Con eso el tribunal sabe que entendiste los datos y no solo los
> cargaste.

## Qué digo

«Es N-CMAPSS DS02: telemetría de vuelo por ciclo de 9 unidades de un mismo tipo de motor. Cada
fila es un instante de un vuelo; el objetivo es el RUL, los ciclos que le quedan al motor. El
reloj es `cycle`; la unidad es `unit`. La tabla tiene 18 canales de sensor, más altitud, Mach y
las condiciones operativas. Ninguna fila es independiente de la anterior: por eso todo split se
hace por motor.»

## La tabla de campos (SAA-3 → 10)

| Campo | Qué significa | Tipo | % nulos |
|---|---|---|---|
| `unit` | Motor (unidad de la flota) | entero | 0 |
| `cycle` | Ciclo de vida acumulado: el reloj | entero | 0 |
| `RUL` | Vida útil restante, la variable objetivo | entero | 0 |
| `alt` | Altitud | real | 0 |
| `Mach` | Número de Mach | real | 0 |
| `TRA` | Acelerador (throttle) | real | 0 |
| `T2` | Temperatura de entrada | real | 0 |
| `T24`, `T30`, `T48`, `T50` | Temperaturas de etapas del compresor/turbina | real | **T30 ≈ 2 %** |
| `P2`, `P15`, `P30`, `Ps30` | Presiones | real | 0 |
| `Nf`, `Nc` | Velocidades de los ejes | real | 0 |
| `phi`, `NRf`, `NRc`, `BPR`, `farB` | Ratios de flujo y combustible | real | 0 |
| `htBleed`, `W31`, `W32` | Sangrado y caudales | real | 0 |
| `fase_vuelo` | Variable nueva: despegue/crucero/descenso | categórica | 0 |

**Campos que se quitan y por qué** (esto es lo que separa un 7 de un 10): no se elimina ningún
sensor por completo; se elimina `T30` **como entrada fiable** cuando falta, y se reconstruye con
la mediana de las unidades de ajuste más `ffill` causal. Los identificadores de vuelo no entran
al modelo porque no generalizan a un motor nuevo.

## Por qué se dice así

- Un 7 es «tabla con nombre, qué significa y tipo». El 10 añade **nulos por campo** y **qué
  quitas y por qué**. Por eso la tabla lleva la columna de nulos aunque casi todo sea 0.
- Decir «T30 falta en el 2 %» prepara el terreno para el MAR de [[12-nb01-nulos-mar-y-variable-nueva]]:
  no es un dato sucio, es un sensor que se cae en una condición de vuelo concreta.

## Evidencia

- Notebook: `notebooks/01_eda_y_contexto.ipynb` (carga, auditoría y formas).
- Definición de sensores y fase: `src/clase/dataset_clase.py` (`SENSOR_COLS`, `asignar_fase_vuelo`).
- Conteos: `17450` ventanas dev / `6196` test; `52635` / `12538` filas.
- Tabla también en `README.md` («Los datos»).

## Pregunta probable

**«¿Por qué 9 unidades y no más?»**
→ «Porque DS02 trae 9 motores y el reparto es por motor, no por fila: 5 para ajuste, 1 de
holdout para el meta y 3 de test. Con 9 unidades el mensaje honesto es que la varianza entre
motores es alta; por eso publico el macro-RMSE y no solo el global.»

## Lo que NO digo

- No digo «el dataset tiene N filas» como si fuera un logro: el tamaño no es la virtud.
- No digo que `unit` o `cycle` son features del modelo secuencial sin matizar: `cycle` sí entra
  como contexto, `unit` nunca (sería memorizar el motor).

## Di esto en el tribunal

> «La verdad es `RUL`, el reloj es `cycle` y la unidad es `unit`; como las filas de un motor
> están correladas, ningún split se hace por fila.»

## Flashcards #flashcards

- ¿Qué tres columnas estructuran el dataset? :: `unit` (motor), `cycle` (reloj) y `RUL` (objetivo).
- ¿Qué campo tiene nulos y por qué? :: `T30`, ≈2 %, porque el sensor se cae en crucero alto (MAR).
