# Plan de la presentación — DS02 · De la predicción a la acción

> v2 · Plan cerrado a nivel de slide, con **el output real que va en cada una**.
> Framework: `frontend-slides` (ya copiada a `.agents/skills/frontend-slides`).
> Plantilla elegida: **Cobalt Grid** (bold-template-pack). Deck generado en
> `docs/presentacion/index.html`.
>
> Arco narrativo: **dinero → dato → modelo → regla → acción**.
> Densidad: **alta / reading-first** (es una defensa con tribunal: las slides
> tienen que sostenerse solas, con tablas y figuras reales).

## Por qué Cobalt Grid

| Criterio | Cobalt Grid | Alternativas descartadas |
|---|---|---|
| Ocasión | Defensa académica: papel crema, tinta cobalto, alta formalidad | Raw Grid (media-baja), Studio (dark, loud) |
| Densidad | **medium-high** — el índice y el ledger son nativos de la plantilla | Cartesian / Vellum (low: no aguantan 5 tablas) |
| Lienzo | papel `#F0EBDE` + cobalto `#1F2BE0` + retícula permanente | Signal (navy: las capturas oscuras competían con el fondo) |
| Coherencia con el material | las figuras de matplotlib, fundidas con el papel, se leen como láminas impresas | las plantillas oscuras obligan a recortar cada captura |
| Tipografía | Newsreader (voz) + Hanken Grotesk (sustancia) + DM Mono (cifras, SHA, rutas) | evita el "AI slop" de Inter/Space Grotesk |

Lo que hace Cobalt Grid por nosotros: **dos tintas y una retícula**, así que
cinco tablas seguidas se leen como el mismo documento impreso y el único
acento posible son las cifras. El cobalto marca titulares y reglas; el mono
resuelve la trazabilidad que este proyecto presume: `d6c70142…`,
`src/mia/reglas.py`, `rmse_val`.

**24 slides** (21 de contenido + 3 separadores), 1920×1080 fijo, un solo HTML.

---

## Acto I · Negocio — por qué existe esto

### 1 · Portada
- **Layout:** navy a sangre, filete superior con kicker mono, titular serif en dos líneas, `acción` en itálica oro.
- **Kicker:** `IABD · RETO 1 · SAA + PIA + MIA · 12 NOV 2026`
- **Titular:** «De la predicción a la *acción*»
- **Subtítulo:** RUL y decisión de hangar en una flota DS02.
- **Cifras de chrome (mono, abajo):** `65.173 LECTURAS` · `9 MOTORES` · `RMSE 4.338` · `SHA d6c70142`
- **Fondo:** `docs/assets/dashboard_ds02.png` al 22 % de opacidad, alineado a la derecha — se intuye la app real, no se enseña todavía.
- **Rúbrica:** README §1 (título + una frase).

### 2 · El problema: una parada no planificada
- **Layout:** 60/40. Izquierda, cifra gigante en oro; derecha, tres líneas y una tabla de 3 filas.
- **La cifra:** `10.000 – 15.000` `USD / hora` (AOG, rango Boeing, credibilidad Media).
- **Texto:** «Hoy el jefe de taller decide con experiencia y sin número.»
- **Tabla real (del README §Coste del error):**

  | Concepto | Valor |
  |---|---:|
  | Coste AOG | 10.000–15.000 USD/h |
  | Horas por ciclo | 1–2 h (supuesto) |
  | Coste por ciclo de error | 10.000–30.000 USD |
  | RMSE del bundle C | **4,338 ciclos** = 17 % del umbral de hangar |

- **Lo que hay que decir:** «evitar una sola parada al año paga el sistema».
- **Rúbrica:** **MIA-1 (10)** — dato + qué mejora supondría.

