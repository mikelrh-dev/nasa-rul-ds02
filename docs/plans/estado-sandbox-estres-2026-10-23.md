# Estado del sandbox de estrés y la demo del tribunal (2026-10-23)

> **Para quien retome esto:** este documento dice qué está hecho, qué está
> verificado con mediciones y qué falta. Si una afirmación no se reproduce con el
> comando que la acompaña, el documento está mal.
>
> **Contexto:** directiva de refinamiento de `app/dashboard_ds02.py` para una demo
> en directo ante un tribunal. Objetivo: que no parezca un script con datos
> precargados y que el input del modelo se pueda cambiar en vivo.

---

## 1. Qué se pidió

| Tarea | Contenido |
|---|---|
| **A** | Terminología: «50 filas» → «50 muestras remuestreadas (~0,4 ciclos de vuelo)» (spec §6.10). Actualizar asserts acoplados. |
| **B** | Sandbox de estrés en la pestaña 5, dentro de `@st.fragment`: slider de deriva térmica + selector de unidad, re-puntuar en vivo y re-decidir con el motor oficial. Banda degradada cuando hay deriva. |
| **C** | Unificar el atajo de U14 ciclo 29 con el paso 3 del modo historia + nota sobre la no-monotonía (ADR-006). |

**Invariantes:** G1 `models/` y `src/ds02_rul/` de solo lectura · G2 cero CSS inyectado · G3 todo gráfico/tabla con `alt` · G4 métricas desde caché o manifiesto · G6 reglas solo de `mia/reglas.py`.

**Decisiones de diseño aprobadas:**
- (a) Sandbox en la **pestaña 5**, no en el sidebar.
- (b) Con deriva ≠ 0 la banda se **muestra** (punteada, leyenda *«Banda proyectada (fuera de garantía conformal 90 %)»*) con aviso; no se oculta.

---

## 2. Qué está hecho

### Tarea A — terminología (completa)

| Fichero | Línea | Cambio |
|---|---|---|
| `app/dashboard_ds02.py` | 449 | «Ventana» → «50 muestras remuestreadas (~0,4 ciclos de vuelo)» |
| `app/dashboard_ds02.py` | 2185-2188 | Caption de la pestaña 5 |
| `app/dashboard_ds02.py` | 2231 | `help` del selector de dataset demo |
| `app/dashboard_ds02.py` | 2280 | Caption de `cycle` |
| `app/dashboard_ds02.py` | 2283 | Botón «Descargar plantilla CSV (50 muestras remuestreadas vacías)» |
| `app/dashboard_ds02.py` | 2310 | Contador «N de M muestras seleccionadas» (rama ejemplo) |
| `app/dashboard_ds02.py` | 2351 | «**N muestras** → K ventana(s)» (rama pegado) — **este era el «50 filas» que fijaba el assert de `test_live_eval.py:351`** |
| `app/dashboard_ds02.py` | 2532 | Caption del contrato |
| `app/ui_batch.py` | 25 | Comentario |
| `app/ui_inference.py` | 242 | Mensaje del validador: «al menos 50 muestras remuestreadas (~0,4 ciclos de vuelo)» |
| `app/ui_inference.py` | 329 | Mensaje de preflight |

Asserts actualizados en el mismo paso (necesario: fijaban el texto literal):
`tests/test_live_eval.py:63`, `tests/test_live_eval.py:351`, `tests/test_ui_batch.py:93`.

> **Nota:** el plan hablaba de 6 textos; el séptimo (`:2310`) lo forzó el assert de
> `:351`. El de `:2351` también: era ahí, no en `:2310`, donde realmente se pintaba
> «50 filas» en la rama que mira el test.

### Tarea C — unificación U14 ciclo 29 (completa)

- **Premisa verificada en caché:** `U14` ciclo 29 tiene `y_true = 47.0` exacto y la
  decisión **cruza dentro del propio ciclo** (INSPECCIÓN → HANGAR):

  ```
  ciclo 28  lower_media=26.42  INSPECCION
  ciclo 29  lower_media=24.80  HANGAR      <- y_true=47.0, lower 25.69 -> 23.29
  ciclo 30  lower_media=22.42  HANGAR
  ```

- **El modo historia ya lo hacía:** `app/ui_alta.py:130` saca `ciclo_hangar` con
  `primer_ciclo(motor, "HANGAR")` y el motor es el de mayor RMSE (U14). Medido:
  `estado_historia(windows, {30,25})[2]` = `{unidad: 14, ciclo: 29}`.
- **Lo que faltaba:** el botón de la pestaña 5 (posición 0.40) caía en ciclos 28→30,
  un camino distinto. Ahora ambos salen de la caché:
  - `app/dashboard_ds02.py:2150-2157` — `DEMO_PRESETS` se construye desde
    `A.estado_historia(...)[2]`, así que si la caché cambia, cambian los dos.
  - `app/dashboard_ds02.py:2160` — el preset crítico se llama
    `"Crítico U14 · ciclo 29 (HANGAR)"`.
  - `app/ui_inference.py:112` — nueva `window_ending_at(unit, cycle)`: la ventana que
    **termina** en el ciclo pedido (mismo contrato que `example_window`, anclada a
    ciclo en vez de a fracción de filas). Verificada: `window_ending_at(14, 29)` →
    `row_slice [570, 620]`, `end_cycle 29`, 50 filas × 19 columnas, preflight sin avisos.
