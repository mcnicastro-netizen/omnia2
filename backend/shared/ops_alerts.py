"""OMNIA — lightweight ops alerts for Founder (no external APM required).

Writes to Mongo `ops_alerts`. Shown on Founder Ops cruscotto.
Also logs at WARNING so tunnel/stdout catch them during demos.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger("omnia.ops_alerts")


async def record_alert(
    *,
    kind: str,
    message: str,
    severity: str = "warning",
    meta: Optional[Dict[str, Any]] = None,
    dedupe_hours: Optional[int] = None,
) -> None:
    """Persist an operational alert. Never raises to callers.

    P-053: kinds like stripe_webhook default to 24h dedupe (unacked same kind).
    """
    if dedupe_hours is None and kind in ("stripe_webhook",):
        dedupe_hours = 24
    doc = {
        "id": str(uuid4()),
        "kind": kind,
        "severity": severity,
        "message": (message or "")[:500],
        "meta": meta or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "acked": False,
    }
    try:
        from shared.db.connection import Database
        db = Database.get()
        if dedupe_hours and dedupe_hours > 0:
            from datetime import timedelta
            cutoff = (
                datetime.now(timezone.utc) - timedelta(hours=dedupe_hours)
            ).isoformat()
            existing = await db.ops_alerts.find_one(
                {
                    "kind": kind,
                    "acked": False,
                    "created_at": {"$gte": cutoff},
                },
                {"_id": 0, "id": 1},
            )
            if existing:
                logger.warning(
                    "OPS_ALERT deduped kind=%s existing=%s", kind, existing.get("id"),
                )
                return
        await db.ops_alerts.insert_one(doc)
    except Exception:
        logger.exception("ops_alerts insert failed kind=%s", kind)
    level = logging.ERROR if severity == "error" else logging.WARNING
    logger.log(level, "OPS_ALERT [%s/%s] %s", severity, kind, message[:200])
