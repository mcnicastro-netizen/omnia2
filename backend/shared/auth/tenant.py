"""OMNIA — Tenant helpers consolidati (L8) + multi-agency attiva (M5 / D-106).

L'agenzia operativa è SOLO `user.active_agency_id` se presente e nella membership.
Nessun fallback semantico a `agency_ids[0]` (D-106 / EC-01).
Se manca o non è valida → errore (require_*) o None (optional_*).
"""
from typing import Optional

from fastapi import HTTPException


def optional_agency_id(user: dict) -> Optional[str]:
    """Agency attiva se legittima; altrimenti None (mai agency_ids[0])."""
    ids = user.get("agency_ids") or []
    if not ids:
        return None
    active = user.get("active_agency_id")
    if active and active in ids:
        return active
    return None


def require_agency(user: dict) -> str:
    ids = user.get("agency_ids") or []
    if not ids:
        raise HTTPException(status_code=400, detail="no_agency")
    active = user.get("active_agency_id")
    if not active:
        raise HTTPException(status_code=400, detail="active_agency_required")
    if active not in ids:
        raise HTTPException(status_code=400, detail="active_agency_invalid")
    return active


def require_agency_404(user: dict) -> str:
    ids = user.get("agency_ids") or []
    if not ids:
        raise HTTPException(status_code=404, detail="no_agency")
    active = user.get("active_agency_id")
    if not active:
        raise HTTPException(status_code=404, detail="active_agency_required")
    if active not in ids:
        raise HTTPException(status_code=404, detail="active_agency_invalid")
    return active


def require_agency_membership(user: dict) -> str:
    ids = user.get("agency_ids") or []
    if not ids:
        raise HTTPException(status_code=403, detail="no_agency_membership")
    active = user.get("active_agency_id")
    if not active:
        raise HTTPException(status_code=403, detail="active_agency_required")
    if active not in ids:
        raise HTTPException(status_code=403, detail="active_agency_invalid")
    return active


async def arequire_agency(user: dict) -> str:
    """Variante awaitable per i call-site legacy `await _agency(user)`."""
    return require_agency(user)
