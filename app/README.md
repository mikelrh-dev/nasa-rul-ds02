# `app/` — mapa de la aplicación

Dos runtimes conviven aquí:

| Runtime | Entry point | Comando |
|---|---|---|
| Streamlit (DSS) | `streamlit_app.py` | `streamlit run app/streamlit_app.py` |
| FastAPI (API) | `api.py` (`app = FastAPI(...)`) | `uvicorn app.api:app --port 8000` |

`streamlit_app.py` es el nombre que pide la rúbrica; solo carga secretos, fuerza
el rerun y delega en `dashboard_ds02.py`.

## Capas

```
Entrada        streamlit_app.py
Orquestador    dashboard_ds02.py      globals, cachés, montaje de las 4 pestañas
Contexto       context.py             AppCtx: un objeto en vez de 18-29 parámetros
Barra lateral  ui_modulos/_sidebar.py devuelve SidebarState (unidad elegida)
Pestañas       ui_modulos/_tab_*.py   fragmentos de Streamlit
Tema           theme.py               colores, `chart_layout`, `style_axes`, `fig_deriva`
Estado puro    flota.py hangar.py twin.py ui_alta.py
Datos/modelo   ui_data_loader.py ui_inference.py ui_shap.py ui_rules.py
Presentación   dashboard_helpers.py pdf_partes.py ui_batch.py ui_n8n.py simulacion.py
Otro runtime   api.py
```

## Una línea por fichero

| Fichero | Qué hace |
|---|---|
| `streamlit_app.py` | Entry point de la rúbrica: secretos, `sys.modules.pop` para el rerun y `import dashboard_ds02`. |
| `dashboard_ds02.py` | Orquestador: carga la caché, construye `AppCtx`, monta sidebar y las 4 pestañas. |
| `context.py` | `AppCtx`: transporte único de datos, estado y helpers hacia las pestañas. |
| `theme.py` | Design tokens y helpers de Plotly (`chart_layout`, `style_axes`, `fig_deriva`). |
| `ui_modulos/__init__.py` | Fachada del paquete; re-exporta `_sha256_cached`. |
| `ui_modulos/_sidebar.py` | Barra lateral: vista, unidad de test, reloj y altas de flota. Devuelve `SidebarState`. |
| `ui_modulos/_tab_flota.py` | Pestaña Flota: muro del hangar, tarjetas, cola y descargas. |
| `ui_modulos/_tab_motor.py` | Pestaña Motor: curva, banda, alarmas, SHAP y órdenes de un motor. |
| `ui_modulos/_tab_casos.py` | Pestaña Casos nuevos: alta en lote, registro y SHAP de la unidad elegida. |
| `ui_modulos/_tab_auditoria.py` | Pestaña Auditoría: procedencia, contraste, reglas e informe PDF. |
| `ui_modulos/_sandbox_estres.py` | Panel de estrés: escenarios y puntuación. |
| `flota.py` | Registro de motores: una clave y una etiqueta para todas las vistas. |
| `hangar.py` | Persistencia del registro: JSON por sesión, migración del legacy, escritura atómica. |
| `twin.py` | Gemelo digital: serie guardada, vista de resultado y órdenes. |
| `ui_alta.py` | Alta de motor nuevo: clave sintética (`PREFIJO_ALTA`) y estado del formulario. |
| `ui_data_loader.py` | Lee `app/cache/`, calcula métricas, curvas, snapshots y SHA. |
| `ui_inference.py` | Puntúa motores en vivo: ventanas, banda conformal, avisos. |
| `ui_rules.py` | Capa de reglas: corrección (pasada B) y decisión (pasada A). |
| `ui_shap.py` | Panel SHAP: importancia global y waterfall (sin TensorFlow). |
| `ui_batch.py` | Ingesta por lotes desde CSV (varios motores). |
| `ui_n8n.py` | Construye el payload y llama al webhook de n8n. |
| `simulacion.py` | Simulación «qué pasaría si» sobre la flota. |
| `pdf_partes.py` | Genera el parte de trabajo en PDF. |
| `dashboard_helpers.py` | Helpers puros sin Streamlit: CSV de contraste/trayectoria, cola filtrada, vista de reglas, sonda n8n. |
| `api.py` | API FastAPI (`/predict`, `/units`) con token e idempotencia. |

## Reglas de la carpeta

- **No muevas `streamlit_app.py`**: es el entry point de la rúbrica.
- **No ejecutes UI al importar** un módulo de `ui_modulos/`: `streamlit_app.py`
  saca `dashboard_ds02` de `sys.modules` en cada rerun, pero los módulos
  importados no se re-ejecutan. Expón funciones (`@st.fragment`) y llama desde
  el dashboard.
- **`app/` está en `sys.path`**: los imports son planos (`import flota`), no
  `app.flota`. Los tests hacen lo mismo.
- `app/cache/` es derivado y se regenera con `scripts/build/build_ui_cache.py`;
  `registros_*` y `registros_sesiones/` son estado runtime (ignorados en git).
