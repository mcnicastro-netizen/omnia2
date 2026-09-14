"""OMNIA — API Keys management (M2.5.2 Track B, D-041/D-046).

Endpoints under `/api/app/api-keys` — JWT-protected UI management by
agency_admin (or group_admin). Not to be confused with `/api/v1/*` which
consumes API keys as auth.
"""
import logging
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, Depends

from shared.db.connection import Database
from shared.auth.dependencies import require_roles
from shared.auth.api_key import (
    generate_plaintext_key,
    hash_key,
    prefix_of,
)
from shared.models.api_key import (
    ApiKeyInDB,
    ApiKeyPublic,
    ApiKeyCreate,
    ApiKeyIssueResponse,
    CreditAdjustment,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api-keys", tags=["api-keys"])


def _to_public(doc: dict) -> dict:
    """Strip hash/_id from a stored key doc before returning."""
    return {k: v for k, v in doc.items() if k not in ("_id", "key_hash")}


def _agency_id_of(user: dict) -> str:
    agencies = user.get("agency_ids") or []
    if not agencies:
        raise HTTPException(status_code=404, detail="no_agency")
    return agencies[0]


# ---------------- LIST ----------------

@router.get("")
async def list_api_keys(user: dict = Depends(require_roles("agency_admin", "super_admin"))):
    """List API keys of the caller's agency (group_admin sees all group keys)."""
    db = Database.get()

    if user.get("role") == "super_admin" or user.get("role") == "group_admin":
        gid = user.get("group_id")
        if gid:
            # scoped to the group's branches
            branch_ids = [a["id"] async for a in db.agencies.find({"group_id": gid}, {"id": 1})]
            flt = {"agency_id": {"$in": branch_ids}} if branch_ids else {"agency_id": _agency_id_of(user)}
        else:
            flt = {"agency_id": _agency_id_of(user)}
    else:
        flt = {"agency_id": _agency_id_of(user)}

    cursor = db.api_keys.find(flt).sort("created_at", -1)
    docs = await cursor.to_list(length=500)
    return {"items": [_to_public(d) for d in docs], "total": len(docs)}


# ---------------- CREATE / ISSUE ----------------

@router.post("", status_code=201, response_model=ApiKeyIssueResponse)
async def create_api_key(
    payload: ApiKeyCreate,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Issue a new API key. **Plaintext returned once, never stored plaintext.**"""
    db = Database.get()
    agency_id = _agency_id_of(user)

    plaintext = generate_plaintext_key()
    doc = ApiKeyInDB(
        agency_id=agency_id,
        group_id=user.get("group_id"),
        name=payload.name,
        key_prefix=prefix_of(plaintext),
        key_hash=hash_key(plaintext),
        credits_balance=payload.initial_credits,
        partner_id=payload.partner_id,
        allowed_origins=payload.allowed_origins or [],
    ).model_dump()
    await db.api_keys.insert_one(doc)
    logger.info(
        "API key issued: id=%s agency=%s prefix=%s partner=%s by=%s",
        doc["id"], agency_id, doc["key_prefix"], doc.get("partner_id"), user["email"],
    )
    return {"key": plaintext, "api_key": _to_public(doc)}


# ---------------- REVOKE ----------------

@router.post("/{key_id}/revoke")
async def revoke_api_key(
    key_id: str,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Deactivate a key immediately (cannot be undone — issue a new one instead)."""
    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    r = await db.api_keys.update_one(
        {"id": key_id, "agency_id": _agency_id_of(user)},
        {"$set": {"is_active": False, "revoked_at": now, "updated_at": now}},
    )
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="api_key_not_found")
    logger.info("API key revoked: id=%s by=%s", key_id, user["email"])
    return {"status": "ok", "id": key_id, "revoked_at": now}


# ---------------- ORIGINS (M2.5.3 widget security) ----------------

from pydantic import BaseModel as _PydanticBase


class AllowedOriginsUpdate(_PydanticBase):
    allowed_origins: list = []


@router.patch("/{key_id}/origins")
async def update_allowed_origins(
    key_id: str,
    payload: AllowedOriginsUpdate,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Update the origin whitelist for a widget-facing API key."""
    db = Database.get()
    origins = [str(o).strip().rstrip("/") for o in (payload.allowed_origins or []) if o]
    now = datetime.now(timezone.utc).isoformat()
    r = await db.api_keys.update_one(
        {"id": key_id, "agency_id": _agency_id_of(user)},
        {"$set": {"allowed_origins": origins, "updated_at": now}},
    )
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="api_key_not_found")
    updated = await db.api_keys.find_one({"id": key_id})
    return _to_public(updated)


# ---------------- CREDITS ADJUSTMENT (manual until M4/Stripe) ----------------

@router.post("/{key_id}/credits")
async def adjust_credits(
    key_id: str,
    payload: CreditAdjustment,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Top-up (delta > 0) or deduct (delta < 0). Manual until M4 Stripe."""
    db = Database.get()
    key = await db.api_keys.find_one({"id": key_id, "agency_id": _agency_id_of(user)})
    if not key:
        raise HTTPException(status_code=404, detail="api_key_not_found")
    new_balance = int(key.get("credits_balance", 0)) + payload.delta
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="balance_would_go_negative")

    now = datetime.now(timezone.utc).isoformat()
    await db.api_keys.update_one(
        {"id": key_id},
        {"$set": {"credits_balance": new_balance, "updated_at": now}},
    )
    await db.api_credit_ledger.insert_one({
        "api_key_id": key_id,
        "agency_id": key["agency_id"],
        "delta": payload.delta,
        "new_balance": new_balance,
        "reason": payload.reason,
        "actor_user_id": user["id"],
        "created_at": now,
    })
    updated = await db.api_keys.find_one({"id": key_id})
    return _to_public(updated)


# ---------------- USAGE LOG ----------------

@router.get("/{key_id}/usage")
async def key_usage(
    key_id: str,
    limit: int = 50,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Return the last N usage rows for a given key (billing audit)."""
    db = Database.get()
    key = await db.api_keys.find_one({"id": key_id, "agency_id": _agency_id_of(user)})
    if not key:
        raise HTTPException(status_code=404, detail="api_key_not_found")
    cursor = db.api_usage_log.find(
        {"api_key_id": key_id}, {"_id": 0}
    ).sort("created_at", -1).limit(min(max(limit, 1), 500))
    items = await cursor.to_list(length=500)
    return {"items": items, "total": len(items)}
