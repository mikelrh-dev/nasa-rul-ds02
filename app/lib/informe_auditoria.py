"""Informe de auditoría en PDF: las dos tablas que un tribunal pide.

Congela la huella del artefacto y las tablas de Evidencia, para que el papel y
la pantalla digan lo mismo. No recalcula el modelo: reusa las series ya
puntuadas de la caché. dueño único de la generación del PDF; la UI
(`app/ui/_tab_auditoria.py`) solo lo invoca detrás del botón.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app.lib import ui_data_loader as L
from app.lib.pdf_partes import _latin1

__all__ = ["_informe_auditoria_pdf", "_informe_pdf_cached"]


def _informe_auditoria_pdf(
    windows: pd.DataFrame,
    curves: dict,
    unidades: list,
    threshold_apto: float,
    threshold_aog: float,
    provenance: dict,
    critical_mae: float,
) -> bytes:
    """Informe de auditoría en PDF: precisión por tramo y alarma vs. verdad."""
    from fpdf import FPDF

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Informe de auditoria - RUL DS02", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=10)
    pdf.cell(0, 6,
             f"Politica en vigor: apto si L_inf >= {threshold_apto:.0f} | "
             f"inspeccion si {threshold_aog:.0f} <= L_inf < {threshold_apto:.0f} | "
             f"hangar si L_inf < {threshold_aog:.0f}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6,
             f"Artefacto congelado SHA-256: {provenance['artifact']['ensemble_sha256']}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6,
             f"MAE en zona critica (RUL real < {threshold_aog:.0f}): "
             f"{critical_mae:.2f} ciclos",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Precision por tramo de vida (MAE sobre RUL real)",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "B", 10)
    for ancho, txt in ((35, "Tramo"), (30, "Ventanas"), (30, "MAE"), (30, "Sesgo")):
        pdf.cell(ancho, 7, txt, border=1, align="C")
    pdf.ln()
    pdf.set_font("helvetica", size=10)
    for r in L.mae_by_band(windows).itertuples():
        pdf.cell(35, 7, _latin1(r.band), border=1)
        pdf.cell(30, 7, f"{int(r.windows)}", border=1, align="R")
        pdf.cell(30, 7, "n/a" if pd.isna(r.mae) else f"{r.mae:.3f}", border=1, align="R")
        pdf.cell(30, 7, "n/a" if pd.isna(r.bias) else f"{r.bias:+.3f}", border=1, align="R")
        pdf.ln()
    pdf.ln(4)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Alarma vs. verdad (adelanto por motor)",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "B", 10)
    for ancho, txt in ((30, "Motor"), (40, "Alarma"), (40, "RUL real < umbral"),
                       (35, "Adelanto")):
        pdf.cell(ancho, 7, txt, border=1, align="C")
    pdf.ln()
    pdf.set_font("helvetica", size=10)
    for u in unidades:
        a, t = L.first_alarm_cycle(curves[u], threshold_aog)
        pdf.cell(30, 7, f"U{int(u)}", border=1)
        pdf.cell(40, 7, "-" if a is None else str(int(a)), border=1, align="R")
        pdf.cell(40, 7, "-" if t is None else str(int(t)), border=1, align="R")
        pdf.cell(35, 7, "-" if (a is None or t is None) else str(int(t - a)),
                 border=1, align="R")
        pdf.ln()
    pdf.ln(4)

    pdf.set_font("helvetica", "I", 8)
    pdf.multi_cell(
        0, 5,
        "La banda conformal es la de la serie guardada: no se recalibra al mover los "
        "umbrales, porque la calibracion es parte del artefacto congelado. La decision "
        "la toma el limite inferior de la banda, no la prediccion puntual (ADR-008).")
    return bytes(pdf.output())


@st.cache_data(ttl=3600, show_spinner="Generando informe de auditoría…")
def _informe_pdf_cached(
    threshold_apto: float,
    threshold_aog: float,
    critical_mae: float,
    ensemble_sha256: str,
    windows_sig: str,
    aplicar_reglas: bool = False,
    pdf_version: str = "",
    *,
    windows: pd.DataFrame,
    curves: dict,
    unidades: list,
    provenance: dict,
) -> bytes:
    """Constructor cacheado del PDF de auditoría.

    La clave son escalares (umbrales, SHA, firma de caché, aplicar_reglas y
    versión de manifest) más los frames de datos, así que no hay que hashear
    DataFrames en cada render. `aplicar_reglas` y `pdf_version` cierran el PDF
    stale al mover umbrales o activar la corrección.
    """
    return _informe_auditoria_pdf(
        windows, curves, unidades,
        threshold_apto, threshold_aog, provenance, critical_mae,
    )
