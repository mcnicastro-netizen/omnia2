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
            # agency_id needed for privacy/viewer resolve; stripped before response (D01)
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

    from shared.db.public_visibility import AGENCY_PUBLIC_PROJ, public_agency_card
    from apps.immocloud.portal_common import _public_photo_url

    agency_raw = None
    if not is_private and p.get("agency_id"):
        agency_raw = await db.agencies.find_one(
            {"id": p["agency_id"], "is_active": True},
            AGENCY_PUBLIC_PROJ,
        )

    publisher = _public_publisher(
        is_private=is_private,
        contact_public=contact_public,
        owner_email=owner_email,
        agency=agency_raw,
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
    agency_pub = public_agency_card(agency_raw)
    enriched = {
        **p,
        "photos": [
            {
                "url": _public_photo_url(pid, i, surface="portal"),
                "is_cover": ph.get("is_cover", False),
                "caption": ph.get("caption"),
                # P-043 — disclosure staging / render AI sulla scheda pubblica
                "is_virtual_staging": bool(ph.get("is_virtual_staging")),
            }
            for i, ph in enumerate(photos)
        ],
        "agency": agency_pub,
        "is_private_listing": is_private,
    }
    viewed = apply_privacy_view(enriched, viewer_level)
    viewed.pop("contact_public", None)
    viewed.pop("owner", None)
    viewed.pop("owner_user_id", None)
    viewed.pop("agency_id", None)  # D01
    # Internal moderation / safety never on public detail
    viewed.pop("safety_gate", None)
    viewed.pop("moderation_reviewed_by", None)
    viewed.pop("moderation_notes", None)
    return {
        **viewed,
        "agency": agency_pub,  # re-assert after privacy_view
        "publisher": publisher,
        "_viewer_level": viewer_level,  # useful for frontend badge
        "viewer_is_lister": viewer_is_lister,
    }


# ============================================================
# 4) Agency public card
# ============================================================

@router.get("/agency/{slug}")
async def public_agency_card(slug: str):
    from shared.db.public_visibility import (
        AGENCY_PUBLIC_PROJ,
        public_agency_card as agency_public_payload,
    )

    db = Database.get()
    # Need id only for count query — never returned (D01)
    a = await db.agencies.find_one(
        {"slug": slug, "is_active": True},
        {**AGENCY_PUBLIC_PROJ, "id": 1},
    )
    if not a:
        raise HTTPException(status_code=404, detail="agency_not_found")
    agency_id = a.get("id")
    count = await db.properties.count_documents({
        "agency_id": agency_id, **_base_filter(),
    })
    out = agency_public_payload(a) or {}
    out["public_property_count"] = count
    return out


# ============================================================
# 5) Contact form — generates a Lead in the agency CRM (M3.S4)
# ============================================================

