# Literatura académica: costes REALES en evaluación coste-sensible de RUL / mantenimiento predictivo (turbofan/aviación)

**Contexto:** NASA C-MAPSS / N-CMAPSS NO contiene costes. Toda la literatura que evalúa coste-sensible sobre C-MAPSS usa costes inventados, normalizados o asumidos. Este documento recoge la evidencia encontrada y una recomendación defendible para tribunal.

---

## 1. Hallazgos: papers que usan coste-sensible en RUL sobre C-MAPSS / N-CMAPSS / PHM

| # | Referencia completa | Coste usado | Fuente del coste | Defendible para tribunal |
|---|---|---|---|---|
| 1 | Lee, J. & Mitici, M. (2023). *Deep reinforcement learning for predictive aircraft maintenance using probabilistic Remaining-Useful-Life prognostics*. Reliability Engineering & System Safety, 230, 108908. DOI: 10.1016/j.ress.2022.108908 | Costes normalizados: c₀=1, c₁=0.01, c_uns=2, D=30 (adimensionales). Resultados: coste total 17.84 (−36.3%), 95.6% mantenimientos no programados evitados, 12.81 ciclos de vida desperdiciados. | No citada. Parámetros asumidos/normalizados. | Parcialmente. Framework sólido (CNN + MC dropout + DRL), pero los costes son adimensionales y no se justifican con datos reales. Defendible si se declara como modelo de coste normalizado. |
| 2 | de Pater, I., Reijns, A. & Mitici, M. (2022). *Alarm-based predictive maintenance scheduling for aircraft engines with imperfect Remaining Useful Life prognostics*. Reliability Engineering & System Safety, 221, 108341. DOI: 10.1016/j.ress.2021.108341 | Coste total de flota (20 aviones, 2 motores c/u) simulado; los fallos suponen 7.4% del coste total de mantenimiento. | C-MAPSS para RUL; costes de mantenimiento derivados de simulación de flota (no datos reales de aerolínea). | Parcialmente. Buen diseño de flota, pero costes simulados. |
| 3 | Ignacio, M.Q. & Naval, P.C. (2025). *Aero-Engine Condition-Based Maintenance Planning Using Reinforcement Learning*. En Mahmud, M. et al. (eds) Neural Information Processing (ICONIP 2024), LNCS vol. 15288, pp. 141–155, Springer. DOI: 10.1007/978-981-96-6582-2_10 | "Actual cost (in millions of US dollars, $M)" como penalizaciones del entorno MDP. | Cita IATA Airline Maintenance Cost Executive Commentary FY2022 [ref. 3] como fuente de inspiración, pero los valores usados son asumidos/normalizados. | Parcialmente. Cita una fuente real (IATA MCX) pero no extrae valores verificables del paper. |
| 4 | Weeber, C. (2024). *Development of a Cost Optimal Predictive Maintenance Strategy*. Junior Management Science, 9(3), 1805–1835. DOI: 10.5282/jums/v9i3pp1805-1835 (Master thesis, TUM) | Coste por ciclo con ratios "razonables" pre/post fallo. Resultados: PdM 36.0% más barato que preventivo, 88.3% que reactivo. | NASA C-MAPSS + flota de 10 aeronaves (simulada). Costes asumidos ("reasonable cost ratios"), sin cita de fuente real. | Parcialmente. Metodología completa (ML + coste por ciclo), pero ratios no validados con datos reales. |
| 5 | Khorasgani, H., Wang, H., Gupta, C. & Farahat, A. (2022). *An Offline Deep Reinforcement Learning for Maintenance Decision-Making*. arXiv:2109.15050 | Costes explícitamente inventados: fallo = 250 ± U(−50,50); reparación = 25 ± U(−5,5); beneficio = 1 ± U(−0.2,0.2) por ciclo. Ratio ≈10:1 inventado. | Declarado como "simple cost structure" / modelo inventado. | No defendible como coste real. Útil solo como ilustración metodológica. |
| 6 | HermosuraM (repo GitHub) *rul-predictive-maintenance* | Ratio de fallo:swap = 100:1 (1 fallo = 100× descartar un ciclo bueno). Sensibilidad: 10:1 → modelo 194% peor; 50:1 → 38% mejor; 100:1 → 50% mejor; 200:1 → 55% mejor. | "defensible for turbomachinery but it is an assumption, not something the data supplies" (declarado honestamente). | Defendible si se declara como supuesto + sensibilidad. El propio repo advierte que por debajo de ~50:1 lo más barato es dejar fallar. |
| 7 | DeltaN04 (repo GitHub) *rul-turbofan-Jet-Engine* | Ratio 10:1 (fallo:alarma falsa). Sensibilidad 5/10/20/50. | "The 10:1 cost ratio is an assumption, not airline data." | Defendible si se declara como supuesto. |
| 8 | Nature (2025) s41598-025-19957-w *Predictive maintenance programs for aircraft engines based on RUL prediction* | C_p = 20 (preventivo), C_c = 100 (correctivo). Ratio 5:1. | Valores inventados (20/100), sin fuente. | No defendible como coste real. |
| 9 | Springer (2026) s44465-026-00024-1 *Predictive maintenance for aircraft cost reduction using machine learning* | Costes en "units": baseline 4.65M, propuesto 2.50M, ahorro 46.25%. | Sin fuente de coste; unidades arbitrarias. | No defendible como coste real. |
| 10 | arXiv 2606.18503 *Quantum Annealing Enhanced RL for RUL* | Menciona caso real: "unscheduled removal cost the operator close to USD 1.4 million" (anecdótico). | Anécdota no citada a fuente verificable. | No defendible como dato. |

