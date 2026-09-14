"""OMNIA — Al for Agents (M5.S1).

Conversational AI assistant for agents inside ImmoWeb CRM.
Uses Gemini 3 Flash Preview via Emergent LLM Key with manual JSON tool-use pattern.

Endpoints:
  POST /api/app/al/chat             — send message, get response (sync)
  GET  /api/app/al/sessions         — list user's sessions
  GET  /api/app/al/sessions/{sid}   — get session messages
  DELETE /api/app/al/sessions/{sid} — delete session

Tools whitelisted (agency_id auto-injected from auth):
  - query_properties     (filters: city, type, operation, status, price_max)
  - query_clients        (filters: client_type, status, source, name)
  - query_leads          (filters: status, since_days, min_score)
  - monthly_performance  (last 30 days summary)
  - write_description    (generate property description)
"""
import json
import re
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database

load_dotenv()
logger = logging.getLogger("omnia.al_agent")
router = APIRouter(prefix="/al", tags=["al-agent"])

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
MODEL = "gemini-3-flash-preview"
TEMPERATURE = 0.2  # deterministic for CRM queries
MAX_TURNS = 30     # cap conversation history per session
SOFT_RATE_LIMIT = 60  # max messages per user per hour


SYSTEM_PROMPT = """Sei HAL, l'assistente AI di OMNIA per agenti immobiliari italiani.

Aiuti l'agente a:
- Cercare immobili, clienti, lead del suo CRM
- Analizzare performance (mese, settimana, lead caldi)
- Scrivere descrizioni annunci professionali
- Rispondere a domande operative sull'app OMNIA

REGOLE FONDAMENTALI:
1. Rispondi sempre in ITALIANO, tono professionale ma cordiale
2. Se serve consultare il CRM, restituisci SOLO un JSON con la chiamata al tool:
   {"tool": "nome_tool", "params": {...}}
   Tools disponibili: query_properties, query_clients, query_leads, monthly_performance, write_description
3. Quando ricevi il risultato del tool, componi una risposta naturale in linguaggio umano
4. NON inventare dati. Se non sai, rispondi "Non ho questa informazione nel tuo CRM"
5. NON dare consigli legali. Se l'utente chiede di leggi/notai/contratti, suggerisci di usare HAL Legal (in arrivo)
6. NON eseguire azioni distruttive (delete, drop). Sei in modalità SOLA LETTURA

TOOLS SCHEMA:
- query_properties(city?, property_type?, operation?, status?, price_max?) → lista immobili
- query_clients(client_type?, status?, source?, name?) → lista clienti
- query_leads(status?, since_days?, min_score?) → lista lead
- monthly_performance() → KPI ultimi 30 giorni
- write_description(property_id, tone?) → descrizione testo (tone: standard|lusso|giovane)
"""


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(min_length=1, max_length=2000)


from shared.auth.tenant import require_agency_membership as _agency_id


async def _check_rate_limit(db, user_id: str, kind: Optional[str] = None) -> None:
    """Soft rate limit per user/hour, optionally scoped to a kind.

    kind=None (default) → counts ONLY chat messages (rows without `kind` field, i.e. chat audit)
    kind="improve"      → counts only improve calls
    """
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    query = {"user_id": user_id, "ts": {"$gt": one_hour_ago}}
    if kind is None:
        # Legacy chat rows do not set the `kind` field
        query["kind"] = {"$exists": False}
    else:
        query["kind"] = kind
    count = await db.al_audit.count_documents(query)
    if count >= SOFT_RATE_LIMIT:
        raise HTTPException(status_code=429, detail="rate_limit_exceeded")


# ============================================================
# Tool implementations (server-side, agency-scoped)
# ============================================================

