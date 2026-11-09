"""OMNIA themes — catalog + config resolution (MOVE-ONLY from themes.py)."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("omnia.themes")

THEME_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "minimal",
        "name": "Minimal",
        "description": "Sobrio, tipografia editoriale, molto spazio bianco. Ideale per agenzie boutique.",
        "best_for": ["familiare", "professionale"],
        "preview_palette": {"primary": "#1c1917", "accent": "#1f6b5c", "neutral_light": "#fafaf9"},
        "header_style": "minimal",
        "card_style": "minimal_border",
        "hero_image": "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=1600&q=80&auto=format&fit=crop",
    },
    {
        "id": "classic",
        "name": "Classic",
        "description": "Layout tradizionale ben strutturato, ottimo per portafogli ampi e clientela mainstream.",
        "best_for": ["professionale", "familiare"],
        "preview_palette": {"primary": "#0B1E3F", "accent": "#C19A6B", "neutral_light": "#f5f3ee"},
        "header_style": "classic",
        "card_style": "shadow_lift",
        "hero_image": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=1600&q=80&auto=format&fit=crop",
    },
    {
        "id": "bold",
        "name": "Bold",
        "description": "Tipografia grande e contrasti netti. Adatto ad agenzie moderne e ad alto volume.",
        "best_for": ["tecnico", "professionale"],
        "preview_palette": {"primary": "#FF5A1F", "accent": "#111111", "neutral_light": "#ffffff"},
        "header_style": "bold",
        "card_style": "image_dominant",
        "hero_image": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1600&q=80&auto=format&fit=crop",
    },
    {
        "id": "luxury",
        "name": "Luxury",
        "description": "Toni scuri, oro, immagini protagoniste. Pensato per immobili di prestigio.",
        "best_for": ["lusso"],
        "preview_palette": {"primary": "#0a0a0a", "accent": "#B89D5E", "neutral_light": "#fafafa"},
        "header_style": "bold",
        "card_style": "image_dominant",
        "hero_image": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1600&q=80&auto=format&fit=crop",
    },
]

THEME_IDS = {t["id"] for t in THEME_CATALOG}

DEFAULT_THEME_ID = "minimal"

DEFAULT_HERO_IMAGE = (
    "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=1600&q=80&auto=format&fit=crop"
)

THEME_HERO_IMAGES = {t["id"]: t.get("hero_image") or DEFAULT_HERO_IMAGE for t in THEME_CATALOG}

DEFAULT_PALETTES = {
    "minimal": {"primary": "#1c1917", "accent": "#1f6b5c",
                "neutral_dark": "#1c1917", "neutral_light": "#fafaf9"},
    "classic": {"primary": "#0B1E3F", "accent": "#C19A6B",
                "neutral_dark": "#1c1917", "neutral_light": "#f5f3ee"},
    "bold":    {"primary": "#FF5A1F", "accent": "#111111",
                "neutral_dark": "#111111", "neutral_light": "#ffffff"},
    "luxury":  {"primary": "#0a0a0a", "accent": "#B89D5E",
                "neutral_dark": "#0a0a0a", "neutral_light": "#fafafa"},
}

DEFAULT_TYPOGRAPHY = {
    "minimal": {"headings": "'Fraunces', Georgia, serif", "body": "system-ui, -apple-system, sans-serif"},
    "classic": {"headings": "'Playfair Display', Georgia, serif", "body": "Georgia, 'Times New Roman', serif"},
    "bold":    {"headings": "'Inter', system-ui, sans-serif", "body": "'Inter', system-ui, sans-serif"},
    "luxury":  {"headings": "'Playfair Display', Georgia, serif", "body": "'Inter', system-ui, sans-serif"},
}

def _resolve_theme_config(agency: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve effective theme config for an agency.

    Priority:
      1. agency.website.theme_config (explicit, saved by user)
      2. defaults for selected theme_id
      3. global default (`minimal`)
    """
    website = (agency.get("website") or {})
    cfg = (website.get("theme_config") or {})
    theme_id = cfg.get("theme_id") if cfg.get("theme_id") in THEME_IDS else DEFAULT_THEME_ID

    palette = {**DEFAULT_PALETTES[theme_id], **(cfg.get("palette") or {})}
    # Sanitize hex codes
    import re as _re
    for k, v in list(palette.items()):
        if not isinstance(v, str) or not _re.match(r"^#[0-9A-Fa-f]{6}$", v):
            palette[k] = DEFAULT_PALETTES[theme_id][k]

    typography = {**DEFAULT_TYPOGRAPHY[theme_id], **(cfg.get("typography") or {})}

    branding = agency.get("branding") or {}
    logo_url = cfg.get("logo_url") or branding.get("logo_url")
    tagline = cfg.get("tagline") or branding.get("tagline")

    return {
        "theme_id": theme_id,
        "palette": palette,
        "typography": typography,
        "logo_url": logo_url,
        "tagline": tagline,
    }

