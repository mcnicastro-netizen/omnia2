"""OMNIA — B2C Valuator entitlements + rate-limit + payload hashing.

Companion module for `apps/immocloud/valuator.py` (Cap. 21 B2C-VAL-01).

Two MongoDB collections:
- **`b2c_valuation_usage`**: append-only record of every completed base-tier
  valuation. Fields: `user_id`, `tier` ("base"|"uni"), `created_at`,
  `valuation_id`. Consumed by `check_base_valuation_allowed` to enforce
  the 1×/12mo rate-limit.
- **`b2c_purchases`**: Stripe one-shot purchase ledger with 24h expiry.
  Fields: `id`, `user_id`, `product_key`, `stripe_session_id`,
  `payload_hash`, `status` ("pending"|"paid"|"failed"),
  `created_at`, `expires_at`.

Regole D-051 (brief §2):
- BASE tier: 1 valuation ogni 12 mesi per user_id, email_verified required.
- UNI tier: entitlement valido 24h per stesso payload_hash (SHA-256 del JSON).

Le funzioni sono pure I/O sul DB — non conoscono FastAPI ne' Stripe.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

from shared.db.connection import Database

logger = logging.getLogger("omnia.b2c_entitlements")

BASE_TIER_COOLDOWN_DAYS = 365
UNI_ENTITLEMENT_TTL_HOURS = 24


def hash_valuation_payload(payload: Dict[str, Any]) -> str:
    """Deterministic SHA-256 of a valuation payload (JSON canonical form).

    Only the fields that influence the valuation are hashed — email/name
    (lead-capture) sono esclusi, cosi' l'utente puo' riscaricare il PDF
    entro 24h senza reincollare il nome.
    """
    if not isinstance(payload, dict):
        payload = dict(payload)
    keys_to_hash = (
        "city", "zone", "address", "property_type", "surface_sqm",
        "condition", "energy_class", "floor",
        "commercial_surfaces", "merit",
    )
    canonical = {k: payload.get(k) for k in keys_to_hash}
    blob = json.dumps(canonical, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


async def check_base_valuation_allowed(user_id: str) -> Tuple[bool, Optional[str]]:
    """Return `(allowed, reset_at_iso)` for a base-tier valuation.

    - `allowed=True, reset_at=None` when the user has 0 base valuations in the
      last 365 days.
    - `allowed=False, reset_at=<iso>` when the user already spent their yearly
      quota; `reset_at` is the timestamp when they'll be allowed again
      (last base valuation + 365d).
    """
    db = Database.get()
    threshold_iso = (datetime.now(timezone.utc) - timedelta(days=BASE_TIER_COOLDOWN_DAYS)).isoformat()
    last = await db.b2c_valuation_usage.find_one(
        {"user_id": user_id, "tier": "base", "created_at": {"$gte": threshold_iso}},
        sort=[("created_at", -1)],
    )
    if not last:
        return True, None
    try:
        last_dt = datetime.fromisoformat(last["created_at"].replace("Z", "+00:00"))
    except (ValueError, KeyError, AttributeError):
        # Corrupted record — fail-open so we don't lock the user forever.
        logger.warning("b2c_valuation_usage record with unparseable created_at: %s", last)
        return True, None
    reset_at = last_dt + timedelta(days=BASE_TIER_COOLDOWN_DAYS)
    return False, reset_at.isoformat()


async def record_base_valuation(user_id: str, valuation_id: str) -> None:
    """Persist a base-tier valuation record for rate-limit tracking."""
    db = Database.get()
    await db.b2c_valuation_usage.insert_one({
        "id": uuid4().hex,
        "user_id": user_id,
        "tier": "base",
        "valuation_id": valuation_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


async def check_uni_entitlement(user_id: str, payload_hash: str) -> bool:
    """Return True if the user has a paid UNI purchase (status=paid) that has
    not yet expired AND matches the given `payload_hash`.

    Payload hash matching keeps the entitlement "sticky" — an user cannot pay
    once and then reuse the entitlement for a totally different property.
    """
    if not user_id or not payload_hash:
        return False
    now_iso = datetime.now(timezone.utc).isoformat()
    db = Database.get()
    doc = await db.b2c_purchases.find_one({
        "user_id": user_id,
        "product_key": "b2c_valuator_uni_pdf",
        "payload_hash": payload_hash,
        "status": "paid",
        "expires_at": {"$gt": now_iso},
    })
    return bool(doc)


async def record_uni_purchase(
    *,
    user_id: str,
    stripe_session_id: str,
    payload_hash: Optional[str],
    product_key: str = "b2c_valuator_uni_pdf",
    status: str = "pending",
) -> str:
    """Create a b2c_purchases record. Returns internal id."""
    db = Database.get()
    now = datetime.now(timezone.utc)
    doc_id = uuid4().hex
    await db.b2c_purchases.insert_one({
        "id": doc_id,
        "user_id": user_id,
        "product_key": product_key,
        "stripe_session_id": stripe_session_id,
        "payload_hash": payload_hash,
        "status": status,
        "created_at": now.isoformat(),
        "expires_at": None,  # populated only when status transitions to paid
    })
    return doc_id


async def mark_uni_purchase_paid(stripe_session_id: str) -> Optional[dict]:
    """Idempotent: called from the Stripe webhook (checkout.session.completed).
    Marks the purchase paid and sets `expires_at = now + 24h`."""
    db = Database.get()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=UNI_ENTITLEMENT_TTL_HOURS)
    doc = await db.b2c_purchases.find_one_and_update(
        {"stripe_session_id": stripe_session_id},
        {"$set": {
            "status": "paid",
            "paid_at": now.isoformat(),
            "expires_at": expires.isoformat(),
        }},
        return_document=True,
    )
    return doc


async def count_uni_purchases_today(user_id: str) -> int:
    """Enforce the daily cap (5 UNI purchases per user, `b2c_products.py`)."""
    db = Database.get()
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    n = await db.b2c_purchases.count_documents({
        "user_id": user_id,
        "product_key": "b2c_valuator_uni_pdf",
        "created_at": {"$gte": start.isoformat()},
    })
    return int(n)


def is_uni_payload(payload: Dict[str, Any]) -> bool:
    """Return True when a valuation payload requires UNI tier (paid) —
    i.e. any of `commercial_surfaces` or `merit` is present and non-empty."""
    cs = payload.get("commercial_surfaces") if isinstance(payload, dict) else None
    me = payload.get("merit") if isinstance(payload, dict) else None
    # For pydantic models
    if cs is None and hasattr(payload, "commercial_surfaces"):
        cs = getattr(payload, "commercial_surfaces")
    if me is None and hasattr(payload, "merit"):
        me = getattr(payload, "merit")

    def _non_empty(v: Any) -> bool:
        if v is None:
            return False
        if hasattr(v, "model_dump"):
            v = v.model_dump(exclude_none=True)
        if isinstance(v, dict):
            return any(vv not in (None, 0, "", False) for vv in v.values())
        return bool(v)

    return _non_empty(cs) or _non_empty(me)
