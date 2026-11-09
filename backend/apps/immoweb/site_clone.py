"""OMNIA — Clone-from-URL (D-023 / D-130 / D-149 casi 1–2).

Fase A: crawl multi-pagina → `website.clone_capture`.
Fase B: brand → tema → preview visitabili home + lista + scheda → `clone_ready=true`.

Best-effort (non pixel-perfect). Dati vivi da API/portafoglio OMNIA.
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
from shared.db.public_visibility import brand_site_filter

logger = logging.getLogger("omnia.site_clone")
router = APIRouter(prefix="/website", tags=["website"])

_UA = "OMNIA-CloneCapture/0.1 (+https://omniarealestateecosystem.it)"
_LISTING_HINTS = re.compile(
    r"(immobili\.asp|propert(?:y|ies)|listing|annunc[iy]|vendita|affitto|ricerca|search|catalog|/immobili/?)",
    re.I,
)
_DETAIL_HINTS = re.compile(
    r"(immobile_dettaglio|dettagl|detail|scheda|cod_annuncio|property/|/id[=/]|rif[=/]|codice)",
    re.I,
)


class CloneCaptureRequest(BaseModel):
    url: HttpUrl
    max_pages: int = Field(default=8, ge=3, le=20)
    build: bool = Field(default=True, description="Dopo la cattura, genera preview e setta clone_ready")


class CloneBuildRequest(BaseModel):
    """Ricomputa preview da cattura già salvata (o da URL se passato)."""
    url: Optional[HttpUrl] = None


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
    parsed = urlparse(url)
    path = (parsed.path or "/").lower()
    query = (parsed.query or "").lower()
    blob = f"{path}?{query} {text[:400]}".lower()
    if is_seed or path in ("", "/", "/web", "/web/"):
        return "home"
    # Detail first: Nicastro uses immobile_dettaglio.asp?cod_annuncio=…
    if (
        "immobile_dettaglio" in path
        or "cod_annuncio=" in query
        or _DETAIL_HINTS.search(blob)
    ):
        if re.search(r"cod_annuncio=|immobile_dettaglio|scheda|detail|/\d{3,}(/)?$", blob):
            return "property"
    if _LISTING_HINTS.search(blob) or path.endswith("immobili.asp"):
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


def _scrape_palette_from_html(html: str) -> Dict[str, str]:
    """Fallback senza LLM: primi hex ricorrenti da CSS inline."""
    hexes = re.findall(r"#([0-9A-Fa-f]{6})\b", html or "")
    # Prefer non-white/black-ish
    ranked: List[str] = []
    for h in hexes:
        full = f"#{h.upper()}"
        if full in ("#FFFFFF", "#000000", "#FFFEEE"):
            continue
        if full not in ranked:
            ranked.append(full)
        if len(ranked) >= 4:
            break
    if not ranked:
        return {}
    out: Dict[str, str] = {"primary": ranked[0]}
    if len(ranked) > 1:
        out["accent"] = ranked[1]
    if len(ranked) > 2:
        out["neutral_dark"] = ranked[2]
    if len(ranked) > 3:
        out["neutral_light"] = ranked[3]
    return out


async def _run_capture(seed: str, max_pages: int) -> Dict[str, Any]:
    pages: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    home_html = ""
    timeout = httpx.Timeout(25.0, connect=10.0)
    headers = {"User-Agent": _UA, "Accept": "text/html", "Accept-Language": "it-IT,it;q=0.9"}

    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        try:
            final_url, html, status = await _fetch(client, seed)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"fetch_failed:{exc}") from exc
        if status >= 400 or not html:
            raise HTTPException(status_code=502, detail=f"seed_http_{status}")
        home_html = html
        pages.append(_page_summary(final_url, html, "home"))
        queue = _discover_links(final_url, html)

        for href in queue:
            if len(pages) >= max_pages:
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
            pages.append(_page_summary(u, h, role))

    roles = {p["role"] for p in pages}
    return {
        "id": str(uuid4()),
        "source_url": seed,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "pages": pages,
        "errors": errors[:20],
        "roles_found": sorted(roles),
        "has_home": True,
        "has_listing": "listing" in roles,
        "has_property": "property" in roles,
        "clone_ready": False,
        "phase": "capture",
        "home_palette_hint": _scrape_palette_from_html(home_html),
        "notes": "Cattura struttura OK.",
    }


async def _ensure_brand_and_theme(agency: Dict[str, Any], source_url: str, capture: Dict[str, Any]) -> Dict[str, Any]:
    """Estrae brand (LLM o fallback CSS) e applica theme_config clone."""
    from apps.immoweb.brand_extractor import _fetch_html, _gemini_brand_profile
    from apps.immoweb.theme_catalog import (
        THEME_HERO_IMAGES,
        auto_pick_theme,
        _palette_from_brand_profile,
        normalize_extracted_profile,
    )

    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    website = agency.get("website") or {}
    extracted = normalize_extracted_profile(website.get("extracted_profile"))
    brand_profile = extracted.get("brand_profile") or {}
    brand_source = "existing"

    need_extract = not (
        brand_profile.get("palette")
        or brand_profile.get("voice")
        or extracted.get("logo_hint")
    )
    if need_extract:
        try:
            summary = await _fetch_html(source_url)
            brand_profile = await _gemini_brand_profile(summary)
            extracted = {
                "brand_profile": brand_profile,
                "extracted_from": source_url,
                "extracted_at": now,
                "title": summary.get("title"),
                "logo_hint": summary.get("logo"),
            }
            brand_source = "gemini"
        except Exception as exc:
            logger.warning("clone brand LLM fallback: %s", exc)
            palette = capture.get("home_palette_hint") or {}
            logo = None
            for p in capture.get("pages") or []:
                logos = p.get("logo_candidates") or []
                if logos:
                    logo = {"url": logos[0], "alt": "logo"}
                    break
            brand_profile = {
                "palette": palette,
                "voice": {"tone": "professionale", "tagline_guess": None},
                "structure": {"header_style": "classic", "hero_type": "image_full", "card_style": "image_dominant"},
                "confidence": 40 if palette else 20,
            }
            extracted = {
                "brand_profile": brand_profile,
                "extracted_from": source_url,
                "extracted_at": now,
                "logo_hint": logo,
                "source": "css_fallback",
            }
            brand_source = "css_fallback"

    theme_id = auto_pick_theme(brand_profile)
    # Nicastro / siti classici agenzia IT → classic di default se confidence bassa
    if theme_id == "minimal" and (brand_profile.get("structure") or {}).get("header_style") == "classic":
        theme_id = "classic"
    palette = _palette_from_brand_profile(brand_profile) or (capture.get("home_palette_hint") or {})
    logo_url = (extracted.get("logo_hint") or {}).get("url")
    tagline = (brand_profile.get("voice") or {}).get("tagline_guess")
    theme_config = {
        "theme_id": theme_id,
        "palette": palette,
        "typography": {},
        "logo_url": logo_url,
        "tagline": tagline,
        "hero_image_url": THEME_HERO_IMAGES.get(theme_id),
        "applied_at": now,
        "source": f"clone_build:{brand_source}",
    }
    await db.agencies.update_one(
        {"id": agency["id"]},
        {
            "$set": {
                "website.theme_config": theme_config,
                "website.extracted_profile": extracted,
                "updated_at": now,
            }
        },
    )
    updated = await db.agencies.find_one({"id": agency["id"]})
    return updated or agency


def _smoke_ok(html: str, marker: str) -> bool:
    return bool(html) and marker in html and len(html) > 400


async def _build_clone_preview(agency: Dict[str, Any], capture: Dict[str, Any]) -> Dict[str, Any]:
    """Genera preview home+lista+scheda e marca clone_ready."""
    from apps.immoweb.theme_render import render_index, render_listing, render_property

    db = Database.get()
    slug = agency.get("slug") or "agency"
    props = await db.properties.find(
        brand_site_filter(agency["id"]), {"_id": 0},
    ).sort("updated_at", -1).to_list(length=48)

    # Enrich MLS bits like site_index (best-effort)
    agency_view = dict(agency)
    if agency.get("mls_enabled"):
        agency_view["_mls_network_count"] = int(agency.get("_mls_network_count") or 0)
        agency_view["_mls_network_props"] = list(agency.get("_mls_network_props") or [])

    home_html = render_index(agency_view, props, slug)
    list_html = render_listing(agency_view, props, slug)
    first = props[0] if props else None
    if first:
        prop_html = render_property(agency_view, first, slug)
        property_path = f"/api/p/{slug}/{first['id']}"
        property_mode = "live"
    else:
        sample = next((p for p in (capture.get("pages") or []) if p.get("role") == "property"), None)
        stub = {
            "id": "clone-preview",
            "title": (sample or {}).get("h1") or (sample or {}).get("title") or "Scheda preview clone",
            "city": (agency.get("address") or {}).get("city") or "",
            "zone": "",
            "operation": "sale",
            "price": None,
            "photos": [],
            "features": {},
            "energy": {},
            "description": "Anteprima scheda clone — portafoglio OMNIA ancora vuoto.",
            "reference_code": "CLONE-PREVIEW",
            "property_type": "apartment",
        }
        prop_html = render_property(agency_view, stub, slug)
        property_path = f"/api/p/{slug}/clone-scheda-preview"
        property_mode = "stub"

    checks = {
        "home": _smoke_ok(home_html, 'data-testid="agency-home"'),
        "listing": _smoke_ok(list_html, 'data-testid="agency-listing"'),
        "property": _smoke_ok(prop_html, "<h1"),
    }
    if not all(checks.values()):
        raise HTTPException(status_code=500, detail=f"clone_smoke_failed:{checks}")

    now = datetime.now(timezone.utc).isoformat()
    preview = {
        "home": f"/api/p/{slug}/",
        "listing": f"/api/p/{slug}/lista",
        "property": property_path,
        "property_mode": property_mode,
        "built_at": now,
        "smoke": checks,
        "theme_id": ((agency.get("website") or {}).get("theme_config") or {}).get("theme_id"),
        "source_url": capture.get("source_url"),
        "best_effort": True,
        "notes": (
            "Preview visitabile home + lista + scheda su OMNIA (best-effort). "
            "Non è garanzia pixel-perfect sul sito originale."
        ),
    }
    capture_out = dict(capture)
    capture_out["clone_ready"] = True
    capture_out["phase"] = "preview"
    capture_out["notes"] = preview["notes"]

    await db.agencies.update_one(
        {"id": agency["id"]},
        {
            "$set": {
                "website.clone_ready": True,
                "website.clone_preview": preview,
                "website.clone_capture": capture_out,
                "website.clone_built_at": now,
                "updated_at": now,
            }
        },
    )
    return preview


@router.post("/clone-capture")
async def clone_capture(
    body: CloneCaptureRequest,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Cattura (+ build default) → clone_ready quando le 3 preview smoke-passano."""
    aid = _agency_id(user)
    db = Database.get()
    agency = await db.agencies.find_one({"id": aid})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")

    seed = str(body.url).rstrip("/")
    if not seed.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="invalid_url")

    capture = await _run_capture(seed, body.max_pages)
    now = datetime.now(timezone.utc).isoformat()
    await db.agencies.update_one(
        {"id": aid},
        {
            "$set": {
                "website.clone_capture": capture,
                "website.clone_source_url": seed,
                "website.clone_ready": False,
                "updated_at": now,
            }
        },
    )

    preview = None
    clone_ready = False
    if body.build:
        agency = await db.agencies.find_one({"id": aid})
        agency = await _ensure_brand_and_theme(agency, seed, capture)
        preview = await _build_clone_preview(agency, capture)
        clone_ready = True

    return {
        "ok": True,
        "agency_id": aid,
        "agency_slug": agency.get("slug"),
        "clone_ready": clone_ready,
        "capture": (await db.agencies.find_one({"id": aid}, {"_id": 0, "website.clone_capture": 1}))
        .get("website", {})
        .get("clone_capture"),
        "preview": preview,
        "next": (
            "Apri le URL in preview.home / listing / property"
            if clone_ready
            else "Rilancia con build=true per generare le preview."
        ),
    }


