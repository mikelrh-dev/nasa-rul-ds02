"""Contrato Deps/CI (DEP-CI-01).

Locked behavior:
- ``pyproject.toml`` pinnea con ``==`` las versiones instaladas en ``.venv``
  (tensorflow, lightgbm, scikit-learn, numpy, pandas, shap, fastapi,
  uvicorn, streamlit, plotly, pytest, nbformat) y es consistente con
  ``requirements.txt`` (cada pin de requirements aparece verbatim en
  pyproject).
- ``.github/workflows/ci.yml`` instala desde requirements.txt o pyproject
  pineado, fija ``PYTHONHASHSEED`` y ejecuta ``python -m pytest tests -q``
  sin reentrenar ni ejecutar DeepSHAP/notebooks.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"

# Versiones exactas instaladas en .venv (verificado con
# .venv/Scripts/python -m pip list).
EXPECTED_PINS = {
    "tensorflow": "2.21.0",
    "lightgbm": "4.7.0",
    "scikit-learn": "1.9.1",
    "numpy": "2.5.4",
    "pandas": "3.0.6",
    "shap": "0.54.1",
    "fastapi": "0.151.0",
    "uvicorn": "0.54.0",
    "streamlit": "1.66.0",
    "plotly": "7.1.0",
    "pytest": "9.1.1",
    "nbformat": "5.11.1",
}


def _load_pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def _all_declared_deps(data: dict) -> list[str]:
    project = data.get("project", {})
    deps = list(project.get("dependencies", []))
    for group in project.get("optional-dependencies", {}).values():
        deps.extend(group)
    return deps


def _pin_map(deps: list[str]) -> dict[str, str]:
    pins: dict[str, str] = {}
    for dep in deps:
        m = re.match(r"^([A-Za-z0-9_.-]+)==([^\s;]+)$", dep.strip())
        if m:
            pins[m.group(1).lower()] = m.group(2)
    return pins


def test_pyproject_pins_exact_venv_versions():
    pins = _pin_map(_all_declared_deps(_load_pyproject()))
    for pkg, version in EXPECTED_PINS.items():
        assert pins.get(pkg.lower()) == version, (
            f"{pkg} debe estar pineado =={version} en pyproject.toml; "
            f"pins encontrados: {pins}"
        )


def test_pyproject_has_no_unpinned_runtime_deps():
    deps = _all_declared_deps(_load_pyproject())
    assert deps, "pyproject.toml debe declarar dependencias"
    for dep in deps:
        assert "==" in dep, f"dependencia sin pin exacto: {dep!r}"


def test_requirements_txt_synced_with_pyproject():
    pins = _pin_map(_all_declared_deps(_load_pyproject()))
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    req_pins = {}
    for line in requirements.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z0-9_.-]+)==([^\s;]+)$", line)
        if m:
            req_pins[m.group(1).lower()] = m.group(2)
    assert req_pins, "requirements.txt debe contener pins =="
    for pkg, version in req_pins.items():
        assert pins.get(pkg) == version, (
            f"requirements.txt pinnea {pkg}=={version} pero pyproject.toml "
            f"tiene {pins.get(pkg)!r}"
        )


def _ci_text() -> str:
    assert CI_PATH.is_file(), f"falta workflow CI: {CI_PATH}"
    return CI_PATH.read_text(encoding="utf-8")


def test_ci_installs_from_pinned_source():
    text = _ci_text()
    assert (
        "requirements.txt" in text or "pip install -e ." in text
    ), "CI debe instalar desde requirements.txt o pyproject pineado"


def test_ci_fixes_pythonhashseed():
    text = _ci_text()
    assert "PYTHONHASHSEED" in text, "CI debe fijar PYTHONHASHSEED"


def test_ci_runs_pytest_without_retraining():
    text = _ci_text()
    assert "python -m pytest tests -q" in text
    # Solo comandos reales: las lineas de comentario pueden nombrar lo que
    # el CI NO hace (p. ej. "sin reentrenar ni ejecutar DeepSHAP").
    commands = "\n".join(
        line for line in text.splitlines() if not line.strip().startswith("#")
    )
    forbidden = [
        "nbconvert",
        "jupyter nbconvert",
        "build_07",
        "train_",
        "DeepSHAP",
        "deepshap",
        "ejecutar_shap_c",
    ]
    lowered = commands.lower()
    for token in forbidden:
        assert token.lower() not in lowered, (
            f"CI no debe reentrenar ni ejecutar DeepSHAP/notebooks: {token!r}"
        )
