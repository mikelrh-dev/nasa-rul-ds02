# Plan de presentación — 28 de núcleo + 14 de respaldo

**Objetivo:** 20 minutos, con 18:37 de guion y ~83 s de colchón.
**Regla:** una idea por slide; el número protagonista va en pantalla, la explicación en la nota del orador.

- Deck: `docs/presentacion/index.html` (42 secciones: 1–28 núcleo, 29–42 respaldo).
- Guion: `docs/defensa/notas-orador.md`.
- Modo presentador: `N` notas · `O` mapa · `T` tiempo · `R` reset · `?` ayuda.

## Antes de empezar

- [ ] Abrir el deck en Chrome a 1920×1080 y comprobar que no hay scroll.
- [ ] `N` y revisar que la nota 1 carga; `O` y comprobar que el mapa tiene 39 tarjetas.
- [ ] `T` para arrancar el cronómetro; `R` para reiniciarlo si hace falta.
- [ ] Tener a mano `docs/defensa/notas-orador.md` y `docs/defensa/mapa-rubrica.md`.
- [ ] No abrir las slides 29–42 salvo que pregunten.

## Acto I · Negocio (165 s)

| # | Slide | Idea | Tiempo | Frase |
|---|---|---|---:|---|
| 1 | Portada | De la predicción a la acción | 15 s | «Predigo la RUL y la convierto en APTO, INSPECCIÓN o HANGAR con reglas auditables.» |
| 2 | Una hora en pista cuesta 10–15k | El coste justifica el sistema | 30 s | «10–15k por hora es rango Boeing de credibilidad Media, sin documento versionado: supuesto. 4,338 ciclos es el 21,7 % del umbral de hangar; el sistema se paga con una parada evitada al año.» |
| 3 | 9 motores, 65.173 lecturas | Escala, split y horizonte real | 40 s | «Una de cada 100 muestras; ≈113 lecturas por ciclo, así que una ventana de 50 cubre 0,44 vuelos.» |
| 4 | El modelo propone; las reglas deciden | IA débil, supervisada, con reglas | 40 s | «El modelo propone, ocho reglas deciden, n8n ejecuta; si falta evidencia, no se decide.» |
| 5 | Equivocarse tarde cuesta más | Por qué `L_inf` | 40 s | «El RMSE cobra igual los dos errores; el negocio no. Y en una flota real el error optimista es seguridad, no dinero.» |

**Transición:** «Si el error caro solo tiene una dirección, lo primero es entender el dato.»

## Acto II · Datos (192 s)

| # | Slide | Idea | Tiempo | Frase |
|---|---|---|---:|---|
| 6 | Separador | Datos | 12 s | «1.185 huecos que tienen causa física.» |
| 7 | 22 columnas en tres grupos | 14 sensores, 4 régimen, 4 contexto | 35 s | «El régimen y el desgaste viajan juntos.» |
| 8 | 1.185 huecos con causa física | MAR, no ruido | 45 s | «Todos en T30, MAR con patrón de crucero alto; ffill causal por unidad.» |
| 9 | Cinco gráficos, cinco lecturas | EDA | 45 s | «El crucero domina, la cola manda, T48 cruda separa fases.» |
| 10 | El régimen no es salud | Residualización | 55 s | «Catorce Ridge separan régimen y desgaste; solo miran los motores de ajuste.» |

**Transición:** «Con el régimen restado, ya se puede modelar. Y aquí empieza la escalera.»

## Acto III · Modelos (545 s)

| # | Slide | Idea | Tiempo | Frase |
|---|---|---|---:|---|
| 11 | Separador | Modelos | 10 s | «De una fila a una secuencia: seis peldaños.» |
| 12 | La escalera | 11,034 → 4,338 | 40 s | «Los dos primeros son de fila; los cuatro siguientes, de ventana.» |
| 13 | XGB gana por 0,06 ciclos | 5 clásicos, 45 ajustes | 60 s | «45 ajustes en tres pliegues por motor, nunca por fila: XGB 8,217; el lineal se queda a 0,06 y es el que menos empeora. A igualdad, el más simple.» |
| 14 | E1 memoriza; E2 gana | 4 experimentos MLP | 55 s | «E1 baja train y sube validación; E2 gana por 0,018, que es un margen.» |
| 15 | Una fila se queda en 7,72 | Techo de fila | 40 s | «Una lectura no ve degradación; 11,034 y 4,338 no se comparan.» |
| 16 | Una fila no basta: tres contratos | Tres contratos | 50 s | «La red lee la secuencia cruda; el árbol, el residuo.» |
| 17 | El reloj no ayuda en ventana | Ablación y contrato | 45 s | «En el secuencial no cambia nada; en el árbol cuesta 0,77. Vive en las dos ramas base y sale del meta.» |
| 18 | OOF + meta + β | Validación honesta | 85 s | «Sin OOF la validación se vuelve 0,308, que es imposible. El meta promedia Ridge y LGBM y la final es p + β·(meta − p): con β = 1,00 manda el meta.» |
| 19 | 4,333 ± 0,040, y U14 | Semillas y reparto | 50 s | «U14 es el 12 % de las ventanas y el 47,9 % del error: RUL larga y 20,6 lecturas por ciclo.» |
| 20 | SHAP: manda el ciclo | Explicabilidad | 55 s | «El 71 % del peso del meta es del árbol; las dos ramas miran cyc_norm y T50.» |
| 21 | 4,338 y qué significa | Métricas y glosas | 55 s | «4,338 son unos 4,3 vuelos; NASA es una suma asimétrica que crece con las ventanas.» |

