"""S7 — demo story unica (C8).

Canonical GTM sandbox = ``demo-agency-001`` (seed gestionale).
Nicastro = dogfood Founder, **non** percorso GTM.

Time-boxed sandbox (D-080 / freccia coerenza): giorni prova → a scadenza CTA
「Acquista pacchetto」. Checkout reale solo se ``OMNIA_SELF_SERVE_ENABLED`` (S9).
"""
from __future__ import annotations

import math
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from apps.core.seed import DEMO_AGENCY_ID as DEMO_AGENCY_ID  # re-export

DEFAULT_TRIAL_DAYS = int(os.environ.get("OMNIA_DEMO_TRIAL_DAYS") or "7")

__all__ = [
    "DEMO_AGENCY_ID",
    "DEFAULT_TRIAL_DAYS",
    "demo_window_fields",
    "build_demo_status",
    "ensure_demo_window",
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def demo_window_fields(
    *,
    trial_days: Optional[int] = None,
    start: Optional[datetime] = None,
    force_expired: bool = False,
) -> dict[str, Any]:
    """Fields to $set on the canonical demo agency."""
    days = int(trial_days if trial_days is not None else DEFAULT_TRIAL_DAYS)
    days = max(1, min(days, 90))
    started = start or _now()
    if force_expired:
        expires = started - timedelta(seconds=1)
    else:
        expires = started + timedelta(days=days)
    return {
        "demo_story": True,
        "demo_trial_days": days,
        "demo_started_at": started.isoformat(),
        "demo_expires_at": expires.isoformat(),
        "updated_at": _now().isoformat(),
    }


def build_demo_status(
    agency: Optional[dict],
    *,
    self_serve_enabled: bool,
) -> dict[str, Any]:
    """Public status payload for billing / probe."""
    if not agency or not agency.get("demo_story"):
        return {
            "is_demo_story": False,
            "agency_id": (agency or {}).get("id"),
            "expired": False,
            "cta": "none",
            "checkout_available": False,
            "self_serve_enabled": self_serve_enabled,
            "message": "Agenzia non è la sandbox demo GTM (demo-agency-001).",
        }

    expires = _parse_iso(agency.get("demo_expires_at"))
    trial_days = int(agency.get("demo_trial_days") or DEFAULT_TRIAL_DAYS)
    now = _now()
    days_remaining = 0
    expired = True
    if expires:
        secs = (expires - now).total_seconds()
        if secs > 0:
            expired = False
            days_remaining = max(1, int(math.ceil(secs / 86400.0)))

    if expired:
        cta = "acquista_pacchetto"
        if self_serve_enabled:
            message = (
                "Sandbox scaduta — puoi acquistare il pacchetto (self-serve aperto)."
            )
        else:
            message = (
                "Sandbox scaduta — Acquista pacchetto (provisioning assistito fino a O6 / S9; "
                "self-serve OFF)."
            )
    else:
        cta = "use_sandbox"
        message = (
            f"Sandbox attiva — {days_remaining} giorno/i rimanenti "
            f"(trial {trial_days}g). Percorso: gestionale → annunci sul portale."
        )

    return {
        "is_demo_story": True,
        "agency_id": agency.get("id") or DEMO_AGENCY_ID,
        "trial_days": trial_days,
        "started_at": agency.get("demo_started_at"),
        "expires_at": agency.get("demo_expires_at"),
        "days_remaining": 0 if expired else days_remaining,
        "expired": expired,
        "cta": cta,
        "checkout_available": bool(expired and self_serve_enabled),
        "self_serve_enabled": self_serve_enabled,
        "message": message,
        "canonical_seed": DEMO_AGENCY_ID,
        "note": "Nicastro = dogfood Founder, fuori percorso GTM (C8).",
    }


async def ensure_demo_window(
    db,
    *,
    trial_days: Optional[int] = None,
    refresh: bool = False,
    force_expired: bool = False,
) -> dict[str, Any]:
    """Ensure demo-agency-001 has a sandbox window. Idempotent unless refresh/expire."""
    agency = await db.agencies.find_one({"id": DEMO_AGENCY_ID})
    if agency is None:
        raise RuntimeError(f"agency {DEMO_AGENCY_ID} missing — run seed_demo_gestionale first")

    need = (
        force_expired
        or refresh
        or not agency.get("demo_story")
        or not agency.get("demo_expires_at")
    )
    if need:
        fields = demo_window_fields(trial_days=trial_days, force_expired=force_expired)
        await db.agencies.update_one({"id": DEMO_AGENCY_ID}, {"$set": fields})
        agency = await db.agencies.find_one({"id": DEMO_AGENCY_ID})

    from shared.billing.self_serve import is_self_serve_enabled

    return build_demo_status(agency, self_serve_enabled=is_self_serve_enabled())
