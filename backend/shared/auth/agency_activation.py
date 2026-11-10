"""Agency CRM activation gate (Founder Ops must unlock)."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import HTTPException, status


def resolve_activation_status(agency: Optional[dict]) -> str:
    """Legacy agencies without field → active (grandfather)."""
    if agency is None:
        return "pending"
    raw = agency.get("activation_status")
    if raw in ("pending", "active", "suspended"):
        return raw
    return "active"


def assert_agency_crm_unlocked(agency: Optional[dict], *, user: Optional[dict] = None) -> None:
    """Raise 403 if agency cannot use ImmoWeb CRM yet.

    super_admin bypasses (Ops can inspect).
    """
    if user and user.get("role") == "super_admin":
        return
    st = resolve_activation_status(agency)
    if st == "active":
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": "agency_pending_activation",
            "code": "agency_pending_activation",
            "activation_status": st,
            "message": (
                "L'agenzia è in attesa di attivazione da OMNIA. "
                "Riceverai una email quando il gestionale sarà sbloccato."
            ),
        },
    )


def public_activation_fields(agency: Dict[str, Any]) -> Dict[str, Any]:
    st = resolve_activation_status(agency)
    return {
        "activation_status": st,
        "activated_at": agency.get("activated_at"),
        "activated_by": agency.get("activated_by"),
        "crm_unlocked": st == "active",
    }
