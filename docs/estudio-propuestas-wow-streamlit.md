# Estudio de propuestas "WOW" para el dashboard Streamlit DS02

**Fecha del estudio:** 2026-10-31
**Alcance:** análisis estático (solo lectura) de 11 propuestas de alto impacto para explotar la infraestructura existente (caché Parquet, Streamlit 1.66.0, n8n, Plotly) sin violar los tests ni introducir latencia. No se modificó código ni tests durante el estudio (salvo un ADR generado por un subagente, ver nota final).
**Repo:** `C:/Users/mikel/Desktop/Pruebas/nasa` (rama master)

## Escala de evaluación

- **Feasibility / Viabilidad (0-10):** esfuerzo y encaje con la arquitectura actual (caché read-only, sin carga de modelo en render, Streamlit rerun model).
- **Improve / Impacto (0-10):** valor para la defensa/tribunal y para el operador.
- **Riesgo (0-10):** probabilidad de romper tests, latencia, fragilidad ante upgrades, seguridad.
- **Recomendación:** APROBADO / CONDICIONAL / DIFERIR / RECHAZADO.

## Inventario verificado del repo (base del estudio)

- Streamlit `==1.66.0` (`requirements.txt:23`).
- App principal `app/entrypoints/dashboard_ds02.py` (~600 líneas): 4 pestañas (Flota, Motor, Casos nuevos, Auditoría), `chart_layout`/`style_axes`, tokens de diseño Python (`INK`, `MUTED`, `GRID`, `SURFACE`, `SKY`, `AMBER`, `GREEN`, `ROSE`).
- Caché: `app/cache/ds02_windows.parquet` (6196 filas, 7 cols: unit, cycle, start_index, y_true, pred, lower, upper) para unidades 11/14/15; `app/cache/ds02_rows.parquet` (12538 filas, 20 cols: unit, cycle + 4 ops + 14 sensores).
- `app/lib/ui_data_loader.py`: `get_windows`, `get_rows`, `fleet_snapshot`, `work_order`, `work_order_csv`, `parte_disponibilidad`, `artifact_hash_check`, `first_alarm_cycle`, `unit_curve`, `CHANNEL_LABELS`/`CHANNEL_GROUPS`.
- `src/mia/casos.py` (158 líneas): reglas y umbrales (30/25, alineados con defaults del loader).
- `src/mia/modelo.py`: `COLUMNAS` (18 canales: 4 ops + 14 sensores).
- Tests: `tests/test_dss_ui.py` (31 passed en la corrida base) incluye guardas `test_no_css_is_injected_into_the_app` (líneas 369-372) y `test_theme_config_is_dark_and_parseable` (352-367); AppTest con timeout 120 s.
- `.streamlit/config.toml` (53 líneas): theming nativo completo (colores, fuentes Inter/Space Grotesk/JetBrains Mono, radios, paletas de 10 colores).
- Sin infraestructura pub/sub: `docker-compose.yml` solo `api` + `dashboard`; sin redis/kafka/ws en requirements ni imports.
- Sin dependencias LLM declaradas; `openai` 3.41 instalado solo a nivel sistema (transitivo); `anthropic` ausente; `requests` 2.34.2 transitivo; `fpdf2` 2.7.7 declarado. Ollama local disponible en dev (`qwen2.5:7b-instruct`).
- Modelos: `models/bilstm_ds02.keras` (~1.85 MiB), `models/ensemble.joblib` (~2 MB), `models/ds02_manifest.json` (3.9 KB). Hashes registrados coinciden con disco.
- Plan previo `docs/plans/plan-prioridad-y-riesgo-2026-10-24.md` ya descartó la integración voz+Telegram (A5).

## Propuestas analizadas

### #1 Simulador táctil cero-latencia con st.toast

