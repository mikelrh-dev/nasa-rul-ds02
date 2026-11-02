"""Envío de la decisión a n8n (MIA 3) — STUB pendiente.

Este change (2026-11-02-clase-track) NO llama a este módulo desde la app.
El flujo real (webhook por decisión + acción distinta según decisión:
HANGAR → Postgres+Calendar+correo, INSPECCIÓN → Sheets, APTO → solo log)
se implementa en el change siguiente. `n8n/flujo.json` es placeholder.
"""


def enviar_decision(decision: str, payload: dict, webhook_url: str | None = None) -> dict:
    """Stub: valida y declara pendiente, nunca hace POST."""
    raise NotImplementedError(
        "n8n pendiente (MIA 3): configura el webhook y el flujo por decisión "
        f"antes de enviar {decision!r}."
    )
