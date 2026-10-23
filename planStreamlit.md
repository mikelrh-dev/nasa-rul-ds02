# Plan revisado: pulido de la demo en vivo del DSS DS02

> **Para quien ejecute este plan:** usa la skill `plan` para validar el alcance y
> `test-driven-development` para cada tarea. Este documento no ejecuta nada.
>
> **Para quien lo revise:** cada cifra es reproducible con los comandos de la
> sección 7. Si una afirmación no se puede reproducir, es un error del plan.

**Objetivo:** que un tribunal ajeno al proyecto entienda la propuesta de valor del
DSS DS02 en menos de 10 segundos, y que el presentador pueda incorporar una unidad
nueva durante la demo en directo sin salirse del flujo ya existente.

**Arquitectura:** no se toca inferencia, ni `models/`, ni `src/ds02_rul/`, ni
`mia/`. Todo el trabajo es presentacional sobre `app/dashboard_ds02.py` y los
módulos de apoyo existentes. El plan es **incremental** sobre la capacidad ya
desplegada en `openspec/specs/ds02-dss-ui/spec.md`: no es una reescritura de la
interfaz.

**Stack:** Streamlit 1.66.0 · Plotly 7.1.0 · pandas · PyArrow. Sin TensorFlow en
tiempo de render.

---

## 0. Cómo leer este plan

Las tareas están ordenadas de menor a mayor riesgo. **C1, C2 y C3 son seguras y
aportan casi todo el valor.** C4 es opcional y lleva su riesgo escrito.

La sección 4 es la más importante para un revisor: lista lo que el plan **rechaza**
y la medición concreta que lo rechaza, para que no se vuelva a proponer.

---

## 1. Punto de partida: lo que ya existe (medido)

Esto ya está construido y verificado. **No es trabajo pendiente.** Si este plan
pidiera reconstruirlo, está mal.

| Pieza | Estado | Fuente |
|---|---|---|
| `app/dashboard_ds02.py` — 1.825 líneas, 5 pestañas, sidebar de simulación | Hecho | `app/dashboard_ds02.py:391-399` |
| Gráficos interactivos | Hecho — 7 `st.plotly_chart`, **cero** matplotlib en `app/` | `app/dashboard_ds02.py:497,1043,1149,1192,1246,1308,1723` |
| Caché offline (6.196 ventanas / 12.538 filas / 3 unidades) | Hecho | `app/cache/ds02_windows.parquet`, `app/cache/ds02_rows.parquet` |
| Cargadores cacheados sin TensorFlow | Hecho | `app/ui_data_loader.py:109-143` |
| Política de triage pura y decisión por límite inferior | Hecho | `app/ui_data_loader.py:145`, `app/ui_rules.py:96` |
| Pasada A del motor de reglas (R1/R9/R8/R7) | Hecho | `mia/reglas.py:195-204` |
| Gemelos registrados (motor externo puntuado y guardado) | Hecho | `app/twin.py`, clave `twins` |
| Ciclo de vida del hangar con decisión congelada | Hecho | `app/hangar.py:56` (`abrir`), `:116` (`revision`) |
| Entrada de datos del usuario (3 rutas: ejemplo, pegar, CSV) | Hecho | `app/dashboard_ds02.py:1432-1438` |
| Tema oscuro en configuración, sin CSS inyectado | Hecho | `.streamlit/config.toml` |
| `alt=` accesible en cada gráfico y tabla | Hecho | verificado por `tests/test_dss_ui.py` |
| Suite de pruebas | 22 tests en `tests/test_dss_ui.py` | `tests/test_dss_ui.py` |
| "Restablecer demo" (borra gemelos y hangar) | Hecho | `app/dashboard_ds02.py:969-982` |

**Conclusión:** el diagnóstico "la app es demasiado ingenieril para un público
externo" es correcto. La conclusión "hay que rehacer la interfaz" no lo es. El
trabajo real es un pulido de entrada, no una reestructuración.

---

## 2. Reglas de oro (invariantes, con su fuente)

Cada una está impuesta por código o por decisión arquitectónica. Violarlas rompe
algo que ya se verificó.

**G1 — `models/` y `src/ds02_rul/` son de solo lectura.**
Lo garantiza `test_reading_the_ui_leaves_the_frozen_artifacts_untouched`
(`tests/test_dss_ui.py:216`). Ninguna tarea de este plan escribe ahí.

