"""Ejecuta NB06 celdas 0-25 y vuelca outputs (largo, CPU). Uso: python scripts/run_nb06_0_25.py"""
import copy
import nbformat
from nbclient import NotebookClient

p = 'notebooks/06_evaluacion_produccion_comparativa.ipynb'
nb = nbformat.read(p, as_version=4)
sub = copy.deepcopy(nb)
sub.cells = sub.cells[:26]
client = NotebookClient(sub, timeout=900, kernel_name='python3', allow_errors=False)
client.execute()
for i in range(26):
    nb.cells[i]['outputs'] = sub.cells[i].get('outputs', [])
    nb.cells[i]['execution_count'] = sub.cells[i].get('execution_count')
nbformat.write(nb, p)
print('NB06 0-25 ejecutado y guardado (sin commit)')
for i in [9, 11, 14, 18, 20, 23, 25]:
    print(i, 'outputs=', len(nb.cells[i].get('outputs', [])))