- **Concepto:** slider de ciclos; al cruzar L_inf el umbral AOG (25) disparar `st.toast('AOG Activado: Motor 14')` y cambiar color de métrica.
- **Scores propuestos:** feas 9 / improve 8 / risk 1. **Ajustados:** feas 7 / improve 8 / risk 4.
- **Feasibility:** los datos ya están cacheados (`L.get_windows`, `L.fleet_snapshot`, curvas); sin llamada a modelo. Pero Streamlit re-ejecuta el script completo en cada cambio del slider: no es "cero-latencia" real. Requiere deduplicación por transición `False→True` en `session_state` (flag `_prev_u14_aog`), inicializado al estado actual para no disparar toast al arrancar. El umbral debe ser el vivo (`threshold_aog`, default 25), no hardcodeado.
- **Color de métrica:** `st.metric` no admite color arbitrario; solo `delta_color`. Prohibido inyectar CSS (`test_no_css_is_injected_into_the_app`). Usar `delta_color="inverse"` + badge/vocabulario `STATE_COLORS`/`STATE_BG` ya existente.
- **Code refs:** `app/entrypoints/dashboard_ds02.py:436-448` (slider `cycle`), `:131-139` (helper `_toast_pendiente`/`_mostrar_toast_pendiente`), `:139,1654,2637,2640` (usos de `st.toast`), `L.first_alarm_cycle` (unidad 14 cruza en ciclo 29→52). `app/lib/flota.py` es registro puro de motores (147 líneas): NO es el lugar para lógica de toast.
- **Test impact:** `test_the_cycle_slider_drives_the_grounded_kpi` mueve el reloj a 40; tests ocultos pueden verificar `app.toast` tras cruzar. Riesgo de spam si no se deduplica. Tests headless (120 s) no se ven afectados si el cambio es aditivo.
- **Recomendación:** CONDICIONAL. Implementar con detección por flanco, solo caché, umbral vivo, texto exacto `st.toast('AOG Activado: Motor 14')`, color vía APIs soportadas. No vender como cero-latencia.

### #2 Kanban operativo de flota (st.columns)

- **Concepto:** 3 columnas [Vuelo Normal]|[Warning]|[Hangar AOG]; las tarjetas de motores (11, 14, 15) saltan de columna según el slider y las reglas de `src/mia/casos.py`.
- **Scores:** feas 8 / improve 9 / risk 2 (confirmados).
- **Code refs:** `app/lib/flota.py` (147 líneas, registro de motores), `mia/casos.py` (158 líneas, umbrales 30/25 alineados con defaults del loader), `app/entrypoints/dashboard_ds02.py` (muro de hangar, columnas), `app/lib/ui_data_loader.py` (`classify`, labels).
- **Test impact:** los tests de tarjetas del muro (conteo/claves) deben seguir verdes si el agrupamiento conserva botones. Recomendar tests nuevos de agrupamiento (read-only). No cambiar reglas de `mia`.
- **Recomendación:** APROBADO con condiciones: refactorizar `_muro_del_hangar` para agrupar por estado, alinear vocabulario, sin tocar reglas.

### #3 Heatmap de degradación sensorial (Plotly px.imshow)

- **Concepto:** ventana de 50 ciclos de `ds02_rows.parquet` para el motor fallando, normalizar con Z-score, mapa de calor temporal de los sensores.
- **Scores:** feas 7 / improve 8 / risk 3 (confirmados).
- **Aclaraciones de datos:** `ds02_rows.parquet` tiene 20 columnas = `unit, cycle` + 4 ops (alt, Mach, TRA, T2) + 14 sensores. "18 sensores" es impreciso: son 18 canales (4 ops + 14 sensores). "50 ciclos" debe ser 50 filas muestreadas (WINDOW_SIZE=50 del modelo), no 50 ciclos de vuelo (serían ~1k-5.6k filas).
- **Performance:** 50×18 = 900 celdas; build ~0.01-0.27 s; memoria negligible. Z-score seguro (min std ≈ 0.024 para Mach en ventana de 50).
- **Code refs:** `app/lib/ui_data_loader.py:78` (`CHANNEL_LABELS`, 18 entradas), `get_rows()`; `app/entrypoints/dashboard_ds02.py:265` (`fig_deriva`, gráfico de deriva existente a complementar, no reemplazar); `:2108-2125` (agregación por ciclo); `:2339-2390` (perfiles de ops); `scripts/build_ui_cache.py:209` (escritura del parquet, sin cambios necesarios).
- **Test impact:** añade un `plotly_chart` (el umbral `>=6` sigue pasando). Debe pasar `alt=` o falla `test_every_chart_and_grid_has_an_accessible_name`. Z-score defensivo (división por cero). Recomendación: z-scorear cada canal sobre el historial completo del motor seleccionado (no por ventana de 50), para que sobreviva la magnitud de la degradación.
- **Recomendación:** APROBADO. Colocar en pestaña "Motor", usar las últimas 50 filas muestreadas del motor seleccionado/fallando, 18 canales en x, ciclos muestreados en y, z-score sobre historial completo, escala `RdBu_r`, con caption explicando 50 filas ≈ 0.44 ciclos de vuelo.

