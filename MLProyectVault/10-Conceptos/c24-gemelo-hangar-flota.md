---
tipo: concepto
status: consolidado
tags:
  - gemelo
  - hangar
  - flota
  - operacion
---

# Gemelo, hangar y flota — del veredicto al registro

> [!abstract] En una frase
> El modelo dice RUL, las reglas dicen estado, el gemelo lo firma por motor, el hangar dice qué pasó después y la flota lo guarda por sesión.

## La idea

Cadena operativa en 4 eslabones, cada uno con dueño:

1. **Gemelo (`app/twin.py:60 make_twin/registrar`)**: congela resultado + contrato (ventana, artefacto SHA, fingerprint CSV, umbrales, banda) en documento auditable. Sin gemelo no hay trazabilidad.
2. **Flota (`app/flota.py:99 registrar_alta`)**: registro de matrículas y altas. Puro libro, no decide.
3. **Hangar (`app/hangar.py:57 permitidas`)**: máquina de estados. Solo transiciones legales. Guarda la decisión que abrió el registro con umbrales vigentes; `revision()` dice qué diría la política actual sin reescribir historia.
4. **Sesión (`hangar.session_registry_path`, `registros_flota_sesion*.json`)**: cada sesión de navegador tiene su fichero. Legacy `registros_flota.json` se copia una vez por sesión, nunca se mueve. Sin fichero, memoria con error visible.

## Dónde aparece en este proyecto

- `app/twin.py`, `app/flota.py`, `app/hangar.py`, `app/ui_alta.py:92 estado_historia`
- `tests/test_twin.py`, `test_hangar.py`, `test_flota.py`, `test_fleet_registries_session.py`
- DSS: `s23-dss-por-pestanas`, recorrido `n04-cadena-de-estado`

> [!warning] La trampa
> «El hangar decide»: no. Decide `src/mia/` sobre `L_inf`. El hangar cuenta qué pasó después. Mezclarlos es pedirle al libro que opine.

## Di esto en el tribunal

> [!quote]
> «Veredicto con reglas, gemelo que lo firma, flota que lo guarda por sesión y hangar que solo permite transiciones legales sin reescribir historia.»

## Flashcards

> [!question]- ¿Quién decide y quién registra?
> Reglas deciden estado; gemelo firma; flota guarda; hangar mueve estados legales por sesión.
