"""Fase 1: higiene notebooks 02-05 (JSON-only, sin re-ejecucion).

1. kernelspec python3 (copiado de 01_eda) en 02-05.
2. 05: mueve celda '## El experimento de 3 vias' a antes de '## Cierre'.
3. 05: elimina lineas WARNING:tensorflow de outputs stdout (conserva prints).
4. Inserta celda MD de procedencia tras cada celda code con read_csv.
"""
import json
import pathlib

PROV = {
    'comparativa.csv': ('track_clase/train_clasicos.py', 'seed 42, GroupKFold(3, groups=unit)'),
    'mlp_comparativa.csv': ('track_clase/train_mlp.py', 'seed 42'),
    'importancia_permutacion.csv': ('track_clase/train_mlp.py', 'seed 42, 200 filas test'),
    'shap_importancia.csv': ('track_clase/shap_clase.py', 'TreeExplainer XGB, fondo 200 train'),
    'comparativa_ventanas.csv': ('track_clase/train_lgbm_adaptada.py', 'seed 42, grano ventana'),
    'comparativa_bundle_c.csv': ('track_clase/train_ensemble_adaptado.py', 'seed 42, grano ventana'),
    'bundle_c_por_motor.csv': ('track_clase/train_ensemble_adaptado.py', 'seed 42, por motor 11/14/15'),
    'bundle_c_multiseed.csv': ('celda multiseed de este notebook', 'seeds 7 y 123'),
    'tabla_final_clase.csv': ('track_clase/tabla_final.py', 'dos ligas, dos campeones'),
}

NB_DIR = pathlib.Path('notebooks')
ref = json.loads((NB_DIR / '01_eda.ipynb').read_text(encoding='utf-8'))
KS = ref['metadata']['kernelspec']
LI = ref['metadata']['language_info']


def md_prov(csv):
    script, det = PROV[csv]
    regen = '' if csv == 'bundle_c_multiseed.csv' else f' Regenerable con: `python {script}`.'
    return {
        'cell_type': 'markdown',
        'metadata': {},
        'source': [
            f'> Procedencia: `resultados/{csv}` \u2190 `{script}` ({det}).{regen} '
            'Si el CSV cambia sin re-ejecutar su fuente, la celda ancla lo detecta.'
        ],
    }


def code_reads_csvs(cell):
    if cell['cell_type'] != 'code':
        return []
    src = ''.join(cell['source'])
    # Clave mas larga primero: 'mlp_comparativa.csv' contiene 'comparativa.csv'.
    found = [csv for csv in sorted(PROV, key=len, reverse=True) if csv in src]
    # Evita doble conteo por subcadena (mlp_comparativa vs comparativa).
    out, used = [], []
    for csv in found:
        if not any(csv in u for u in used):
            out.append(csv)
            used.append(csv)
    return out


for name in ['02_modelos_A.ipynb', '03_modelos_B.ipynb',
             '04_lgbm_adaptada.ipynb', '05_ensemble_adaptado.ipynb']:
    p = NB_DIR / name
    nb = json.loads(p.read_text(encoding='utf-8'))
    nb['metadata']['kernelspec'] = dict(KS)
    nb['metadata']['language_info'] = dict(LI)

    if name == '05_ensemble_adaptado.ipynb':
        # 2. Mover celda 3 vias (idx 0) justo antes del Cierre.
        cells = nb['cells']
        idx_3v = next(i for i, c in enumerate(cells)
                      if ''.join(c.get('source', []))
                      .startswith('## El experimento de 3'))
        idx_cierre = next(i for i, c in enumerate(cells)
                          if ''.join(c.get('source', []))
                          .startswith('## Cierre'))
        cell_3v = cells.pop(idx_3v)
        idx_cierre = next(i for i, c in enumerate(cells)
                          if ''.join(c.get('source', []))
                          .startswith('## Cierre'))
        cells.insert(idx_cierre, cell_3v)
        # 3. Podar WARNING:tensorflow de stdout (conservar el resto).
        for c in cells:
            if c['cell_type'] != 'code':
                continue
            for o in c.get('outputs', []):
                if o.get('output_type') == 'stream' and 'text' in o:
                    o['text'] = [ln for ln in o['text']
                                 if 'WARNING:tensorflow' not in ln
                                 and 'oneDNN' not in ln
                                 and 'TF-TRT' not in ln]

    # 4. Procedencia tras cada read_csv (idempotente: regenera las MD).\
    cells = [c for c in nb['cells']
             if not (c['cell_type'] == 'markdown'
                     and ''.join(c.get('source', [])).startswith('> Procedencia:'))]
    out = []
    for c in cells:
        out.append(c)
        for csv in code_reads_csvs(c):
            out.append(md_prov(csv))
    nb['cells'] = out

    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n',
                 encoding='utf-8')
    print(f'{name}: kernelspec={nb["metadata"]["kernelspec"]["name"]}, '
          f'celdas={len(nb["cells"])}')
print('FASE 1 OK')
