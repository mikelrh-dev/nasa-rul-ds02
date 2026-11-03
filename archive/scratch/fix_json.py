import json

path = "notebooks/04_arquitectura_bilstm_oof.ipynb"
with open(path, encoding="utf-8") as f:
    nb = json.load(f)

# Fix cell 3: add viz import (source is a string)
for cell in nb["cells"]:
    src = cell.get("source", "")
    if isinstance(src, str) and "Alias estilo clase" in src and cell["cell_type"] == "code":
        old = 'print("[FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)")'
        new = 'from ds02_rul.viz import evaluar_clase, mostrar_clase\nprint("[FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)")'
        cell["source"] = src.replace(old, new)
        print("Fixed cell 3 (viz import)")

# Fix cell 4: add oof_base_predictions import + constants (source is a string)
for cell in nb["cells"]:
    src = cell.get("source", "")
    if isinstance(src, str) and "OOF en vivo" in src and cell["cell_type"] == "code":
        old = 'dev_units = aux["dev_units"]\n'
        new = ('dev_units = aux["dev_units"]\n'
               'from ds02_rul.pipeline import oof_base_predictions\n'
               'PRIMARY_SEED = 42\n'
               'WINDOW_SIZE = 50\n'
               'STEP_TRAIN = 1\n')
        cell["source"] = src.replace(old, new, 1)
        print("Fixed cell 4 (oof_base_predictions + constants)")

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")

print("Saved.")
