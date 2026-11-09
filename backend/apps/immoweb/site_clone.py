"""OMNIA — Clone-from-URL capture (D-023 / D-130 / D-149 casi 1–2).

Fase A (questa): crawl multi-pagina best-effort (httpx + BS4) → salva
`agency.website.clone_capture` con home / lista / scheda candidate.
NON genera ancora bundle look-alike (Vision + render per-agenzia = fase B).

Onesto: `clone_ready=false` finché non esiste preview visitabile home+lista+scheda.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse
from uuid import uuid4

import httpx
from bs4 import BeautifulSoup
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, HttpUrl

from shared.auth.dependencies import require_roles
from shared.auth.tenant import optional_agency_id
from shared.db.connection import Database

logger = logging.getLogger("omnia.site_clone")
router = APIRouter(prefix="/website", tags=["website"])

_UA = "OMNIA-CloneCapture/0.1 (+https://omniarealestateecosystem.it)"
_LISTING_HINTS = re.compile(
    r"(immobil|propert|listing|annunc|vendita|affitto|ricerca|search|catalog)",
    re.I,
)
_DETAIL_HINTS = re.compile(
    r"(dettagl|detail|scheda|property/|/id|rif[=/]|codice)",
    re.I,
)


class CloneCaptureRequest(BaseModel):
    url: HttpUrl
    max_pages: int = Field(default=8, ge=3, le=20)


def _agency_id(user: dict) -> str:
    aid = optional_agency_id(user)
    if not aid:
        raise HTTPException(status_code=400, detail="no_active_agency")
    return aid


async def _fetch(client: httpx.AsyncClient, url: str) -> Tuple[str, str, int]:
    r = await client.get(url, follow_redirects=True)
    return str(r.url), r.text if "html" in (r.headers.get("content-type") or "") else "", r.status_code


def _same_host(base: str, candidate: str) -> bool:
    try:
        return urlparse(base).netloc == urlparse(candidate).netloc
    except Exception:
        return False


def _classify(url: str, text: str, is_seed: bool = False) -> str:
    path = (urlparse(url).path or "/").lower()
    blob = f"{path} {text[:400]}".lower()
    if is_seed or path in ("", "/"):
        return "home"
    if _DETAIL_HINTS.search(blob) and not _LISTING_HINTS.search(path):
        # detail-ish path with id-like segment
        if re.search(r"/\d{3,}(/)?$", path) or "scheda" in path or "detail" in path:
            return "property"
    if _LISTING_HINTS.search(blob):
        return "listing"
    if _DETAIL_HINTS.search(blob):
        return "property"
    return "other"


def _page_summary(url: str, html: str, role: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = (soup.title.string or "").strip() if soup.title else ""
    h1 = ""
    h1_el = soup.find("h1")
    if h1_el:
        h1 = h1_el.get_text(" ", strip=True)[:160]
    logos = []
    for img in soup.find_all("img", src=True)[:12]:
        alt = (img.get("alt") or "").lower()
        cls = " ".join(img.get("class") or []).lower()
        src = urljoin(url, img["src"])
        if "logo" in alt or "logo" in cls or "logo" in src.lower():
            logos.append(src)
    nav_links = []
    for a in soup.find_all("a", href=True)[:40]:
        href = urljoin(url, a["href"])
        label = a.get_text(" ", strip=True)[:80]
        if label and _same_host(url, href):
            nav_links.append({"href": href, "label": label})
    text_len = len(soup.get_text(" ", strip=True))
    return {
        "role": role,
        "url": url,
        "title": title[:200],
        "h1": h1,
        "logo_candidates": logos[:3],
        "nav_sample": nav_links[:12],
        "text_chars": text_len,
        "has_forms": bool(soup.find("form")),
    }


def _discover_links(seed: str, html: str) -> List[str]:
    soup = BeautifulSoup(html or "", "html.parser")
    out: List[str] = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(seed, a["href"]).split("#")[0]
        if href in seen or not _same_host(seed, href):
            continue
        if href.startswith("mailto:") or href.startswith("tel:"):
            continue
        seen.add(href)
        label = a.get_text(" ", strip=True)
        score = 0
        if _LISTING_HINTS.search(href) or _LISTING_HINTS.search(label):
            score += 2
        if _DETAIL_HINTS.search(href) or _DETAIL_HINTS.search(label):
            score += 1
        if score:
            out.append(href)
    return out


@router.post("/clone-capture")
async def clone_capture(
    body: CloneCaptureRequest,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Cattura multi-pagina per migrazione sito (casi 1–2). Non promette clone full."""
    aid = _agency_id(user)
    db = Database.get()
    agency = await db.agencies.find_one({"id": aid}, {"_id": 0, "id": 1, "slug": 1})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")

    seed = str(body.url).rstrip("/")
    if not seed.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="invalid_url")

    pages: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    timeout = httpx.Timeout(25.0, connect=10.0)
    headers = {"User-Agent": _UA, "Accept": "text/html", "Accept-Language": "it-IT,it;q=0.9"}

    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        try:
            final_url, html, status = await _fetch(client, seed)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"fetch_failed:{exc}") from exc
        if status >= 400 or not html:
            raise HTTPException(status_code=502, detail=f"seed_http_{status}")
        pages.append(_page_summary(final_url, html, "home"))
        queue = _discover_links(final_url, html)

        for href in queue:
            if len(pages) >= body.max_pages:
                break
            if any(p["url"] == href for p in pages):
                continue
            try:
                u, h, st = await _fetch(client, href)
            except Exception as exc:
                errors.append({"url": href, "error": str(exc)[:160]})
                continue
            if st >= 400 or not h:
                errors.append({"url": href, "error": f"http_{st}"})
                continue
            role = _classify(u, BeautifulSoup(h, "html.parser").get_text(" ", strip=True)[:500])
            # Prefer listing/property; skip pure other if we already have both roles later
            pages.append(_page_summary(u, h, role))

    roles = {p["role"] for p in pages}
    has_listing = "listing" in roles
    has_property = "property" in roles
    capture = {
        "id": str(uuid4()),
        "source_url": seed,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "pages": pages,
        "errors": errors[:20],
        "roles_found": sorted(roles),
        "has_home": True,
        "has_listing": has_listing,
        "has_property": has_property,
        # Fase A only — Vision + bundle = still open (D-023).
        "clone_ready": False,
        "phase": "capture",
        "notes": (
            "Cattura struttura OK. Preview look-alike home+lista+scheda "
            "non ancora generata (clone full in corso)."
        ),
    }

    await db.agencies.update_one(
        {"id": aid},
        {
            "$set": {
                "website.clone_capture": capture,
                "website.clone_source_url": seed,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    return {
        "ok": True,
        "agency_id": aid,
        "agency_slug": agency.get("slug"),
        "clone_ready": False,
        "capture": capture,
        "next": (
            "Usa Brand Extractor + tema per demo vestita; "
            "clone full (D-023) arriverà sulla base di questa cattura."
        ),
    }


@router.get("/clone-capture")
async def get_clone_capture(
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    aid = _agency_id(user)
    db = Database.get()
    agency = await db.agencies.find_one(
        {"id": aid},
        {"_id": 0, "website.clone_capture": 1, "website.clone_source_url": 1, "mls_enabled": 1, "slug": 1},
    )
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    website = agency.get("website") or {}
    return {
        "agency_id": aid,
        "agency_slug": agency.get("slug"),
        "mls_enabled": bool(agency.get("mls_enabled")),
        "migration_case": "case_1_mls" if agency.get("mls_enabled") else "case_2_no_mls",
        "clone_source_url": website.get("clone_source_url"),
        "capture": website.get("clone_capture"),
        "clone_ready": bool((website.get("clone_capture") or {}).get("clone_ready")),
    }
