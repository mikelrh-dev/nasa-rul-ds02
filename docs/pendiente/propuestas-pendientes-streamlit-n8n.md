# Propuestas pendientes — Streamlit DS02 y n8n

**Carpeta:** `docs/pendiente/`
**Fecha de archivo:** 2026-10-31
**Estado:** ninguna de estas propuestas está implementada aún. Este archivo las consolida para consulta futura. El estudio detallado completo está en `docs/estudio-propuestas-wow-streamlit.md`.

**Leyenda de estado:** APROBADO (bajo riesgo, alto valor) · CONDICIONAL (implementar con guardas) · DIFERIR (depende de datos/infra no disponibles) · RECHAZADO (riesgo > beneficio para la defensa).

---

## A. Propuestas "WOW" (11) — Bloques A/B/C

### A.1 Simulador táctil cero-latencia con st.toast — CONDICIONAL
- Slider de ciclos; al cruzar L_inf el umbral AOG (25) disparar `st.toast('AOG Activado: Motor 14')` y cambiar color de métrica.
- Scores: feas 7 (vs 9), improve 8, risk 4 (vs 1).
- Notas: no es cero-latencia real (rerun completo de Streamlit). Deduplicar por flanco en session_state (`_prev_u14_aog`). Usar umbral vivo (`threshold_aog`), no hardcodeado. Color vía `delta_color`/badge (prohibido CSS). Texto exacto para tests.
- Refs: `app/dashboard_ds02.py:436-448` (slider), `:131-139` (toast helper), `:139,1654,2637,2640` (usos toast).

### A.2 Kanban operativo de flota (st.columns) — APROBADO (condiciones)
- 3 columnas [Vuelo Normal]|[Warning]|[Hangar AOG]; tarjetas saltan automáticamente por slider + reglas `mia/casos.py`.
- Scores: feas 8, improve 9, risk 2.
- Notas: refactorizar `_muro_del_hangar` (líneas 1093-1244) de grid plano (i%3) a buckets por estado. Mantener claves de botones `muro_gemelo_{u}` y conteo de tarjetas. No tocar reglas de `mia`.
- Refs: `app/flota.py` (147 líneas), `mia/casos.py` (158 líneas, umbrales 30/25).

### A.3 Heatmap de degradación sensorial (Plotly px.imshow) — APROBADO
- Ventana de 50 filas muestreadas del motor fallando, z-score, mapa de calor temporal de 18 canales (4 ops + 14 sensores).
- Scores: feas 7, improve 8, risk 3.
- Notas: "50 ciclos" = 50 filas muestreadas (WINDOW_SIZE=50), no 50 ciclos de vuelo. Z-score sobre historial completo del motor (no por ventana) para que sobreviva la degradación. Complementa `fig_deriva`, no lo reemplaza. Añadir `alt=`. Colocar en pestaña Motor, preferiblemente en expander.
- Refs: `app/ui_data_loader.py:78` (CHANNEL_LABELS), `get_rows()`; `app/dashboard_ds02.py:265` (fig_deriva); `scripts/build_ui_cache.py:209`.

### A.4 Radar de anomalías (Plotly scatterpolar) — DIFERIR
- Telaraña comparando 14 sensores ciclo 1 vs actual.
- Scores: feas 4, improve 9, risk 6.
- Notas: bloqueo principal = no hay residuos por sensor en caché (`ds02_rows.parquet` solo sensores crudos). Residuos solo vía `SensorResidualizer` dentro del bundle (carga TF prohibida en render). Además escalas incompatibles (T en K, P en psi, rpm) → distorsión por unidades sin estandarización. Overlap con `fig_deriva` (deriva % vs primeros 5 ciclos). Fase A1 "Residuos Ridge" diferida.
- Refs: `app/dashboard_ds02.py:265`; `src/ds02_rul/residualizer.py`, `ensemble.py:202`; `mia/modelo.py` (COLUMNAS).

