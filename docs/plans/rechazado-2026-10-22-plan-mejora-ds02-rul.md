> ## ESTADO: RECHAZADO — no ejecutar
>
> **Veredicto:** 2026-10-22. Se conserva el documento íntegro y sin editar como
> registro de una hipótesis que fue evaluada contra la evidencia del repo.
>
> **Por qué se rechaza.** El plan diagnostica un problema de modelo y propone
> soluciones de modelo, pero la evidencia ya estableció que el error dominante es
> la **vida total del motor** (`L`), no observable en inferencia. Ninguna
> transformación de las features fabrica ese escalar.
>
> | Eje del plan | Medición que lo contradice |
> |---|---|
> | Motor 14 = *covariate shift* / densidad de muestreo | `informe-2026-10-21-p3-capacidad-vs-informacion` §4.quater: diezmar a la densidad del 14 **mejora** el RMSE |
> | `cyc_norm` es un atajo a eliminar | Cuesta **+0,355 RMSE**; el k-NN sin reloj pierde 0,70 |
> | β saturado = colapso del meta | `β=1` significa "usar el meta completo"; el meta ya mezcla ambas ramas (`ensemble.py`) |
> | Meta más expresivo (gate, discrepancia, soporte) | `informe-2026-10-21-p0-p1-prior-de-vida` §P1: M1/M3/M4/M7 fallan el gate en `dev` |
> | Escalado estático sobre k=3 ciclos | Es `StandardScaler` global + residualización grado-2 (`ADR-002`); el baseline k=3 existe como `use_baseline_delta`, apagado |
> | EDA sobre el motor 14 (Fase 1) | El motor 14 es **test**: viola el invariante §5.3 del propio plan |
> | Pesos `1/T^γ` para arreglar el motor 14 | De-enfatizan motores largos, y el 14 es el más largo (76 ciclos): trabajan contra el objetivo declarado |
> | Objetivo RMSE < 4,20 | Dentro del IC bootstrap `[3,51 · 5,03]`; 5 semillas no estrechan esa varianza de muestreo |
>
> **Lo único que sobrevive** es el estudio de la banda conformal, y no como mejora
> del modelo sino como **decisión de producto**: `L_inf` gobierna el estado de la
> flota (APTO ≥ 30 / HANGAR < 25 en `cache_manifest`), así que estrechar la banda
> afloja el margen de mantenimiento. Es una decisión del operador, no un cambio de
> código. El EMA adaptativo (Eje 2) queda descartado: con `step=2` el `span=5`
> cubre 0,09–0,49 ciclos, así que el retardo que ataca no existe.
>
> Contexto: `docs/informes/pendientes-2026-10-22-traspaso.md` y los informes
> P0/P1/P3 y ADR-002/005/006/007.

---

# Plan de Mejora Técnica y Metodológica — Proyecto DS02 RUL

Este documento presenta la revisión exhaustiva y la hoja de ruta técnica para optimizar el pipeline híbrido de predicción de Remaining Useful Life ($\text{RUL}$) basado en **BiLSTM + LightGBM Stacking con suavizado EMA**. El objetivo principal es corregir los cuellos de botella detectados en las pruebas de ablación, estabilizar la varianza inter-semilla y reducir la penalización asimétrica en unidades atípicas.

---

## 1. Diagnóstico Crítico del Modelo Actual

Tras auditar los resultados sobre las semillas $[42, 7, 123]$ y el análisis por pliegues (*out-of-fold*), se establecen cuatro vulnerabilidades estructurales en la arquitectura actual:

1. **Asimetría de Rendimiento entre Unidades ($\text{Macro-RMSE}$ vs. $\text{Micro-RMSE}$):**
   * El ensamble logra un $\text{RMSE}$ global competitivo de $4.352 \pm 0.099$ ciclos y un $\text{NASA Score}$ de $2347.7 \pm 53.3$.
   * Sin embargo, la desagregación por motor revela una desviación severa en el **Motor 14** ($\text{RMSE} = 8.044$), en contraste con el Motor 11 ($3.785$) y el Motor 15 ($2.804$). Esto eleva el $\text{macro-RMSE}$ a $4.878$ frente al $\text{RMSE}$ ponderado por ventana ($4.275$).