### #4 Radar de anomalías (Plotly scatterpolar)

- **Concepto:** gráfico de telaraña comparando 14 sensores en ciclo 1 vs ciclo actual; se deforma hacia el sensor crítico.
- **Scores propuestos:** feas 4 / improve 9 / risk 6. Confirmados (con matices).
- **Bloqueo principal:** no hay datos de residual por sensor en el caché (`ds02_rows.parquet` solo sensores crudos; `ds02_windows.parquet` solo pred/lower/upper). Los residuos solo se obtienen vía `SensorResidualizer.transform` dentro de `ensemble.predict_interval` (carga del bundle TF, prohibida en render por contrato read-only). Además, las 14 canales tienen escalas incompatibles (T en K, P en psi, rpm); sin estandarización por sensor, el "mayor residual" es un artefacto de unidades.
- **Overlap con análisis previo:** el panel "Radiografía de sensores" (`fig_deriva`, `app/entrypoints/dashboard_ds02.py:265`) ya muestra deriva % vs. los primeros 5 ciclos: es la vista honesta actual y equivalente en propósito.
- **Code refs:** `app/entrypoints/dashboard_ds02.py:265` (fig_deriva); `scripts/build_ui_cache.py:209`; `src/ds02_rul/residualizer.py`, `ensemble.py:202` (residualizer dentro del bundle); `mia/modelo.py` (COLUMNAS); `app/lib/ui_data_loader.py` (CHANNEL_LABELS, CHANNEL_GROUPS).
- **¿Existen residuos pre-calculados en algún sitio?** No. Ni CSV ni parquet ni joblib almacenan columnas de residual. El `res_scaler` vive dentro de `models/ensemble.joblib` y no se exporta al caché. La fase A1 "Residuos Ridge" está verificada pero diferida por exactamente esta razón.
- **Recomendación:** DIFERIR. Si se persigue: (a) implementar la fase A1 offline para usar residuos estandarizados (σ) reales; (b) estandarizar cada eje (z-score o percentil vs. baseline ciclo 1) antes de graficar. Mientras tanto, mantener `fig_deriva` como única vista honesta.

### #5 Calculadora financiera de riesgo (ROI MRO)

- **Concepto:** panel que traduce RMSE a euros (FP = 10k€ mantenimiento temprano, FN = 5M€ motor destruido), mostrando ahorro de la banda híbrida vs BiLSTM base.
- **Scores:** feas 9 / improve 9 / risk 0. **Risk real: >0** (ver abajo).
- **Datos disponibles:** sí. `models/v2_metrics.json` tiene RMSEs estilo FD001 (XGBoost 26.16, LSTM2 15.13, LightGBM 13.42, BiLSTM 14.78). `models/ds02_manifest.json` tiene RMSE DS02 (`reference_row.RMSE 4.251`, `BiLSTM solo 6.218±0.541`, `Híbrido+EMA5 4.340±0.101`, `macro_rmse 4.8433`, por unidad). Caché también registra `rmse 4.2515`.
- **Riesgos concretos:** (1) `v2_metrics.json` es FD001; la UI DS02 no puede referenciar FD001 (`test_no_fd001_artifact_is_referenced`). (2) RMSE→€ no es directo: requiere umbral de decisión y matriz de coste binaria; si no, falsa precisión. (3) Contar ventanas (6196) vs ciclos (199) cambia costes en órdenes de magnitud. (4) La banda conservadora cambia 49 falsas alarmas por 0 motores perdidos: capacidad de mantenimiento y coste de molestia son reales. (5) Las constantes de coste (10k/5M) son supuestos de negocio, no métricas del modelo.
- **Cálculo honesto:** sobre 199 ciclos DS02 deduplicados, una política de predicción puntual (umbral 25) cuesta ~15.01M€ (1 FP + 3 FN), mientras la política de límite inferior conformal cuesta ~0.49M€ (49 FP, 0 FN): ahorro ~14.5M€. Esa es la historia honesta de "ahorro".
- **Code refs:** `models/v2_metrics.json`, `models/ds02_manifest.json`, `app/cache/cache_manifest.json`, `app/cache/ds02_windows.parquet` (`y_true, pred, lower, upper`).
- **Test impact:** implementación read-only no toca `models/` ni hashes (tests verdes). La lógica de coste debe ser helper puro en `app/lib/ui_data_loader.py` con tests enfocados; evitar hardcodear métricas FD001 en la UI.
- **Recomendación:** APROBADO CONDICIONAL. Panel solo-DS02, etiquetado como escenario con supuestos, constantes configurables, deduplicación por ciclo, tests de aritmética de coste. No usar `v2_metrics.json` en la UI ni presentar RMSE como euros.

