"""Match annunci privati B2C → richieste CRM di tutte le agenzie.

Decisione Founder (19-Ott-2026): il sistema legge l'annuncio privato e lo
matcha alle richieste agenzia **indipendentemente** da `mls_shared`.
I privati restano fuori dall'inventario MLS generico; questo è un canale
parallelo (scope `portal`).
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from shared.db.connection import Database
from apps.immoweb import client_requests_service as svc
from apps.immoweb.matching import (
    compute_match_score_fast,
    prefs_with_tolerance,
    resolve_tolerances,
)

logger = logging.getLogger("omnia.private_listing_matching")

NOTIF_COLLECTION = "request_match_notifications"
PORTAL_SCAN_CAP = 300
REQUEST_SCAN_CAP = 2000
MAX_LISTINGS_PER_RUN = 200
MAX_ALERTS_PER_LISTING = 30


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def private_portal_listing_query() -> Dict[str, Any]:
    """Annunci privati live sul portale (non inventario MLS)."""
    from shared.db.trash import with_not_trashed
    return with_not_trashed({
        "is_private_listing": True,
        "status": "active",
        "moderation_status": "approved",
    })


async def match_private_listing_to_requests(
    db,
    prop: Dict[str, Any],
    *,
    min_score: Optional[int] = None,
    limit: int = MAX_ALERTS_PER_LISTING,
) -> List[Dict[str, Any]]:
    """Scoring: un immobile privato → richieste aperte di *tutte* le agenzie.

    Include richieste con `mls_shared` true **e** false.
    """
    is_private = bool(prop.get("is_private_listing")) or prop.get("agency_id") == "_private_listings"
    if not is_private:
        return []

    p = svc._normalize_prop_for_match(prop)
    default_threshold = int(min_score if min_score is not None else svc.MATCH_THRESHOLD)

    reqs = await db[svc.COLLECTION].find(
        {
            "status": {"$in": ["open", "matched", "negotiating"]},
            "auto_match": {"$ne": False},
        },
        {"_id": 0},
    ).sort("updated_at", -1).to_list(length=REQUEST_SCAN_CAP)

    results: List[Dict[str, Any]] = []
    for req in reqs:
        if req.get("request_type") == "property_interest" and req.get("property_id"):
            if req["property_id"] != p.get("id"):
                continue
            score = 90
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
            if score < int(tol.get("min_score") or default_threshold):
                continue

        results.append({
            "request_id": req.get("id"),
            "client_id": req.get("client_id"),
            "agency_id": req.get("agency_id"),
            "title": req.get("title"),
            "request_type": req.get("request_type"),
            "source": req.get("source"),
            "mls_shared": bool(req.get("mls_shared")),
            "assigned_agent_id": req.get("assigned_agent_id"),
            "score": score,
            "scope": "portal",
            "property_id": p.get("id"),
            "property_title": p.get("title"),
            "property_city": p.get("city"),
            "property_price": p.get("price") or p.get("rent_monthly"),
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:limit]


async def _already_notified(db, request_id: str, property_id: str) -> bool:
    hit = await db[NOTIF_COLLECTION].find_one(
        {"request_id": request_id, "property_id": property_id},
        {"_id": 1},
    )
    return bool(hit)


async def _mark_notified(
    db,
    *,
    agency_id: str,
    request_id: str,
    property_id: str,
    client_id: str,
    score: int,
) -> None:
    await db[NOTIF_COLLECTION].update_one(
        {"request_id": request_id, "property_id": property_id},
        {"$set": {
            "id": str(uuid4()),
            "agency_id": agency_id,
            "request_id": request_id,
            "property_id": property_id,
            "client_id": client_id,
            "score": score,
            "channel": "inbox_portal",
            "scope": "portal",
            "notified_at": _now(),
        }},
        upsert=True,
    )


async def _notify_agency_portal_match(
    db,
    *,
    agency_id: str,
    req: Dict[str, Any],
    hit: Dict[str, Any],
) -> None:
    try:
        from shared.notifications.center import (
            TYPE_LEAD_NEW,
            notify_users,
            resolve_agency_owner_and_admins,
        )
        recipients = await resolve_agency_owner_and_admins(agency_id)
        agent = req.get("assigned_agent_id") or hit.get("assigned_agent_id")
        if agent:
            recipients = list({*recipients, agent})
        title = hit.get("property_title") or "Annuncio privato"
        city = hit.get("property_city") or ""
        score = hit.get("score")
        await notify_users(
            recipients,
            type=TYPE_LEAD_NEW,
            title=f"Match portale · {title}",
            body=(
                f"Annuncio privato compatibile con «{req.get('title') or req.get('id')}»"
                f"{f' · {city}' if city else ''} · score {score}/100."
            ),
            link="/app/requests/" + str(req.get("id") or ""),
            agency_id=agency_id,
            meta={
                "request_id": req.get("id"),
                "property_id": hit.get("property_id"),
                "score": score,
                "scope": "portal",
            },
        )
    except Exception as e:  # noqa: BLE001
        logger.warning("portal match inbox failed agency=%s: %s", agency_id, e)


async def process_private_listing_matches(
    db,
    prop: Dict[str, Any],
    *,
    min_score: Optional[int] = None,
) -> Dict[str, Any]:
    """Match + alert agenzie (dedup). Nessuna email al cliente CRM sul privato."""
    hits = await match_private_listing_to_requests(db, prop, min_score=min_score)
    fresh = 0
    notified = 0
    for hit in hits:
        rid = hit.get("request_id")
        pid = hit.get("property_id")
        aid = hit.get("agency_id")
        if not rid or not pid or not aid:
            continue
        if await _already_notified(db, rid, pid):
            continue
        fresh += 1
        req = {
            "id": rid,
            "title": hit.get("title"),
            "assigned_agent_id": hit.get("assigned_agent_id"),
        }
        await _notify_agency_portal_match(db, agency_id=aid, req=req, hit=hit)
        await _mark_notified(
            db,
            agency_id=aid,
            request_id=rid,
            property_id=pid,
            client_id=hit.get("client_id") or "",
            score=int(hit.get("score") or 0),
        )
        notified += 1
        # Promote request status if still open
        await db[svc.COLLECTION].update_one(
            {"id": rid, "status": "open"},
            {"$set": {"status": "matched", "updated_at": _now()}},
        )
    return {
        "property_id": prop.get("id"),
        "hits": len(hits),
        "new": fresh,
        "notified": notified,
    }


async def run_private_listing_request_matching(
    *,
    property_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Job: scansiona annunci privati attivi e matcha le richieste agenzia."""
    db = Database.get()
    await svc.ensure_indexes(db)
    await db[NOTIF_COLLECTION].create_index(
        [("request_id", 1), ("property_id", 1)], unique=True,
    )

    q = private_portal_listing_query()
    if property_id:
        q = {"$and": [q, {"id": property_id}]}

    props = await db.properties.find(
        q,
        {**svc._PROP_PROJ, "is_private_listing": 1, "owner_user_id": 1, "moderation_status": 1},
    ).sort("updated_at", -1).to_list(length=MAX_LISTINGS_PER_RUN)

    processed = 0
    with_new = 0
    notified_total = 0
    errors = 0
    for prop in props:
        try:
            r = await process_private_listing_matches(db, prop)
            processed += 1
            if r.get("new"):
                with_new += 1
            notified_total += int(r.get("notified") or 0)
        except Exception as e:  # noqa: BLE001
            errors += 1
            logger.warning("private listing match failed %s: %s", prop.get("id"), e)

    return {
        "ok": True,
        "scanned": len(props),
        "processed": processed,
        "with_new_matches": with_new,
        "notified": notified_total,
        "errors": errors,
    }