**Transición:** «El modelo ya da un número y una banda. Ahora, la decisión.»

## Acto IV · Decisión (175 s)

| # | Slide | Idea | Tiempo | Frase |
|---|---|---|---:|---|
| 22 | Separador | Decisión | 10 s | «El modelo no decide; las reglas deciden y se pueden auditar.» |
| 23 | Ocho reglas, una de seguridad | Reglas y prioridad | 45 s | «R1 es seguridad: sin evidencia no hay APTO.» |
| 24 | L_inf = 19: HANGAR | Pesimista | 45 s | «Decidimos sobre 19, no sobre 27; la banda cubre 6.196 de 6.196 con ancho 25,3 y sobre-cubre porque la calibraron modelos más débiles.» |
| 25 | La decisión se convierte en acción | n8n | 40 s | «20 nodos y 4 ramas; HANGAR escribe en Postgres y el FALLBACK alerta.» |
| 26 | El caso nuevo (y el caso malo) | App | 35 s | «El caso malo no rompe: no decide.» |

**Transición:** «Y esto es lo que el sistema no hace.»

## Acto V · Cierre (40 s)

| # | Slide | Idea | Tiempo | Frase |
|---|---|---|---:|---|
| 27 | Lo que este sistema no hace | Límites y dos campeones | 35 s | «E2 es el campeón de clase; C, el de producción.» |
| 28 | Preguntas | Cierre | 5 s | «El detalle está en las slides de respaldo.» |

## Respaldo (no se presenta)

| # | Slide | Para qué |
|---|---|---|
| 29 | Los siete cuadernos | Mapa de evidencia 01–07 |
| 30 | Qué mide cada columna | Glosario de sensores |
| 31 | Los tres contratos, con detalle | 22 columnas con one-hot, 19 canales crudos + reloj, 93 features residualizadas |
| 32 | Diagnóstico del residuo | Sesgo, 58,8 %, 4,3 %, coste |
| 33 | Rúbrica → evidencia | Rutas reales por criterio |
| 34 | Glosario de métricas | RMSE, MAE, R², NASA, OOF, conformal, SHAP, EMA5 |
| 35 | MLflow: 17 runs curados | Compare fila/ventana y run de producción |
| 36 | n8n: lo que se ejecutó | 29 ejecuciones, 25/4, efectos reales |
| 37 | Preguntas frecuentes | Respuestas cortas SAA/PIA/MIA |
| 38 | Qué mira el MLP E2 | Permutación: cycle 28, T50 20,5 |
| 39 | Del HDF5 al parquet | Columnar y tipado; 8,2 MB / 55 ms frente a 2,45 GB / 2,4 s |
| 40 | El BiLSTM: 50 pasos a un número | 2 × BiLSTM(64) bidireccional, triple pooling, 154.253 parámetros |
| 41 | LightGBM: 300 árboles al cuantil 0,35 | Boosting, 15 hojas, cuantil 0,35, 93 features |
| 42 | La banda, paso a paso | Conformal por tramos, 5 % por lado, cubre 6.196/6.196 |

## Transiciones literales

1. «Si el error caro solo tiene una dirección, lo primero es entender el dato.»
2. «Con el régimen restado, ya se puede modelar. Y aquí empieza la escalera.»
3. «El modelo ya da un número y una banda. Ahora, la decisión.»
4. «Y esto es lo que el sistema no hace.»

## Reglas de lenguaje

- Titular = afirmación; subtítulo = número.
- Una idea y un número protagonista por slide.
- Glosa la jerga la primera vez: OOF, NASA, EMA5, conformal.
- Notas habladas en 2–3 frases cortas, no en una frase de 70 palabras.
- Voz activa y «nosotros»: elegimos, medimos, descartamos.
- No leas tablas; señala la fila y di qué significa.

## Si hay que bajar a 15 minutos

Recorta en este orden: 9 y 10 en una pasada de 50 s; 13 a tres frases; 16 sin el diagrama; 17 y 18 juntas; 19 sin la tabla por motor. No quites 5, 12, 24 ni 27.

## Si hay que subir a 25 minutos

Abre 31 (contratos), 32 (residuo) y 35 (MLflow) como slides normales. No añadas tablas nuevas: usa las de respaldo.
