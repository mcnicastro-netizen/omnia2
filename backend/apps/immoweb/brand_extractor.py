"""OMNIA — Brand Profile Extractor (M2.S5 Layer D Phase 1, D-023).

Crawl an agency's existing website + ask Gemini-3-flash to extract a structured
"Brand Profile" (palette/typography/structure/voice). Saved on Agency.website.brand_profile
for later consumption by the Theme Registry (M2.S6, D-022).
"""
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlparse
from uuid import uuid4

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from shared.auth.dependencies import require_roles
from shared.db.connection import Database

logger = logging.getLogger("omnia.brand_extract")
router = APIRouter(prefix="/website", tags=["website"])


SYSTEM_PROMPT = """Sei un brand & UI designer esperto.
Ricevi l'HTML di una homepage di un sito di un'agenzia immobiliare italiana.
Devi estrarre un **brand profile** strutturato in JSON.

REGOLE FERREE:
- Rispondi SOLO con un oggetto JSON valido, niente prima o dopo.
- Lingua: italiano.
- Sii pragmatico: se un dato non è deducibile, metti null.

SCHEMA:
{
  "palette": {
    "primary": "#hex",         // colore brand dominante
    "accent": "#hex",          // colore accent secondario
    "neutral_dark": "#hex",    // testo principale
    "neutral_light": "#hex"    // sfondi chiari
  },
  "typography": {
    "headings_family": "string",     // famiglia font intuita per titoli (es. 'Playfair Display' o generic 'serif')
    "body_family": "string",
    "scale": "compact" | "comfortable" | "spacious"
  },
  "structure": {
    "header_style": "minimal" | "classic" | "bold",
    "hero_type": "image_full" | "text_left_image_right" | "search_box_centered" | "carousel" | "none",
    "navigation": "horizontal_top" | "sidebar" | "hamburger_only",
    "card_style": "minimal_border" | "shadow_lift" | "image_dominant" | "list_compact"
  },
  "voice": {
    "tone": "professionale" | "familiare" | "lusso" | "tecnico" | "amichevole",
    "tagline_guess": "string o null"
  },
  "logo_hint": {
    "url": "string assoluto o null",
    "alt": "string o null"
  },
  "confidence": 0-100      // quanto sei sicuro dell'estrazione, intero
}
"""


class ExtractRequest(BaseModel):
    url: HttpUrl


async def _fetch_html(url: str) -> Dict[str, Any]:
    """Fetch URL and extract a compact summary for the LLM."""
    headers = {
        "User-Agent": "OMNIA-BrandBot/1.0 (+https://omniarealestateecosystem.it)",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    }
    timeout = httpx.Timeout(20.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text[:200_000]  # cap to 200KB

    soup = BeautifulSoup(html, "html.parser")
    # Title + meta description
    title = (soup.title.string.strip() if soup.title and soup.title.string else "") or ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = (desc_tag.get("content", "").strip() if desc_tag else "")
    # Logo candidate: first <img> with class containing 'logo' or near header
    logo = None
    for img in soup.find_all("img")[:30]:
        cls = " ".join(img.get("class") or [])
        alt = (img.get("alt") or "")
        if "logo" in cls.lower() or "logo" in alt.lower() or "logo" in (img.get("src") or "").lower():
            logo = {"url": urljoin(url, img.get("src", "")), "alt": alt}
            break
    # Nav items
    nav_items = []
    for a in soup.select("nav a, header a")[:20]:
        text = a.get_text(strip=True)
        if text and len(text) < 40:
            nav_items.append(text)
    # First H1
    h1 = soup.find("h1")
    hero = h1.get_text(strip=True)[:200] if h1 else ""
    # Inline style hint (max 5KB)
    inline_styles = " ".join(
        (s.string or "")[:1000] for s in soup.find_all("style")[:5]
    )[:5000]
    # First 3 stylesheets refs
    css_refs = [
        urljoin(url, link.get("href", ""))
        for link in soup.find_all("link", rel="stylesheet")[:3]
        if link.get("href")
    ]
    return {
        "url": url,
        "title": title,
        "description": description,
        "logo": logo,
        "nav_items": nav_items[:15],
        "hero_text": hero,
        "inline_styles_snippet": inline_styles,
        "css_refs": css_refs,
    }


async def _gemini_brand_profile(summary: Dict[str, Any]) -> Dict[str, Any]:
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="emergent_llm_key_missing")
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage  # type: ignore
        chat = LlmChat(
            api_key=api_key,
            session_id=f"brand-extract-{uuid4()}",
            system_message=SYSTEM_PROMPT,
        ).with_model("gemini", "gemini-3-flash-preview")
        user_text = "Estrai il brand profile dal seguente riepilogo HTML:\n\n" + json.dumps(summary, ensure_ascii=False)[:18000]
        raw = await chat.send_message(UserMessage(text=user_text))
        text = (raw or "").strip()
        if text.startswith("```"):
            text = text.split("```", 2)[1] if text.count("```") >= 2 else text
            if text.lower().startswith("json"):
                text = text[4:]
        data = json.loads(text.strip())
        # Light sanitization
        for hex_field in ("primary", "accent", "neutral_dark", "neutral_light"):
            v = data.get("palette", {}).get(hex_field)
            if v and not re.match(r"^#[0-9A-Fa-f]{6}$", str(v).strip()):
                data["palette"][hex_field] = None
        confidence = int(data.get("confidence", 0) or 0)
        data["confidence"] = max(0, min(100, confidence))
        return data
    except json.JSONDecodeError as e:
        logger.warning(f"Gemini brand profile JSON decode failed: {e}")
        raise HTTPException(status_code=502, detail="ai_response_invalid")
    except Exception as e:
        logger.warning(f"Brand profile extraction failed: {type(e).__name__}: {e}")
        raise HTTPException(status_code=502, detail=f"extraction_failed: {type(e).__name__}")


from shared.auth.tenant import arequire_agency as _agency


@router.post("/extract-from-url")
async def extract_brand_profile(
    payload: ExtractRequest,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """🔥 D-023: dato l'URL del sito attuale dell'agenzia, estrae brand profile via Gemini.
    Salva il risultato in `agency.website.brand_profile` per la successiva generazione bundle (M2.S6).
    """
    url = str(payload.url)
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="invalid_url_scheme")

    try:
        summary = await _fetch_html(url)
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"fetch_failed: {type(e).__name__}")

    profile = await _gemini_brand_profile(summary)

    # Persist on agency document
    agency_id = await _agency(user)
    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    profile_doc = {
        "brand_profile": profile,
        "extracted_from": url,
        "extracted_at": now,
        "title": summary.get("title"),
        "logo_hint": summary.get("logo"),
    }
    await db.agencies.update_one(
        {"id": agency_id},
        {"$set": {"website.extracted_profile": profile_doc, "updated_at": now}},
    )
    return {
        "agency_id": agency_id,
        "source_url": url,
        "summary": {
            "title": summary.get("title"),
            "description": summary.get("description"),
            "nav_items_found": len(summary.get("nav_items") or []),
            "logo_found": bool(summary.get("logo")),
        },
        "brand_profile": profile,
        "extracted_at": now,
    }
