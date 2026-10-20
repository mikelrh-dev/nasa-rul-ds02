import json
import pathlib
import sys
import nbformat
from nbclient import NotebookClient

sys.stdout.reconfigure(encoding='utf-8')

NB_PATH = pathlib.Path('notebook_nasa_fd001.ipynb')
nb = nbformat.read(str(NB_PATH), as_version=4)

print(f"Executing cells 0 through 21...")
# We only want to execute cells 0 to 21 to generate real outputs and plots
nb_sub = nbformat.v4.new_notebook()
nb_sub.cells = nb.cells[:22]

client = NotebookClient(nb_sub, timeout=300, kernel_name='python3')
client.execute()

# Copy back executed cells with outputs into full notebook
for i in range(22):
    nb.cells[i] = nb_sub.cells[i]

with open(NB_PATH, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("Cells 0-21 executed and saved to notebook_nasa_fd001.ipynb successfully!")
