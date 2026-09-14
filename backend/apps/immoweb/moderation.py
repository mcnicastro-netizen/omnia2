"""OMNIA — Private Listings Moderation (M3.S5 v2).

Admin endpoints to review B2C private property listings before they go live
on ImmobilCloud.

Only `super_admin` (platform-wide) and `group_admin` (holding) can moderate.
No fantom roles.

Endpoints (admin auth required):
  GET    /api/app/moderation/queue          — list pending listings
  POST   /api/app/moderation/{pid}/approve  — approve → status=active
  POST   /api/app/moderation/{pid}/reject   — reject with notes → status=draft
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database

logger = logging.getLogger("omnia.moderation")
router = APIRouter(prefix="/moderation", tags=["moderation"])

# H3 — B2C private listings are platform-wide (no tenant): only super_admin moderates.
ALLOWED_ROLES = {"super_admin"}


async def _ensure_admin(user: dict) -> None:
    if user.get("role") not in ALLOWED_ROLES:
        raise HTTPException(status_code=403, detail="moderation_forbidden")


class ModerationRejectPayload(BaseModel):
    notes: str = Field(min_length=3, max_length=1000)

    def stripped_notes(self) -> str:
        return self.notes.strip()


@router.get("/queue")
async def moderation_queue(
    status: Optional[str] = "pending",
    user: dict = Depends(get_current_user),
):
    """List private listings awaiting review (default) or any status."""
    await _ensure_admin(user)
    db = Database.get()
    flt = {"is_private_listing": True}
    if status in ("pending", "approved", "rejected"):
        flt["moderation_status"] = status
    cursor = db.properties.find(
        flt,
        {"_id": 0, "id": 1, "title": 1, "description": 1, "property_type": 1,
         "operation": 1, "city": 1, "address": 1, "price": 1, "rent_monthly": 1,
         "surface_sqm": 1, "rooms": 1, "bedrooms": 1, "bathrooms": 1,
         "photos": 1, "owner_user_id": 1, "owner": 1,
         "moderation_status": 1, "moderation_notes": 1,
         "moderation_reviewed_at": 1, "created_at": 1, "updated_at": 1,
         "status": 1},
    ).sort("created_at", -1)
    items = await cursor.to_list(length=200)
    return {"items": items, "total": len(items)}


@router.post("/{pid}/approve")
async def approve_listing(pid: str, user: dict = Depends(get_current_user)):
    await _ensure_admin(user)
    db = Database.get()
    p = await db.properties.find_one(
        {"id": pid, "is_private_listing": True}, {"_id": 0, "id": 1},
    )
    if not p:
        raise HTTPException(status_code=404, detail="listing_not_found")

    now = datetime.now(timezone.utc).isoformat()
    await db.properties.update_one(
        {"id": pid},
        {"$set": {
            "moderation_status": "approved",
            "status": "active",
            "visibility": "public",
            "moderation_notes": None,
            "moderation_reviewed_at": now,
            "moderation_reviewed_by": user["id"],
            "updated_at": now,
        }},
    )
    logger.info("listing approved: id=%s by=%s", pid, user["id"])
    return {"ok": True, "moderation_status": "approved", "status": "active"}


@router.post("/{pid}/reject")
async def reject_listing(
    pid: str, payload: ModerationRejectPayload,
    user: dict = Depends(get_current_user),
):
    await _ensure_admin(user)
    db = Database.get()
    p = await db.properties.find_one(
        {"id": pid, "is_private_listing": True}, {"_id": 0, "id": 1},
    )
    if not p:
        raise HTTPException(status_code=404, detail="listing_not_found")

    notes_clean = payload.stripped_notes()
    if len(notes_clean) < 3:
        raise HTTPException(status_code=422, detail="notes_too_short")

    now = datetime.now(timezone.utc).isoformat()
    await db.properties.update_one(
        {"id": pid},
        {"$set": {
            "moderation_status": "rejected",
            "status": "draft",
            "moderation_notes": notes_clean,
            "moderation_reviewed_at": now,
            "moderation_reviewed_by": user["id"],
            "updated_at": now,
        }},
    )
    logger.info("listing rejected: id=%s by=%s", pid, user["id"])
    return {"ok": True, "moderation_status": "rejected"}
