import json

nb = json.load(open('notebook_nasa_fd001.ipynb', encoding='utf-8'))
with open('cells_detail.txt', 'w', encoding='utf-8') as f:
    for i in [3, 6, 7, 8, 10, 12, 14, 18, 19, 20, 21, 22, 23, 25, 26, 28, 30, 31, 33, 34, 40, 42, 44, 48, 50, 52]:
        if i < len(nb['cells']):
            f.write(f"\n{'='*20} CELL {i} ({nb['cells'][i]['cell_type']}) {'='*20}\n")
            f.write("".join(nb['cells'][i].get('source', [])))
            f.write("\n")
print("Wrote cells_detail.txt")