### 3 · El sistema, y por qué es una IA débil
- **Layout:** cadena horizontal de 5 nodos con filetes finos; debajo, dos tarjetas de contraste.
- **Cadena:** `telemetría → RUL (p) → 8 reglas → APTO/INSPECCIÓN/HANGAR → webhook → acción`
- **Tarjeta A — IA débil:** predice RUL de DS02 con lo aprendido de *su* telemetría; no transfiere a otro motor ni dominio. **Contraste exigido por el 10:** una IA fuerte generalizaría el concepto de degradación; aquí hay una función ajustada a 9 motores.
- **Tarjeta B — aprendizaje:** supervisado de **regresión** (RUL continua, etiqueta real, métrica contra verdad). **Contraste:** el no supervisado agruparía regímenes sin saber cuántos ciclos quedan.
- **Rúbrica:** SAA-1 (5 %), SAA-2 (10 %).

### ▸ Separador A — «Datos»
Filete oro, la palabra `DATOS` en serif enorme, una línea: «65.173 lecturas de 9 motores, y 1.185 huecos que no son ruido.»

---

## Acto II · Datos

### 5 · Qué mide cada columna
- **Layout:** glosario de las 22 columnas en cuatro familias físicas, dos columnas de tabla y una franja de identificadores.
- **Por qué está aquí:** el SHAP y la residualización hablan de sensores por su nombre; sin esto no se pueden leer. Antes la tabla listaba 7 campos y de los 14 sensores solo nombraba dos.
- **Temperaturas (°R):** `T2` entrada del fan (va con el régimen) · `T24` salida LPC · `T30` salida HPC (**la única con nulos**) · `T48` salida HPT (la que separa régimen) · `T50` salida LPT (2.ª del SHAP del árbol).
- **Presiones (psia):** `P2` entrada fan · `P15` sangrado · `P21` salida LPC · `P24` salida HPC · `Ps30` estática HPC · `P40` total HPT · `P50` total LPT.
- **Rotacionales:** `Nf` fan · `Nc` núcleo · `Wf` caudal de combustible.
- **Régimen (no es desgaste):** `alt` 10.001–35.029 ft · `Mach` 0,327–0,742 · `TRA` palanca.
- **Franja inferior:** `unit` (grupo del split, no predictor) · `cycle` · `fase_vuelo` (one-hot) · `RUL` (objetivo).
- **Frase:** «el régimen y el desgaste viajan en las mismas columnas; el trabajo es separarlos».
- **Rúbrica:** PIA-1, SAA-4.
- **Layout:** tabla grande a la izquierda, tres cifras de contexto a la derecha.
- **Cifras:** `65.173` filas (STRIDE 100) · `9` motores · `18` canales + `RUL`.
- **Tabla real (recortada a 7 filas de las 20 del README):**

  | Campo | Qué significa | Tipo | Nulos antes → después |
  |---|---|---|---|
  | `unit` | Motor (grupo, no predictor) | numérica | 0 % → 0 % |
  | `cycle` | Ciclo de vuelo | numérica | 0 % → 0 % |
  | `alt, Mach, TRA, T2` | Régimen de vuelo | numéricas | 0 % → 0 % |
  | `T30` | Temp. salida HPC (°R) | numérica | **~1,8 % MAR** → 0 % |
  | `T48` | Temp. salida HPT (°R) | numérica | 0 % → 0 % |
  | `fase_vuelo` | Ascenso/Crucero/Descenso (nueva) | categórica | 0 % → 0 % |
  | `RUL` | **Objetivo:** ciclos restantes | numérica | 0 % (nunca se inyecta) |

- **Columna "qué campos quitas y por qué" (exigida por el 10):** `unit` (grupo del split; usarlo sería fuga), `RUL` (es el objetivo), `split_origen` (trazabilidad), `fase_vuelo` (el bundle C está residualizado sin categórica).
- **Rúbrica:** SAA-3 (5 %).

### 6 · Calidad y nulos: 1.185 huecos con causa física
- **Layout:** tres bloques — duplicados / imposibles / nulos — y una banda inferior con el split.
- **Duplicados:** 0 funcionales.
- **Imposibles:** Mach ∈ [0,33; 0,74], alt ∈ [10k, 35k]; el 30k/0,8 teórico **no existe** en DS02 (0 filas).
- **Nulos:** `1.185` en `T30`, **MAR con patrón físico** — dropout de sonda en crucero alto. **No al azar.**
- **Imputación derivada del patrón (el porqué):** `ffill` causal por unidad + mediana de train solo para el primer NaN.
- **Banda del split:** train `52.635` (uds 2/5/10/18/20/16) · test `12.538` (uds 11/14/15) · **una sola lectura del test** · split **por motor, nunca por fila**.
- **Variables nuevas:** `fase_vuelo` (de `alt`/`Mach`) y `cyc_norm = cycle/100`.
- **Rúbrica:** SAA-5 (5 %), SAA-4.

