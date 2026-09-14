"""OMNIA — Matching API endpoints (M2.S4 D-025).

Exposes Property↔Client match scoring across the agency.
Strategy: compute on read (no persisted matches collection for MVP).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database

from apps.immoweb.matching import compute_match, is_searcher
from apps.immoweb.lead_scoring import score_lead


router = APIRouter(prefix="/matches", tags=["matches"])


from shared.auth.tenant import arequire_agency as _agency


def _trim_client(c: dict) -> dict:
    return {
        "id": c["id"],
        "name": c.get("name"),
        "surname": c.get("surname"),
        "email": c.get("email"),
        "phone": c.get("phone"),
        "client_type": c.get("client_type"),
        "status": c.get("status"),
    }


def _trim_property(p: dict) -> dict:
    photos = p.get("photos") or []
    cover = next((x for x in photos if x.get("is_cover")), photos[0] if photos else None)
    return {
        "id": p["id"],
        "title": p.get("title"),
        "property_type": p.get("property_type"),
        "operation": p.get("operation"),
        "status": p.get("status"),
        "city": p.get("city"),
        "zone": p.get("zone"),
        "price": p.get("price"),
        "rent_monthly": p.get("rent_monthly"),
        "surface_sqm": p.get("surface_sqm"),
        "rooms": p.get("rooms"),
        "cover_photo_url": (cover or {}).get("url"),
    }


# -------------------- GET /matches --------------------

@router.get("")
async def list_all_matches(
    min_score: int = Query(50, ge=0, le=100),
    limit: int = Query(50, ge=1, le=200),
    user: dict = Depends(get_current_user),
):
    """Top matches across the agency, sorted by score desc."""
    agency_id = await _agency(user)
    db = Database.get()
    # Only active/published properties get matched (never drafts)
    props_cursor = db.properties.find(
        {"agency_id": agency_id, "status": "active"}, {"_id": 0},
    )
    properties = await props_cursor.to_list(length=2000)
    clients_cursor = db.clients.find(
        {"agency_id": agency_id, "client_type": {"$in": ["buyer", "tenant", "investor"]}},
        {"_id": 0},
    )
    clients = await clients_cursor.to_list(length=2000)

    results = []
    for p in properties:
        for c in clients:
            m = compute_match(p, c)
            if m["score"] < min_score:
                continue
            results.append({
                "property": _trim_property(p),
                "client": _trim_client(c),
                "score": m["score"],
                "missing": m["missing"],
                "breakdown": m["breakdown"],
            })
    results.sort(key=lambda r: r["score"], reverse=True)
    return {"items": results[:limit], "total": len(results), "min_score": min_score}


# -------------------- GET /matches/property/{pid} --------------------

@router.get("/property/{pid}")
async def matches_for_property(
    pid: str,
    min_score: int = Query(40, ge=0, le=100),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    agency_id = await _agency(user)
    db = Database.get()
    p = await db.properties.find_one({"id": pid, "agency_id": agency_id}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="property_not_found")
    clients = await db.clients.find(
        {"agency_id": agency_id, "client_type": {"$in": ["buyer", "tenant", "investor"]}},
        {"_id": 0},
    ).to_list(length=2000)
    results = []
    for c in clients:
        m = compute_match(p, c)
        if m["score"] < min_score:
            continue
        results.append({
            "client": _trim_client(c),
            "score": m["score"],
            "missing": m["missing"],
            "breakdown": m["breakdown"],
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    return {"property": _trim_property(p), "items": results[:limit], "total": len(results)}


# -------------------- GET /matches/client/{cid} --------------------

@router.get("/client/{cid}")
async def matches_for_client(
    cid: str,
    min_score: int = Query(40, ge=0, le=100),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    agency_id = await _agency(user)
    db = Database.get()
    c = await db.clients.find_one({"id": cid, "agency_id": agency_id}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="client_not_found")
    if not is_searcher(c):
        return {"client": _trim_client(c), "items": [], "total": 0,
                "info": "client_type_does_not_search"}
    props = await db.properties.find(
        {"agency_id": agency_id, "status": "active"}, {"_id": 0},
    ).to_list(length=2000)
    results = []
    for p in props:
        m = compute_match(p, c)
        if m["score"] < min_score:
            continue
        results.append({
            "property": _trim_property(p),
            "score": m["score"],
            "missing": m["missing"],
            "breakdown": m["breakdown"],
        })
    results.sort(key=lambda r: r["score"], reverse=True)
    return {"client": _trim_client(c), "items": results[:limit], "total": len(results)}


# -------------------- POST /matches/lead-score --------------------

@router.post("/lead-score")
async def compute_lead_score(
    property_id: str,
    client_id: str,
    force_refresh: bool = False,
    user: dict = Depends(get_current_user),
):
    """Compute AI Lead Score for a specific (property, client) pair.
    Combines deterministic match + Gemini-3 Flash classification.
    24h cache by default (force_refresh=true to bypass).
    Always returns a valid response (falls back to rule-based on AI failure).
    """
    agency_id = await _agency(user)
    db = Database.get()
    p = await db.properties.find_one({"id": property_id, "agency_id": agency_id}, {"_id": 0})
    if not p:
        raise HTTPException(status_code=404, detail="property_not_found")
    c = await db.clients.find_one({"id": client_id, "agency_id": agency_id}, {"_id": 0})
    if not c:
        raise HTTPException(status_code=404, detail="client_not_found")
    match = compute_match(p, c)

    cache_key = {"agency_id": agency_id, "property_id": property_id, "client_id": client_id}
    if not force_refresh:
        hit = await db.lead_score_cache.find_one(cache_key, {"_id": 0})
        if hit:
            # Keep cached AI; the deterministic match is always recomputed (cheap and fresh)
            return {
                "property": _trim_property(p),
                "client": _trim_client(c),
                "match": match,
                "lead_score": hit["lead_score"],
                "cached": True,
                "cached_at": hit.get("cached_at"),
            }

    ai = await score_lead(c, p, match)
    # Persist (atomic upsert)
    from datetime import datetime, timezone
    await db.lead_score_cache.update_one(
        cache_key,
        {"$set": {**cache_key, "lead_score": ai, "cached_at": datetime.now(timezone.utc)}},
        upsert=True,
    )
    return {
        "property": _trim_property(p),
        "client": _trim_client(c),
        "match": match,
        "lead_score": ai,
        "cached": False,
    }
