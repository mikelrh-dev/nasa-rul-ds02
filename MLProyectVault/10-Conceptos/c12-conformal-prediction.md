---
tipo: concepto
status: sin-estudiar
tags:
  - conformal
  - cobertura
  - incertidumbre
  - banda
---

# Predicción conformal — cobertura y asimetría

> [!abstract] En una frase
> Una banda conformal garantiza cobertura marginal al nivel pedido, es decir, un porcentaje de aciertos promediado sobre la población de calibración, no una garantía por motor ni por tramo de vida.

## El problema que resuelve

Una predicción puntual no es desplegable por sí sola: el mantenimiento decide sobre un rango, no sobre un número. Tampoco sirve un intervalo inventado a partir de la desviación del residuo global, porque el error no tiene la misma escala en toda la vida del motor.

La banda resuelve dos cosas a la vez. Primero, da un rango con una propiedad medible: la fracción de verdades que caen dentro. Segundo, admite asimetría: el costo de sobreestimar RUL y el de subestimarlo no son iguales bajo la métrica de NASA, así que una banda simétrica gastaría la mitad de su ancho en el lado barato (`src/ds02_rul/conformal.py:4`).

## Cómo funciona

Es conformal partido (split conformal). Se reservan filas de calibración que el meta-aprendiz no vio, se calculan los residuos con signo y se toman sus cuantiles:

$$
r_i = y_i - \hat{y}_i \qquad
\text{banda} = \left[\hat{y} + q_{\alpha},\; \hat{y} + q_{1-\alpha}\right],
\quad \alpha = \frac{1 - \text{objetivo}}{2}
$$

Con objetivo 0,90, cada cola reserva 0,05 (`src/ds02_rul/conformal.py:49`). El residuo se define como verdad menos predicción, con signo (`src/ds02_rul/conformal.py:50`), de modo que un cuantil negativo baja la cota y uno positivo la sube.

La banda no es única para toda la predicción. Se calcula por tramos de RUL **predicha**, con cortes en 0, 25, 50 y 75 (`src/ds02_rul/conformal.py:18`). Cada tramo tiene sus propios cuantiles, así que el ancho puede crecer donde el error crece. Un tramo con menos de `min_rows` filas, 100 por defecto, cae a los cuantiles globales para no dibujar una banda con un puñado de puntos (`src/ds02_rul/conformal.py:29`).

Después se imponen dos guardas. Las cotas nunca cruzan la predicción puntual (`src/ds02_rul/conformal.py:107`), y la cota inferior se recorta en cero solo cuando la predicción es no negativa (`src/ds02_rul/conformal.py:112`). La cobertura se mide, no se asume: es la fracción de verdades entre cota y cota (`src/ds02_rul/conformal.py:116`).

La asimetría aparece en los extremos. En el tramo alto el modelo subestima de forma sistemática, así que los dos cuantiles del residuo son negativos. La cota inferior se aleja y la superior se pega al punto, porque el código prohíbe que una cota excluya a su propio centro (`src/ds02_rul/conformal.py:107`). Eso no es un defecto: es el sesgo del modelo, y la banda lo absorbe en lugar de disimularlo (`src/ds02_rul/conformal.py:36`).

## Dónde aparece en este proyecto

- El bundle expone `predict_interval`, que devuelve punto, cota inferior y cota superior; `predict` queda intacto (`src/ds02_rul/ensemble.py:161`).
- Resultado enviado: objetivo 90 %, cobertura realizada 100 %, ancho medio `26.41` ciclos, con 11 → `26.92`, 14 → `26.03`, 15 → `25.75` ([[e00-cifras-autoritativas]]).
- Calibración sobre `17450` ventanas fuera de fold de los seis motores de desarrollo (incluye la unidad 16: el meta la vio; `14915` es la banda de decisión sin la 16) ([[e00-cifras-autoritativas]]; `README.md:78`).
- La cota inferior alimenta la decisión de estado en [[s13-capa-de-reglas-y-decision]]; el detalle de la banda enviada está en [[s11-banda-conformal]].
- La nota de honestidad del README lo dice sin rodeos: es una cota conservadora, no un intervalo de grado de decisión (`README.md:80`).

