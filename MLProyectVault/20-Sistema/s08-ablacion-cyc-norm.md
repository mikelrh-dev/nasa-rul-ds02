---
tipo: sistema
status: sin-estudiar
tags:
  - ablacion
  - cyc-norm
  - reloj
---

# Ablación cyc_norm — el contador de ciclos

> [!abstract] En una frase
> El ciclo acumulado ayuda, pero si se deja solo se convierte en un reloj que predice sin mirar sensores.

## Contrato

| Entra | Sale |
|---|---|
| Pipeline con y sin canal `cyc_norm` | Tabla comparativa por semilla y por rama |
| Importancias y coeficiente del reloj | Decisión de conservarlo acompañado, nunca solo |

## Cómo está implementado

La medición vive en `src/ds02_rul/pipeline.py:247` y se invoca sin reentrenar el bundle final.

| Condición (seed 42) | LightGBM | BiLSTM | Híbrido |
|---|---|---|---|
| Con `cyc_norm` | 7.113 | 5.419 | 5.386 |
| Sin `cyc_norm` | 6.297 | 6.513 | 6.477 |

Cifras de ablación ([[e00-cifras-autoritativas]]). El patrón es revelador: sin el contador, LightGBM mejora y el BiLSTM empeora. El contador ayuda a la secuencia y estorba al tabular si va solo.

El reloj desnudo es tramposo: OLS solo con reloj da 14.327 y la constante da ≈20.02. El coeficiente del reloj llega a −98.4065 con importancias `[0, 0, 720]`: el modelo deja de leer sensores y cuenta ciclos. El protocolo anterior daba 5.523 por este atajo.

## La decisión que hay detrás

ADR-008 conserva `cyc_norm` como canal 19 y como feature tabular, pero prohíbe usarlo solo. La ablación demuestra que el aporte es real en el híbrido (casi un ciclo de RMSE) sin convertirlo en reloj.

Se rechazó eliminarlo del todo: el BiLSTM lo necesita como ancla temporal dentro de la ventana de medio ciclo.

## Qué medimos

La tabla de arriba es salida de esa ejecución, no resultado del bundle. El resultado vigente sigue siendo ≈4.3 con fila 4.338 (bundle C, [[e00-cifras-autoritativas]]).

La lección es metodológica: medir, no afirmar. La ablación existe para que nadie diga «el ciclo no aporta» ni «el ciclo lo hace todo» sin números.

## El límite

> [!warning] Lo que la ablación no dice
> Mide una semilla y un protocolo concreto. Con otras semillas el ranking se mantiene pero los decimales se mueven en ±0.1 ([[c14-ruido-y-reproducibilidad]]). No conviertas 5.386 en cifra de defensa: es diagnóstico, no resultado.

## Di esto en el tribunal

> [!quote]
> «Ablacioné el contador de ciclos: con él el híbrido da 5.39 y sin él 6.48 en esa corrida. Solo con el reloj da 14.33, así que no es un reloj. Aporta, pero acompañado de sensores.»

## Flashcards

> [!question]- ¿Qué pasa sin cyc_norm en cada rama?
> LightGBM mejora (6.30 vs 7.11) y el BiLSTM empeora (6.51 vs 5.42).

> [!question]- ¿Cuánto da el reloj solo?
> OLS solo reloj 14.327; constante 20.022. No es competitivo.

> [!question]- ¿Qué significa importancias [0,0,720]?
> Que el modelo deja de leer sensores y cuenta ciclos.

> [!question]- ¿Se conserva o se quita cyc_norm?
> Se conserva acompañado: canal 19 y feature, nunca solo.

> [!question]- ¿Qué afirma esta nota en una frase?
> El ciclo acumulado ayuda, pero si se deja solo se convierte en un reloj que predice sin mirar sensores.

> [!question]- ¿Cómo la contarías en el tribunal?
> «Ablacioné el contador de ciclos: con él el híbrido da 5.39 y sin él 6.48 en esa corrida. Solo con el reloj da 14.33, así que no es un reloj. Aporta, pero acompañado de sensores.»

> [!question]- ¿Qué archivo respalda esta nota?
`src/ds02_rul/pipeline.py:247`

## Conexiones

Antes: [[s07-ema-por-motor]] · Después: [[s09-oof-y-beta]] · Mecanismo: [[c02-ventanas-y-horizonte]]
