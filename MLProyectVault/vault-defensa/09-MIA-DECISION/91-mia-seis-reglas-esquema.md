---
title: Esquema — Las seis reglas
course: Reto 1 · SAA+PIA+MIA
block: 09 — MIA decisión
node: D2
type: esquema
status: en-curso
tags:
  - esquema
  - reglas
---

# Esquema — Las seis reglas

> Nota de repaso rápido. Teoría completa: [[91-mia-seis-reglas]]

## La idea en una frase
> La predicción no decide: decide una regla con prioridad, porqué y una de seguridad que manda.

## Las piezas
| Regla | Prioridad | Efecto |
|---|---|---|
| R1 seguridad | 10 | dato inválido → no se decide |
| R9 hangar | 3 | `L_inf < 25` |
| R8 inspección | 2 | 25 ≤ `L_inf` < 30 |
| R7 apto | 1 | `L_inf ≥ 30` |

## El flujo
```mermaid
flowchart TD
    A["Predicción + L_inf"] --> B{"¿dato imposible?"}
    B -->|sí| C["R1 SEGURIDAD<br/>no se decide"]
    B -->|no| D["R9 HANGAR<br/>L_inf < 25"]
    D --> E["R8 INSPECCIÓN<br/>25–30"]
    E --> F["R7 APTO<br/>>= 30"]
    C --> G["registro con porqué"]
    D --> G
    E --> G
    F --> G
```
Fuente: [[visuals/decision-reglas]]

## Sí / No
- ✅ seis reglas, ni una de adorno.
- ❌ `L_inf` no es una probabilidad.
- ❌ R2b no demuestra monotonía: corrige una tendencia.

## Flashcards #flashcards
- ¿Qué prioridad tiene la regla de seguridad? :: 10, la máxima.
- ¿Qué umbrales separan los estados? :: 25 hangar, 25–30 inspección, 30 apto.

## Estado
- [ ] En curso