### 7 · Cinco gráficos, cinco lecturas
- **Layout:** galería única: tres figuras arriba y dos abajo con el panel de variables nuevas.
- **Antes eran dos slides** («Lo que dicen los datos» y «Dónde se esconde la información»); se fundieron para que el acto de datos quepa.
- **Los cinco exigidos, cada uno con lectura:** barras por fase → el crucero domina · histograma de RUL → la cola manda · boxplot de T48 por fase → crudo separa fases · dispersión alt-Mach → el régimen es una nube estructurada · heatmap → 18 canales no aportan 18 veces.
- **Panel:** `fase_vuelo` y `cyc_norm = cycle/100`, las dos variables que no venían.
- **Rúbrica:** SAA-4 (EDA), PIA-2.

### 8 · El régimen no es salud (residualización)
- **Layout:** cuatro bloques a la izquierda; a la derecha, el antes y el después de la misma figura.
- **La idea física:** un motor se calienta porque se rompe **o** porque el avión sube a tope. Si no se separan las dos cosas, el modelo aprende pilotaje.
- **Qué se resta:** un Ridge **por sensor (14)** sobre un polinomio de grado 2 en `alt · Mach · TRA · T2`. Lo que sobra es el residuo: la degradación.
- **Con qué se ajusta:** solo con los fit-units `2·5·10·18·20`. Es la línea de la que cuelga todo lo demás; ningún otro motor participa.
- **Qué sale:** 19 canales escalados (red) y 93 features de resumen (árbol). El mismo residuo, dos vistas.
- **Figuras (el argumento entero):** `eda_box_t48_fase.png` (antes: la fase separa las cajas) frente a `eda_t48_resid_fase.png` (después: se solapan).
- **Frase:** «si el residuo todavía separara fases, todo lo que viene después aprendería a volar, no a envejecer».
- **No confundir (pregunta típica):** hay tres Ridges en el proyecto — el de 14 sensores (física, aquí), el de una fila (baseline de 02) y el `ridge_meta` (mezcla dos predicciones, 04/06).
- **Rúbrica:** SAA-4/SAA-5 (feature engineering), PIA-3 (pipeline).

### ▸ Separador B — «Modelos»
«Cinco clásicos, cuatro MLP, una ablación y un ensemble que no se conforma con la media.»

---

## Acto III · Modelos

### 10 · Siete cuadernos, una decisión (recorrido)
- **Layout:** tabla de 7 filas: cuaderno · qué pregunta resuelve · qué deja.
- **Por qué existe:** en la defensa se pregunta «¿dónde está esto?». Esta slide es el mapa para no buscar en vivo.

  | Cuaderno | Pregunta | Deja |
  |---|---|---|
  | 01 · EDA | nulos MAR, fase, residualización | 6 figuras + auditoría |
  | 02 · Clásicos y MLP | ¿cuánto da una fila? | XGB 8,22 val |
  | 03 · Ablación | ¿el reloj ayuda? | OFF 6,297 · ON 7,067 |
  | 04 · OOF y meta | β, stacking, banda | **β = 1,00** |
  | 05 · Semillas | ¿fue suerte? | 4,324 ± 0,107 |
  | 06 · Bundle C | entreno oficial y cierre | 4,338 · SHA |
  | 07 · SHAP | las tres ramas | `cyc_norm` domina |

- **Frase:** cada cuaderno responde una pregunta y deja un artefacto; **ninguno entrena el bundle** — eso lo hace `src/ds02_rul/bundle_c.py` y lo firma el manifiesto.
- **Rúbrica:** PIA-1/PIA-4 (trazabilidad), y prepara las preguntas individuales.

