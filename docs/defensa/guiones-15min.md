# Guiones de defensa — 15 minutos por alumno

Verificación previa: toda cifra citada sale de `resultados/`, de `mlruns/` o de
código con `path:línea`. MLflow: 17 runs en `mlruns/` (9 fila + 4 ventana + 4 ablación) y
export en `docs/evidencia/mlflow/comparativa.csv`. n8n: flujo incluido en
`n8n/flujo.json`: el flujo versionado está inactivo por diseño, pero la instancia local lo tiene activo y lo ejecutó 29 veces el 2026-11-07 (25 success / 4 error) con efectos reales en Postgres, Calendar y Gmail. El envío desde la app está cableado (`src/n8n.py`), pero no hay ejecución atribuible a la app.

---

## 1. SAA-10 — SAA (modelado de clase)

### 1.1. ¿Cómo elegiste el mejor modelo? ¿Usaste el test?

**Pregunta 1 — ¿Por qué un modelo y no otro?**
**Respuesta.** Elegí por `rmse_val`, nunca por test, con desempate al más
simple. En clásicos: `src/clase/train_clasicos.py:145` ordena por `rmse_val`.
En MLP: `src/clase/train_mlp.py:107` ordena por `rmse_val`. No hay reentreno
en la elección: el test se toca una sola vez y solo para el elegido.

**Pregunta 2 — ¿De dónde salen 7,3404 y 7,7211?**
**Respuesta.** Son la validación y el test del MLP-E2, el campeón del track de
clase. El modelo que se despliega es otro: el ensemble C (4,338), que se elige y
se mide con su propio protocolo de ventanas.
Los dos números están en `resultados/mlp_comparativa.csv`, fila `E2_reg_lr`.
La validación (7,3404) salía del CV por motores; el test (7,7211) es una
lectura única posterior, solo para confirmar que no hay fuga.

**Pregunta 3 — ¿Cómo sabes que SHAP explica de verdad y no decora?**
**Respuesta.** Uso la aditividad: base + suma(SHAP) == predicción, con
tolerancia 1e-5, en `src/clase/shap_clase.py` (`check_aditividad`). El
explainer + fondo son explícitos y las 200 filas explicadas son de
validación (fold-0), nunca test. Si el assert falla, se declara, no se oculta.

**Pregunta 4 — ¿Y el modelo que se despliega?**
**Respuesta.** El ensemble C: BiLSTM + LightGBM cuantílico, meta-learner y EMA causal,
RMSE 4,338 y macro-RMSE 5,0153 (U11 3,63 · U14 8,58 · U15 2,84). La capa opcional de reglas
recalibra la banda (R6) sobre 14.915 filas OOF puras: la unidad 16 se excluye porque
entrenó el meta-learner. Sin esa corrección, la lectura usa la banda del artefacto. El guion no confunde los dos campeonatos: E2 es el mejor del
track de clase; C es el que está en producción.

**Que NO decir.** No mezcles E1 (capacidad grande, más overfit, val 7,48) con
E2 (regularización, val 7,34): si te preguntan por capacidad, cita E1; si es
por regularización, cita E2. No digas «elegí por test» ni «probé el test
varias veces»: el test es de una sola lectura. No presentes la validación
(7,34) como si fuera el test (7,72).

## 2. PIA-6 — PIA (pipelines y preprocesado)

### 2.1. ¿Por qué un Pipeline? ¿Por qué no escalar a mano?

**Pregunta 1 — ¿Dónde está el preprocesado y dónde está el modelo?**
**Respuesta.** Están juntos en un Pipeline para que el `fit` del preprocesado
sea solo en train y se reutilice en validación y test. La definición única
está en `src/clase/pipeline_clase.py:27` (`ColumnTransformer`). El numérico
lleva `StandardScaler` y la categórica `OneHotEncoder`. Así no hay fuga del
escalado al test.

**Pregunta 2 — ¿XGB 8,217 / 11,034 significa que XGB es peor?**
**Respuesta.** Son validación (8,217) y test (11,034) de XGB en el pipeline
común, fila `xgb` de `resultados/comparativa.csv`. La caída entre val y test
es mayor que con el MLP-E2 (7,34/7,72), como les pasa a los modelos más
flexibles en este corte. La elección final no sale de estos dos números
solos: sale de `rmse_val` completo y del desempate al más simple en
`src/clase/train_clasicos.py:145`.