**G2 — El tema vive en `.streamlit/config.toml`, no en CSS.**
`tests/test_dss_ui.py:292` (`test_no_css_is_injected_into_the_app`) busca
`unsafe_allow_html` y `<style` en el código de la app. **Cualquier tarjeta
estilizada con HTML crudo falla ese test.** El tema define base `#0b1220`,
superficie `#141d2e` y dos paletas de 10 colores.

**G3 — Cada gráfico y tabla lleva un `alt` no vacío.**
`tests/test_dss_ui.py:260`. Todo lo nuevo debe llevarlo.

**G4 — Las métricas se recalculan de la caché, nunca se hardcodean.**
Requisito "Live metrics from cached predictions" en
`openspec/specs/ds02-dss-ui/spec.md`. La caché da RMSE 4,2892 · MAE 3,1792 ·
macro-RMSE 4,9026; por motor U11 3,7728 · U14 8,175 · U15 2,76
(`app/cache/cache_manifest.json:74-82`). El manifiesto se muestra aparte,
etiquetado como contrato congelado.

**G5 — La decisión la toma el límite inferior conformal, con umbrales 30 / 25.**
`docs/decisions/ADR-008-conformal-lower-bound-triage.md`. Los umbrales por
defecto están en `app/cache/cache_manifest.json:176-179`
(`threshold_airworthy: 30.0`, `threshold_aog: 25.0`).

**G6 — El motor de reglas es el que es. No se inventan reglas.**
`mia/reglas.py:187-204`:

```
REGLAS_CORRECCION  R2b_ISOTONICO_CAUSAL (2) · R6_BANDA (1)
REGLAS_DECISION    R1_SEGURIDAD (10) · R9_HANGAR (3) · R8_INSPECCION (2) · R7_APTO (1)
```

No existe R3, R4 ni R5 en ninguna parte del repo. La UI no reclasifica: pregunta
al motor (`app/ui_rules.py:96-122`).

**G7 — La integridad metodológica es el principal activo ante un tribunal.**
El repo publica lo que no sabe ("sin ground truth no se declara RMSE"), declara
hipótesis refutadas ("la densidad no explica el error") y no inventa valores
("no se dibuja una barra vacía ni se inventa un valor"). Cualquier cambio que
introduzca un número sin fuente o un dato manipulado destruye exactamente eso.

---

## 3. Cambios propuestos

### C1 — Formulario de alta rápida en el sidebar

**Qué es.** Un bloque compacto al inicio de la sidebar para incorporar una unidad
a la vista de flota con dos interacciones, en lugar de navegar hasta la quinta
pestaña. Reutiliza por completo la ruta de entrada existente.

**Qué NO es.** No fabrica telemetría, no inyecta offsets en sensores, no modifica
`app/ui_inference.py` ni el modelo. La unidad "nueva" es una lectura distinta de
la caché ya existente.

**Ficheros.**

- Crear `app/ui_alta.py` — mapeo puro perfil → (unidad, ciclo), sin Streamlit,
  para poder probarlo sin levantar la app (misma convención que `app/twin.py` y
  `app/hangar.py`: no importan Streamlit).
- Modificar `app/dashboard_ds02.py:184-241` (bloque `with st.sidebar:`) para
  añadir el formulario.

**Perfiles y sus cifras medidas.** Cada preset recorta la serie de una unidad ya
cacheada. Las bandas son las de G5. La decisión por ciclo es la de la ventana más
restrictiva (menor `lower`), que es lo que hace
`app/ui_rules.estado_por_ciclo:125-131`.

| Perfil | Unidad | Ciclo | `L_inf` | Estado |
|---|---|---|---|---|
| Recién salido de revisión | U11 | 1 | 35,41 | APTO |
| Recién salido de revisión | U15 | 2 | 35,43 | APTO |
| Desgaste operativo medio | U11 | 20 | 29,28 | INSPECCIÓN |
| Desgaste operativo medio | U14 | 20 | 29,20 | INSPECCIÓN |
| Fin de vida / crítico | U14 | 29 | 23,29 | HANGAR |
| Fin de vida / crítico | U11 | 22 | 24,85 | HANGAR |
| Caso atípico | U14 | 3 | 32,43 | APTO |

El último perfil es el que el plan original destacaba. Dos advertencias, medidas:

* **U14 no tiene ventanas en los ciclos 1 y 2.** Su primer ciclo puntuado es el
  **3** (`L_inf` 32,43). El ciclo 1 no existe para esta unidad: un preset que lo
  pida no falla en silencio, lanza `ValueError` desde `ventanas_de_alta`, pero es
  una trampa en la que no hay que caer.