### 11 · Un pipeline, cinco modelos
- **Layout:** tabla de 5 filas + dos notas al margen.
- **Tabla real (`resultados/comparativa.csv`):**

  | Modelo | Mejores params | RMSE train | RMSE val | Tiempo |
  |---|---:|---:|---:|---:|
  | KNN | `n_neighbors=31` | 6,984 | 9,409 | 9,1 s |
  | Regresión | `alpha=10.0` | 8,200 | 8,276 | 3,5 s |
  | Random Forest | `max_depth=8` | 7,157 | 9,070 | 79,6 s |
  | SVM | `C=10, ε=1` | 7,525 | 8,293 | 2,7 s |
  | **XGBoost** | `max_depth=4` | 7,189 | **8,217** | 7,2 s |

- **Nota 1 — la brecha train/val es el hallazgo:** RF baja de 7,157 a 9,070 (sobreajuste) y es el más caro en tiempo; XGB generaliza mejor con 7,2 s.
- **Nota 2 — por qué `rmse_val` y no test:** el test se lee **una vez por familia**; elegir con test es hacer trampa.
- **Figura de apoyo:** `docs/evidencia/mlflow/compare_fila.png` (vista Compare, 9 runs por `rmse_val`).
- **Rúbrica:** SAA-6 (30 %), PIA-3 (pipeline), PIA-4 (MLflow).

### 12 · Dos contratos de entrada
- **Layout:** dos columnas enfrentadas, 22 contra 19, y una frase de cierre.
- **Track de clase (fila):** 19 numéricas (`cycle` + régimen + 14 sensores) con `StandardScaler` + `fase_vuelo` con `OneHotEncoder` → **3 columnas 0/1** = 22 entradas. Un solo `ColumnTransformer` para los 5 clásicos y el MLP, guardado en el joblib.
- **Bundle C (ventana):** **14 Ridge independientes**, uno **por sensor**, α = 1,0, sobre los **14 términos** del polinomio de grado 2 en `alt · Mach · TRA · T2`; 19 canales × 50 pasos y **sin categórica**.
- **El porqué, en una línea:** cada sensor responde al régimen a su manera (la altura mueve `T48` de una forma y `Nf` de otra), así que catorce rectas y no una.
- **Frase:** «la categórica etiqueta el régimen; el Ridge lo resta. Coexisten: la app sirve el segundo».
- **Código:** `src/clase/pipeline_clase.py:39`, `src/ds02_rul/features.py:42-48`, `src/ds02_rul/residualizer.py`.
- **Rúbrica:** PIA-3, SAA-4/SAA-8.

### 13 · MLP: una base y tres experimentos con hipótesis
- **Layout:** tabla de 4 filas con la columna «hipótesis» visible — es literalmente lo que pide el 10.
- **Tabla real (`resultados/mlp_comparativa.csv`):**

  | Exp. | Hipótesis | Params | RMSE val |
  |---|---|---|---:|
  | base | «2 capas bastan sin memorizar» | (128,64) α=0,001 | 7,358 |
  | E1 capacidad | «más capacidad capta interacción régimen-degradación» | (256,128,64) | 7,481 |
  | **E2 reg_lr** | «más regularización frena memorización de 22 features ruidosas» | α=0,01 | **7,340** |
  | E3 batch | «batch grande estabiliza el gradiente en ventanas correladas» | batch=1024 | 7,355 |

- **El experimento que sale mal, contado:** E1 **empeora** (7,358 → 7,481). Subir capacidad memoriza. Eso es método, no fracaso.
- **Test (una lectura):** MLP-E2 `7,7211 / MAE 5,8132 / R² 0,8343`.
- **Rúbrica:** SAA-7 (20 %).

### 14 · El techo del modelo de fila
- **Layout:** dos columnas enfrente — «fila» y «ventana» — con la misma métrica y distinto grano.
- **Contraste:** `12.538` lecturas sueltas vs `6.196` ventanas de `50 × 19`.
- **La frase:** una lectura no ve degradación; la degradación es una secuencia.
- **La advertencia (y anticipación de la pregunta individual):** los granos **no se mezclan**; 11,034 (fila) y 4,338 (ventana) no miden lo mismo.
- **Rúbrica:** SAA-6/SAA-8.

