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
Estado/registro lib/flota.py lib/hangar.py lib/twin.py lib/alta.py lib/simulacion.py
Datos/modelo   lib/ui_data_loader.py lib/ui_inference.py lib/ui_shap.py lib/rules.py
Presentacion   lib/dashboard_helpers.py lib/pdf_partes.py lib/batch.py lib/n8n_payload.py
API            services/api.py
```

## Una línea por fichero

| Fichero | Qué hace |
|---|---|
| `entrypoints/streamlit_app.py` | Entry point de la rúbrica: secretos, `sys.modules.pop` para el rerun y `import app.entrypoints.dashboard_ds02`. |
| `entrypoints/dashboard_ds02.py` | Orquestador: carga la caché, construye `AppCtx`, monta sidebar y las 4 pestañas. |
| `lib/context.py` | `AppCtx`: transporte único de datos, estado y helpers hacia las pestañas. |
| `lib/_constantes.py` | Dueño único de los umbrales 25/20 (ADR-013), sin Streamlit. |
| `lib/theme.py` | Dueño único de los design tokens y helpers de Plotly (`chart_layout`, `style_axes`, `fig_deriva`). |
| `ui/__init__.py` | Fachada del paquete; re-exporta `_sha256_cached`. |
| `ui/_paneles.py` | Paneles compartidos: `preflight_panel`, `shap_panel` y las tarjetas del muro. |
| `ui/_sidebar.py` | Barra lateral: vista, unidad de test, reloj y altas de flota. Devuelve `SidebarState`. |
| `ui/_tab_flota.py` | Pestaña Flota: muro del hangar, tarjetas, cola y descargas. |
| `ui/_tab_motor.py` | Pestaña Motor: curva, banda, alarmas, SHAP y órdenes de un motor. |
| `ui/_tab_casos.py` | Pestaña Casos nuevos: alta en lote, registro y SHAP de la unidad elegida. |
| `ui/_tab_auditoria.py` | Pestaña Auditoría: procedencia, contraste, reglas e informe PDF. |
| `ui/_sandbox_estres.py` | Panel de estrés: escenarios y puntuación. |
| `lib/flota.py` | Registro de motores: una clave y una etiqueta para todas las vistas. |
| `lib/hangar.py` | Persistencia del registro: JSON por sesión, migración del legacy, escritura atómica. |
| `lib/twin.py` | Gemelo digital: serie guardada, vista de resultado y órdenes. |
| `lib/alta.py` | Alta de motor nuevo: clave sintética (`PREFIJO_ALTA`) y estado del formulario. |
| `lib/ui_data_loader.py` | Lee `app/cache/`, calcula métricas, curvas, snapshots y SHA. |
| `lib/ui_inference.py` | Puntúa motores en vivo: ventanas, banda conformal, avisos. |
| `lib/rules.py` | Capa de reglas: corrección (pasada B) y decisión (pasada A). |
| `lib/ui_shap.py` | Panel SHAP: importancia global y waterfall (sin TensorFlow). |
| `lib/batch.py` | Ingesta por lotes desde CSV (varios motores). |
| `lib/n8n_payload.py` | Construye el payload y llama al webhook de n8n. |
| `lib/simulacion.py` | Simulación «qué pasaría si» sobre la flota. |
| `lib/sandbox.py` | Puntuación del tramo del sandbox (preflight + score + decisión), cacheada. |
| `lib/informe_auditoria.py` | Informe de auditoría en PDF: las dos tablas que pide un tribunal. |
| `lib/pdf_partes.py` | Genera el parte de trabajo en PDF. |
| `lib/dashboard_helpers.py` | Helpers puros sin Streamlit: CSV de contraste/trayectoria, cola filtrada, vista de reglas, sonda n8n. |
| `services/api.py` | API FastAPI (`/predict`, `/units`) con token e idempotencia. |
| `_paths.py` | Único dueño de las rutas del repositorio (`ROOT`, `APP_DIR`, `CACHE_DIR`, registros, secretos). |

## Cómo se lee una pestaña

Las dos pestañas grandes (`_tab_flota.py`, `_tab_casos.py`) siguen el mismo
patrón: **preámbulo de alias, funciones anidadas con nombre y un cuerpo que es
el guion de la pantalla**.

```python
def _tab_flota(ctx: AppCtx) -> None:
    frame = ctx.frame                    # 1. preámbulo: alias del AppCtx

    def _muro_del_hangar_ui() -> None:   # 2. cada bloque, su función
        ...

    _muro_del_hangar_ui()                # 3. el cuerpo, el orden visual
    _cronologia_estado()
```

| Regla | Por qué |
|---|---|
| Las funciones no reciben parámetros: leen los alias por clausura. | El estado compartido ya viaja en el `AppCtx`; repetirlo en cada firma es ruido. |
| El orden de las llamadas es el orden de la pantalla. | Para saber qué ve el usuario se lee el final del fichero, no los 900 renglones de arriba. |
| Un bloque nuevo = una `def` más una llamada. | No obliga a tocar los demás bloques ni el preámbulo. |
| Dos sentencias que comparten estado (`if correccion`, un `st.info` que depende de lo anterior) se quedan en el cuerpo. | Envolverlas obligaría a inventar parámetros y a reordenar la ejecución. |
| La pestaña no se reparte en módulos más pequeños. | `tests/test_app_fixes2.py` lee el fuente y exige `@st.fragment` y `scope="app"` ahí; partirlo rompe la paginación del muro. |

Orden en `_tab_flota`: muro → taller → avance → sesión → cola → historial →
reglas → orden de trabajo → gemelos → detalle → ciclo de vida. En `_tab_casos`: lote → ejemplo → ciclo → unidad nueva →
resultado → sandbox → SHAP.

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
