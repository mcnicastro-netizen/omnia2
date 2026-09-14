"""OMNIA — ImmobilCloud B2C Public Portal (M3.S1).

Aggregates all `status=active` + `visibility=public` + `is_listed_on_immobilcloud=true`
properties from ALL OMNIA agencies and exposes them through public, NO-AUTH endpoints.

Mounted at `/api/cloud/*`. Hostname `cloud.omniarealestateecosystem.it` will be
routed here by the platform reverse proxy + a public React app served on the
same domain consuming these endpoints.

Endpoints (PUBLIC, NO AUTH):
  GET  /search       — filtered+paginated property list
  GET  /facets       — counters for the filter UI (cities/types/operations)
  GET  /property/{id} — single property detail
  GET  /property/{id}/agency — public agency card (display_name, slug, city)

Photos are served by the existing endpoint /api/public/property/{pid}/photo/{idx}.
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, EmailStr, Field

from shared.db.connection import Database
from shared.utils.privacy_gate import (
    apply_privacy_view,
    can_view_property,
    resolve_viewer_level,
)
from shared.auth.dependencies import get_current_user_optional

logger = logging.getLogger("omnia.immobilcloud")
router = APIRouter(tags=["immobilcloud"])


# ============================================================
# Helpers
# ============================================================

PUBLIC_FIELDS = {
    "_id": 0,
    "owner": 0,                # internal-only
    "seller_client_id": 0,     # internal-only
    "commission_pct": 0,
    "listing_agent_id": 0,
    "lead_count": 0,
    "view_count": 0,
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
}


def _base_filter() -> Dict[str, Any]:
    """Common visibility filter applied to every public query."""
    return {
        "status": "active",
        "visibility": "public",
        "is_listed_on_immobilcloud": {"$ne": False},
        "moderation_status": {"$nin": ["pending", "rejected"]},
    }


def _cover_photo(photos: Optional[List[dict]]) -> Optional[str]:
    if not photos:
        return None
    idx = next((i for i, p in enumerate(photos) if p.get("is_cover")), 0)
    return f"/api/public/property/{photos[idx].get('property_id') or ''}/photo/{idx}".replace("//photo/", "/photo/")


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
        "agency": {
            "id": agency.get("id") if agency else None,
            "name": agency.get("display_name") if agency else None,
            "slug": agency.get("slug") if agency else None,
        } if agency else None,
    }


# ============================================================
# 1) Search — main list endpoint
# ============================================================

@router.get("/search")
async def public_search(
    q: Optional[str] = None,
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    operation: Optional[str] = Query(None, pattern="^(sale|rent)$"),
    price_min: Optional[int] = Query(None, ge=0),
    price_max: Optional[int] = Query(None, ge=0),
    surface_min: Optional[int] = Query(None, ge=0),
    surface_max: Optional[int] = Query(None, ge=0),
    rooms_min: Optional[int] = Query(None, ge=0),
    bedrooms_min: Optional[int] = Query(None, ge=0),
    bathrooms_min: Optional[int] = Query(None, ge=0),
    energy_class: Optional[str] = Query(None, pattern="^(A4|A3|A2|A1|A|B|C|D|E|F|G)$"),
    sort: str = Query("recent", pattern="^(recent|price_asc|price_desc|surface_desc)$"),
    page: int = Query(1, ge=1, le=500),
    page_size: int = Query(20, ge=1, le=60),
):
    """Public paginated listing filtered by common B2C criteria."""
    db = Database.get()
    flt: Dict[str, Any] = _base_filter()

    if city:
        flt["city"] = {"$regex": f"^{city}", "$options": "i"}
    if property_type:
        flt["property_type"] = property_type
    if operation:
        flt["operation"] = operation
    if rooms_min:
        flt["rooms"] = {"$gte": rooms_min}
    if bedrooms_min:
        flt["bedrooms"] = {"$gte": bedrooms_min}
    if bathrooms_min:
        flt["bathrooms"] = {"$gte": bathrooms_min}
    if energy_class:
        flt["energy.energy_class"] = energy_class
    if surface_min or surface_max:
        rng = {}
        if surface_min:
            rng["$gte"] = surface_min
        if surface_max:
            rng["$lte"] = surface_max
        flt["surface_sqm"] = rng
    if price_min or price_max:
        rng = {}
        if price_min:
            rng["$gte"] = price_min
        if price_max:
            rng["$lte"] = price_max
        # price for sale; rent_monthly for rent
        if operation == "rent":
            flt["rent_monthly"] = rng
        else:
            flt["price"] = rng
    if q:
        flt["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"city": {"$regex": q, "$options": "i"}},
            {"zone": {"$regex": q, "$options": "i"}},
        ]

    # Sort
    sort_map = {
        "recent": [("updated_at", -1)],
        "price_asc": [("price", 1), ("rent_monthly", 1)],
        "price_desc": [("price", -1), ("rent_monthly", -1)],
        "surface_desc": [("surface_sqm", -1)],
    }
    sort_spec = sort_map[sort]

    total = await db.properties.count_documents(flt)
    skip = (page - 1) * page_size
    cursor = db.properties.find(flt, LIST_FIELDS).sort(sort_spec).skip(skip).limit(page_size)
    props = await cursor.to_list(length=page_size)

    # Batch-resolve agencies
    agency_ids = list({p.get("agency_id") for p in props if p.get("agency_id")})
    agencies: Dict[str, Dict[str, Any]] = {}
    if agency_ids:
        async for a in db.agencies.find(
            {"id": {"$in": agency_ids}, "is_active": True},
            {"_id": 0, "id": 1, "slug": 1, "display_name": 1},
        ):
            agencies[a["id"]] = a

    return {
        "items": [_to_card(p, agencies.get(p.get("agency_id"))) for p in props],
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": skip + page_size < total,
        "sort": sort,
    }


# ============================================================
# 1.5) M3.S8 Advanced search (multi-zone, polygon draw, near-me, price compare)
# ============================================================


class AdvancedSearchBody(BaseModel):
    q: Optional[str] = None
    cities: Optional[List[str]] = Field(default=None, max_length=20)
    property_types: Optional[List[str]] = Field(default=None, max_length=20)
    operation: Optional[str] = Field(default=None, pattern="^(sale|rent)$")
    price_min: Optional[float] = Field(default=None, ge=0)
    price_max: Optional[float] = Field(default=None, ge=0)
    surface_min: Optional[float] = Field(default=None, ge=0)
    surface_max: Optional[float] = Field(default=None, ge=0)
    rooms_min: Optional[int] = Field(default=None, ge=0)
    bedrooms_min: Optional[int] = Field(default=None, ge=0)
    energy_class: Optional[str] = Field(default=None, pattern="^(A4|A3|A2|A1|A|B|C|D|E|F|G)$")
    polygon: Optional[List[List[float]]] = Field(default=None, max_length=100)
    near_me: Optional[Dict[str, float]] = None
    compare_prices: bool = False
    sort: str = Field(default="recent", pattern="^(recent|price_asc|price_desc|surface_desc|distance_asc)$")
    page: int = Field(default=1, ge=1, le=500)
    page_size: int = Field(default=20, ge=1, le=60)


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


@router.post("/search/advanced")
async def public_search_advanced(body: AdvancedSearchBody):
    """M3.S8 — Advanced search: multi-city, draw-on-map polygon, near-me
    haversine radius, cross-zone price comparison."""
    db = Database.get()
    flt: Dict[str, Any] = _base_filter()

    if body.cities:
        flt["city"] = {"$in": body.cities}
    if body.property_types:
        flt["property_type"] = {"$in": body.property_types}
    if body.operation:
        flt["operation"] = body.operation
    if body.rooms_min:
        flt["rooms"] = {"$gte": body.rooms_min}
    if body.bedrooms_min:
        flt["bedrooms"] = {"$gte": body.bedrooms_min}
    if body.energy_class:
        flt["energy.energy_class"] = body.energy_class
    if body.surface_min or body.surface_max:
        rng: Dict[str, Any] = {}
        if body.surface_min: rng["$gte"] = body.surface_min
        if body.surface_max: rng["$lte"] = body.surface_max
        flt["surface_sqm"] = rng
    if body.price_min or body.price_max:
        rng = {}
        if body.price_min: rng["$gte"] = body.price_min
        if body.price_max: rng["$lte"] = body.price_max
        if body.operation == "rent":
            flt["rent_monthly"] = rng
        else:
            flt["price"] = rng
    if body.q:
        flt["$or"] = [
            {"title": {"$regex": body.q, "$options": "i"}},
            {"description": {"$regex": body.q, "$options": "i"}},
            {"zone": {"$regex": body.q, "$options": "i"}},
        ]

    # Near-me bbox pre-filter
    if body.near_me:
        lat = body.near_me.get("lat")
        lng = body.near_me.get("lng")
        radius_km = body.near_me.get("radius_km", 5)
        if lat is None or lng is None:
            raise HTTPException(status_code=422, detail="near_me_requires_lat_lng")
        from math import cos, radians
        dlat = radius_km / 111.0
        dlng = radius_km / (111.0 * max(0.01, cos(radians(lat))))
        flt["lat"] = {"$gte": lat - dlat, "$lte": lat + dlat}
        flt["lng"] = {"$gte": lng - dlng, "$lte": lng + dlng}

    # Polygon bbox pre-filter
    if body.polygon and len(body.polygon) >= 3:
        lats = [p[0] for p in body.polygon]
        lngs = [p[1] for p in body.polygon]
        flt["lat"] = {"$gte": min(lats), "$lte": max(lats)}
        flt["lng"] = {"$gte": min(lngs), "$lte": max(lngs)}

    sort_map = {
        "recent": [("updated_at", -1)],
        "price_asc": [("price", 1), ("rent_monthly", 1)],
        "price_desc": [("price", -1), ("rent_monthly", -1)],
        "surface_desc": [("surface_sqm", -1)],
        "distance_asc": [("updated_at", -1)],
    }
    sort_spec = sort_map[body.sort]

    fetch_limit = body.page_size * body.page + 200 if (body.polygon or body.near_me) else body.page_size
    cursor = db.properties.find(flt, LIST_FIELDS).sort(sort_spec).limit(fetch_limit)
    docs = await cursor.to_list(length=fetch_limit)

    if body.polygon and len(body.polygon) >= 3:
        docs = [d for d in docs if d.get("lat") is not None and d.get("lng") is not None
                and _point_in_polygon(d["lat"], d["lng"], body.polygon)]

    if body.near_me:
        lat = body.near_me["lat"]; lng = body.near_me["lng"]
        radius_km = body.near_me.get("radius_km", 5)
        annotated = []
        for d in docs:
            if d.get("lat") is None or d.get("lng") is None:
                continue
            dist = _haversine_km(lat, lng, d["lat"], d["lng"])
            if dist <= radius_km:
                d["_distance_km"] = round(dist, 2)
                annotated.append(d)
        docs = annotated
        if body.sort == "distance_asc":
            docs.sort(key=lambda x: x["_distance_km"])

    total = len(docs)
    skip = (body.page - 1) * body.page_size
    page_docs = docs[skip: skip + body.page_size]

    agency_ids = list({p.get("agency_id") for p in page_docs if p.get("agency_id")})
    agencies: Dict[str, Dict[str, Any]] = {}
    if agency_ids:
        async for a in db.agencies.find(
            {"id": {"$in": agency_ids}, "is_active": True},
            {"_id": 0, "id": 1, "slug": 1, "display_name": 1},
        ):
            agencies[a["id"]] = a

    price_stats = None
    if body.compare_prices and docs:
        prices = [d.get("price") for d in docs if d.get("price")]
        rents = [d.get("rent_monthly") for d in docs if d.get("rent_monthly")]
        if prices:
            ps = sorted(prices)
            price_stats = {"type": "sale", "count": len(ps), "avg": round(sum(ps)/len(ps)),
                           "median": ps[len(ps)//2], "min": min(ps), "max": max(ps)}
        elif rents:
            rs = sorted(rents)
            price_stats = {"type": "rent", "count": len(rs), "avg": round(sum(rs)/len(rs)),
                           "median": rs[len(rs)//2], "min": min(rs), "max": max(rs)}

    return {
        "items": [_to_card(p, agencies.get(p.get("agency_id"))) for p in page_docs],
        "total": total,
        "page": body.page,
        "page_size": body.page_size,
        "has_next": (skip + body.page_size) < total,
        "sort": body.sort,
        "price_stats": price_stats,
        "filters_applied": {
            "cities": body.cities or [],
            "polygon_points": len(body.polygon) if body.polygon else 0,
            "near_me": body.near_me or None,
            "compare_prices": body.compare_prices,
        },
    }


# ============================================================
# 2) Facets — counters for filter UI
# ============================================================

@router.get("/map")
async def public_map_markers(
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    operation: Optional[str] = Query(None, pattern="^(sale|rent)$"),
    price_min: Optional[int] = Query(None, ge=0),
    price_max: Optional[int] = Query(None, ge=0),
    rooms_min: Optional[int] = Query(None, ge=0),
    bedrooms_min: Optional[int] = Query(None, ge=0),
    energy_class: Optional[str] = Query(None, pattern="^(A4|A3|A2|A1|A|B|C|D|E|F|G)$"),
    bbox: Optional[str] = Query(None, description="south,west,north,east"),
    limit: int = Query(500, ge=1, le=2000),
):
    """M3.S3 — Lightweight markers for map view. Returns only id/lat/lng/price/type
    of properties with coordinates. Optional bbox filter (south,west,north,east).
    """
    db = Database.get()
    flt: Dict[str, Any] = _base_filter()
    # Required: must have coordinates
    flt["lat"] = {"$ne": None, "$exists": True}
    flt["lng"] = {"$ne": None, "$exists": True}

    if city:
        flt["city"] = {"$regex": f"^{city}", "$options": "i"}
    if property_type:
        flt["property_type"] = property_type
    if operation:
        flt["operation"] = operation
    if rooms_min:
        flt["rooms"] = {"$gte": rooms_min}
    if bedrooms_min:
        flt["bedrooms"] = {"$gte": bedrooms_min}
    if energy_class:
        flt["energy.energy_class"] = energy_class
    if price_min or price_max:
        rng = {}
        if price_min:
            rng["$gte"] = price_min
        if price_max:
            rng["$lte"] = price_max
        if operation == "rent":
            flt["rent_monthly"] = rng
        else:
            flt["price"] = rng

    # Bounding box filter (south, west, north, east)
    if bbox:
        try:
            south, west, north, east = (float(x) for x in bbox.split(","))
            flt["lat"] = {"$gte": south, "$lte": north}
            flt["lng"] = {"$gte": west, "$lte": east}
        except (ValueError, AttributeError):
            raise HTTPException(status_code=400, detail="invalid_bbox_format")

    cursor = db.properties.find(
        flt,
        {"_id": 0, "id": 1, "lat": 1, "lng": 1, "price": 1, "rent_monthly": 1,
         "property_type": 1, "operation": 1, "city": 1, "title": 1},
    ).limit(limit)
    items = await cursor.to_list(length=limit)
    return {"items": items, "count": len(items)}


@router.get("/facets")
async def public_facets(
    operation: Optional[str] = Query(None, pattern="^(sale|rent)$"),
):
    """Returns top cities & property types with counts (for hero search box)."""
    db = Database.get()
    flt = _base_filter()
    if operation:
        flt["operation"] = operation

    # Top 20 cities
    cities_cur = db.properties.aggregate([
        {"$match": flt},
        {"$group": {"_id": "$city", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20},
    ])
    cities = [{"city": d["_id"], "count": d["count"]} async for d in cities_cur if d["_id"]]

    types_cur = db.properties.aggregate([
        {"$match": flt},
        {"$group": {"_id": "$property_type", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ])
    types = [{"type": d["_id"], "count": d["count"]} async for d in types_cur if d["_id"]]

    total = await db.properties.count_documents(flt)

    return {
        "total_active": total,
        "cities": cities,
        "property_types": types,
    }


# ============================================================
# 3) Detail — single property
# ============================================================

@router.get("/property/{pid}")
@router.get("/property/{pid}")
async def public_property_detail(pid: str, request: Request):
    db = Database.get()
    p = await db.properties.find_one(
        {"id": pid, **_base_filter()},
        PUBLIC_FIELDS,
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

    agency = None
    if p.get("agency_id"):
        agency = await db.agencies.find_one(
            {"id": p["agency_id"], "is_active": True},
            {"_id": 0, "id": 1, "slug": 1, "display_name": 1, "logo_url": 1,
             "phone": 1, "email": 1, "city": 1},
        )

    # Bump view counter (best-effort)
    try:
        await db.properties.update_one({"id": pid}, {"$inc": {"view_count": 1}})
    except Exception:
        pass

    photos = p.get("photos") or []
    # Build the enriched dict then apply the privacy gate
    enriched = {
        **p,
        "photos": [
            {
                "url": f"/api/public/property/{pid}/photo/{i}",
                "is_cover": ph.get("is_cover", False),
                "caption": ph.get("caption"),
            }
            for i, ph in enumerate(photos)
        ],
        "agency": agency,
    }
    return {
        **apply_privacy_view(enriched, viewer_level),
        "_viewer_level": viewer_level,  # useful for frontend badge
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

class PropertyContactPayload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    surname: Optional[str] = Field(default=None, max_length=200)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    message: str = Field(min_length=10, max_length=2000)
    gdpr_consent: bool = False
    visit_requested: bool = False  # optional checkbox "richiedi visita"


@router.post("/property/{pid}/contact")
async def public_property_contact(pid: str, payload: PropertyContactPayload):
    """B2C contact form. Creates (or reuses) a client in the agency CRM and
    a Lead linking it to this property. Source = 'ImmobilCloud'.
    """
    if not payload.gdpr_consent:
        raise HTTPException(status_code=400, detail="gdpr_consent_required")

    db = Database.get()
    prop = await db.properties.find_one(
        {"id": pid, **_base_filter()},
        {"_id": 0, "id": 1, "agency_id": 1, "title": 1},
    )
    if not prop:
        raise HTTPException(status_code=404, detail="property_not_found")

    agency_id = prop.get("agency_id")
    if not agency_id:
        raise HTTPException(status_code=409, detail="property_has_no_agency")

    now = datetime.now(timezone.utc).isoformat()

    # 1) Find or create client
    existing = await db.clients.find_one(
        {"agency_id": agency_id, "email": payload.email.lower()},
        {"_id": 0, "id": 1},
    )
    if existing:
        client_id = existing["id"]
        # Refresh updated_at + last source if reused
        await db.clients.update_one(
            {"id": client_id},
            {"$set": {"updated_at": now}, "$setOnInsert": {}},
        )
    else:
        client_id = str(uuid4())
        await db.clients.insert_one({
            "id": client_id,
            "agency_id": agency_id,
            "name": payload.name,
            "surname": payload.surname,
            "email": payload.email.lower(),
            "phone": payload.phone,
            "whatsapp": None,
            "fiscal_code": None,
            "client_type": "buyer",
            "status": "new",
            "source": "ImmobilCloud",
            "assigned_agent_id": None,
            "preferences": {},
            "notes": None,
            "gdpr_consent": True,
            "created_at": now,
            "updated_at": now,
        })

    # 2) Fetch listing agent OR fallback to agency email
    prop_full = await db.properties.find_one(
        {"id": pid},
        {"_id": 0, "listing_agent_id": 1},
    )
    notify_email = None
    notify_lang = "it"
    if prop_full and prop_full.get("listing_agent_id"):
        agent = await db.users.find_one(
            {"id": prop_full["listing_agent_id"]},
            {"_id": 0, "email": 1, "lang": 1},
        )
        if agent and agent.get("email"):
            notify_email = agent["email"]
            notify_lang = agent.get("lang") or "it"
    if not notify_email:
        agency_doc = await db.agencies.find_one(
            {"id": agency_id},
            {"_id": 0, "email": 1, "lang": 1},
        )
        if agency_doc and agency_doc.get("email"):
            notify_email = agency_doc["email"]
            notify_lang = agency_doc.get("lang") or "it"

    # 3) Create lead
    lead_id = str(uuid4())
    note_lines = [payload.message.strip()]
    if payload.visit_requested:
        note_lines.append("[richiesta visita immobile]")
    await db.leads.insert_one({
        "id": lead_id,
        "agency_id": agency_id,
        "client_id": client_id,
        "property_id": pid,
        "status": "new",
        "score": None,
        "notes": "\n".join(note_lines),
        "assigned_agent_id": None,
        "source": "ImmobilCloud",
        "created_at": now,
        "updated_at": now,
    })

    # 4) Bump property lead counter (best-effort)
    try:
        await db.properties.update_one({"id": pid}, {"$inc": {"lead_count": 1}})
    except Exception:
        pass

    # 5) Fire-and-forget email notification to agent (M3.S4.1)
    if notify_email:
        _schedule_lead_email(
            to=notify_email,
            lang=notify_lang,
            property_title=prop.get("title") or "Immobile",
            lead_name=f"{payload.name} {payload.surname or ''}".strip(),
            lead_email=payload.email,
            lead_phone=payload.phone,
            lead_message="\n".join(note_lines),
            agency_id=agency_id,
            property_id=pid,
        )

    logger.info("B2C contact: lead=%s client=%s property=%s agency=%s notify=%s",
                lead_id, client_id, pid, agency_id, notify_email or "—")
    return {"ok": True, "lead_id": lead_id, "client_id": client_id}


def _schedule_lead_email(*, to: str, lang: str, property_title: str,
                        lead_name: str, lead_email: str,
                        lead_phone: Optional[str], lead_message: str,
                        agency_id: str, property_id: str) -> None:
    """Fire-and-forget Resend notification to listing agent / agency."""
    import asyncio
    import os
    from shared.email.client import send_email

    base = os.environ.get("FRONTEND_BASE_URL", "https://omniarealestateecosystem.it")
    crm_url = f"{base}/{lang if lang in ('it', 'en', 'es') else 'it'}/app/properties/{property_id}"
    phone_block = (
        f'<p style="margin:4px 0 0 0; font-size:14px; color:#0E1419;">📞 '
        f'<a href="tel:{lead_phone}" style="color:#0B1E3F;">{lead_phone}</a></p>'
        if lead_phone else ""
    )

    async def _task():
        # Retry with exponential back-off (1s, 3s, 10s). Log final failure.
        delays = [0, 1, 3, 10]
        last_exc: Optional[Exception] = None
        for attempt, delay in enumerate(delays, start=1):
            if delay:
                await asyncio.sleep(delay)
            try:
                await send_email(
                    to=to,
                    template="lead_notification",
                    lang=lang,
                    variables={
                        "property_title": property_title,
                        "lead_name": lead_name,
                        "lead_email": lead_email,
                        "lead_phone_block": phone_block,
                        "lead_message": lead_message,
                        "crm_url": crm_url,
                    },
                )
                if attempt > 1:
                    logger.info("lead email delivered on attempt %d to=%s", attempt, to)
                return
            except Exception as e:  # noqa: BLE001
                last_exc = e
                logger.warning("lead email attempt %d/%d failed: %s", attempt, len(delays), e)
        # All retries exhausted → durable log for manual replay
        logger.error("lead email PERMANENTLY FAILED to=%s agency=%s property=%s: %s",
                     to, agency_id, property_id, last_exc)

    try:
        asyncio.create_task(_task())
    except RuntimeError:
        pass
