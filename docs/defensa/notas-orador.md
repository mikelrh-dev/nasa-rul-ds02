# Notas de orador — 28 slides de núcleo + 10 de respaldo, 20 minutos

Presupuesto: 1.200 s. Las frases de abajo suman **1.117 s = 18 min 37 s**, así que quedan ~83 s para transiciones y preguntas. Una frase por slide: si se dice la frase, la slide está cubierta; el resto es decoración que el tribunal ya lee.

Las slides 1–28 se presentan. Las 29–38 son **respaldo**: no se abren salvo que pregunten.

Reglas: no leer tablas en voz alta; no repetir el número que ya está en pantalla; tres remates en todo el deck, no quince.

Atajos del deck: `N` notas · `O` mapa · `T` tiempo · `R` reset · `?` ayuda.

## Acto I · Negocio (165 s)

| # | Slide | Frase de apertura | s | Qué no decir |
|---|---|---|---:|---|
| 1 | Portada | «Predigo la RUL de la flota y la convierto en APTO, INSPECCIÓN o HANGAR con reglas auditables.» | 15 | No abras con el modelo ni con el RMSE. |
| 2 | Una hora en pista cuesta 10–15k | «Una hora de AOG cuesta 10–15k; 4,338 ciclos es el 21,7 % del umbral de hangar. El sistema se paga si cuesta menos que una parada evitada al año.» | 30 | No prometas ahorro medido: el coste es supuesto. |
| 3 | 9 motores, 65.173 lecturas | «Nueve motores simulados, 65.173 lecturas, 22 columnas y una etiqueta; el split es por motor y ningún motor cae en los dos lados.» | 40 | No lo vendas como flota real ni nombres fabricantes. |
| 4 | El modelo propone; las reglas deciden | «El modelo propone, ocho reglas deciden, n8n ejecuta; si falta evidencia, no se decide.» | 40 | No digas «IA fuerte» ni «generaliza». |
| 5 | Equivocarse tarde cuesta más | «Tarde cuesta 10–15k por hora; pronto, horas de taller. El RMSE cobra igual los dos, por eso decidimos con la banda inferior.» | 40 | No digas que el sistema evita el AOG: dice cuándo mirar. |

## Acto II · Datos (192 s)

| # | Slide | Frase de apertura | s | Qué no decir |
|---|---|---|---:|---|
| 6 | Separador | «1.185 huecos que tienen causa física.» | 12 | — |
| 7 | 22 columnas en tres grupos | «14 sensores, 4 de régimen y 4 de contexto; el régimen y el desgaste viajan juntos.» | 35 | No leas el glosario entero. |
| 8 | 1.185 huecos con causa física | «1.185 nulos, todos en T30, MAR con patrón de crucero alto; ffill causal por unidad.» | 45 | No digas que los nulos son ruido ni que se inyectaron. |
| 9 | Cinco gráficos, cinco lecturas | «El crucero domina, la cola manda, T48 cruda separa fases y en el árbol el régimen se resta.» | 45 | No enumeres los cinco títulos. |
| 10 | El régimen no es salud | «Un motor se calienta porque se rompe o porque sube: catorce Ridge separan las dos cosas y solo miran los motores de ajuste. El Ridge alimenta al árbol; la red lee 18 canales crudos + reloj.» | 55 | No digas que la red usa los residuos ni confundas este Ridge con el del baseline o el meta. |

## Acto III · Modelos (545 s)

| # | Slide | Frase de apertura | s | Qué no decir |
|---|---|---|---:|---|
| 11 | Separador | «De una fila a una secuencia: seis peldaños.» | 10 | — |
| 12 | La escalera | «Seis peldaños: XGB 11,034, MLP 7,721, LGBM 7,067, BiLSTM 5,654, EMA 5,618, híbrido 4,338. Los dos primeros son de fila; los cuatro siguientes, de ventana.» | 40 | No compares 11,034 con 4,338: distinto grano. |
| 13 | XGB gana por 0,06 ciclos | «45 ajustes y tres pliegues por motor. XGB gana con 8,217; el lineal se queda a 0,06 y es el que menos se mueve al generalizar. A igualdad, gana el más simple.» | 60 | No digas que el lineal es el mejor: es el que menos empeora. |
| 14 | E1 memoriza; E2 gana | «E1 sube capacidad y memoriza: train 5,229, validación 7,481. E2 regulariza y gana: 7,340 en validación y 7,721 en test.» | 55 | No mezcles E1 y E2 ni llames fracaso a E1. |
| 15 | Una fila se queda en 7,72 | «Una lectura no ve degradación; por eso 11,034 y 4,338 no se comparan. Se mide con RMSE porque penaliza la cola; MAPE explota cuando la RUL tiende a cero.» | 40 | No presentes el 11,03 como «el modelo malo». |
| 16 | Una fila no basta: tres contratos | «Tres entradas: 22 columnas con one-hot, 19 canales crudos + reloj y 93 features residualizadas. La red no usa el Ridge; el árbol sí.» | 50 | No mezcles la ventana de 19 con la de 93 ni digas que la red usa los residuos. |
| 17 | El reloj no ayuda en ventana | «El reloj no cambia el secuencial, 5,878–5,974, y cuesta +0,77 en LGBM. Se queda en el contrato del BiLSTM; no entra en LGBM ni en el meta.» | 45 | No digas que la ablación «demuestra» que el reloj sobra: dice que no aporta. |
| 18 | OOF + meta + β | «Tres pliegues por motor; sin OOF la validación se hunde a 0,308. El meta es Ridge α = 88,6 + LGBM 50/50 y solo ve dos columnas. β = 1,00; el meta rechazado subía de 4,04 a 10,17.» | 85 | No mezcles la corrida OOF con la del bundle ni digas que β se eligió a ojo. |
| 19 | 4,333 ± 0,040, y U14 | «4,333 ± 0,040 en tres semillas; U14 es el 12 % de las ventanas y el 47,9 % del error. Global 4,338, macro 5,015; la tabla es semilla 42.» | 50 | No cites 4,324 ± 0,107 ni mezcles la tabla de una semilla con la media. |
| 20 | SHAP: manda el ciclo | «El 71 % del peso del meta es del árbol; las dos ramas miran cyc_norm y T50. SHAP describe el modelo, no el motor.» | 55 | No vendas la coincidencia 28/72 como validación ni hables de causas. |
| 21 | 4,338 y qué significa | «RMSE 4,338, MAE 3,227, R² 0,9461, NASA 2336,2. NASA es una suma asimétrica; EMA5 es media móvil causal span 5. El test se leyó una vez.» | 55 | No compares NASA entre modelos con distinto número de filas. |

