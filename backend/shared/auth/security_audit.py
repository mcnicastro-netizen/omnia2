"""OMNIA — security / RBAC audit trail (append-only).

Events land in ``security_events`` (not product CRM). Never store secrets.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def record_security_event(
    db,
    *,
    event: str,
    actor_user_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    target_user_id: Optional[str] = None,
    organization_id: Optional[str] = None,
    detail: Optional[dict[str, Any]] = None,
) -> None:
    """Best-effort append; failures must not break the primary mutation."""
    doc = {
        "id": str(uuid4()),
        "event": event,
        "actor_user_id": actor_user_id,
        "actor_role": actor_role,
        "target_user_id": target_user_id,
        "organization_id": organization_id,
        "detail": detail or {},
        "created_at": _now(),
    }
    try:
        await db.security_events.insert_one(doc)
    except Exception as exc:  # noqa: BLE001
        logger.warning("security_events insert failed (%s): %s", event, exc)
