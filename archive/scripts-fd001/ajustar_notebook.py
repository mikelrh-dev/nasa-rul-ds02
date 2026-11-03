import pathlib, json

nb = json.loads(pathlib.Path('notebook_nasa_fd001.ipynb').read_bytes().decode('utf-8','replace'))

# encontrar celda conclusiones
target_idx = None
for i,c in enumerate(nb['cells']):
    if c.get('cell_type') != 'markdown':
        continue
    src = ''.join(c.get('source', ''))
    if src.strip().startswith('## 7. Conclusiones'):
        target_idx = i
        break
assert target_idx is not None, 'no encuentro celda conclusiones'

c = nb['cells'][target_idx]
lines = list(c['source'])
# insertar línea de referencia después del encabezado de tabla (línea 5 = separador)
# buscamos línea '|----------|...' y añadimos una nota debajo
sep_idx = None
for i,l in enumerate(lines):
    if l.startswith('|----------|'):
        sep_idx = i
        break
assert sep_idx is not None, 'no encuentro separador de tabla'

# nota debajo del separador, antes de la fila XGBoost original
note_line = '| *(test corregido: última ventana por motor evaluada contra RUL_FD001.txt; ver modelos/test_eval_ultima_ventana.csv)* |'
# insertamos después del separador (sep_idx+1)
lines.insert(sep_idx+1, note_line)

c['source'] = lines

pathlib.Path('notebook_nasa_fd001.ipynb').write_bytes(json.dumps(nb, indent=1).encode('utf-8'))
print('notebook actualizado: añadida referencia a models/test_eval_ultima_ventana.csv')