* **U14 no llega a HANGAR hasta el ciclo 29**, con una RUL real de 47 ciclos en ese
  momento. Si la demo quiere mostrarlo ya en rojo, hay que elegir el ciclo 29 o
  superior.

Del mismo modo, **U15 empieza en el ciclo 2**: no tiene ciclo 1.

**Campos del formulario.**

- `Matrícula / etiqueta` — texto libre, mínimo 3 caracteres (reutilizar la
  validación de `app/twin.py:26`, `MIN_ID`).
- `Perfil de desgaste` — selector con los presets de arriba, en lenguaje de
  negocio.
- Botón `Incorporar unidad` — guarda en `st.session_state` y redirige a la pestaña
  de flota.

**Dónde vive el estado.** La etiqueta se guarda junto al gemelo o registro
existente, **no** en una lista nueva `flota_hangar` (no existe y rompería la
persistencia de `app/registros_flota.json`). Si la etiqueta solo se muestra, basta
`st.session_state`; si debe sobrevivir a una recarga, va en `app/twin.py` junto al
gemelo.

**Verificación.**

1. Test unitario de `app/ui_alta.py`: para cada preset, el `L_inf` cae en la banda
   que declara.
   `pytest tests/test_ui_alta.py -v`
2. Test de contrato: la etiqueta no modifica `models/`, `src/` ni `mia/`.
3. `AppTest` en `tests/test_dss_ui.py`: pulsar el botón cambia la vista y añade una
   fila a la cola de flota.
4. `pytest tests -q` — nada se rompe.

**Riesgo:** bajo. No toca el camino de inferencia.

---

### C2 — Modo demo en un clic

**Qué es.** Un botón que deja la aplicación en el estado exacto desde el que se
cuenta la historia, sin que el presentador tenga que acordarse de tres ajustes.

**Qué NO es.** No reentrena nada ni toca la caché. Solo pone widgets.

**Estado que debe dejar.**

- Umbrales en **30 / 25** (los de G5, no otros).
- Reloj de flota en **ciclo 29**, que es donde U14 cruza a HANGAR.
- Unidad seleccionada en **U14**, el caso con más historia: empieza APTO (ciclo 1,
  `L_inf` 32,43), pasa por INSPECCIÓN (ciclo 8) y llega a HANGAR en el ciclo 29 con
  **47 ciclos de RUL real restantes**.
- Flota registrada restaurada al estado inicial (gemelos y hangar vacíos), que ya
  hace hoy el bloque de `app/dashboard_ds02.py:969-982`.

**Ficheros.** `app/dashboard_ds02.py`, junto al bloque de restablecimiento
existente. La lógica de "qué estado es el de demo" va en `app/ui_alta.py` como
función pura, para poder probarla sin Streamlit.

**Por qué el ciclo 29 y no otro.** Es el cruce medido de U14. Es exactamente "un
avión a punto de entrar en zona crítica", y encima es el motor cuyo sesgo (−5,14)
explica por qué la banda lo inmoviliza pronto. Es el mejor argumento de la demo,
no un inconveniente.

**Verificación.**

1. Test puro: la función devuelve umbrales 30/25, ciclo 29, unidad 14.
2. `AppTest`: pulsar el botón deja esos tres valores en el estado de los widgets.
3. El KPI de unidades en hangar pasa a 1.

**Riesgo:** bajo.

---

### C3 — Panel de primera lectura

**Qué es.** Tres métricas y una frase, arriba del todo y antes de las pestañas,
para que un visitante se lleve el mensaje sin leer ingeniería.

**Contenido, con su fuente real.**

- **Unidades monitorizadas:** 3, con 6.196 ventanas evaluadas
  (`app/ui_data_loader.py:288`, `global_metrics`).
- **MAE en zona crítica** (RUL real < 25): 1,13 ciclos
  (`app/ui_data_loader.py:326`, `critical_zone_mae`).
- **Unidades en hangar ahora mismo:** se recalcula con el reloj
  (`app/dashboard_ds02.py:426-431`).

Y una frase que diga la idea en una línea: la decisión de inmovilizar no la toma la
predicción, la toma el peor caso de la banda. Esa frase es el argumento central de
ADR-008 y hoy está enterrada en el `st.info` de `app/dashboard_ds02.py:567-576`.

**Qué NO es.** No añade métricas nuevas ni números con otra fuente. Los tres
valores ya se calculan hoy; solo se suben de sitio y se redacta la frase.

