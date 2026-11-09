"""OMNIA ImmobilCloud — public search / map / facets (MOVE-ONLY)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from shared.db.connection import Database
from apps.immocloud.portal_common import (
    LIST_FIELDS,
    _active_boost_tier,
    _base_filter,
    _haversine_km,
    _point_in_polygon,
    _to_card,
)

router = APIRouter(tags=["immobilcloud"])

@router.get("/search")
async def public_search(
    request: Request,
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
    energy_class: Optional[str] = Query(None, pattern="^(A4|A3|A2|A1|A\+|A|B|C|D|E|F|G)$"),
    bbox: Optional[str] = Query(None, description="south,west,north,east — Idealista-like map area"),
    sort: str = Query("recent", pattern="^(recent|price_asc|price_desc|surface_desc)$"),
    page: int = Query(1, ge=1, le=500),
    page_size: int = Query(20, ge=1, le=60),
):
    """Public paginated listing filtered by common B2C criteria."""
    from shared.security.rate_limit import enforce_ip_rate_limit
    await enforce_ip_rate_limit(request, bucket="cloud_search", max_requests=120, window_seconds=3600)
    db = Database.get()
    flt: Dict[str, Any] = _base_filter()

    # Area mappa: bbox ha priorità sulla città (flusso Idealista «cerca in questa zona»).
    if bbox:
        try:
            south, west, north, east = (float(x) for x in bbox.split(","))
            flt["lat"] = {"$gte": south, "$lte": north, "$ne": None, "$exists": True}
            flt["lng"] = {"$gte": west, "$lte": east, "$ne": None, "$exists": True}
        except (ValueError, AttributeError):
            raise HTTPException(status_code=400, detail="invalid_bbox_format")
    elif city:
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

    # D-127 — boost su tutti i sort + rotazione + cap densità per pagina
    # (con filtro city i pool sono scoped → densità locale città)
    from apps.billing.boost_ranking import (
        fetch_search_page_with_density_cap,
        schedule_boost_impressions,
    )

    total = await db.properties.count_documents(flt)
    skip = (page - 1) * page_size
    props, density = await fetch_search_page_with_density_cap(
        db,
        flt,
        sort=sort,
        page=page,
        page_size=page_size,
        project_fields=LIST_FIELDS,
    )

    # Impressioni boost (async): alimenta la rotazione equa
    schedule_boost_impressions([p.get("id") for p in props if _active_boost_tier(p)])

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
        "boost_density": density,
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
    energy_class: Optional[str] = Field(default=None, pattern="^(A4|A3|A2|A1|A\+|A|B|C|D|E|F|G)$")
    polygon: Optional[List[List[float]]] = Field(default=None, max_length=100)
    near_me: Optional[Dict[str, float]] = None
    compare_prices: bool = False
    sort: str = Field(default="recent", pattern="^(recent|price_asc|price_desc|surface_desc|distance_asc)$")
    page: int = Field(default=1, ge=1, le=500)
    page_size: int = Field(default=20, ge=1, le=60)


@router.post("/search/advanced")
async def public_search_advanced(body: AdvancedSearchBody, request: Request):
    """M3.S8 — Advanced search: multi-city, draw-on-map polygon, near-me
    haversine radius, cross-zone price comparison."""
    from shared.security.rate_limit import enforce_ip_rate_limit
    await enforce_ip_rate_limit(request, bucket="cloud_search_advanced", max_requests=60, window_seconds=3600)
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
    request: Request,
    city: Optional[str] = None,
    property_type: Optional[str] = None,
    operation: Optional[str] = Query(None, pattern="^(sale|rent)$"),
    price_min: Optional[int] = Query(None, ge=0),
    price_max: Optional[int] = Query(None, ge=0),
    rooms_min: Optional[int] = Query(None, ge=0),
    bedrooms_min: Optional[int] = Query(None, ge=0),
    energy_class: Optional[str] = Query(None, pattern="^(A4|A3|A2|A1|A\+|A|B|C|D|E|F|G)$"),
    bbox: Optional[str] = Query(None, description="south,west,north,east"),
    limit: int = Query(500, ge=1, le=2000),
):
    """M3.S3 — Lightweight markers for map view. Returns only id/lat/lng/price/type
    of properties with coordinates. Optional bbox filter (south,west,north,east).
    """
    from shared.security.rate_limit import enforce_ip_rate_limit
    await enforce_ip_rate_limit(request, bucket="cloud_map", max_requests=120, window_seconds=3600)
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


