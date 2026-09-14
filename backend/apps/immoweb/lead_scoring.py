"""OMNIA — Lead Scoring AI service (M2.S4 D-025 Layer 2).

Input: client profile + match result + property context.
Output: structured JSON {score, temperature, reasons[], action_hint} in Italian.
Uses Gemini-3-flash-preview via Emergent LLM Key. Graceful rule-based fallback.
"""
import json
import logging
import os
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger("omnia.lead_scoring")

_EMERGENT_KEY_ENV = "EMERGENT_LLM_KEY"

SYSTEM_PROMPT = """Sei un esperto consulente di agenzia immobiliare italiana.
Il tuo compito: stimare quanto un cliente è "caldo" per uno specifico immobile in base ai dati forniti.

REGOLE FERREE:
- Rispondi SOLO con un oggetto JSON valido, niente testo prima o dopo.
- Lingua: italiano colloquiale e diretto, come parlerebbe un agente esperto a un collega.
- Sii pragmatico: una buona corrispondenza preferenze + cliente recente con GDPR consent → punteggio alto. Cliente vecchio o profilo scarno → punteggio basso.

SCHEMA JSON ATTESO:
{
  "score": int 0-100,
  "temperature": "freddo" | "tiepido" | "caldo" | "rovente",
  "reasons": ["motivo 1 max 90 char", "motivo 2", "motivo 3"],   // 2-4 motivi, concreti
  "action_hint": "una sola frase d'azione immediata max 120 char, in tono diretto"
}

MAPPATURA temperature:
- 0-39 → freddo
- 40-64 → tiepido
- 65-84 → caldo
- 85-100 → rovente
"""


def _classify(score: int) -> str:
    if score >= 85:
        return "rovente"
    if score >= 65:
        return "caldo"
    if score >= 40:
        return "tiepido"
    return "freddo"


def _build_user_prompt(client: Dict[str, Any], prop: Dict[str, Any], match: Dict[str, Any]) -> str:
    """Compact context payload for the LLM. Keep token-cheap."""
    c = {
        "nome": f"{client.get('name','')} {client.get('surname','') or ''}".strip(),
        "tipo": client.get("client_type"),
        "stato_crm": client.get("status"),
        "ha_email": bool(client.get("email")),
        "ha_telefono": bool(client.get("phone")),
        "ha_whatsapp": bool(client.get("whatsapp")),
        "gdpr_ok": bool(client.get("gdpr_consent")),
        "origine": client.get("source"),
        "preferenze": {
            "operazione": (client.get("preferences") or {}).get("operation"),
            "città": (client.get("preferences") or {}).get("cities"),
            "tipologie": (client.get("preferences") or {}).get("property_types"),
            "prezzo_min": (client.get("preferences") or {}).get("price_min"),
            "prezzo_max": (client.get("preferences") or {}).get("price_max"),
            "feature_must": (client.get("preferences") or {}).get("must_have_features"),
        },
        "note": client.get("notes"),
    }
    p = {
        "titolo": prop.get("title"),
        "tipo": prop.get("property_type"),
        "operazione": prop.get("operation"),
        "città": prop.get("city"),
        "prezzo": prop.get("price") or prop.get("rent_monthly"),
        "mq": prop.get("surface_sqm"),
        "locali": prop.get("rooms"),
        "stato_immobile": prop.get("status"),
    }
    m = {
        "score_deterministico": match.get("score"),
        "criteri_mancanti": match.get("missing"),
    }
    return (
        "Cliente:\n" + json.dumps(c, ensure_ascii=False) +
        "\n\nImmobile:\n" + json.dumps(p, ensure_ascii=False) +
        "\n\nMatch deterministico già calcolato:\n" + json.dumps(m, ensure_ascii=False) +
        "\n\nProduci il JSON di valutazione."
    )


def _rule_based_fallback(client: Dict[str, Any], match: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback when AI is unavailable."""
    base = int(match.get("score") or 0)
    bonus = 0
    reasons = []
    if client.get("gdpr_consent"):
        bonus += 5
        reasons.append("Consenso GDPR rilasciato")
    if client.get("phone"):
        bonus += 3
        reasons.append("Telefono presente")
    if client.get("status") in ("qualified", "negotiating"):
        bonus += 10
        reasons.append(f"Stato CRM: {client.get('status')}")
    elif client.get("status") in ("closed_lost", "archived"):
        bonus -= 30
        reasons.append(f"Stato CRM negativo: {client.get('status')}")
    if (match.get("missing") or []) == []:
        bonus += 5
        reasons.append("Nessuna preferenza mancante")
    score = max(0, min(100, base + bonus))
    return {
        "score": score,
        "temperature": _classify(score),
        "reasons": reasons[:4] or [f"Match deterministico: {base}/100"],
        "action_hint": (
            f"Contatta entro 24h: profilo qualificato ({score}/100)."
            if score >= 65 else
            "Profilo da scaldare: invia listino curato e attendi reazione."
            if score >= 40 else
            "Profilo freddo: rinvia o riqualifica con una breve email."
        ),
        "engine": "rule-based",
    }


async def score_lead(
    client: Dict[str, Any],
    prop: Dict[str, Any],
    match: Dict[str, Any],
) -> Dict[str, Any]:
    """Score a (client, property, match) tuple. Always returns a valid dict."""
    api_key = os.environ.get(_EMERGENT_KEY_ENV)
    if not api_key:
        logger.warning("EMERGENT_LLM_KEY not set, using rule-based fallback")
        return _rule_based_fallback(client, match)

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage  # type: ignore

        chat = LlmChat(
            api_key=api_key,
            session_id=f"lead-score-{uuid4()}",
            system_message=SYSTEM_PROMPT,
        ).with_model("gemini", "gemini-3-flash-preview")

        user_msg = UserMessage(text=_build_user_prompt(client, prop, match))
        raw = await chat.send_message(user_msg)
        # raw is the text response; strip ``` if present
        text = raw.strip() if isinstance(raw, str) else str(raw)
        if text.startswith("```"):
            text = text.split("```", 2)[1] if text.count("```") >= 2 else text
            if text.lower().startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        # Sanitize
        score = int(max(0, min(100, int(data.get("score", 0)))))
        temperature = data.get("temperature") or _classify(score)
        reasons = data.get("reasons") or []
        if isinstance(reasons, str):
            reasons = [reasons]
        action_hint = data.get("action_hint") or ""
        return {
            "score": score,
            "temperature": temperature,
            "reasons": [str(r)[:200] for r in reasons[:4]],
            "action_hint": str(action_hint)[:200],
            "engine": "gemini-3-flash",
        }
    except Exception as e:
        logger.warning(f"Gemini lead scoring failed ({type(e).__name__}: {e}), falling back to rule-based")
        return _rule_based_fallback(client, match)
