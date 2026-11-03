"""Rellena execution_count + outputs reales de las 3 celdas estaticas de 05.

Celdas 18 (ancla manifest), 34 (lectura tabla final) y 36 (tabla viva).
Se ejecutan con cwd=notebooks porque usan rutas '../resultados/...'.
"""
import contextlib
import io
import json
import os
import pathlib
import sys

NB = pathlib.Path('notebooks/05_ensemble_adaptado.ipynb')
ROOT = pathlib.Path('.').resolve()
TARGETS = {18: 6, 34: 7, 36: 8}

nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']
ns = {'__name__': '__main__'}
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

cwd = os.getcwd()
os.chdir(ROOT / 'notebooks')
try:
    for idx, count in TARGETS.items():
        cell = cells[idx]
        src = ''.join(cell['source'])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            exec(compile(src, f'cell{idx}', 'exec'), ns)
        out = buf.getvalue()
        cell['outputs'] = [{'name': 'stdout', 'output_type': 'stream',
                            'text': out.splitlines(keepends=True)}]
        cell['execution_count'] = count
        print(f'celda {idx}: {len(out)} chars de stdout')
finally:
    os.chdir(cwd)

NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

code = [c for c in nb['cells'] if c['cell_type'] == 'code']
print('05: %d celdas, %d de codigo, %d con outputs'
      % (len(nb['cells']), len(code), sum(1 for c in code if c.get('outputs'))))