- **Nota de no-monotonía** en `app/dashboard_ds02.py:2193-2224`: calcula `_lo_max`,
  `_lo_min`, `_y_real` y los ciclos de caída/repunte **desde la caché** (G4) y cita
  ADR-006. Texto pintado: «…cae a inspección en el ciclo 8 y vuelve a apto en el 14…».

### Tarea B — sandbox en la pestaña 5 (completa)

- `app/dashboard_ds02.py:577-754` — `@st.fragment def _sandbox_estres()`.
- `app/dashboard_ds02.py:2837-2840` — llamada al final de la pestaña 5, dentro de un
  `st.container(border=True)`.
- **Controla:** `st.segmented_control` «Unidad del tramo» (`key="sbx_unit"`) y
  `st.slider` «Deriva térmica acumulada en T48» (`key="sbx_deriva"`, 0–30 %).
- **Tramo derivado de la caché:** del primer ciclo puntuado al primero en que la caché
  ya manda al hangar. Medido: U11 1→22, U14 3→29, U15 2→25.
- **Perturbación:** rampa progresiva sobre `T48` dentro del tramo
  (`T48 * (1 + deriva * linspace(0,1,n))`), no un escalón.
- **Puntuación:** `INF.score_table()` + `UR.decidir_ventanas()` (G6). Nada se
  reentrena, no se toca `models/` ni `src/` (G1).
- **Banda:** con deriva = 0 → `Banda conformal (90 %)`; con deriva ≠ 0 →
  `Banda proyectada (fuera de garantía conformal 90 %)`, línea punteada y relleno rojo
  (decisión b). Umbrales como `hline` y `vline` en el cruce.
- **Avisos:** los del preflight + uno propio que explica que la intervención sintética
  rompe la intercambiabilidad y la banda pierde el 90 % (ADR-008).
- **Umbrales leídos de `session_state`**, no del global del módulo: el fragment se
  re-ejecuta solo y un global quedaría obsoleto si el tribunal cambia la política en la
  pestaña del taller.
- **G3:** el gráfico lleva `alt` que describe el cruce y el estado.

---

## 3. Qué está verificado

### Mediciones (reproducibles)

```
score_table()      0,25 s para 545 ventanas (tramo U14 3→30)
get_ensemble()     5,90 s, una sola vez (@st.cache_resource)
AppTest por cambio  1,4–2,1 s según unidad
```

El sandbox en U14, moviendo el deslizador (AppTest, `key="sbx_deriva"`):

| Deriva | Cruce a HANGAR | RUL al final |
|---|---|---|
| 0 % | ciclo 29 | 36,3 |
| 5 % | ciclo 13 | 25,8 |
| 10 % | ciclo 13 | 21,6 |
| 30 % | ciclo 12 | 20,7 |

Unidades alternativas: U11 → cruce 22, U15 → cruce 24.

Leyenda verificada leyendo `proto.spec`: `['Banda conformal (90 %)', ' ', 'RUL predicha']`
con deriva 0 y `['Banda proyectada (fuera de garantía conformal 90 %)', ...]` con 10 %.
`alt` no vacío en ambos casos. El aviso de honestidad aparece **solo** con deriva ≠ 0
(0 avisos a 0 %, 1 aviso a 10 %).

### Suite

```
.venv/Scripts/python.exe -m pytest tests -q
→ 185 passed in 97,28 s
```

180 tests previos + 5 nuevos (`tests/test_live_eval.py`, bloque «sandbox»):

- `test_el_sandbox_reproduce_la_caché_con_deriva_cero` — el cruce a 0 % es el primer
  ciclo HANGAR de `unit_curve`, no una constante.
- `test_el_sandbox_degrada_la_banda_cuando_la_entrada_es_sintetica` — leyenda + aviso.
- `test_la_deriva_sintetica_adelanta_la_decision` — el cruce se adelanta o se queda.
- `test_el_sandbox_decide_con_el_motor_oficial` — el estado es una etiqueta de
  `L.STATE_LABELS`.
- `test_el_sandbox_muestra_el_tramo_y_no_toda_la_vida_del_motor` — **regresión** del
  fallo que cazó el navegador (ver 3.2).

### 3.2 Verificación en navegador real (hecha)

Servidor en el puerto 8502, Chrome real. Comprobado:

