import json

path = "notebooks/04_arquitectura_bilstm_oof.ipynb"
with open(path, encoding="utf-8") as f:
    nb = json.load(f)

NL = chr(10)
DQ = chr(34)

for cell in nb["cells"]:
    src = cell.get("source", "")
    if isinstance(src, list):
        src = "".join(src)
    if "Alias estilo clase" in src and cell["cell_type"] == "code":
        old = "print(" + DQ + "[FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)" + DQ + ")"
        new = "from ds02_rul.viz import evaluar_clase, mostrar_clase" + NL + "print(" + DQ + "[FASE A OK] evaluar_clase / mostrar_clase listos (alias, sin efecto en el modelo)" + DQ + ")"
        cell["source"] = src.replace(old, new)
        print("Fixed cell viz import")
    if "OOF en vivo" in src and cell["cell_type"] == "code":
        old = "dev_units = aux[" + DQ + "dev_units" + DQ + "]" + NL
        new = ("dev_units = aux[" + DQ + "dev_units" + DQ + "]" + NL +
               "from ds02_rul.pipeline import oof_base_predictions" + NL +
               "PRIMARY_SEED = 42" + NL +
               "WINDOW_SIZE = 50" + NL +
               "STEP_TRAIN = 1" + NL)
        cell["source"] = src.replace(old, new, 1)
        print("Fixed cell oof import")

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write(NL)

print("Saved.")