async def _tool_query_properties(db, agency_id: str, params: dict) -> dict:
    flt = {"agency_id": agency_id}
    if params.get("city"):
        flt["city"] = {"$regex": f"^{params['city']}", "$options": "i"}
    if params.get("property_type"):
        flt["property_type"] = params["property_type"]
    if params.get("operation"):
        flt["operation"] = params["operation"]
    if params.get("status"):
        flt["status"] = params["status"]
    if params.get("price_max"):
        flt["price"] = {"$lte": int(params["price_max"])}
    cursor = db.properties.find(flt, {"_id": 0, "id": 1, "title": 1, "city": 1,
        "property_type": 1, "operation": 1, "price": 1, "rent_monthly": 1,
        "surface_sqm": 1, "rooms": 1, "status": 1}).limit(15)
    items = await cursor.to_list(length=15)
    return {"count": len(items), "items": items}


async def _tool_query_clients(db, agency_id: str, params: dict) -> dict:
    flt = {"agency_id": agency_id}
    if params.get("client_type"):
        flt["client_type"] = params["client_type"]
    if params.get("status"):
        flt["status"] = params["status"]
    if params.get("source"):
        flt["source"] = params["source"]
    if params.get("name"):
        flt["name"] = {"$regex": params["name"], "$options": "i"}
    cursor = db.clients.find(flt, {"_id": 0, "id": 1, "name": 1, "surname": 1,
        "email": 1, "phone": 1, "client_type": 1, "status": 1, "source": 1,
        "lead_score": 1}).limit(15)
    items = await cursor.to_list(length=15)
    return {"count": len(items), "items": items}


async def _tool_query_leads(db, agency_id: str, params: dict) -> dict:
    flt = {"agency_id": agency_id}
    if params.get("status"):
        flt["status"] = params["status"]
    if params.get("since_days"):
        d = datetime.now(timezone.utc) - timedelta(days=int(params["since_days"]))
        flt["created_at"] = {"$gte": d.isoformat()}
    if params.get("min_score"):
        flt["score"] = {"$gte": int(params["min_score"])}
    cursor = db.leads.find(flt, {"_id": 0, "id": 1, "client_id": 1, "property_id": 1,
        "status": 1, "score": 1, "notes": 1, "source": 1, "created_at": 1}).sort("created_at", -1).limit(15)
    items = await cursor.to_list(length=15)
    return {"count": len(items), "items": items}


async def _tool_monthly_performance(db, agency_id: str, params: dict) -> dict:
    since = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    new_props = await db.properties.count_documents({"agency_id": agency_id, "created_at": {"$gte": since}})
    active = await db.properties.count_documents({"agency_id": agency_id, "status": "active"})
    new_clients = await db.clients.count_documents({"agency_id": agency_id, "created_at": {"$gte": since}})
    new_leads = await db.leads.count_documents({"agency_id": agency_id, "created_at": {"$gte": since}})
    hot_leads = await db.leads.count_documents(
        {"agency_id": agency_id,
         "status": {"$in": ["new", "contacted"]},
         "score": {"$gte": 70}}
    )
    return {
        "period_days": 30,
        "new_properties": new_props, "active_properties": active,
        "new_clients": new_clients,
        "new_leads": new_leads, "hot_leads_open": hot_leads,
    }


async def _tool_write_description(db, agency_id: str, params: dict) -> dict:
    pid = params.get("property_id")
    if not pid:
        return {"error": "property_id_required"}
    p = await db.properties.find_one({"id": pid, "agency_id": agency_id},
        {"_id": 0, "title": 1, "property_type": 1, "city": 1, "surface_sqm": 1,
         "rooms": 1, "bedrooms": 1, "bathrooms": 1, "energy": 1, "features": 1, "price": 1})
    if not p:
        return {"error": "property_not_found"}
    return {"property": p, "tone": params.get("tone", "standard")}


TOOLS = {
    "query_properties": _tool_query_properties,
    "query_clients": _tool_query_clients,
    "query_leads": _tool_query_leads,
    "monthly_performance": _tool_monthly_performance,
    "write_description": _tool_write_description,
}