@router.post("/clone-build")
async def clone_build(
    body: CloneBuildRequest = CloneBuildRequest(),
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Genera/rigenera preview da cattura esistente (o cattura di nuovo se url)."""
    aid = _agency_id(user)
    db = Database.get()
    agency = await db.agencies.find_one({"id": aid})
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    website = agency.get("website") or {}
    capture = website.get("clone_capture")
    source = str(body.url).rstrip("/") if body.url else (website.get("clone_source_url") or "")

    if body.url or not capture:
        if not source:
            raise HTTPException(status_code=400, detail="no_clone_source_url")
        capture = await _run_capture(source, 10)
        await db.agencies.update_one(
            {"id": aid},
            {"$set": {"website.clone_capture": capture, "website.clone_source_url": source}},
        )
        agency = await db.agencies.find_one({"id": aid})

    source = source or capture.get("source_url") or ""
    agency = await _ensure_brand_and_theme(agency, source, capture)
    preview = await _build_clone_preview(agency, capture)
    return {
        "ok": True,
        "agency_id": aid,
        "agency_slug": agency.get("slug"),
        "clone_ready": True,
        "preview": preview,
        "mls_enabled": bool(agency.get("mls_enabled")),
        "migration_case": "case_1_mls" if agency.get("mls_enabled") else "case_2_no_mls",
    }


@router.get("/clone-capture")
async def get_clone_capture(
    user: dict = Depends(require_roles("agency_admin", "agent", "super_admin")),
):
    aid = _agency_id(user)
    db = Database.get()
    agency = await db.agencies.find_one(
        {"id": aid},
        {
            "_id": 0,
            "website.clone_capture": 1,
            "website.clone_source_url": 1,
            "website.clone_ready": 1,
            "website.clone_preview": 1,
            "mls_enabled": 1,
            "slug": 1,
        },
    )
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    website = agency.get("website") or {}
    ready = bool(website.get("clone_ready") or (website.get("clone_capture") or {}).get("clone_ready"))
    return {
        "agency_id": aid,
        "agency_slug": agency.get("slug"),
        "mls_enabled": bool(agency.get("mls_enabled")),
        "migration_case": "case_1_mls" if agency.get("mls_enabled") else "case_2_no_mls",
        "clone_source_url": website.get("clone_source_url"),
        "capture": website.get("clone_capture"),
        "preview": website.get("clone_preview"),
        "clone_ready": ready,
    }
