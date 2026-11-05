---
tipo: notebook
status: sin-estudiar
tags:
  - nb01
  - eda
  - clase
  - saa
---

# NB01 — EDA del track de clase

> [!abstract] En una frase
> Este cuaderno mira los datos antes de modelar: calidad, nulos MAR, fase de vuelo y figuras que justifican cada decisión posterior.

## Antes de empezar

32 celdas. Requiere el HDF5 en `archive/CCMaps/N-CMAPSS_DS02-006.h5` y `pyproject.toml` en la raíz para fijar el `cwd`. Es EDA puro: rápido, sin entrenos. Cubre rúbrica SAA 1–5 (IA débil/supervisada, tabla de sensores, nulos, fase).

## Recorrido celda a celda

| Bloque | Qué entra | Qué hace | Qué sale |
|---|---|---|---|
| IA débil y supervisada | rúbrica SAA 1/2 | declara el tipo de IA por escrito | el sistema solo predice RUL de DS02 |
| Glosario rápido | vocabulario | tabla palabra → significado aquí | leer el notebook sin perderse |
| Tabla de campos + calidad | base downsampleada | campo, tipo, %nulos antes/después | T30 ~1.8% MAR → 0% tras ffill+mediana |
| Fig.1 barras fase_vuelo | train | reparto Ascenso 26% / Crucero 30% / Descenso 44% | la categórica tiene señal |
| Fig.2 histograma RUL | RUL | cola y rango | baseline 20.022 que calibra la escala |
| Fig.3 boxplot T48 por fase | sensor crudo | el sensor manda régimen | sin fase se aprende pilotaje (ADR-002) |
| Fig.4 alt vs Mach por fase | régimen | el plano se corta en bandas coherentes | justifica `fase_vuelo` |
| Fig.5 heatmap correlación | régimen + sensores + RUL | última fila/columna | qué sensor mira a la RUL |

Las cifras de calidad viven en `src/clase/README.md` (tabla «Nulos antes / Nulos después»).

## Las 5 celdas que importan

1. IA débil: la declaración SAA 1 que el tribunal quiere oír primero.
2. Tabla de campos: T30 MAR con patrón físico, no aleatorio.
3. Fig.1: la fase reparte la flota en tres regímenes desiguales.
4. Fig.3: T48 separada por fase, la prueba del pilotaje.
5. Baseline: la constante 38.08 con 20.022, el suelo de todo lo que sigue.

## Qué NO hace este cuaderno

No entrena nada, no parte por motor para modelar (eso lo hace cada track al construir su base), no elige modelos. NB01 mira y deja constancia.

## Si falla algo

Si el HDF5 no aparece, revisa `archive/CCMaps/N-CMAPSS_DS02-006.h5` y el `cwd` de la celda 1.

## Conexiones

- Nulos: [[c17-nulos-mar-e-imputacion-causal]] · fase: [[c18-fase-vuelo-y-onehot]] · IA débil: [[c21-shap-e-ia-debil]] · dataset: [[s15-dataset-de-clase]]
- Sigue en [[n02-recorrido-nb02]] (clásicos + MLP).

> [!quote] Di esto en el tribunal
> «En el primer cuaderno miro antes de modelar: declaro que es una IA débil supervisada, mido la calidad con T30 cayéndose en crucero alto, derivo la fase de vuelo y demuestro con el boxplot de T48 que sin fase el modelo aprendería pilotaje».

## Flashcards

> [!question]- ¿Qué demuestra la Fig.3 (T48 por fase)?
> Que el sensor crudo responde al régimen, no a la degradación: sin la fase como contexto, el modelo aprende a distinguir pilotaje en vez de salud (ADR-002).

> [!question]- ¿Qué deja NB01 para NB02?
> La base mirada y documentada (calidad, nulos, fase) más el baseline 20.022: el suelo contra el que compite cada modelo del siguiente cuaderno.
