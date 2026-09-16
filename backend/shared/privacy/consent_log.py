"""OMNIA — GDPR consent audit log."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from shared.db.connection import Database

logger = logging.getLogger("omnia.consent")


async def log_consent(
    *,
    action: str,
    email: Optional[str] = None,
    user_id: Optional[str] = None,
    source: str = "api",
    ip: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    """Append an immutable consent event. Never raises to callers."""
    eid = str(uuid4())
    try:
        db = Database.get_raw() if hasattr(Database, "get_raw") else Database.get()
        raw = getattr(db, "_db", db)
        await raw.consent_events.insert_one(
            {
                "id": eid,
                "action": action,
                "email": (email or "").lower() or None,
                "user_id": user_id,
                "source": source,
                "ip": (ip or "")[:64] or None,
                "meta": meta or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as e:
        logger.warning("consent log failed action=%s err=%s", action, e)
    return eid
