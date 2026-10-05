"""OMNIA — Theme Registry & Site Generation (M2.S5 Layer D Phase 2, D-022).

Headless theme registry that consumes the Brand Profile extracted by
`brand_extractor.py` (Phase 1) and renders the agency public site
(`/api/p/{slug}/`) with the agency's own visual identity.

4 themes (minimal / classic / bold / luxury) — each a pair of `render_index`
+ `render_property` functions that produce SEO-clean HTML.
"""
import json
import logging
import os
from datetime import datetime, timezone
from html import escape
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from shared.auth.dependencies import require_roles, get_current_user
from shared.db.connection import Database

logger = logging.getLogger("omnia.themes")
router = APIRouter(prefix="/website", tags=["website"])


# ============================================================
# THEME CATALOG (static metadata, shown in the picker UI)
# ============================================================

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

# Hero banner di default (home pubblica) — override via branding.hero_image_url / theme_config
DEFAULT_HERO_IMAGE = (
    "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=1600&q=80&auto=format&fit=crop"
)
THEME_HERO_IMAGES = {t["id"]: t.get("hero_image") or DEFAULT_HERO_IMAGE for t in THEME_CATALOG}


# ============================================================
# THEME CONFIG (saved in DB on agency.website.theme_config)
# ============================================================

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


# ============================================================
# HTML BUILDING BLOCKS
# ============================================================

def _eur(v: Optional[float]) -> str:
    if v is None:
        return "—"
    try:
        return f"€ {int(v):,}".replace(",", ".")
    except Exception:
        return f"€ {v}"


def _price_str(p: Dict[str, Any]) -> str:
    if p.get("price"):
        return _eur(p["price"])
    if p.get("rent_monthly"):
        return f"{_eur(p['rent_monthly'])}/mese"
    return "—"


def _cover_url(p: Dict[str, Any]) -> Optional[str]:
    photos = p.get("photos") or []
    if not photos:
        return None
    cover_idx = next((i for i, ph in enumerate(photos) if ph.get("is_cover")), 0)
    return f"/api/public/property/{p['id']}/photo/{cover_idx}"


