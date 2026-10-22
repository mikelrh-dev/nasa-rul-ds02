# Auditoría DS02 — ¿alguna reparación exige reentrenar?

**Fecha:** 2026-10-21 · **Alcance:** los 18 hallazgos de la auditoría del mismo día
(3 altos, 7 medios, 8 bajos). **Modo:** lectura y recomputación; sin ejecutar el
notebook, sin reentrenar, sin modificar código.

## Respuesta corta

**No. Ninguno de los 18 hallazgos requiere reentrenar los artefactos congelados**
(`models/ensemble.joblib`, `models/bilstm_ds02.keras`). Todos se reparan en capas
por encima del modelo: motor de reglas, aritmética de la banda, UI, gate, tests y
documentación.

Esta nota clasifica los hallazgos por capa de reparación; no reproduce el informe
completo. Los que deciden la respuesta se citan con fichero y línea; el resto
aparece agrupado por naturaleza, sin detalle individual.

## Por qué: la banda no la produce el modelo

La banda conformal se aplica **después** de la predicción puntual, con cuantiles
guardados:

- `src/ds02_rul/ensemble.py:161-176` — `predict_interval()` es `predict()` más
  `apply_conformal(point, self.conformal)`. No recalcula nada: consume el
  diccionario `self.conformal` que viaja en el bundle.
- `src/ds02_rul/conformal.py:90-106` — `apply_conformal()` suma `q_low` / `q_high`
  del tramo que corresponde al punto.
- `mia/reglas.py:94-97` — la misma aritmética con `mia/calibracion_banda.json`:
  `lower = min(punto + q_low, punto)` y `upper = max(punto + q_high, punto)`.
- `mia/calibracion_banda.json` — declara el método: `split-conformal, per
  predicted-RUL bin, asymmetric`, `debias: false`, 14 915 filas OOF puras y
  `"cache_origen": "_p1_oof_cache.npz"`.

Recalibrar es, por tanto, recalcular cuantiles sobre residuos ya existentes. La
predicción puntual no cambia, y con ella tampoco los pesos.

## Clasificación por capa de reparación

| Capa | Hallazgo | Dónde | ¿Reentrenar? |
| --- | --- | --- | --- |
| Gate | `--write` re-congela el JSON **antes** de comprobar la deriva | `scripts/freeze_rules_evidence.py:484-499` | No |
| Orden de trabajo | Documento sin procedencia de la regla; `live_work_order` decide con `classify`, no con `mia.motor` | `app/ui_inference.py:292-301` | No |
| Umbrales cableados | Alarma y MAE crítica con `25.0` literal aunque el operador mueva el slider | `app/dashboard_ds02.py:268,279` | No |
| Criterio de estado | Estado por `lower.min()` del ciclo, alarma por `lower` medio | `app/ui_data_loader.py:181,183,234` vs `first_alarm_cycle` | No |
| Calibración doble | Dos bandas para el mismo punto: artefacto y JSON | `models/ds02_manifest.json` vs `mia/calibracion_banda.json` | No |
| Tramos | Discontinuidad al cruzar 75 ciclos | `mia/calibracion_banda.json` (tramo 3, n=419) | No |
| Reproducibilidad | La caché OOF no viaja en el repo | `.gitignore:49`, `scripts/p1_oof_cache.py` | No (ver matiz 1) |
| Tests, specs y cifras | Ficheros de texto y de test | `tests/`, `openspec/`, `docs/informes/informe-2026-10-21-reglas-oof.md` | No |

### Detalle de las capas que importan

**Gate (`--write`).** `failures = _compare(...)` se calcula en la línea 482, pero
`_write_frozen()` se ejecuta en la 485 dentro de `if write:` y el `return
EXIT_DRIFT` llega en la 499. Resultado reproducido contra una copia temporal:
código de salida 4 **y** JSON modificado. Reparación: mover el bloque de escritura
detrás de la comprobación. Cinco líneas, ningún dato entrenado.