2. **Inestabilidad Estocástica del Extractor Secuencial (BiLSTM):**
   * El bloque BiLSTM exhibe una desviación estándar elevada entre semillas ($\text{RMSE} = 6.437 \pm 0.757$). Aunque el meta-aprendiz mitiga este efecto, la propagación de incertidumbre degrada la consistencia de los intervalos de predicción en los tramos iniciales de vida útil.

3. **Saturación del Hiperparámetro de Mezcla ($\hat{\beta}$):**
   * La calibración *out-of-fold* arroja una mediana de $\hat{\beta} = 1.00$ con alta dispersión inter-fold. Este comportamiento binario indica que el meta-aprendiz lineal colapsa hacia uno de los modelos base dependiendo de la partición, desaprovechando la complementariedad local entre las representaciones tabulares (LightGBM) y secuenciales (BiLSTM).

4. **Dependencia Esférica del Contador de Ciclos (`cyc_norm`) y Sobre-cobertura Conformal:**
   * La ablación de `cyc_norm` penaliza al BiLSTM en $+0.355$ ciclos de $\text{RMSE}$, demostrando que la red recurrente memoriza la duración media de los motores de entrenamiento en lugar de aislar puramente la firma de degradación física.
   * Las bandas de predicción conformales presentan sobre-cobertura empírica en test, producto de calibrar los cuantiles sobre residuos *out-of-fold* más ruidosos que las predicciones del ensamble final reentrenado.

---

## 2. Arquitectura de Soluciones y Ejes de Intervención

### Eje 1: Mitigación de Deriva de Dominio y Tratamiento del Motor 14
El fallo en el Motor 14 sugiere un desplazamiento de covariables (*covariate shift*) en las condiciones operativas o una degradación acelerada no capturada por el escalado global.

* **Normalización Causal Robusta por Unidad:**
  Sustituir la estandarización estática inicial (actualmente basada en los primeros $k=3$ ciclos) por un estimador robusto de ventana deslizante inicial ($k=5$ ciclos usando mediana y rango intercuartílico $\text{IQR}$) acoplado a una proyección de ajuste por régimen operativo (clustering o regresión sobre variables de entorno antes de calcular el residuo del sensor).
* **Re-ponderación Inversa por Longitud de Trayectoria en elEntrenamiento:**
  Para evitar que los motores con vidas más largas dominen la función de coste, el entrenamiento del meta-aprendiz y del LightGBM incorporará pesos por muestra $w_{i,t}$ inversamente proporcionales al número total de ventanas $T_i$ de la unidad $i$:
  $$w_{i,t} = \frac{1}{T_i^\gamma} \cdot \left(1 + \alpha \exp\left(-\frac{y_{i,t}}{\tau}\right)\right)$$
  donde $\gamma \in [0.5, 1.0]$ equilibra la contribución al $\text{macro-RMSE}$, y el término exponencial ($\alpha > 0, \tau \approx 25$) enfatiza la precisión en la zona crítica de fallo.

### Eje 2: Rediseño del Meta-Aprendiz y Stacking Dinámico $\beta(r)$
En lugar de un coeficiente $\beta$ estático global que satura en $1.00$, el peso relativo entre el BiLSTM ($\hat{y}_{\text{seq}}$) y el LightGBM ($\hat{y}_{\text{tab}}$) debe adaptarse a la fase de degradación estimada.

* **Esquema de Mezcla Dependiente del Régimen de RUL:**
  Definir una función de compuerta (*gating network*) regularizada o un modelo de combinación por tramos continuos donde el peso dependa de la predicción preliminar media $\bar{y}_t = \frac{1}{2}(\hat{y}_{\text{seq}, t} + \hat{y}_{\text{tab}, t})$ y de la volatilidad reciente de los sensores $\sigma_t$:
  $$\hat{y}_{\text{stack}, t} = \beta(\bar{y}_t, \sigma_t) \, \hat{y}_{\text{seq}, t} + \left(1 - \beta(\bar{y}_t, \sigma_t)\right) \hat{y}_{\text{tab}, t}$$
  donde $\beta(\cdot)$ se parametriza mediante una regresión logística penalizada ($\text{L2}$) entrenada directamente para minimizar una aproximación diferenciable del $\text{NASA Score}$ combinada con pérdida de Huber.
