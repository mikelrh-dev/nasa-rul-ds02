# DS02 · Explicación de la lógica de negocio y la decisión de "hangar"

**Para:** defensa del proyecto (tribunal).  
**Qué leer:** este documento acompaña la pregunta *"¿cómo decide el sistema si revisar, parar en hangar o dejar volar un motor?"*.  
**Verificado:** todas las cifras se reprodujeron ejecutando código contra la caché (`app/cache/`) y contra `ui_data_loader.first_alarm_cycle` la misma semana de la defensa.

---

## 0. Hilo de defensa (lo que decir en 30 segundos)

1. El sistema **no decide con la predicción puntual** de la RUL, sino con el **límite inferior de la banda conformal** (`L_inf`). Por eso el proceso no se rompe por el sesgo del modelo.
2. El umbral **30/25** no es arbitrario: es el único que hace alcanzable el estado "verde" sobre la caché real, porque la banda subtendrá ~24 ciclos alrededor del techo de predicción (~60.6 ciclos). El plan original 50/25 dejaría toda la flota en ámbar.
3. "Hangar" aquí es un **triage conservador**, no un control operativo. El modelo dice "hay riesgo", el taller decide "desmontarlos". Eso se dice en la app y el ADR-008.

---

## 1. Flujo completo del sistema

```
Ventana (50 filas, 18 canales, muestreadas cada 100 filas: ~0,44 ciclos de vuelo)
   ↓
Ensamble hibrido BiLSTM + LightGBM cuantílico (con 50% objetivo asimétrico)
   ↓
predict_interval() → rul_punto, limite_inferior, limite_superior  (banda conformal 90%)
   ↓
[Pasada B — corrección opcional] R2b isotónica causal sobre el punto, R6 recalibra la banda
   ↓
[Pasada A — decisión] Reglas R1/R9/R8/R7 sobre `limite_inferior`
   ↓
Estado: APTO / INSPECCIÓN / HANGAR (según L_inf ≥ 30 / 25 ≤ L_inf < 30 / L_inf < 25)
```

El artefacto (modelo) está **congelado** en `models/ensemble.joblib`; la app no carga TensorFlow en el despegue, solo lee `app/cache/` y el manifest.

## 2. ¿Por qué no se decide sobre la predicción puntual?

La RUL estimada por el modelo **tiene sesgo por motor**:

| Unidad | sesgo de la RUL puntual |
|---|---|
| 11 | +3.03 |
| 14 | −5.19 |
| 15 | −2.27 |

Decidir sobre ese número haría que un motor "bonito" (U14, que falla tarde en la caché) pase a señal de riesgo **por el valor del modelo, no por la evidencia**. El `L_inf` —el peor caso de la banda— absorbe ese sesgo, y es la dirección que compensa la penalización asimétrica de la NASA score (estimar menos vida que la real es más caro que sobreestimar).

Esto está documentado en el ADR-008 del propio repositorio.

## 3. ¿Por qué 30 / 25 y no 50 / 25?

Es la trampa matemática que descubrió el equipo:

- La predicción puntual se **satura** en ~60.6 ciclos (la zona plana inicial del DS02, donde no hay degradación visible).
- Al calibrar la banda conformal al 90 % en el tramo `[50, 75)`, el margen de incertidumbre restado al techo es de **−24.47 ciclos**.
- Luego: `L_inf(max) ≈ 60.6 − 24.47 ≈ 36 ciclos`.

Es decir, **nunca** el `L_inf` de un motor nuevo superará los ~36 ciclos. Con un umbral verde de 50, el semáforo nunca se pondría en verde (toda la flota aparecía ámbar desde el minuto cero, y eso falsaría la percepción de un modelo preciso).

La solución: ajustar los umbrales al rango real de la banda:

| Estado | Condición | Significado operativo |
|---|---|---|
| 🟢 APTO | `L_inf ≥ 30` | Motor sano. Todos arrancan en verde (35.7 / 33.0 / 35.8). |
| 🟡 INSPECCIÓN | `25 ≤ L_inf < 30` | Alertas preventivas; vigilar. |
| 🔴 HANGAR | `L_inf < 25` | Inmovilización; orden de trabajo emitida. |

El umbral **25** además coincide exactamente con el tramo crítico `[0, 25)` del modelo (donde la MAE del modelo es 1.13 ciclos), así que el corte rojo también define el "cambio de régimen".

## 4. La banda es conservadora. Eso tiene costo y se declara.

La cobertura real de la banda alcanza **100 %** sobre el 90 % objetivo, con un ancho promedio de ~26 ciclos. Consecuencias declaradas:

- El sistema **protege más de lo necesario**: una unidad puede quedar en "hangar" con RUL puntual aún por encima de 25.
- Eso tiene un coste operativo (pérdida de disponibilidad) que el ADR-008 mide y publica: el motor U14 pudo quedar hundido con 47 ciclos aún por verificar.
- El propósito del sesgo conservador es que el error del modelo no es simétrico: equivocarse "hacia abajo" (decir que se acabó antes) es el peor fallo, porque en un motor de aviación hay que priorizar la seguridad.

## 5. La cifra que hay que tener muy clara: "anticipación" o "lead time"

Hay **dos** medidas de antelación, y el documento original mezcla las dos. Para el tribunal conviene explicarlas por separado, porque responden a preguntas distintas:

### 5.1 Lead time (lo que dice el ADR-008) — 9 / 23 / 17 ciclos