### #6 "Data Leakage Trap" (toggle honesto vs trampa)

- **Concepto:** switch [Modo OOF Riguroso]/[Modo Paper Académico (Trampa)] que muestra el RMSE falso 0.308 para evidenciar el peligro de evaluar series temporales sin separación por motor.
- **Scores:** feas 9 / improve 10 / risk 3-4 (propuesto 1; ajustado por riesgo de confusión en tribunal o contaminación de métricas live).
- **Verificación de 0.308:** aparece en `docs/02_DS02_ensemble_RUL_spec.md` §3.7/§6.3; `docs/decisions/ADR-001`, `ADR-005`; openspec proposal y spec; `src/ds02_rul/stacking.py` (docstring del protocolo legacy in-sample); `app/cache/cache_manifest.json` (`beta: 1.0`); `src/ds02_rul/ensemble.py` (default `beta=1.0`). Es un artefacto real pero inválido (in-sample), no datos inventados. Ningún test referencia 0.308 (~212 tests baseline).
- **Code refs:** `app/entrypoints/dashboard_ds02.py` (toggle de reglas existente como patrón), `src/ds02_rul/stacking.py`, `ensemble.py`.
- **Test impact:** modo riguroso por defecto: tests existentes no se ven afectados. Necesita 2-3 tests AppTest nuevos (default off, modo trampa muestra 0.308 solo en panel diagnóstico, sin contaminar aserciones de RMSE cacheado).
- **Recomendación:** CONDICIONAL. Implementar como panel diagnóstico/académico opt-in en pestaña Evidencia, etiquetado explícitamente "Trampa" y "no es métrica válida", con provenance al audit de stacking. Nunca reemplazar RMSE/macro-RMSE live. Si no se garantiza aislamiento, rechazar.

### #7 Auditoría criptográfica en vivo

- **Concepto:** botón que calcula SHA-256 de `ds02_manifest.json` y del binario `.keras`, mostrando check verde que garantiza que el modelo en demo es matemáticamente el mismo que el entrenado (anti-tampering).
- **Scores:** feas 8 / improve 7 / risk 3 (confirmados).
- **Tamaños verificados:** `models/ds02_manifest.json` = 3,988 B; `models/bilstm_ds02.keras` = 1,935,382 B (~1.85 MiB). Hashes registrados coinciden con disco (`bilstm_sha256 = d0c5ed...`, `ensemble_sha256 = 7acba3...`, también en `cache_manifest.json`).
- **Performance:** hashear el `.keras` completo cuesta ~2.5 ms; el manifest ~6 ms (chunks de 1 MiB). Hashing síncrono es efectivamente gratis para un click. Riesgo real: llamarlo en cada rerun sin gating/caché. Debe ir detrás de `st.button` o cachear en `session_state`.
- **Code refs:** `app/lib/ui_data_loader.py:151` (`artifact_hash_check()`, actualmente solo verifica `ensemble.joblib` vs `cache_manifest.json`; constantes `ARTIFACT_PATH`, `HASH_CHUNK = 1<<20`); `app/entrypoints/dashboard_ds02.py` ~595-610 ("Contrato de artefacto congelado" expander); `~2556-2565` (muestra `ensemble_sha256`); `models/ds02_manifest.json` artifacts (`bilstm_sha256`, `bilstm_bytes`, `ensemble_sha256`, `ensemble_bytes`); `src/ds02_rul/persistence.py` (`sha256_of()`, `save_ensemble()`); `tests/test_dss_ui.py:255-304` (tests de hash), `:208` (test read-only sobre 4 artefactos).
- **Test impact:** los tests de `artifact_hash_check` asumen un path y una forma de retorno fijos; un cambio in-place rompería. Implementar de forma aditiva (helper nuevo o dict extendido) para mantener verdes los 31 tests, y añadir cobertura para `.keras`/manifest.
- **Recomendación:** PROCEDER. Los hashes y bytes ya existen; es sobre todo cableado de UI. No degradar a "JSON + archivo ligero": hashear el `.keras` real cuesta ~2.5 ms y es exactamente lo que exige la claim anti-tampering. Gatear tras botón, lectura por chunks, read-only, preservar contrato de `artifact_hash_check`.

