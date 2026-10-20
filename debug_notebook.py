import json

with open('notebook_nasa_fd001.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Find and modify the LSTM training cells in the V2 section
# Cells 23-39 are the V2-inserted cells
# Let's look at cell 23's source to understand the structure
cell23 = nb['cells'][23]
src23 = ''.join(cell23.get('source', []))
print("Cell 23 source preview:", src23[:200])

# Find the EarlyStopping patience and epochs in the V2 cells
# We need to reduce epochs from 80 to something smaller