"""OMNIA — Client Requests CRM (D-089 · Lista richieste)."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user, require_roles
from shared.auth.tenant import arequire_agency as _agency
from shared.db.connection import Database
from shared.db.trash import with_not_trashed
from shared.models.client import SearchPreferences
from shared.models.client_request import (
    ClientRequestCreate,
    ClientRequestUpdate,
)
from apps.immoweb import client_requests_service as svc

logger = logging.getLogger("omnia.client_requests")
router = APIRouter(prefix="/requests", tags=["client-requests"])


def _strip(doc: dict) -> dict:
    return {k: v for k, v in doc.items() if k != "_id"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MigrateResult(BaseModel):
    created: int


@router.get("")
async def list_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    source: Optional[str] = None,
    client_id: Optional[str] = None,
    q: Optional[str] = None,
    enrich_match: bool = Query(True),
    migrate: bool = Query(True, description="Auto-migrate client preferences → requests once"),
    user: dict = Depends(get_current_user),
):
    agency_id = await _agency(user)
    db = Database.get()
    await svc.ensure_indexes(db)

    migrated = 0
    if migrate:
        try:
            migrated = await svc.migrate_preferences_for_agency(db, agency_id)
        except Exception as e:  # noqa: BLE001
            logger.warning("preferences migrate failed: %s", e)

    query: Dict[str, Any] = {"agency_id": agency_id}
    if status:
        query["status"] = status
    if request_type:
        query["request_type"] = request_type
    if source:
        query["source"] = source
    if client_id:
        query["client_id"] = client_id

    total = await db[svc.COLLECTION].count_documents(query)
    docs = await (
        db[svc.COLLECTION]
        .find(query, {"_id": 0})
        .sort("created_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list(page_size)
    )

    # Enrich client + property labels; optional match summary
    client_ids = list({d["client_id"] for d in docs if d.get("client_id")})
    prop_ids = list({d["property_id"] for d in docs if d.get("property_id")})
    clients_map: Dict[str, dict] = {}
    props_map: Dict[str, dict] = {}
    if client_ids:
        for c in await db.clients.find(
            with_not_trashed({"id": {"$in": client_ids}}),
            {"_id": 0, "id": 1, "name": 1, "surname": 1, "client_type": 1, "email": 1, "phone": 1},
        ).to_list(length=len(client_ids)):
            clients_map[c["id"]] = c
    if prop_ids:
        for p in await db.properties.find(
            {"id": {"$in": prop_ids}},
            {"_id": 0, "id": 1, "title": 1, "reference_code": 1},
        ).to_list(length=len(prop_ids)):
            props_map[p["id"]] = p

    # Optional text filter on enriched fields (post-query for simplicity at agency scale)
    items = []
    for d in docs:
        c = clients_map.get(d.get("client_id") or "", {})
        p = props_map.get(d.get("property_id") or "", {})
        client_name = f"{c.get('name') or ''} {c.get('surname') or ''}".strip() or None
        row = {
            **d,
            "client_name": client_name,
            "client_type": c.get("client_type"),
            "property_title": p.get("title"),
            "property_ref": p.get("reference_code"),
            "best_match_score": None,
            "best_match_scope": None,
            "matches_portfolio": 0,
            "matches_mls": 0,
        }
        if q:
            qlow = q.lower()
            blob = " ".join([
                client_name or "",
                d.get("title") or "",
                d.get("source") or "",
                p.get("title") or "",
                p.get("reference_code") or "",
            ]).lower()
            if qlow not in blob:
                continue
        if enrich_match and d.get("status") in ("open", "matched", "negotiating"):
            try:
                summary = await svc.quick_match_summary(db, agency_id, d)
                row.update(summary)
            except Exception as e:  # noqa: BLE001
                logger.debug("match summary skip: %s", e)
        items.append(row)

    # Counts by type / source / status (agency-wide)
    pipeline = [
        {"$match": {"agency_id": agency_id}},
        {"$group": {
            "_id": None,
            "all": {"$sum": 1},
            "open": {"$sum": {"$cond": [{"$eq": ["$status", "open"]}, 1, 0]}},
            "property_interest": {"$sum": {"$cond": [{"$eq": ["$request_type", "property_interest"]}, 1, 0]}},
            "search_brief": {"$sum": {"$cond": [{"$eq": ["$request_type", "search_brief"]}, 1, 0]}},
            "mls_shared": {"$sum": {"$cond": ["$mls_shared", 1, 0]}},
        }},
    ]
    agg = await db[svc.COLLECTION].aggregate(pipeline).to_list(1)
    counts = agg[0] if agg else {"all": 0, "open": 0, "property_interest": 0, "search_brief": 0, "mls_shared": 0}
    counts.pop("_id", None)
    if migrated:
        counts["migrated_this_call"] = migrated

    # Source breakdown
    src_pipe = [
        {"$match": {"agency_id": agency_id}},
        {"$group": {"_id": "$source", "n": {"$sum": 1}}},
    ]
    sources = {r["_id"] or "unknown": r["n"] for r in await db[svc.COLLECTION].aggregate(src_pipe).to_list(50)}
    counts["by_source"] = sources

    if q:
        total = len(items)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "counts": counts,
    }


@router.post("/run-matching")
async def run_matching_now(
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Trigger matching digest for the active agency (manual / test)."""
    agency_id = await _agency(user)
    from apps.immoweb.request_matching_job import run_all_request_matching
    result = await run_all_request_matching(agency_id=agency_id)
    return {"ok": True, **result}