| Comprobación | Resultado |
|---|---|
| La pestaña 5 pinta el sandbox | Sí: slider «Deriva térmica acumulada en T48» y selector 11/14/15 |
| Render inicial **sin** TensorFlow | Sí. Servidor reiniciado en limpio: el log no traía ni una línea de TF tras cargar y abrir la pestaña 5 |
| Mover el slider carga el modelo | Sí. TF aparece en el log **solo** al mover el slider (15:31:06); el segundo movimiento (15:34:01) no vuelve a importar |
| Re-puntuación en vivo | Sí. Métrica y conteo cambian de caché a scoring: `38,3 ciclos / 29 / 286 ventanas` → `21,6 / 13 / 530` |
| Banda degradada | Sí. Leyenda `Banda proyectada (fuera de garantía conformal 90 %)` |
| Avisos honestos | Sí. OOD (`T48 28/579` al 10 %, `157/579` al 20 %) + el aviso de intercambiabilidad |
| Selector de unidad | Sí. U11 → tramo `1→22`, 2487 muestras, cruce 11 |
| Aislamiento del fragment | Sí. Tras mover el slider, `stSidebar` y `stMainContainer` siguen siendo **los mismos nodos** (`===` en JS) y una marca `dataset` puesta antes sobrevive |
| Excepciones | Ninguna (`stException` vacío en todos los estados probados) |

**Fallo cazado por el navegador y corregido** (`app/dashboard_ds02.py:644`):
en la rama de caché (deriva 0) `unit_curve` devuelve **toda la vida** del motor, así
que la métrica y la curva usaban los 76 ciclos en vez del tramo. Se veía «RUL 0,9
ciclos» (fin de vida) y «760 ventanas». Ahora `_cur` se filtra a `_c_fin` y `_ventanas`
cuenta solo las ventanas del tramo (286). El test de regresión
`test_el_sandbox_muestra_el_tramo_y_no_toda_la_vida_del_motor` lo fija.

### Cambio de diseño durante la ejecución (importante)

El primer diseño puntuaba el sandbox en **cada** render. Eso rompía
`test_live_eval.py::test_the_app_does_not_load_the_model_until_asked`: la app está
documentada y testeada para **arrancar sin el artefacto** (2,3 GB, ~6 s).

Solución adoptada: **con deriva 0 % el tramo se dibuja desde la caché y el modelo no se
carga**; solo una deriva ≠ 0 paga la carga (una vez, `@st.cache_resource`). Se probó
también con `on_change` + bandera en `session_state`, pero `on_change` no dispara en
AppTest cuando el valor no cambia (0→0) y hacía frágil el test.

---

## 4. Qué falta

1. ~~Verificación en navegador real.~~ **Hecha** (sección 3.2). Aislamiento del
   fragment confirmado, carga diferida confirmada y ninguna excepción.
2. **Decidir si el tramo por defecto es el recomendado.** El plan decía «ciclos 3 a 8»;
   con ese tramo **no se ve el salto de estado** (el `lower` se queda en 27,5 > 25 y la
   decisión no cambia). El tramo actual es 3→29 (del primer ciclo al cruce natural a
   hangar). Confirmar que se prefiere así.
3. **Revisar el notebook y la documentación** si se quiere reflejar la nueva terminología
   en los cuadernos (el spec §6.10 ya la documenta; los `.ipynb` de
   `notebooks/ds02_ensemble/` tienen modificaciones previas ajenas a esta tarea).
4. **Commits.** Todo está **sin commitear**. Los ficheros tocados por esta tarea son:
   `app/dashboard_ds02.py`, `app/ui_inference.py`, `app/ui_batch.py`,
   `tests/test_live_eval.py`, `tests/test_ui_batch.py`, más este `.md`. Los tres
   `.ipynb` y `MLProyectVault/` estaban ya modificados antes de empezar.

---

## 5. Cómo relanzar

```bash
cd C:/Users/mikel/Desktop/Pruebas/nasa

# suite
.venv/Scripts/python.exe -m pytest tests -q

# app
.venv/Scripts/python.exe -m streamlit run app/dashboard_ds02.py --server.headless true
```

Servidor de trabajo levantado en el **8502** (sesión `proc_6f5902ee6fac`,
`http://localhost:8502`, `/_stcore/health` → `ok`). Si se quiere el 8501, matar el
proceso y relanzar con `--server.port 8501`.

**Nota sobre el navegador:** el slider de Streamlit no reacciona a un `.value` puesto
por JS (React no emite `onChange`). Para moverlo en una prueba de extremo a extremo
hay que enfocar el `input[type=range]` y enviar `ArrowRight`/`ArrowLeft` por CDP.

---

## 6. Cómo explicar esto al tribunal

- **La caché no es un truco:** son los motores 11, 14 y 15 del test DS02, ya puntuados
  por el artefacto congelado. La app dice que son el histórico de referencia.
- **El input se cambia en vivo:** pestaña 5 → «Puntúa un motor con datos que aportes tú»
  (pegar desde Excel o subir CSV) puntúa lo que el tribunal escriba. Ahí está la defensa
  real contra «datos precargados».
- **El sandbox demuestra que el pipeline corre:** mover el deslizador re-puntúa con el
  BiLSTM + LightGBM y re-decide con el motor de reglas, en ~1,4 s.
- **El 50 está mal contado en el nombre, no en el modelo:** 50 muestras de una serie
  remuestreada ×100 ≈ 0,4 ciclos de vuelo (spec §3.1 y §6.10). La app lo dice ahora.
- **La banda sintética se degrada a propósito:** una intervención sintética rompe la
  intercambiabilidad del split-conformal, así que la leyenda lo avisa en vez de
  aparentar una cobertura del 90 % que ya no tiene.
