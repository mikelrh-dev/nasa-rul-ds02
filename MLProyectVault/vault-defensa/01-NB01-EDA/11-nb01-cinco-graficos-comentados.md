---
title: NB01 · Cinco gráficos comentados
course: Reto 1 · SAA+PIA+MIA
block: 01 — NB01 EDA
node: B1.2
indicador: SAA-4
descriptor: 10
spine: true
status: en-curso
tags:
  - nb01
  - graficos
  - rubrica/saa-4
---

# NB01 · Cinco gráficos comentados

> [!abstract] En una frase
> La rúbrica no pide gráficos: pide **cinco tipos** y que debajo de cada uno esté escrito qué
> ves y qué decisión sale de ahí. Aquí cada figura termina en una decisión de modelado.

## Los cinco, con su lectura

| # | Tipo | Archivo | Qué veo | Conclusión de modelado |
|---|---|---|---|---|
| 1 | Barras | `resultados/eda_barras_fase.png` | El crucero domina; despegue y descenso son colas | La fase es una variable real, no ruido: entra como categórica |
| 2 | Histograma | `resultados/eda_hist_rul.png` | RUL concentrado en valores bajos y cola larga | Métricas simétricas castigan la cola: usar RMSE y mirar el macro |
| 3 | Boxplot | `resultados/eda_box_t48_fase.png` | T48 se separa por fase | Sin fase, el modelo aprendería «pilotaje» en vez de degradación |
| 4 | Dispersión | `resultados/eda_scatter_alt_mach.png` | Altitud y Mach forman regímenes, no una nube | Hay que residualizar sensores sobre condiciones operativas |
| 5 | Heatmap | `resultados/eda_heatmap_corr.png` | Sensores correlados entre sí; RUL correlaciona débil con lo instantáneo | Una fila no basta: hace falta ventana |
| 6 | Extra | `resultados/eda_t48_resid_fase.png` | Tras residualizar, T48 ya no depende de la fase | La residualización limpia el efecto operativo |

## Por qué se dice así

- El 7 son «3 o 4 gráficos comentados»; el 10 exige los cinco tipos. Se enseñan los cinco y el
  sexto como cierre.
- Cada figura **cambia una decisión**: fase (one-hot), ventana (secuencia), residualización,
  métrica. Eso convierte el EDA en argumento, no en decorado.
- La conclusión 5 es la que justifica todo el resto de la defensa: si una fila bastara, no
  habría BiLSTM.

## Evidencia

- Notebook: `notebooks/01_eda_y_contexto.ipynb` — cada figura tiene su bloque `QUÉ VEO` y
  `CONCLUSIÓN` escrito en Markdown.
- Los seis PNG están versionados en `resultados/`.

## Pregunta probable

**«¿El heatmap no demuestra que sobra un sensor?»**
→ «Demuestra que están correlados, que no es lo mismo. Quitar uno por correlación alta es una
decisión que se prueba, no que se asume; la ablación que sí probamos es la del reloj
(`cyc_norm`), y ahí el resultado fue distinto por rama.»

## Lo que NO digo

- No digo «hice muchos gráficos»: digo cinco tipos y qué decisión salió de cada uno.
- No presento correlación como causalidad: el heatmap describe el dataset, no el motor.

## Di esto en el tribunal

> «Cada gráfico termina en una decisión: la fase entra como categórica, la ventana es
> obligatoria, los sensores se residualizan y la métrica tiene que mirar el motor 14.»

## Flashcards #flashcards

- ¿Qué cinco tipos exige la rúbrica? :: barras, histograma, boxplot, dispersión y heatmap.
- ¿Qué decisión sale del boxplot de T48 por fase? :: que la fase debe entrar al modelo o aprendería pilotaje.
- ¿Qué decisión sale del heatmap? :: que una fila no basta y hace falta ventana.
