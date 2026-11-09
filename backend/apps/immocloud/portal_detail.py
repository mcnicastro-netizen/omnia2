"""OMNIA ImmobilCloud — property detail + agency card (MOVE-ONLY)."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request

from shared.auth.dependencies import get_current_user_optional
from shared.db.connection import Database
from shared.utils.privacy_gate import (
    apply_privacy_view,
    can_view_property,
    resolve_viewer_level,
)
from apps.immocloud.portal_common import (
    _base_filter,
    _public_publisher,
    _viewer_is_lister,
)

router = APIRouter(tags=["immobilcloud"])

@router.get("/property/{pid}")
async def public_property_detail(pid: str, request: Request):
    db = Database.get()
    # Need owner_user_id / contact for publisher — fetch then strip
    p = await db.properties.find_one(
        {"id": pid, **_base_filter()},
        {
            "_id": 0,
            "seller_client_id": 0,
            "commission_pct": 0,
            "listing_agent_id": 0,
            "lead_count": 0,
            "view_count": 0,
        },
    )
    if not p:
        raise HTTPException(status_code=404, detail="property_not_found")

    # M3.S9 Privacy Gate — determine viewer level
    user = await get_current_user_optional(request)
    # Qualified viewer: authenticated + has a confirmed lead on this property
    qualified = False
    if user and user.get("id"):
        qualified_lead = await db.leads.find_one({
            "property_id": pid,
            "user_id": user["id"],
            "gdpr_consent": True,
        })
        qualified = bool(qualified_lead)
    viewer_level = resolve_viewer_level(user, p.get("agency_id"), qualified=qualified)
    property_privacy = p.get("privacy_level") or "L2"
    if not can_view_property(viewer_level, property_privacy):
        raise HTTPException(status_code=404, detail="property_not_found")

    viewer_is_lister = _viewer_is_lister(user, p)

    is_private = bool(p.get("is_private_listing")) or p.get("agency_id") == "_private_listings"
    owner_doc = p.pop("owner", None) or {}
    contact_public = p.pop("contact_public", None) or {}
    owner_email = owner_doc.get("email")
    if is_private and not owner_email and p.get("owner_user_id"):
        u = await db.users.find_one(
            {"id": p["owner_user_id"]},
            {"_id": 0, "email": 1},
        )
        owner_email = (u or {}).get("email")

    agency = None
    if not is_private and p.get("agency_id"):
        agency = await db.agencies.find_one(
            {"id": p["agency_id"], "is_active": True},
            {"_id": 0, "id": 1, "slug": 1, "display_name": 1, "logo_url": 1,
             "phone": 1, "email": 1, "city": 1},
        )

    publisher = _public_publisher(
        is_private=is_private,
        contact_public=contact_public,
        owner_email=owner_email,
        agency=agency,
    )

    # Bump view counter + daily bucket (best-effort) — D-093 / A-029
    try:
        await db.properties.update_one({"id": pid}, {"$inc": {"view_count": 1}})
        from apps.immocloud.listing_stats import bump_daily_stat
        await bump_daily_stat(db, pid, "view")
    except Exception:
        pass

    photos = p.get("photos") or []
    # Strip sensitive ownership fields before public response
    p.pop("owner_user_id", None)
    enriched = {
        **p,
        "photos": [
            {
                "url": f"/api/public/property/{pid}/photo/{i}",
                "is_cover": ph.get("is_cover", False),
                "caption": ph.get("caption"),
                # P-043 — disclosure staging / render AI sulla scheda pubblica
                "is_virtual_staging": bool(ph.get("is_virtual_staging")),
            }
            for i, ph in enumerate(photos)
        ],
        "agency": agency,
        "is_private_listing": is_private,
    }
    viewed = apply_privacy_view(enriched, viewer_level)
    viewed.pop("contact_public", None)
    viewed.pop("owner", None)
    viewed.pop("owner_user_id", None)
    # Internal moderation / safety never on public detail
    viewed.pop("safety_gate", None)
    viewed.pop("moderation_reviewed_by", None)
    viewed.pop("moderation_notes", None)
    return {
        **viewed,
        "publisher": publisher,
        "_viewer_level": viewer_level,  # useful for frontend badge
        "viewer_is_lister": viewer_is_lister,
    }


# ============================================================
# 4) Agency public card
# ============================================================

@router.get("/agency/{slug}")
async def public_agency_card(slug: str):
    db = Database.get()
    a = await db.agencies.find_one(
        {"slug": slug, "is_active": True},
        {"_id": 0, "id": 1, "slug": 1, "display_name": 1, "logo_url": 1,
         "phone": 1, "email": 1, "city": 1, "address": 1, "description": 1},
    )
    if not a:
        raise HTTPException(status_code=404, detail="agency_not_found")
    # Count of public properties of this agency
    count = await db.properties.count_documents({
        "agency_id": a["id"], **_base_filter(),
    })
    return {**a, "public_property_count": count}


# ============================================================
# 5) Contact form — generates a Lead in the agency CRM (M3.S4)
# ============================================================

