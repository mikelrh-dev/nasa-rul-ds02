# scripts/ — qué es vigente y qué es legado

Vigente DS02 (bundle C, clase-track):
- `build_ui_cache.py` — construye `app/cache/` desde `models/` (fuente para la app sin TF).
- `freeze_rules_evidence.py` — gate de la capa de reglas (RULES-06, ADR-009). Por
  defecto verifica la banda publicada contra el instrumento versionado
  (`src/mia/instrumento_oof.npz`); `--cache PATH` re-deriva desde el caché OOF
  (camino de desarrollo, ADR-012).
- `freeze_oof_instrument.py` — deriva, escribe y comprueba ese instrumento desde
  `nb2_selection.joblib` (`--write` / `--check`).
- `verify_gate.py` — gate full `pytest tests/` (260/16/7 baseline A6, ver verify-report).
- `evaluate_model_quality.py`, `p0/p1_*` — sondas de medición (no reentrenan bundle).
- `anclar_raiz_pylance.py` — helper editor (no afecta a runtime).
- `predict_ds02.py` — CLI DS02.

Legado FD001 (no tocar para DS02, solo referencia):
- `v3_*.py`, `predict.py`, `repackage_artifact.py`.

Generación vieja de notebooks de clase retirada el 2026-11-09 a un backup externo (ver `archive/README.md`).
