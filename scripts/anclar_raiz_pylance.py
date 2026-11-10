"""Ancla la raíz del repo en el venv para que Pylance resuelva `src.*` siempre.

Por qué existe: el proyecto importa con prefijo `src.` (`from src.clase...`,
81 sitios entre `src/`, `tests/`, `app/` y notebooks), pero `src` **no** es un
paquete instalado: el `pip install -e .` solo expone `clase`, `ds02_rul` y
`mia` (ver `src/ds02_rul.egg-info/top_level.txt` y el `.pth` editable del venv).
Es decir, `import src.clase` necesita la raíz del repo en `sys.path`:

- en runtime la tiene por el cwd (Jupyter arranca en la raíz, la app también) y
  por los `sys.path.insert` de algunos módulos;
- el analizador estático solo la tiene si Pylance encuentra `pyrightconfig.json`
  o `python.analysis.extraPaths` — y si abres VS Code en una carpeta padre, esa
  config no se lee. El notebook corre, pero el import sale subrayado.

Este script escribe un `.pth` en site-packages con la raíz del repo. Pylance lee
los `.pth` del intérprete (es el mismo mecanismo por el que ya resuelve
`ds02_rul`), así que la resolución deja de depender de qué carpeta abras.

Efecto colateral asumido: la raíz entra en `sys.path` de ese venv, así que
`app`, `tests`, `scripts`... también pasan a ser importables como nombres
sueltos. Ya era el caso en runtime (cwd = raíz); no cambia nada que hoy funcione.

Local y no versionado: `.venv/` está en `.gitignore`, y recrear el venv borra el
`.pth` → vuelve a ejecutar el script.

Uso:
    .venv/Scripts/python scripts/anclar_raiz_pylance.py   # Windows
    .venv/bin/python     scripts/anclar_raiz_pylance.py   # POSIX
"""

from __future__ import annotations

import os
import sys
import sysconfig

NOMBRE_PTH = "nasa_root.pth"


def main() -> int:
    """Fija la raiz del repo en la configuracion de Pylance y crea el marcador."""
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if sys.prefix == sys.base_prefix:
        print("ERROR: corre esto con el python del venv del proyecto, no con")
        print("       el intérprete global:")
        print("       .venv/Scripts/python scripts/anclar_raiz_pylance.py")
        return 2

    site = sysconfig.get_paths()["purelib"]
    if not os.path.isdir(site):
        print(f"ERROR: no existe site-packages del venv: {site}")
        return 1

    destino = os.path.join(site, NOMBRE_PTH)
    with open(destino, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(raiz + "\n")

    # Prints en ASCII a proposito: la consola de Windows (cp1252) revienta con
    # '->' unicode y el script moria despues de escribir el .pth.
    print(f"OK: {destino}")
    print(f"    raiz del repo = {raiz}")
    print("    Siguiente paso en VS Code: Ctrl+Shift+P -> "
          "'Python: Restart Language Server'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