### 15 · BiLSTM y la ablación de `cyc_norm`
- **Layout:** tabla 2×2 + figura de barras.
- **La pregunta:** ¿el reloj ayuda o es un atajo?
- **Tabla real (`resultados/ablacion_cycnorm.csv`):**

  | Variante | LGBM | BiLSTM + EMA5 |
  |---|---:|---:|
  | `cyc_norm` OFF | **6,297** | **5,878** |
  | `cyc_norm` ON (baseline) | 7,067 | 5,910 |
  | OFF + baseline delta | 8,765 | 5,896 |
  | ON + baseline delta | 8,547 | 5,974 |

- **Figura:** `resultados/ablacion_cycnorm_rmse.png`.
- **Conclusión:** en el secuencial las cuatro variantes caen en **5,878–5,974** (0,10 de horquilla): el reloj no cambia el resultado. En LGBM **cuesta +0,77**. Por eso `cyc_norm` es canal del BiLSTM y **no entra** en LGBM ni en el meta.
- **Rúbrica:** **SAA-6, columna de 10** — «prueba algo no visto en clase y demuestra si mejora o no».

### 16 · Cada ventana la puntúa otro meta (OOF)
- **Layout:** izquierda el argumento, derecha el diagrama de pliegues.
- **El problema:** elegir β sobre las mismas filas que ajustaron al meta es la fuga clásica; el RMSE de validación se hunde a **0,308** y deja de medir nada.
- **El protocolo:** OOF de **3 pliegues agrupados por motor** sobre los seis motores de desarrollo (`2·5·10·16·18·20`); cada pliegue entrena con cuatro y puntúa a ciegas con los otros dos; el preprocesado se reajusta dentro del pliegue.
- **Dos corridas distintas, no mezclar:** el OOF usa stride 1 y 15 épocas (4–5 min, para medir); el bundle usa stride 3 y 22 épocas (para desplegar).
- **El test no participa** en ninguno de los dos caminos: se lee una vez y solo confirma.
- **Frase:** «la validación no es donde el modelo queda bien: es donde se le puede creer».
- **Rúbrica:** SAA-6, PIA-4 (evaluación honesta).

### 17 · El meta por dentro
- **Layout:** tres piezas a la izquierda, pesos del bundle instalado a la derecha.
- **Pieza 1 — RidgeCV** sobre `[p_lstm, p_lgb]`: elige **α = 88,6** en el propio holdout. α alto porque las dos ramas están correlacionadas; sin regularizar, los pesos se disparan.
- **Pieza 2 — LightGBM** sobre las mismas dos columnas: corrige cuando una rama se desvía. No ve sensores, ni ciclos, ni RUL.
- **Pieza 3 — reconciliación fija:** `p_meta = 0,5 · Ridge + 0,5 · LGBM`. No se aprende un tercer peso: con 2.535 filas de holdout solo añadiría varianza.
- **Figura real:** `resultados/ridge_meta_pesos_06.png` → **28 % red / 72 % árbol**, intercepto **−0,27** ciclos (reconcilia, no aprende un nivel propio).
- **Frase:** cuando se le dio el reloj al meta se lo quedó todo (100 % del peso en `cyc_norm`); por eso el juez solo ve dos columnas.
- **Rúbrica:** SAA-6/SAA-8, PIA-4.

### 18 · β = 1,00 y lo que rechazamos
- **Layout:** la fórmula a la izquierda; a la derecha, las barras del meta que se descartó.
- **La mezcla:** `p = p_lstm + β · (p_meta − p_lstm)`. β = 0 deja el campeón sin riesgo; β = 1 manda el meta. Se elige **fuera de fold** y salió **1,00** (mediana de los tres pliegues).
- **Se dice en voz alta:** con β = 1,00 el sistema no conserva nada del BiLSTM en la salida; queda escrito en el manifiesto.
- **Sensibilidad EMA (no se reelige):** 5,654 → 5,618 con span 5; con span 10 daría 5,574, pero el span se fijó antes de mirar test.
- **El rechazo, medido:** meta ajustado sobre el OOF de los cinco motores (14.915 ventanas, RUL hasta 88) predice media **39,9** con RUL real **31,5**, y el RMSE crece con β: **4,04 → 7,48 → 10,17**. Aprende un prior de nivel que no transfiere. Documentado en `INFORME_motor16_vs_oof.md`.
- **Frase:** «probar lo contrario y publicar el número es parte del método».
- **Rúbrica:** SAA-6, PIA-4.

