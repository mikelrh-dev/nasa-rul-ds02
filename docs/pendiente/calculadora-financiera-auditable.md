# Calculadora financiera auditable — diseño (no implementada)

**Estado:** propuesta de diseño. Nada de esto está en la app.
**Origen:** discusión sobre la A.5 (`propuestas-ordenadas-por-roi.md`); la versión
"FP=10k€ / FN=5M€ / ahorro ~14,5M€" se descarta por indecidible ante un tribunal.
Este documento la sustituye por un comparador auditable.
**Fecha:** 2026-10-31.

## Por qué la A.5 original no vale

1. Las constantes (10k€, 5M€) no tienen fuente.
2. Extrapola a flota desde n=3 motores.
3. Multiplicaría ciclos simulados (degradación acelerada NASA, vidas de 59–76
   ciclos) por €/FC reales en silencio.

## Principio del diseño

Tres columnas separadas: **evento medido (intocable) → % de vida (invariante que
viaja al mundo real) → € (traducción con supuestos a la vista)**. La conclusión
vive en los eventos, no en los precios.

## Bloque 1 — Tabla medida (cero supuestos, sale de `ds02_windows.parquet`)

Umbrales 30/25. Agregado por ciclo: banda = `lower_min`, puntual = `pred` media,
verdad = `y_true` media.

| | Alarma banda | Alarma puntual | Verdad cruza 25 | Antelación banda | Antelación puntual |
|---|---|---|---|---|---|
| U11 (vida 59) | 21 | 37 | 35 | +14 (24% vida) | −2, tarde (−3%) |
| U14 (vida 76) | 29 | 50 | 52 | +23 (30%) | +2 (3%) |
| U15 (vida 67) | 24 | 40 | 43 | +19 (28%) | +3 (4%) |

Inspecciones (ciclos en 25–30): banda 9/14/13, puntual 5/4/5 → **+22 inspecciones**.

Métricas-auditoras derivadas, sin precio:

- **Exposición** (ciclos volados con RUL real <25 declarado apto): banda **0**,
  puntual **2** (U11, ciclos 35–36).
- **Antelación total**: banda 56 ciclos (~28% de vida media), puntual 3 (~2%).

Titular defendible: *"la banda avisa con ~28% de vida restante; la puntual, con
~2% — y una vez tarde"*.

## Bloque 2 — Traductor a euros (cada fila: valor + fuente + estado)

| Constante | Valor | Fuente | Estado |
|---|---|---|---|
| MRO por ciclo de vuelo | ~1.804 $ | IATA MCX FY2024: 3.758 $/FC × 48% parte motor | Citada, fórmula visible |
| Cancelación NB 180 pax | 25.720 € | EUROCONTROL SI Ed.10, Tabla 20 | Citada (orden de magnitud) |
| Retraso táctico puerta | 166 €/min | EUROCONTROL SI Ed.10 | Citada |
| Resto costes unitarios | `costes_reales_aeronauticos.md` | Primaria/auditada | Citada |
| Coste de una inspección | Editable (defecto = fórmula IATA) | **Dato del operador** | Supuesto declarado |
| Coste de fallo no detectado | Vacío (lo teclea el operador o no se calcula) | **Dato del operador** | Supuesto declarado |
| Ciclos reales entre visitas al taller | Editable (p. ej. 3.000) | **Dato del operador** | Supuesto declarado |
| Puente ciclo→FH | Rango 1,5–3,0 | Supuesto con rango | Supuesto declarado |

Fórmula a la vista: `antelación_real ≈ (% vida ganada) × (ciclos reales)` →
coste ≈ eso × (coste/fuente citada). Slider de sensibilidad sobre los supuestos;
la conclusión que debe sobrevivir en todo el rango: *la banda cuesta más
inspecciones y evita todas las exposiciones; la puntual ahorra inspecciones y
deja 2 ciclos de exposición*.

## Bloque 3 — Cierre y disclaimer

Conclusión generada, no redactada, con los supuestos declarados arriba.
Disclaimer estructural: *"Aritmética ilustrativa sobre el panel de test
(3 motores, 6.196 ventanas). No es extrapolación a flota. Degradación
acelerada: vidas de 59–76 ciclos frente a miles en operación real; los
absolutos son del simulador, los porcentajes y el ranking son lo transferible."*

## Líneas rojas

Constantes sin fuente, un único número de ahorro, extrapolación a flota,
multiplicar ciclos simulados × €/FC sin puente declarado.

## Implementación esbozada (cuando se decida, loop SDD)

Función pura en `app/ui_data_loader.py` (eventos desde la caché) + tests +
panel con tabla de procedencia. Sin tocar modelo ni caché. Referencias:
`costes_reales_aeronauticos.md`, `docs/decisions/ADR-008-*`, `mia/casos.py`,
`tests/test_dss_ui.py`.