# ============================================================
# Inline AI: Improve title/description in property form
# ============================================================

class ImproveRequest(BaseModel):
    field: str = Field(pattern="^(title|description)$")
    current_text: str = Field(default="", max_length=10000)
    property_data: Dict[str, Any] = Field(default_factory=dict)
    target_lang: str = Field(default="it", pattern="^(it|en|es)$")
    tone: Optional[str] = Field(default="standard", pattern="^(standard|lusso|giovane)$")


def _format_property_context(data: dict) -> str:
    """Build a compact, human-readable bullet list of available property data."""
    lines: List[str] = []
    def add(label: str, key: str, fmt=None):
        v = data.get(key)
        if v in (None, "", [], {}):
            return
        if fmt:
            v = fmt(v)
        lines.append(f"- {label}: {v}")

    add("Tipologia", "property_type")
    add("Operazione", "operation")
    add("Città", "city")
    add("Provincia", "province")
    add("Zona/Quartiere", "zone")
    add("Indirizzo", "address")
    add("Superficie", "surface_sqm", lambda v: f"{v} mq")
    add("Locali", "rooms")
    add("Camere", "bedrooms")
    add("Bagni", "bathrooms")
    add("Piano", "floor")
    add("Piani totali", "total_floors")
    add("Anno costruzione", "year_built")
    add("Condizione", "condition")
    add("Arredamento", "furnished")
    add("Prezzo vendita", "price", lambda v: f"€ {v}")
    add("Canone mensile", "rent_monthly", lambda v: f"€ {v}/mese")
    add("Spese condominiali", "condo_fees", lambda v: f"€ {v}")

    energy = data.get("energy") or {}
    if isinstance(energy, dict):
        ec = energy.get("energy_class")
        if ec:
            lines.append(f"- Classe energetica: {ec}")
        heat = energy.get("heating")
        if heat:
            lines.append(f"- Riscaldamento: {heat}")

    features = data.get("features") or {}
    if isinstance(features, dict):
        active = [k for k, v in features.items() if v]
        if active:
            lines.append(f"- Caratteristiche: {', '.join(active[:20])}")
    elif isinstance(features, list) and features:
        lines.append(f"- Caratteristiche: {', '.join(features[:20])}")

    return "\n".join(lines) if lines else "(nessun dato disponibile)"


_LANG_LABEL = {"it": "italiano", "en": "inglese", "es": "spagnolo"}
_TONE_HINT = {
    "standard": "tono professionale, chiaro, informativo. Stile real estate moderno italiano.",
    "lusso": "tono elegante e ricercato, lessico premium, evoca esclusività e prestigio.",
    "giovane": "tono dinamico, fresco, friendly. Stile più colloquiale, ideale per giovani acquirenti/inquilini.",
}


def _build_improve_prompt(req: ImproveRequest) -> str:
    ctx = _format_property_context(req.property_data)
    lang_label = _LANG_LABEL.get(req.target_lang, "italiano")
    tone_hint = _TONE_HINT.get(req.tone or "standard", _TONE_HINT["standard"])

    if req.field == "title":
        target_rules = (
            "Genera un TITOLO accattivante per l'annuncio immobiliare, MASSIMO 80 caratteri. "
            "Deve includere tipologia + zona/città + 1-2 punti di forza. Niente prezzo nel titolo. "
            "Niente emoji. Niente virgolette. Niente punto finale."
        )
        max_len = "80 caratteri"
    else:
        target_rules = (
            "Genera una DESCRIZIONE professionale per l'annuncio immobiliare, 600-1200 caratteri. "
            "Struttura: 1) attacco con punti di forza, 2) descrizione locali/finiture, 3) zona/servizi, "
            "4) classe energetica e info pratiche. Niente bullet point, paragrafi fluidi. "
            "Niente prezzo nel testo. Niente emoji. Niente claim invented (non inventare dati assenti)."
        )
        max_len = "1200 caratteri"

    current = (req.current_text or "").strip()
    current_block = f"TESTO ATTUALE DELL'AGENTE/PRIVATO (da migliorare/sostituire):\n\"{current}\"\n\n" if current else ""

    return (
        f"Sei HAL, copywriter immobiliare di OMNIA. Riscrivi in {lang_label} con {tone_hint}\n\n"
        f"{target_rules}\n\n"
        f"DATI IMMOBILE DISPONIBILI:\n{ctx}\n\n"
        f"{current_block}"
        f"REGOLE FERREE:\n"
        f"- Massimo {max_len}.\n"
        f"- Non inventare dati che non sono nei DATI IMMOBILE (no falsi metri quadri, no false stanze).\n"
        f"- Non includere mai prezzo, telefono, email, URL.\n"
        f"- Rispondi SOLO con il testo finale, senza prefissi, senza spiegazioni, senza markdown, senza virgolette.\n"
    )