### 19 · ¿Fue suerte, o es el motor 14?
- **Layout:** tres cifras arriba, tabla por unidad y `bundle_c_rmse_por_motor.png`.
- **Multisemilla:** **4,324 ± 0,107** RMSE y **2341,0 ± 54,1** NASA sobre las semillas 42 · 7 · 123 (README es la fuente autoritativa).
- **Reparto:** U11 3,6328 (3.293 ventanas) · **U14 8,5761 (760)** · U15 2,8371 (2.143) · global 4,338 · macro 5,0153.
- **La frase que hay que decir:** U14 son el 12 % de las ventanas y se lleva el 45 % del error cuadrático; por eso se publican global y macro.
- **Puente con la asignatura (SAA-8):** el LGBM sobre base adaptada cae en **7,067** (NASA 5731,3), exactamente el primer peldaño de la cascada — la misma cifra por dos caminos.
- **Aviso interno:** `resultados/bundle_c_multiseed.csv` en disco da 4,371 y 4,291 (media 4,333); la cifra del deck es la del README. No mezclarlas en la misma slide.
- **Rúbrica:** SAA-7, PIA-4.

### 20 · De 7,067 a 4,338, sin tocar el test
- **Layout:** cuatro KPI, `bundle_c_cascada_rmse.png` y `real_vs_predicho_bundle_c.png`, con la serie completa al pie.
- **Cascada:** LGBM-C 7,067 → BiLSTM-C 5,654 → +EMA5 5,618 → Híbrido-C **4,338**.
- **Métricas del manifiesto:** RMSE 4,338 · MAE 3,227 · R² 0,9461 · NASA 2336,2.
- **Lo que se dice en voz alta:** el test se leyó **una vez**; todo se eligió por validación y lo firma el manifiesto, no el deck.
- **Rúbrica:** SAA-7, PIA-4.

### 21 · El juez se fía del árbol (SHAP de las tres ramas)
- **Layout:** izquierda barras del meta + diagnóstico del residuo; derecha `bar_bilstm.png` y `bar_lgbm.png`.
- **La métrica la elige el negocio:** no RMSE sino **NASA score**, asimétrico — predecir de más deja un motor fundido en vuelo; de menos manda a hangar sin necesidad.
- **SHAP del meta (`resultados/shap_bundle_C/shap_meta.csv`):** `p_lgb` 20,15 · `p_lstm` 8,09 → **71 % árbol / 29 % red**. Sale de un método distinto al Ridge y da el mismo reparto que el 28/72: dos caminos, una conclusión. **Esta coincidencia es el argumento fuerte de la slide.**
- **SHAP de cada rama:** BiLSTM (19 canales) `cyc_norm` 24,1 · `T50` 16,6; LightGBM (93 features) `cyc_norm` 12,9 · `T50_mean` 9,1. Las dos se apoyan en el reloj y en la temperatura de salida.
- **Diagnóstico del residuo (del 06):** sesgo **+0,369** ciclos, rango **−14,8 a +9,5**, el **58,8 %** de las ventanas se pasa —el lado que la NASA castiga— y el 4,3 % falla más de 10 ciclos.
- **Límites dichos aquí mismo:** SHAP describe el modelo, no el motor (asociaciones, no causas); el BiLSTM se agrega por canal y la EMA de producción queda fuera.
- **Coste del error:** 4,338 ciclos ≈ **43.000–130.000 USD** si todo cayera en AOG; U14 ≈ 86.000–257.000. Supuesto declarado.
- **Rúbrica:** **SAA-9 (10)** — SHAP.

