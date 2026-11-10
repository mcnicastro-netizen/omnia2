"""D-157 — Credenziali gestionale: API key = password iniziale (show-once)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from shared.auth.api_key import generate_plaintext_key, hash_key, prefix_of
from shared.auth.hashing import hash_password
from shared.db.connection import Database
from shared.models.api_key import ApiKeyInDB

logger = logging.getLogger("omnia.agency_credentials")


async def agency_payment_ok(db, agency_id: str) -> bool:
    """True se c'è subscription attiva/trialing o tx subscription paid."""
    sub = await db.subscriptions.find_one(
        {"agency_id": agency_id},
        {"_id": 0, "status": 1},
    )
    if sub and (sub.get("status") or "").lower() in ("active", "trialing", "paid"):
        return True
    tx = await db.payment_transactions.find_one(
        {
            "agency_id": agency_id,
            "kind": "subscription",
            "payment_status": "paid",
        },
        {"_id": 0, "session_id": 1},
    )
    return bool(tx)


async def issue_login_api_credential(
    *,
    user_id: str,
    agency_id: str,
    name: str = "Accesso gestionale",
    issued_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Emette API key plaintext, la salva hashed, e la imposta come password_hash utente.

    La plaintext è restituita **una sola volta** (mai riletta da DB).
    """
    db = Database.get()
    plaintext = generate_plaintext_key()
    now = datetime.now(timezone.utc).isoformat()
    doc = ApiKeyInDB(
        agency_id=agency_id,
        name=(name or "Accesso gestionale")[:120],
        key_prefix=prefix_of(plaintext),
        key_hash=hash_key(plaintext),
        credits_balance=0,
        partner_id=None,
        allowed_origins=[],
    ).model_dump()
    doc["purpose"] = "login_bootstrap"
    doc["issued_by"] = issued_by
    await db.api_keys.insert_one(doc)
    await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "password_hash": hash_password(plaintext),
                "must_change_password": True,
                "login_credential_issued_at": now,
                "updated_at": now,
            }
        },
    )
    logger.warning(
        "login credential issued user=%s agency=%s prefix=%s by=%s",
        user_id,
        agency_id,
        doc["key_prefix"],
        issued_by,
    )
    return {
        "ok": True,
        "key": plaintext,
        "key_prefix": doc["key_prefix"],
        "api_key_id": doc["id"],
        "must_change_password": True,
    }
