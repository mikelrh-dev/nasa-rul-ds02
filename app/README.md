# `app/` — mapa de la aplicación

Dos runtimes conviven aquí:

| Runtime | Entry point | Comando |
|---|---|---|
| Streamlit (DSS) | `entrypoints/streamlit_app.py` | `streamlit run app/entrypoints/streamlit_app.py` |
| FastAPI (API) | `services/api.py` (`app = FastAPI(...)`) | `uvicorn app.services.api:app --port 8000` |

`entrypoints/streamlit_app.py` es el nombre que pide la rúbrica; solo carga
secretos, fuerza el rerun y delega en `entrypoints/dashboard_ds02.py`.

## Capas

```
Entrada        entrypoints/streamlit_app.py
Orquestador    entrypoints/dashboard_ds02.py   globals, cachés, montaje de las 4 pestañas
Contexto       lib/context.py                  AppCtx: un objeto en vez de 18-29 parámetros
Barra lateral  ui/_sidebar.py                  devuelve SidebarState (unidad elegida)
Pestañas       ui/_tab_*.py                    fragmentos de Streamlit
Tema           lib/theme.py                    dueno unico de tokens, `chart_layout`, `style_axes`, `fig_deriva`
Estado puro    lib/flota.py lib/hangar.py lib/twin.py lib/ui_alta.py lib/simulacion.py
Datos/modelo   lib/ui_data_loader.py lib/ui_inference.py lib/ui_shap.py lib/ui_rules.py
Presentacion   lib/dashboard_helpers.py lib/pdf_partes.py lib/ui_batch.py lib/ui_n8n.py
API            services/api.py
```

## Una línea por fichero

| Fichero | Qué hace |
|---|---|
| `entrypoints/streamlit_app.py` | Entry point de la rúbrica: secretos, `sys.modules.pop` para el rerun y `import app.entrypoints.dashboard_ds02`. |
| `entrypoints/dashboard_ds02.py` | Orquestador: carga la caché, construye `AppCtx`, monta sidebar y las 4 pestañas. |
| `lib/context.py` | `AppCtx`: transporte único de datos, estado y helpers hacia las pestañas. |
| `lib/theme.py` | Dueño único de los design tokens y helpers de Plotly (`chart_layout`, `style_axes`, `fig_deriva`). |
| `ui/__init__.py` | Fachada del paquete; re-exporta `_sha256_cached`. |
| `ui/_sidebar.py` | Barra lateral: vista, unidad de test, reloj y altas de flota. Devuelve `SidebarState`. |
| `ui/_tab_flota.py` | Pestaña Flota: muro del hangar, tarjetas, cola y descargas. |
| `ui/_tab_motor.py` | Pestaña Motor: curva, banda, alarmas, SHAP y órdenes de un motor. |
| `ui/_tab_casos.py` | Pestaña Casos nuevos: alta en lote, registro y SHAP de la unidad elegida. |
| `ui/_tab_auditoria.py` | Pestaña Auditoría: procedencia, contraste, reglas e informe PDF. |
| `ui/_sandbox_estres.py` | Panel de estrés: escenarios y puntuación. |
| `lib/flota.py` | Registro de motores: una clave y una etiqueta para todas las vistas. |
| `lib/hangar.py` | Persistencia del registro: JSON por sesión, migración del legacy, escritura atómica. |
| `lib/twin.py` | Gemelo digital: serie guardada, vista de resultado y órdenes. |
| `lib/ui_alta.py` | Alta de motor nuevo: clave sintética (`PREFIJO_ALTA`) y estado del formulario. |
| `lib/ui_data_loader.py` | Lee `app/cache/`, calcula métricas, curvas, snapshots y SHA. |
| `lib/ui_inference.py` | Puntúa motores en vivo: ventanas, banda conformal, avisos. |
| `lib/ui_rules.py` | Capa de reglas: corrección (pasada B) y decisión (pasada A). |
| `lib/ui_shap.py` | Panel SHAP: importancia global y waterfall (sin TensorFlow). |
| `lib/ui_batch.py` | Ingesta por lotes desde CSV (varios motores). |
| `lib/ui_n8n.py` | Construye el payload y llama al webhook de n8n. |
| `lib/simulacion.py` | Simulación «qué pasaría si» sobre la flota. |
| `lib/pdf_partes.py` | Genera el parte de trabajo en PDF. |
| `lib/dashboard_helpers.py` | Helpers puros sin Streamlit: CSV de contraste/trayectoria, cola filtrada, vista de reglas, sonda n8n. |
| `services/api.py` | API FastAPI (`/predict`, `/units`) con token e idempotencia. |
| `_paths.py` | Único dueño de las rutas del repositorio (`ROOT`, `APP_DIR`, `CACHE_DIR`, registros, secretos). |

## Reglas de la carpeta

- **No muevas `entrypoints/streamlit_app.py`**: es el entry point de la rúbrica.
- **No ejecutes UI al importar** un módulo de `ui/`: `streamlit_app.py`
  saca `app.entrypoints.dashboard_ds02` de `sys.modules` en cada rerun, pero
  los módulos importados no se re-ejecutan. Expón funciones (`@st.fragment`) y
  llama desde el dashboard.
- **La raíz del repo está en `sys.path`**, no `app/`: el entrypoint la añade
  antes de importar `app.*`. Los imports son de paquete
  (`from app.lib import flota`), nunca planos (`import flota`). Los tests
  insertan la raíz del repo y usan el mismo estilo.
- `app/cache/` está trackeado en git (3 ficheros) y se regenera con
  `scripts/build/build_ui_cache.py`; `registros_*` y `registros_sesiones/` son
  estado runtime (ignorados en git).
