# Anticipación al fallo en las unidades de validación ciega

**Fecha:** 24 de octubre de 2026
**Cifra:** 13, 23 y 18 ciclos de anticipación para las unidades 11, 14 y 15.
**Umbral:** 25,0 ciclos (ADR-008, el mismo que gobierna la decisión de hangar).

## Qué mide exactamente

No es un *backtest*. Es una sola resta, sobre las tres unidades de validación
ciega:

> **anticipación = ciclo en que la verdad cruza el umbral − ciclo en que la
> banda lo cruza**

La *alarma* es el primer ciclo en que el **límite inferior** de la banda
conformal (`lower_min`) cae por debajo de 25. Es la misma estadística que usa
`fleet_snapshot` para decidir el estado, así que la alarma y la decisión no
pueden discrepar.

La *verdad* es el primer ciclo en que la RUL real (`y_true`) cae por debajo de
25.

La resta dice cuánto antes avisa la banda que la vida real se agota.

## El comando

Se reproduce con `L.first_alarm_cycle`, que devuelve ambos ciclos juntos:

```bash
cd app && PYTHONPATH=. ../.venv/Scripts/python.exe -c "
import ui_data_loader as L
w = L.get_windows()
for u in sorted(int(x) for x in w['unit'].unique()):
    c = L.unit_curve(w, u)
    alarma, verdad = L.first_alarm_cycle(c, 25.0)
    print(f'U{u}: alarma {alarma}, verdad {verdad}, anticipacion {verdad-alarma}')
"
```

Salida verificada el 24 de octubre de 2026:

```
U11: alarma 22, verdad 35, anticipacion 13
U14: alarma 29, verdad 52, anticipacion 23
U15: alarma 25, verdad 43, anticipacion 18
```

## Qué no es

- **No es un backtest.** No hay protocolo de backtest en el proyecto, y llamarlo
  así invita a preguntar por uno que no existe.
- **No mide la bondad de la predicción.** Es la distancia entre dos cruces de un
  mismo umbral. El error de la predicción se mide aparte (MAE en zona crítica,
  macro-RMSE).
- **No es una garantía.** La banda está calibrada para cubrir el 90 % de las
  ventanas, no para predecir el ciclo exacto del fallo. Un motor puede cruzar la
  verdad antes de que su banda cruce el umbral.
- **Las tres unidades ya cruzaron.** Son datos congelados, no una predicción sobre
  motores vivos.

## Por qué importa

Es la cifra que responde a la pregunta que un tribunal técnico sí hace: *"¿y
esto avisa con tiempo suficiente para actuar?"*. La respuesta es 13, 23 y 18
ciclos según el motor: tiempo de sobra para planificar una revisión, que es
exactamente lo que un sistema de mantenimiento necesita y lo que un modelo que
solo acertara el número no daría.

## Cómo se citó antes

El informe de arquitectura (`docs/informe_estrat_gico_y_arquitectura_mro_ds02.md`)
mencionaba «13, 23 y 18 ciclos» sin decir de dónde salían. Ahora salen de aquí.
