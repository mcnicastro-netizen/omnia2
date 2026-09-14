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

from shared.auth.dependencies import get_current_user
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

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
MODEL = "gemini-3-flash-preview"
TEMPERATURE = 0.2          # D-029: low temp for legal accuracy
SOFT_RATE_LIMIT = 30       # per-user / per-hour (lower than CRM chat — costlier)
MAX_TURNS = 6

DISCLAIMER_HEADER = (
    "Le informazioni fornite da HAL Legal hanno carattere orientativo e divulgativo. "
    "HAL Legal NON è un avvocato e NON sostituisce un parere legale ai sensi dell'art. 2 L. 247/2012. "
    "Per il tuo caso specifico, rivolgiti sempre a un notaio o avvocato di fiducia."
)


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
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="llm_key_not_configured")
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        client = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_prompt,
        ).with_model("gemini", MODEL)
        return await client.send_message(UserMessage(text=user_msg))
    except HTTPException:
        raise
    except Exception as e:
        msg = str(e).lower()
        logger.warning("Legal LLM call failed: %s", e)
        if any(k in msg for k in ("budget", "quota", "credit", "402")):
            raise HTTPException(status_code=503, detail="llm_budget_exceeded")
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
        "kind": "pdf_analysis",
        "filename": file.filename[:200],
        "page_count": total_pages,
        "ts": now,
        "user_msg": question[:1000],
        "assistant_msg": final_answer[:2000],
        "citation_count": len(citations),
        "confidence": confidence,
        "unsupported_claims": verdict.get("unsupported_claims", []),
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
        "llm_configured": bool(EMERGENT_LLM_KEY),
    }
