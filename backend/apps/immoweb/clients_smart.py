"""OMNIA — Smart Clients List (M2.S4+ D-FUTURE-04).

Editorial CRM view: enrich the clients list with per-client AI lead scoring
hints, sort by score desc, and let the agent see *who to call first*.

Endpoints (mounted under /app/clients):
  GET  /smart            → enriched list (deterministic match + cached AI)
  POST /smart/refresh    → batch-refresh AI lead score for top N uncached

Scale notes (D-072 stress @10k):
  - page / page_size required for payload (default 50)
  - property match capped; score uses compute_match_score_fast
  - cheap Mongo counts for all / searchers / sellers
  - page-first path when score ranking is not needed
"""
import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user, require_roles
from shared.db.connection import Database
from apps.immoweb.matching import compute_match, compute_match_score_fast, is_searcher
from apps.immoweb.lead_scoring import score_lead, _classify

logger = logging.getLogger("omnia.clients_smart")
router = APIRouter(prefix="/clients", tags=["clients-smart"])


SEARCHER_TYPES = {"buyer", "tenant", "investor"}
MATCH_COUNT_THRESHOLD = 50   # property is considered a "real" match for the counter

PAGE_SIZE_DEFAULT = 50
PAGE_SIZE_MAX = 100
CLIENT_SCAN_CAP = 2000       # max clients scored for score/temp ranking
PROPERTY_MATCH_CAP = 200     # max active properties used for list matching

# Projection: only fields needed for matching + row display
_PROP_PROJ = {
    "_id": 0,
    "id": 1,
    "title": 1,
    "reference_code": 1,
    "city": 1,
    "zone": 1,
    "operation": 1,
    "property_type": 1,
    "price": 1,
    "rent_monthly": 1,
    "surface_sqm": 1,
    "rooms": 1,
    "bedrooms": 1,
    "bathrooms": 1,
    "condition": 1,
    "floor": 1,
    "total_floors": 1,
    "energy": 1,
    "features": 1,
    "photos": 1,
    "virtual_tour_url": 1,
    "updated_at": 1,
}

_CLIENT_PROJ = {
    "_id": 0,
    "id": 1,
    "name": 1,
    "surname": 1,
    "email": 1,
    "phone": 1,
    "whatsapp": 1,
    "client_type": 1,
    "status": 1,
    "source": 1,
    "preferences": 1,
    "gdpr_consent": 1,
    "created_at": 1,
    "updated_at": 1,
}


# ============================================================
# Helpers
# ============================================================

from shared.auth.tenant import arequire_agency as _agency_id


def _action_hint_fallback(temperature: str, matches_count: int, is_seller: bool) -> str:
    """Short Italian action hint used when no AI cache is available."""
    if is_seller:
        return "Venditore: nessun matching automatico."
    if matches_count == 0:
        return "Profilo da scaldare: nessun match al momento, invia una selezione curata."
    if temperature == "rovente":
        return f"Chiama oggi: {matches_count} immobili compatibili pronti da inviare."
    if temperature == "caldo":
        return f"Invia in giornata i {matches_count} match disponibili."
    if temperature == "tiepido":
        return "Aggiorna preferenze del cliente e poi proponi una shortlist."
    return "Riqualifica via mail breve, poi decidi se archiviare."


def _escape_q(q: Optional[str]) -> Optional[str]:
    if not q:
        return None
    q = q.strip()[:100]
    if not q:
        return None
    return re.escape(q)


def _client_base_query(agency_id: str, q: Optional[str]) -> Dict[str, Any]:
    cl_query: Dict[str, Any] = {"agency_id": agency_id}
    eq = _escape_q(q)
    if eq:
        cl_query["$or"] = [
            {"name": {"$regex": eq, "$options": "i"}},
            {"surname": {"$regex": eq, "$options": "i"}},
            {"email": {"$regex": eq, "$options": "i"}},
            {"phone": {"$regex": eq, "$options": "i"}},
        ]
    return cl_query


