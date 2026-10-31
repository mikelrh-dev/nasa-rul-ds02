# Propuestas pendientes ordenadas por ROI (impacto/riesgo)

**Fuente:** `docs/pendiente/propuestas-pendientes-streamlit-n8n.md` + `docs/estudio-propuestas-wow-streamlit.md`.
**ROI** = improve (0-10) / risk (0-10), con risk=0 tratado como ∞ (arriba del todo).
Valores marcados con ~ son estimaciones propias donde el estudio no dio número explícito.

## Ranking (mayor ROI primero)

| # | Propuesta | Improve | Risk | ROI | Estado |
|---|-----------|---------|------|-----|--------|
| 1 | A.8 Descarga parte de trabajo PDF/CSV | 6 | 0 | ∞ | APROBADO |
| 2 | A.5 Calculadora financiera ROI MRO | 9 | ~1 | 9.0 | APROBADO CONDICIONAL |
| 3 | A.2 Kanban operativo de flota | 9 | 2 | 4.5 | APROBADO (cond.) |
| 4 | F.2 Parte MRO por plantilla (n8n) | ~7 | ~2 | 3.5 | Post-defensa |
| 5 | F.3 Auditoría criptográfica cron (n8n) | ~7 | ~2 | 3.5 | Post-defensa |
| 6 | A.6 Data Leakage Trap toggle | 10 | ~3.5 | 2.9 | CONDICIONAL |
| 7 | A.3 Heatmap degradación sensorial | 8 | 3 | 2.7 | APROBADO |
| 8 | F.5 Pipeline cron (n8n) | ~5 | ~2 | 2.5 | Post-defensa |
| 9 | A.7 Auditoría criptográfica en vivo | 7 | 3 | 2.3 | PROCEDER |
| 10 | E.3 Interactividad on_select | 7 | 3 | 2.3 | Adoptar acotado |
| 11 | A.1 st.toast al cruzar AOG | 8 | 4 | 2.0 | CONDICIONAL |
| 12 | F.1 Glass-Box AOG→Telegram (dry-run) | ~8 | ~4 | 2.0 | Post-defensa |
| 13 | C.1 Beep de audio (st.audio) | ~7.5 | ~4.5 | 1.7 | Diferir salvo necesidad |
| 14 | D.1 Imágenes mínimas (logo+empty) | 5 | 3 | 1.7 | Diferir por defecto |
| 15 | A.4 Radar de anomalías | 9 | 6 | 1.5 | DIFERIR |
| 16 | F.4 Alerting multicanal (n8n) | ~6 | ~5 | 1.2 | Solo con fallback |
| 17 | E.4 Intro/landing | 5 | 5 | 1.0 | Solo si onboarding |
| 18 | A.11 Simulador desacoplado (n8n) | 9 | 10 | 0.9 | RECHAZADO |
| 19 | E.2 Video embebido | 3 | 4 | 0.75 | Opcional |
| 20 | A.10 LLM MRO report | ~6.5 | 9 | 0.72 | RECHAZAR en defensa |
| 21 | A.9 n8n webhook real | 5 | 7 | 0.71 | DIFERIR/RECHAZAR |
| 22 | D.2 Gestión de assets | 4 | 6 | 0.67 | DIFERIR |
| 23 | B.3 CSS inyectado | 4 | 8 | 0.5 | NO |
| 24 | E.1 GSAP/animaciones JS | 4 | 8 | 0.5 | Evitar |

## Top 5 por ROI (implementar primero)
1. A.8 Descarga parte de trabajo PDF (riesgo 0).
2. A.5 ROI MRO (~9.0, alto wow financiero).
3. A.2 Kanban operativo de flota (4.5).
4. F.2/F.3 n8n plantilla/cron (3.5, post-defensa).
5. A.6 Data Leakage Trap (2.9, wow pedagógico).

## Notas
- Las propuestas sin puntuación explícita (B.1, B.2, B.4, C.2, C.3) solapan con las anteriores; ver archivo consolidado.
- F.x son estimaciones propias; el estudio no las puntuó con números.
- El ranking no sustituye al estudio detallado; es solo un ordenador por ROI.
", "path">
docs/pendiente/propuestas-ordenadas-por-roi.md