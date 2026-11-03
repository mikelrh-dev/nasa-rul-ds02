import json

with open('notebook_nasa_fd001.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

with open('cells_dump.txt', 'w', encoding='utf-8') as out:
    for i, c in enumerate(nb['cells']):
        ctype = c['cell_type']
        out.write(f"=== CELL {i} ({ctype}) ===\n")
        out.write(''.join(c.get('source', [])))
        out.write('\n\n')

print(f"Dumped {len(nb['cells'])} cells successfully")
