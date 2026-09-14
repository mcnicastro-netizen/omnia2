"""Anti-hallucination validator for AL Legal.

After the primary sub-agent drafts a reply, this module runs a SECOND
LLM call (different session, fresh context) asking it to verify:
- Every legal claim references one of the provided citations
- No invented article numbers / case IDs
- Returns a confidence score 0.0-1.0 and a list of unsupported claims

If confidence < 0.85 (D-028 threshold), the response is downgraded with
a CTA "Parla con un notaio" and the unsupported claims are flagged.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List

logger = logging.getLogger("omnia.legal.validator")

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
MODEL = "gemini-3-flash-preview"
CONFIDENCE_THRESHOLD = 0.85

VALIDATOR_PROMPT = """Sei un revisore severo. Devi valutare se la RISPOSTA scritta da un assistente legale è interamente supportata dalle FONTI fornite.

Output OBBLIGATORIO: SOLO JSON valido, senza markdown, senza commento.
Schema:
{
  "confidence": numero tra 0.0 e 1.0,
  "unsupported_claims": ["claim 1", "claim 2", ...],
  "fabricated_refs": ["art. 9999 c.c.", "Sent. Cass. 99999/2099", ...],
  "rationale": "1-2 frasi"
}

Criteri:
- confidence = 1.0 → ogni affermazione giuridica è verificabile nelle FONTI
- confidence = 0.5 → almeno una citazione [n] è plausibile ma non confermata dalle FONTI
- confidence = 0.0 → presenza di riferimenti normativi inventati o claim chiaramente non supportati
- unsupported_claims: elenca testualmente le frasi della RISPOSTA che non hanno supporto nelle FONTI
- fabricated_refs: elenca articoli/sentenze citati che NON compaiono nelle FONTI
"""


async def validate(answer: str, sources_block: str) -> Dict[str, Any]:
    """Run anti-hallucination check.

    Returns dict {confidence, unsupported_claims, fabricated_refs, rationale}.
    Defaults to confidence=0.5 + rationale="validator_unavailable" on errors,
    so the user still gets the response but with the cautionary CTA.
    """
    if not EMERGENT_LLM_KEY:
        return {"confidence": 0.5, "unsupported_claims": [], "fabricated_refs": [],
                "rationale": "validator_no_key"}

    user_msg = (
        f"FONTI:\n{sources_block}\n\n"
        f"RISPOSTA DA VALUTARE:\n{answer}\n\n"
        "Restituisci ora SOLO il JSON con il tuo verdetto."
    )

    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        client = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"legal-validator-{abs(hash(answer)) % 10_000_000:07d}",
            system_message=VALIDATOR_PROMPT,
        ).with_model("gemini", MODEL)
        raw = await client.send_message(UserMessage(text=user_msg))
    except Exception as e:
        logger.warning("Validator LLM failed: %s", e)
        return {"confidence": 0.5, "unsupported_claims": [], "fabricated_refs": [],
                "rationale": "validator_error"}

    # Extract JSON from raw (strip fences if present)
    cleaned = (raw or "").strip()
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
    except Exception:
        # Fallback: find first {...} block
        m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not m:
            return {"confidence": 0.5, "unsupported_claims": [], "fabricated_refs": [],
                    "rationale": "validator_parse_error"}
        try:
            parsed = json.loads(m.group(0))
        except Exception:
            return {"confidence": 0.5, "unsupported_claims": [], "fabricated_refs": [],
                    "rationale": "validator_json_invalid"}

    # Normalize
    conf = parsed.get("confidence")
    try:
        conf = float(conf)
        conf = max(0.0, min(1.0, conf))
    except Exception:
        conf = 0.5

    def _strlist(v: Any) -> List[str]:
        if isinstance(v, list):
            return [str(x)[:400] for x in v if x]
        return []

    return {
        "confidence": conf,
        "unsupported_claims": _strlist(parsed.get("unsupported_claims")),
        "fabricated_refs": _strlist(parsed.get("fabricated_refs")),
        "rationale": str(parsed.get("rationale") or "")[:500],
    }


def append_disclaimers(answer: str, confidence: float, sources_present: bool) -> str:
    """Append legal disclaimer + CTA notaio when confidence < threshold."""
    parts = [answer.rstrip()]

    if not sources_present:
        parts.append(
            "\n\n⚠️ Non ho trovato fonti normative ufficiali per questa specifica domanda. "
            "Le informazioni sopra hanno carattere puramente orientativo e devono essere "
            "verificate con un professionista."
        )
    elif confidence < CONFIDENCE_THRESHOLD:
        parts.append(
            "\n\n⚠️ La risposta sopra è orientativa e potrebbe non coprire tutti gli aspetti "
            "del tuo caso specifico. Ti suggerisco di parlare con un notaio o avvocato di "
            "fiducia prima di prendere decisioni."
        )

    return "".join(parts)
