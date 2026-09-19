"""OMNIA — Soft-delete / Cestino helpers (agency archives).

Eliminare un immobile o un cliente lo sposta nel Cestino per
TRASH_RETENTION_DAYS giorni. Poi viene cancellato in modo definitivo
dal job di purge (cron).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from shared.models.base import utcnow_iso

TRASH_RETENTION_DAYS = 30


def not_trashed() -> Dict[str, Any]:
    """Mongo clause: record ancora attivo (non nel Cestino)."""
    return {"$or": [{"deleted_at": {"$exists": False}}, {"deleted_at": None}]}


def in_trash() -> Dict[str, Any]:
    """Mongo clause: record nel Cestino."""
    return {"deleted_at": {"$exists": True, "$nin": [None, ""]}}


def with_not_trashed(base: Dict[str, Any]) -> Dict[str, Any]:
    """Merge a base query with not_trashed (safe with existing $or)."""
    return {"$and": [base, not_trashed()]}


def soft_delete_fields(user_id: Optional[str] = None) -> Dict[str, Any]:
    now = utcnow_iso()
    fields: Dict[str, Any] = {"deleted_at": now, "updated_at": now}
    if user_id:
        fields["deleted_by"] = user_id
    return fields


def restore_update() -> Dict[str, Any]:
    return {
        "$unset": {"deleted_at": "", "deleted_by": ""},
        "$set": {"updated_at": utcnow_iso()},
    }


def purge_cutoff_iso(days: int = TRASH_RETENTION_DAYS) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def days_left_in_trash(deleted_at: Optional[str], days: int = TRASH_RETENTION_DAYS) -> Optional[int]:
    if not deleted_at:
        return None
    try:
        raw = deleted_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        expires = dt + timedelta(days=days)
        left = (expires - datetime.now(timezone.utc)).days
        return max(0, left)
    except Exception:
        return None
