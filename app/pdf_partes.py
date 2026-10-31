"""Generacion de partes de trabajo en PDF para DS02.

Espejo de los CSV/JSON que ya produce `ui_data_loader.work_order()`. No
recalcula nada: vuelca el documento ya construido. Reusa el patron fpdf2 del
informe de auditoria.
"""

from __future__ import annotations

from typing import Any


def parte_trabajo_pdf(order: dict[str, Any]) -> bytes:
    from fpdf import FPDF

    def _latin1(txt: str) -> str:
        for _a, _b in (("∞", "inf"), ("≥", ">="), ("≤", "<="), ("—", "-"),
                       ("–", "-"), ("×", "x"), ("≈", "~"), ("→", "->"),
                       ("·", "-"), ("…", "...")):
            txt = str(txt).replace(_a, _b)
        return txt.encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Parte de trabajo - DS02", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=10)
    pdf.cell(0, 6, f"Documento: {_latin1(order.get('documento', ''))}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Generado: {order.get('generado_en', '')}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6,
             f"Artefacto SHA-256: {order.get('artefacto_sha256', '')}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6,
             f"Motor: {order.get('motor', '')}  |  Modo: {order.get('modo', '')}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    for u in order.get("unidades", []):
        pdf.set_font("helvetica", "B", 11)
        pdf.cell(0, 7, f"Unidad {_latin1(u.get('unidad', ''))} - {u.get('estado', '')}",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("helvetica", size=10)
        pdf.cell(0, 6, f"RUL estimada: {u.get('rul_estimada', '')}  |  "
                       f"L_inf: {u.get('limite_inferior', '')}  |  "
                       f"L_sup: {u.get('limite_superior', '')}",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Accion: {_latin1(u.get('accion', ''))}",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, f"Motivo: {_latin1(u.get('motivo', ''))}",
                 new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)
    return bytes(pdf.output())