### A.5 Calculadora financiera de riesgo (ROI MRO) — APROBADO CONDICIONAL
- Panel que traduce RMSE a euros: FP = 10k€ mantenimiento temprano, FN = 5M€ motor destruido; ahorro de banda híbrida vs BiLSTM base.
- Scores: feas 9, improve 9 (cond.), risk >0.
- Notas: solo DS02 (prohibido referenciar FD001 en UI). RMSE→€ requiere umbral de decisión + matriz de coste binaria. Contar ciclos (199) no ventanas (6196). Constantes de coste son supuestos de negocio. Cálculo honesto: política puntual ~15.01M€ (1 FP + 3 FN) vs banda conformal ~0.49M€ (49 FP, 0 FN) → ahorro ~14.5M€. Helper puro en `ui_data_loader.py` con tests.
- Refs: `models/v2_metrics.json` (FD001, no usar en UI), `models/ds02_manifest.json`, `app/cache/ds02_windows.parquet`.

### A.6 "Data Leakage Trap" (toggle honesto vs trampa) — CONDICIONAL
- Switch [Modo OOF Riguroso]/[Modo Paper Académico (Trampa)] mostrando RMSE falso 0.308.
- Scores: feas 9, improve 10, risk 3-4 (vs 1).
- Notas: 0.308 es artefacto real (in-sample, `beta=1.0`) registrado en docs/openspec/src, no dato inventado. Ningún test referencia 0.308. Modo riguroso por defecto. 2-3 tests AppTest nuevos. Etiquetar explícitamente "Trampa" y "no es métrica válida", con provenance al audit de stacking. Nunca reemplazar RMSE/macro-RMSE live.
- Refs: `docs/02_DS02_ensemble_RUL_spec.md` §3.7/§6.3; `docs/decisions/ADR-001`, `ADR-005`; `src/ds02_rul/stacking.py`; `ensemble.py` (default beta=1.0); `app/cache/cache_manifest.json`.

### A.7 Auditoría criptográfica en vivo — PROCEDER
- Botón SHA-256 de `ds02_manifest.json` y binario `.keras`, check verde anti-tampering.
- Scores: feas 8, improve 7, risk 3.
- Notas: tamaños verificados (manifest 3.9 KB, keras ~1.85 MiB). Hashing completo del keras ~2.5 ms. Gatear tras botón o cachear en session_state. Implementar de forma aditiva (no romper `artifact_hash_check`). Hashes registrados coinciden con disco.
- Refs: `app/ui_data_loader.py:151` (artifact_hash_check); `app/dashboard_ds02.py` ~595-610 (expander contrato); `~2556-2565` (muestra hash); `models/ds02_manifest.json` artifacts; `src/ds02_rul/persistence.py` (sha256_of, save_ensemble); `tests/test_dss_ui.py:255-304`.

### A.8 Descarga de parte de trabajo determinista (PDF/CSV) — APROBADO
- `st.download_button` exportando estado actual, predicción y fallo de reglas (AOG).
- Scores: feas 10, improve 6, risk 0.
- Notas: CSV/JSON ya implementados (`work_order`, `work_order_csv`, `parte_disponibilidad`). Solo falta PDF con fpdf2 (ya declarado, patrón `_informe_auditoria_pdf` en línea 975). Añadir botón "Descargar parte (PDF)" junto a JSON/CSV (~1606). Test de paridad espejando PDF de auditoría. `generado_en` usa `pd.Timestamp.now()` (no determinista solo en estampa).
- Refs: `app/ui_data_loader.py:403,456,472`; `app/ui_inference.py:483`; `app/dashboard_ds02.py:975,1606,3329`.