* **Optimización del Filtro Post-Proceso (EMA Causal Adaptativo):**
  Reemplazar el suavizado exponencial fijo de $5$ pasos por un filtro EMA con factor de olvido adaptativo $\lambda_t$. Cuando la primera diferencia de las predicciones indique una caída abrupta (entrada en el codo de degradación), $\lambda_t$ debe incrementarse para eliminar el retardo sistemático (*lag*) que provoca sobre-estimaciones tardías altamente penalizadas por la métrica de la NASA.

### Eje 3: Desacoplamiento Temporal (`cyc_norm`) y Estabilización del BiLSTM
Para reducir la varianza inter-semilla ($\pm 0.757$) y eliminar el atajo estadístico de `cyc_norm`:

* **Sustitución por Salud Acumulada Virtual (Virtual Health Index - VHI):**
  Eliminar `cyc_norm` del vector de entrada del BiLSTM y reemplazarlo por dos variables estrictamente físicas y causales:
  1. ** Energía Acumulada de Degradación ($E_t$):** Integral trapezoidal causal de las pendientes de los sensores monótonos principales desde $t=0$ hasta $t$.
  2. **Tasa de Cambio Local ($\Delta s_t$):** Pendiente por mínimos cuadrados ordinarios sobre ventanas locales de longitud $W \in \{5, 10, 20\}$.
* **Regularización Espectral y Ensembling Intra-Semilla (*Snapshot Ensembling*):**
  Aplicar *Weight Decay* desacoplado ($\text{AdamW}$ con $\lambda = 10^{-3}$), *Variational Dropout* en las capas recurrentes (manteniendo la misma máscara a lo largo de los pasos temporales) y promediar los últimos $3$ *checkpoints* del ciclo de entrenamiento (*Stochastic Weight Averaging* - $\text{SWA}$) antes de pasar las predicciones al meta-aprendiz.

### Eje 4: Calibración Conformal Condicional y Asimétrica
Para corregir la sobre-cobertura y alinear los intervalos con el riesgo operativo real:

* **Conformalized Quantile Regression (CQR) Asimétrico por Tramos:**
  Dividir el espacio de $\text{RUL}$ predicho en tres regímenes operativos: Vida Alta ($>60$), Transición ($[25, 60]$) y Crítico ($<25$).
  Calcular cuantiles de no-conformidad independientes para la cola inferior ($\alpha_{\text{low}}$) y superior ($\alpha_{\text{high}}$), con $\alpha_{\text{low}} + \alpha_{\text{high}} = \alpha = 0.10$, asignando un presupuesto de error más estricto al límite superior ($\alpha_{\text{high}} = 0.03, \alpha_{\text{low}} = 0.07$) para proteger contra predicciones tardías (riesgo de fallo no anticipado).
* **Corrección de Escala Out-of-Fold a Full-Model:**
  Aplicar un factor de contracción empírico $\kappa \in (0, 1]$ a los radios conformales obtenidos en validación cruzada, estimado mediante la razón entre la varianza residual del ensamble *out-of-fold* y la reducción teórica de varianza por promediado de $K$ pliegues: $\kappa = \sqrt{\frac{1 + (K-1)\rho}{K}}$, donde $\rho$ es la correlación media de los errores entre pliegues.

---

## 3. Función de Pérdida Híbrida Propuesta

Tanto para el ajuste fino del BiLSTM como para el objetivo personalizado (*custom objective*) de LightGBM y el meta-aprendiz, se unificará el criterio de optimización mediante la pérdida compuesta $\mathcal{L}_{\text{DS02}}$:

$$\mathcal{L}_{\text{DS02}}(y, \hat{y}) = \eta \, \mathcal{L}_{\text{Huber}}(y - \hat{y}; \delta) + (1 - \eta) \, \mathcal{L}_{\text{NASA}}(y, \hat{y})$$

Donde la componente asimétrica de la NASA para un error $d = \hat{y} - y$ se define como:

$$\mathcal{L}_{\text{NASA}}(d) = \begin{cases} \exp\left(-\frac{d}{a_1}\right) - 1, & \text{si } d < 0 \text{ (predicción temprana)} \\ \exp\left(\frac{d}{a_2}\right) - 1, & \text{si } d \ge 0 \text{ (predicción tardía)} \end{cases}$$

