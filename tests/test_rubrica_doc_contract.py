"""Contrato de documentación y entrega.

Bloquea las regresiones detectadas por la auditoría del 2026-11-15: anclas en el
README raíz, umbrales publicados iguales a los del código (25/20), cifras
multisemilla vigentes, versión fijada de pyarrow y rutas vivas.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8")


def _norm(texto: str) -> str:
    return re.sub(r"\s+", " ", texto)


def test_readme_raiz_anclas_de_rubrica() -> None:
    texto = _leer(ROOT / "README.md")
    assert "Qué hemos construido" in texto
    assert "IA fuerte" in texto
    assert "no supervisado" in texto
    # La tabla de modelos debe declarar el tiempo de entrenamiento.
    assert re.search(r"\|\s*Tiempo[^|]*\|", texto), "la tabla de modelos no declara Tiempo"


def test_umbrales_publicados_igualan_el_codigo() -> None:
    codigo = _leer(ROOT / "app" / "lib" / "_constantes.py")
    apto = float(re.search(r"DEFAULT_AIRWORTHY\s*=\s*([0-9.]+)", codigo).group(1))
    aog = float(re.search(r"DEFAULT_AOG\s*=\s*([0-9.]+)", codigo).group(1))
    for nombre in ("README.md", "README.en.md"):
        texto = _norm(_leer(ROOT / nombre))
        assert f"{apto:g}/{aog:g}" in texto, f"{nombre} no publica {apto:g}/{aog:g}"
        assert "≥ 30" not in texto and ">=30" not in texto and ">= 30" not in texto


def test_multisemilla_vigente_en_documentacion() -> None:
    for nombre in ("README.md", "README.en.md"):
        texto = _norm(_leer(ROOT / nombre))
        assert "4.333 ± 0.040" in texto or "4.333±0.040" in texto
        assert "4.371" in texto and "4.291" in texto
        for frag in re.findall(r"[^.]*\b4\.368\b[^.]*\.", texto):
            bajo = frag.lower()
            assert ("históric" in bajo or "obsolet" in bajo or "historical" in bajo
                    or "no deben" in bajo), frag


def test_pyarrow_pineado_en_dos_manifiestos() -> None:
    req = _leer(ROOT / "requirements.txt")
    pyproj = _leer(ROOT / "pyproject.toml")
    assert re.search(r"(?im)^pyarrow==\S+", req), "requirements.txt no pinean pyarrow"
    assert re.search(r"(?im)[\"']pyarrow==\S+[\"']", pyproj), "pyproject.toml no espeja pyarrow"


def test_rutas_citadas_del_track_existen() -> None:
    clase = _leer(ROOT / "src" / "clase" / "README.md")
    for ruta in (
        "app/lib/ui_shap.py",
        "app/entrypoints/dashboard_ds02.py",
        "scripts/operativo/evaluate_bundle_stability.py",
    ):
        assert (ROOT / ruta).exists(), f"ruta citada inexistente: {ruta}"
    assert "app/ui_shap.py" not in clase
    assert "app/dashboard_ds02.py" not in clase


def test_notas_del_vault_coherentes_con_el_instrumento() -> None:
    vault = ROOT / "MLProyectVault" / "50-Evidencia" / "e00-cifras-autoritativas.md"
    if not vault.exists():
        pytest.skip("vault personal no presente en este checkout")
    texto = _norm(_leer(vault))
    assert "4.371" in texto and "4.291" in texto
    assert "0.901643" in texto
