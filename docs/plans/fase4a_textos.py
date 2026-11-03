"""Fase 4a: textos P1-P5 + P8 (sin ejecucion).

P1: termino explicito 'IA fuerte' en 01_eda celda 1.
P2: tabla de 14 sensores individual en 01_eda celda 3 y track README.
P3: captura app_clase.png referenciada (track README link roto + README raiz).
P4: cuantificacion negocio (AOG) en track README.
P5: seccion negocio en README raiz.
P8: scripts/README.md (vigente vs legacy).
"""
import json
import pathlib

ROOT = pathlib.Path('.')

# ---------------- P1 + P2 en 01_eda ----------------
p = ROOT / 'notebooks/01_eda.ipynb'
nb = json.loads(p.read_text(encoding='utf-8'))
c1 = ''.join(nb['cells'][1]['source'])
assert 'IA débil' in c1
c1 = c1.replace(
    '- **IA débil**: solo predice RUL de DS02 a partir de telemetría aprendida. '
    'No sabría fijar precios ni atender llamadas. Ventaja: barata, rápida, auditable.',
    '- **IA débil**: solo predice RUL de DS02 a partir de telemetría aprendida. '
    'Una **IA fuerte** (AGI: fijar precios, atender llamadas, razonar en cualquier dominio) '
    'no existe aquí: el sistema no transfiere nada fuera de DS02. '
    'Ventaja de lo débil: barata, rápida, auditable.')
nb['cells'][1]['source'] = [c1]

SENSores = (
    '| T24 | temp. salida LPC (°R) | numérica | 0% | 0% |',
    '| T30 | temp. salida HPC (°R) — sonda con dropout | numérica | ~1.8% MAR (crucero alto) | 0% tras ffill+mediana |',
    '| T48 | temp. salida HPT (°R) | numérica | 0% | 0% |',
    '| T50 | temp. salida LPT (°R) | numérica | 0% | 0% |',
    '| P15 | presión sangrado (psia) | numérica | 0% | 0% |',
    '| P2 | presión entrada fan (psia) | numérica | 0% | 0% |',
    '| P21 | presión salida LPC (psia) | numérica | 0% | 0% |',
    '| P24 | presión salida HPC (psia) | numérica | 0% | 0% |',
    '| Ps30 | presión estática HPC (psia) | numérica | 0% | 0% |',
    '| P40 | presión total HPT (psia) | numérica | 0% | 0% |',
    '| P50 | presión total LPT (psia) | numérica | 0% | 0% |',
    '| Nf | rpm del fan | numérica | 0% | 0% |',
    '| Nc | rpm del núcleo | numérica | 0% | 0% |',
    '| Wf | caudal combustible (pps) | numérica | 0% | 0% |',
)
c3 = ''.join(nb['cells'][3]['source'])
old_row = '| T24..Wf (14) | sensores / estaciones motor | numéricas | ~1.8% MAR en T30 | 0% tras ffill+mediana |'
assert old_row in c3
c3 = c3.replace(old_row, '\n'.join(SENSores))
nb['cells'][3]['source'] = [c3]
p.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('01_eda: P1+P2 ok')

# ---------------- P2 + P4 + P3 + SHAP-fix en track README ----------------
t = ROOT / 'track_clase/README.md'
tx = t.read_text(encoding='utf-8')
old_t = '| `T24..Wf` (14) | Sensores del motor | numéricas | ~1.8% MAR solo en T30 | 0% tras ffill+mediana train |'
assert old_t in tx
tx = tx.replace(old_t, '\n'.join('|' + s[1:] for s in
    ('| `T24` | Temp. salida LPC (°R) | numérica | 0% | 0% |',
     '| `T30` | Temp. salida HPC (°R), sonda con dropout | numérica | ~1.8% MAR (crucero alto) | 0% tras ffill+mediana |',
     '| `T48` | Temp. salida HPT (°R) | numérica | 0% | 0% |',
     '| `T50` | Temp. salida LPT (°R) | numérica | 0% | 0% |',
     '| `P15` | Presión sangrado (psia) | numérica | 0% | 0% |',
     '| `P2` | Presión entrada fan (psia) | numérica | 0% | 0% |',
     '| `P21` | Presión salida LPC (psia) | numérica | 0% | 0% |',
     '| `P24` | Presión salida HPC (psia) | numérica | 0% | 0% |',
     '| `Ps30` | Presión estática HPC (psia) | numérica | 0% | 0% |',
     '| `P40` | Presión total HPT (psia) | numérica | 0% | 0% |',
     '| `P50` | Presión total LPT (psia) | numérica | 0% | 0% |',
     '| `Nf` | RPM del fan | numérica | 0% | 0% |',
     '| `Nc` | RPM del núcleo | numérica | 0% | 0% |',
     '| `Wf` | Caudal combustible (pps) | numérica | 0% | 0% |')))

