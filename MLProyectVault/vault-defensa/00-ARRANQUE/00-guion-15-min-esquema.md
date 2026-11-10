---
title: Esquema — Guion de 15 minutos
course: Reto 1 · SAA+PIA+MIA
block: 00 — Arranque
node: A1
type: esquema
status: en-curso
tags:
  - esquema
  - guion
---

# Esquema — Guion de 15 minutos

> Nota de repaso rápido. Teoría completa: [[00-guion-15-min]]

## La idea en una frase
> El guion sigue el orden de los cuadernos y corta por el final: primero NB03, luego NB07 y NB05.

## Las piezas
| Tramo | Minutos | Qué se dice |
|---|---|---|
| Negocio | 0:00–1:15 | coste + IA débil |
| NB01 | 1:15–3:00 | datos, gráficos, nulos |
| NB02 | 3:00–5:00 | 5 modelos, MLP, elección |
| NB03 | 5:00–5:45 | ablación |
| NB04–05 | 5:45–7:15 | BiLSTM, OOF, banda |
| NB06–07 | 7:15–9:15 | cascada y SHAP |
| PIA | 9:15–10:45 | pipeline, MLflow, app |
| MIA | 10:45–13:30 | reglas y n8n |
| Cierre | 13:30–15:00 | límites |

## El flujo
```mermaid
flowchart LR
    A["0:00 negocio<br/>+ IA débil"] --> B["1:15 NB01<br/>datos"]
    B --> C["3:00 NB02<br/>5 modelos + MLP"]
    C --> D["5:00 NB03<br/>ablación"]
    D --> E["5:45 NB04-05<br/>BiLSTM + banda"]
    E --> F["7:15 NB06<br/>bundle C"]
    F --> G["8:30 NB07<br/>SHAP"]
    G --> H["9:15 PIA<br/>código"]
    H --> I["10:45 MIA<br/>reglas + n8n"]
    I --> J["13:30 cierre"]
```
Fuente: [[visuals/arco-15min]]

## Sí / No
- ✅ MIA y cierre no se cortan nunca.
- ❌ No se abre el portátil antes del minuto 13.

## Flashcards #flashcards
- ¿Qué se corta primero si falta tiempo? :: NB03, luego NB07 y NB05.
- ¿Qué no se corta? :: MIA y el cierre con límites.

## Estado
- [ ] En curso
