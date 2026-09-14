"""OMNIA — MLS Network (M2 / ex M4.S1).

Dashboard CRM + network search + partner offers, designed for ≥10k agencies.
Uses visibility public|mls_only for shareable inventory. Seed fills demo data
so the UI works with zero real customers.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user, require_roles
from shared.auth.tenant import optional_agency_id
from shared.db.connection import Database

logger = logging.getLogger("omnia.mls")
router = APIRouter(prefix="/mls", tags=["mls"])

OfferStatus = Literal["pending", "accepted", "rejected", "expired", "revoked"]
PartnerStatus = Literal["pending", "active", "revoked"]


class JoinMlsBody(BaseModel):
    accept_terms: bool = True
    province_sigla: Optional[str] = Field(default=None, max_length=2)


class PartnerInviteBody(BaseModel):
    partner_agency_id: str
    message: Optional[str] = Field(default=None, max_length=500)


class OfferBody(BaseModel):
    to_agency_id: str
    property_id: str
    message: Optional[str] = Field(default=None, max_length=1000)


class OfferActionBody(BaseModel):
    action: Literal["accept", "reject"]


class SeedBody(BaseModel):
    agencies: int = Field(default=50, ge=1, le=1000)
    properties_per_agency: int = Field(default=5, ge=1, le=50)
    province_sigla: str = Field(default="CT", max_length=2)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: Optional[datetime] = None) -> str:
    return (dt or _now()).isoformat()


def _agency_id(user: dict) -> str:
    aid = optional_agency_id(user)
    if not aid:
        raise HTTPException(status_code=400, detail="no_active_agency")
    return aid


def _prop_projection() -> Dict[str, int]:
    return {
        "_id": 0,
        "id": 1,
        "agency_id": 1,
        "title": 1,
        "city": 1,
        "province": 1,
        "province_sigla": 1,
        "price": 1,
        "operation": 1,
        "property_type": 1,
        "sqm": 1,
        "rooms": 1,
        "visibility": 1,
        "cover_url": 1,
        "photos": 1,
        "reference_code": 1,
        "status": 1,
        "created_at": 1,
    }


def _cover(p: dict) -> Optional[str]:
    if p.get("cover_url"):
        return p["cover_url"]
    photos = p.get("photos") or []
    if photos and isinstance(photos[0], dict):
        return photos[0].get("url") or photos[0].get("path")
    if photos and isinstance(photos[0], str):
        return photos[0]
    return None


async def ensure_mls_indexes(db) -> None:
    await db.mls_partners.create_index([("agency_a", 1), ("agency_b", 1)], unique=True)
    await db.mls_partners.create_index([("agency_a", 1), ("status", 1)])
    await db.mls_partners.create_index([("agency_b", 1), ("status", 1)])
    await db.mls_requests.create_index([("to_agency_id", 1), ("status", 1), ("created_at", -1)])
    await db.mls_requests.create_index([("from_agency_id", 1), ("status", 1)])
    await db.mls_requests.create_index([("property_id", 1)])
    await db.mls_events.create_index([("agency_id", 1), ("created_at", -1)])
    await db.agencies.create_index([("mls_enabled", 1), ("mls_province", 1)])
    await db.properties.create_index(
        [("visibility", 1), ("province_sigla", 1), ("status", 1), ("created_at", -1)]
    )


async def _log_event(db, agency_id: str, kind: str, payload: Optional[dict] = None) -> None:
    await db.mls_events.insert_one(
        {
            "id": str(uuid4()),
            "agency_id": agency_id,
            "kind": kind,
            "payload": payload or {},
            "created_at": _iso(),
        }
    )


@router.get("/dashboard")
async def mls_dashboard(user: dict = Depends(require_roles("agency_admin", "agent", "super_admin"))):
    """CRM MLS hub — contatori stile Agesta (struttura), dati OMNIA."""
    db = Database.get()
    await ensure_mls_indexes(db)
    aid = _agency_id(user)
    agency = await db.agencies.find_one({"id": aid}, {"_id": 0})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")

    my_shared = await db.properties.count_documents(
        {"agency_id": aid, "visibility": {"$in": ["public", "mls_only"]}, "status": {"$ne": "deleted"}}
    )
    my_exclusive = await db.properties.count_documents(
        {"agency_id": aid, "visibility": "private", "status": {"$ne": "deleted"}}
    )
    with_photos = await db.properties.count_documents(
        {
            "agency_id": aid,
            "visibility": {"$in": ["public", "mls_only"]},
            "status": {"$ne": "deleted"},
            "$or": [{"cover_url": {"$exists": True, "$ne": None}}, {"photos.0": {"$exists": True}}],
        }
    )

    province = (agency.get("mls_province") or agency.get("province_sigla") or "").upper()
    local_q: Dict[str, Any] = {
        "visibility": {"$in": ["public", "mls_only"]},
        "status": {"$ne": "deleted"},
        "agency_id": {"$ne": aid},
    }
    if province:
        local_q["province_sigla"] = province
    local_listings = await db.properties.count_documents(local_q)
    national_listings = await db.properties.count_documents(
        {
            "visibility": {"$in": ["public", "mls_only"]},
            "status": {"$ne": "deleted"},
            "agency_id": {"$ne": aid},
        }
    )
    network_agencies = await db.agencies.count_documents({"mls_enabled": True, "id": {"$ne": aid}})

    partners_active = await db.mls_partners.count_documents(
        {"status": "active", "$or": [{"agency_a": aid}, {"agency_b": aid}]}
    )
    invites_pending = await db.mls_partners.count_documents(
        {"status": "pending", "agency_b": aid}
    )
    offers_in = await db.mls_requests.count_documents(
        {"to_agency_id": aid, "status": "pending", "type": "offer"}
    )
    offers_out = await db.mls_requests.count_documents(
        {"from_agency_id": aid, "status": "pending", "type": "offer"}
    )
    requests_shared = await db.mls_requests.count_documents(
        {"status": "accepted", "$or": [{"from_agency_id": aid}, {"to_agency_id": aid}]}
    )

    return {
        "mls_enabled": bool(agency.get("mls_enabled")),
        "joined_at": agency.get("mls_joined_at"),
        "province_sigla": province or None,
        "mine": {
            "shared": my_shared,
            "exclusive": my_exclusive,
            "with_photos": with_photos,
        },
        "network": {
            "agencies": network_agencies,
            "local_listings": local_listings,
            "national_listings": national_listings,
            "label_local": f"MLS {province}" if province else "MLS Locale",
            "label_national": "MLS Italia",
        },
        "collaborations": {
            "partners": partners_active,
            "invites_pending": invites_pending,
            "offers_incoming": offers_in,
            "offers_outgoing": offers_out,
            "accepted": requests_shared,
        },
    }


@router.post("/join")
async def join_mls(
    body: JoinMlsBody,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    if not body.accept_terms:
        raise HTTPException(status_code=400, detail="terms_required")
    db = Database.get()
    aid = _agency_id(user)
    agency = await db.agencies.find_one({"id": aid}, {"_id": 0})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    province = (body.province_sigla or agency.get("province_sigla") or agency.get("province") or "").upper()[:2]
    await db.agencies.update_one(
        {"id": aid},
        {
            "$set": {
                "mls_enabled": True,
                "mls_joined_at": _iso(),
                "mls_province": province or None,
            }
        },
    )
    await _log_event(db, aid, "join", {"province": province})
    return {"ok": True, "mls_enabled": True, "province_sigla": province or None}


@router.get("/inventory")
async def my_mls_inventory(
    scope: Literal["mine", "local", "national"] = "mine",
    limit: int = Query(default=24, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    agency = await db.agencies.find_one({"id": aid}, {"_id": 0, "mls_province": 1, "province_sigla": 1})
    province = ((agency or {}).get("mls_province") or (agency or {}).get("province_sigla") or "").upper()

    q: Dict[str, Any] = {
        "visibility": {"$in": ["public", "mls_only"]},
        "status": {"$ne": "deleted"},
    }
    if scope == "mine":
        q["agency_id"] = aid
    elif scope == "local":
        q["agency_id"] = {"$ne": aid}
        if province:
            q["province_sigla"] = province
    else:
        q["agency_id"] = {"$ne": aid}

    total = await db.properties.count_documents(q)
    cursor = (
        db.properties.find(q, _prop_projection())
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    items = []
    async for p in cursor:
        items.append(
            {
                **{k: p.get(k) for k in ("id", "agency_id", "title", "city", "province", "province_sigla",
                                         "price", "operation", "property_type", "sqm", "rooms",
                                         "visibility", "reference_code", "status")},
                "cover_url": _cover(p),
            }
        )
    return {"scope": scope, "total": total, "items": items, "limit": limit, "skip": skip}


@router.get("/partners")
async def list_partners(user: dict = Depends(require_roles("agency_admin", "agent", "super_admin"))):
    db = Database.get()
    aid = _agency_id(user)
    cursor = db.mls_partners.find(
        {"$or": [{"agency_a": aid}, {"agency_b": aid}]},
        {"_id": 0},
    ).sort("created_at", -1)
    rows = [r async for r in cursor]
    other_ids = []
    for r in rows:
        other = r["agency_b"] if r["agency_a"] == aid else r["agency_a"]
        other_ids.append(other)
    agencies = {
        a["id"]: a
        async for a in db.agencies.find(
            {"id": {"$in": other_ids}},
            {"_id": 0, "id": 1, "name": 1, "slug": 1, "city": 1, "mls_province": 1},
        )
    }
    items = []
    for r in rows:
        other = r["agency_b"] if r["agency_a"] == aid else r["agency_a"]
        items.append(
            {
                **r,
                "counterpart_id": other,
                "counterpart": agencies.get(other),
                "direction": "outgoing" if r["agency_a"] == aid else "incoming",
            }
        )
    return {"items": items}


@router.post("/partners/invite")
async def invite_partner(
    body: PartnerInviteBody,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    if body.partner_agency_id == aid:
        raise HTTPException(status_code=400, detail="cannot_partner_self")
    partner = await db.agencies.find_one({"id": body.partner_agency_id, "mls_enabled": True}, {"_id": 0, "id": 1})
    if not partner:
        raise HTTPException(status_code=404, detail="partner_not_in_mls")
    a, b = sorted([aid, body.partner_agency_id])
    existing = await db.mls_partners.find_one({"agency_a": a, "agency_b": b}, {"_id": 0})
    if existing and existing.get("status") in ("active", "pending"):
        return existing
    doc = {
        "id": str(uuid4()),
        "agency_a": a,
        "agency_b": b,
        "initiator_id": aid,
        "status": "pending",
        "message": body.message,
        "created_at": _iso(),
        "since": None,
    }
    await db.mls_partners.insert_one(doc)
    await _log_event(db, aid, "partner_invite", {"partner": body.partner_agency_id})
    doc.pop("_id", None)
    return doc


@router.post("/partners/{partner_id}/respond")
async def respond_partner(
    partner_id: str,
    body: OfferActionBody,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    row = await db.mls_partners.find_one({"id": partner_id}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    if aid not in (row["agency_a"], row["agency_b"]):
        raise HTTPException(status_code=403, detail="forbidden")
    if row.get("initiator_id") == aid:
        raise HTTPException(status_code=400, detail="initiator_cannot_respond")
    status = "active" if body.action == "accept" else "revoked"
    patch = {"status": status}
    if status == "active":
        patch["since"] = _iso()
    await db.mls_partners.update_one({"id": partner_id}, {"$set": patch})
    await _log_event(db, aid, f"partner_{body.action}", {"partner_id": partner_id})
    return {"id": partner_id, "status": status}


@router.get("/offers")
async def list_offers(
    direction: Literal["in", "out", "all"] = "all",
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    q: Dict[str, Any] = {"type": "offer"}
    if direction == "in":
        q["to_agency_id"] = aid
    elif direction == "out":
        q["from_agency_id"] = aid
    else:
        q["$or"] = [{"to_agency_id": aid}, {"from_agency_id": aid}]
    items = [r async for r in db.mls_requests.find(q, {"_id": 0}).sort("created_at", -1).limit(100)]
    return {"items": items}


@router.post("/offers")
async def create_offer(
    body: OfferBody,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    prop = await db.properties.find_one(
        {"id": body.property_id, "agency_id": aid},
        {"_id": 0, "id": 1, "title": 1, "visibility": 1},
    )
    if not prop:
        raise HTTPException(status_code=404, detail="property_not_found")
    if prop.get("visibility") == "private":
        raise HTTPException(status_code=400, detail="property_not_shared_on_mls")
    target = await db.agencies.find_one({"id": body.to_agency_id, "mls_enabled": True}, {"_id": 0, "id": 1})
    if not target:
        raise HTTPException(status_code=404, detail="target_not_in_mls")
    doc = {
        "id": str(uuid4()),
        "type": "offer",
        "from_agency_id": aid,
        "to_agency_id": body.to_agency_id,
        "property_id": body.property_id,
        "property_title": prop.get("title"),
        "message": body.message,
        "status": "pending",
        "created_at": _iso(),
        "expires_at": _iso(_now() + timedelta(days=14)),
    }
    await db.mls_requests.insert_one(doc)
    await _log_event(db, aid, "offer_created", {"offer_id": doc["id"]})
    doc.pop("_id", None)
    return doc


@router.post("/offers/{offer_id}/respond")
async def respond_offer(
    offer_id: str,
    body: OfferActionBody,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    row = await db.mls_requests.find_one({"id": offer_id, "type": "offer"}, {"_id": 0})
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    if row["to_agency_id"] != aid:
        raise HTTPException(status_code=403, detail="forbidden")
    status = "accepted" if body.action == "accept" else "rejected"
    await db.mls_requests.update_one({"id": offer_id}, {"$set": {"status": status, "responded_at": _iso()}})
    await _log_event(db, aid, f"offer_{body.action}", {"offer_id": offer_id})
    return {"id": offer_id, "status": status}


@router.get("/search/public")
async def public_network_search(
    province: Optional[str] = None,
    city: Optional[str] = None,
    operation: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    limit: int = Query(default=24, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
):
    """Public dual-box: network-wide MLS search (no auth)."""
    db = Database.get()
    q: Dict[str, Any] = {
        "visibility": {"$in": ["public", "mls_only"]},
        "status": {"$ne": "deleted"},
    }
    if province:
        q["province_sigla"] = province.upper()[:2]
    if city:
        q["city"] = {"$regex": f"^{city}$", "$options": "i"}
    if operation:
        q["operation"] = operation
    if price_min is not None or price_max is not None:
        price_q: Dict[str, Any] = {}
        if price_min is not None:
            price_q["$gte"] = price_min
        if price_max is not None:
            price_q["$lte"] = price_max
        q["price"] = price_q

    total = await db.properties.count_documents(q)
    agencies_in_mls = await db.agencies.count_documents({"mls_enabled": True})
    items = []
    async for p in (
        db.properties.find(q, _prop_projection()).sort("created_at", -1).skip(skip).limit(limit)
    ):
        items.append(
            {
                "id": p.get("id"),
                "title": p.get("title"),
                "city": p.get("city"),
                "province_sigla": p.get("province_sigla"),
                "price": p.get("price"),
                "operation": p.get("operation"),
                "property_type": p.get("property_type"),
                "sqm": p.get("sqm"),
                "cover_url": _cover(p),
            }
        )
    return {
        "total": total,
        "network_agencies": agencies_in_mls,
        "claim": f"{total:,} immobili condivisi".replace(",", "."),
        "items": items,
        "limit": limit,
        "skip": skip,
    }


@router.post("/seed")
async def seed_mls_network(
    body: SeedBody,
    user: dict = Depends(require_roles("super_admin")),
):
    """Synthetic agencies+listings for UI and load ladder (10/50/500/1000…)."""
    db = Database.get()
    await ensure_mls_indexes(db)
    created_agencies = 0
    created_props = 0
    province = body.province_sigla.upper()[:2]
    cities = {
        "CT": ["Catania", "Belpasso", "Acireale", "Misterbianco"],
        "RM": ["Roma", "Frascati", "Tivoli"],
        "MI": ["Milano", "Sesto San Giovanni", "Monza"],
    }.get(province, ["Catania", "Belpasso", "Acireale"])

    for i in range(body.agencies):
        aid = f"mls-seed-{province.lower()}-{i+1:04d}"
        existing = await db.agencies.find_one({"id": aid}, {"_id": 0, "id": 1})
        if not existing:
            await db.agencies.insert_one(
                {
                    "id": aid,
                    "name": f"Agenzia MLS Demo {province} {i+1}",
                    "slug": f"mls-demo-{province.lower()}-{i+1}",
                    "city": cities[i % len(cities)],
                    "province_sigla": province,
                    "mls_enabled": True,
                    "mls_joined_at": _iso(),
                    "mls_province": province,
                    "plan_type": "starter",
                    "created_at": _iso(),
                    "_seed": True,
                }
            )
            created_agencies += 1
        else:
            await db.agencies.update_one(
                {"id": aid},
                {"$set": {"mls_enabled": True, "mls_province": province}},
            )

        for j in range(body.properties_per_agency):
            pid = f"{aid}-p{j+1:02d}"
            if await db.properties.find_one({"id": pid}, {"_id": 0, "id": 1}):
                continue
            city = cities[(i + j) % len(cities)]
            await db.properties.insert_one(
                {
                    "id": pid,
                    "agency_id": aid,
                    "title": f"{'Appartamento' if j % 2 == 0 else 'Villa'} in {city} · rif {j+1}",
                    "city": city,
                    "province": province,
                    "province_sigla": province,
                    "price": 80000 + (i * 1000) + (j * 15000),
                    "operation": "sale" if j % 3 else "rent",
                    "property_type": "appartamento" if j % 2 == 0 else "villa",
                    "sqm": 60 + j * 10,
                    "rooms": 2 + (j % 3),
                    "visibility": "mls_only" if j % 4 == 0 else "public",
                    "status": "listed",
                    "privacy_level": "L2",
                    "reference_code": f"{province}-{i+1}-{j+1}",
                    "created_at": _iso(),
                    "_seed": True,
                }
            )
            created_props += 1

    # Wire a few pending partner links / offers for the caller's agency if any
    caller_aid = optional_agency_id(user)
    if caller_aid:
        seed_ids = [
            f"mls-seed-{province.lower()}-{n:04d}"
            for n in range(1, min(6, body.agencies + 1))
        ]
        for sid in seed_ids[:3]:
            a, b = sorted([caller_aid, sid])
            if not await db.mls_partners.find_one({"agency_a": a, "agency_b": b}):
                await db.mls_partners.insert_one(
                    {
                        "id": str(uuid4()),
                        "agency_a": a,
                        "agency_b": b,
                        "initiator_id": sid,
                        "status": "pending" if sid.endswith("0001") else "active",
                        "since": _iso() if not sid.endswith("0001") else None,
                        "created_at": _iso(),
                        "_seed": True,
                    }
                )

    total_mls = await db.agencies.count_documents({"mls_enabled": True})
    total_listings = await db.properties.count_documents(
        {"visibility": {"$in": ["public", "mls_only"]}, "status": {"$ne": "deleted"}}
    )
    return {
        "created_agencies": created_agencies,
        "created_properties": created_props,
        "totals": {"mls_agencies": total_mls, "shared_listings": total_listings},
        "ladder_hint": "Rilanciare con agencies=10|50|500|1000 per lo scale test",
    }
