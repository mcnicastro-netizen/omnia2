"""S5 / D-115 — hard-gate self-serve distinto da Stripe sandbox.

`STRIPE_ENABLED` = infrastruttura pagamenti (test/live) disponibile.
`OMNIA_SELF_SERVE_ENABLED` = rubinetto commerciale checkout B2B (default OFF fino a O6 PASS).

Così Cloud può tenere Stripe ON per probe/webhook senza aprire abbonamenti self-serve.
"""
from __future__ import annotations

import os

from fastapi import HTTPException


def is_self_serve_enabled() -> bool:
    return (os.environ.get("OMNIA_SELF_SERVE_ENABLED") or "").strip().lower() == "true"


def guard_self_serve() -> None:
    """Block B2B self-serve checkout when O6 rubinetto is closed."""
    if is_self_serve_enabled():
        return
    raise HTTPException(
        status_code=503,
        detail={
            "error": "self_serve_blocked",
            "code": "self_serve_blocked",
            "message": (
                "Attivazione self-serve non aperta (D-115 / gate O6). "
                "Richiedi provisioning assistito dopo la demo guidata."
            ),
        },
    )