**Pregunta 3 — ¿Por qué validación por grano y no filas sueltas?**
**Respuesta.** Porque el RUL es serie por motor: las filas de un mismo motor
están correladas y si van a train y a validación a la vez, la validación
miente. Uso GroupKFold por motor (validación, nunca test). El grano de
ventana es otra cosa: dentro del motor, cada ventana es una muestra de
entrenamiento, no una fila suelta.

**Que NO decir.** No confundas grano-fila (una fila = una ventana) con
grano-motor (el split agrupa motores). No digas que escalar sobre todo el
dataset es inocuo: el scaler se ajusta solo en train. No compares val de un
modelo con test de otro como si fueran la misma métrica.

## 3. MIA-4 — MIA (reglas de decisión)

### 3.1. ¿Por qué reglas y por qué esas prioridades?

**Pregunta 1 — ¿Por qué un sistema de reglas y no un clasificador?**
**Respuesta.** Porque la decisión final es de seguridad y tiene que ser
auditable línea a línea: APTO, INSPECCIÓN o HANGAR no salen de una caja
negra. El sistema está en `src/mia/reglas.py` con tuplas
(nombre, condición, efecto, prioridad, porqué). La regla de seguridad R1
tiene prioridad 10; las de decisión van 3/2/1 (hangar/inspección/apto). Si
el dato es imposible, no se decide nada, tenga el riesgo que tenga.

**Pregunta 2 — ¿Qué significan los umbrales 25 y 30?**
**Respuesta.** Son los umbrales conformales documentados en ADR-008 y citados
en `src/mia/reglas.py:15`. En la práctica, `L_inf` por debajo del de hangar
no vuela (HANGAR, prioridad 3); entre los dos umbrales, inspección
programada (prioridad 2); por encima del de apto, sigue en servicio
(prioridad 1). No los inventé yo: están en el informe de calibración y en la
cabecera de reglas.

**Pregunta 3 — ¿Qué es R2b y qué es isotónico aquí?**
**Respuesta.** R2b es la corrección isotónica causal: si la tendencia del
desgaste no sube con el ciclo, se toma el extremo del ajuste isotónico del
historial, con prioridad 2 en `src/mia/reglas.py:209`. «Isotónico» aquí
significa un ajuste que respeta la monotonía del historial, no que el mundo
sea monótono de verdad. La decisión después sigue pasando por R6_BANDA, que
recalibra sobre el punto ya corregido, no sobre el crudo.

**Que NO decir.** No confundas `L_inf` (límite inferior conformal) con `p`
(probabilidad): el primero no es una probabilidad. No digas que «R2b isotónico
prueba que el desgaste es monótono»: corrige una tendencia que no sube, no
demuestra la técnica. No digas que los nulos los inyecté para «engañar»: son
MAR (~2% solo en T30 con alt>27 000 y Mach>0,68, ver
`src/clase/dataset_clase.py:11`), con auditoría, y la simulación con seed 7
es solo una de las semillas del análisis.

---

## Notas rápidas para los tres

- **Manifest 4,338.** El híbrido desplegado (bundle C) está en
  `resultados/tabla_final_clase.csv` con 4,338. Es el número de la tabla, no
  un promedio inventado. Si te preguntan por multiseed, cita la media que trae
  el artefacto, sin inventar decimal.
- **Test una vez.** La frase es siempre: «el test se evalúa una sola vez y
  solo para el elegido». Ver `src/clase/train_clasicos.py` y
  `src/clase/train_mlp.py:107`.
- **Acción novedosa en n8n (MIA-3).** El flujo tiene 20 nodos (13 funcionales + 7 notas) y 4 ramas. Lo que no es de clase: la rama FALLBACK (decisión no reconocida → Set de error + alerta Telegram, sin ejecutar acción) y el aviso Telegram en las tres ramas. Si el tribunal no acepta Telegram como novedad, el argumento es el FALLBACK y el contrato de decisión (decisión + motivo + L_inf + SHA), no la rama HANGAR: Postgres, Calendar y Gmail sí son de clase. No digas que el flujo llama a nuestra API: el JSON no tiene nodo HTTP.
- **MLflow / n8n.** «MLflow tiene 17 runs en `mlruns/`: 9 de fila, 4 de ventana y 4 de ablación, con export y capturas; el store es texto y no guarda binarios. n8n está incluido; el flujo versionado está inactivo por diseño (un test lo exige así), pero la instancia local lo ejecutó 29 veces (2026-11-07) con efectos reales. No vendas una ejecución de la app: no la hay.»
