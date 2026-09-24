"""OMNIA — B2C Favorites / wishlist (ImmobilCloud).

Endpoints under /api/cloud/me/favorites (B2C auth required).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database
from apps.immocloud.public_portal import _base_filter, _to_card

logger = logging.getLogger("omnia.favorites")
router = APIRouter(prefix="/me/favorites", tags=["cloud-favorites"])

MAX_FAVORITES = 100


async def _ensure_b2c(user: dict) -> None:
    if user.get("account_type") != "b2c" or user.get("role") != "client":
        raise HTTPException(status_code=403, detail="b2c_account_required")


@router.get("")
async def list_favorites(user: dict = Depends(get_current_user)):
    """Wishlist including ended listings (sold/rented/withdrawn) with status badge.

    Public search still hides non-active ads; favorites keep them so the user
    sees Idealista-style «venduto» instead of a silent disappearance (D-093).
    """
    await _ensure_b2c(user)
    db = Database.get()
    from shared.db.trash import with_not_trashed

    favs = await db.favorites.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).to_list(length=MAX_FAVORITES)
    pids = [f["property_id"] for f in favs]
    if not pids:
        return {"items": [], "total": 0}
    flt = with_not_trashed({"id": {"$in": pids}})
    props = await db.properties.find(flt, {"_id": 0}).to_list(length=MAX_FAVORITES)
    by_id = {p["id"]: p for p in props}
    agency_ids = list({p.get("agency_id") for p in props if p.get("agency_id")})
    agencies: Dict[str, Any] = {}
    if agency_ids:
        async for a in db.agencies.find(
            {"id": {"$in": agency_ids}, "is_active": True},
            {"_id": 0, "id": 1, "name": 1, "slug": 1},
        ):
            agencies[a["id"]] = a
    ended = {"sold", "rented", "withdrawn"}
    items = []
    for f in favs:
        p = by_id.get(f["property_id"])
        if not p:
            continue
        card = _to_card(p, agencies.get(p.get("agency_id")))
        card["favorited_at"] = f.get("created_at")
        st = p.get("status") or "active"
        card["listing_status"] = st
        card["listing_ended"] = st in ended
        card["listing_end_status"] = p.get("listing_end_status") or (st if st in ended else None)
        items.append(card)
    return {"items": items, "total": len(items)}


@router.get("/ids")
async def favorite_ids(user: dict = Depends(get_current_user)):
    """Lightweight id set for heart toggles on search cards."""
    await _ensure_b2c(user)
    db = Database.get()
    ids = [
        d["property_id"]
        async for d in db.favorites.find({"user_id": user["id"]}, {"_id": 0, "property_id": 1})
    ]
    return {"ids": ids}


@router.post("/{pid}", status_code=201)
async def add_favorite(pid: str, user: dict = Depends(get_current_user)):
    await _ensure_b2c(user)
    db = Database.get()
    prop = await db.properties.find_one({**_base_filter(), "id": pid}, {"_id": 0, "id": 1})
    if not prop:
        raise HTTPException(status_code=404, detail="property_not_found")
    existing = await db.favorites.find_one({"user_id": user["id"], "property_id": pid})
    if existing:
        return {"id": existing["id"], "property_id": pid, "already": True}
    count = await db.favorites.count_documents({"user_id": user["id"]})
    if count >= MAX_FAVORITES:
        raise HTTPException(status_code=409, detail="favorites_limit_reached")
    doc = {
        "id": str(uuid4()),
        "user_id": user["id"],
        "property_id": pid,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.favorites.insert_one(doc)
    return {"id": doc["id"], "property_id": pid, "already": False}


@router.delete("/{pid}", status_code=204)
async def remove_favorite(pid: str, user: dict = Depends(get_current_user)):
    await _ensure_b2c(user)
    db = Database.get()
    r = await db.favorites.delete_one({"user_id": user["id"], "property_id": pid})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="favorite_not_found")