**Ficheros.** `app/dashboard_ds02.py`, bloque de cabecera (`:368-389`). El panel de
KPIs de la pestaña 1 (`:404-431`) queda como está, sin duplicar la métrica de zona
crítica.

**Verificación.**

1. Las tres cifras del panel coinciden con las de la pestaña 1. Test que compare
   ambos orígenes.
2. Sigue pasando `test_every_chart_and_grid_has_an_accessible_name` (los
   `st.metric` nuevos no llevan `alt`, pero el panel no añade gráficos).
3. `pytest tests -q`.

**Riesgo:** muy bajo.

---

### C4 — Traducción de terminología (OPCIONAL, con riesgo explícito)

**Qué es.** Sustituir etiquetas crudas por etiquetas de negocio en la vista:
`U11` → `Motor DS02-11`, `corte de ventana` → `ciclos de vuelo acumulados`.

**Riesgo, y por qué es opcional.** El repo es deliberado al no inventar entidades:
la caché tiene **tres motores**, no aviones. Un A320neo, un 737 MAX 8 y un A350-900
son tres variantes de un mismo motor, y este dataset tiene **un solo turbofán**.
Presentar cada motor como un modelo de avión distinto es una afirmación que el
dataset no sostiene, y es exactamente el tipo de cosa que un tribunal técnico
detecta en un minuto.

**Regla para aceptar esta tarea.** Se permite un **alias de visualización** que sea
claramente una etiqueta (`Motor DS02-11`). **No** se permite: un modelo de avión por
motor, una matrícula inventada como identidad, ni ninguna cifra económica (ver
sección 4, R8).

**Ficheros.** `app/ui_data_loader.py:101-105` (`UNIT_LABELS`) y las cadenas de
`app/dashboard_ds02.py`. No toca las columnas de la caché ni `mia/`.

**Verificación.**

1. Test de que el alias no altera ningún dato: mismo recuento de unidades, mismos
   `unit_id` en la caché.
2. `pytest tests -q`.

**Recomendación:** hacer solo si C1–C3 no bastan para que el tribunal entienda la
pantalla. Es cosmética.

---

## 4. Rechazado explícitamente (con la medición que lo rechaza)

Cada rechazo está medido sobre la caché real. No es una opinión.

### R1 — Umbrales ROJO ≤ 15 / AMARILLO ≤ 35 / VERDE > 35

**Rechazado.** Con VERDE en `> 35` solo el **5,58 %** de las 6.196 ventanas es verde,
y **U14 es verde en 13 de 760 ventanas (1,7 %)**: el caso estrella del plan original
estaría permanentemente en rojo. Además, la propuesta de "2 aviones en VERDE
óptimos" es imposible con esos umbrales.

Los umbrales reales no están donde el plan original decía: `mia/reglas.py` no
contiene ningún umbral; están en ADR-008 y en `app/cache/cache_manifest.json:176-179`.

### R2 — Reglas R1 Aceleración de daño / R2 Pendiente EGT / R3 Discrepancia de
ramas / R4 Criterio de parada / R5 Coste económico

**Rechazado.** No existen. El motor tiene exactamente seis reglas, listadas en G6.
Proponer reglas nuevas en la UI, o "explicar" reglas que el motor no tiene, es
mostrar al tribunal un comportamiento que el sistema no implementa.

### R3 — Métricas RMSE 4,35 ± 0,10 · MAE 3,22 · R² 0,946 · NASA 2347,7
y por motor 2,88 / 3,72 / 8,04

**Rechazado.** Esas cifras vienen del informe del cuaderno, no del manifiesto. Los
valores congelados y los vivos son los de G4, y el NASA Score registrado en
`models/ds02_manifest.json` es **2310,6**, no 2347,7. Esto ya se corrigió una vez:
`openspec/changes/2026-10-21-ds02-streamlit-dss/proposal.md:26` lo documenta como
blocker B3.

### R4 — Migrar los gráficos de Matplotlib a Plotly

**Rechazado.** No hay matplotlib en `app/`. Los 7 gráficos ya son Plotly. Trabajo
inexistente.

### R5 — Inyectar un offset en los sensores para forzar la caída del RUL

**Rechazado de plano.** Es fabricar datos para controlar la salida del modelo. Es lo
único del plan original que ataca directamente el activo principal del proyecto ante
un tribunal (G7). Si alguien propone "perturbación en vivo", "offset térmico" o
"ajustar el corte para que se vea la caída", se rechaza sin discusión: **la
perturbación se hace eligiendo el ciclo de la caché, no tocando los sensores.**

