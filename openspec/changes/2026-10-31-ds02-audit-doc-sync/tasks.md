# Tasks: sincronización documental bundle B

## 1. Papeles vigentes

- [ ] **1.1** `README.md`: etiquetar las tres revisiones y dejar una fila vigente
  (bundle B 4.251 / 3.183 / 0.9482 / 2305.1; macro 4.8433); corregir "shipped
  4.301" y macro 4.939/4.903; añadir notas de legados, duplicados y 14915 vs 17450.
  Aceptación: `grep` no encuentra "shipped.*4.301" ni "4.939" como vigente.
- [ ] **1.2** `AGENT.md`: stack Python 3.12.10 + cifras DS02 bundle B.
  Aceptación: sin "13.42" ni "3.10".
- [ ] **1.3** `openspec/project.md` + `config.yaml`: loader que lanza (no "dead
  code"); persistencia canónica en `models/`.
  Aceptación: sin "falls back" presente ni "duplicated under models/".

## 2. Docstrings (sin comportamiento)

- [ ] **2.1** `metrics.py`: 4.26/4.88 → 4.2515/4.8433. `dashboard.py`: cartel legado.
  Aceptación: `py_compile` limpio + suite verde.

## 3. Cierre

- [ ] **3.1** Verify: `git status` limpio en `models/`, `app/cache/`, `*.ipynb`,
  `archive/`; SHA-256 cruzados; `pytest tests -q` verde; este change con
  `verify-report.md`.
- [ ] **3.2** Commit local sin push (7 modificados + vault 07 + change + informe).
