import json

with open('notebook_nasa_fd001.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for i in [31, 32, 33, 35, 37]:
    cell = nb['cells'][i]
    src = ''.join(cell.get('source', []))[:300]
    print(f'Cell {i}: type={cell.get("cell_type")}')
    print(f'  First 300 chars: {src}')
    print()