### R6 — Un slider de "avance de vuelos" por avión

**Rechazado.** Existe un único reloj de flota (`app/dashboard_ds02.py:197-207`) y es
deliberado: es el calendario compartido, lo usan las órdenes de trabajo y
`app/hangar.py`, y clampa las unidades cortas en vez de extrapolarlas. Sustituirlo
rompería el contrato de `hangar.revision()` y la comparabilidad entre unidades.

### R7 — `render_turbofan_svg()` dentro de `app/twin.py`

**Rechazado.** `app/twin.py` ya existe y es el modelo de datos de los gemelos
(motores externos puntuados), no un renderizador. Además, el plan original llama
"Gemelo Digital del Motor" a una vista distinta de lo que el repo ya llama gemelo.
Dos conceptos con el mismo nombre en la misma app. Si se quiere el diagrama SVG, va
en un módulo nuevo, y con el riesgo de G2: un `unsafe_allow_html` falla el test de
tema.

### R8 — Cifras económicas (150.000 € AOG / 18.000 € preventivo / 132.000 € ahorrados)

**Rechazado.** No existen en ningún fichero del repo: aparecen únicamente en el plan
original. Pintar euros inventados en una defensa es un riesgo de credibilidad
innecesario y contradice G7. Si el tribunal pregunta por dinero, la respuesta
honesta es que este proyecto mide ciclos de vida, no euros.

### R9 — Matrículas (EC-NTF, IB-3402, LH-891) y modelos (A320neo, 737 MAX 8, A350-900)

**Rechazado** como identidad. Ver C4: etiqueta de visualización sí, entidad nueva no.
El dataset tiene un solo motor; asignar tres modelos de avión es una afirmación que
el dataset no sostiene.

---

## 5. Fuera de alcance

- Cambiar el motor de reglas, añadir reglas o reimplementar la decisión en la UI.
- Cambiar los umbrales por defecto 30 / 25.
- Cambiar la agregación de la decisión (ver la nota de la sección 6.3 sobre el
  parpadeo).
- Tocar `app/ui_inference.py`, `app/ui_data_loader.py` (salvo `UNIT_LABELS` en C4) o
  `app/cache/`.
- Añadir dependencias nuevas. C1–C3 no necesitan ninguna.

---

## 6. Verificación

### 6.1 Comandos

```bash
# suite completa
pytest tests -q

# solo lo nuevo
pytest tests/test_ui_alta.py -v
pytest tests/test_dss_ui.py -v

# la app arranca sin excepción
./.venv/Scripts/python.exe -m streamlit run app/dashboard_ds02.py --server.headless true
```

### 6.2 Guards que deben seguir verdes

Estos tests existentes son la red de seguridad. Si alguno falla, el cambio está mal:

| Test | Qué impide |
|---|---|
| `tests/test_dss_ui.py:292` `test_no_css_is_injected_into_the_app` | C1–C4 con CSS crudo (G2) |
| `tests/test_dss_ui.py:260` `test_every_chart_and_grid_has_an_accessible_name` | gráficos nuevos sin `alt` (G3) |
| `tests/test_dss_ui.py:216` `test_reading_the_ui_leaves_the_frozen_artifacts_untouched` | escribir en `models/` (G1) |
| `tests/test_dss_ui.py:51` `test_airworthy_state_is_reachable_on_this_band` | cambiar los umbrales (G5) |
| `tests/test_dss_ui.py:203` `test_no_fd001_artifact_is_referenced` | mezclar artefactos FD001 |
| `tests/test_dss_ui.py:209` `test_ui_does_not_reimplement_the_model` | reimplementar inferencia |
| `tests/test_dss_ui.py:114` `test_metrics_are_recomputed_from_the_cache` | hardcodear métricas (G4) |
| `tests/test_dss_ui.py:299` `test_the_cycle_slider_drives_the_grounded_kpi` | romper el reloj de flota (R6) |

### 6.3 Nota sobre el parpadeo del semáforo (no es una tarea de este plan)

Medido sobre la caché: la decisión por ciclo se lee de la **ventana más restrictiva**
de ese ciclo (`app/ui_rules.estado_por_ciclo:125-131`), así que el estado oscila en
los bordes. Transiciones reales de U11: APTO→INSPECCIÓN en c6, vuelve a APTO en c8,
INSPECCIÓN en c9, APTO en c17, INSPECCIÓN en c20, HANGAR en c22. U14: c8, c14, c20,
c29. U15: c9, c16, c18, c25.

