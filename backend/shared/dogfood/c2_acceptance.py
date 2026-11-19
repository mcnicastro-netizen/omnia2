"""D-175 C2 — acceptance gates for the certified backup/restore drill.

A drill PASS requires proven bootstrap + auth + role separation, not only
data restore coherence.
"""
from __future__ import annotations

from typing import Any


def require_bootstrap_ok(boot: dict[str, Any]) -> None:
    """Bootstrap failure aborts the drill — no silent continuation."""
    if not boot or not boot.get("ok"):
        raise RuntimeError(
            f"bootstrap_failed:rc={boot.get('returncode') if boot else None}"
        )


def require_admin_credentials(creds: dict[str, Any] | None) -> str:
    """Admin password must exist; unauthenticated drill path is forbidden."""
    pwd = (creds or {}).get("admin")
    if not pwd or not str(pwd).strip():
        raise RuntimeError("admin_credentials_missing")
    return str(pwd)


def roles_fully_verified(role_checks: dict[str, Any] | None) -> bool:
    """True only when every privilege check ran and matched expectations.

    Any ``NOT VERIFIED`` result forces overall failure (C2 acceptance).
    """
    if not role_checks:
        return False
    checks = role_checks.get("checks") or []
    if not checks:
        return False
    if any(c.get("result") == "NOT VERIFIED" for c in checks):
        return False
    if not role_checks.get("verified"):
        return False
    return True


def compute_drill_ok(
    *,
    after: dict[str, Any],
    dump: dict[str, Any],
    media: dict[str, Any],
    deny_cases: list[dict[str, Any]],
    boot: dict[str, Any],
    role_checks: dict[str, Any],
) -> bool:
    """Certified C2 PASS: restore + media + deny targets + bootstrap + roles."""
    return bool(
        boot.get("ok")
        and after.get("ok")
        and dump.get("ok")
        and media.get("ok")
        and all(d.get("blocked") for d in deny_cases)
        and roles_fully_verified(role_checks)
    )