def _enrich_client(
    c: Dict[str, Any],
    properties: List[Dict[str, Any]],
    cache_index: Dict[tuple, Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute deterministic best match + matches_count for a client,
    overlaying any cached AI lead_score for the top property."""
    seller = not is_searcher(c)
    base = {
        "id": c["id"],
        "name": c.get("name"),
        "surname": c.get("surname"),
        "email": c.get("email"),
        "phone": c.get("phone"),
        "whatsapp": c.get("whatsapp"),
        "client_type": c.get("client_type"),
        "status": c.get("status"),
        "source": c.get("source"),
        "preferences": c.get("preferences"),
        "gdpr_consent": bool(c.get("gdpr_consent")),
        "created_at": c.get("created_at"),
        "updated_at": c.get("updated_at"),
    }

    if seller or not properties:
        return {
            **base,
            "matches_count": 0,
            "best_match_score": None,
            "lead_score": None,
            "temperature": None,
            "top_property": None,
            "action_hint": _action_hint_fallback("freddo", 0, seller),
            "ai_engine": None,
            "ai_cached": False,
        }

    prefs = c.get("preferences") if isinstance(c.get("preferences"), dict) else {}
    best_score = 0
    best_prop: Optional[Dict[str, Any]] = None
    matches_count = 0
    for p in properties:
        s = compute_match_score_fast(p, prefs)
        if s <= 0:
            continue
        if s >= MATCH_COUNT_THRESHOLD:
            matches_count += 1
        if s > best_score:
            best_score = s
            best_prop = p

    if not best_prop:
        return {
            **base,
            "matches_count": 0,
            "best_match_score": 0,
            "lead_score": 0,
            "temperature": "freddo",
            "top_property": None,
            "action_hint": _action_hint_fallback("freddo", 0, False),
            "ai_engine": None,
            "ai_cached": False,
        }

    cache_key = (best_prop["id"], c["id"])
    cached = cache_index.get(cache_key)

    if cached:
        ls = cached.get("lead_score") or {}
        ai_score = int(ls.get("score") or 0)
        ai_temp = ls.get("temperature") or _classify(ai_score)
        action_hint = ls.get("action_hint") or _action_hint_fallback(ai_temp, matches_count, False)
        ai_engine = ls.get("engine")
        return {
            **base,
            "matches_count": matches_count,
            "best_match_score": best_score,
            "lead_score": ai_score,
            "temperature": ai_temp,
            "top_property": {
                "id": best_prop["id"],
                "title": best_prop.get("title"),
                "reference_code": best_prop.get("reference_code"),
                "city": best_prop.get("city"),
            },
            "action_hint": action_hint,
            "ai_engine": ai_engine,
            "ai_cached": True,
        }

    derived_temp = _classify(best_score)
    return {
        **base,
        "matches_count": matches_count,
        "best_match_score": best_score,
        "lead_score": best_score,
        "temperature": derived_temp,
        "top_property": {
            "id": best_prop["id"],
            "title": best_prop.get("title"),
            "reference_code": best_prop.get("reference_code"),
            "city": best_prop.get("city"),
        },
        "action_hint": _action_hint_fallback(derived_temp, matches_count, False),
        "ai_engine": None,
        "ai_cached": False,
    }


def _apply_bucket(enriched: List[Dict[str, Any]], bucket: Optional[str]) -> List[Dict[str, Any]]:
    if bucket == "to_call_today":
        return [
            e for e in enriched
            if (e.get("temperature") in ("rovente", "caldo")) and (e.get("matches_count") or 0) > 0
        ]
    if bucket in ("rovente", "caldo", "tiepido", "freddo"):
        return [e for e in enriched if e.get("temperature") == bucket]
    if bucket == "searchers":
        return [e for e in enriched if e.get("client_type") in SEARCHER_TYPES]
    if bucket == "sellers":
        return [e for e in enriched if e.get("client_type") not in SEARCHER_TYPES]
    return enriched


def _sort_enriched(enriched: List[Dict[str, Any]], sort: str) -> None:
    if sort == "score_desc":
        enriched.sort(key=lambda e: (e.get("lead_score") or -1, e.get("matches_count") or 0), reverse=True)
    elif sort == "score_asc":
        enriched.sort(key=lambda e: (e.get("lead_score") or 9999, e.get("matches_count") or 0))
    elif sort == "created_desc":
        enriched.sort(key=lambda e: e.get("created_at") or "", reverse=True)
    elif sort == "name_asc":
        enriched.sort(key=lambda e: ((e.get("name") or "").lower(), (e.get("surname") or "").lower()))


def _counts_from_enriched(full_enriched: List[Dict[str, Any]]) -> Dict[str, int]:
    return {
        "all": len(full_enriched),
        "to_call_today": sum(
            1 for e in full_enriched
            if e.get("temperature") in ("rovente", "caldo") and (e.get("matches_count") or 0) > 0
        ),
        "rovente": sum(1 for e in full_enriched if e.get("temperature") == "rovente"),
        "caldo": sum(1 for e in full_enriched if e.get("temperature") == "caldo"),
        "tiepido": sum(1 for e in full_enriched if e.get("temperature") == "tiepido"),
        "freddo": sum(1 for e in full_enriched if e.get("temperature") == "freddo"),
        "searchers": sum(1 for e in full_enriched if e.get("client_type") in SEARCHER_TYPES),
        "sellers": sum(1 for e in full_enriched if e.get("client_type") not in SEARCHER_TYPES),
        "ai_cached": sum(1 for e in full_enriched if e.get("ai_cached")),
        "ai_uncached_searchers": sum(
            1 for e in full_enriched
            if e.get("client_type") in SEARCHER_TYPES
            and not e.get("ai_cached")
            and (e.get("matches_count") or 0) > 0
        ),
    }


async def _mongo_type_counts(db, agency_id: str, base_q: Dict[str, Any]) -> Tuple[int, int, int]:
    """Exact all / searchers / sellers via Mongo (no enrich)."""
    all_n = await db.clients.count_documents(base_q)
    searchers_q = {**base_q, "client_type": {"$in": list(SEARCHER_TYPES)}}
    # If base_q already has client_type from bucket prefilter, count_documents still works
    searchers_n = await db.clients.count_documents(searchers_q)
    sellers_n = max(0, all_n - searchers_n)
    return all_n, searchers_n, sellers_n


def _needs_score_scan(sort: str, bucket: Optional[str]) -> bool:
    """True when we must enrich a scan window before paging."""
    if sort in ("score_desc", "score_asc"):
        return True
    if bucket in ("rovente", "caldo", "tiepido", "freddo", "to_call_today"):
        return True
    return False


# ============================================================
# GET /clients/smart
# ============================================================

@router.get("/smart")
async def smart_clients(
    sort: str = Query("score_desc", pattern="^(score_desc|score_asc|created_desc|name_asc)$"),
    bucket: Optional[str] = Query(None, pattern="^(rovente|caldo|tiepido|freddo|to_call_today|searchers|sellers|all)$"),
    q: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(PAGE_SIZE_DEFAULT, ge=1, le=PAGE_SIZE_MAX),
    # legacy alias used by stress script / older clients
    limit: Optional[int] = Query(None, ge=1, le=PAGE_SIZE_MAX),
    user: dict = Depends(get_current_user),
):
    """Enriched clients list with deterministic match + cached AI lead score.

    Paginated: `items` is one page; `total` is the filtered set size.
    Temperature bucket counts are computed on the scored scan window
    (capped at CLIENT_SCAN_CAP); all/searchers/sellers are exact Mongo counts
    when the query is not already narrowed to a temp bucket.
    """
    if limit is not None:
        page_size = limit

    agency_id = await _agency_id(user)
    db = Database.get()
    base_q = _client_base_query(agency_id, q)

    # Properties once (capped, projected, newest first)
    properties = await db.properties.find(
        {"agency_id": agency_id, "status": "active"},
        _PROP_PROJ,
    ).sort("updated_at", -1).to_list(length=PROPERTY_MATCH_CAP)

    # Lead score cache (agency-scoped)
    cache_docs = await db.lead_score_cache.find(
        {"agency_id": agency_id}, {"_id": 0},
    ).to_list(length=20000)
    cache_index: Dict[tuple, Dict[str, Any]] = {
        (d["property_id"], d["client_id"]): d for d in cache_docs
    }

    bkt = bucket if bucket and bucket != "all" else None
    skip = (page - 1) * page_size

    # ---- Page-first path (no score ranking needed) ----
    if not _needs_score_scan(sort, bkt):
        mongo_q = dict(base_q)
        if bkt == "searchers":
            mongo_q["client_type"] = {"$in": list(SEARCHER_TYPES)}
        elif bkt == "sellers":
            mongo_q["client_type"] = {"$nin": list(SEARCHER_TYPES)}

        total = await db.clients.count_documents(mongo_q)
        mongo_sort = [("created_at", -1)] if sort == "created_desc" else [("name", 1), ("surname", 1)]
        page_clients = await (
            db.clients.find(mongo_q, _CLIENT_PROJ)
            .sort(mongo_sort)
            .skip(skip)
            .limit(page_size)
            .to_list(length=page_size)
        )
        items = [_enrich_client(c, properties, cache_index) for c in page_clients]

        all_n, searchers_n, sellers_n = await _mongo_type_counts(db, agency_id, base_q)
        # Temp / AI counts need a score scan — omit numbers here (FE hides non-numbers).
        # Switching to score sort or a temperature bucket triggers the scored path.
        counts = {
            "all": all_n,
            "searchers": searchers_n,
            "sellers": sellers_n,
        }
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "counts": counts,
            "counts_scope": "mongo_types",
            "scanned": len(page_clients),
            "properties_matched": len(properties),
            "sort": sort,
            "bucket": bucket or "all",
        }

    # ---- Score / temperature path: scan → enrich → filter → sort → page ----
    scan_q = dict(base_q)
    # Temp buckets + score ranking: prefer searchers (sellers have no score).
    if bkt in ("rovente", "caldo", "tiepido", "freddo", "to_call_today", "searchers"):
        scan_q["client_type"] = {"$in": list(SEARCHER_TYPES)}
        clients = await db.clients.find(scan_q, _CLIENT_PROJ).to_list(length=CLIENT_SCAN_CAP)
    elif bkt == "sellers":
        scan_q["client_type"] = {"$nin": list(SEARCHER_TYPES)}
        clients = await db.clients.find(scan_q, _CLIENT_PROJ).to_list(length=CLIENT_SCAN_CAP)
    elif sort in ("score_desc", "score_asc"):
        # Score ranking: fill scan with searchers first (they dominate the top).
        searchers = await db.clients.find(
            {**base_q, "client_type": {"$in": list(SEARCHER_TYPES)}},
            _CLIENT_PROJ,
        ).to_list(length=CLIENT_SCAN_CAP)
        remaining = max(0, CLIENT_SCAN_CAP - len(searchers))
        sellers = []
        if remaining:
            sellers = await db.clients.find(
                {**base_q, "client_type": {"$nin": list(SEARCHER_TYPES)}},
                _CLIENT_PROJ,
            ).to_list(length=remaining)
        clients = searchers + sellers
    else:
        clients = await db.clients.find(scan_q, _CLIENT_PROJ).to_list(length=CLIENT_SCAN_CAP)

    full_enriched = [_enrich_client(c, properties, cache_index) for c in clients]

    # Counts: merge Mongo type totals with temp from scan when scan is unfiltered-ish
    all_n, searchers_n, sellers_n = await _mongo_type_counts(db, agency_id, base_q)
    scanned_counts = _counts_from_enriched(full_enriched)
    if bkt in ("rovente", "caldo", "tiepido", "freddo", "to_call_today", "searchers"):
        # full_enriched is searchers-only — keep temp from scan; types from mongo
        counts = {
            "all": all_n,
            "searchers": searchers_n,
            "sellers": sellers_n,
            "to_call_today": scanned_counts["to_call_today"],
            "rovente": scanned_counts["rovente"],
            "caldo": scanned_counts["caldo"],
            "tiepido": scanned_counts["tiepido"],
            "freddo": scanned_counts["freddo"],
            "ai_cached": scanned_counts["ai_cached"],
            "ai_uncached_searchers": scanned_counts["ai_uncached_searchers"],
        }
    elif bkt == "sellers":
        counts = {
            "all": all_n,
            "searchers": searchers_n,
            "sellers": sellers_n,
            "to_call_today": 0,
            "rovente": 0,
            "caldo": 0,
            "tiepido": 0,
            "freddo": 0,
            "ai_cached": 0,
            "ai_uncached_searchers": 0,
        }
    else:
        # scanned mixed set — use scanned temp; prefer mongo for type totals
        counts = {
            **scanned_counts,
            "all": all_n,
            "searchers": searchers_n,
            "sellers": sellers_n,
        }

    enriched = _apply_bucket(full_enriched, bkt)
    _sort_enriched(enriched, sort)
    total = len(enriched)
    items = enriched[skip: skip + page_size]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "counts": counts,
        "counts_scope": "scanned",
        "scanned": len(clients),
        "properties_matched": len(properties),
        "sort": sort,
        "bucket": bucket or "all",
    }


# ============================================================
# POST /clients/smart/refresh
# ============================================================

class RefreshRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=50)


@router.post("/smart/refresh")
async def refresh_smart_scores(
    payload: Optional[RefreshRequest] = None,
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    """Trigger AI lead scoring for the next N uncached searcher clients
    (best deterministic match first). Honors 24h cache; runs in parallel."""
    limit = (payload or RefreshRequest()).limit
    agency_id = await _agency_id(user)
    db = Database.get()

    clients = await db.clients.find(
        {"agency_id": agency_id, "client_type": {"$in": list(SEARCHER_TYPES)}},
        _CLIENT_PROJ,
    ).to_list(length=CLIENT_SCAN_CAP)
    properties = await db.properties.find(
        {"agency_id": agency_id, "status": "active"},
        _PROP_PROJ,
    ).sort("updated_at", -1).to_list(length=PROPERTY_MATCH_CAP)
    if not clients or not properties:
        return {"refreshed": 0, "skipped": 0, "items": []}

    cache_docs = await db.lead_score_cache.find(
        {"agency_id": agency_id}, {"_id": 0, "property_id": 1, "client_id": 1},
    ).to_list(length=20000)
    cached_pairs = {(d["property_id"], d["client_id"]) for d in cache_docs}

    pending: List[Dict[str, Any]] = []
    for c in clients:
        prefs = c.get("preferences") if isinstance(c.get("preferences"), dict) else {}
        best_score = 0
        best_prop = None
        best_match = None
        for p in properties:
            s = compute_match_score_fast(p, prefs)
            if s <= 0:
                continue
            if s > best_score:
                best_score = s
                best_prop = p
        if not best_prop:
            continue
        if (best_prop["id"], c["id"]) in cached_pairs:
            continue
        # Full match only for the winner (AI needs breakdown)
        best_match = compute_match(best_prop, c)
        pending.append({"client": c, "property": best_prop, "match": best_match, "score": best_score})
        if len(pending) >= limit:
            break

    if not pending:
        return {"refreshed": 0, "skipped": 0, "items": []}

    async def _score_one(item: Dict[str, Any]) -> Dict[str, Any]:
        try:
            ai = await score_lead(item["client"], item["property"], item["match"])
            now = datetime.now(timezone.utc)
            await db.lead_score_cache.update_one(
                {"agency_id": agency_id, "property_id": item["property"]["id"], "client_id": item["client"]["id"]},
                {"$set": {
                    "agency_id": agency_id,
                    "property_id": item["property"]["id"],
                    "client_id": item["client"]["id"],
                    "lead_score": ai,
                    "cached_at": now,
                }},
                upsert=True,
            )
            return {
                "client_id": item["client"]["id"],
                "property_id": item["property"]["id"],
                "score": ai.get("score"),
                "temperature": ai.get("temperature"),
                "engine": ai.get("engine"),
            }
        except Exception as e:
            logger.warning("score_lead failed for client=%s prop=%s: %s",
                           item["client"]["id"], item["property"]["id"], e)
            return {"client_id": item["client"]["id"], "error": type(e).__name__}

    results = await asyncio.gather(*(_score_one(it) for it in pending))
    refreshed = sum(1 for r in results if "error" not in r)
    return {
        "refreshed": refreshed,
        "skipped": len(pending) - refreshed,
        "items": results,
    }