**Conclusión del bloque 1:** Ningún paper sobre C-MAPSS/N-CMAPSS cita una fuente real verificable para el ratio de coste FN/FP. Los que son honestos (HermosuraM, DeltaN04) lo declaran explícitamente como supuesto.

---

## 2. Estudios que validan ratios (5:1, 10:1) con datos reales de aerolíneas o MRO

**Resultado de la búsqueda: NO se encontró ningún estudio académico que valide ratios FN/FP (5:1, 10:1) con datos reales de aerolíneas o MRO.**

- Los ratios usados en la literatura son asunciones o valores normalizados.
- La única fuente de datos reales de coste de mantenimiento aeronáutico es la **IATA Aircraft Maintenance Cost Data eXchange (MCX)** (programa privado, solo aerolíneas participantes; exec report público pero sin datos unitarios vinculados a RUL).
- **Aircraft Commerce** publica costes reales de shop visit (CFM56, V2500, etc.) pero son datos de mercado, no vinculados a RUL ni a fallos no programados.
- **Boeing** estima AOG en $10.000–$150.000/hora (Wikipedia AOG, ref. Boeing 2008) y $10.000–$20.000 por evento de 1–2 h (citado ampliamente).
- **NASA NTRS** tiene informes históricos (1970s–1980s) con costes de mantenimiento por hora de vuelo, pero no vinculados a RUL.

**Rangos reales documentados (fuentes de industria, citables):**
- AOG narrowbody: $10.000–$15.000/h; widebody: $20.000–$30.000/h (OxMaint, Boeing).
- Coste total de un evento AOG de motor: $50.000–$600.000+ (Air Cargo Week, Enginestands).
- Shop visit CFM56: $0.8M–$1.7M (Aircraft Commerce, 2003–2006).
- LLP stack CFM56: ~$1.4M (Aircraft Commerce).
- Mantenimiento = 20–25% de los costes operativos de una aerolínea; motor = 35–40% del mantenimiento (MDPI, Kwakye 2024).
- 20% de los shop visits de motor no son programados (MDPI).
- IATA MCX FY2024: coste mantenimiento medio $1.522/FH, $3.758/FC, $5.05M/avión (28 aerolíneas, 2.703 aviones).

**Validación de ratios:** No existe. Los ratios 5:1 / 10:1 / 100:1 usados en la literatura son hipótesis no validadas empíricamente.

---

## 3. Métricas de coste alternativas a euros absolutos (defendibles)

| Métrica | Fuente / justificación | Defendible |
|---|---|---|
| **NASA PHM08 asymmetric score** (exp(−d/13)−1 si d<0; exp(d/10)−1 si d≥0) | Estándar oficial del benchmark PHM08 (Saxena & Goebel 2008). Penaliza predicciones tardías más que tempranas. | SÍ. Es la métrica estándar del dataset, sin costes monetarios. |
| **Ciclos de vida desperdiciados (wasted life)** | Lee & Mitici (2023): 12.81 ciclos. Métrica operacional directa. | SÍ. |
| **Mantenimientos no programados evitados (%)** | Lee & Mitici (2023): 95.6%. Métrica operacional. | SÍ. |
| **AOG hours saved / shop visits avoided** | Industria (HCLTech, OxMaint, IATA). Métrica operacional con valor económico indirecto. | SÍ, como métrica operacional; el valor en € requiere supuestos. |
| **Coste por ciclo (relativo)** | Weeber (2024): coste medio por ciclo por estrategia. | Parcialmente: requiere supuestos de coste. |
| **Coste relativo / ratio FN:FP normalizado** | HermosuraM, DeltaN04: declarado como supuesto + sensibilidad. | SÍ si se declara como supuesto y se hace análisis de sensibilidad. |
| **Reducción de coste (%)** | Varios papers: 29.3% (Lee & Mitici), 36% (Weeber), 46.25% (Springer 2026). | Parcialmente: depende del modelo de coste asumido. |

---