### A.9 Integración n8n Webhook "Glass-Box" (Push a Telegram) — DIFERIR/RECHAZAR en defensa
- Botón [Desplegar AOG] POST a webhook n8n → Telegram; `st.code` muestra JSON exacto.
- Scores propuestos: feas 8, improve 10, risk 4. Ajustados: feas 7, improve 5, risk 7.
- Notas: es exactamente el A5 ya descartado en `plan-prioridad-y-riesgo-2026-10-24.md`. Sin webhook/telegram/requests en repo. `requests` transitivo (no declarado). Riesgo de red en aula. Configuración n8n vive en VPS. Recomendación: no antes de la defensa; post-defensa opt-in dry-run (glass-box sin red por defecto), feature flag, timeouts cortos, `requests` declarado o `urllib`.
- Refs: `app/dashboard_ds02.py` ~1890-2010 (hangar); `:596,2559` (st.code existente); `app/api.py` (único os.environ).

### A.10 Orquestación n8n con IA generativa (Ollama/LLM MRO report) — RECHAZAR en defensa
- n8n llama LLM local, redacta reporte MRO, envía por Telegram.
- Scores: feas 5, improve 6-7 (no 10), risk 9.
- Notas: VRAM 4-8 GB, latencia 15s+, alucinación en contexto safety-critical. Dependencias: n8n + Ollama + Telegram + libs Python + Docker Compose + GPU. Alternativa más barata: reporte MRO por plantilla con hechos calculados.
- Refs: `app/api.py`, `app/simulacion.py`, `app/hangar.py`, `app/flota.py`, `app/twin.py`, caché/manifest.

### A.11 Simulador de flota desacoplado (n8n polling) — RECHAZADO
- Streamlit solo pinta; VPS/n8n envía telemetría 1 ciclo/seg vía API.
- Scores: feas 3, improve 9, risk 10.
- Notas: Streamlit es request/response por sesión, sin estado compartido ni canal de entrada. Sin pub/sub en repo (verificado: docker-compose solo api+dashboard; requirements sin broker/ws; sin imports; api.py sin ingesta). Reemplazar requeriría backend + store + transport.
- Refs: `app/simulacion.py`, `st.session_state`, `app/api.py`. ADR generado: `docs/decisions/ADR-010-reject-decoupled-fleet-simulator-n8n-polling.md`.

---

## B. Propuestas sueltas anteriores (solapan con A)

### B.1 Animación en tiempo real ciclo a ciclo (st.empty + time.sleep)
- Solapa con A.1 y A.3. Conclusión: no añadir animación con `time.sleep` en render por defecto. Si se quiere, opt-in con `@st.fragment` + animación nativa de Plotly (frames), preservando `alt=` en frame final y tests con presupuesto de tiempo.

### B.2 Radar de anomalías (Plotly scatterpolar)
- Solapa con A.4. Mismas conclusiones: diferir por gap de residuos y distorsión por escala.