_FENCE_RE = re.compile(r"^```(?:\w+)?\s*\n?|\n?\s*```\s*$", re.IGNORECASE)
_PREFIX_RE = re.compile(
    r"^\s*(titolo|descrizione|title|description|título|descripción)\s*[:\-–]\s*",
    re.IGNORECASE,
)


def _sanitize_improve_output(text: str) -> str:
    """Strip markdown fences, common prefixes ('Titolo:', etc.) and wrapping quotes."""
    if not text:
        return ""
    out = text.strip()
    # Strip fenced code blocks (```json ... ``` or ``` ... ```)
    out = _FENCE_RE.sub("", out).strip()
    # Drop common label prefix ("Titolo:", "Description:", etc.)
    out = _PREFIX_RE.sub("", out, count=1).strip()
    # Strip wrapping quotes (regular, smart, French, German)
    pairs = [('"', '"'), ("«", "»"), ("“", "”"), ("„", "“"), ("'", "'")]
    for left, right in pairs:
        if len(out) >= 2 and out.startswith(left) and out.endswith(right):
            out = out[1:-1].strip()
            break
    return out


@router.post("/improve")
async def improve_text(req: ImproveRequest, user: dict = Depends(get_current_user)):
    """Generate an improved title or description from property form data.

    Used inline in PropertyForm (agents) and SellPage (B2C private owners).
    No agency_id needed — operation is on form data only.
    """
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="llm_key_not_configured")

    db = Database.get()
    await _check_rate_limit(db, user["id"], kind="improve")

    prompt = _build_improve_prompt(req)

    from emergentintegrations.llm.chat import LlmChat, UserMessage
    chat_client = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"improve-{user['id']}-{uuid4().hex[:8]}",
        system_message="Sei HAL, copywriter immobiliare di OMNIA. Rispondi sempre e solo con il testo finale richiesto, senza prefissi né spiegazioni.",
    ).with_model("gemini", MODEL)

    try:
        text = await chat_client.send_message(UserMessage(text=prompt))
    except Exception as e:
        msg = str(e).lower()
        logger.warning("Improve LLM call failed: %s", e)
        if any(k in msg for k in ("budget", "quota", "credit", "402")):
            raise HTTPException(status_code=503, detail="llm_budget_exceeded")
        raise HTTPException(status_code=503, detail="llm_unavailable")

    cleaned = _sanitize_improve_output(text)

    # Audit (lightweight)
    await db.al_audit.insert_one({
        "id": str(uuid4()),
        "user_id": user["id"],
        "kind": "improve",
        "field": req.field,
        "lang": req.target_lang,
        "tone": req.tone,
        "ts": datetime.now(timezone.utc).isoformat(),
        "input_len": len(req.current_text or ""),
        "output_len": len(cleaned),
    })

    return {
        "field": req.field,
        "lang": req.target_lang,
        "tone": req.tone,
        "improved": cleaned,
    }


# ============================================================
# Chat endpoint
# ============================================================

