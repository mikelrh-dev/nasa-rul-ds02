import json

with open('notebook_nasa_fd001.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

with open('cells_summary.txt', 'w', encoding='utf-8') as out:
    for i, c in enumerate(nb['cells']):
        src = "".join(c.get("source", [])).replace("\n", " ")[:120]
        out.write(f"Cell {i:02d} [{c['cell_type']}]: {src}\n")

print(f"Total cells: {len(nb['cells'])}")