## Acto IV · Decisión y acción

### 23 · Ocho reglas, una de seguridad
- **Layout:** tabla de 6 filas con la columna `prioridad` en mono, y la fila de R1 marcada en oro.
- **Tabla real (`src/mia/reglas.py`):**

  | Regla | Prio | Qué hace |
  |---|---:|---|
  | **R1_SEGURIDAD** | **10** | Dato imposible → `SIN_DECISION`, con motivo. Nunca un APTO sin evidencia. |
  | R10_DATOS_INSUFICIENTES | 9 | Faltan límite o umbrales → no se clasifica |
  | R11_UMBRALES_INCOHERENTES | 8 | `hangar ≥ apto` → no se clasifica |
  | R9_HANGAR | 3 | `L_inf < 25` |
  | R8_INSPECCION | 2 | `25 ≤ L_inf < 30` |
  | R7_APTO | 1 | `L_inf ≥ 30` |

- **Cada regla tiene `id`, `prioridad`, `porque`, `accion`** — se enseñan las 4 columnas.
- **Frase:** «con la escalera de umbrales invertida cualquier decisión sería arbitraria, así que no se decide».
- **Rúbrica:** **MIA-2 (30 % de MIA)**.

### 24 · Decidimos sobre el pesimista, no sobre la predicción
- **Layout:** una sola idea, tipografía grande, un esquema de banda.
- **El esquema:** predicción `27` con banda `[23 · 31]`; la regla lee **23** → HANGAR. Sin banda habría salido APTO.
- **Por qué:** equivocarse por optimismo es una parada en pista; por pesimismo, una inspección programada.
- **Coherencia:** conecta la cobertura empírica del conformal con R9/R8/R7. Sin esta slide la banda parece decoración.
- **Rúbrica:** MIA-2 + SAA-8 (umbrales 30/25 de ADR-008).

### 25 · n8n: la decisión se convierte en acción
- **Layout:** diagrama del flujo (15 nodos) arriba, tabla de 3 ramas abajo.
- **Flujo real:** webhook `POST /ds02/decision` → `Switch` (3 salidas) → acción. `responseMode: onReceived` (200 inmediato, compatible con el timeout de 5 s de la app).
- **Tabla:**

  | Rama | Acción |
  |---|---|
  | APTO | registro/log de la decisión |
  | INSPECCION | Google Sheets + aviso para la próxima parada |
  | **HANGAR** | **Postgres `ds02_decisiones`** + Calendar + Gmail |

- **Lo que separa el 7 del 10:** la rama HANGAR **no** hace lo de clase: escribe en Postgres y llama a nuestra API.
- **Transparencia:** el JSON está `active: false` por diseño, sin secretos (solo `id`+`name`), `columns.schema` del nodo Postgres relleno para que importe y funcione; `onError: continueRegularOutput` en la API para no romper la rama si el servicio no está levantado.
- **Rúbrica:** **MIA-3 (35 % de MIA)**.

### 26 · La app: el caso nuevo
- **Layout:** `docs/assets/dashboard_ds02.png` grande + 3 anotaciones.
- **Qué se ve:** RUL, banda conformal, decisión con motivo, SHA del bundle, SHAP local.
- **Control de errores (el 10 de PIA-5):** entrada vacía o imposible → R1 devuelve `SIN_DECISION` con motivo. **Demostrar el caso malo**, no el bueno.
- **Rúbrica:** **PIA-5 (25 %)**, MIA-3 extremo a extremo.

## Acto V · Cierre

### 27 · Límites, dichos por nosotros
- Layout: lista corta en mono, sin adornos.
- TensorFlow en CPU no es determinista bit a bit → el **manifiesto** es la fuente de verdad.
- El coste AOG es **supuesto declarado**, no medición.
- `data/processed/` se regenera; no está versionado.
- n8n inactivo por diseño.
- SHAP cubre las tres ramas, pero el BiLSTM se agrega por canal (se pierde el detalle dentro de la ventana) y la EMA queda fuera de la atribución.
- **Para qué sirve esta slide:** desarma las preguntas hostiles y demuestra criterio.