def _resolve_hero_image(agency: Dict[str, Any], cfg: Dict[str, Any]) -> str:
    """Hero banner: agency override → theme default → global default."""
    branding = agency.get("branding") or {}
    website = agency.get("website") or {}
    theme_cfg = website.get("theme_config") or {}
    for candidate in (
        theme_cfg.get("hero_image_url"),
        branding.get("hero_image_url"),
        THEME_HERO_IMAGES.get(cfg.get("theme_id") or ""),
        DEFAULT_HERO_IMAGE,
    ):
        if isinstance(candidate, str) and candidate.startswith(("http://", "https://", "/")):
            return candidate
    return DEFAULT_HERO_IMAGE

def auto_pick_theme(brand_profile: Dict[str, Any]) -> str:
    """Heuristic mapping from extracted brand_profile → theme_id."""
    if not brand_profile or not isinstance(brand_profile, dict):
        return DEFAULT_THEME_ID
    voice = (brand_profile.get("voice") or {}).get("tone") or ""
    structure = brand_profile.get("structure") or {}
    header_style = structure.get("header_style") or ""
    card_style = structure.get("card_style") or ""

    if voice == "lusso":
        return "luxury"
    if header_style == "bold" or card_style == "image_dominant":
        return "bold"
    if voice in ("familiare", "amichevole"):
        return "classic"
    if header_style == "classic":
        return "classic"
    if voice == "tecnico":
        return "bold"
    return "minimal"

def _palette_from_brand_profile(brand_profile: Dict[str, Any]) -> Dict[str, str]:
    """Extract a usable palette dict from the brand_profile (or empty)."""
    palette = (brand_profile or {}).get("palette") or {}
    out: Dict[str, str] = {}
    import re as _re
    for k in ("primary", "accent", "neutral_dark", "neutral_light"):
        v = palette.get(k)
        if isinstance(v, str) and _re.match(r"^#[0-9A-Fa-f]{6}$", v.strip()):
            out[k] = v.strip()
    return out

def normalize_extracted_profile(extracted: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Accept extractor shape (`brand_profile` nested) and seed/legacy flat shape.

    Seed Nicastro wrote palette/voice/logo_hint on extracted_profile itself.
    Auto-configure used to 400 `no_extracted_profile` because it only read
    `extracted_profile.brand_profile`.
    """
    extracted = dict(extracted or {})
    bp = extracted.get("brand_profile")
    nested_ok = isinstance(bp, dict) and bool(
        bp.get("palette") or bp.get("voice") or bp.get("confidence") or bp.get("logo_hint")
    )
    if nested_ok:
        if not extracted.get("logo_hint") and bp.get("logo_hint"):
            extracted["logo_hint"] = bp.get("logo_hint")
        return extracted
    if extracted.get("palette") or extracted.get("voice") or extracted.get("logo_hint"):
        logo = extracted.get("logo_hint")
        return {
            "brand_profile": {
                "palette": extracted.get("palette") or {},
                "typography": extracted.get("typography") or {},
                "structure": extracted.get("structure") or {},
                "voice": extracted.get("voice") or {},
                "logo_hint": logo,
                "confidence": extracted.get("confidence") or 0,
            },
            "logo_hint": logo,
            "extracted_from": extracted.get("extracted_from") or extracted.get("source_url"),
            "source_url": extracted.get("source_url") or extracted.get("extracted_from"),
            "extracted_at": extracted.get("extracted_at"),
            "title": extracted.get("title"),
            "assisted": extracted.get("assisted"),
            "note": extracted.get("note"),
        }
    return extracted