@router.post("/chat")
async def chat(req: ChatRequest, user: dict = Depends(get_current_user)):
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="llm_key_not_configured")

    db = Database.get()
    agency_id = _agency_id(user)
    await _check_rate_limit(db, user["id"])

    # Load or create session
    sid = req.session_id or str(uuid4())
    sess = await db.al_sessions.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    if not sess:
        sess = {"id": sid, "user_id": user["id"], "agency_id": agency_id,
                "messages": [], "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()}
        await db.al_sessions.insert_one(sess)

    # Inject user message
    history = sess.get("messages", [])[-MAX_TURNS * 2:]
    history.append({"role": "user", "content": req.message})

    # Init LLM
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    chat_client = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=sid,
        system_message=SYSTEM_PROMPT,
    ).with_model("gemini", MODEL)

    # Replay history (excluding the current user message we just appended)
    for msg in history[:-1]:
        if msg["role"] == "user":
            await chat_client.send_message(UserMessage(text=msg["content"]))

    # Send current message → potentially get JSON tool call
    try:
        raw_reply = await chat_client.send_message(UserMessage(text=req.message))
    except Exception as e:
        msg = str(e).lower()
        logger.warning("LLM call failed: %s", e)
        if "budget" in msg or "quota" in msg or "credit" in msg or "402" in msg:
            raise HTTPException(status_code=503, detail="llm_budget_exceeded")
        raise HTTPException(status_code=503, detail="llm_unavailable")

    # Detect JSON tool call (manual pattern — no native function calling in lib)
    final_reply = raw_reply
    tool_used = None
    tool_result = None
    parsed_call = _try_parse_tool_call(raw_reply)
    if parsed_call:
        tool_name = parsed_call.get("tool")
        params = parsed_call.get("params", {}) or {}
        if tool_name in TOOLS:
            try:
                tool_result = await TOOLS[tool_name](db, agency_id, params)
                tool_used = tool_name
                # Feed result back to LLM for natural-language composition
                follow_up = (
                    f"Risultato del tool {tool_name}:\n{json.dumps(tool_result, ensure_ascii=False)}\n\n"
                    "Componi ora la risposta finale all'utente in italiano, sintetica e utile."
                )
                try:
                    final_reply = await chat_client.send_message(UserMessage(text=follow_up))
                except Exception as e:
                    msg = str(e).lower()
                    logger.warning("LLM follow-up failed: %s", e)
                    if "budget" in msg or "quota" in msg or "credit" in msg or "402" in msg:
                        raise HTTPException(status_code=503, detail="llm_budget_exceeded")
                    raise HTTPException(status_code=503, detail="llm_unavailable")
            except Exception as e:
                logger.warning("tool %s failed: %s", tool_name, e)
                final_reply = f"Ho provato a consultare {tool_name} ma ho avuto un problema. Riprova."

    # Persist messages & audit
    now = datetime.now(timezone.utc).isoformat()
    history.append({"role": "assistant", "content": final_reply, "tool": tool_used})
    await db.al_sessions.update_one(
        {"id": sid},
        {"$set": {"messages": history, "updated_at": now}},
    )
    await db.al_audit.insert_one({
        "id": str(uuid4()), "session_id": sid,
        "user_id": user["id"], "agency_id": agency_id,
        "ts": now, "user_msg": req.message[:500],
        "assistant_msg": final_reply[:1000],
        "tool": tool_used, "tool_params_count": len(parsed_call.get("params", {})) if parsed_call else 0,
    })

    return {
        "session_id": sid,
        "reply": final_reply,
        "tool_used": tool_used,
        "messages_count": len(history),
    }


