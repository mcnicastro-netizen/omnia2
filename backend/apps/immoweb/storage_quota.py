"""OMNIA — Storage usage API (D-085 + D-175 C6)."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from shared.auth.dependencies import get_current_user, require_roles
from shared.auth.tenant import arequire_agency as _require_agency
from shared.db.connection import Database
from shared.models.base import utcnow_iso
from shared.storage.quota import (
    STORAGE_ADDON_GB,
    get_storage_status,
    get_storage_status_for_cc,
)

router = APIRouter(prefix="/storage", tags=["storage"])


@router.get("/usage")
async def storage_usage(user: dict = Depends(get_current_user)):
    """Meter: org usage + shared CC pool (S3)."""
    agency_id = await _require_agency(user)
    db = Database.get()
    return await get_storage_status(db, agency_id)


@router.get("/usage/commercial-customer/{commercial_customer_id}")
async def storage_usage_cc(
    commercial_customer_id: str,
    user: dict = Depends(get_current_user),
):
    """Central CC pool meter + per-org breakdown (Main Admin / Super Admin)."""
    db = Database.get()
    cc_id = (commercial_customer_id or "").strip()
    if not cc_id:
        raise HTTPException(status_code=400, detail="commercial_customer_id_required")

    role = (user.get("role") or "").strip()
    if role != "super_admin":
        cc = await db.commercial_customers.find_one(
            {"id": cc_id}, {"_id": 0, "main_admin_user_id": 1}
        )
        if not cc or cc.get("main_admin_user_id") != user.get("id"):
            raise HTTPException(status_code=403, detail="forbidden")

    return await get_storage_status_for_cc(db, cc_id)


@router.post("/grant-extra")
async def grant_extra_storage(
    packs: int = Query(1, ge=1, le=50),
    agency_id: Optional[str] = Query(None),
    commercial_customer_id: Optional[str] = Query(None),
    user: dict = Depends(require_roles("super_admin")),
):
    """Founder/support: add N×100 GB to CC SoT (S1). Resolves CC from agency if needed."""
    db = Database.get()
    cc_id = (commercial_customer_id or "").strip() or None
    aid = (agency_id or "").strip() or None
    if not cc_id:
        aid = aid or await _require_agency(user)
        agency = await db.agencies.find_one(
            {"id": aid}, {"_id": 0, "id": 1, "commercial_customer_id": 1}
        )
        if not agency:
            raise HTTPException(status_code=404, detail="agency_not_found")
        cc_id = (agency.get("commercial_customer_id") or "").strip() or None
        if not cc_id:
            raise HTTPException(
                status_code=400,
                detail="commercial_customer_required",
            )

    cc = await db.commercial_customers.find_one({"id": cc_id}, {"_id": 0, "id": 1})
    if not cc:
        raise HTTPException(status_code=404, detail="commercial_customer_not_found")

    delta = packs * STORAGE_ADDON_GB
    await db.commercial_customers.update_one(
        {"id": cc_id},
        {
            "$inc": {"storage_extra_gb": delta},
            "$set": {"updated_at": utcnow_iso()},
        },
    )
    return await get_storage_status_for_cc(db, cc_id)