### #8 Descarga de parte de trabajo determinista (PDF/CSV)

- **Concepto:** `st.download_button` exportando estado actual del motor, predicción y fallo de reglas (AOG) a archivo auditado.
- **Scores:** feas 10 / improve 6 / risk 0 (confirmados).
- **Veredicto:** APROBAR con alcance limitado. La mitad CSV ya está entregada; solo falta la variante PDF.
- **Code refs:** `app/lib/ui_data_loader.py:403` (`work_order(...)` construye el documento auditado: unidades, regla, motivo, pred, lower/upper, rul_real, hash de provenance, umbrales, banda/corrección); `:456` (`work_order_csv(...)` companion, usado en `app/entrypoints/dashboard_ds02.py:1615`); `app/lib/ui_inference.py:483` (`live_work_order(...)` variante de unidad única); `app/entrypoints/dashboard_ds02.py:3329` (descarga JSON); `app/entrypoints/dashboard_ds02.py:975` (`_informe_auditoria_pdf(...)` usando fpdf2 — patrón exacto a espejar); `app/lib/ui_data_loader.py:472` (`parte_disponibilidad(...)` para caso sin unidades bloqueadas).
- **Dependencias:** `fpdf2==2.7.7` declarado e instalado (`requirements.txt:26`, importa como `fpdf`). `reportlab` NO está en requirements ni instalado — no usarlo; fpdf2 ya es la lib PDF del proyecto.
- **Test impact:** ningún AppTest afirma conteo exacto de `download_button`; no hay test hoy de los botones de orden de trabajo (solo PDF de auditoría + "plantilla CSV"). Añadir botón es de bajo riesgo. Si se añade `_parte_trabajo_pdf`, espejar `test_dss_interaction.py:419` (extraer fn vía AST, assert `data[:5] == b"%PDF-"` y `%%EOF` final) para mantener garantía de PDF no truncado. Contrato de cabecera vacía de `work_order_csv` (`test_dss_ui.py:181`) debe seguir pasando (sin cambios).
- **Recomendación:** implementar solo la variante PDF faltante (JSON+CSV ya hechos), reutilizando fpdf2 + helper `_latin1`; sin dependencia nueva. Añadir un botón "Descargar parte (PDF)" junto al par JSON/CSV en `app/entrypoints/dashboard_ds02.py:1606`, alimentando `L.work_order(...)` (y manejar caso vacío con `parte_disponibilidad`). Añadir test de paridad espejando el PDF de auditoría. Mantener `models/` y `app/cache/` intocados (G1). Nota: `generado_en` usa `pd.Timestamp.now()` → no determinismo solo en la estampa (contenido derivado del estado es determinista).

### #9 Integración n8n Webhook "Glass-Box" (Push a Telegram)