## 4. Datasets públicos con costes de mantenimiento aeronáutico (además de C-MAPSS)

| Dataset / fuente | Contenido | Acceso | Vinculado a RUL/sensores |
|---|---|---|---|
| NASA C-MAPSS / N-CMAPSS | Sensores + RUL. **Sin costes.** | Público (NASA PCoE) | Sí (RUL), no costes |
| IATA MCX (FY2024 exec report) | Costes de mantenimiento reales de 28 aerolíneas, 2.703 aviones ($/FH, $/FC, $/avión). | Exec report público; datos unitarios solo miembros | No (costes agregados, sin RUL) |
| Aircraft Commerce (revista) | Costes de shop visit reales por motor (CFM56, V2500, etc.). | Público (PDFs) | No (datos de mercado) |
| Scholz (HAW Hamburg, 2026) | 35 observaciones de maintenance reserve normalizadas a 2025 USD (regresión por thrust y flight-cycle length). | Público (PDF) | No (costes planificados, sin RUL) |
| NASA NTRS | Informes históricos con costes de mantenimiento por hora de vuelo (1970s–1980s). | Público (PDF) | No (histórico, sin RUL) |
| Aircraft Monitor | Datos de shop visit costs, maintenance reserve. | Público (web) | No |
| Kaggle (varios repos) | Copias de C-MAPSS/N-CMAPSS. **Sin costes.** | Público | Sí (RUL), no costes |

**Conclusión:** No existe ningún dataset público que vincule costes de mantenimiento aeronáutico con datos de sensores/RUL. Cualquier coste en € usado en RUL sobre C-MAPSS es inventado o asumido.

---

## 5. Recomendación para el tribunal

**No usar euros absolutos.** No hay datos reales que los vinculen al dataset; inventarlos es académicamente indefendible (y el tribunal lo detectará).

**Recomendación (orden de preferencia):**

1. **Métricas estándar sin coste (obligatorias):** RMSE, MAE, NASA PHM08 score (estándar del benchmark). Esto es lo que espera un tribunal.
2. **Métricas operacionales defendibles:** ciclos de vida desperdiciados, mantenimientos no programados evitados (%), AOG hours saved (con fuente de industria: Boeing $10k–$150k/h, IATA MCX).
3. **Análisis coste-sensible con ratio NORMALIZADO (10:1 o 100:1) declarado explícitamente como supuesto**, con análisis de sensibilidad (como HermosuraM y DeltaN04). Citar que es asunción, no dato.
4. **Si se quiere dar un rango en €:** citar fuentes de industria (IATA MCX, Aircraft Commerce, Boeing) como rangos de referencia, NO como valores exactos vinculados al dataset. Declarar que son "órdenes de magnitud de referencia".

**Frase defendible para el tribunal:**
> "Dado que NASA C-MAPSS no contiene costes, no se asignan valores monetarios absolutos a los errores de predicción. Se utiliza el score asimétrico NASA PHM08 (estándar del benchmark) como métrica coste-sensible, complementado con un análisis de sensibilidad bajo ratios FN:FP normalizados (10:1, 50:1, 100:1) declarados explícitamente como supuestos, siguiendo la práctica de Lee & Mitici (2023) y HermosuraM (2024). Las métricas operacionales (ciclos desperdiciados, AOG hours saved) se justifican con rangos de la industria (IATA MCX, Boeing)."

**Evitar:** inventar euros (ej. "un fallo cuesta 100.000 €") sin fuente; usar ratios sin declararlos como supuesto; presentar ahorros en € como resultados del modelo.

---

## Referencias clave

- Saxena, A. & Goebel, K. (2008). *Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation*. PHM08.
- Lee, J. & Mitici, M. (2023). RESS, 230, 108908.
- de Pater, I., Reijns, A. & Mitici, M. (2022). RESS, 221, 108341.
- Ignacio, M.Q. & Naval, P.C. (2025). ICONIP 2024, LNCS 15288, pp. 141–155.
- Weeber, C. (2024). Junior Management Science, 9(3), 1805–1835.
- Khorasgani, H. et al. (2022). arXiv:2109.15050.
- IATA MCX Executive Report FY2024 (28 aerolíneas, 2.703 aviones).
- Aircraft Commerce (varios issues, 2002–2006): costes de shop visit CFM56/V2500.
- Boeing (estimación AOG: $10.000–$150.000/h).
- Scholz, D. (2026). *Empirical Regression with Thrust and Flight-Cycle Length*. HAW Hamburg.
- Wikipedia: Aircraft on Ground (ref. Boeing 2008).
- HermosuraM (GitHub): rul-predictive-maintenance.
- DeltaN04 (GitHub): rul-turbofan-Jet-Engine.

**Elaborado:** investigación web (octubre 2026). Fuentes verificadas mediante búsqueda y extracción de contenido.
