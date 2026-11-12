"""OMNIA — Theme Registry & Site Generation (M2.S5 Layer D Phase 2, D-022).

MOVE-ONLY split: catalog → theme_catalog.py · CSS → theme_css.py ·
shell/helpers → theme_common.py · home → theme_home.py · property → theme_render.py.
This module keeps the FastAPI /website router and re-exports public symbols.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from shared.auth.dependencies import require_roles, get_current_user
from shared.db.connection import Database

from apps.immoweb.theme_catalog import (
    DEFAULT_HERO_IMAGE,
    DEFAULT_PALETTES,
    DEFAULT_THEME_ID,
    DEFAULT_TYPOGRAPHY,
    THEME_CATALOG,
    THEME_HERO_IMAGES,
    THEME_IDS,
    THEME_ROADMAP,
    _palette_from_brand_profile,
    _resolve_hero_image,
    _resolve_theme_config,
    auto_pick_theme,
    normalize_extracted_profile,
)
from apps.immoweb.theme_render import (
    render_index,
    render_listing,
    render_property,
)

logger = logging.getLogger("omnia.themes")
router = APIRouter(prefix="/website", tags=["website"])

class PaletteOverride(BaseModel):
    primary: Optional[str] = None
    accent: Optional[str] = None
    neutral_dark: Optional[str] = None
    neutral_light: Optional[str] = None

class TypographyOverride(BaseModel):
    headings: Optional[str] = None
    body: Optional[str] = None

class ApplyThemeRequest(BaseModel):
    theme_id: str = Field(..., min_length=2, max_length=20)
    palette: Optional[PaletteOverride] = None
    typography: Optional[TypographyOverride] = None
    logo_url: Optional[str] = Field(default=None, max_length=500)
    tagline: Optional[str] = Field(default=None, max_length=200)
    hero_image_url: Optional[str] = Field(default=None, max_length=500)


class SitePresenceRequest(BaseModel):
    """Scelta semplice: sito già mio (external) oppure vetrina OMNIA."""

    mode: Literal["external", "omnia_template"]
    external_url: Optional[str] = Field(default=None, max_length=500)


def _normalize_site_url(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    u = str(raw).strip()
    if not u:
        return None
    if " " in u or "\n" in u:
        raise HTTPException(status_code=400, detail="invalid_url")
    if not u.startswith(("http://", "https://")):
        u = f"https://{u}"
    parsed = urlparse(u)
    host = (parsed.netloc or "").split("@")[-1].split(":")[0]
    if parsed.scheme not in ("http", "https") or not host or "." not in host:
        raise HTTPException(status_code=400, detail="invalid_url")
    return u.rstrip("/")


async def _agency_for(user: dict) -> Dict[str, Any]:
    from shared.auth.tenant import require_agency
    aid = require_agency(user)
    db = Database.get()
    a = await db.agencies.find_one({"id": aid})
    if not a:
        raise HTTPException(status_code=404, detail="agency_not_found")
    return a

@router.post("/presence")
async def set_site_presence(
    payload: SitePresenceRequest,
    user: dict = Depends(require_roles("agency_admin", "super_admin", "group_admin")),
):
    """Salva la scelta sito: esterno (già mio) o vetrina OMNIA."""
    agency = await _agency_for(user)
    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    url = _normalize_site_url(payload.external_url)
    website = agency.get("website") or {}
    if payload.mode == "external" and not url:
        url = (website.get("external_url") or "").strip() or None
        if not url and agency.get("existing_domain"):
            ed = str(agency.get("existing_domain")).strip()
            url = ed if ed.startswith("http") else f"https://{ed}"
        if not url:
            raise HTTPException(
                status_code=400,
                detail={"error": "url_required", "hint": "Inserisci l’indirizzo del tuo sito"},
            )
    sets: Dict[str, Any] = {
        "website.mode": payload.mode,
        "updated_at": now,
    }
    if url:
        sets["website.external_url"] = url
    await db.agencies.update_one({"id": agency["id"]}, {"$set": sets})
    updated = await db.agencies.find_one({"id": agency["id"]})
    web = (updated or {}).get("website") or {}
    return {
        "ok": True,
        "website_mode": web.get("mode"),
        "external_url": web.get("external_url"),
        "public_url": f"/api/p/{agency.get('slug')}/",
    }


@router.get("/themes")
async def list_themes(_: dict = Depends(get_current_user)):
    """Theme picker: catalogo temi live (roadmap nascosta in UI semplice)."""
    return {
        "themes": THEME_CATALOG,
        "roadmap": THEME_ROADMAP,
        "default_theme_id": DEFAULT_THEME_ID,
        "mls_matrix": True,
        "target_live_count": {"min": 5, "max": 10},
    }

@router.get("/theme")
async def get_current_theme(user: dict = Depends(get_current_user)):
    """Return the currently saved theme_config for the user's agency,
    plus the resolved effective config."""
    agency = await _agency_for(user)
    website = agency.get("website") or {}
    saved = website.get("theme_config")
    resolved = _resolve_theme_config(agency)
    extracted = normalize_extracted_profile(website.get("extracted_profile"))
    clone_ready = bool(
        website.get("clone_ready")
        or (website.get("clone_capture") or {}).get("clone_ready")
    )
    external_url = (website.get("external_url") or "").strip() or None
    existing_domain = (agency.get("existing_domain") or "").strip() or None
    declared_url = external_url or (
        f"https://{existing_domain}" if existing_domain else None
    )
    # D-167 — stato percorso sito (solo campi già in Mongo; no auto-crawl)
    if extracted and clone_ready:
        site_phase = "clone_ready"
    elif extracted:
        site_phase = "brand_extracted"
    elif declared_url or website.get("mode") == "external":
        site_phase = "declared"
    elif saved or resolved:
        site_phase = "theme_only"
    else:
        site_phase = "none"
    return {
        "agency_id": agency["id"],
        "agency_slug": agency.get("slug"),
        "saved_theme_config": saved,
        "resolved": resolved,
        "extracted_profile": extracted,
        "public_url": f"/api/p/{agency.get('slug')}/",
        "website_mode": website.get("mode"),
        "external_url": external_url,
        "existing_domain": existing_domain,
        "declared_url": declared_url,
        "clone_ready": clone_ready,
        "clone_source_url": website.get("clone_source_url"),
        "site_phase": site_phase,
    }

@router.post("/theme/apply")
async def apply_theme(
    payload: ApplyThemeRequest,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Save the chosen theme + overrides on agency.website.theme_config."""
    if payload.theme_id not in THEME_IDS:
        raise HTTPException(status_code=400, detail="invalid_theme_id")
    agency = await _agency_for(user)
    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()

    palette = (payload.palette.model_dump(exclude_none=True) if payload.palette else {}) or {}
    typography = (payload.typography.model_dump(exclude_none=True) if payload.typography else {}) or {}

    theme_config = {
        "theme_id": payload.theme_id,
        "palette": palette,
        "typography": typography,
        "logo_url": payload.logo_url,
        "tagline": payload.tagline,
        "hero_image_url": payload.hero_image_url or THEME_HERO_IMAGES.get(payload.theme_id),
        "applied_at": now,
    }
    await db.agencies.update_one(
        {"id": agency["id"]},
        {"$set": {"website.theme_config": theme_config, "updated_at": now}},
    )
    updated = await db.agencies.find_one({"id": agency["id"]})
    return {
        "ok": True,
        "applied_at": now,
        "resolved": _resolve_theme_config(updated),
        "public_url": f"/api/p/{agency.get('slug')}/",
    }