- **Concepto:** botón [Desplegar AOG] que hace POST al webhook de n8n en el VPS; n8n enruta a Telegram; `st.code` muestra el JSON exacto enviado.
- **Scores propuestos:** feas 8 / improve 10 / risk 4. **Ajustados:** feas 7 / improve 5 / risk 7.
- **Contexto:** esto es exactamente el A5 (voz+Telegram) ya descartado en `docs/plans/plan-prioridad-y-riesgo-2026-10-24.md` ("DESCARTADO POR AHORA — necesita red y un token en el repo. Falla en directo si el aula no tiene internet").
- **Code refs:** no hay envío externo activo (`webhook`/`telegram`) ni cliente HTTP en `app/`, `src/mia/`, `src/`, `tests/` (solo stub `src/n8n.py` + API local `app/services/api.py` `/health,/units,/predict`). Único uso de `os.environ` es `DS02_ARTIFACT` en `app/services/api.py`. Punto de inserción natural: bloque de hangar en `app/entrypoints/dashboard_ds02.py` ~1890-2010 (candidatos AOG y registros abiertos). `st.code(..., language=None)` ya se usa para el hash de provenance (`app/entrypoints/dashboard_ds02.py:596`, `:2559`) — el patrón de "glass-box" JSON reutilizable.
- **Dependencias:** `requests==2.34.2` instalado pero solo transitivo (`Required-by: jupyterlab_server, streamlit, tensorflow`); NO está en `requirements.txt` ni `pyproject.toml`. `httpx==0.28.1` solo vía jupyterlab (dev). Docker tiene `curl` (healthcheck) pero no cliente outbound garantizado. Recomendación: si se implementa, usar `requests` y declararlo explícitamente, o `urllib` (stdlib, cero deps). Evitar `httpx` salvo que se añada a requirements + Dockerfile.
- **Riesgo de red (wifi universitario):** POST saliente a VPS puede ser bloqueado por captive portal/proxy/WAF/DNS/puertos; sin fallback offline = fallo de demo. Handler síncrono: `requests.post` sin timeout corto congela toda la UI. Secreto (URL webhook / token) debe vivir en `.streamlit/secrets.toml` o env (ya gitignored), documentado para operadores. Endpoint VPS debe ser HTTPS.
- **Test impact:** tests con AppTest sensibles a archivos de estado (`app/registros_flota.json` ya causó incidentes). Llamada de red real en handler haría tests lentos/flaky salvo que el cliente HTTP se abstraiga en una función única monkeypatcheable. No hay `responses`/`pytest-httpx`/`respx` en deps. Tests nuevos: forma del payload en `st.code`, path éxito (mock 200), path fallo (timeout/5xx → error de UI sin crash), modo dry-run.
- **Configuración n8n:** ninguna en el repo; vive enteramente en el VPS (nodo webhook, bot token + chat id de Telegram, routing, auth header). La app solo necesita URL webhook (+ header secreto opcional) vía secrets/env.
- **Recomendación:** NO implementar antes de la defensa (consistente con decisión A5). Si se implementa post-defensa: opt-in y offline-safe: feature flag vía secret/env (deshabilitado por defecto → "dry-run" que renderiza el JSON exacto en `st.code` sin red), POST abstraído en una función única, mockeable en tests, timeouts cortos, error de UI amable, declarar `requests` en requirements (o `urllib`), nunca commitear la URL webhook, documentar setup. El valor "glass-box" (mostrar JSON exacto) se mantiene incluso en dry-run: es la parte de valor real con riesgo de red cero.

### #10 Orquestación n8n con IA generativa (Ollama/LLM MRO report)

- **Concepto:** n8n recibe el webhook, llama a un LLM local que redacta un reporte de mantenimiento persuasivo y lo manda por Telegram.
- **Scores propuestos:** feas 5 / improve 10 / risk 9. **Ajustados:** improve 6-7 (no 10) — mejora comunicación/demo wow, no métricas ML (RMSE, NASA, cobertura conformal).
- **Code refs que alimentarían el reporte (fuentes existentes, read-only):** `app/services/api.py` (`/health`, `/units`, `/predict`); `app/lib/simulacion.py` (reloj de flota, `retenidos`, `ciclos_hasta_fallo`, replay sobre caché sin modelo); `app/lib/hangar.py` (máquina de estados, decisiones congeladas, `cola`, `revision`); `app/lib/flota.py`, `app/lib/twin.py` (registro de motores, gemelos, fingerprints SHA-256, verdad); caché y manifest. Decisión previa: A5 descartado en Fase 5.
- **Dependencias a añadir:** servicios runtime n8n (Node) + Ollama + Telegram Bot API (internet saliente); libs Python HTTP + Telegram SDK (no en requirements); manejo de secretos (env/vault, nunca commiteado); Docker Compose + volúmenes, posible GPU passthrough; descarga de modelo (GBs).
- **VRAM/tiempo:** LLM 7B necesita ~4-8 GB VRAM (o CPU lento); contención con runtime TF si co-localizado. Generación + envío Telegram = segundos a decenas de segundos; debe ser async/background, nunca bloquear Streamlit. Riesgo de alucinación: el LLM no debe inventar números; el reporte debe estar anclado en hechos calculados (RUL, L_inf, umbrales) con validación.
- **Test impact:** suite actual ~209 tests. Nueva integración requiere HTTP mockeado y tests de payload determinista; tests live de n8n/Ollama/Telegram deben ser opcionales/saltados en CI. Riesgo de tests flaky y rotura de versiones en el build Docker pineado.
- **Recomendación:** RECHAZAR para la defensa (consistente con A5). No poner en path crítico ni demo. Si se persigue post-defensa: reporter opcional, async, fuera de proceso, consumiendo snapshot JSON del estado de flota/gemelo; LLM solo para prosa sobre hechos validados; secretos vía env/vault; feature-flag; totalmente mockeado en tests. Alternativa más barata: reporte MRO basado en plantilla con los mismos hechos calculados, evitando VRAM/tiempo/alucinación.