**Orden de trabajo.** `L.work_order` incluye `artefacto_sha256`, la ventana y los
umbrales, pero no la corrección aplicada, la fuente de banda ni la regla, así que
un JSON con el toggle encendido es indistinguible de uno apagado. Además
`live_work_order` usa `L.classify(lower, ...)`, una segunda implementación de la
misma política que no registra la regla aplicada; la divergencia es **latente**
(el botón de descarga está condicionado a `state == AOG`, así que un
`SIN_DECISIÓN` no llega a emitir documento), pero basta con que cambie una regla
para que el papel y la pantalla dejen de coincidir. Reparación: añadir campos y
llamar a `mia.motor`.

**Umbrales cableados.** `alarms = {u: L.first_alarm_cycle(curves[u], 25.0)}`
(`:268`) y `critical_mae = L.critical_zone_mae(windows, 25.0)` (`:279`) ignoran
`threshold_aog`, que sí usan la tabla de flota (`:896`) y la gráfica (`:598`). Con
aog 20/25/28 la alarma de U11 cae en ciclo 31/26/13. En la misma zona,
`per_unit_metrics(windows)` (`:272`) y la MAE crítica trabajan sobre `windows`
**sin corregir** mientras el estado se decide sobre `frame`: con el toggle
encendido la tabla mezcla lectura corregida y cruda. Reparación: pasar
`threshold_aog` y el frame vigente.

**Criterio de estado.** `unit_curve` agrega `lower` con **media** y guarda
`lower_min` aparte (`app/ui_data_loader.py:181,183`); `first_alarm_cycle` lee la
media, mientras `fleet_snapshot` decide con `lower.min()` (`:234`). Hubo 5 ciclos
en que el mínimo baja de 25 y la media no. Reparación: una sola definición,
explícita en la UI. Es una decisión de producto, no de modelo.

**Calibración doble.** Mismo punto, dos bandas:

| Fuente | lower | upper |
| --- | --- | --- |
| `models/ds02_manifest.json` (crudo y evaluación en vivo) | 17.3383 | 47.8451 |
| `mia/calibracion_banda.json` (R6, toggle encendido) | 20.0992 | 47.5024 |

Los cuantiles difieren tramo a tramo (tramo 0: `-5.6452/7.2864` contra
`-4.1928/7.1817`; tramo 3: `-25.7569/-17.4921` contra `-21.2133/-15.3651`), y el
bloque `conformal` del manifiesto es **idéntico** al diccionario del bundle
(`ens.conformal == man` → `True`): el manifiesto sí registra la banda que usa el
artefacto, la divergencia es real y no un desajuste de documentación.
Sobre las 6 196 ventanas la banda del artefacto es 2.098 ciclos más baja de media
y 915 ventanas (14.8 %) cambian de estado con 30/25. Reparación: declarar la
fuente o unificar. Recalcular cuantiles desde la caché OOF, no reentrenar.

**Discontinuidad en 75.** 74.999 ciclos cae en el tramo 2 (`q_high +19.7588`) y
75.0 en el tramo 3 (`q_high -15.3651`, recortado al propio punto): el límite
superior se hunde ~19.8 ciclos al cruzar el borde, y el tramo 3 queda de una sola
cara. Reparación: recomputar o fusionar ese tramo (419 filas). Sin modelo.

## Matiz 1 — recalcular no es reentrenar, pero la caché no viaja en el repo