### B.3 Estética "Control Center NASA" (CSS inyectado)
- No aparece en A. Conclusión: NO inyectar CSS. Usar theming nativo (`config.toml`: `baseRadius`/`buttonRadius` a 0, `metricValueFont` mono, `backgroundColor` #000000, `primaryColor` verde neón) + tokens Python para Plotly. Guardia `test_no_css_is_injected_into_the_app` y `test_theme_config_is_dark_and_parseable` se mantienen. Riesgo 8, improve 4.

### B.4 Generación automática del parte de trabajo (LLM)
- Solapa con A.10 y parcialmente A.8. Conclusión: diferir LLM; primero plantilla determinista. Si LLM, adapter opt-in/env-gated/mockeable. `work_order()` ya existe como fuente de verdad.

---

## C. Aviso de voz / audio cuando sea urgente

### C.1 Beep de audio (st.audio)
- Feasible alta, improve 7-8, risk 4-5. Generar beep en Python (numpy/wave) sin binario. Reproducir solo en transición AOG False→True (dedup de A.1), gateado por toggle "Sonido de alarma" (off por defecto). Solo pestaña Flota.

### C.2 Aviso de voz (preferencia del usuario)
- Ruta A (recomendada): archivo de voz pregrabado corto reproducido con `st.audio` (determinista, offline-safe, sin dependencias runtime; coste: binario ~10-50 KB + grabarlo). Ruta B: Web Speech API vía `st.components.v1.html` (JS inyectado, sufre autoplay, rompe espíritu de guardia). Evitar TTS en servidor (pyttsx3 necesita SAPI Windows, no existe en Docker; gTTS necesita red).

### C.3 n8n vs inyección directa para audio
- Recomendación: inyección directa (`st.audio` + wav + toggle) para audio en la app. n8n reservado para notificaciones externas (Telegram/email/audit cron). No añadir red/latencia a un aviso instantáneo.

---

## D. Imágenes en Streamlit (sin CSS)

### D.1 Placement y UX
- Feasible 8/10, improve 5/10, risk 3/10. Recomendado mínimo: logo en header (líneas 746-767) + ilustraciones de estado vacío (muro sin gemelos ~1668, casos nuevos sin resultados ~2634+). Evitar fotos por motor, esquemas que impliquen física no soportada, URLs externas.
- Tests: `test_every_chart_and_grid_has_an_accessible_name` solo mira plotly_chart + dataframe (no se rompe). `alt=` debe pasarse; en AppTest se lee en `proto.imgs[*].alt`, no `proto.alt`. Render de 12 imágenes ~1.3 s (dentro de 120 s).

### D.2 Gestión de assets
- Feasible 8/10, improve 4/10, risk 6/10. No hay assets estáticos hoy. Formatos: PNG (Pillow), SVG (base64 data URI, xmlns inyectado), WebP (Pillow/libwebp). Presupuesto sugerido: ≤100 KB por asset, ≤500 KB total. Gitignore sin reglas de imagen (quedarían tracked). Usar `app/static/` + `server.enableStaticServing = true` (default False). LFS instalado pero no configurado. Preferir SVG (texto, diff-friendly); PNG/WebP binarios hinchan git. Accesibilidad: `alt=` (o `""` decorativo).
- Recomendación: DIFERIR por defecto; CONDICIONAL si se requiere un diagrama concreto (módulo nuevo, no `app/twin.py`, alt, SVG preferido, LFS para binarios, sin CSS/HTML).

---

## E. GSAP, video, interactividad, intro/landing

### E.1 GSAP / animaciones JS
- Evitar. Feasible media-baja, improve 4/10, risk 8/10. Requiere inyección de `<script>` (conflicto con guardia y no verificable en AppTest). Alternativa nativa: frames de Plotly + `@st.fragment`.

### E.2 Video embebido
- Opcional solo con fallback de archivo faltante. Feasible alta, improve 3/10, risk 4/10. `st.video` soporta mp4/webm/ogg + subtítulos + `alt`, autoplay/muted/loop. Clip corto (≤10 s) local o link YouTube, sin autoplay con sonido. Mejor en expander colapsado (carga en AppTest).

### E.3 Interactividad extra (on_select, etc.)
- Adoptar de forma acotada. Feasible alta, improve 7/10, risk 3/10. `st.plotly_chart(..., on_select="rerun")` y `st.dataframe(..., on_select=...)` para drill-down en ribbon de flota (~1208) y tabla de orden de trabajo (~1448). `st.toggle` ya usado (~1268). Requiere plumbing de selección → session_state → flags diferidos. Mejor ROI de esta sección.

### E.4 Intro / landing previa
- Solo si el onboarding lo justifica. Feasible alta, improve 5/10, risk 5/10. Router delgado `app/streamlit_app.py` con `st.navigation` (2 páginas: intro + dashboard), dejando `dashboard_ds02.py` y sus 4 pestañas intocados. Alternativa barata: splash in-app con flag de session_state. Cambio de entrypoint afecta README/Dockerfile y tests del entrypoint.

### Ranking de esta sección
1. Interactividad nativa `on_select` (mejor ROI).
2. Imágenes mínimas (logo + empty states).
3. Video solo con asset corto y fallback.
4. Landing solo si onboarding lo merece.
5. GSAP: no.

---

## F. Integraciones n8n (si se decide usar n8n)

### F.1 Glass-Box AOG → Telegram (real o dry-run)
- Botón [Desplegar AOG] POST a webhook n8n → Telegram; `st.code` muestra JSON exacto. Wow alto (cierre ciber-físico). Sin limitar por red: POST real a n8n → Telegram en segundos. Condición: validar que VPS/n8n/Telegram respondan <3s antes de la defensa; si no, volver a dry-run. Payload determinista, glass-box.

### F.2 Generación automática de parte MRO (plantilla, no LLM)
- n8n recibe JSON de `work_order()`, genera PDF/HTML con plantilla determinista, archiva o envía por email. Wow: documentación automática auditable. Riesgo bajo si es plantilla (sin alucinación). Reutiliza fpdf2/patrón existente.

### F.3 Auditoría criptográfica programada (cron)
- n8n cada X minutos consulta `GET /health` y `/units` de FastAPI, verifica hash del manifest/ensemble, alerta si mismatch o caché stale. Wow: MLOps "sistema vivo" monitorizado. Read-only, sin modelo, bajo riesgo. Bueno para demostrar disciplina DevSecOps.

### F.4 Alerting multicanal con deduplicación
- Al AOG, n8n enruta a Telegram + email (+ opcional Slack) con dedup y escalado. Wow: alerting de grado empresarial. Riesgo: red + gestión de secretos. Apropiado con fallback offline o post-defensa.

### F.5 Orquestación de pipeline (rebuild caché / reportes)
- n8n cron ejecuta `build_ui_cache.py` o genera reportes periódicos y notifica al terminar. Wow: automatización MLOps. Bajo riesgo, corre en VPS. No toca modelo ni tests.

### No recomendadas
- Telemetría push a Streamlit (A.11, sin pub/sub, arquitectónicamente inviable).
- LLM generativo (A.10, VRAM/tiempo/alucinación).
- Voz en vivo (A5 descartado).

### Prioridad si "tienes que meter n8n" para la defensa
1. F.3 (cron audit) + F.1 en dry-run (glass-box sin red): wow real, offline-safe.
2. F.2 y F.5 post-defensa.
3. F.4 solo con fallback offline.

---

## G. Recomendación global de implementación

Implementar ahora (alto valor, bajo riesgo):
1. A.2 Kanban operativo de flota
2. A.3 Heatmap de degradación sensorial
3. A.7 Auditoría criptográfica en vivo
4. A.8 Descarga de parte de trabajo PDF
5. A.1 st.toast al cruzar AOG (con dedup)

Si sobra tiempo (condicionales):
6. A.5 ROI MRO
7. A.6 Data Leakage Trap toggle

No implementar (riesgo > beneficio):
- A.4 Radar, A.9 n8n webhook real, A.10 LLM, A.11 telemetría push, B.3 CSS inyectado, E.1 GSAP.

Audio/voz e imágenes: diferir salvo necesidad concreta (C.2 ruta A y D.1 mínimos).

---

## Archivos movidos a esta carpeta

- `docs/plans/pendiente-adopcion-bundle-B.md` → `docs/pendiente/pendiente-adopcion-bundle-B.md`
- `docs/informes/pendientes-2026-10-22-traspaso.md` → `docs/pendiente/pendientes-2026-10-22-traspaso.md`

## Referencias

- Estudio detallado completo: `docs/estudio-propuestas-wow-streamlit.md`
- ADR-010 (rechazo #11): `docs/decisions/ADR-010-reject-decoupled-fleet-simulator-n8n-polling.md`
- Plan previo: `docs/plans/plan-prioridad-y-riesgo-2026-10-24.md` (decisión A5 descartada)
- Transcripts de subagentes: `C:\Users\mikel\AppData\Local\hermes\cache\delegation\live\`
", "path">
docs/pendiente/propuestas-pendientes-streamlit-n8n.md