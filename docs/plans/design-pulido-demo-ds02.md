# Design: Pulido demo DS02 (adopta docs/plans/ejecucion-planStreamlit.md §6)

## Decisión C1 (bloqueante resuelto)
Tablero no lee flota de session_state; `fleet_snapshot` solo ve units de caché (11/14/15). Solución adoptada:
- Alta = lectura puntuada de caché con `unit_id` sintético negativo `PREFIJO_ALTA=-1000 - indice`, rango que no colisiona con caché(11/14/15), live(-1), twins(0).
- Dos frames: `frame_cache` (métricas/telemetría globales, solo caché) y `frame` (caché+altas para flota/órdenes). Métricas globales nunca cuentan doble.
- Estado = `min(lower)` del ciclo concreto (`cycle==ciclo`), no mínimo del prefijo. Ej: U11 ciclo 20 estado 29.28 (INSPECCIÓN), prefijo mín 25.53 misma banda pero distinto número.
- `app/ui_alta.py` puro: `PERFILES`, `unidad_alta(i)`, `ventanas_de_alta(windows,unidad,ciclo_hasta,unit_id)`, `estado_demo()`. ValueError si recorte vacío (U14 pide 1-2, U15 pide 1).
- Sidebar form: matrícula (normalizar_id MIN_ID=3) + selector PERFILES + botón. Guarda recorte en `st.session_state["altas"]` (lista dfs) y `st.rerun()`. Frame = concat(cache, altas).

## Decisión C2
Botón "Cargar escenario demo" junto a Reset (`:969-982`). Escribe claves exactas: `preset="Normal"`, `th_apto_Normal=30.0`, `th_aog_Normal=25.0`, `unit=14`, `cycle=29`, limpia twins/hangar. Requiere `import ui_alta as A`.

## Decisión C3
Panel tras badges (`:376-389`) antes de `st.tabs(:391)` con 3x `st.metric` desde `global_metrics/critical_mae/grounded` ya calculados (`:348-365`) + caption peor-caso. No duplicar help de pestaña 1.

## Orden y dependencias
T1 C2 (sin deps) + T2 C3 (sin deps) paralelizables -> T3 C1 (requiere T1/T2 verdes por tocar mismo dashboard) -> verificación final. C4 excluido.

## Riesgos
- Claves `th_apto_{preset}` frágiles si cambia preset -> usar `estado_demo()` centralizado.
- Altas duplican ventanas si se recalcula métrica global -> mitigado con doble frame.
- C4 cosmético/credibilidad -> fuera.

## Checkpoints
Gate1 C2: 30/25/29/14 + hangar=1. Gate2 C3: paridad 3 cifras + guards verdes. Gate3 C1: presets en banda + AppTest alta + `pytest -q`.
