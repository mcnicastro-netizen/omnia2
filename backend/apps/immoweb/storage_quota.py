"""OMNIA — Storage usage API (D-085)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from shared.auth.dependencies import get_current_user, require_roles
from shared.auth.tenant import arequire_agency as _require_agency
from shared.db.connection import Database
from shared.models.base import utcnow_iso
from shared.storage.quota import STORAGE_ADDON_GB, get_storage_status

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/usage")
async def storage_usage(user: dict = Depends(get_current_user)):
    """Meter: used vs quota for the active agency."""
    agency_id = await _require_agency(user)
    db = Database.get()
    return await get_storage_status(db, agency_id)


@router.post("/grant-extra")
async def grant_extra_storage(
    packs: int = Query(1, ge=1, le=50),
    agency_id: Optional[str] = Query(None),
    user: dict = Depends(require_roles("super_admin")),
):
    """Founder/support: add N×100 GB to an agency (no Stripe)."""
    db = Database.get()
    aid = agency_id or await _require_agency(user)
    agency = await db.agencies.find_one({"id": aid})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    new_extra = int(agency.get("storage_extra_gb") or 0) + packs * STORAGE_ADDON_GB
    await db.agencies.update_one(
        {"id": aid},
        {"$set": {"storage_extra_gb": new_extra, "updated_at": utcnow_iso()}},
    )
    return await get_storage_status(db, aid)
