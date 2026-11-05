---
tipo: concepto
status: sin-estudiar
tags:
  - negocio
  - mia
  - aog
  - coste
---

# Cuánto vale acertar — el negocio del taller

> [!abstract] En una frase
> Un AOG imprevisto cuesta 10.000–15.000 USD por hora; una inspección programada, una fracción: el modelo se paga evitando una sola parada al año.

## La idea

La métrica del taller no es el RMSE: es el coste de equivocarse en cada dirección. Un motor parado en pista (**AOG**, *aircraft on ground*) cuesta 10.000–15.000 USD/h (≈240.000–360.000 USD/día, rango Boeing, credibilidad media: `costes_reales_aeronauticos.md` §1, citado de forma secundaria). Una inspección programada cuesta una fracción. Por eso el sistema decide sobre el borde inferior conservador (`L_inf`), no sobre el punto: subestimar manda a inspección barata; sobreestimar deja un avión parado caro.

## La asimetría, en tres capas

1. **Métrica**: el NASA score ya castiga sobreestimar (1/10) más que subestimar (1/13) ([[c04-metricas-y-baseline]]).
2. **Decisión**: `L_inf ≥ 30` APTO, `25–30` INSPECCIÓN, `< 25` HANGAR ([[s13-capa-de-reglas-y-decision]]).
3. **Negocio**: cada HANGAR a tiempo es una parada imprevista menos; con una evitada al año, el sistema está pagado.

Esto es el criterio MIA de cuantificación: no «el modelo es bueno», sino «esto vale esto porque evita esto». Y el objetivo cabe en una frase: se predice RUL por motor, para decidir hangar a tiempo, y lo usa el jefe de taller (MIA-1: qué se predice, para qué y quién lo usa).

## Dónde aparece en este proyecto

- `src/clase/README.md` y `README.md` — sección «La necesidad de negocio» con la horquilla Boeing.
- `costes_reales_aeronauticos.md` §1 — fuente de los 10.000–15.000 USD/h.
- Lead time por motor 9/23/17: las horas de aviso que la pantalla convierte en plan ([[s14-app-y-despliegue]]).
- `docs/defensa_ds02_explicacion_logica_negocio.md` — la lógica de negocio completa.

> [!warning] La trampa
> «Ahorra X millones»: sin horquilla declarada ni credibilidad de la fuente, es humo. Aquí la horquilla (10–15k) y la cautela («citado de forma secundaria») van escritas, y el argumento funciona con el extremo bajo.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Un imprevisto en pista cuesta del orden de diez a quince mil dólares por hora; una inspección programada, una fracción. Decidimos sobre el borde conservador para equivocarnos hacia lo barato, y con una sola parada evitada al año el sistema está pagado».

## Flashcards

> [!question]- ¿Cuánto cuesta un AOG y de dónde sale la cifra?
> 10.000–15.000 USD/h (≈240–360k USD/día), rango Boeing con credibilidad media (`costes_reales_aeronauticos.md` §1, citado de forma secundaria).

> [!question]- ¿Cómo se traduce el coste a decisión técnica?
> Decidiendo sobre `L_inf` con 30/25: la asimetría del negocio (fallo caro, inspección barata) se vuelve umbral conservador.