Es un comportamiento **honesto** (un ciclo es la peor de sus ventanas) y hoy ya
tiene su explicación en pantalla. Cambiar la agregación sería cambiar la decisión,
lo cual está fuera de alcance. Si molesta en la demo, la vía correcta es una nota que
lo explique, no suavizar la serie.

---

## 7. Cómo reproducir cada cifra de este plan

```bash
# Umbrales por defecto y métricas
cat app/cache/cache_manifest.json

# Reglas del motor (ver G6)
sed -n '186,206p' mia/reglas.py
```

Escala de la banda:

```bash
./.venv/Scripts/python.exe -c "
import pandas as pd
w = pd.read_parquet('app/cache/ds02_windows.parquet')
print('max L_inf :', round(float(w['lower'].max()), 2))
for t in (15, 25, 30, 35, 50):
    print(f'L_inf >= {t:2d}: {int((w.lower>=t).sum()):5d} de {len(w)}')
"
```

Resultado esperado:

```
max L_inf : 36.5
L_inf >= 15:  3869 de 6196
L_inf >= 25:  2399 de 6196
L_inf >= 30:  1306 de 6196
L_inf >= 35:   346 de 6196   -> 5,58 %
L_inf >= 50:     0 de 6196
```

Decisión por ciclo (ventana más restrictiva) y transiciones de estado:

```bash
./.venv/Scripts/python.exe -c "
import pandas as pd
w = pd.read_parquet('app/cache/ds02_windows.parquet')
idx = w.groupby(['unit','cycle'])['lower'].idxmin()
pc  = w.loc[idx,['unit','cycle','lower']].sort_values(['unit','cycle'])
def banda(v): return 'APTO' if v>=30 else ('INSPECCION' if v>=25 else 'HANGAR')
for u,g in pc.groupby('unit'):
    g = g.reset_index(drop=True)
    b = g['lower'].map(banda)
    saltos = g[b != b.shift()].assign(s=b)
    print(f'U{u}: ciclo1 L_inf={g.lower.iloc[0]:.2f} -> {b.iloc[0]} | vida {int(g.cycle.max())}')
    print('   ', [f'c{int(r.cycle)}->{r.s}' for r in saltos.itertuples()])
"
```

Resultado esperado:

| Unidad | Ciclo 1 | APTO | INSPECCIÓN | HANGAR |
|---|---|---|---|---|
| U11 (vida 59) | APTO, `L_inf` 35,41 | 1–19 | 6–21 | 22–59 |
| U14 (vida 76) | APTO, `L_inf` 32,43 | 3–19 | 8–28 | 29–76 |
| U15 (vida 67) | APTO, `L_inf` 35,43 | 2–17 | 9–24 | 25–67 |

Si cualquiera de estos números sale distinto, el repo ha cambiado y este plan queda
desactualizado: **no se ejecuta hasta recalcularlo.**

---

## 8. Riesgos y preguntas abiertas

**Riesgos.**

1. **C4 es cosmética y tiene un riesgo de credibilidad.** Es la única tarea que
   puede salir mal ante un tribunal. Recomendación: dejarla para el final y
   descartarla si C1–C3 bastan.
2. **C1 puede acabar duplicando la pestaña 5.** El formulario del sidebar y la
   pestaña "Evaluar unidad nueva" deben compartir el mismo validador
   (`app/ui_inference.py`), no tener dos caminos. Si C1 crea un segundo validador,
   el cambio está mal.
3. **El estado de demo de C2 es frágil** si cambia la caché: fija el ciclo 29 por
   una medición concreta. Si `app/cache/` se regenera, hay que re-verificarlo con la
   sección 7.
4. **La persistencia.** Si la etiqueta de C1 debe sobrevivir a una recarga, toca
   `app/twin.py` y `app/registros_flota.json`, y `tests/conftest.py` limpia ese
   fichero en cada test. Un campo nuevo en el gemelo obliga a revisar
   `tests/test_twin.py`.

**Preguntas abiertas.**

1. ¿Quién es la audiencia real de la demo: tribunal académico, mixto, o cliente
   MRO? Cambia cuánto interesa C4.
2. ¿Hay cifras económicas reales disponibles (coste de AOG, coste de intervención
   preventiva)? Si existen y vienen de una fuente del proyecto, R8 podría
   reabrirse con su fuente; si no, se queda cerrado.
3. ¿La demo se hace con el portátil del presentador o en un equipo del tribunal?
   Determina si la caché de 2 MB es suficiente o hace falta algo más.
