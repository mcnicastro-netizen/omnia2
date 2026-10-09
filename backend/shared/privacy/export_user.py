"""P-038 — GDPR data export (portability / access) for authenticated user."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from shared.db.connection import Database


async def build_user_export(user: dict) -> Dict[str, Any]:
    """Assemble a JSON-serializable snapshot of personal data for the user."""
    db = Database.get()
    uid = user["id"]
    email = (user.get("email") or "").lower()
    now = datetime.now(timezone.utc).isoformat()

    async def _list(coll: str, flt: dict, limit: int = 500) -> List[dict]:
        out: List[dict] = []
        try:
            cur = db[coll].find(flt, {"_id": 0}).limit(limit)
            async for doc in cur:
                out.append(doc)
        except Exception:
            pass
        return out

    profile = {
        "id": uid,
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role"),
        "account_type": user.get("account_type"),
        "lang": user.get("lang"),
        "intents": user.get("intents") or [],
        "notification_channels": user.get("notification_channels") or [],
        "marketing_consent": bool(user.get("marketing_consent")),
        "age_confirmed": bool(user.get("age_confirmed")),
        "email_verified": bool(user.get("email_verified")),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }

    return {
        "exported_at": now,
        "format": "omnia_b2c_export_v1",
        "profile": profile,
        "favorites": await _list("favorites", {"user_id": uid}),
        "saved_searches": await _list("saved_searches", {"user_id": uid}),
        "b2c_purchases": await _list("b2c_purchases", {"user_id": uid}),
        "consent_events": await _list(
            "consent_events",
            {"$or": [{"user_id": uid}, {"email": email}]},
        ),
        "mortgage_leads": await _list("mortgage_leads", {"email": email}),
        "visura_orders": await _list("visura_orders", {"user_id": uid}),
        "listing_inquiries": await _list("listing_inquiries", {"email": email}),
        "private_listings": await _list(
            "properties",
            {"owner_user_id": uid},
            limit=200,
        ),
        "al_legal_sessions": await _list("al_legal_sessions", {"user_id": uid}, limit=100),
        "valuation_leads": await _list("valuation_leads", {"email": email}),
    }