def _theme_css(cfg: Dict[str, Any]) -> str:
    """Generate the shared CSS-vars block + theme-specific overrides."""
    pal = cfg["palette"]
    typ = cfg["typography"]
    theme_id = cfg["theme_id"]

    base = f"""
    :root {{
      --o-primary: {pal['primary']};
      --o-accent: {pal['accent']};
      --o-dark: {pal['neutral_dark']};
      --o-light: {pal['neutral_light']};
      --o-font-headings: {typ['headings']};
      --o-font-body: {typ['body']};
    }}
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:var(--o-font-body);color:var(--o-dark);background:var(--o-light);line-height:1.55}}
    a{{color:var(--o-primary);text-decoration:none}}
    a:hover{{opacity:.85}}
    h1,h2,h3{{font-family:var(--o-font-headings);font-weight:600;letter-spacing:-.01em}}
    .container{{max-width:1180px;margin:0 auto;padding:24px}}
    footer{{margin-top:3rem;padding:24px;text-align:center;color:#78716c;font-size:.85rem;border-top:1px solid rgba(0,0,0,.08)}}
    img{{max-width:100%;display:block}}
    """

    if theme_id == "minimal":
        return base + """
        header{background:transparent;padding:32px 0 16px}
        header .container{display:flex;align-items:center;gap:16px}
        .brand-logo{height:36px;width:auto}
        .brand-name{font-family:var(--o-font-headings);font-size:1.25rem;color:var(--o-dark)}
        h1{font-size:2.6rem;line-height:1.1;margin:2rem 0 .8rem}
        h2{font-size:1.4rem;margin:2rem 0 1rem}
        .price{font-size:2rem;font-weight:600;color:var(--o-accent)}
        .meta{color:#78716c;font-size:.9rem;margin-bottom:1.2rem}
        .listings{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-top:1.5rem}
        .listings a{background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:4px;overflow:hidden;transition:border .2s}
        .listings a:hover{border-color:var(--o-primary)}
        .listings img{height:200px;width:100%;object-fit:cover}
        .listings .body{padding:14px}
        .listings .body h3{font-size:1.05rem;margin-bottom:.3rem}
        .listings .body p{color:#78716c;font-size:.85rem;margin-bottom:.4rem;font-family:var(--o-font-body)}
        .listings .body strong{color:var(--o-accent)}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:1.5rem 0}
        .grid>div{background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:4px;padding:12px}
        .grid label{display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#78716c;margin-bottom:.3rem;font-family:var(--o-font-body)}
        .grid strong{font-size:1.05rem;color:var(--o-dark);font-family:var(--o-font-body)}
        .photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:8px;margin:1.5rem 0}
        .photos img{height:240px;object-fit:cover;border-radius:4px}
        .description{background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:4px;padding:1.5rem;white-space:pre-wrap;margin:1.5rem 0}
        .features{display:flex;flex-wrap:wrap;gap:8px;margin:1rem 0}
        .features span{background:#fff;border:1px solid rgba(0,0,0,.12);border-radius:999px;padding:5px 13px;font-size:.85rem;color:var(--o-dark)}
        .card{background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:4px;padding:20px;margin:1.5rem 0}
        """

    if theme_id == "classic":
        return base + """
        header{background:var(--o-primary);color:#fff;padding:18px 0;border-bottom:3px solid var(--o-accent)}
        header .container{display:flex;align-items:center;gap:16px}
        .brand-logo{height:42px;width:auto;filter:brightness(0) invert(1)}
        .brand-name{font-family:var(--o-font-headings);font-size:1.35rem;color:#fff}
        h1{font-size:2.4rem;line-height:1.15;margin:1.8rem 0 .6rem;color:var(--o-primary)}
        h2{font-size:1.3rem;color:var(--o-primary);margin:1.8rem 0 1rem;border-bottom:2px solid var(--o-accent);padding-bottom:.4rem;display:inline-block}
        .price{font-size:2.2rem;font-weight:700;color:var(--o-accent);font-family:var(--o-font-headings)}
        .meta{color:#666;font-size:.92rem;margin-bottom:1.2rem;font-style:italic}
        .listings{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px;margin-top:1.5rem}
        .listings a{background:#fff;border-radius:6px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,.08);transition:transform .2s,box-shadow .2s}
        .listings a:hover{transform:translateY(-2px);box-shadow:0 6px 22px rgba(0,0,0,.12)}
        .listings img{height:210px;width:100%;object-fit:cover}
        .listings .body{padding:18px}
        .listings .body h3{font-size:1.15rem;color:var(--o-primary);margin-bottom:.4rem}
        .listings .body p{color:#666;font-size:.88rem;margin-bottom:.6rem;font-family:var(--o-font-body)}
        .listings .body strong{color:var(--o-accent);font-size:1.1rem}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:1.5rem 0}
        .grid>div{background:#fff;border-radius:4px;padding:14px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
        .grid label{display:block;font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;color:#999;margin-bottom:.3rem;font-family:var(--o-font-body)}
        .grid strong{font-size:1.05rem;color:var(--o-primary);font-family:var(--o-font-body)}
        .photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:10px;margin:1.5rem 0}
        .photos img{height:260px;object-fit:cover;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.1)}
        .description{background:#fff;border-radius:6px;padding:1.8rem;white-space:pre-wrap;margin:1.5rem 0;box-shadow:0 1px 4px rgba(0,0,0,.06)}
        .features{display:flex;flex-wrap:wrap;gap:8px;margin:1rem 0}
        .features span{background:var(--o-primary);color:#fff;border-radius:4px;padding:6px 14px;font-size:.85rem}
        .card{background:#fff;border-radius:6px;padding:22px;margin:1.5rem 0;box-shadow:0 2px 12px rgba(0,0,0,.08)}
        """

    if theme_id == "bold":
        return base + """
        body{background:var(--o-light)}
        header{background:#fff;border-bottom:4px solid var(--o-primary);padding:20px 0}
        header .container{display:flex;align-items:center;gap:16px}
        .brand-logo{height:40px;width:auto}
        .brand-name{font-family:var(--o-font-headings);font-size:1.4rem;font-weight:800;color:var(--o-dark);text-transform:uppercase;letter-spacing:-.02em}
        h1{font-size:3.2rem;font-weight:800;line-height:1;margin:1.8rem 0 .6rem;text-transform:uppercase;letter-spacing:-.03em}
        h2{font-size:1.6rem;font-weight:800;margin:2rem 0 1rem;text-transform:uppercase;letter-spacing:-.02em}
        .price{font-size:2.6rem;font-weight:800;color:var(--o-primary);letter-spacing:-.02em}
        .meta{color:#666;font-size:.9rem;margin-bottom:1.2rem;text-transform:uppercase;letter-spacing:.05em;font-weight:600}
        .listings{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:6px;margin-top:1.5rem}
        .listings a{background:#fff;overflow:hidden;border:none;transition:transform .25s}
        .listings a:hover{transform:scale(.98)}
        .listings img{height:340px;width:100%;object-fit:cover}
        .listings .body{padding:18px;background:var(--o-dark);color:#fff}
        .listings .body h3{font-size:1.2rem;color:#fff;margin-bottom:.4rem;text-transform:uppercase;letter-spacing:-.01em}
        .listings .body p{color:#aaa;font-size:.82rem;margin-bottom:.6rem;text-transform:uppercase;letter-spacing:.04em;font-family:var(--o-font-body)}
        .listings .body strong{color:var(--o-primary);font-size:1.2rem;font-weight:800}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1px;margin:1.5rem 0;background:rgba(0,0,0,.08)}
        .grid>div{background:#fff;padding:18px}
        .grid label{display:block;font-size:.65rem;text-transform:uppercase;letter-spacing:.12em;color:#999;margin-bottom:.4rem;font-family:var(--o-font-body);font-weight:700}
        .grid strong{font-size:1.15rem;color:var(--o-dark);font-family:var(--o-font-body);font-weight:700}
        .photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(400px,1fr));gap:4px;margin:1.5rem 0}
        .photos img{height:320px;object-fit:cover}
        .description{background:var(--o-dark);color:#fff;padding:2.2rem;white-space:pre-wrap;margin:1.5rem 0;font-size:1.05rem;line-height:1.7}
        .features{display:flex;flex-wrap:wrap;gap:4px;margin:1rem 0}
        .features span{background:var(--o-primary);color:#fff;padding:6px 14px;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700}
        .card{background:var(--o-dark);color:#fff;padding:24px;margin:1.5rem 0}
        .card strong{color:var(--o-primary);font-size:1.2rem}
        """

    # luxury
    return base + """
    body{background:var(--o-light)}
    header{background:transparent;padding:40px 0;border-bottom:1px solid rgba(0,0,0,.06)}
    header .container{display:flex;align-items:center;justify-content:center;gap:16px;text-align:center;flex-direction:column}
    .brand-logo{height:54px;width:auto}
    .brand-name{font-family:var(--o-font-headings);font-size:1.8rem;font-weight:400;color:var(--o-dark);letter-spacing:.04em}
    .brand-tagline{font-size:.7rem;letter-spacing:.5em;text-transform:uppercase;color:var(--o-accent);margin-top:6px;font-family:var(--o-font-body)}
    h1{font-size:2.8rem;line-height:1.15;margin:2.5rem 0 .8rem;font-weight:400;letter-spacing:.01em}
    h2{font-size:1.3rem;margin:2.5rem 0 1.2rem;font-weight:400;letter-spacing:.04em;color:var(--o-accent);text-transform:uppercase;font-size:.95rem}
    .price{font-size:2.4rem;font-weight:300;color:var(--o-accent);letter-spacing:.01em}
    .meta{color:#888;font-size:.78rem;text-transform:uppercase;letter-spacing:.2em;margin-bottom:1.4rem}
    .listings{display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));gap:32px;margin-top:2rem}
    .listings a{background:transparent;overflow:hidden;transition:opacity .25s}
    .listings a:hover{opacity:.85}
    .listings img{height:300px;width:100%;object-fit:cover}
    .listings .body{padding:18px 0;text-align:center}
    .listings .body h3{font-size:1.2rem;color:var(--o-dark);margin-bottom:.4rem;font-weight:400}
    .listings .body p{color:#888;font-size:.72rem;margin-bottom:.6rem;text-transform:uppercase;letter-spacing:.18em;font-family:var(--o-font-body)}
    .listings .body strong{color:var(--o-accent);font-size:1.05rem;font-weight:400}
    .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin:2rem 0}
    .grid>div{background:transparent;border-top:1px solid var(--o-accent);padding:14px 4px}
    .grid label{display:block;font-size:.62rem;text-transform:uppercase;letter-spacing:.2em;color:#999;margin-bottom:.4rem;font-family:var(--o-font-body)}
    .grid strong{font-size:1rem;color:var(--o-dark);font-family:var(--o-font-body);font-weight:400}
    .photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:12px;margin:2rem 0}
    .photos img{height:380px;object-fit:cover}
    .description{background:transparent;padding:2rem 0;white-space:pre-wrap;margin:1.5rem 0;font-size:1.05rem;line-height:1.85;color:#444;text-align:center;max-width:720px;margin-left:auto;margin-right:auto}
    .features{display:flex;flex-wrap:wrap;gap:8px;margin:1rem 0;justify-content:center}
    .features span{background:transparent;border:1px solid var(--o-accent);color:var(--o-accent);padding:6px 16px;font-size:.72rem;letter-spacing:.15em;text-transform:uppercase}
    .card{background:transparent;border-top:1px solid var(--o-accent);border-bottom:1px solid var(--o-accent);padding:32px 0;margin:2rem 0;text-align:center}
    .card strong{color:var(--o-dark);font-family:var(--o-font-headings);font-size:1.5rem;font-weight:400;display:block;margin-bottom:.4rem}
    """


