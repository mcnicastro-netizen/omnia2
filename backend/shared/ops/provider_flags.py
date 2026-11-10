"""Kill-switch persistente per fornitori esterni (Cabina · Onda 2).

Mongo `provider_flags` + mirror in-memory su circuit holds.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from shared.db.connection import Database
from shared.security import circuit as circuit_mod

logger = logging.getLogger("omnia.provider_flags")

KNOWN = ("resend", "fal", "gemini", "llm", "stripe", "openai", "tavily", "mongodb")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def load_holds_into_circuit() -> int:
    """All'avvio API: ripristina kill-switch da Mongo → circuit holds."""
    try:
        db = Database.get()
        docs = await db.provider_flags.find({"killed": True}, {"_id": 0, "id": 1}).to_list(
            length=50
        )
        n = 0
        for d in docs:
            pid = (d.get("id") or "").strip()
            if not pid:
                continue
            circuit_mod.force_hold(pid)
            # alias LLM
            if pid == "gemini":
                circuit_mod.force_hold("llm")
            n += 1
        if n:
            logger.warning("provider kill-switches restored: %s", n)
        return n
    except Exception:  # noqa: BLE001
        logger.exception("load_holds_into_circuit failed")
        return 0


async def list_flags() -> List[Dict[str, Any]]:
    db = Database.get()
    docs = await db.provider_flags.find({}, {"_id": 0}).to_list(length=50)
    by_id = {d["id"]: d for d in docs if d.get("id")}
    out = []
    for pid in KNOWN:
        d = by_id.get(pid) or {"id": pid, "killed": False}
        out.append(
            {
                "id": pid,
                "killed": bool(d.get("killed")),
                "updated_at": d.get("updated_at"),
                "updated_by_email": d.get("updated_by_email"),
                "note": d.get("note") or "",
                "held": circuit_mod.is_held(pid) or (pid == "gemini" and circuit_mod.is_held("llm")),
            }
        )
    return out


async def set_killed(
    provider_id: str,
    *,
    killed: bool,
    user: Optional[dict] = None,
    note: str = "",
) -> Dict[str, Any]:
    pid = (provider_id or "").strip().lower()
    if pid not in KNOWN:
        raise ValueError("unknown_provider")
    db = Database.get()
    now = _now()
    doc = {
        "id": pid,
        "killed": bool(killed),
        "updated_at": now,
        "updated_by": (user or {}).get("id"),
        "updated_by_email": (user or {}).get("email"),
        "note": (note or "").strip()[:500],
    }
    await db.provider_flags.update_one({"id": pid}, {"$set": doc}, upsert=True)
    if killed:
        circuit_mod.force_hold(pid)
        if pid == "gemini":
            circuit_mod.force_hold("llm")
    else:
        circuit_mod.clear_hold(pid)
        if pid == "gemini":
            circuit_mod.clear_hold("llm")
    logger.warning(
        "provider_flag id=%s killed=%s by=%s",
        pid,
        killed,
        (user or {}).get("email"),
    )
    return doc
