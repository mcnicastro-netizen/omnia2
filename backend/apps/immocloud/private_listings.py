"""OMNIA — ImmobilCloud B2C Private Listings (M3.S5 v2).

Lets B2C users (role='client') publish their own property ad without going
through an agency. Properties created here have:
  - agency_id = "_private_listings"     # sentinel (no real agency)
  - is_private_listing = True
  - owner_user_id = current user id
  - status = "draft" until user submits
  - moderation_status = "pending"       # admin must approve

Endpoints (B2C auth required):
  POST   /api/cloud/me/properties        — create new private ad
  GET    /api/cloud/me/properties        — list my own ads (any status)
  GET    /api/cloud/me/properties/{pid}  — detail of my own ad
  PATCH  /api/cloud/me/properties/{pid}  — edit my own ad (resets to pending on substantive change)
  POST   /api/cloud/me/properties/{pid}/submit — submit for moderation
  DELETE /api/cloud/me/properties/{pid}  — delete

A free B2C user can keep at most 1 *active* private listing (limit_count below).
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database
from shared.models.property import PropertyCreate, PropertyUpdate
from apps.immocloud.geocoding import schedule_geocode

logger = logging.getLogger("omnia.private_listings")
router = APIRouter(prefix="/me/properties", tags=["cloud-private-listings"])

PRIVATE_AGENCY_SENTINEL = "_private_listings"
FREE_TIER_MAX_ACTIVE = 1  # one free ad per user


async def _ensure_b2c(user: dict) -> None:
    if user.get("account_type") != "b2c":
        raise HTTPException(status_code=403, detail="b2c_account_required")
    if user.get("role") != "client":
        raise HTTPException(status_code=403, detail="b2c_account_required")


def _strip(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


@router.post("", status_code=201)
async def create_private_listing(
    payload: PropertyCreate,
    user: dict = Depends(get_current_user),
):
    await _ensure_b2c(user)
    db = Database.get()

    # Free-tier limit: max 1 active listing
    active_count = await db.properties.count_documents({
        "owner_user_id": user["id"],
        "is_private_listing": True,
        "status": {"$in": ["draft", "active"]},
    })
    if active_count >= FREE_TIER_MAX_ACTIVE:
        raise HTTPException(status_code=409, detail="free_tier_listing_limit_reached")

    now = datetime.now(timezone.utc).isoformat()
    data = payload.model_dump()
    data.update({
        "id": str(uuid4()),
        "agency_id": PRIVATE_AGENCY_SENTINEL,
        "is_private_listing": True,
        "owner_user_id": user["id"],
        "status": "draft",
        "moderation_status": "pending",
        "moderation_notes": None,
        "moderation_reviewed_at": None,
        "moderation_reviewed_by": None,
        "view_count": 0,
        "lead_count": 0,
        "created_at": now,
        "updated_at": now,
    })
    # Owner contact pre-populated from user profile (private/internal field)
    data["owner"] = {
        "name": user.get("name"),
        "phone": user.get("phone"),
        "email": user.get("email"),
        "notes": None,
    }
    await db.properties.insert_one(data)

    if not data.get("lat") and not data.get("lng"):
        schedule_geocode(db, data["id"], {
            "address": data.get("address"), "city": data.get("city"),
            "province": data.get("province"), "postal_code": data.get("postal_code"),
        })

    logger.info("private listing created: id=%s user=%s", data["id"], user["id"])
    return _strip(data)


@router.get("")
async def list_my_private_listings(user: dict = Depends(get_current_user)):
    await _ensure_b2c(user)
    db = Database.get()
    cursor = db.properties.find(
        {"owner_user_id": user["id"], "is_private_listing": True},
        {"_id": 0, "owner": 0},
    ).sort("created_at", -1)
    items = await cursor.to_list(length=50)
    return {"items": items, "total": len(items)}


@router.get("/{pid}")
async def get_my_private_listing(pid: str, user: dict = Depends(get_current_user)):
    await _ensure_b2c(user)
    db = Database.get()
    p = await db.properties.find_one(
        {"id": pid, "owner_user_id": user["id"], "is_private_listing": True},
        {"_id": 0},
    )
    if not p:
        raise HTTPException(status_code=404, detail="listing_not_found")
    return p


@router.patch("/{pid}")
async def update_my_private_listing(
    pid: str, payload: PropertyUpdate, user: dict = Depends(get_current_user),
):
    await _ensure_b2c(user)
    db = Database.get()
    existing = await db.properties.find_one(
        {"id": pid, "owner_user_id": user["id"], "is_private_listing": True},
        {"_id": 0, "address": 1, "city": 1, "province": 1, "postal_code": 1,
         "moderation_status": 1, "status": 1},
    )
    if not existing:
        raise HTTPException(status_code=404, detail="listing_not_found")

    update_doc = payload.model_dump(exclude_unset=True)
    if "status" in update_doc:
        # Users can only set status to draft (we expose /submit for active)
        update_doc.pop("status", None)
    update_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    # If previously rejected/approved and substantive edit → back to pending
    substantive = any(k in update_doc for k in
                      ("title", "description", "price", "rent_monthly", "address",
                       "city", "surface_sqm", "rooms", "photos"))
    if substantive and existing.get("moderation_status") in ("approved", "rejected"):
        update_doc["moderation_status"] = "pending"
        update_doc["status"] = "draft"

    await db.properties.update_one({"id": pid}, {"$set": update_doc})

    if any(k in update_doc for k in ("address", "city", "province", "postal_code")):
        full = await db.properties.find_one({"id": pid}, {"_id": 0})
        schedule_geocode(db, pid, {
            "address": full.get("address"), "city": full.get("city"),
            "province": full.get("province"), "postal_code": full.get("postal_code"),
        })

    updated = await db.properties.find_one({"id": pid}, {"_id": 0})
    return updated


@router.post("/{pid}/submit")
async def submit_for_moderation(pid: str, user: dict = Depends(get_current_user)):
    """Move a draft listing into the moderation queue. Status stays 'draft'
    until admin approves (then becomes 'active'), or 'rejected'."""
    await _ensure_b2c(user)
    db = Database.get()
    p = await db.properties.find_one(
        {"id": pid, "owner_user_id": user["id"], "is_private_listing": True},
        {"_id": 0, "id": 1, "title": 1, "city": 1, "price": 1, "rent_monthly": 1,
         "moderation_status": 1, "status": 1},
    )
    if not p:
        raise HTTPException(status_code=404, detail="listing_not_found")
    if p.get("moderation_status") == "approved" and p.get("status") == "active":
        raise HTTPException(status_code=409, detail="already_approved_and_active")

    # Minimum viable ad: title, city, AT LEAST one of price/rent_monthly
    if not (p.get("title") and p.get("city") and (p.get("price") or p.get("rent_monthly"))):
        raise HTTPException(status_code=400, detail="missing_required_fields")

    await db.properties.update_one(
        {"id": pid},
        {"$set": {
            "moderation_status": "pending",
            "moderation_notes": None,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    logger.info("private listing submitted: id=%s user=%s", pid, user["id"])
    return {"ok": True, "moderation_status": "pending"}


@router.delete("/{pid}", status_code=204)
async def delete_my_private_listing(pid: str, user: dict = Depends(get_current_user)):
    await _ensure_b2c(user)
    db = Database.get()
    r = await db.properties.delete_one(
        {"id": pid, "owner_user_id": user["id"], "is_private_listing": True},
    )
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="listing_not_found")
    return None
