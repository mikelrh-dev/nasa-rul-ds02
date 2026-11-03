"""T5 (parte 1) — repaso storytelling 01_eda.ipynb. Solo markdown, sin re-ejecucion."""
import json
import pathlib

NB = pathlib.Path('notebooks/01_eda.ipynb')

GLOSARIO = '''## Glosario rapido (para seguir el notebook sin perderte)

| Palabra | Que significa aqui |
|---|---|
| RUL | Ciclos que le quedan al motor. Es lo que predecimos (numero, no categoria: regresion). |
| MAR | El nulo tiene causa conocida (aqui: la sonda T30 se pierde en crucero alto). Se puede modelar. |
| MCAR | El nulo cae al azar, sin causa. Mas facil de ignorar, menos realista. |
| ffill causal | Rellenar cada hueco con el ultimo valor *anterior* del mismo motor. Nunca mira al futuro: sin fuga. |
| Fuga (leakage) | Usar en entreno informacion que en produccion no tendrias (p. ej. medianas del test, o filas futuras). Invalida el experimento. |
| OneHot | Convertir `fase_vuelo` en 3 columnas 0/1 (Ascenso/Crucero/Descenso) para que el modelo la pueda usar. |
| Split por motor | Entrenar con unos motores y probar con otros distintos (11/14/15). Si mezclas filas del mismo motor en ambos lados, el modelo "recuerda" en vez de generalizar. |

> Como leer este notebook: cada figura trae su QUÉ VEO (lo literal) y su CONCLUSIÓN (qué decisión de modelado sale de ahí). Si solo tienes 5 minutos, lee los títulos + conclusiones.'''

TIP_FUGA = '''
> TIP (fuga): las medianas de imputacion se calculan SOLO con train y se aplican a test. Si las calcularas con todo el dataset, el test "contaminaria" el entreno y el RMSE mentiria a la baja. Lo mismo con `fase_vuelo`: solo usa alt/Mach (régimen), nunca sensores ni RUL.'''

PROV = '''
**Procedencia de los datos:** `data/raw/DS02*.hdf5` (original NASA, intacto) → `track_clase/dataset_clase.py` (inyecta MAR + imputa + fase) → `data/processed/train|test.parquet` (lo que carga este notebook). La auditoría vive en `data/processed/auditoria_nulos.json`.'''

nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']

# Idempotencia.
cells = [c for c in cells
         if not (c['cell_type'] == 'markdown'
                 and any(m in ''.join(c.get('source', []))
                         for m in ['Glosario rapido', 'TIP (fuga)',
                                   'Procedencia de los datos']))]

# 1. Glosario tras la celda SAA 1/2 (indice 1).
cells.insert(2, {'cell_type': 'markdown', 'metadata': {}, 'source': [GLOSARIO]})

# 2. "Como leer" en cada cabecera de figura.
GUIAS = {
    'Fig.1': 'Lee primero la altura de Crucero: ahí vive el MAR de T30.',
    'Fig.2': 'Fíjate en la cola de la derecha (motores jóvenes) y en que T48 separa fases: el régimen manda.',
    'Fig.4': 'Cada símbolo es una fase; si se mezclaran, los umbrales estarían mal.',
    'Fig.5': 'Mira la última fila/columna (RUL): correlaciones débiles = una fila no basta.',
}
for c in cells:
    if c['cell_type'] == 'markdown':
        src = ''.join(c.get('source', []))
        for k, g in GUIAS.items():
            if src.startswith(f'## {k}') and 'Cómo leer' not in src:
                c['source'] = [src.rstrip() + f'\n*Cómo leer: {g}*\n']

# 3. Cierre: TIP fuga + procedencia.
for c in cells:
    if c['cell_type'] == 'markdown' and ''.join(c.get('source', []))\
            .startswith('## Cierre EDA'):
        c['source'] = [''.join(c.get('source', [])).rstrip()
                       + '\n' + TIP_FUGA + '\n' + PROV + '\n']

nb['cells'] = cells
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'01: {len(cells)} celdas. Repaso listo.')
