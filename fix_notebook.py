import json

with open('notebook_nasa_fd001.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Fix: add execution_count and id to cells that need it
for i, cell in enumerate(nb['cells']):
    if cell.get('cell_type') == 'code':
        if 'execution_count' not in cell:
            cell['execution_count'] = 0
        if 'id' not in cell:
            cell['id'] = f'cell_{i}_{id(cell)}'

# Write back
with open('notebook_nasa_fd001.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print('Fixed notebook JSON')