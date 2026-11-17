"""D-174 / B03-DEC-01 — gate email verificata sulle funzioni operative B2B."""
from __future__ import annotations

from fastapi import HTTPException, status

# Ruoli gestionale B2B / franchising — richiedono email verificata.
_OPERATIONAL_B2B_ROLES = frozenset({
    "agency_admin",
    "agent",
    "branch_admin",
    "branch_agent",
    "group_admin",
})


def assert_email_verified_for_operations(user: dict) -> None:
    """Raise 403 email_not_verified when B2B operational role lacks verified email.

    Exempt: super_admin; B2C client/student (gate separati); account senza ruolo operativo.
    """
    role = user.get("role") or ""
    if role == "super_admin":
        return
    if role not in _OPERATIONAL_B2B_ROLES:
        return
    if user.get("email_verified") is True:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": "email_not_verified",
            "hint": "Conferma l'email prima di usare le funzioni operative",
        },
    )
