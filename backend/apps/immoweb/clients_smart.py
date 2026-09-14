"""OMNIA — Smart Clients List (M2.S4+ D-FUTURE-04).

Editorial CRM view: enrich the clients list with per-client AI lead scoring
hints, sort by score desc, and let the agent see *who to call first*.

Endpoints (mounted under /app/clients):
  GET  /smart            → enriched list (deterministic match + cached AI)
  POST /smart/refresh    → batch-refresh AI lead score for top N uncached
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user, require_roles
from shared.db.connection import Database
from apps.immoweb.matching import compute_match, is_searcher
from apps.immoweb.lead_scoring import score_lead, _classify

logger = logging.getLogger("omnia.clients_smart")
router = APIRouter(prefix="/clients", tags=["clients-smart"])


SEARCHER_TYPES = {"buyer", "tenant", "investor"}
MATCH_COUNT_THRESHOLD = 50   # property is considered a "real" match for the counter


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


def _enrich_client(
    c: Dict[str, Any],
    properties: List[Dict[str, Any]],
    cache_index: Dict[tuple, Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute deterministic best match + matches_count for a client,
    overlaying any cached AI lead_score for the top property."""
    is_seller = not is_searcher(c)
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

    if is_seller or not properties:
        return {
            **base,
            "matches_count": 0,
            "best_match_score": None,
            "lead_score": None,
            "temperature": None,
            "top_property": None,
            "action_hint": _action_hint_fallback("freddo", 0, is_seller),
            "ai_engine": None,
            "ai_cached": False,
        }

    # deterministic match vs every property
    scored: List[tuple] = []
    for p in properties:
        m = compute_match(p, c)
        if m["score"] > 0:
            scored.append((m["score"], p, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    matches_count = sum(1 for s, *_ in scored if s >= MATCH_COUNT_THRESHOLD)

    if not scored:
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

    best_score, best_prop, best_match = scored[0]
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

    # no AI cache yet — use deterministic only for the score
    derived_temp = _classify(best_score)
    return {
        **base,
        "matches_count": matches_count,
        "best_match_score": best_score,
        "lead_score": best_score,   # deterministic acts as placeholder
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


# ============================================================
# GET /clients/smart
# ============================================================

@router.get("/smart")
async def smart_clients(
    sort: str = Query("score_desc", pattern="^(score_desc|score_asc|created_desc|name_asc)$"),
    bucket: Optional[str] = Query(None, pattern="^(rovente|caldo|tiepido|freddo|to_call_today|searchers|sellers|all)$"),
    q: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Enriched clients list with deterministic match + cached AI lead score."""
    agency_id = await _agency_id(user)
    db = Database.get()

    # 1. Pull clients (basic search filter)
    cl_query: Dict[str, Any] = {"agency_id": agency_id}
    if q:
        cl_query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"surname": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
            {"phone": {"$regex": q, "$options": "i"}},
        ]
    clients = await db.clients.find(cl_query, {"_id": 0}).to_list(length=2000)

    # 2. Pull all active+draft properties of the agency
    properties = await db.properties.find(
        {"agency_id": agency_id, "status": "active"}, {"_id": 0},
    ).to_list(length=2000)

    # 3. Pull lead_score_cache for this agency once → index by (property_id, client_id)
    cache_docs = await db.lead_score_cache.find(
        {"agency_id": agency_id}, {"_id": 0},
    ).to_list(length=20000)
    cache_index: Dict[tuple, Dict[str, Any]] = {
        (d["property_id"], d["client_id"]): d for d in cache_docs
    }

    # 4. Enrich once (used for both counts and filtered output)
    full_enriched = [_enrich_client(c, properties, cache_index) for c in clients]

    # 5. Counts for the UI pills (computed on the full set, pre-bucket)
    counts = {
        "all": len(full_enriched),
        "to_call_today": sum(1 for e in full_enriched if e.get("temperature") in ("rovente", "caldo") and (e.get("matches_count") or 0) > 0),
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

    # 6. Bucket filter (applied to a copy so counts remain global)
    enriched = list(full_enriched)
    if bucket == "to_call_today":
        enriched = [e for e in enriched if (e.get("temperature") in ("rovente", "caldo")) and (e.get("matches_count") or 0) > 0]
    elif bucket in ("rovente", "caldo", "tiepido", "freddo"):
        enriched = [e for e in enriched if e.get("temperature") == bucket]
    elif bucket == "searchers":
        enriched = [e for e in enriched if e.get("client_type") in SEARCHER_TYPES]
    elif bucket == "sellers":
        enriched = [e for e in enriched if e.get("client_type") not in SEARCHER_TYPES]
    # else "all" or None → no filter

    # 7. Sort
    if sort == "score_desc":
        enriched.sort(key=lambda e: (e.get("lead_score") or -1, e.get("matches_count") or 0), reverse=True)
    elif sort == "score_asc":
        enriched.sort(key=lambda e: (e.get("lead_score") or 9999, e.get("matches_count") or 0))
    elif sort == "created_desc":
        enriched.sort(key=lambda e: e.get("created_at") or "", reverse=True)
    elif sort == "name_asc":
        enriched.sort(key=lambda e: ((e.get("name") or "").lower(), (e.get("surname") or "").lower()))

    return {
        "items": enriched,
        "total": len(enriched),
        "counts": counts,
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
        {"agency_id": agency_id, "client_type": {"$in": list(SEARCHER_TYPES)}}, {"_id": 0},
    ).to_list(length=2000)
    properties = await db.properties.find(
        {"agency_id": agency_id, "status": "active"}, {"_id": 0},
    ).to_list(length=2000)
    if not clients or not properties:
        return {"refreshed": 0, "skipped": 0, "items": []}

    cache_docs = await db.lead_score_cache.find(
        {"agency_id": agency_id}, {"_id": 0, "property_id": 1, "client_id": 1},
    ).to_list(length=20000)
    cached_pairs = {(d["property_id"], d["client_id"]) for d in cache_docs}

    # Build pipeline: for each client → best match → if uncached, queue for AI
    pending: List[Dict[str, Any]] = []
    for c in clients:
        scored = []
        for p in properties:
            m = compute_match(p, c)
            if m["score"] > 0:
                scored.append((m["score"], p, m))
        if not scored:
            continue
        scored.sort(key=lambda x: x[0], reverse=True)
        best_score, best_prop, best_match = scored[0]
        if (best_prop["id"], c["id"]) in cached_pairs:
            continue
        pending.append({"client": c, "property": best_prop, "match": best_match, "score": best_score})
        if len(pending) >= limit:
            break

    if not pending:
        return {"refreshed": 0, "skipped": 0, "items": []}

    # Run AI in parallel (gemini-3-flash; ~1-2s each, capped by limit)
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
