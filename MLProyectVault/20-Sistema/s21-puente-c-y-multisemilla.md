---
tipo: sistema
status: sin-estudiar
tags:
  - puente
  - multisemilla
  - scripts
---

# Puente C y multisemilla — los scripts que sostienen el número

> [!abstract] En una frase
> Dos scripts sin modelo nuevo: `puente_c.py` traslada la base al bundle y `evaluar_c_multisemilla.py` repite el protocolo en tres semillas.

## Contrato

| Entra | Sale |
|---|---|
| Base de clase + bundle C entrenado | Evidencia repetible: CSVs multiseed + comparativas |

## Cómo está implementado

| Pieza | Dónde | Qué hace |
|---|---|---|
| `puente_c.py` | `src/clase/puente_c.py` | conecta la base adaptada con el protocolo del bundle (sin reentrenar a ciegas) |
| `evaluar_c_multisemilla.py` | `src/clase/evaluar_c_multisemilla.py` | semillas [42, 7, 123] → `bundle_c_multiseed.csv` |
| `comparativa_bundle_c.csv` | `resultados/` | bundle C frente a bases, misma ventana de test |
| Ventanas adaptadas | `src/clase/ventanas_adaptadas.py` | ventanas de 50 sobre la base imputada |

Sin estos scripts, «4.322±0.064» sería una frase; con ellos, debería ser un CSV regenerable — pero el CSV en disco hoy **NO reproduce** la media impresa (7=4.429, 123=4.336 → 4.368, **NO reconciliada** per [[e00-cifras-autoritativas]]); la fila oficial es 4.338 (semilla 42).

## Conexiones

- Lectura del número: [[c20-multisemilla-y-ruido]] · el bundle: [[s20-ensemble-adaptado-y-bundle-c]] · cifras: [[e00-cifras-autoritativas]]

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «La media de tres semillas no está escrita a mano: sale de un script que cualquiera puede reejecutar, y los CSV están en resultados».

## Flashcards

> [!question]- ¿Qué garantizan puente_c y evaluar_c_multisemilla?
> Que el número multiseed es **impreso en NB05/NB06, no regenerable hoy desde el CSV** (CSV 4.368 pendiente de reconciliar per [[e00-cifras-autoritativas]]): el puente traslada la base al protocolo del bundle y el script de multisemilla repite [42, 7, 123] dejando los CSV en `resultados/`.
