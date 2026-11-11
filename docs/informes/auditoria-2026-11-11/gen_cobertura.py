"""Genera cobertura.csv: una fila por archivo versionado y por estado local relevante.

Solo lee el repositorio. Las columnas `estado` y `evidencia` las rellena la
auditoría; este script deja `pendiente` en todas las filas.
"""

from __future__ import annotations

import collections
import csv
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "informes" / "auditoria-2026-11-11" / "cobertura.csv"

ARTIFACT_EXT = {".joblib", ".keras", ".npz", ".npy", ".parquet", ".png", ".jpg", ".jpeg", ".gif", ".h5"}
CONFIG_EXT = {".toml", ".lock", ".yml", ".yaml", ".cfg", ".ini"}


def git(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8"
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def tier(path: str) -> str:
    p = path.replace("\\", "/")
    name = p.rsplit("/", 1)[-1]
    low = p.lower()
    if low.startswith(("mlruns/", "archive/")):
        return "C"
    if pathlib.PurePosixPath(low).suffix in ARTIFACT_EXT:
        return "C"
    if low.startswith(("src/", "app/", "tests/", "scripts/", "notebooks/", "n8n/")):
        return "A"
    if low.startswith(("docs/", "openspec/", "docClase/", "MLProyectVault/")):
        return "B"
    if low.startswith("resultados/"):
        return "B" if pathlib.PurePosixPath(low).suffix in {".csv", ".json", ".md"} else "C"
    if low.startswith("models/"):
        return "A" if low.endswith(".json") or name.upper().startswith("README") else "C"
    if low.startswith(".github/") or pathlib.PurePosixPath(low).suffix in CONFIG_EXT:
        return "A"
    if name in {".gitignore", ".gitattributes"}:
        return "A"
    if name.lower().startswith("readme") or name in {
        "AGENT.md",
        "AUDITORIA_REDUNDANCIA_CLASE_VS_DS02.md",
    }:
        return "B"
    return "B"


def grupo(path: str) -> str:
    p = path.replace("\\", "/")
    parts = p.split("/")
    if len(parts) == 1:
        return "raiz"
    for prefix in (
        "src/clase",
        "src/ds02_rul",
        "src/mia",
        "app/entrypoints",
        "app/lib",
        "app/ui",
        "app/services",
        "docs/informes",
        "docs/plans",
        "docs/decisions",
        "scripts/auditoria",
        "scripts/build",
        "scripts/legacy",
        "scripts/operativo",
    ):
        if p.startswith(prefix + "/"):
            return prefix
    if p.startswith("src/"):
        return "src/raiz"
    if p.startswith("app/"):
        return "app/raiz"
    if p.startswith("scripts/"):
        return "scripts/raiz"
    if p.startswith("docs/"):
        return "docs"
    for prefix in ("tests", "notebooks", "n8n", "openspec", "mlruns", "models",
                   "resultados", "docClase", "MLProyectVault", "archive"):
        if p.startswith(prefix + "/"):
            return prefix
    return parts[0]


def tipo(path: str) -> str:
    p = path.replace("\\", "/").lower()
    name = p.rsplit("/", 1)[-1]
    ext = pathlib.PurePosixPath(name).suffix.lstrip(".")
    if ext == "py":
        return "python"
    if ext == "ipynb":
        return "notebook"
    if ext == "md":
        return "doc"
    if ext in {"yaml", "yml"}:
        return "mlflow_meta" if "mlruns/" in p else "yaml"
    if ext == "csv":
        return "csv"
    if ext == "json":
        return "json"
    if ext in {"png", "jpg", "jpeg", "gif"}:
        return "imagen"
    if ext in {"joblib", "keras", "npz", "npy", "parquet", "h5"}:
        return "artefacto"
    if ext in {"toml", "lock", "txt"}:
        return "config"
    if ext == "svg":
        return "imagen_vector"
    if ext == "html":
        return "html"
    return ext or "sin_extension"


def loc(path: str) -> str:
    full = ROOT / path
    try:
        if full.stat().st_size > 2_000_000 or tipo(path) in {"artefacto", "imagen", "imagen_vector"}:
            return ""
        return str(len(full.read_text(encoding="utf-8", errors="ignore").splitlines()))
    except OSError:
        return ""


def row(path: str, origen: str, evidencia: str = "") -> dict[str, str]:
    return {
        "path": path,
        "tier": tier(path),
        "grupo": grupo(path),
        "tipo": tipo(path),
        "loc": loc(path),
        "origen": origen,
        "estado": "pendiente",
        "evidencia": evidencia,
    }


def main() -> None:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()

    for path in git("ls-files"):
        rows.append(row(path, "git"))
        seen.add(path.replace("\\", "/"))

    for entry in git("status", "--porcelain"):
        if not entry.startswith("?? "):
            continue
        path = entry[3:].strip().rstrip("/")
        if path.startswith("mlruns/"):
            run_name = ROOT / path / "tags" / "mlflow.runName"
            label = run_name.read_text(encoding="utf-8").strip() if run_name.exists() else ""
            item = row(path + "/", "untracked", label)
            item["tipo"] = "mlflow_run_live"
            item["loc"] = ""
            rows.append(item)
            continue
        if path not in seen and (ROOT / path).exists():
            rows.append(row(path, "untracked"))
            seen.add(path)

    for base, origen in (("data", "local-ignorado"), ("MLProyectVault", "local-ignorado")):
        for full in sorted((ROOT / base).rglob("*")):
            if not full.is_file():
                continue
            path = full.relative_to(ROOT).as_posix()
            if path in seen:
                continue
            item = row(path, origen)
            if base == "data":
                item["tier"] = "C"
                item["grupo"] = "data-local"
                item["loc"] = ""
            rows.append(item)
            seen.add(path)

    rows.sort(key=lambda item: (item["grupo"], item["path"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["path", "tier", "grupo", "tipo", "loc", "origen", "estado", "evidencia"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV: {OUT.relative_to(ROOT)} filas={len(rows)}")
    print("por tier:", dict(sorted(collections.Counter(r["tier"] for r in rows).items())))
    print("por origen:", dict(sorted(collections.Counter(r["origen"] for r in rows).items())))
    print("por grupo:")
    for key, value in sorted(
        collections.Counter(r["grupo"] for r in rows).items(), key=lambda pair: -pair[1]
    ):
        print(f"  {value:5d}  {key}")
    print("loc texto:", sum(int(r["loc"]) for r in rows if r["loc"]))


if __name__ == "__main__":
    main()
