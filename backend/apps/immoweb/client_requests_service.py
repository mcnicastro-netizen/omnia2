"""Helpers for Client Requests (D-089)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from shared.models.client import SearchPreferences
from apps.immoweb.matching import (
    compute_match_score_fast,
    prefs_with_tolerance,
    resolve_tolerances,
)
from apps.immoweb.mls import _shareable_listing_clause

logger = logging.getLogger("omnia.client_requests")

COLLECTION = "client_requests"
MATCH_THRESHOLD = 50
PORTFOLIO_SCAN_CAP = 200
MLS_SCAN_CAP = 150
DEFAULT_TOLERANCES = {"price_pct": 10, "surface_pct": 10, "min_score": 50}

SEARCHER_TYPES = {"buyer", "tenant", "investor"}

_PROP_PROJ = {
    "_id": 0,
    "id": 1,
    "title": 1,
    "reference_code": 1,
    "agency_id": 1,
    "city": 1,
    "zone": 1,
    "operation": 1,
    "property_type": 1,
    "price": 1,
    "rent_monthly": 1,
    "surface_sqm": 1,
    "sqm": 1,
    "rooms": 1,
    "bedrooms": 1,
    "bathrooms": 1,
    "condition": 1,
    "floor": 1,
    "total_floors": 1,
    "energy": 1,
    "features": 1,
    "photos": 1,
    "status": 1,
    "visibility": 1,
    "mls_shared": 1,
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _prefs_nonempty(prefs: Optional[Dict[str, Any]]) -> bool:
    if not prefs or not isinstance(prefs, dict):
        return False
    keys = (
        "operation", "property_types", "cities", "zones",
        "price_min", "price_max", "surface_min", "surface_max",
        "rooms_min", "rooms_max", "bedrooms_min", "bathrooms_min",
        "conditions", "floor_preferences", "must_have_features",
        "energy_min_class", "notes",
    )
    for k in keys:
        v = prefs.get(k)
        if v is None or v is False or v == "" or v == []:
            continue
        return True
    if prefs.get("needs_photos") or prefs.get("needs_video") or prefs.get("needs_virtual_tour"):
        return True
    return False


def _normalize_prop_for_match(p: Dict[str, Any]) -> Dict[str, Any]:
    """Align MLS/legacy field names with matching engine expectations."""
    out = dict(p)
    if out.get("surface_sqm") is None and out.get("sqm") is not None:
        out["surface_sqm"] = out["sqm"]
    return out


async def ensure_indexes(db) -> None:
    await db[COLLECTION].create_index([("agency_id", 1), ("status", 1), ("created_at", -1)])
    await db[COLLECTION].create_index([("agency_id", 1), ("client_id", 1), ("created_at", -1)])
    await db[COLLECTION].create_index([("agency_id", 1), ("source", 1)])
    await db[COLLECTION].create_index([("agency_id", 1), ("request_type", 1)])
    await db[COLLECTION].create_index([("mls_shared", 1), ("status", 1)])
    await db[COLLECTION].create_index([("lead_id", 1)], sparse=True)


def build_request_doc(
    *,
    agency_id: str,
    client_id: str,
    request_type: str,
    source: str,
    criteria: Optional[Dict[str, Any]] = None,
    property_id: Optional[str] = None,
    title: Optional[str] = None,
    notes: Optional[str] = None,
    lead_id: Optional[str] = None,
    mls_shared: bool = False,
    assigned_agent_id: Optional[str] = None,
    status: str = "open",
) -> Dict[str, Any]:
    now = _now()
    crit = criteria if isinstance(criteria, dict) else {}
    if not crit:
        crit = SearchPreferences().model_dump()
    return {
        "id": str(uuid4()),
        "agency_id": agency_id,
        "client_id": client_id,
        "request_type": request_type,
        "status": status,
        "source": source or "manual",
        "title": title,
        "property_id": property_id,
        "criteria": crit,
        "mls_shared": bool(mls_shared),
        "auto_match": True,
        "match_tolerances": dict(DEFAULT_TOLERANCES),
        "assigned_agent_id": assigned_agent_id,
        "notes": notes,
        "lead_id": lead_id,
        "created_at": now,
        "updated_at": now,
    }


async def create_request(db, doc: Dict[str, Any]) -> Dict[str, Any]:
    await db[COLLECTION].insert_one(doc)
    return {k: v for k, v in doc.items() if k != "_id"}


async def find_by_lead(db, lead_id: str) -> Optional[Dict[str, Any]]:
    if not lead_id:
        return None
    return await db[COLLECTION].find_one({"lead_id": lead_id}, {"_id": 0})


async def ensure_from_immobilcloud(
    db,
    *,
    agency_id: str,
    client_id: str,
    property_id: str,
    lead_id: str,
    notes: Optional[str] = None,
    assigned_agent_id: Optional[str] = None,
) -> Dict[str, Any]:
    existing = await find_by_lead(db, lead_id)
    if existing:
        return existing
    prop = await db.properties.find_one(
        {"id": property_id},
        {"_id": 0, "title": 1, "reference_code": 1, "operation": 1, "city": 1, "property_type": 1, "price": 1},
    )
    title = None
    criteria: Dict[str, Any] = {}
    if prop:
        title = f"Interesse · {prop.get('title') or prop.get('reference_code') or property_id}"
        if prop.get("operation"):
            criteria["operation"] = prop["operation"]
        if prop.get("city"):
            criteria["cities"] = [prop["city"]]
        if prop.get("property_type"):
            criteria["property_types"] = [prop["property_type"]]
        if prop.get("price"):
            criteria["price_max"] = prop["price"]
    doc = build_request_doc(
        agency_id=agency_id,
        client_id=client_id,
        request_type="property_interest",
        source="ImmobilCloud",
        criteria=criteria,
        property_id=property_id,
        title=title,
        notes=notes,
        lead_id=lead_id,
        assigned_agent_id=assigned_agent_id,
    )
    return await create_request(db, doc)


async def ensure_from_widget(
    db,
    *,
    agency_id: str,
    lead_id: str,
    source: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    message: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    property_id: Optional[str] = None,
) -> Dict[str, Any]:
    existing = await find_by_lead(db, lead_id)
    if existing:
        return existing

    ctx = context if isinstance(context, dict) else {}
    pid = property_id or ctx.get("property_id")

    # Find or create client
    client_id = None
    if email:
        c = await db.clients.find_one(
            {"agency_id": agency_id, "email": str(email).lower()},
            {"_id": 0, "id": 1},
        )
        if c:
            client_id = c["id"]
    if not client_id and phone:
        c = await db.clients.find_one(
            {"agency_id": agency_id, "phone": phone},
            {"_id": 0, "id": 1},
        )
        if c:
            client_id = c["id"]
    if not client_id:
        now = _now()
        parts = (name or "").strip().split(None, 1)
        client_id = str(uuid4())
        await db.clients.insert_one({
            "id": client_id,
            "agency_id": agency_id,
            "name": parts[0] if parts else (email or phone or "Lead"),
            "surname": parts[1] if len(parts) > 1 else None,
            "email": str(email).lower() if email else None,
            "phone": phone,
            "whatsapp": None,
            "fiscal_code": None,
            "client_type": "buyer",
            "status": "new",
            "source": source,
            "assigned_agent_id": None,
            "preferences": SearchPreferences().model_dump(),
            "notes": message,
            "gdpr_consent": True,
            "created_at": now,
            "updated_at": now,
        })

    criteria: Dict[str, Any] = {}
    # Pull searchable hints from widget context if present
    for key in ("operation", "price_max", "price_min", "city", "cities", "property_type"):
        if key in ctx and ctx[key] is not None:
            if key == "city":
                criteria.setdefault("cities", []).append(ctx[key])
            elif key == "property_type":
                criteria["property_types"] = [ctx[key]]
            else:
                criteria[key] = ctx[key]

    rtype = "property_interest" if pid else "search_brief"
    title = f"Lead widget · {source}"
    if pid:
        title = f"Interesse widget · {pid[:8]}"
    doc = build_request_doc(
        agency_id=agency_id,
        client_id=client_id,
        request_type=rtype,
        source=source,
        criteria=criteria,
        property_id=pid,
        title=title,
        notes=message,
        lead_id=lead_id,
    )
    return await create_request(db, doc)


async def migrate_preferences_for_agency(db, agency_id: str) -> int:
    """Create search_brief requests from existing client.preferences (once per client)."""
    created = 0
    cursor = db.clients.find(
        {
            "agency_id": agency_id,
            "client_type": {"$in": list(SEARCHER_TYPES)},
            "$or": [{"trashed_at": {"$exists": False}}, {"trashed_at": None}],
        },
        {"_id": 0, "id": 1, "preferences": 1, "name": 1, "surname": 1, "source": 1},
    )
    clients = await cursor.to_list(length=5000)
    for c in clients:
        prefs = c.get("preferences") or {}
        if not _prefs_nonempty(prefs):
            continue
        already = await db[COLLECTION].count_documents({
            "agency_id": agency_id,
            "client_id": c["id"],
            "source": "migration_preferences",
        })
        if already:
            continue
        # Also skip if any open request already exists for this client
        open_n = await db[COLLECTION].count_documents({
            "agency_id": agency_id,
            "client_id": c["id"],
            "status": {"$in": ["open", "matched", "negotiating"]},
        })
        if open_n:
            continue
        name = f"{c.get('name') or ''} {c.get('surname') or ''}".strip() or "Cliente"
        doc = build_request_doc(
            agency_id=agency_id,
            client_id=c["id"],
            request_type="search_brief",
            source="migration_preferences",
            criteria=prefs if isinstance(prefs, dict) else {},
            title=f"Ricerca · {name}",
        )
        await create_request(db, doc)
        created += 1
    return created


async def score_properties(
    properties: List[Dict[str, Any]],
    criteria: Dict[str, Any],
    *,
    threshold: int = MATCH_THRESHOLD,
    price_pct: float = 0.10,
    surface_pct: float = 0.10,
) -> Tuple[List[Dict[str, Any]], Optional[int]]:
    """Return matches >= threshold sorted by score desc, plus best score (any)."""
    scored: List[Dict[str, Any]] = []
    best: Optional[int] = None
    prefs = prefs_with_tolerance(
        criteria if isinstance(criteria, dict) else {},
        price_pct=price_pct,
        surface_pct=surface_pct,
    )
    for raw in properties:
        p = _normalize_prop_for_match(raw)
        s = compute_match_score_fast(p, prefs)
        if best is None or s > best:
            best = s
        if s >= threshold:
            scored.append({
                "property_id": p.get("id"),
                "agency_id": p.get("agency_id"),
                "title": p.get("title"),
                "reference_code": p.get("reference_code"),
                "city": p.get("city"),
                "operation": p.get("operation"),
                "property_type": p.get("property_type"),
                "price": p.get("price") or p.get("rent_monthly"),
                "score": s,
            })
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored, best


async def match_request(
    db,
    agency_id: str,
    req: Dict[str, Any],
    *,
    min_score: Optional[int] = None,
) -> Dict[str, Any]:
    """Portfolio first; if no useful match, fall through to MLS shareable inventory."""
    tol = resolve_tolerances(req.get("match_tolerances"))
    threshold = int(min_score if min_score is not None else tol["min_score"])
    criteria = req.get("criteria") or {}
    # Type A with explicit property: score that one first
    if req.get("request_type") == "property_interest" and req.get("property_id"):
        prop = await db.properties.find_one({"id": req["property_id"]}, _PROP_PROJ)
        if prop:
            p = _normalize_prop_for_match(prop)
            prefs = prefs_with_tolerance(criteria, price_pct=tol["price_pct"], surface_pct=tol["surface_pct"])
            if not _prefs_nonempty(criteria):
                score = 100 if prop.get("agency_id") == agency_id else 70
            else:
                score = compute_match_score_fast(p, prefs)
            scope = "portfolio" if prop.get("agency_id") == agency_id else "mls"
            item = {
                "property_id": p.get("id"),
                "agency_id": p.get("agency_id"),
                "title": p.get("title"),
                "reference_code": p.get("reference_code"),
                "city": p.get("city"),
                "operation": p.get("operation"),
                "property_type": p.get("property_type"),
                "price": p.get("price") or p.get("rent_monthly"),
                "score": score,
                "scope": scope,
            }
            return {
                "scope_used": scope,
                "best_score": score,
                "tolerances": tol,
                "portfolio_matches": [item] if scope == "portfolio" and score >= threshold else [],
                "mls_matches": [item] if scope == "mls" and score >= threshold else [],
                "items": [item] if score >= threshold else [],
            }

    own = await db.properties.find(
        {"agency_id": agency_id, "status": "active"},
        _PROP_PROJ,
    ).sort("updated_at", -1).to_list(length=PORTFOLIO_SCAN_CAP)
    portfolio_hits, best_own = await score_properties(
        own, criteria, threshold=threshold,
        price_pct=tol["price_pct"], surface_pct=tol["surface_pct"],
    )

    if portfolio_hits:
        for h in portfolio_hits:
            h["scope"] = "portfolio"
        return {
            "scope_used": "portfolio",
            "best_score": best_own,
            "tolerances": tol,
            "portfolio_matches": portfolio_hits,
            "mls_matches": [],
            "items": portfolio_hits,
        }

    # Fall through to MLS (other agencies, shareable)
    clause = _shareable_listing_clause()
    mls_q = {
        **clause,
        "agency_id": {"$ne": agency_id},
        "status": "active",
    }
    mls_props = await db.properties.find(mls_q, _PROP_PROJ).sort("updated_at", -1).to_list(length=MLS_SCAN_CAP)
    mls_hits, best_mls = await score_properties(
        mls_props, criteria, threshold=threshold,
        price_pct=tol["price_pct"], surface_pct=tol["surface_pct"],
    )
    for h in mls_hits:
        h["scope"] = "mls"
    best = best_own if best_own is not None else best_mls
    if best_mls is not None and (best is None or best_mls > best):
        best = best_mls
    return {
        "scope_used": "mls" if mls_hits else "none",
        "best_score": best,
        "tolerances": tol,
        "portfolio_matches": [],
        "mls_matches": mls_hits,
        "items": mls_hits,
    }


async def match_property_to_requests(
    db,
    agency_id: str,
    prop: Dict[str, Any],
    *,
    min_score: int = 40,
    limit: int = 20,
    include_mls_shared: bool = True,
) -> List[Dict[str, Any]]:
    """Match inverso: immobile → richieste aperte (proprie + MLS shared di altre agenzie)."""
    p = _normalize_prop_for_match(prop)
    results: List[Dict[str, Any]] = []

    own_reqs = await db[COLLECTION].find(
        {"agency_id": agency_id, "status": {"$in": ["open", "matched", "negotiating"]}},
        {"_id": 0},
    ).to_list(length=2000)

    network_reqs: List[Dict[str, Any]] = []
    if include_mls_shared:
        network_reqs = await db[COLLECTION].find(
            {
                "agency_id": {"$ne": agency_id},
                "mls_shared": True,
                "status": {"$in": ["open", "matched", "negotiating"]},
            },
            {"_id": 0},
        ).to_list(length=1000)

    for req in own_reqs + network_reqs:
        # Explicit property interest
        if req.get("request_type") == "property_interest" and req.get("property_id"):
            if req["property_id"] != p.get("id"):
                continue
            score = 100 if req.get("agency_id") == agency_id else 90
        else:
            tol = resolve_tolerances(req.get("match_tolerances"))
            prefs = prefs_with_tolerance(
                req.get("criteria") or {},
                price_pct=tol["price_pct"],
                surface_pct=tol["surface_pct"],
            )
            if not prefs:
                continue
            score = compute_match_score_fast(p, prefs)
        if score < min_score:
            continue
        scope = "portfolio" if req.get("agency_id") == agency_id else "mls"
        results.append({
            "request_id": req.get("id"),
            "client_id": req.get("client_id"),
            "agency_id": req.get("agency_id"),
            "title": req.get("title"),
            "request_type": req.get("request_type"),
            "source": req.get("source"),
            "mls_shared": bool(req.get("mls_shared")),
            "score": score,
            "scope": scope,
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


async def quick_match_summary(
    db,
    agency_id: str,
    req: Dict[str, Any],
) -> Dict[str, Any]:
    """Lightweight counts for list rows."""
    result = await match_request(db, agency_id, req, min_score=MATCH_THRESHOLD)
    scope = result.get("scope_used") or "none"
    best = result.get("best_score")
    return {
        "best_match_score": best if scope != "none" else (best if (best or 0) >= MATCH_THRESHOLD else None),
        "best_match_scope": scope if (result.get("items")) else "none",
        "matches_portfolio": len(result.get("portfolio_matches") or []),
        "matches_mls": len(result.get("mls_matches") or []),
    }