```

U11: cruce del L_inf medio del ciclo < 25 en ciclo 26; el fallo real (RUL < 25) en ciclo 35. → antelación 9 ciclos.
U14: 29 → 52. → 23 ciclos.
U15: 26 → 43. → 17 ciclos.

```

"Combien de ciclos tengo de antelación antes de que el **corte de decisión (media del ciclo)** llegue a AOG, sobre el momento en que la RUL real se acaba?"

### 5.2 Anticipación (lo que dice el informe de 24 de octubre) — 13 / 23 / 18 ciclos

```

U11: el peor L_inf de la ventana cruza 25 en ciclo 22; la verdad en 35. → 13 ciclos.
U14: 29 → 52. → 23 ciclos.
U15: 25 → 43. → 18 ciclos.

```

"Combien de ciclos tengo de antelación antes de que el **peor límite inferior de la ventana** (el más conservador) cruce 25, sobre la RUL real."

### 5.3 La diferencia técnica

El `L_inf` no es un número fijo por ciclo: cada ciclo acumula varias **ventanas** (50 filas, muestreadas cada 100 filas: ~0,44 ciclos de vuelo). El ADR-008 cota el cruce con la **media de los límites inferiores** del ciclo (`lower`), que es el valor que usa la regla R9 en `fleet_snapshot`. El informe de 24 de octubre usa el **peor** límite inferior de la ventana (`lower_min`), que avisa más temprano. Las dos cifras son correctas; mide magnitudes distintas, y la diferencia es mayor en la unidad 11 (9 vs 13) que en la 14 (23 = igual en ambas, porque su `lower` y `lower_min` bajan de golpe).

> Regla de oro para la defensa: si te preguntan "cuánto avisa", contesta **13/23/18 ciclos** (medida conservadora, ventana peor), y, si te piden la cifra del diseño, **9/23/17** (lead time al corte neto de la regla). No mezcles las dos sin explicar la diferencia.

## 6. Qué significa "hangar" aquí, y qué le falta a este sistema para ser operativo

Esto es lo más importante para la pregunta original del tribunal: *"¿realmente un hangar se llena así?"*

- Lo que el sistema **sí** hace: **triangula**. Dada la RUL estimada y su incertidumbre, dice "esta unidad es candidata a derivarse".
- Lo que el sistema **no** hace: **llegar al hangar**. No incluye programación de banner, disponibilidad de taller, comprobación de repuestos, orden de servicio, ni los criterios operativos del aeropuerto. El módulo `hangar.py` es **solo un registro de estado** —una cuenta con transiciones permitidas y la traza de quién moveió qué— tal como lo declara su propio docstring: *"operational bookkeeping that no gate measures"*.

En un proyecto real esto debería ir acompañado de un **modelo de costes** (coste de una falsa confirmación, coste de un fallo no detectado, coste de una ventana sin taller libre). Ese modelo no está en el repo; lo que sí lo está es la **disciplina de declararlo**.

## 7. Qué está verificado (evidencia de ejecución)

| Afirmación | Verificación |
|---|---|
| 211 tests del paquete `src/mia/` + `hangar()`/`flota()` + reglas pasan | Ejecutados 2026-10-25: `211 passed in 196.76s` |
| Primera operación de `first_alarm_cycle(c, 25.0)` | Reproducida: `U11: 22/35/13`, `U14: 29/52/23`, `U15: 25/43/18` |
| Saturación de la predicción puntual en ~60.6 y bin `[50,75)` −24.47 | Cites del ADR-008 y del `README.md`; consistente con la curva de U11 |
| `L_inf(max) ≈ 36` y todos los motores empiezan en verde | Alta estimación teórica ~36.13; observada 35.7 / 33.0 / 35.8 |

## 8. Preguntas que puede hacer el tribunal y respuesta directa

**"¿Y si el modelo falla?"** → La regla R1_SEGURIDAD (`alertas_datos`) convierte cualquier dato imposible en `SIN_DECISIÓN` (no se decide). La decisión se basa en el límite inferior de la banda, no en el punto.

**"¿Por qué 30/25 si parece poco margen?"** → Porque el `L_inf` nunca puede superar ~36 ciclos (quizá la pregunta más complicada). Los umbrales están calibrados al rango de la banda y son **ajustables en la UI**; con un slider a 50/25 el operador ve toda la flota en ámbar, y la app lo declara.

**"¿Esto es un hangar real o un triaje?"** → Es un triaje conservador. El modelo ofrece riesgo; el taller decide. Lo que falta para ser operativo son el modelo de costes y la integración con el despacho de trabajos.

**"¿Y el margen 9 vs 13?"** → Son el mismo hecho, dos estadísticas: media del ciclo (`lower`, lo que usa la regla) vs peor ventana (`lower_min`, lo más conservador). Se presentan por separado en el ADR-008 y el informe de 24 de octubre, y hay que decir la diferencia.

## 9. Referencias del proyecto

- `docs/decisions/ADR-008-conformal-lower-bound-triage.md` — aceptado 2026-10-21; la regla 30/25.
- `docs/decisions/ADR-009-r2b-is-an-isotonic-fit-not-a-monotonicity-rule.md` — la corrección isotónica causal.
- `docs/informes/informe-2026-10-24-anticipacion-al-fallo.md` — cifra 13/23/18 y su cálculo.
- `src/mia/reglas.py` — motor de reglas (pasada B: R2b/R6; pasada A: R1/R9/R8/R7).
- `app/hangar.py` — cuenta de estado, no decisión.
- `src/mia/modelo.py` — capa de predicción del artefacto congelado.