Con $a_1 = 13$, $a_2 = 10$, parámetro de transición de Huber $\delta = 5.0$ ciclos, y factor de balanceo $\eta = 0.65$ (ajustable por validación cruzada agrupada por motor).

---

## 4. Plan de Ejecución e Hitos de Validación

| Fase | Paquete de Trabajo | Modificaciones en Código / Módulos | Métrica de Control y Criterio de Aceptación |
| :--- | :--- | :--- | :--- |
| **Fase 1: Datos y Motor 14** | Auditoría de anomalías en Motor 14 y nuevo escalado causal por $\text{IQR}$ + ponderación $w_{i,t}$. | `ds02_rul/preprocessing.py`<br>`notebooks/01_eda_motor14.ipynb` | Reducción del $\text{RMSE}$ del Motor 14 de $8.044 \rightarrow \mathbf{< 6.20}$ ciclos sin degradar Motores 11 y 15 en más de $+0.15$ ciclos. |
| **Fase 2: Ingeniería Causal y BiLSTM** | Reemplazo de `cyc_norm` por $\text{VHI}$ ($E_t, \Delta s_t$) + implementación de $\text{SWA}$ y pérdida $\mathcal{L}_{\text{DS02}}$. | `ds02_rul/features.py`<br>`ds02_rul/models/bilstm.py` | Reducción de la desviación estándar inter-semilla del BiLSTM de $\pm 0.757 \rightarrow \mathbf{< \pm 0.350}$ ciclos y mejora de su $\text{RMSE}$ base a $< 5.80$. |
| **Fase 3: Stacking Dinámico** | Sustitución de $\beta$ estático por compuerta $\beta(\bar{y}_t, \sigma_t)$ + EMA adaptativo en codo de fallo. | `ds02_rul/ensemble.py`<br>`ds02_rul/postprocessing.py` | Eliminación de la saturación ($\hat{\beta} \in [0.25, 0.85]$ en todos los folds). $\text{Macro-RMSE}$ global $< \mathbf{4.50}$ ciclos y $\text{NASA Score} < \mathbf{2100}$. |
| **Fase 4: Conformal Asimétrico** | Implementación de $\text{CQR}$ estratificado por tramo de RUL con factor de contracción $\kappa$. | `ds02_rul/conformal.py` | Cobertura empírica en test dentro de $\mathbf{90\% \pm 1.5\%}$ y reducción del ancho medio del intervalo en al menos un $12\%$ en el tramo $[0, 25)$. |
| **Fase 5: Cierre y Reproducibilidad** | Evaluación multisemilla expandida ($5$ semillas: $[42, 7, 123, 99, 2024]$) y empaquetado. | `models/manifest.json`<br>`scripts/run_benchmark.py` | Pipeline íntegro ejecutable sin fuga de datos (*zero data leakage*), con $\text{RMSE}$ medio global $< \mathbf{4.20}$ ciclos. |

---

## 5. Protocolo de Verificación Anti-Leakage (Invariantes del Proyecto)

Para garantizar la validez científica de todas las iteraciones anteriores, cualquier modificación deberá respetar estrictamente tres restricciones de diseño:
1. **Aislamiento por Unidad (`GroupKFold`):** Ninguna ventana temporal de un mismo motor puede coexistir entre entrenamiento y validación durante el ajuste de $\beta(\bar{y}_t, \sigma_t)$ ni en el cálculo de residuos conformales.
2. **Causalidad Estricta en Inferencia:** Tanto la normalización inicial por motor, el cálculo de pendientes locales $\Delta s_t$, como el suavizado EMA adaptativo deben operar exclusivamente con datos en el intervalo $[0, t]$, prohibiéndose cualquier estadístico global de la serie completa de test.
3. **Inmutabilidad del Conjunto de Test:** Las decisiones sobre hiperparámetros ($\eta, \gamma, \alpha_{\text{low}}, \alpha_{\text{high}}$) se fijarán utilizando únicamente las métricas *out-of-fold* de entrenamiento antes de ejecutar la evaluación final sobre los motores 11, 14 y 15.