import json
import os
import re
import sys

TMP = os.path.join(os.environ["LOCALAPPDATA"], "Temp")

FILES = [
    ("NB01", "notebooks/ds02_ensemble/01_datos_y_bases.ipynb", os.path.join(TMP, "nb01b.ipynb")),
    ("NB02", "notebooks/ds02_ensemble/02_decision_ablacion_oof_ensamble.ipynb", os.path.join(TMP, "nb02b.ipynb")),
    ("NB03", "notebooks/ds02_ensemble/03_evidencia_multisemilla_diagnostico.ipynb", os.path.join(TMP, "nb03b.ipynb")),
]


def source_is_notebook(path: str) -> str | None:
    """Devuelve la ruta del notebook fuente si existe, o None.

    Los notebooks ejecutados en /tmp pueden no estar disponibles en otro
    ordenador/clone; en ese caso este script reporta la ruta del fuente
    para que el revisor abra el .ipynb manualmente.
    """
    return path if os.path.exists(path) else None


def text_outputs(nb_path: str):
    nb = json.load(open(nb_path, encoding="utf-8"))
    out = []
    for i, c in enumerate(nb["cells"]):
        if c["cell_type"] != "code":
            continue
        chunks = []
        for o in c.get("outputs", []):
            if "text" in o:
                chunks.append("".join(o["text"]))
            for k, v in c.get("data", {}).items():
                if k == "text/plain":
                    chunks.append("".join(v))
        text = "\n".join(chunks or [""]).strip()
        if not text:
            continue
        if re.search(r"\bFigure size\b", text):
            continue
        if any(w in text for w in ["WARNING:", "iopub.status", "keras", "tensorflow", "lightgbm", "sklearn", "ds02_rul", "cwd:"]):
            continue
        out.append((i, c.get("execution_count"), text))
    return out


def main():
    for tag, src_path, run_path in FILES:
        print("\n" + "=" * 34, tag)
        if not os.path.exists(run_path):
            print(f"[sin copia ejecutada en {run_path}]")
            fuente = source_is_notebook(src_path)
            print(f"[fuente notebook: {fuente or src_path}]")
            continue
        print("copia ejecutada:", run_path)
        for idx, ec, text in text_outputs(run_path):
            print(f"celda {idx} (exec {ec})")
            for ln in text.splitlines():
                if ln.strip():
                    print(" ", ln)


if __name__ == "__main__":
    main()
