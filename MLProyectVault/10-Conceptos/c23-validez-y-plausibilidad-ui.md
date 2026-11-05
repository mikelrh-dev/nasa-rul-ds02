---
tipo: concepto
status: consolidado
tags:
  - ui
  - validacion
  - contrato
---

# Validez y plausibilidad en la UI — lo puntuable vs lo avisado

> [!abstract] En una frase
> La UI rechaza lo impuntuable con error y avisa lo puntuable-pero-raro sin bloquear: confundirlos es o puntuar basura o bloquear taller.

## La idea

Dos filtros distintos con dos políticas distintas:

1. **Validez (`ui_inference.validate_table`)**: contrato duro del bundle. 50 filas mínimo (`window_size` de `cache/provenance`), orden exacto `cycle + 18 canales`, numérico finito (rechaza NaN/inf/coma europea `3,2`), `cycle` no decreciente. Si falla, `ValueError` con columna y fila. No adivina: `reordenar_columnas` es botón explícito, nunca silencioso.
2. **Plausibilidad (`ui_inference.plausibility_warnings`)**: aviso blando. Envelope observado DS02 ±5% por canal (`observed_envelope` desde `ds02_rows.parquet`). Mach 49 o psia en Pa puntúan pero avisan fuera de dominio. `cycle` único avisa tendencia plana. Nunca bloquea.

## Dónde aparece en este proyecto

- `app/ui_inference.py:295 validate_table`, `:232 plausibility_warnings`, `:140 observed_envelope`, `MAX_FILAS 5000 / UMBRAL_RECORTE 1500`
- `tests/test_live_eval.py`: orden, columnas, inf/NaN, coma europea, cycle decreciente
- Trazabilidad: `twin.fingerprint` SHA-256 CSV en contrato, viaja a orden y gemelo

> [!warning] La trampa
> «Puntúa igual, luego vale igual»: un `inf` llega al EMA causal y corrompe todas las ventanas posteriores. Por eso validez falla alto y plausibilidad solo avisa.

## Di esto en el tribunal

> [!quote]
> «Rechazo lo que el bundle no puede puntuar con columna y fila, y aviso lo puntuable fuera de dominio sin bloquear. Un infinito no es un dato raro: es una corrupción del EMA.»

## Flashcards

> [!question]- ¿Qué rechaza validate_table?
> Menos de 50 filas, orden cambiado, NaN/inf/coma europea, cycle decreciente. Con columna y fila.

> [!question]- ¿Qué hace plausibilidad?
> Avisa fuera de envelope DS02 ±5% sin bloquear. Puntuar fuera de dominio se dice, no se esconde.
