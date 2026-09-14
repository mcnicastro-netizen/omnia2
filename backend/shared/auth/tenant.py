"""OMNIA — Tenant helpers consolidati (L8) + multi-agency attiva (M5).

Sostituisce i 13+ helper `_agency`/`_agency_id`/`_require_agency` copia-incollati
nei moduli immoweb. L'agenzia "attiva" è `user.active_agency_id` se presente e
legittima, altrimenti la prima di `agency_ids` (backward-compatible).
"""
from typing import Optional

from fastapi import HTTPException


def optional_agency_id(user: dict) -> Optional[str]:
    ids = user.get("agency_ids") or []
    if not ids:
        return None
    active = user.get("active_agency_id")
    return active if active in ids else ids[0]


def require_agency(user: dict) -> str:
    aid = optional_agency_id(user)
    if not aid:
        raise HTTPException(status_code=400, detail="no_agency")
    return aid


def require_agency_404(user: dict) -> str:
    aid = optional_agency_id(user)
    if not aid:
        raise HTTPException(status_code=404, detail="no_agency")
    return aid


def require_agency_membership(user: dict) -> str:
    aid = optional_agency_id(user)
    if not aid:
        raise HTTPException(status_code=403, detail="no_agency_membership")
    return aid


async def arequire_agency(user: dict) -> str:
    """Variante awaitable per i call-site legacy `await _agency(user)`."""
    return require_agency(user)