### 28 · Mapa rúbrica → evidencia
- Layout: tres columnas SAA / PIA / MIA, cada celda con su ruta real.
- La frase de 20 s: la rúbrica cita `src/reglas.py` y `src/utils.py`; aquí la lógica está en `src/mia/reglas.py` y el entrypoint en `app/entrypoints/streamlit_app.py`, y **un test de arquitectura prohíbe las fachadas**.
- **Rúbrica:** PIA-1 (10 %) y prepara las 3 preguntas individuales.

### 29 · Respaldo (no se presenta)
Slides de apoyo para las preguntas individuales:
- **SAA:** ¿por qué `cyc_norm` fuera de LGBM? (ablación, +0,77) · ¿por qué 11,034 no se compara con 4,338? (granos) · ¿por qué U14 falla? (760 ventanas, peor caso).
- **PIA:** ¿dónde está el pipeline? (`src/clase/pipeline_clase.py`) · ¿qué garantiza MLflow? (17 runs curados; `--check` falla si hay `live__*`) · ¿qué pasa si el SHA no coincide? (`load_ensemble` verifica antes de deserializar).
- **MIA:** ¿y si el webhook falla? (`onError: continueRegularOutput`, timeout 5 s) · ¿por qué no decides con la predicción puntual? (`L_inf`) · ¿cuánto cuesta una hora de AOG? (10–15k, credibilidad Media).

---

## Tiempos (20 min)

| Acto | Slides | Min |
|---|---|---|
| I · Negocio | 1–3 | 2,0 |
| II · Datos | 4–8 | 4,0 |
| III · Modelos | 9–21 | 9,5 |
| IV · Decisión | 22–26 | 3,0 |
| V · Cierre | 27–28 | 1,5 |

El acto III son 13 slides en 9,5 min: **~44 s por slide**, y las cuatro de mecanismo
(12 contratos, 16 OOF, 17 meta, 18 β) se llevan casi la mitad. Si hay que bajar a
15 min, el orden de recorte es: 6 y 7 a una sola pasada de 30 s, 13 (MLP) a tres
frases y 19 a la cifra de multisemilla sin tabla. **Nunca quitar 15, 21 ni 25** —
son las celdas de 10 puntos. A 12 min, además: 12 y 14 se cuentan juntas y 16+18
se funden (el OOF justifica β).

## Inventario de outputs reales que van en el deck

| Asset | Slide |
|---|---|
| `docs/assets/dashboard_ds02.png` | 1 (fondo), 26 (protagonista) |
| `resultados/eda_barras_fase.png` · `eda_hist_rul.png` · `eda_box_t48_fase.png` | 7 (arriba) |
| `resultados/eda_scatter_alt_mach.png` · `eda_heatmap_corr.png` | 7 (abajo) |
| `resultados/eda_t48_resid_fase.png` | 8 (después de residualizar) |
| `docs/evidencia/mlflow/compare_fila.png` | 11 |
| `resultados/clasicos_real_vs_pred.png` · `mlp_real_vs_pred.png` | 14 |
| `resultados/importancia_permutacion.png` | 14 |
| `resultados/ablacion_cycnorm_rmse.png` | 15 |
| `resultados/ridge_meta_pesos_06.png` | 17 |
| `resultados/bundle_c_rmse_por_motor.png` | 19 |
| `resultados/bundle_c_cascada_rmse.png` | 20 |
| `docs/assets/real_vs_predicho_bundle_c.png` | 20 |
| `docs/evidencia/mlflow/compare_ventana.png` · `run_prod.png` | 20 / respaldo |
| `resultados/shap_bundle_C/bar_bilstm.png` · `bar_lgbm.png` | 21 |
| `resultados/loss_curve_c.png` | 15 (apoyo: early stopping) |

Sin usar a propósito: `ridge_meta_pesos_04.png` es el mismo gráfico que el 06
(mismo holdout-16), y `app_clase.png` lo cubre la captura de la app.


## Estado

29 slides, ordenadas como los siete cuadernos (01 → 07).
