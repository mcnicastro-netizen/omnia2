"""OMNIA ImmobilCloud — portal shared helpers (MOVE-ONLY from public_portal)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("omnia.immobilcloud")

PUBLIC_FIELDS = {
    "_id": 0,
    "owner": 0,                # internal-only
    "owner_user_id": 0,        # never expose; use viewer_is_lister instead
    "seller_client_id": 0,     # internal-only
    "commission_pct": 0,
    "listing_agent_id": 0,
    "lead_count": 0,
    "view_count": 0,
    "contact_public": 0,       # never raw; exposed via publisher.channels
}


def _digits_phone(raw: Optional[str]) -> str:
    if not raw:
        return ""
    return "".join(ch for ch in str(raw) if ch.isdigit() or ch == "+")


def _public_publisher(
    *,
    is_private: bool,
    contact_public: Optional[Dict[str, Any]],
    owner_email: Optional[str],
    agency: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Safe publisher card for the detail sidebar (agency vs private seller)."""
    if is_private:
        cp = contact_public or {}
        channels: Dict[str, Optional[str]] = {
            "email": None,
            "phone": None,
            "whatsapp": None,
        }
        if cp.get("show_email") and owner_email:
            channels["email"] = owner_email
        phone = (cp.get("phone") or "").strip() or None
        wa = (cp.get("whatsapp") or "").strip() or None
        if cp.get("show_phone") and phone:
            channels["phone"] = phone
        if cp.get("show_whatsapp") and wa:
            channels["whatsapp"] = wa
        return {
            "kind": "private",
            "display_name": (cp.get("display_name") or "Privato").strip() or "Privato",
            "channels": channels,
            # Form always allowed when we can notify the account email
            "accepts_messages": bool(owner_email),
        }
    return {
        "kind": "agency",
        "display_name": (agency or {}).get("display_name"),
        "channels": {
            "email": (agency or {}).get("email"),
            "phone": (agency or {}).get("phone"),
            "whatsapp": None,
        },
        "accepts_messages": True,
    }

LIST_FIELDS = {
    "_id": 0,
    "id": 1, "agency_id": 1, "title": 1, "description": 1,
    "property_type": 1, "operation": 1, "status": 1,
    "city": 1, "zone": 1, "address": 1,
    "lat": 1, "lng": 1,
    "price": 1, "rent_monthly": 1,
    "surface_sqm": 1, "rooms": 1, "bedrooms": 1, "bathrooms": 1,
    "floor": 1, "energy": 1,
    "photos": 1, "features": 1,
    "updated_at": 1, "created_at": 1,
    "reference_code": 1,
    "boost_tier": 1, "boost_rank": 1, "boost_until": 1,
    "boost_last_shown_at": 1, "boost_impression_count": 1,
    "floor_plan_url": 1, "address": 1,
}


def _base_filter() -> Dict[str, Any]:
    """S4 — stesso contratto pubblico del brand (surface base) + delta portale.

    Portale-only: is_listed_on_immobilcloud ≠ false · privacy ∉ L3/L4 (P-033).
    SoT: `shared.db.public_visibility`.
    """
    from shared.db.public_visibility import portal_listing_filter
    return portal_listing_filter()


def _cover_photo(photos: Optional[List[dict]]) -> Optional[str]:
    if not photos:
        return None
    idx = next((i for i, p in enumerate(photos) if p.get("is_cover")), 0)
    return f"/api/public/property/{photos[idx].get('property_id') or ''}/photo/{idx}".replace("//photo/", "/photo/")


def _active_boost_tier(p: Dict[str, Any]) -> Optional[str]:
    """Return boost_tier only while boost_until is in the future."""
    tier = p.get("boost_tier")
    until_raw = p.get("boost_until")
    if not tier or not until_raw:
        return None
    try:
        until = datetime.fromisoformat(str(until_raw).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    if until <= datetime.now(timezone.utc):
        return None
    return tier


def _to_card(p: Dict[str, Any], agency: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Public list card payload."""
    photos = p.get("photos") or []
    cover_idx = next((i for i, ph in enumerate(photos) if ph.get("is_cover")), 0 if photos else None)
    return {
        "id": p["id"],
        "title": p.get("title"),
        "property_type": p.get("property_type"),
        "operation": p.get("operation"),
        "city": p.get("city"),
        "zone": p.get("zone"),
        "lat": p.get("lat"),
        "lng": p.get("lng"),
        "price": p.get("price"),
        "rent_monthly": p.get("rent_monthly"),
        "surface_sqm": p.get("surface_sqm"),
        "rooms": p.get("rooms"),
        "bedrooms": p.get("bedrooms"),
        "bathrooms": p.get("bathrooms"),
        "energy_class": (p.get("energy") or {}).get("energy_class"),
        "cover_url": f"/api/public/property/{p['id']}/photo/{cover_idx}" if cover_idx is not None else None,
        "photo_count": len(photos),
        "reference_code": p.get("reference_code"),
        "updated_at": p.get("updated_at"),
        "boost_tier": _active_boost_tier(p),
        "scout_hint": _scout_hint(p),
        "agency": {
            "id": agency.get("id") if agency else None,
            "name": agency.get("display_name") if agency else None,
            "slug": agency.get("slug") if agency else None,
        } if agency else None,
    }


def _scout_hint(p: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Lightweight completeness for list cards (no LLM)."""
    try:
        from apps.immocloud.buyer_brief import completeness_score
        c = completeness_score(p)
        return {
            "score": c["score"],
            "grade": c["grade"],
            "grade_label_it": c.get("grade_label_it"),
        }
    except Exception:
        return None


# ============================================================
# 1) Search — main list endpoint
# ============================================================

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    from math import radians, sin, cos, asin, sqrt
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * R * asin(sqrt(a))


def _point_in_polygon(lat: float, lng: float, poly: List[List[float]]) -> bool:
    if not poly or len(poly) < 3:
        return False
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        yi, xi = poly[i][0], poly[i][1]
        yj, xj = poly[j][0], poly[j][1]
        if ((yi > lat) != (yj > lat)) and (lng < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def _viewer_is_lister(user: Optional[Dict[str, Any]], p: Dict[str, Any]) -> bool:
    """True when the authenticated viewer owns/lists this property (B2C owner or agency)."""
    if not user or not user.get("id"):
        return False
    uid = user["id"]
    if p.get("owner_user_id") and p["owner_user_id"] == uid:
        return True
    if p.get("is_private_listing") and p.get("owner_user_id") == uid:
        return True
    agency_id = p.get("agency_id")
    if not agency_id or agency_id == "_private_listings":
        return False
    agencies = set(user.get("agency_ids") or [])
    if user.get("agency_id"):
        agencies.add(user["agency_id"])
    return agency_id in agencies


# ============================================================
# 3) Detail — single property
# ============================================================