def _try_parse_tool_call(text: str) -> Optional[dict]:
    """Try to extract a JSON tool call from the LLM output."""
    if not text:
        return None
    s = text.strip()
    # Strip markdown code fences
    if s.startswith("```"):
        s = s.split("```", 2)[1] if "```" in s[3:] else s[3:]
        if s.startswith("json"):
            s = s[4:]
        s = s.strip()
    # Try direct parse
    try:
        d = json.loads(s)
        if isinstance(d, dict) and "tool" in d:
            return d
    except (json.JSONDecodeError, ValueError):
        pass
    # Try to find embedded JSON
    start = s.find("{")
    end = s.rfind("}")
    if start >= 0 and end > start:
        try:
            d = json.loads(s[start:end + 1])
            if isinstance(d, dict) and "tool" in d:
                return d
        except (json.JSONDecodeError, ValueError):
            pass
    return None


# ============================================================
# Streaming chat endpoint (Server-Sent Events)
# ============================================================

@router.post("/chat/stream")
async def chat_stream(req: ChatRequest, user: dict = Depends(get_current_user)):
    """SSE token-by-token streaming. Yields lines like `data: {json}\\n\\n`.

    Event types:
      - {"type":"session","session_id":"..."}     — sent once at start
      - {"type":"thinking"}                        — sniffed a JSON tool call, waiting
      - {"type":"tool","name":"..."}               — about to execute a CRM tool
      - {"type":"token","content":"..."}           — natural-language token delta
      - {"type":"done","tool_used":"...|null"}     — terminator
      - {"type":"error","detail":"..."}            — terminator on error
    """
    if not EMERGENT_LLM_KEY:
        raise HTTPException(status_code=503, detail="llm_key_not_configured")

    db = Database.get()
    agency_id = _agency_id(user)
    await _check_rate_limit(db, user["id"])

    sid = req.session_id or str(uuid4())
    sess = await db.al_sessions.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    if not sess:
        sess = {"id": sid, "user_id": user["id"], "agency_id": agency_id,
                "messages": [], "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()}
        await db.al_sessions.insert_one(sess)

    history = sess.get("messages", [])[-MAX_TURNS * 2:]
    history.append({"role": "user", "content": req.message})

    from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta
    chat_client = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=sid,
        system_message=SYSTEM_PROMPT,
    ).with_model("gemini", MODEL)

    # Replay history (best-effort; same compromise as /chat)
    for msg in history[:-1]:
        if msg["role"] == "user":
            try:
                await chat_client.send_message(UserMessage(text=msg["content"]))
            except Exception:
                break

    def _sse(data: dict) -> str:
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    async def event_gen():
        yield _sse({"type": "session", "session_id": sid})

        # Phase 1: stream first response, sniff for JSON tool call
        text_buf: List[str] = []
        looks_like_tool = None  # None=undecided, True/False once we have enough
        thinking_sent = False
        SNIFF_CHARS = 16

        try:
            async for delta in chat_client.stream_message(UserMessage(text=req.message)):
                if not isinstance(delta, TextDelta):
                    continue
                text_buf.append(delta.content)
                buf_str = "".join(text_buf)

                if looks_like_tool is None and len(buf_str) >= SNIFF_CHARS:
                    head = buf_str.lstrip().lower()
                    looks_like_tool = head.startswith("{") or head.startswith("```json") or head.startswith("```\n{")
                    if looks_like_tool is False:
                        # Flush already-buffered tokens to client
                        yield _sse({"type": "token", "content": buf_str})
                        continue
                    if looks_like_tool is True and not thinking_sent:
                        yield _sse({"type": "thinking"})
                        thinking_sent = True
                        continue

                if looks_like_tool is False:
                    yield _sse({"type": "token", "content": delta.content})
        except Exception as e:
            msg = str(e).lower()
            logger.warning("Stream phase-1 failed: %s", e)
            detail = "llm_budget_exceeded" if any(k in msg for k in ("budget", "quota", "credit", "402")) else "llm_unavailable"
            yield _sse({"type": "error", "detail": detail})
            return

        raw_reply = "".join(text_buf)
        # If we never decided (short reply), treat as plain text
        if looks_like_tool is None:
            for ch in raw_reply:
                yield _sse({"type": "token", "content": ch})
            looks_like_tool = False

        final_reply = raw_reply
        tool_used = None
        tool_params = {}

        # Phase 2: tool execution + streamed natural-language follow-up
        if looks_like_tool:
            parsed = _try_parse_tool_call(raw_reply)
            if parsed and parsed.get("tool") in TOOLS:
                tool_name = parsed["tool"]
                tool_params = parsed.get("params", {}) or {}
                yield _sse({"type": "tool", "name": tool_name})
                try:
                    tool_result = await TOOLS[tool_name](db, agency_id, tool_params)
                    tool_used = tool_name
                    follow_up = (
                        f"Risultato del tool {tool_name}:\n"
                        f"{json.dumps(tool_result, ensure_ascii=False)}\n\n"
                        "Componi ora la risposta finale all'utente in italiano, sintetica e utile."
                    )
                    final_buf: List[str] = []
                    async for delta in chat_client.stream_message(UserMessage(text=follow_up)):
                        if not isinstance(delta, TextDelta):
                            continue
                        final_buf.append(delta.content)
                        yield _sse({"type": "token", "content": delta.content})
                    final_reply = "".join(final_buf)
                except HTTPException:
                    raise
                except Exception as e:
                    msg = str(e).lower()
                    logger.warning("Tool/follow-up failed: %s", e)
                    if any(k in msg for k in ("budget", "quota", "credit", "402")):
                        yield _sse({"type": "error", "detail": "llm_budget_exceeded"})
                        return
                    err_msg = f"Ho provato a consultare {tool_name} ma ho avuto un problema. Riprova."
                    for ch in err_msg:
                        yield _sse({"type": "token", "content": ch})
                    final_reply = err_msg
            else:
                # JSON-looking but unparseable → emit raw as fallback
                for ch in raw_reply:
                    yield _sse({"type": "token", "content": ch})

        # Persist + audit
        now = datetime.now(timezone.utc).isoformat()
        history.append({"role": "assistant", "content": final_reply, "tool": tool_used})
        await db.al_sessions.update_one(
            {"id": sid},
            {"$set": {"messages": history, "updated_at": now}},
        )
        await db.al_audit.insert_one({
            "id": str(uuid4()), "session_id": sid,
            "user_id": user["id"], "agency_id": agency_id,
            "ts": now, "user_msg": req.message[:500],
            "assistant_msg": final_reply[:1000],
            "tool": tool_used, "tool_params_count": len(tool_params),
            "stream": True,
        })

        yield _sse({"type": "done", "tool_used": tool_used, "session_id": sid})

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/sessions")
async def list_sessions(user: dict = Depends(get_current_user)):
    db = Database.get()
    cursor = db.al_sessions.find({"user_id": user["id"]},
        {"_id": 0, "id": 1, "created_at": 1, "updated_at": 1, "messages": 1}
    ).sort("updated_at", -1).limit(20)
    items = await cursor.to_list(length=20)
    for s in items:
        msgs = s.pop("messages", [])
        s["message_count"] = len(msgs)
        s["preview"] = msgs[0]["content"][:80] if msgs else ""
    return {"items": items}


@router.get("/sessions/{sid}")
async def get_session(sid: str, user: dict = Depends(get_current_user)):
    db = Database.get()
    s = await db.al_sessions.find_one({"id": sid, "user_id": user["id"]}, {"_id": 0})
    if not s:
        raise HTTPException(status_code=404, detail="session_not_found")
    return s


@router.delete("/sessions/{sid}", status_code=204)
async def delete_session(sid: str, user: dict = Depends(get_current_user)):
    db = Database.get()
    r = await db.al_sessions.delete_one({"id": sid, "user_id": user["id"]})
    if r.deleted_count == 0:
        raise HTTPException(status_code=404, detail="session_not_found")
    return None