def _render_header(cfg: Dict[str, Any], agency: Dict[str, Any]) -> str:
    name = escape(agency.get("display_name") or "")
    logo = cfg.get("logo_url")
    tagline = cfg.get("tagline")
    logo_html = f'<img src="{escape(logo)}" class="brand-logo" alt="{name}"/>' if logo else ""
    tagline_html = (
        f'<div class="brand-tagline">{escape(tagline)}</div>'
        if tagline and cfg["theme_id"] == "luxury" else ""
    )
    return f"""
    <header>
      <div class="container">
        {logo_html}
        <span class="brand-name">{name}</span>
        {tagline_html}
      </div>
    </header>"""


def _shell(cfg: Dict[str, Any], agency: Dict[str, Any],
           title: str, description: str, canonical: str, og_image: Optional[str],
           jsonld: str, body_html: str) -> str:
    og_img = f'<meta property="og:image" content="{escape(og_image)}"/>' if og_image else ""
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}"/>
<link rel="canonical" href="{escape(canonical)}"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="{escape(title)}"/>
<meta property="og:description" content="{escape(description)}"/>
<meta property="og:url" content="{escape(canonical)}"/>
{og_img}
<meta name="generator" content="OMNIA Real Estate Ecosystem"/>
<style>{_theme_css(cfg)}
{_share_css()}</style>
<script type="application/ld+json">{jsonld}</script>
</head>
<body data-theme="{cfg['theme_id']}">
{_render_header(cfg, agency)}
<main class="container">{body_html}</main>
<footer></footer>
</body>
</html>"""


# ============================================================
# SOCIAL SHARE (WhatsApp · Facebook · Email · Copy Link)
# ============================================================

def _public_base_url() -> str:
    """Backend-served public site origin (used to build absolute share URLs).
    Falls back to FRONTEND_URL — in this deployment the frontend host
    proxies /api/* to the backend, so /api/p/{slug} is publicly reachable there.
    """
    return (os.environ.get("FRONTEND_URL") or "").rstrip("/")


def _share_block(absolute_url: str, share_title: str, share_text: str) -> str:
    """Render 4 share buttons (WhatsApp / Facebook / Email / Copy link).
    Pure HTML + a tiny inline JS for copy-to-clipboard. No 3rd-party scripts."""
    u = quote_plus(absolute_url)
    t_text = quote_plus(share_text)
    t_title = quote_plus(share_title)
    wa = f"https://wa.me/?text={t_text}%20{u}"
    fb = f"https://www.facebook.com/sharer/sharer.php?u={u}"
    mailto = f"mailto:?subject={t_title}&body={t_text}%20{u}"
    return f"""
    <div class="share-block" data-share-url="{escape(absolute_url)}">
      <p class="share-label">Condividi questo immobile</p>
      <div class="share-row">
        <a class="share-btn share-wa" href="{wa}" target="_blank" rel="noopener" aria-label="Condividi su WhatsApp">
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M.057 24l1.687-6.163A11.867 11.867 0 0 1 .157 11.892C.16 5.335 5.495 0 12.05 0a11.817 11.817 0 0 1 8.413 3.488 11.824 11.824 0 0 1 3.48 8.414c-.003 6.557-5.338 11.892-11.893 11.892a11.9 11.9 0 0 1-5.688-1.448L.057 24zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-.999 3.648 3.742-.981zm11.387-5.464c-.074-.124-.272-.198-.57-.347-.297-.149-1.758-.868-2.031-.967-.272-.099-.47-.149-.669.149-.198.297-.768.967-.941 1.165-.173.198-.347.223-.644.074-.297-.149-1.255-.462-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.297-.347.446-.521.151-.172.2-.296.3-.495.099-.198.05-.372-.025-.521-.075-.148-.669-1.611-.916-2.206-.242-.579-.487-.501-.669-.51l-.57-.01c-.198 0-.52.074-.792.372s-1.04 1.016-1.04 2.479c0 1.462 1.065 2.875 1.213 3.074.149.198 2.095 3.2 5.076 4.487.709.306 1.263.489 1.694.626.712.226 1.36.194 1.872.118.571-.085 1.758-.719 2.006-1.413.248-.695.248-1.29.173-1.414z"/></svg>
          WhatsApp
        </a>
        <a class="share-btn share-fb" href="{fb}" target="_blank" rel="noopener" aria-label="Condividi su Facebook">
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M22.675 0H1.325C.593 0 0 .593 0 1.325v21.351C0 23.408.593 24 1.325 24H12.82v-9.294H9.692v-3.622h3.128V8.413c0-3.1 1.893-4.788 4.659-4.788 1.325 0 2.463.099 2.795.143v3.24l-1.918.001c-1.504 0-1.795.715-1.795 1.763v2.313h3.587l-.467 3.622h-3.12V24h6.116c.73 0 1.323-.592 1.323-1.324V1.325C24 .593 23.408 0 22.675 0z"/></svg>
          Facebook
        </a>
        <a class="share-btn share-em" href="{mailto}" aria-label="Condividi via Email">
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M0 3v18h24V3H0zm21.518 2L12 12.713 2.482 5h19.036zM2 19V6.255l10 8.105 10-8.105V19H2z"/></svg>
          Email
        </a>
        <button type="button" class="share-btn share-copy" data-action="copy" aria-label="Copia link">
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>
          <span class="share-copy-label">Copia link</span>
        </button>
      </div>
    </div>
    <script>(function(){{
      var b=document.currentScript.previousElementSibling.querySelector('[data-action="copy"]');
      if(!b) return;
      b.addEventListener('click',function(){{
        var url=b.closest('.share-block').getAttribute('data-share-url');
        var lbl=b.querySelector('.share-copy-label');
        var orig=lbl.textContent;
        var done=function(){{lbl.textContent='\u2713 Copiato'; setTimeout(function(){{lbl.textContent=orig;}},1800);}};
        if(navigator.clipboard){{navigator.clipboard.writeText(url).then(done,function(){{alert(url);}});}}
        else{{var ta=document.createElement('textarea');ta.value=url;document.body.appendChild(ta);ta.select();try{{document.execCommand('copy');done();}}catch(_){{}}document.body.removeChild(ta);}}
      }});
    }})();</script>"""


def _share_css() -> str:
    """Theme-agnostic styling for the share block (uses CSS variables already in scope)."""
    return """
    .share-block{margin:2rem 0;padding:1.25rem 0;border-top:1px solid rgba(0,0,0,.06)}
    .share-label{font-family:var(--o-font-body);font-size:.72rem;letter-spacing:.2em;text-transform:uppercase;color:#888;margin-bottom:.8rem}
    .share-row{display:flex;flex-wrap:wrap;gap:8px}
    .share-btn{display:inline-flex;align-items:center;gap:8px;padding:8px 14px;border-radius:999px;font-family:var(--o-font-body);font-size:.85rem;font-weight:500;cursor:pointer;border:1px solid rgba(0,0,0,.12);background:#fff;color:var(--o-dark);text-decoration:none;transition:transform .15s,box-shadow .15s,opacity .15s}
    .share-btn:hover{transform:translateY(-1px);box-shadow:0 2px 8px rgba(0,0,0,.08);text-decoration:none}
    .share-wa{background:#25D366;color:#fff;border-color:#25D366}
    .share-fb{background:#1877F2;color:#fff;border-color:#1877F2}
    .share-em{background:var(--o-primary);color:#fff;border-color:var(--o-primary)}
    .share-copy{background:#fff;color:var(--o-dark)}
    .share-wa:hover,.share-fb:hover,.share-em:hover{color:#fff;opacity:.92}
    """


# ============================================================
# AGENCY HOME (Track A) — layout riferimento nicastroimmobiliare.it
# Dual search (MLS network + portafoglio proprio) + In evidenza + Ultimi
# ============================================================

def _home_css() -> str:
    """Fixed structure CSS for the public agency home (chrome uses --o-primary)."""
    return """
    body.agency-home{background:#f4f4f4;color:#222;font-family:Arial,Helvetica,sans-serif}
    body.agency-home a{color:inherit}
    .ah-wrap{max-width:1100px;margin:0 auto;padding:0 12px 40px}
    .ah-top{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 0 10px;flex-wrap:wrap}
    .ah-brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:#222}
    .ah-brand img{height:52px;width:auto;object-fit:contain}
    .ah-brand-name{font-size:1.15rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase}
    .ah-nav{display:flex;flex-wrap:wrap;background:var(--o-primary);border-radius:2px;overflow:hidden}
    .ah-nav a{color:#fff;text-decoration:none;padding:10px 14px;font-size:.85rem;font-weight:600;border-right:1px solid rgba(255,255,255,.18)}
    .ah-nav a:last-child{border-right:0}
    .ah-nav a:hover{background:rgba(0,0,0,.12)}
    .ah-hero{margin:8px 0 16px;min-height:260px;border-radius:2px;position:relative;overflow:hidden;display:flex;align-items:flex-end;justify-content:center;background-color:var(--o-primary);background-size:cover;background-position:center center;background-repeat:no-repeat}
    .ah-hero::before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.15) 0%,rgba(0,0,0,.45) 100%);pointer-events:none}
    .ah-hero-inner{position:relative;z-index:1;padding:28px 20px;color:#fff;text-align:center;width:100%}
    .ah-hero-inner strong{display:block;font-size:1.35rem;letter-spacing:.06em;text-transform:uppercase;text-shadow:0 1px 3px rgba(0,0,0,.35)}
    .ah-hero-dots{display:flex;gap:8px;justify-content:center;margin-top:12px}
    .ah-hero-dots span{width:10px;height:10px;border-radius:50%;background:rgba(255,255,255,.55);box-shadow:0 0 0 1px rgba(0,0,0,.15)}
    .ah-hero-dots span.on{background:#fff}
    .ah-search-row{display:grid;grid-template-columns:260px 1fr;gap:14px;margin-bottom:28px}
    .ah-search-row.solo{grid-template-columns:1fr}
    .ah-box{background:var(--o-primary);color:#fff;border-radius:2px;padding:14px 14px 12px}
    .ah-box h2{font-family:inherit;font-size:1rem;font-weight:700;margin:0 0 12px;color:#fff;letter-spacing:.02em}
    .ah-field{margin-bottom:8px}
    .ah-field label{display:block;font-size:.72rem;margin-bottom:3px;opacity:.95}
    .ah-field select,.ah-field input{width:100%;padding:7px 8px;border:0;border-radius:2px;font-size:.85rem;color:#222}
    .ah-range{display:grid;grid-template-columns:1fr 1fr;gap:6px}
    .ah-btn{display:inline-block;width:100%;margin-top:8px;padding:10px 12px;border:0;border-radius:2px;background:#4a4a4a;color:#fff;font-weight:700;font-size:.9rem;cursor:pointer;text-align:center;text-decoration:none}
    .ah-btn.black{background:#111}
    .ah-btn:hover{opacity:.92}
    .ah-powered{margin-top:10px;text-align:center;font-size:.65rem;letter-spacing:.12em;text-transform:uppercase;opacity:.9}
    .ah-agency-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 14px}
    .ah-agency-actions{grid-column:1 / -1;display:flex;justify-content:flex-end}
    .ah-agency-actions .ah-btn{width:auto;min-width:220px}
    .ah-section{margin:8px 0 28px}
    .ah-section h2{font-family:inherit;font-size:1.25rem;font-weight:700;color:#333;margin:0 0 14px;padding-bottom:6px;border-bottom:2px solid var(--o-primary)}
    .ah-cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
    .ah-card{display:block;background:#fff;border:1px solid #ddd;text-decoration:none;color:#222;overflow:hidden}
    .ah-card:hover{box-shadow:0 4px 14px rgba(0,0,0,.1)}
    .ah-card-img{position:relative;aspect-ratio:4/3;background:#e8e8e8;background-size:cover;background-position:center}
    .ah-card-op{position:absolute;top:0;left:0;background:var(--o-primary);color:#fff;font-size:.72rem;font-weight:700;padding:5px 10px;text-transform:uppercase}
    .ah-card-price{position:absolute;right:8px;bottom:8px;background:rgba(255,255,255,.95);color:#111;font-weight:700;font-size:.95rem;padding:4px 8px;border-radius:2px}
    .ah-card-body{padding:10px 12px 0}
    .ah-card-city{font-size:.85rem;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-bottom:4px}
    .ah-card-title{font-size:.92rem;line-height:1.3;min-height:2.4em}
    .ah-card-zone{font-size:.78rem;color:#777;margin:4px 0 8px}
    .ah-card-meta{display:flex;gap:0;background:#eee;border-top:1px solid #ddd;margin-top:8px}
    .ah-card-meta span{flex:1;text-align:center;padding:8px 4px;font-size:.75rem;color:#444;border-right:1px solid #ddd}
    .ah-card-meta span:last-child{border-right:0}
    .ah-empty{grid-column:1/-1;background:#fff;border:1px dashed #ccc;padding:28px;text-align:center;color:#666}
    .ah-footer{margin-top:36px;background:#ececec;border-top:1px solid #ccc;padding:28px 0}
    .ah-footer-inner{max-width:1100px;margin:0 auto;padding:0 12px;display:grid;grid-template-columns:1.2fr 1fr;gap:24px}
    .ah-footer h3{font-size:.95rem;margin:0 0 10px;color:#333}
    .ah-footer ul{list-style:none;padding:0;margin:0}
    .ah-footer li{font-size:.82rem;color:#555;margin:4px 0}
    .ah-footer li:before{content:'› ';color:var(--o-primary);font-weight:700}
    .ah-footer-contact p{font-size:.85rem;color:#444;margin:4px 0;line-height:1.45}
    @media (max-width:900px){
      .ah-search-row,.ah-search-row.solo{grid-template-columns:1fr}
      .ah-agency-grid{grid-template-columns:1fr}
      .ah-cards{grid-template-columns:1fr 1fr}
      .ah-footer-inner{grid-template-columns:1fr}
    }
    @media (max-width:560px){
      .ah-cards{grid-template-columns:1fr}
      .ah-nav{width:100%}
    }
    """


def _split_featured_latest(props: List[Dict[str, Any]], featured_n: int = 3, latest_n: int = 6) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    exclusive = [p for p in props if p.get("is_exclusive")]
    featured = exclusive[:featured_n]
    if len(featured) < featured_n:
        seen = {p.get("id") for p in featured}
        for p in props:
            if p.get("id") in seen:
                continue
            featured.append(p)
            if len(featured) >= featured_n:
                break
    feat_ids = {p.get("id") for p in featured}
    latest = [p for p in props if p.get("id") not in feat_ids][:latest_n]
    if len(latest) < latest_n:
        # allow overlap if portfolio is small
        for p in props:
            if len(latest) >= latest_n:
                break
            if p not in latest:
                latest.append(p)
    return featured, latest


def _home_card(p: Dict[str, Any], slug: str) -> str:
    cover = _cover_url(p)
    price = _price_str(p)
    op = p.get("operation") or "sale"
    op_label = "Vendita" if op == "sale" else "Affitto"
    city = escape((p.get("city") or "").upper())
    title = escape(p.get("title") or "—")
    zone = escape(p.get("zone") or "")
    sqm = p.get("surface_sqm") or "—"
    rooms = p.get("rooms") or "—"
    beds = p.get("bedrooms") or "—"
    bg = f'style="background-image:url(\'{escape(cover)}\')"' if cover else ""
    return f"""
    <a class="ah-card" href="/api/p/{escape(slug)}/{escape(p.get('id') or '')}">
      <div class="ah-card-img" {bg}>
        <span class="ah-card-op">{op_label}</span>
        <span class="ah-card-price">{escape(price)}</span>
      </div>
      <div class="ah-card-body">
        <div class="ah-card-city">{city}</div>
        <div class="ah-card-title">{title}</div>
        <div class="ah-card-zone">{zone}</div>
      </div>
      <div class="ah-card-meta">
        <span>{escape(str(sqm))} Mq</span>
        <span>{escape(str(rooms))} Vani</span>
        <span>{escape(str(beds))} Cam.</span>
      </div>
    </a>"""


def _select(name: str, label: str, options: List[Tuple[str, str]], selected: str = "") -> str:
    opts = "".join(
        f'<option value="{escape(v)}"{" selected" if v == selected else ""}>{escape(lbl)}</option>'
        for v, lbl in options
    )
    return f'<div class="ah-field"><label>{escape(label)}</label><select name="{escape(name)}">{opts}</select></div>'


def _mls_search_box(network_count: int) -> str:
    claim = f"{network_count:,}".replace(",", ".") if network_count else "Network"
    return f"""
    <aside class="ah-box ah-mls" data-testid="agency-home-mls-box">
      <h2>+ {escape(claim)} immobili condivisi</h2>
      {_select("contratto", "Contratto", [("sale", "Vendita"), ("rent", "Affitto")], "sale")}
      {_select("categoria", "Categoria", [("", "Tutte"), ("residential", "Residenziale"), ("commercial", "Commerciale")], "residential")}
      {_select("provincia", "Provincia", [("", "Scegli"), ("CT", "CATANIA"), ("ME", "MESSINA"), ("PA", "PALERMO"), ("RG", "RAGUSA")])}
      {_select("comune", "Comune", [("", "Scegli")])}
      <div class="ah-field"><label>Prezzo</label>
        <div class="ah-range">
          <input type="number" name="price_min" placeholder="Min" min="0"/>
          <input type="number" name="price_max" placeholder="Max" min="0"/>
        </div>
      </div>
      <button type="button" class="ah-btn" onclick="location.href='/it/cloud?mls=1'">Avvia la ricerca</button>
      <div class="ah-powered">Powered by OMNIA</div>
    </aside>"""


def _agency_search_box() -> str:
    return f"""
    <section class="ah-box ah-agency" data-testid="agency-home-agency-search">
      <h2>Cerca il tuo immobile</h2>
      <div class="ah-agency-grid">
        {_select("contratto", "Contratto", [("", "Tutti"), ("sale", "Vendita"), ("rent", "Affitto")])}
        {_select("categoria", "Categoria", [("", "Tutte"), ("residential", "Residenziale"), ("commercial", "Commerciale")])}
        {_select("tipologia", "Tipologia", [("", "Tutte"), ("apartment", "Appartamento"), ("house", "Casa/Villa"), ("land", "Terreno")])}
        {_select("provincia", "Provincia", [("", "Tutte"), ("CT", "CATANIA"), ("ME", "MESSINA"), ("PA", "PALERMO")])}
        {_select("comune", "Comune", [("", "Tutti")])}
        <div class="ah-field"><label>Prezzo (da — a)</label><div class="ah-range">
          <input type="number" name="price_min" placeholder="da" min="0"/>
          <input type="number" name="price_max" placeholder="a" min="0"/>
        </div></div>
        <div class="ah-field"><label>Mq (da — a)</label><div class="ah-range">
          <input type="number" name="sqm_min" placeholder="da" min="0"/>
          <input type="number" name="sqm_max" placeholder="a" min="0"/>
        </div></div>
        <div class="ah-field"><label>Vani (da — a)</label><div class="ah-range">
          <input type="number" name="rooms_min" placeholder="da" min="0"/>
          <input type="number" name="rooms_max" placeholder="a" min="0"/>
        </div></div>
        <div class="ah-field"><label>Camere (da — a)</label><div class="ah-range">
          <input type="number" name="beds_min" placeholder="da" min="0"/>
          <input type="number" name="beds_max" placeholder="a" min="0"/>
        </div></div>
        <div class="ah-field"><label>Riferimento</label><input type="text" name="rif" placeholder="es. 25002"/></div>
        {_select("ordine", "Ordine", [("relevance", "Rilevanza"), ("price_asc", "Prezzo ↑"), ("price_desc", "Prezzo ↓"), ("date_desc", "Più recenti")])}
        <div class="ah-agency-actions">
          <button type="button" class="ah-btn black" onclick="location.href='#ultimi'">Avvia la ricerca</button>
        </div>
      </div>
    </section>"""


def _cards_section(title: str, section_id: str, cards_html: str) -> str:
    inner = cards_html or '<div class="ah-empty">Nessun immobile pubblicato al momento.</div>'
    return f"""
    <section class="ah-section" id="{escape(section_id)}" data-testid="agency-home-{escape(section_id)}">
      <h2>{escape(title)}</h2>
      <div class="ah-cards">{inner}</div>
    </section>"""


def render_index(agency: Dict[str, Any], props: List[Dict[str, Any]], slug: str) -> str:
    """Public agency home — struttura allineata al box MLS / vetrina di riferimento.

    - Box MLS (sx) solo se `agency.mls_enabled`
    - Box ricerca agenzia (dx) = portafoglio proprio
    - In evidenza (3) + Ultimi annunci (6) da props agenzia
    """
    cfg = _resolve_theme_config(agency)
    base = _public_base_url()
    canonical_rel = f"/api/p/{slug}/"
    canonical = f"{base}{canonical_rel}" if base else canonical_rel
    name = agency.get("display_name") or agency.get("name") or ""
    title = f"{name} — Immobili in vendita e affitto"
    desc = (
        f"Portafoglio immobili pubblicato da {name}. "
        f"{len(props)} annunci attivi su OMNIA."
    )
    logo = cfg.get("logo_url")
    logo_html = (
        f'<img src="{escape(logo)}" alt="{escape(name)}"/>'
        if logo else ""
    )
    hero_url = _resolve_hero_image(agency, cfg)
    hero_style = f'style="background-image:url(\'{escape(hero_url)}\')"'
    contact = agency.get("contact") or {}
    address = agency.get("address") or {}
    fiscal = agency.get("fiscal") or {}
    addr_line = ", ".join(
        x for x in [
            address.get("street"),
            " ".join(x for x in [address.get("postal_code") or "", (address.get("city") or "").upper()] if x).strip(),
            f"({address.get('province')})" if address.get("province") else "",
        ] if x
    )
    mls_on = bool(agency.get("mls_enabled"))
    # Live network size is filled by site.py when available; fallback claim for layout.
    network_count = int(agency.get("_mls_network_count") or 0)

    featured, latest = _split_featured_latest(props)
    featured_html = "".join(_home_card(p, slug) for p in featured)
    latest_html = "".join(_home_card(p, slug) for p in latest)

    search_row_cls = "ah-search-row" if mls_on else "ah-search-row solo"
    mls_html = _mls_search_box(network_count) if mls_on else ""

    nav = """
      <nav class="ah-nav" aria-label="Principale">
        <a href="#contatti">Contatti</a>
        <a href="#links">Links</a>
        <a href="/api/p/{slug}/">Home</a>
        <a href="#chi-siamo">Chi siamo</a>
        <a href="#ultimi">Vendita</a>
        <a href="#ultimi">Affitto</a>
      </nav>
    """.format(slug=escape(slug))

    jsonld_obj = {
        "@context": "https://schema.org",
        "@type": "RealEstateAgent",
        "name": name,
        "url": canonical,
    }
    if contact.get("phone"):
        jsonld_obj["telephone"] = contact.get("phone")
    if contact.get("email"):
        jsonld_obj["email"] = contact.get("email")

    legal_name = fiscal.get("legal_name") or name
    phone = contact.get("phone") or ""
    mobile = contact.get("mobile") or contact.get("phone_mobile") or ""
    email = contact.get("email") or ""
    vat = fiscal.get("vat_number") or ""
    cf = fiscal.get("fiscal_code") or ""

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}"/>
<link rel="canonical" href="{escape(canonical)}"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="{escape(title)}"/>
<meta property="og:description" content="{escape(desc)}"/>
<meta property="og:url" content="{escape(canonical)}"/>
<meta name="generator" content="OMNIA Real Estate Ecosystem"/>
<style>{_theme_css(cfg)}
{_home_css()}</style>
<script type="application/ld+json">{json.dumps(jsonld_obj, ensure_ascii=False)}</script>
</head>
<body class="agency-home" data-theme="{cfg['theme_id']}" data-testid="agency-home">
  <div class="ah-wrap">
    <div class="ah-top">
      <a class="ah-brand" href="/api/p/{escape(slug)}/">
        {logo_html}
        <span class="ah-brand-name">{escape(name)}</span>
      </a>
      {nav}
    </div>
    <div class="ah-hero" data-testid="agency-home-hero" {hero_style}>
      <div class="ah-hero-inner">
        <strong>{escape(name)}</strong>
        <div class="ah-hero-dots" aria-hidden="true"><span class="on"></span><span></span><span></span></div>
      </div>
    </div>
    <div class="{search_row_cls}" data-testid="agency-home-search-row">
      {mls_html}
      {_agency_search_box()}
    </div>
    {_cards_section("In evidenza", "evidenza", featured_html)}
    {_cards_section("Ultimi annunci inseriti", "ultimi", latest_html)}
  </div>
  <footer class="ah-footer" id="contatti">
    <div class="ah-footer-inner">
      <div id="links">
        <h3>Links</h3>
        <ul>
          <li>Il mutuo casa</li>
          <li>Contratti preliminari</li>
          <li>Documentazione immobile</li>
          <li>Valutazione gratuita</li>
        </ul>
      </div>
      <div class="ah-footer-contact" id="chi-siamo">
        <h3>{escape(legal_name)}</h3>
        <p>{escape(addr_line)}</p>
        <p>{('C.F. ' + escape(cf)) if cf else ''}{(' · P.IVA ' + escape(vat)) if vat else ''}</p>
        <p>{escape(email)}</p>
        <p>{escape(phone)}{(' · ' + escape(mobile)) if mobile and mobile != phone else ''}</p>
      </div>
    </div>
  </footer>
</body>
</html>"""


def render_property(agency: Dict[str, Any], p: Dict[str, Any], slug: str) -> str:
    cfg = _resolve_theme_config(agency)
    photos = p.get("photos") or []
    canonical = f"/api/p/{slug}/{p['id']}"
    base = _public_base_url()
    absolute_url = f"{base}{canonical}" if base else canonical
    cover_idx = next((i for i, ph in enumerate(photos) if ph.get("is_cover")), 0 if photos else None)
    og_image = f"/api/public/property/{p['id']}/photo/{cover_idx}" if cover_idx is not None else None
    og_image_abs = f"{base}{og_image}" if og_image and base else og_image
    title = f"{p.get('title')} — {agency.get('display_name')}"
    price = _price_str(p)
    desc = (
        f"{p.get('property_type','')} in {p.get('operation','')} a {p.get('city','')} · "
        f"{p.get('surface_sqm') or '—'} m² · {p.get('rooms') or '—'} locali · {price}"
    ).strip()

    photo_html = "".join(
        f'<img src="/api/public/property/{p["id"]}/photo/{i}" alt="{escape(p.get("title") or "")} foto {i+1}" loading="lazy"/>'
        for i in range(len(photos))
    )
    feats = p.get("features") or {}
    feats_keys = (
        [k for k, v in feats.items() if v] if isinstance(feats, dict)
        else (feats if isinstance(feats, list) else [])
    )
    feats_html = "".join(f"<span>{escape(k.replace('_', ' '))}</span>" for k in feats_keys)
    en = p.get("energy") or {}

    def cell(label: str, value: Any) -> str:
        if value in (None, ""):
            return ""
        return f'<div><label>{escape(label)}</label><strong>{escape(str(value))}</strong></div>'

    cells = "".join([
        cell("Tipologia", p.get("property_type")),
        cell("Operazione", p.get("operation")),
        cell("Città", p.get("city")),
        cell("Zona", p.get("zone")),
        cell("Superficie", f"{p.get('surface_sqm')} m²" if p.get("surface_sqm") else None),
        cell("Locali", p.get("rooms")),
        cell("Camere", p.get("bedrooms")),
        cell("Bagni", p.get("bathrooms")),
        cell("Piano", p.get("floor")),
        cell("Classe energetica", en.get("energy_class")),
        cell("Anno", p.get("year_built")),
        cell("Riferimento", p.get("reference_code")),
    ])

    description_block = (
        f'<h2>Descrizione</h2><div class="description">{escape(p.get("description") or "")}</div>'
        if p.get("description") else ""
    )
    features_block = (
        f'<h2>Caratteristiche</h2><div class="features">{feats_html}</div>' if feats_html else ""
    )

    share_title = f"{p.get('title') or ''} — {agency.get('display_name') or ''}".strip(" —")
    share_text = f"{share_title} · {price}"
    share_html = _share_block(absolute_url, share_title, share_text)

    body = f"""
    <h1>{escape(p.get('title') or '—')}</h1>
    <p class="meta">{escape(p.get('city') or '')}{(' · ' + escape(p.get('zone'))) if p.get('zone') else ''} · Rif. {escape(p.get('reference_code') or '—')}</p>
    <p class="price">{escape(price)}</p>
    {f'<div class="photos">{photo_html}</div>' if photos else ''}
    <h2>Caratteristiche principali</h2>
    <div class="grid">{cells}</div>
    {description_block}
    {features_block}
    {share_html}
    <div class="card">
      <strong>Contatta {escape(agency.get('display_name') or '')}</strong>
      <p class="meta" style="margin-top:.4rem">Per maggiori informazioni su questo immobile, contatta direttamente l'agenzia.</p>
    </div>
    """

    jsonld_obj = {
        "@context": "https://schema.org",
        "@type": "Product",
        "additionalType": "https://schema.org/RealEstateListing",
        "name": p.get("title"),
        "description": p.get("description") or desc,
        "category": p.get("property_type"),
        "image": [og_image_abs] if og_image_abs else [],
        "offers": {
            "@type": "Offer",
            "priceCurrency": "EUR",
            "price": p.get("price") or p.get("rent_monthly"),
            "availability": "https://schema.org/InStock",
            "seller": {"@type": "RealEstateAgent", "name": agency.get("display_name")},
        },
        "areaServed": p.get("city"),
        "url": absolute_url,
    }
    return _shell(cfg, agency, title, desc, absolute_url, og_image_abs,
                  json.dumps(jsonld_obj, ensure_ascii=False), body)


# ============================================================
# AUTH-PROTECTED API (Theme picker / apply / preview)
# ============================================================

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


async def _agency_for(user: dict) -> Dict[str, Any]:
    ag_ids = user.get("agency_ids") or []
    if not ag_ids:
        raise HTTPException(status_code=400, detail="no_agency")
    db = Database.get()
    a = await db.agencies.find_one({"id": ag_ids[0]})
    if not a:
        raise HTTPException(status_code=404, detail="agency_not_found")
    return a


@router.get("/themes")
async def list_themes(_: dict = Depends(get_current_user)):
    """Public list of available themes (for the picker UI)."""
    return {"themes": THEME_CATALOG, "default_theme_id": DEFAULT_THEME_ID}


@router.get("/theme")
async def get_current_theme(user: dict = Depends(get_current_user)):
    """Return the currently saved theme_config for the user's agency,
    plus the resolved effective config."""
    agency = await _agency_for(user)
    saved = (agency.get("website") or {}).get("theme_config")
    resolved = _resolve_theme_config(agency)
    extracted = normalize_extracted_profile((agency.get("website") or {}).get("extracted_profile"))
    return {
        "agency_id": agency["id"],
        "agency_slug": agency.get("slug"),
        "saved_theme_config": saved,
        "resolved": resolved,
        "extracted_profile": extracted,
        "public_url": f"/api/p/{agency.get('slug')}/",
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

    db = Database.get()
    props = await db.properties.find(
        {"agency_id": agency["id"], "status": "active"}, {"_id": 0},
    ).sort("updated_at", -1).to_list(length=24)

    html = render_index(transient, props, agency.get("slug") or "preview")
    return Response(content=html, media_type="text/html; charset=utf-8",
                    headers={"X-Robots-Tag": "noindex"})
