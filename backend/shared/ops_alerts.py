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
) -> None:
    """Persist an operational alert. Never raises to callers."""
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
        await db.ops_alerts.insert_one(doc)
    except Exception:
        logger.exception("ops_alerts insert failed kind=%s", kind)
    level = logging.ERROR if severity == "error" else logging.WARNING
    logger.log(level, "OPS_ALERT [%s/%s] %s", severity, kind, message[:200])
