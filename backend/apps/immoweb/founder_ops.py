"""Founder Ops — cruscotto costi/consumi (solo super_admin).

Aggrega i principali centri di costo OMNIA:
  HAL Agents, Guida HAL, HAL Legal, Virtual Staging, Micro-tour,
  API Track B (crediti), wallet crediti agenzie.

Stime COGS = ordini di grandezza (non fatture provider).
Politica (D-075/D-076): AI in-app inclusa; crediti = API/overage/B2C.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

from shared.auth.dependencies import require_roles
from shared.db.connection import Database

logger = logging.getLogger("omnia.founder_ops")
router = APIRouter(prefix="/ops", tags=["founder-ops"])

# --- Assunzioni COGS (€) -------------------------------------------------
EUR_PER_CREDIT_LIST = 0.05  # listino Track A
EUR_HAL_AGENTS = 0.005
EUR_HAL_IMPROVE = 0.005
EUR_HAL_KNOWLEDGE = 0.002
EUR_HAL_LEGAL_GEMINI = 0.01
EUR_TAVILY_PER_CREDIT = 0.0074
TAVILY_CREDITS_PER_LEGAL = 2
TAVILY_FREE_MONTH = 1000
EUR_STAGING_JOB = 0.056
EUR_MICRO_TOUR = 0.88


def _since(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()


def _month_start() -> str:
    return datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).isoformat()


async def _count(db, coll: str, match: dict) -> int:
    try:
        return int(await db[coll].count_documents(match))
    except Exception:
        logger.exception("count failed %s", coll)
        return 0


def _money_row(
    *,
    key: str,
    label: str,
    channel: str,
    events: int,
    unit_cogs_eur: Optional[float],
    cogs_eur: Optional[float],
    list_credits_unit: int,
    revenue_eur: float,
    revenue_source: str,
    note: str,
) -> Dict[str, Any]:
    """Una riga P&L: costi, incassi, margine (attuale e a listino)."""
    list_eur = round(events * list_credits_unit * EUR_PER_CREDIT_LIST, 2) if list_credits_unit else 0.0
    cogs = None if cogs_eur is None else round(float(cogs_eur), 2)
    rev = round(float(revenue_eur or 0), 2)
    margin = None if cogs is None else round(rev - cogs, 2)
    margin_listed = None if cogs is None else round(list_eur - cogs, 2)
    return {
        "key": key,
        "label": label,
        "channel": channel,
        "events": events,
        "unit_cogs_eur": unit_cogs_eur,
        "cogs_eur": cogs,
        "list_credits": list_credits_unit,
        "list_eur": list_eur,
        "revenue_eur": rev,
        "revenue_source": revenue_source,
        "margin_eur": margin,
        "margin_if_listed_eur": margin_listed,
        "note": note,
    }


@router.get("/overview")
async def ops_overview(
    days: int = 30,
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    """Hub Founder: tutti i consumi e stime costi."""
    days = max(1, min(int(days or 30), 90))
    db = Database.get()
    since = _since(days)
    month_start = _month_start()
    tavily_on = bool(os.environ.get("TAVILY_API_KEY"))
    llm_on = bool(
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("EMERGENT_LLM_KEY")
    )

    # --- Volume per servizio --------------------------------------------
    al_chat = await _count(db, "al_audit", {"ts": {"$gte": since}, "kind": {"$exists": False}})
    # chat rows historically without kind; also count explicit chat if any
    al_chat_alt = await _count(db, "al_audit", {"ts": {"$gte": since}, "kind": "chat"})
    al_chat = max(al_chat, al_chat_alt)
    # Prefer: all al_audit minus improve = chat-ish, plus improve separate
    al_all = await _count(db, "al_audit", {"ts": {"$gte": since}})
    al_improve = await _count(db, "al_audit", {"ts": {"$gte": since}, "kind": "improve"})
    al_chat = max(0, al_all - al_improve) if al_all else al_chat

    knowledge = await _count(db, "hal_knowledge_sessions", {"created_at": {"$gte": since}})
    legal = await _count(db, "al_legal_audit", {"ts": {"$gte": since}})
    legal_month = await _count(db, "al_legal_audit", {"ts": {"$gte": month_start}})
    staging = await _count(db, "virtual_staging_jobs", {"created_at": {"$gte": since}})
    videos = await _count(db, "videos", {"created_at": {"$gte": since}})

    # API usage
    api_calls = 0
    api_credits = 0
    api_by_endpoint: List[Dict[str, Any]] = []
    try:
        api_rows = await db.api_usage_log.aggregate([
            {"$match": {"created_at": {"$gte": since}}},
            {"$group": {
                "_id": "$endpoint",
                "calls": {"$sum": 1},
                "credits": {"$sum": {"$ifNull": ["$credits_charged", 0]}},
            }},
            {"$sort": {"credits": -1}},
            {"$limit": 20},
        ]).to_list(20)
        for r in api_rows:
            api_calls += int(r.get("calls") or 0)
            api_credits += int(r.get("credits") or 0)
            api_by_endpoint.append({
                "endpoint": r.get("_id") or "—",
                "calls": int(r.get("calls") or 0),
                "credits": int(r.get("credits") or 0),
                "list_eur": round(int(r.get("credits") or 0) * EUR_PER_CREDIT_LIST, 2),
            })
    except Exception:
        logger.exception("api_usage aggregate failed")

    # Video credits charged (if field present)
    video_credits = 0
    try:
        vrows = await db.videos.aggregate([
            {"$match": {"created_at": {"$gte": since}}},
            {"$group": {"_id": None, "credits": {"$sum": {"$ifNull": ["$credits_charged", 0]}}}},
        ]).to_list(1)
        if vrows:
            video_credits = int(vrows[0].get("credits") or 0)
    except Exception:
        pass

    # Agency wallets
    wallet_balance = 0
    agencies_with_credits = 0
    try:
        wrows = await db.agencies.aggregate([
            {"$group": {
                "_id": None,
                "balance": {"$sum": {"$ifNull": ["$credits_balance", 0]}},
                "with_credits": {"$sum": {"$cond": [{"$gt": [{"$ifNull": ["$credits_balance", 0]}, 0]}, 1, 0]}},
            }},
        ]).to_list(1)
        if wrows:
            wallet_balance = int(wrows[0].get("balance") or 0)
            agencies_with_credits = int(wrows[0].get("with_credits") or 0)
    except Exception:
        pass

    # Credit ledger / transactions if present
    credit_delta = 0
    try:
        trows = await db.credit_transactions.aggregate([
            {"$match": {"created_at": {"$gte": since}}},
            {"$group": {"_id": None, "delta": {"$sum": {"$ifNull": ["$delta", 0]}}}},
        ]).to_list(1)
        if trows:
            credit_delta = int(trows[0].get("delta") or 0)
    except Exception:
        pass

    # B2C purchases (carta) — se presenti
    b2c_revenue = 0.0
    b2c_by_product: Dict[str, float] = {}
    try:
        brows = await db.b2c_purchases.aggregate([
            {"$match": {"created_at": {"$gte": since}, "status": {"$in": ["paid", "complete", "completed", "succeeded"]}}},
            {"$group": {
                "_id": "$product_key",
                "eur": {"$sum": {"$ifNull": ["$amount_eur", {"$ifNull": ["$price_eur", 0]}]}},
                "n": {"$sum": 1},
            }},
        ]).to_list(50)
        for r in brows:
            pk = r.get("_id") or "other"
            eur = float(r.get("eur") or 0)
            b2c_by_product[pk] = eur
            b2c_revenue += eur
    except Exception:
        pass

    # Payment transactions (subscription / credits topup) — ricavi piattaforma
    payments_revenue = 0.0
    try:
        prows = await db.payment_transactions.aggregate([
            {"$match": {
                "created_at": {"$gte": since},
                "payment_status": {"$in": ["paid", "complete", "completed", "succeeded"]},
            }},
            {"$group": {"_id": "$kind", "eur": {"$sum": {"$ifNull": ["$amount_eur", {"$ifNull": ["$amount", 0]}]}}}},
        ]).to_list(20)
        for r in prows:
            payments_revenue += float(r.get("eur") or 0)
    except Exception:
        pass

    # API legal credits separately for legal revenue attribution
    api_legal_credits = 0
    for e in api_by_endpoint:
        ep = (e.get("endpoint") or "").lower()
        if "legal" in ep:
            api_legal_credits += int(e.get("credits") or 0)

    legal_cogs = round(
        legal * EUR_HAL_LEGAL_GEMINI
        + legal * (TAVILY_CREDITS_PER_LEGAL * EUR_TAVILY_PER_CREDIT if tavily_on else 0),
        2,
    )
    legal_revenue = round(
        api_legal_credits * EUR_PER_CREDIT_LIST
        + float(b2c_by_product.get("b2c_hal_legal_query") or 0),
        2,
    )
    staging_revenue = round(
        float(b2c_by_product.get("b2c_staging_render") or 0),
        2,
    )
    # Se in futuro staging scala crediti agenzia, somma qui da ledger
    video_revenue = round(video_credits * EUR_PER_CREDIT_LIST, 2)
    # Evita doppio conteggio: i crediti legal restano sulla riga HAL Legal
    api_revenue = round(max(0, api_credits - api_legal_credits) * EUR_PER_CREDIT_LIST, 2)

    services = [
        _money_row(
            key="hal_agents",
            label="HAL Assistente CRM",
            channel="in_app_incluso",
            events=al_chat,
            unit_cogs_eur=EUR_HAL_AGENTS,
            cogs_eur=al_chat * EUR_HAL_AGENTS,
            list_credits_unit=4,
            revenue_eur=0.0,
            revenue_source="incluso_abbonamento",
            note="Costo operativo; ricavo nel piano, non a consumo",
        ),
        _money_row(
            key="hal_improve",
            label="HAL Migliora testo",
            channel="in_app_incluso",
            events=al_improve,
            unit_cogs_eur=EUR_HAL_IMPROVE,
            cogs_eur=al_improve * EUR_HAL_IMPROVE,
            list_credits_unit=0,
            revenue_eur=0.0,
            revenue_source="incluso_abbonamento",
            note="Costo operativo; ricavo nel piano",
        ),
        _money_row(
            key="hal_knowledge",
            label="Guida HAL",
            channel="in_app_incluso",
            events=knowledge,
            unit_cogs_eur=EUR_HAL_KNOWLEDGE,
            cogs_eur=knowledge * EUR_HAL_KNOWLEDGE,
            list_credits_unit=0,
            revenue_eur=0.0,
            revenue_source="incluso_abbonamento",
            note="Costo operativo; ricavo nel piano",
        ),
        _money_row(
            key="hal_legal",
            label="HAL Legal",
            channel="misto",
            events=legal,
            unit_cogs_eur=round(
                EUR_HAL_LEGAL_GEMINI + (TAVILY_CREDITS_PER_LEGAL * EUR_TAVILY_PER_CREDIT if tavily_on else 0),
                4,
            ),
            cogs_eur=legal_cogs,
            list_credits_unit=12,
            revenue_eur=legal_revenue,
            revenue_source="api_crediti+b2c",
            note="In-app incluso; incassi = API legal + B2C legal",
        ),
        _money_row(
            key="virtual_staging",
            label="Virtual Staging",
            channel="crediti",
            events=staging,
            unit_cogs_eur=EUR_STAGING_JOB,
            cogs_eur=staging * EUR_STAGING_JOB,
            list_credits_unit=18,
            revenue_eur=staging_revenue,
            revenue_source="crediti+b2c",
            note="Incassi quando scalati crediti / B2C staging",
        ),
        _money_row(
            key="micro_tour",
            label="Micro-tour video",
            channel="crediti",
            events=videos,
            unit_cogs_eur=EUR_MICRO_TOUR,
            cogs_eur=videos * EUR_MICRO_TOUR,
            list_credits_unit=10,
            revenue_eur=video_revenue,
            revenue_source="crediti_scalati",
            note="Incassi = crediti addebitati × €0,05",
        ),
        _money_row(
            key="api_gateway",
            label="API Track B",
            channel="crediti",
            events=api_calls,
            unit_cogs_eur=None,
            cogs_eur=0.0,  # COGS già nelle voci prodotto; qui solo ricavo crediti
            list_credits_unit=0,
            revenue_eur=api_revenue,
            revenue_source="crediti_scalati",
            note="Incassi crediti API (COGS nei servizi sottostanti)",
        ),
        _money_row(
            key="subscriptions_topups",
            label="Abbonamenti & ricariche",
            channel="abbonamento",
            events=0,
            unit_cogs_eur=0.0,
            cogs_eur=0.0,
            list_credits_unit=0,
            revenue_eur=round(payments_revenue, 2),
            revenue_source="stripe",
            note="Incassi Stripe piano + pacchetti crediti",
        ),
    ]
    # Override list_eur for api_gateway to show credit list value
    for s in services:
        if s["key"] == "api_gateway":
            s["list_eur"] = round(api_credits * EUR_PER_CREDIT_LIST, 2)
            s["list_credits"] = api_credits
            s["margin_if_listed_eur"] = round(s["list_eur"] - (s["cogs_eur"] or 0), 2)
        if s["key"] == "subscriptions_topups":
            s["list_eur"] = s["revenue_eur"]
            s["margin_if_listed_eur"] = s["revenue_eur"]
            s["margin_eur"] = s["revenue_eur"]

    total_cogs = round(sum(s["cogs_eur"] or 0 for s in services), 2)
    total_list = round(sum(s["list_eur"] or 0 for s in services), 2)
    total_revenue = round(sum(s["revenue_eur"] or 0 for s in services), 2)
    total_margin = round(total_revenue - total_cogs, 2)
    total_events = sum(int(s["events"] or 0) for s in services)

    legal_month_tavily = legal_month * (TAVILY_CREDITS_PER_LEGAL if tavily_on else 0)
    tavily_free_left = max(0, TAVILY_FREE_MONTH - legal_month_tavily)
    tavily_paid_eur = 0.0
    if legal_month_tavily > TAVILY_FREE_MONTH:
        tavily_paid_eur = (legal_month_tavily - TAVILY_FREE_MONTH) * EUR_TAVILY_PER_CREDIT

    # Serie giornaliera aggregata (legal + al + knowledge) per sparkline
    by_day_map: Dict[str, int] = {}
    for coll, field in (
        ("al_audit", "ts"),
        ("al_legal_audit", "ts"),
        ("hal_knowledge_sessions", "created_at"),
        ("virtual_staging_jobs", "created_at"),
        ("videos", "created_at"),
    ):
        try:
            rows = await db[coll].aggregate([
                {"$match": {field: {"$gte": since}}},
                {"$group": {"_id": {"$substr": [f"${field}", 0, 10]}, "n": {"$sum": 1}}},
            ]).to_list(120)
            for r in rows:
                day = r.get("_id") or ""
                if day:
                    by_day_map[day] = by_day_map.get(day, 0) + int(r.get("n") or 0)
        except Exception:
            logger.exception("by_day failed %s", coll)
    by_day = [{"day": d, "events": by_day_map[d]} for d in sorted(by_day_map.keys())]

    # Recent operational alerts (AI / Stripe)
    recent_alerts: List[Dict[str, Any]] = []
    try:
        recent_alerts = await db.ops_alerts.find(
            {},
            {"_id": 0, "id": 1, "kind": 1, "severity": 1, "message": 1, "created_at": 1, "acked": 1},
        ).sort("created_at", -1).to_list(20)
    except Exception:
        logger.exception("ops_alerts list failed")

    unacked = sum(1 for a in recent_alerts if not a.get("acked"))

    return {
        "period_days": days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "providers": {
            "llm_configured": llm_on,
            "tavily_configured": tavily_on,
            "gemini_model": os.environ.get("GEMINI_MODEL", "gemini-flash-latest"),
        },
        "policy": {
            "in_app_ai": "incluso (HAL CRM, Guida, Legal in agenzia)",
            "credits": "staging, video, API partner, overage, promozioni",
            "b2c": "carta one-shot (valuator UNI, legal portale, …)",
        },
        "alerts": {
            "unacked": unacked,
            "recent": recent_alerts,
        },
        "totals": {
            "events": total_events,
            "cogs_eur": total_cogs,
            "revenue_eur": total_revenue,
            "margin_eur": total_margin,
            "list_value_eur": total_list,
            "margin_if_listed_eur": round(total_list - total_cogs, 2),
            "b2c_revenue_eur": round(b2c_revenue, 2),
        },
        "services": services,
        "tavily": {
            "month_credits_used": legal_month_tavily,
            "free_credits_month": TAVILY_FREE_MONTH,
            "free_left": tavily_free_left,
            "month_paid_eur": round(tavily_paid_eur, 2),
        },
        "wallets": {
            "agency_credits_balance": wallet_balance,
            "agencies_with_credits": agencies_with_credits,
            "credit_transactions_delta": credit_delta,
            "list_value_of_balance_eur": round(wallet_balance * EUR_PER_CREDIT_LIST, 2),
        },
        "api_by_endpoint": api_by_endpoint,
        "by_day": by_day,
        "assumptions": {
            "eur_per_credit_list": EUR_PER_CREDIT_LIST,
            "note": (
                "Incassi = crediti scalati / Stripe / B2C quando presenti. "
                "Costi = stime COGS. Margine = Incassi − Costi. "
                "«A listino» = se tutto il volume fosse fatturato a listino crediti."
            ),
        },
        "links": {
            "legal_detail": "/app/ops/legal",
        },
    }
