---
title: Esquema Persistencia y notebooks (B)
course: DS02-RUL
block: B0 - Guion defensa B
node: N5
status: en-curso
tags:
  - esquema
---

# Esquema Persistencia y notebooks (B)

> Nota de repaso rapido. Teoria completa: [[00-persistencia-notebooks]]

## La idea en una frase

> Guardar 3 piezas + recargar identico.

## Las 3 piezas

| Pieza | Que es | Analogia |
|---|---|---|
| Bundle | joblib + scaler + keras | Caja con manual |
| Reload | Memoria == recargado | Fotocopia exacta |
| Viz | Helpers fuera del notebook | Caja de herramientas |

## El flujo

```mermaid
flowchart LR
    SAVE[save] --> RELOAD[reload OK]
```

## Si / No

- SI: Grafo por ruta, nunca picklado.
- NO: viz.py no se persiste en el bundle.

## Flashcards #flashcards

- 3 ficheros del bundle? :: ensemble.joblib + scaler.joblib + bilstm_ds02.keras.
- Import estilo clase? :: from ds02_rul.viz import *.

## Estado

- [ ] En curso
