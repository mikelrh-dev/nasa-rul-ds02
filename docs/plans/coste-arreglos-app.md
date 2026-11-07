# Coste de arreglar defectos de la app Streamlit

Fecha: 2026-11-06
Estado: PLAN, sin ejecutar. Excluidos por el usuario: respuesta individual, MLflow y n8n por ahora.
Ningún arreglo toca notebooks, todo es app/.py y docs/resultados.

| # | Defecto | Fichero:línea | ¿Toca notebook? | Riesgo 0-10 | Mejora 0-10 | Coste |
|---|---|---|---|---|---|---|
| 1 | SHAP waterfall roto totals | app/ui_shap.py:251-262 (258 totals=[float(base)]), llamado en app/dashboard_ds02.py:487 | NO | 2 | 9 | 1 línea, 1 fichero |
| 7 | Multisemilla sin reconciliar | src/clase/evaluar_c_multisemilla.py:93-114 + resultados/*.csv + 5 docs | NO, docs/resultados | 3 | 7 | 0 líneas app, 1 regeneración CSV + 5-6 citas |
| 5 | R9 invisible en Motor si APTO | app/ui_modulos/_tab_motor.py:225-230 vs _tab_flota.py:687-718 | NO | 3 | 6 | ~15 líneas, 1 fichero solo vista |
| 6 | 6,196 vs 6.196 | app/dashboard_ds02.py:745-746,918,932 + 4 ficheros con :, | NO | 2 | 4 | ~12 call sites, 1 helper nuevo |
| 3 | Preset no restaura 30/25 (quedan 35/20) | app/ui_modulos/_tab_flota.py:392-410 + app/dashboard_ds02.py:584-589 | NO | 4 | 7 | ~20 líneas, 1-2 ficheros |
| 2 | Incorporar 3→5, Reset 5→4 (no a 3) | app/dashboard_ds02.py:671,682,725-743 + app/flota.py:99-136 | NO | 6 | 9 | ~30 líneas, 2-3 ficheros |
| 4 | Switch Aplicar corrección click interceptado | app/ui_modulos/_tab_flota.py:413-423 | NO | 3 | 3 | ~5 líneas, 1 fichero |

Orden: mejora/riesgo descendente (1 > 7 > 5 > 6 > 3 > 2 > 4).

## Detalle

1. **SHAP waterfall.** Causa en ui_shap.py:258: go.Waterfall con totals=[float(base)]. Plotly valida totals como número escalar, no lista. Arreglo: quitar totals o totals=float(base); si se quiere barra final, añadir "total" a measure. Alternativa: reutilizar shap_waterfall_png de ui_shap.py:288-295 (Matplotlib, funciona). Test: no hay; tests/test_mejoras_streamlit.py:68-76 solo comprueba que existe shap_waterfall_fig, nunca la construye.
2. **Flota.** No es caché. Es doble fuente en el muro: tarjetas_cache (857-875, frame_con_altas con _altas()) más tarjetas_gemelos (811-850, twins en memoria). Incorporar (dashboard_ds02.py:682,686-714) escribe ambos (alta + gemelo + _guardar_registros), por eso 1 alta = 2 tarjetas. Reset (725-743) solo hace quitar_alta sobre altas (flota.py:129-135) y guarda; nunca borra twins ni hangar. Fichero activo no es app/registros_flota.json (legacy vacío) sino app/registros_sesiones/registros_flota_<session>.json (hangar.py:189-193). Test: tests/test_flota.py solo prueba la función pura; test_fleet_registries_session.py y test_dss_interaction.py no prueban Reset contra gemelos.
3. **Preset.** Estado no sincronizado. Claves por preset th_apto_{preset} (_tab_flota.py:401,407) + lectura session_state.get (dashboard_ds02.py:588-589). Streamlit ignora value= cuando la clave ya existe. Agravante: modo historia paso 4 (ui_alta.py:130-132 blandos = 35/20) se escribe en la clave del preset vigente vía _umbrales_pendientes (dashboard_ds02.py:584-587 + _tab_flota.py:484). Si el preset era Normal, la Normal queda contaminada y volver no restaura 30/25. Test: ninguno de preset/spin.
4. **Toggle.** _tab_flota.py:413 st.toggle dentro de @st.fragment. Sin CSS propio. Click en el label es el hit-target frágil de Streamlit+Playwright; evaluate sobre el input sí dispara porque la lógica está bien (dashboard_ds02.py:596). Label/control, no CSS. Workaround actual funcional; cambiar a st.checkbox o on_change es cosmética. Test: ninguno del toggle.
5. **R9.** Diseño, no falta de evaluación. src/mia/motor.py:40-68 elige solo la regla ganadora (R1 10 > R10 9 > R11 8 > R9 3 > R8 2 > R7 1, reglas.py:254-271) y usadas solo lleva la ganadora. En APTO solo puede salir R7. Motor (_tab_motor.py:225) pinta solo Regla que decide + porque de la ganadora. Flota (687-718) además pinta traza_decision + catálogo completo, de ahí que R9 se vea allí. Reglas evaluadas-no-disparadas no se devuelven; habría que evaluar si_R* por separado. Test: test_audit_fixes.py, test_mia_rules.py cubren motor, no la vista de Motor.
6. **Formato.** Es f"{n:,}" de Python, separador coma sin locale. 11 sitios: dashboard_ds02.py (745,746,918,932,245,247,1738-1744), _tab_flota.py:529, _tab_auditoria.py:313, ui_batch.py:50-51,60, ui_inference.py:59-60,499-500. Arreglo español: helper fmt_miles en ui_data_loader.py y cambiar los ~12 usos; no usar locale global. Tests que romperían: tests/test_live_eval.py:79-80 aserta f"{MAX:,}" literal.
7. **Multisemilla.** Docs/resultados, no app. bundle_c_multiseed.csv solo trae 7 (4.429) y 123 (4.336); comparativa_c_multisemilla.csv añade 42 desde manifiesto (4.338) y media 4.368±0.053. Divergentes: NB05 4.330, NB06 4.322±0.064, ADR-011 4.347±0.012. Cierre sin reentrenar: python -m src.clase.evaluar_c_multisemilla --desde-csv (evaluar_c_multisemilla.py:93-114,126) reconstruye la tabla desde evidencia ya medida; luego homogeneizar citas en README.md:115-116, AGENT.md:6, README.en.md:62,179, ADR-011:19,54, LEARNING_LOG.md:100 y notas de autoridad de notebooksMD/06:559. No reeditar .ipynb con salidas históricas; la fuente es models/ds02_manifest.json (seed 42 manda). Test: tests/test_clase_c_multisemilla.py:63-76.

## Qué NO se toca sin orden

- Notebooks, outputs guardados, execution_count, CSVs históricos, joblibs, keras y manifiesto, salvo la regeneración CSV de multisemilla acordada.
- MLflow, n8n y respuesta individual: excluidos por el usuario por ahora.
- Git push sin orden explícita.
