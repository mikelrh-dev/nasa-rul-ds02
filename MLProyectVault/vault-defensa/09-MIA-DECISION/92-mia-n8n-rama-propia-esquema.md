---
title: Esquema — n8n con acción propia
course: Reto 1 · SAA+PIA+MIA
block: 09 — MIA decisión
node: D3
type: esquema
status: en-curso
tags:
  - esquema
  - n8n
---

# Esquema — n8n con acción propia

> Nota de repaso rápido. Teoría completa: [[92-mia-n8n-rama-propia]]

## La idea en una frase
> La rama de hangar llama a nuestra API y registra la decisión: eso es la acción que no se vio en clase.

## Las piezas
| Pieza | Valor |
|---|---|
| Flujo | `n8n/flujo.json`, 15 nodos, webhook con `headerAuth` |
| Ramas | apto · inspección · hangar |
| Acción propia | `POST /n8n-decision` (`app/api.py:262`) |
| Protección | token compartido + idempotencia por `fingerprint` |
| Estado del repo | `active:false` por diseño |

## Sí / No
- ✅ «instancia local con 29 ejecuciones reales».
- ❌ «está en producción».
- ❌ «la app disparó el flujo» (no hay ejecución atribuible).

## Flashcards #flashcards
- ¿Qué hace distinta a la rama de hangar? :: llama a `POST /n8n-decision` de nuestra API.
- ¿Cómo evita duplicados? :: idempotencia por `fingerprint`.

## Estado
- [ ] En curso