@router.post("/migrate-preferences", response_model=MigrateResult)
async def migrate_preferences(
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    agency_id = await _agency(user)
    db = Database.get()
    n = await svc.migrate_preferences_for_agency(db, agency_id)
    return {"created": n}


@router.get("/mls-network")
async def list_mls_shared_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    min_score_vs_my_stock: Optional[int] = Query(
        None, ge=0, le=100,
        description="Se impostato, tiene solo richieste che matchano almeno un immobile del mio portafoglio",
    ),
    user: dict = Depends(get_current_user),
):
    """Richieste condivise da altre agenzie (mls_shared=true) — D-090 regole rete."""
    agency_id = await _agency(user)
    db = Database.get()
    q = {
        "agency_id": {"$ne": agency_id},
        "mls_shared": True,
        "status": {"$in": ["open", "matched", "negotiating"]},
    }
    total = await db[svc.COLLECTION].count_documents(q)
    docs = await (
        db[svc.COLLECTION]
        .find(q, {"_id": 0, "client_id": 0, "notes": 0, "lead_id": 0})  # privacy: no client PII
        .sort("updated_at", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
        .to_list(page_size)
    )

    # Optional: filter by compatibility with my active stock
    items = []
    my_props = None
    if min_score_vs_my_stock is not None:
        my_props = await db.properties.find(
            {"agency_id": agency_id, "status": "active"},
            svc._PROP_PROJ,
        ).to_list(length=svc.PORTFOLIO_SCAN_CAP)

    for d in docs:
        row = {
            "id": d.get("id"),
            "agency_id": d.get("agency_id"),
            "request_type": d.get("request_type"),
            "title": d.get("title") or "Richiesta MLS",
            "criteria": d.get("criteria") or {},
            "match_tolerances": d.get("match_tolerances"),
            "status": d.get("status"),
            "updated_at": d.get("updated_at"),
            "best_vs_my_stock": None,
        }
        # Strip criteria notes that might leak PII
        if isinstance(row["criteria"], dict):
            row["criteria"] = {k: v for k, v in row["criteria"].items() if k != "notes"}
        if my_props is not None:
            from apps.immoweb.matching import resolve_tolerances
            tol = resolve_tolerances(d.get("match_tolerances"))
            scored, best = await svc.score_properties(
                my_props,
                row["criteria"],
                threshold=min_score_vs_my_stock,
                price_pct=tol["price_pct"],
                surface_pct=tol["surface_pct"],
            )
            row["best_vs_my_stock"] = best
            if best is None or best < min_score_vs_my_stock:
                continue
            row["matches_vs_my_stock"] = len(scored)
        items.append(row)

    return {
        "items": items,
        "total": total if min_score_vs_my_stock is None else len(items),
        "page": page,
        "page_size": page_size,
        "privacy": "no_client_pii",
    }


@router.post("", status_code=201)
async def create_request(
    payload: ClientRequestCreate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    agency_id = await _agency(user)
    db = Database.get()
    client = await db.clients.find_one(
        with_not_trashed({"id": payload.client_id, "agency_id": agency_id}),
        {"_id": 0, "id": 1, "client_type": 1, "name": 1, "surname": 1},
    )
    if not client:
        raise HTTPException(status_code=404, detail="client_not_found")

    if payload.request_type == "property_interest" and not payload.property_id:
        raise HTTPException(status_code=400, detail="property_id_required_for_interest")

    if payload.property_id:
        prop = await db.properties.find_one({"id": payload.property_id}, {"_id": 0, "id": 1})
        if not prop:
            raise HTTPException(status_code=404, detail="property_not_found")

    criteria = (payload.criteria.model_dump() if payload.criteria else SearchPreferences().model_dump())
    title = payload.title
    if not title:
        name = f"{client.get('name') or ''} {client.get('surname') or ''}".strip() or "Cliente"
        if payload.request_type == "property_interest":
            title = f"Interesse · {name}"
        else:
            title = f"Ricerca · {name}"

    doc = svc.build_request_doc(
        agency_id=agency_id,
        client_id=payload.client_id,
        request_type=payload.request_type,
        source=payload.source or "manual",
        criteria=criteria,
        property_id=payload.property_id,
        title=title,
        notes=payload.notes,
        mls_shared=payload.mls_shared,
        assigned_agent_id=user.get("id"),
        status=payload.status or "open",
    )
    return await svc.create_request(db, doc)


@router.get("/{request_id}")
async def get_request(
    request_id: str,
    user: dict = Depends(get_current_user),
):
    agency_id = await _agency(user)
    db = Database.get()
    doc = await db[svc.COLLECTION].find_one(
        {"id": request_id, "agency_id": agency_id},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="request_not_found")
    return doc


@router.patch("/{request_id}")
async def update_request(
    request_id: str,
    payload: ClientRequestUpdate,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    agency_id = await _agency(user)
    db = Database.get()
    existing = await db[svc.COLLECTION].find_one(
        {"id": request_id, "agency_id": agency_id},
        {"_id": 0},
    )
    if not existing:
        raise HTTPException(status_code=404, detail="request_not_found")

    data = payload.model_dump(exclude_unset=True)
    if "criteria" in data and data["criteria"] is not None:
        if hasattr(data["criteria"], "model_dump"):
            data["criteria"] = data["criteria"].model_dump()
    data["updated_at"] = _now()
    await db[svc.COLLECTION].update_one(
        {"id": request_id, "agency_id": agency_id},
        {"$set": data},
    )
    doc = await db[svc.COLLECTION].find_one({"id": request_id}, {"_id": 0})
    return doc


@router.delete("/{request_id}", status_code=204)
async def archive_request(
    request_id: str,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Soft-archive (status=archived) — no hard delete in v1."""
    agency_id = await _agency(user)
    db = Database.get()
    r = await db[svc.COLLECTION].update_one(
        {"id": request_id, "agency_id": agency_id},
        {"$set": {"status": "archived", "updated_at": _now()}},
    )
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="request_not_found")
    return Response(status_code=204)


@router.get("/{request_id}/matches")
async def request_matches(
    request_id: str,
    min_score: int = Query(50, ge=0, le=100),
    user: dict = Depends(get_current_user),
):
    agency_id = await _agency(user)
    db = Database.get()
    doc = await db[svc.COLLECTION].find_one(
        {"id": request_id, "agency_id": agency_id},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="request_not_found")
    result = await svc.match_request(db, agency_id, doc, min_score=min_score)
    return {
        "request_id": request_id,
        "min_score": min_score,
        **result,
    }


class ShareBody(BaseModel):
    mls_shared: bool = True


@router.post("/{request_id}/share")
async def set_mls_share(
    request_id: str,
    body: ShareBody,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    agency_id = await _agency(user)
    db = Database.get()
    r = await db[svc.COLLECTION].update_one(
        {"id": request_id, "agency_id": agency_id},
        {"$set": {"mls_shared": bool(body.mls_shared), "updated_at": _now()}},
    )
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="request_not_found")
    doc = await db[svc.COLLECTION].find_one({"id": request_id}, {"_id": 0})
    return doc
