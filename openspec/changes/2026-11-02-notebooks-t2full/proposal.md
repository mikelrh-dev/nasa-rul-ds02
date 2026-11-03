# T2-full: reentrenar todo en notebooks 01-05 (estilo ds02_ensemble/01-03)

## Objetivo
Que 01-05 cuenten el proceso completo con código que entrena de verdad, sin salir
de `notebooks/`. Un estudiante de IA/ML puede explicar cada número señalando la
celda que lo calcula. `notebooks/ds02_ensemble/` no se toca (cuna auditable de B).

## Decisión (autorizada): T2 con aparato de estilo viejo
- 02/03/04 reentrenan en memoria (determinista: sklearn + seeds fijas).
- 05 reentrena C en memoria ( BiLSTM-42 + OOF/beta + meta + EMA + conformal +
  multiseed vivo ya existente). B aparece como referencia congelada + inferencia.
- Cero escrituras a `models/`, `track_clase/models/`, `resultados/*.csv` desde
  celdas nuevas (las figuras PNG a `resultados/` sí, están gitignoradas).
- Anclas exactas mueren donde el entreno las reemplaza; quedan las de
  manifest (deterministas) + notas de procedencia con la divergencia esperada
  (~4.35 vivo vs 4.251 congelado vs 4.338 manifest C).
- Cada notebook: glosario/TIP/cómo-leer/qué-vemos con números en negrita,
  baseline primero, regla de empate escrita (donde aplique).

## No-objetivos
- No tocar `notebooks/ds02_ensemble/`, `models/`, `src/`, `app/cache/`.
- No re-freezar bundles (requiere otro change).
- No MLflow ni n8n (change posterior).
- Sin commit.
