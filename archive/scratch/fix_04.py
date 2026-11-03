import json

path = "notebooks/04_arquitectura_bilstm_oof.ipynb"
with open(path, encoding="utf-8") as f:
    nb = json.load(f)

# Fix cell 3: add import of viz
for cell in nb["cells"]:
    src = "".join(cell.get("source", []))
    if "Alias estilo clase" in src and cell["cell_type"] == "code":
        new_src = src.replace(
            'print("[FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)")',
            'from ds02_rul.viz import evaluar_clase, mostrar_clase\nprint("[FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)")'
        )
        cell["source"] = new_src.split("\n")
        # ensure each line ends with \n except last
        cell["source"] = [line + "\n" for line in cell["source"][:-1]] + [cell["source"][-1]] if cell["source"][-1] else cell["source"]
        print("Fixed cell 3 (viz import)")

# Fix cell 4: add import of oof_base_predictions + constants
for cell in nb["cells"]:
    src = "".join(cell.get("source", []))
    if "OOF en vivo" in src and cell["cell_type"] == "code":
        old = 'dev_units = aux["dev_units"]\n'
        new = ('dev_units = aux["dev_units"]\n'
               'from ds02_rul.pipeline import oof_base_predictions\n'
               'PRIMARY_SEED = 42\n'
               'WINDOW_SIZE = 50\n'
               'STEP_TRAIN = 1\n')
        new_src = src.replace(old, new, 1)
        cell["source"] = new_src.split("\n")
        cell["source"] = [line + "\n" for line in cell["source"][:-1]] + [cell["source"][-1]] if cell["source"][-1] else cell["source"]
        print("Fixed cell 4 (oof_base_predictions + constants)")

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")

print("Saved.")
"