# P4: cuantificacion (estimacion declarada como tal)
old_neg = ('| Referencia externa | Las aerolíneas programan hangar por horas de vuelo; aquí por RUL predicha |')
assert old_neg in tx
tx = tx.replace(old_neg, old_neg + '
| Cuánto vale acertar (rango Boeing, credibilidad Media) | Un AOG imprevisto cuesta 10.000–15.000 USD/h (≈240.000–360.000 USD/día); '
    'una inspección programada cuesta una fracción. Evitar una sola parada no planificada al año paga el sistema. Fuente: costes_reales_aeronauticos.md §1. |')

# P3: link roto dashboard_ds02.png -> captura real app_clase.png
old_img = '![App de producción](../resultados/dashboard_ds02.png)'
assert old_img in tx
tx = tx.replace(old_img, '![App del track de clase](../resultados/app_clase.png)\n\n*Captura real de la app del track (métricas + caso nuevo con decisión de reglas). '
    'La del dashboard de producción va en el README raíz.*')

# SHAP: XGB, no LGBM del hibrido
old_shap = '**Qué pesan más (SHAP TreeExplainer, LightGBM del híbrido):**'
assert old_shap in tx
tx = tx.replace(old_shap, '**Qué pesan más (SHAP TreeExplainer exacto, XGB con mejores hiperparámetros de `comparativa.csv`, fondo 200 train):**')
t.write_text(tx, encoding='utf-8')
print('track README: P2+P3+P4+SHAP ok')

# ---------------- P5 + P3 en README raiz ----------------
r = ROOT / 'README.md'
rx = r.read_text(encoding='utf-8')
anchor = 'Lo de abajo es el sistema en producción (bundle B congelado, RMSE 4.251).'
assert anchor in rx
bloque = anchor + '''

![App del track de clase](resultados/app_clase.png)

*Captura real de la app Streamlit del track académico (métricas en test + caso nuevo con decisión de reglas).*

## La necesidad de negocio

Taller MRO con flota DS02: un motor parado en pista (AOG) cuesta del orden de 10.000–15.000 USD/h (rango Boeing, credibilidad Media); una inspección a tiempo cuesta una fracción. Hoy la decisión de hangar depende de juicio experto sin número.

**Objetivo:** predecir la RUL de cada motor para que el jefe de taller decida APTO / INSPECCIÓN / HANGAR, con la predicción convertida en decisión por reglas (`mia/`, 6 con prioridad + seguridad R1) y, más adelante, en acción automática vía n8n. Evitar una sola parada no planificada al año paga el sistema. Detalle académico: [`track_clase/README.md`](track_clase/README.md).'''
rx = rx.replace(anchor, bloque)
r.write_text(rx, encoding='utf-8')
print('README raiz: P3+P5 ok')

# ---------------- P8: scripts/README.md ----------------
(ROOT / 'scripts/README.md').write_text(
    '# scripts/ — vigente vs legacy\n\n'
    '## Vigente (se usa)\n\n'
    '- `build_ui_cache.py` — genera `app/cache/` (ventanas demo + provenance).\n'
    '- `freeze_rules_evidence.py` — evidencia congelada de reglas (gate de tests).\n'
    '- `predict_ds02.py` — inferencia CLI sobre el bundle.\n'
    '- `build_02_notebook.py`, `build_05_notebook.py` — generan notebooks congelados de referencia.\n\n'
    '## Legacy (no tocar, solo historia)\n\n'
    '- `finalize_v2.py`, `finalize_v3.py`, `inspect_v2_v3.py`, `execute_baseline_cells.py`, `extract_legacy_artifact.py` — era FD001/v2-v3.\n'
    '- `ablate_meta_cycle.py`, `p0_density_control.py`, `p1_*.py` — experimentos de un solo uso ya registrados.\n'
    '- `ajustar_notebook.py`, `add_v3_notebook.py`, `dump_cells.py`, `inspect_cells.py`, `build_and_run_notebook.py` — utilidades de edición de notebooks.\n'
    '- `*.npy`, `nb_exec_v4*.log` — restos de ejecuciones (ignorados por git).\n',
    encoding='utf-8')
print('scripts/README.md: P8 ok')
print('FASE 4a OK')