@router.post("/theme/auto-configure")
async def auto_configure(
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Picks the best theme + palette from the previously extracted brand_profile.
    Saves it as the active theme_config and returns the resolved config."""
    agency = await _agency_for(user)
    extracted = normalize_extracted_profile((agency.get("website") or {}).get("extracted_profile"))
    brand_profile = extracted.get("brand_profile") or {}
    if not (
        brand_profile.get("palette")
        or brand_profile.get("voice")
        or extracted.get("logo_hint")
    ):
        raise HTTPException(status_code=400, detail="no_extracted_profile")

    theme_id = auto_pick_theme(brand_profile)
    palette = _palette_from_brand_profile(brand_profile)
    logo_url = (extracted.get("logo_hint") or {}).get("url")
    tagline = (brand_profile.get("voice") or {}).get("tagline_guess")

    db = Database.get()
    now = datetime.now(timezone.utc).isoformat()
    theme_config = {
        "theme_id": theme_id,
        "palette": palette,
        "typography": {},
        "logo_url": logo_url,
        "tagline": tagline,
        "applied_at": now,
        "source": "auto_from_extracted",
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
    return {
        "ok": True,
        "theme_id": theme_id,
        "applied_at": now,
        "resolved": _resolve_theme_config(updated),
        "public_url": f"/api/p/{agency.get('slug')}/",
    }

@router.get("/preview/{theme_id}", response_class=Response)
async def preview_theme(
    theme_id: str,
    user: dict = Depends(get_current_user),
):
    """Render the listings index for the user's agency with a *transient* theme
    override (does not persist). Used by the live-preview iframe in the UI."""
    if theme_id not in THEME_IDS:
        raise HTTPException(status_code=400, detail="invalid_theme_id")
    agency = await _agency_for(user)

    # Inject a transient theme_config into a shallow copy of agency
    extracted = normalize_extracted_profile((agency.get("website") or {}).get("extracted_profile"))
    bp = extracted.get("brand_profile") or {}
    transient = dict(agency)
    transient_website = dict(agency.get("website") or {})
    transient_website["theme_config"] = {
        "theme_id": theme_id,
        "palette": _palette_from_brand_profile(bp),
        "typography": {},
        "logo_url": (extracted.get("logo_hint") or {}).get("url")
                    or (agency.get("branding") or {}).get("logo_url"),
        "tagline": (bp.get("voice") or {}).get("tagline_guess")
                   or (agency.get("branding") or {}).get("tagline"),
        "hero_image_url": THEME_HERO_IMAGES.get(theme_id) or DEFAULT_HERO_IMAGE,
    }
    transient["website"] = transient_website

    from shared.db.public_visibility import brand_site_filter

    db = Database.get()
    props = await db.properties.find(
        brand_site_filter(agency["id"]), {"_id": 0},
    ).sort("updated_at", -1).to_list(length=24)

    html = render_index(transient, props, agency.get("slug") or "preview")
    return Response(content=html, media_type="text/html; charset=utf-8",
                    headers={"X-Robots-Tag": "noindex"})