## Acto IV · Decisión (175 s)

| # | Slide | Frase de apertura | s | Qué no decir |
|---|---|---|---:|---|
| 22 | Separador | «El modelo no decide; las reglas deciden y se pueden auditar.» | 10 | — |
| 23 | Ocho reglas, una de seguridad | «Ocho reglas con prioridad; R1 es seguridad y sin evidencia no hay APTO. Umbrales 20 y 25.» | 45 | No digas que las reglas «mejoran» el RMSE. |
| 24 | L_inf = 19: HANGAR | «Decidimos sobre L_inf = 19, no sobre 27. La banda es nominal 90 %, empírica 99,7 % y ancho 25,9: conservadora a propósito.» | 45 | No digas que la banda es estrecha ni que es decorativa. |
| 25 | La decisión se convierte en acción | «20 nodos y 4 ramas; HANGAR escribe en Postgres y el FALLBACK alerta. La instancia local lo ejecutó 29 veces: 25 success y 4 error.» | 40 | No digas que el flujo llama a nuestra API: no hay nodo HTTP. |
| 26 | El caso nuevo (y el caso malo) | «La app enseña p, banda, motivo, SHA y SHAP local; el caso malo no rompe, no decide.» | 35 | No hagas la demo sin red: si falla, usa la captura. |

## Acto V · Cierre (40 s)

| # | Slide | Frase de apertura | s | Qué no decir |
|---|---|---|---:|---|
| 27 | Lo que este sistema no hace | «Seis límites declarados; dos campeones: E2 7,721 en clase y C 4,338 en producción.» | 35 | No los llames «trabajo futuro»; son límites. |
| 28 | Preguntas | «Fin. El detalle está en las slides de respaldo.» | 5 | No abras el respaldo salvo que pregunten. |

## Respaldo (no se presenta)

| # | Slide | Para qué está | s |
|---|---|---|---:|
| 29 | Los siete cuadernos | Mapa de evidencia de los cuadernos 01–07. | 0 |
| 30 | Qué mide cada columna | Glosario completo de sensores. | 0 |
| 31 | Los tres contratos, con detalle | 22 columnas con one-hot, 19 canales crudos + reloj y 93 features residualizadas. El Ridge solo alimenta al árbol. | 0 |
| 32 | Diagnóstico del residuo | Sesgo +0,369, 58,8 % se pasa, 4,3 % falla >10 ciclos. | 0 |
| 33 | Rúbrica → evidencia | Cada celda con su ruta real. | 0 |
| 34 | Glosario de métricas | RMSE, MAE, R², NASA, GroupKFold, OOF, stacking, conformal, SHAP, EMA5. | 0 |
| 35 | MLflow: 17 runs curados | Compare de fila, compare de ventana y run de producción. | 0 |
| 36 | n8n: lo que se ejecutó | 29 ejecuciones, 25/4, efectos reales. | 0 |
| 37 | Preguntas frecuentes | Respuestas cortas de SAA, PIA y MIA. | 0 |
| 38 | Qué mira el MLP E2 | Permutación: cycle 28, T50 20,5; la fase casi no entra. | 0 |

## Suma

165 + 192 + 545 + 175 + 40 = **1.117 s = 18 min 37 s**. Quedan 83 s de colchón.

## Si hay que bajar a 15 minutos

Orden de recorte: 9 y 10 en una pasada de 50 s; 13 a tres frases; 16 sin el diagrama;
17 y 18 juntas (OOF justifica β); 19 sin la tabla por motor. Nunca quitar 5, 12, 24 ni 27.