`_p1_oof_cache.npz` está ignorada por git (`.gitignore:49`, patrón `_p1_*.npz`).
Existe en local (195 870 bytes), así que aquí recalibrar es inmediato. En un clon
limpio no: habría que re-ejecutar `scripts/p1_oof_cache.py`, que llama a
`oof_base_predictions(..., epochs=15)` y **reajusta los tres folds**. Eso choca de
frente con la regla del repo (`openspec/config.yaml`: *"Do not retrain models in
CI; the suite reads `app/cache/` and `_p1_oof_cache.npz` only"*).

⇒ Cualquier fix que toque la calibración debe **emitir y versionar los cuantiles
resultantes**, no depender de recomputarlos en CI. Si no, la reparación introduce
un reentrenamiento encubierto en el camino de verificación.

## Matiz 2 — llevar la banda corregida al artefacto es reserializar

Si se prefiere que la banda corregida viaje dentro de `ensemble.joblib` (para que
crudo y corregido coincidan sin duplicar código), basta sustituir
`self.conformal`, que es un atributo guardado y solo se consume en
`predict_interval`. Los pesos de LSTM, GBM y meta no se tocan: es
reserialización, no reentrenamiento.

*No verificado en esta nota:* no se re-serializó un bundle, porque eso escribe en
`models/`; la afirmación se apoya en que `predict_interval` no recalcula los
cuantiles.

## Lo que sí exigiría reentrenar

Nada de lo anterior, pero conviene tenerlo escrito para no confundir deuda con
defecto:

- cambiar la ventana (50), el `step` o los 18 canales de entrada;
- cambiar la arquitectura, el objetivo cuantílico o los hiperparámetros;
- corregir una fuga de información hacia el modelo, si apareciera;
- **mejorar la precisión en zona crítica** (margen de tolerancia al 95 %). Esto es
  una limitación de calidad medida, no un defecto reparable: atacarla es modelado
  nuevo y queda fuera de esta auditoría.

## Cómo se comprobó

```bash
# el gate escribe antes de fallar
grep -n "if write:\|_write_frozen\|return EXIT_DRIFT" scripts/freeze_rules_evidence.py
# la orden externa no pasa por el motor
sed -n '292,301p' app/ui_inference.py
# umbrales cableados y frames mezclados
grep -n "first_alarm_cycle\|threshold_aog" app/dashboard_ds02.py | sed -n '1,6p'
# estado por mínimo, alarma por media
sed -n '176,186p' app/ui_data_loader.py; sed -n '230,236p' app/ui_data_loader.py
# la caché OOF no está versionada
git check-ignore -v _p1_oof_cache.npz
```

Contraste de la banda entre artefacto y reglas (ejecutable tal cual, desde la raíz):

```python
import json, sys
import numpy as np
sys.path.insert(0, "src")
from ds02_rul.conformal import apply_conformal
from ds02_rul.persistence import load_ensemble
import mia.reglas as R

man = json.load(open("models/ds02_manifest.json", encoding="utf-8"))["conformal"]
ens = load_ensemble("models/ensemble.joblib")
print("bundle.conformal == manifest['conformal']:", ens.conformal == man)

p = np.array([30.8385])
lo, hi = apply_conformal(p, man)
print(f"artefacto ({lo[0]:.4f}, {hi[0]:.4f})")
lo, hi = R.banda_recalibrada_vector(p, R.cargar_calibracion())
print(f"reglas    ({lo[0]:.4f}, {hi[0]:.4f})")
for x in (74.999, 75.0):
    lo, hi = R.banda_recalibrada_vector(np.array([x]), R.cargar_calibracion())
    print(f"punto {x}: reglas ({lo[0]:.2f}, {hi[0]:.2f})")
```

Salida observada:

```
bundle.conformal == manifest['conformal']: True
artefacto (17.3383, 47.8451)
reglas    (20.0992, 47.5024)
punto 74.999: reglas (53.32, 94.76)
punto 75.0: reglas (53.79, 75.00)
```

## Estado y limitaciones

- **Sin cambios de código:** la auditoría no modificó el repositorio.
- Es estática más recomputación sobre artefactos ya generados; no cubre el
  pipeline de entrenamiento ni los notebooks, que se tomaron como contrato.
- No mide rendimiento bajo carga concurrente del servidor.
- La nota clasifica y documenta. Los arreglos que no exigen reentrenar están
  implementados en `openspec/changes/2026-10-21-ds02-audit-fixes/`; las dos
decisiones de modelado (unificar la banda numéricamente y mejorar la zona
  crítica) siguen abiertas.
