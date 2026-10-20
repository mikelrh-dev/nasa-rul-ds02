import json
import sys

sys.stdout.reconfigure(encoding='utf-8')
nb = json.load(open('notebook_nasa_fd001.ipynb', encoding='utf-8'))
for i in range(22, len(nb['cells'])):
    c = nb['cells'][i]
    src = ''.join(c.get('source', []))[:100].replace('\n', ' ')
    print(f"[{i:02d}] {c['cell_type']:8s} | {src}")