## Qué alternativa se rechazó

| Alternativa | Por qué no |
|---|---|
| Banda simétrica alrededor del punto | Gasta la mitad del ancho en el lado barato de la penalización exponencial |
| Cuantiles globales, sin tramos | Aplica el mismo ancho a un motor con pocos ciclos de vida restantes y a uno con muchos; el error no se comporta igual en ambos extremos |
| Recalibrar en la unidad 16 para estrechar | Colapsa a ≈3.4 ciclos de ancho con **31.4 %** de cobertura: el meta se ajusta en esa unidad y ninguna fila suya supera los 62 ciclos, así que ningún cuantil suyo cubre vida alta |
| Banda de-sesgada (`debias=True`) como banda enviada | Mide dispersión en vez de absorber el sesgo; deja de cubrir justo donde el modelo se equivoca. Se conserva como diagnóstico (`src/ds02_rul/conformal.py:36`) |

> [!warning] La trampa
> 100 % de cobertura con objetivo 90 % no es una virtud: una banda infinita también cubriría todo. La lectura correcta es «cero verdades fuera, ancho 26.41, conservadora por construcción». Presentarla como precisión sería confundir una cota con una estimación.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «La banda garantiza cobertura marginal: un 90 % promediado sobre la población de calibración, no un 90 % para cada motor. Por eso publico la cobertura por motor y no solo la global. Y por eso digo que es una cota: se calibró con modelos de fold más débiles que el desplegado, cubre el 100 % y mide 26.41 ciclos de ancho. Estrecharla recalibrando en la unidad 16 la dejaría en 31.4 % de cobertura, que es peor que no tener banda.»

## Flashcards

> [!question]- Pregunta de repaso
> ¿Qué garantiza exactamente una banda conformal y qué no garantiza?
> Garantiza cobertura marginal: la fracción de verdades dentro de la banda, promediada sobre la distribución de calibración, tiende al nivel pedido. No garantiza cobertura condicional: no promete ese porcentaje para cada motor, cada tramo de RUL ni cada régimen.

> [!question]- Pregunta de repaso
> ¿Por qué los residuos se guardan con signo en lugar de usar su valor absoluto?
> Porque la banda es asimétrica. Un cuantil bajo y otro alto del residuo con signo permiten que la cota inferior y la superior se desplacen de forma independiente; con valores absolutos la banda sería forzosamente simétrica.

> [!question]- Pregunta de repaso
> ¿Qué significa que en el tramo alto las dos cotas queden por debajo del punto?
> Que el modelo subestima de forma sistemática en ese tramo: los dos cuantiles del residuo son negativos. La cota inferior se aleja y la superior se pega al punto por la guarda que impide que una cota excluya su centro. La banda se vuelve unilateral y eso refleja el sesgo real.

> [!question]- Pregunta de repaso
> ¿Por qué recalibrar en la unidad 16 arruina la cobertura?
> Porque el meta-aprendiz se ajusta en esa unidad y sus filas no superan los 62 ciclos. Los cuantiles aprendidos ahí son estrechos y no representan la vida alta, así que la banda deja fuera la mayoría de las verdades: 31.4 % de cobertura.

> [!question]- Pregunta de repaso
> ¿Cuál es la diferencia entre una cota y un intervalo de decisión?
> La cota es conservadora: se puede confiar en que la verdad no cae por debajo, a costa de un ancho grande. Un intervalo de decisión tendría que ser estrecho y cubrir de forma pareja; con 26.41 ciclos de ancho y cobertura 100 %, esta banda sirve para triage, no para prometer un valor.

## Conexiones

Antes: [[c11-shrinkage-beta]] · Después: [[c13-ema-causal]]
