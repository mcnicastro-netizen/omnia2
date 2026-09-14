"""OMNIA — Privacy Audit endpoints for agents (M3.S9, D-062).

Provides:
  PATCH /api/app/properties/{id}/privacy   — set privacy_level with audit trail
  GET   /api/app/properties/{id}/privacy   — read current level + audit history
  GET   /api/app/properties/{id}/privacy/preview?viewer=L1|L2|L3|L4
        — dry-run view of what each viewer level sees

Tenant isolation: property must belong to caller's agency.
"""
from __future__ import annotations
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from shared.auth.dependencies import require_roles
from shared.db.connection import Database
from shared.utils.privacy_gate import apply_privacy_view, log_privacy_change

router = APIRouter(prefix="/properties", tags=["property-privacy"])

Level = Literal["L1", "L2", "L3", "L4"]


class PrivacyUpdateBody(BaseModel):
    privacy_level: Level
    reason: Optional[str] = Field(default=None, max_length=500)


from shared.auth.tenant import require_agency_404 as _agency_id


async def _get_owned(db, pid: str, aid: str) -> dict:
    p = await db.properties.find_one({"id": pid, "agency_id": aid})
    if not p:
        raise HTTPException(status_code=404, detail="property_not_found")
    return p


@router.patch("/{pid}/privacy")
async def set_privacy_level(
    pid: str,
    body: PrivacyUpdateBody,
    user: dict = Depends(require_roles("agent", "agency_admin", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    p = await _get_owned(db, pid, aid)
    old_level = p.get("privacy_level") or "L2"
    if old_level == body.privacy_level:
        return {"id": pid, "privacy_level": old_level, "unchanged": True}
    await db.properties.update_one(
        {"id": pid},
        {"$set": {"privacy_level": body.privacy_level}},
    )
    await log_privacy_change(
        db, pid, actor_id=user["id"], agency_id=aid,
        old_level=old_level, new_level=body.privacy_level, reason=body.reason,
    )
    return {"id": pid, "privacy_level": body.privacy_level, "previous": old_level}


@router.get("/{pid}/privacy")
async def get_privacy_status(
    pid: str,
    user: dict = Depends(require_roles("agent", "agency_admin", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    p = await _get_owned(db, pid, aid)
    audit = await db.privacy_audit_events.find(
        {"property_id": pid}, {"_id": 0}
    ).sort("created_at", -1).limit(20).to_list(20)
    return {
        "id": pid,
        "privacy_level": p.get("privacy_level") or "L2",
        "audit_events": audit,
    }


@router.get("/{pid}/privacy/preview")
async def preview_privacy_view(
    pid: str,
    viewer: Level = "L2",
    user: dict = Depends(require_roles("agent", "agency_admin", "super_admin")),
):
    """Return the property document AS SEEN by a viewer of the requested level.

    Useful for agents to preview what an anonymous visitor / logged-in B2C
    user / qualified lead actually see on the ImmobilCloud portal.
    """
    db = Database.get()
    aid = _agency_id(user)
    p = await _get_owned(db, pid, aid)
    view = apply_privacy_view(p, viewer)
    return {
        "viewer_level": viewer,
        "property_privacy": p.get("privacy_level") or "L2",
        "view": view,
    }
