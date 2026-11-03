import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('notebook_nasa_fd001.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Total cells: {len(nb['cells'])}")
for i, c in enumerate(nb['cells']):
    first_line = c['source'][0].strip() if c['source'] else '<empty>'
    ctype = c['cell_type']
    print(f"[{i:02d}] {ctype:8s} | {first_line[:80]}")
