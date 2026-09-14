"""AL Legal — FastAPI router.

Endpoints:
  POST /api/app/legal/chat        — multi-turn chat with web search + validation
  POST /api/app/legal/analyze-pdf — upload a real-estate document for analysis
  GET  /api/app/legal/sessions    — list user sessions
  GET  /api/app/legal/sessions/{sid} — full session detail
  DELETE /api/app/legal/sessions/{sid} — remove a session
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user, require_roles
from shared.db.connection import Database

from .pdf_parser import extract_text_from_pdf
from .prompts import SUB_AGENTS, route
from .tavily import format_sources_for_prompt, web_search
from .validator import (
    CONFIDENCE_THRESHOLD,
    append_disclaimers,
    validate as validate_answer,
)

logger = logging.getLogger("omnia.legal")
router = APIRouter(prefix="/legal", tags=["al-legal"])


def _llm_key() -> Optional[str]:
    return (
        os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
        or os.environ.get("EMERGENT_LLM_KEY")
        or ""
    ).strip() or None


EMERGENT_LLM_KEY = _llm_key()
MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
TEMPERATURE = 0.2          # D-029: low temp for legal accuracy
SOFT_RATE_LIMIT = 30       # per-user / per-hour (lower than CRM chat — costlier)
MAX_TURNS = 6

# Stima costi operativi (D-076) — ordini di grandezza, non fattura provider
TAVILY_CREDITS_PER_QUERY = 2          # search_depth=advanced
TAVILY_FREE_CREDITS_MONTH = 1000
TAVILY_EUR_PER_CREDIT = 0.0074        # ~$0.008 PAYG → EUR
GEMINI_EUR_PER_QUERY = 0.01           # 2 chiamate Flash (risposta + validatore)
LIST_PRICE_CREDITS = 12               # listino B2B PRICING_OMNIA
LIST_PRICE_EUR = 0.60

DISCLAIMER_HEADER = (
    "Le informazioni fornite da HAL Legal hanno carattere orientativo e divulgativo. "
    "HAL Legal NON è un avvocato e NON sostituisce un parere legale ai sensi dell'art. 2 L. 247/2012. "
    "Per il tuo caso specifico, rivolgiti sempre a un notaio o avvocato di fiducia."
)


def _agency_id_of(user: dict) -> Optional[str]:
    ids = user.get("agency_ids") or []
    return user.get("active_agency_id") or (ids[0] if ids else None)


def _estimate_query_cost(*, had_citations: bool = True) -> Dict[str, Any]:
    """Stima € per query Legal (Tavily advanced + 2× Gemini)."""
    tavily_on = bool(os.environ.get("TAVILY_API_KEY"))
    tavily_credits = TAVILY_CREDITS_PER_QUERY if tavily_on else 0
    tavily_eur = round(tavily_credits * TAVILY_EUR_PER_CREDIT, 4)
    gemini_eur = GEMINI_EUR_PER_QUERY
    return {
        "tavily_credits": tavily_credits,
        "tavily_eur": tavily_eur,
        "gemini_eur": gemini_eur,
        "total_eur": round(tavily_eur + gemini_eur, 4),
        "had_citations": had_citations,
    }


# ─── Schemas ─────────────────────────────────────────────────────
class LegalChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(min_length=2, max_length=2000)


# ─── Helpers ─────────────────────────────────────────────────────
async def _check_rate_limit(db, user_id: str) -> None:
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    count = await db.al_legal_audit.count_documents({
        "user_id": user_id,
        "ts": {"$gt": one_hour_ago},
    })
    if count >= SOFT_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")


async def _persist_session(db, sid: str, user_id: str, history: List[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    await db.al_legal_sessions.update_one(
        {"id": sid, "user_id": user_id},
        {"$set": {"messages": history, "updated_at": now},
         "$setOnInsert": {"id": sid, "user_id": user_id, "created_at": now}},
        upsert=True,
    )


def _build_user_prompt(sub_agent_key: str, user_message: str, sources_block: str) -> str:
    return (
        f"FONTI NORMATIVE DISPONIBILI (usa SOLO queste per supportare le tue affermazioni):\n"
        f"{sources_block}\n\n"
        f"DOMANDA DELL'UTENTE:\n{user_message}\n\n"
        "Rispondi in italiano seguendo il Chain of Thought e citando le FONTI con [n]."
    )


async def _call_llm(system_prompt: str, user_msg: str, session_id: str) -> str:
    if not _llm_key():
        raise HTTPException(status_code=503, detail="llm_key_not_configured")
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        client = LlmChat(
            api_key=_llm_key(),
            session_id=session_id,
            system_message=system_prompt,
        ).with_model("gemini", MODEL)
        return await client.send_message(UserMessage(text=user_msg))
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Legal LLM call failed: %s", e)
        raise HTTPException(status_code=503, detail="llm_unavailable")


# ─── Endpoints ───────────────────────────────────────────────────
@router.post("/chat")
async def legal_chat(req: LegalChatRequest, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """Multi-turn legal chat with web search + anti-hallucination."""
    db = Database.get()
    await _check_rate_limit(db, user["id"])

    sid = req.session_id or str(uuid4())

    # 1. Route to specialist sub-agent
    sub_agent_key = route(req.message)
    system_prompt = SUB_AGENTS[sub_agent_key]

    # 2. Web search live (Italian legal sources)
    citations = await web_search(req.message, max_results=5)
    sources_block = format_sources_for_prompt(citations)

    # 3. Primary LLM call (temperature 0.2 enforced via system prompt content)
    user_msg = _build_user_prompt(sub_agent_key, req.message, sources_block)
    raw_answer = await _call_llm(
        system_prompt=system_prompt,
        user_msg=user_msg,
        session_id=f"legal-{sid}-{uuid4().hex[:6]}",
    )

    # 4. Anti-hallucination validator (D-028 confidence ≥ 0.85)
    verdict = await validate_answer(raw_answer, sources_block)
    confidence = float(verdict.get("confidence", 0.5))

    # 5. Append disclaimer if low-confidence or no sources
    final_answer = append_disclaimers(
        raw_answer,
        confidence=confidence,
        sources_present=bool(citations),
    )

    # 6. Persist session + audit
    now = datetime.now(timezone.utc).isoformat()
    sess = await db.al_legal_sessions.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    history = (sess or {}).get("messages", [])[-MAX_TURNS * 2:]
    history.append({"role": "user", "content": req.message, "ts": now})
    history.append({
        "role": "assistant",
        "content": final_answer,
        "sub_agent": sub_agent_key,
        "citations": citations,
        "confidence": confidence,
        "ts": now,
    })
    await _persist_session(db, sid, user["id"], history)

    await db.al_legal_audit.insert_one({
        "id": str(uuid4()),
        "user_id": user["id"],
        "agency_id": _agency_id_of(user),
        "session_id": sid,
        "kind": "chat",
        "sub_agent": sub_agent_key,
        "ts": now,
        "user_msg": req.message[:1000],
        "assistant_msg": final_answer[:2000],
        "citation_count": len(citations),
        "confidence": confidence,
        "unsupported_claims": verdict.get("unsupported_claims", []),
        "fabricated_refs": verdict.get("fabricated_refs", []),
        "validator_rationale": verdict.get("rationale", "")[:300],
        "cost_estimate": _estimate_query_cost(had_citations=bool(citations)),
        "channel": "in_app",
    })

    return {
        "session_id": sid,
        "sub_agent": sub_agent_key,
        "reply": final_answer,
        "citations": citations,
        "confidence": confidence,
        "low_confidence": confidence < CONFIDENCE_THRESHOLD,
        "disclaimer": DISCLAIMER_HEADER,
    }


@router.post("/analyze-pdf")
async def analyze_pdf(
    file: UploadFile = File(...),
    question: str = Form(default="Analizza questo documento immobiliare e segnala criticità, clausole atipiche e verifiche da fare."),
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Upload a real-estate document PDF (proposta, preliminare, locazione)
    and receive a structured analysis from HAL Legal."""
    db = Database.get()
    await _check_rate_limit(db, user["id"])

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="only_pdf_allowed")

    pdf_bytes = await file.read()

    try:
        text, total_pages = extract_text_from_pdf(pdf_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Web search context from the user's question
    citations = await web_search(question, max_results=5)
    sources_block = format_sources_for_prompt(citations)

    user_prompt = (
        f"FONTI NORMATIVE DISPONIBILI:\n{sources_block}\n\n"
        f"DOMANDA DELL'UTENTE:\n{question}\n\n"
        f"TESTO DEL DOCUMENTO ({total_pages} pagine, troncato a 40000 caratteri):\n"
        f"{text}\n\n"
        "Esegui ora l'analisi strutturata seguendo il formato indicato nelle ISTRUZIONI."
    )

    raw_answer = await _call_llm(
        system_prompt=SUB_AGENTS["pdf_analysis"],
        user_msg=user_prompt,
        session_id=f"legal-pdf-{user['id']}-{uuid4().hex[:6]}",
    )

    verdict = await validate_answer(raw_answer, sources_block)
    confidence = float(verdict.get("confidence", 0.5))

    final_answer = append_disclaimers(raw_answer, confidence=confidence, sources_present=bool(citations))

    now = datetime.now(timezone.utc).isoformat()
    await db.al_legal_audit.insert_one({
        "id": str(uuid4()),
        "user_id": user["id"],
        "agency_id": _agency_id_of(user),
        "kind": "pdf_analysis",
        "filename": file.filename[:200],
        "page_count": total_pages,
        "ts": now,
        "user_msg": question[:1000],
        "assistant_msg": final_answer[:2000],
        "citation_count": len(citations),
        "confidence": confidence,
        "unsupported_claims": verdict.get("unsupported_claims", []),
        "cost_estimate": _estimate_query_cost(had_citations=bool(citations)),
        "channel": "in_app",
    })

    return {
        "filename": file.filename,
        "page_count": total_pages,
        "extracted_chars": len(text),
        "sub_agent": "pdf_analysis",
        "reply": final_answer,
        "citations": citations,
        "confidence": confidence,
        "low_confidence": confidence < CONFIDENCE_THRESHOLD,
        "disclaimer": DISCLAIMER_HEADER,
    }


@router.get("/sessions")
async def list_legal_sessions(user: dict = Depends(get_current_user)) -> List[Dict[str, Any]]:
    db = Database.get()
    cur = db.al_legal_sessions.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("updated_at", -1).limit(30)
    items: List[Dict[str, Any]] = []
    async for s in cur:
        msgs = s.get("messages", [])
        first_user = next((m for m in msgs if m.get("role") == "user"), None)
        items.append({
            "id": s.get("id"),
            "created_at": s.get("created_at"),
            "updated_at": s.get("updated_at"),
            "message_count": len(msgs),
            "preview": (first_user or {}).get("content", "")[:120],
        })
    return items


@router.get("/sessions/{sid}")
async def get_legal_session(sid: str, user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    db = Database.get()
    sess = await db.al_legal_sessions.find_one(
        {"id": sid, "user_id": user["id"]}, {"_id": 0}
    )
    if not sess:
        raise HTTPException(status_code=404, detail="session_not_found")
    return sess


@router.delete("/sessions/{sid}", status_code=204)
async def delete_legal_session(sid: str, user: dict = Depends(get_current_user)):
    db = Database.get()
    await db.al_legal_sessions.delete_one({"id": sid, "user_id": user["id"]})
    return None


@router.get("/health")
async def legal_health() -> Dict[str, Any]:
    """Quick health probe (no auth) — confirms wiring + Tavily key presence."""
    return {
        "service": "al-legal",
        "model": MODEL,
        "temperature": TEMPERATURE,
        "soft_rate_limit_per_hour": SOFT_RATE_LIMIT,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "sub_agents": list(SUB_AGENTS.keys()),
        "tavily_configured": bool(os.environ.get("TAVILY_API_KEY")),
        "llm_configured": bool(_llm_key()),
    }


@router.get("/ops/overview")
async def legal_ops_overview(
    days: int = 30,
    user: dict = Depends(require_roles("super_admin")),
) -> Dict[str, Any]:
    """Cruscotto Founder: volume Legal, stima costi, stato provider (D-076)."""
    days = max(1, min(int(days or 30), 90))
    db = Database.get()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    month_start = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()

    match = {"ts": {"$gte": since}}
    total = await db.al_legal_audit.count_documents(match)
    chats = await db.al_legal_audit.count_documents({**match, "kind": "chat"})
    pdfs = await db.al_legal_audit.count_documents({**match, "kind": "pdf_analysis"})
    month_total = await db.al_legal_audit.count_documents({"ts": {"$gte": month_start}})

    # Confidence media
    conf_pipe = [
        {"$match": match},
        {"$group": {"_id": None, "avg_conf": {"$avg": "$confidence"}, "with_citations": {
            "$sum": {"$cond": [{"$gt": ["$citation_count", 0]}, 1, 0]}
        }}},
    ]
    conf_rows = await db.al_legal_audit.aggregate(conf_pipe).to_list(1)
    avg_conf = round(float((conf_rows[0] or {}).get("avg_conf") or 0), 3) if conf_rows else 0.0
    with_citations = int((conf_rows[0] or {}).get("with_citations") or 0) if conf_rows else 0

    # Serie giornaliera
    day_pipe = [
        {"$match": match},
        {"$group": {
            "_id": {"$substr": ["$ts", 0, 10]},
            "queries": {"$sum": 1},
            "avg_confidence": {"$avg": "$confidence"},
        }},
        {"$sort": {"_id": 1}},
    ]
    by_day = [
        {
            "day": r["_id"],
            "queries": r["queries"],
            "avg_confidence": round(float(r.get("avg_confidence") or 0), 3),
        }
        for r in await db.al_legal_audit.aggregate(day_pipe).to_list(120)
    ]

    # Top utenti
    user_pipe = [
        {"$match": match},
        {"$group": {"_id": "$user_id", "queries": {"$sum": 1}, "agency_id": {"$last": "$agency_id"}}},
        {"$sort": {"queries": -1}},
        {"$limit": 10},
    ]
    top_user_rows = await db.al_legal_audit.aggregate(user_pipe).to_list(10)
    user_ids = [r["_id"] for r in top_user_rows if r.get("_id")]
    users_map = {}
    if user_ids:
        async for u in db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "email": 1, "name": 1, "role": 1}):
            users_map[u["id"]] = u
    top_users = [
        {
            "user_id": r["_id"],
            "email": (users_map.get(r["_id"]) or {}).get("email"),
            "name": (users_map.get(r["_id"]) or {}).get("name"),
            "role": (users_map.get(r["_id"]) or {}).get("role"),
            "agency_id": r.get("agency_id"),
            "queries": r["queries"],
        }
        for r in top_user_rows
    ]

    # Top agenzie
    ag_pipe = [
        {"$match": {**match, "agency_id": {"$nin": [None, ""]}}},
        {"$group": {"_id": "$agency_id", "queries": {"$sum": 1}}},
        {"$sort": {"queries": -1}},
        {"$limit": 10},
    ]
    top_ag_rows = await db.al_legal_audit.aggregate(ag_pipe).to_list(10)
    ag_ids = [r["_id"] for r in top_ag_rows if r.get("_id")]
    ag_map = {}
    if ag_ids:
        async for a in db.agencies.find({"id": {"$in": ag_ids}}, {"_id": 0, "id": 1, "display_name": 1, "name": 1}):
            ag_map[a["id"]] = a
    top_agencies = [
        {
            "agency_id": r["_id"],
            "name": (ag_map.get(r["_id"]) or {}).get("display_name") or (ag_map.get(r["_id"]) or {}).get("name") or r["_id"],
            "queries": r["queries"],
        }
        for r in top_ag_rows
    ]

    # API Track B legal usage (crediti)
    api_legal = 0
    api_credits = 0
    try:
        api_pipe = [
            {"$match": {"created_at": {"$gte": since}}},
            {"$match": {"endpoint": {"$regex": "legal", "$options": "i"}}},
            {"$group": {
                "_id": None,
                "calls": {"$sum": 1},
                "credits": {"$sum": {"$ifNull": ["$credits_charged", 0]}},
            }},
        ]
        api_rows = await db.api_usage_log.aggregate(api_pipe).to_list(1)
        if api_rows:
            api_legal = int(api_rows[0].get("calls") or 0)
            api_credits = int(api_rows[0].get("credits") or 0)
    except Exception:
        logger.exception("api_usage_log aggregate failed")

    tavily_on = bool(os.environ.get("TAVILY_API_KEY"))
    tavily_credits_used = month_total * (TAVILY_CREDITS_PER_QUERY if tavily_on else 0)
    tavily_free_left = max(0, TAVILY_FREE_CREDITS_MONTH - tavily_credits_used)
    tavily_eur_month = 0.0
    if tavily_credits_used > TAVILY_FREE_CREDITS_MONTH:
        tavily_eur_month = round(
            (tavily_credits_used - TAVILY_FREE_CREDITS_MONTH) * TAVILY_EUR_PER_CREDIT, 2
        )

    unit = _estimate_query_cost()
    gross_period = round(total * unit["total_eur"], 2)
    month_effective = round(month_total * GEMINI_EUR_PER_QUERY + tavily_eur_month, 2)

    recent = []
    async for row in db.al_legal_audit.find(
        match,
        {
            "_id": 0, "ts": 1, "kind": 1, "user_id": 1, "agency_id": 1,
            "confidence": 1, "citation_count": 1, "user_msg": 1, "cost_estimate": 1,
        },
    ).sort("ts", -1).limit(15):
        recent.append({
            "ts": row.get("ts"),
            "kind": row.get("kind"),
            "user_id": row.get("user_id"),
            "agency_id": row.get("agency_id"),
            "confidence": row.get("confidence"),
            "citation_count": row.get("citation_count"),
            "preview": (row.get("user_msg") or "")[:120],
            "cost_estimate": row.get("cost_estimate"),
        })

    return {
        "period_days": days,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "volume": {
            "total_queries": total,
            "chats": chats,
            "pdf_analyses": pdfs,
            "month_to_date": month_total,
            "with_citations": with_citations,
            "avg_confidence": avg_conf,
        },
        "by_day": by_day,
        "top_users": top_users,
        "top_agencies": top_agencies,
        "api_track_b": {
            "calls": api_legal,
            "credits_charged": api_credits,
        },
        "providers": {
            "tavily_configured": tavily_on,
            "llm_configured": bool(_llm_key()),
            "model": MODEL,
        },
        "costs": {
            "assumptions": {
                "tavily_credits_per_query": TAVILY_CREDITS_PER_QUERY,
                "tavily_free_credits_month": TAVILY_FREE_CREDITS_MONTH,
                "tavily_eur_per_credit": TAVILY_EUR_PER_CREDIT,
                "gemini_eur_per_query": GEMINI_EUR_PER_QUERY,
                "list_price_credits": LIST_PRICE_CREDITS,
                "list_price_eur": LIST_PRICE_EUR,
                "note": "Stime operative. Fatture reali = dashboard Tavily + Google AI.",
            },
            "per_query_eur": unit["total_eur"],
            "period_gross_eur": gross_period,
            "month_tavily_credits_used": tavily_credits_used,
            "month_tavily_free_credits_left": tavily_free_left,
            "month_tavily_paid_eur": tavily_eur_month,
            "month_effective_eur": month_effective,
            "period_list_price_value_eur": round(total * LIST_PRICE_EUR, 2),
        },
        "policy": {
            "in_app": "incluso (gratuito per agenzia)",
            "api_b2b": "a crediti",
            "b2c": "a pagamento carta",
        },
        "recent": recent,
    }