### #11 Simulador de flota desacoplado (n8n polling)

- **Concepto:** Streamlit solo pinta; un VPS/n8n envía telemetría (1 ciclo/seg) vía API a Streamlit.
- **Scores:** feas 3 / improve 9 / risk 10 (confirmados). Recomendación del propio estudio: RECHAZADO.
- **Verificación de ausencia de pub/sub (read-only):** `docker-compose.yml` solo `api` + `dashboard`; `requirements.txt` sin redis/kafka/paho-mqtt/websockets/celery/rq/amqp/nats/pulsar/zmq; ningún módulo Python importa broker/ws/streaming; `app/entrypoints/dashboard_ds02.py` no hace HTTP saliente ni expone WS/SSE; `app/services/api.py` no tiene ruta de ingesta de telemetría ni `/telemetry`/`/ingest`/suscripción. Streamlit es request/response por sesión, sin estado compartido ni canal de entrada.
- **Recomendación:** RECHAZAR. Mantener el simulador in-process y cache-backed (`app/lib/simulacion.py` + reloj en `st.session_state`). No añadir VPS/n8n, polling ni store compartido para una superficie de demo read-only.
- **Nota:** el subagente generó `docs/decisions/ADR-010-reject-decoupled-fleet-simulator-n8n-polling.md` (ver nota final).

## Estudio anterior (4 propuestas sueltas) — cruce con #1-#11

Las 4 propuestas analizadas antes de recibir la lista de 11 se solapan parcialmente:
- "Simulación de vuelo en tiempo real (animación ciclo a ciclo)" ↔ solapa con #1 (st.toast) y #3 (heatmap). Conclusión: no añadir animación con `time.sleep` en render por defecto; si se quiere, opt-in con fragment + animación nativa de Plotly.
- "Radiografía de fallo (radar Plotly scatterpolar)" ↔ #4. Conclusión: diferir (gap de datos de residuos).
- "Estética Control Center NASA (CSS personalizado)" ↔ no aparece en #1-#11. Conclusión previa: no inyectar CSS; usar theming nativo + tokens Python (riesgo 8).
- "Generación automática del parte de trabajo (LLM)" ↔ #10 (y parcialmente #8). Conclusión: diferir LLM; primero plantilla determinista.

## Ranking consolidado por recomendación

APROBADOS (bajo riesgo, alto valor):
- #2 Kanban operativo de flota
- #3 Heatmap de degradación sensorial
- #7 Auditoría criptográfica en vivo
- #8 Descarga de parte de trabajo (añadir PDF)

CONDICIONALES (implementar con guardas):
- #1 Simulador táctil con st.toast
- #5 Calculadora financiera ROI MRO
- #6 Data Leakage Trap toggle

DIFERIR (dependen de datos/infra no disponibles):
- #4 Radar de anomalías (residuos por sensor)
- #9 n8n webhook -> Telegram (post-defensa, dry-run)

RECHAZADOS (riesgo > beneficio para la defensa):
- #10 n8n + LLM MRO report
- #11 Simulador desacoplado n8n polling

## Nota sobre cambios no solicitados

Durante el estudio "solo lectura", el subagente del #11 creó un archivo nuevo: `docs/decisions/ADR-010-reject-decoupled-fleet-simulator-n8n-polling.md`. El resto del estudio no tocó código ni tests. Si se prefiere mantener el repo sin ese archivo, borrarlo manualmente o indicarlo.

## Fuentes

- Transcripts de subagentes en `C:\Users\mikel\AppData\Local\hermes\cache\delegation\live\deleg_33f3c26e\` (propuestas 1-6) y `deleg_a489a190\` (propuestas 7-11).
- Código y caché verificados directamente contra el repo (read-only).
- Plan previo: `docs/plans/plan-prioridad-y-riesgo-2026-10-24.md` (decisión A5 descartada).
", "path">
docs/estudio-propuestas-wow-streamlit.md