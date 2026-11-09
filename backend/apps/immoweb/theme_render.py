"""OMNIA themes — public site HTML renderers (MOVE-ONLY from themes.py)."""
from __future__ import annotations

import json
import logging
import os
from html import escape
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus

from apps.immoweb.theme_catalog import (
    _resolve_hero_image,
    _resolve_theme_config,
)

logger = logging.getLogger("omnia.themes")

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

    if theme_id == "luxury":
        return base + """
        body{background:var(--o-light)}
        header{background:transparent;padding:40px 0;border-bottom:1px solid rgba(0,0,0,.06)}
        header .container{display:flex;align-items:center;justify-content:center;gap:16px;text-align:center;flex-direction:column}
        .brand-logo{height:54px;width:auto}
        .brand-name{font-family:var(--o-font-headings);font-size:1.8rem;font-weight:400;color:var(--o-dark);letter-spacing:.04em}
        .brand-tagline{font-size:.7rem;letter-spacing:.5em;text-transform:uppercase;color:var(--o-accent);margin-top:6px;font-family:var(--o-font-body)}
        h1{font-size:2.8rem;line-height:1.15;margin:2.5rem 0 .8rem;font-weight:400;letter-spacing:.01em}
        h2{margin:2.5rem 0 1.2rem;font-weight:400;letter-spacing:.04em;color:var(--o-accent);text-transform:uppercase;font-size:.95rem}
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

    if theme_id == "atelier":
        return base + """
        body{background:var(--o-light)}
        header{background:transparent;padding:20px 0}
        header .container{display:flex;align-items:center;gap:14px}
        .brand-logo{height:36px;width:auto}
        .brand-name{font-family:var(--o-font-headings);font-size:1.35rem;font-weight:400;color:var(--o-dark)}
        h1{font-size:2.8rem;line-height:1.08;margin:2rem 0 .8rem;font-weight:400;letter-spacing:-.02em}
        h2{font-size:1.5rem;font-weight:500;margin:2rem 0 1rem;letter-spacing:-.02em}
        .price{font-size:1.8rem;font-weight:500;color:var(--o-accent)}
        .meta{color:#666;font-size:.9rem;margin-bottom:1.2rem}
        .listings{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-top:1.5rem}
        .listings a{background:#fff;border-radius:16px;overflow:hidden}
        .listings img{height:200px;width:100%;object-fit:cover}
        .listings .body{padding:14px 16px}
        .listings .body h3{font-size:1.05rem;margin-bottom:.4rem;font-weight:500}
        .listings .body strong{color:var(--o-dark)}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:1.5rem 0}
        .grid>div{background:#fff;border-radius:12px;padding:14px}
        .photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px;margin:1.5rem 0}
        .photos img{height:240px;object-fit:cover;border-radius:16px}
        .description{background:#fff;border-radius:16px;padding:1.5rem;white-space:pre-wrap;margin:1.5rem 0}
        .features span{background:var(--o-dark);color:#fff;border-radius:999px;padding:6px 14px;font-size:.8rem;margin:0 6px 6px 0;display:inline-block}
        .card{background:#fff;border-radius:16px;padding:22px;margin:1.5rem 0}
        """

    if theme_id == "cinematic":
        return base + """
        body{background:var(--o-light);color:#f5f5f5}
        header{background:transparent;padding:28px 0;border-bottom:1px solid rgba(255,255,255,.1)}
        header .container{display:flex;align-items:center;gap:16px}
        .brand-name{font-family:var(--o-font-headings);font-size:1.6rem;font-weight:400;color:#fff}
        h1{font-size:3rem;line-height:1;margin:2rem 0 .8rem;font-weight:400;color:#fff}
        h2{font-family:var(--o-font-headings);font-size:1.6rem;font-weight:400;margin:2rem 0 1rem;color:#fff}
        .price{font-size:2rem;font-weight:400;color:var(--o-accent)}
        .meta{color:rgba(255,255,255,.55);font-size:.85rem;margin-bottom:1.2rem}
        .listings{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin-top:1.5rem}
        .listings a{background:#0c1822;overflow:hidden;border-radius:4px}
        .listings img{height:220px;width:100%;object-fit:cover}
        .listings .body{padding:14px;color:#fff}
        .listings .body h3{font-family:var(--o-font-headings);font-size:1.2rem;font-weight:400;color:#fff}
        .listings .body strong{color:var(--o-accent)}
        a{color:var(--o-accent)}
        .grid>div{background:#0c1822;padding:14px;border-radius:4px}
        .grid label{color:rgba(255,255,255,.45)}
        .grid strong{color:#fff}
        .description{background:#0c1822;padding:1.8rem;border-radius:4px;color:rgba(255,255,255,.85);white-space:pre-wrap}
        .features span{border:1px solid var(--o-accent);color:var(--o-accent);padding:6px 14px;font-size:.75rem;letter-spacing:.1em;text-transform:uppercase;margin:0 6px 6px 0;display:inline-block}
        .card{background:#0c1822;padding:22px;border-radius:4px;color:#fff}
        footer{color:rgba(255,255,255,.45);border-top-color:rgba(255,255,255,.1)}
        """

    if theme_id == "editorial":
        return base + """
        body{background:var(--o-light)}
        header{background:transparent;padding:24px 0;border-bottom:1px solid var(--o-dark)}
        header .container{display:flex;align-items:center;justify-content:center}
        .brand-name{font-family:var(--o-font-headings);font-size:1.5rem;font-weight:400;text-align:center}
        h1{font-size:2.8rem;line-height:1.05;margin:2rem 0 .8rem;font-weight:400}
        h2{font-size:1.4rem;font-weight:400;margin:2rem 0 1rem}
        .price{font-size:1.6rem;font-weight:500}
        .meta{color:#78716c;font-size:.85rem;margin-bottom:1.2rem}
        .listings{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:0;border-top:1px solid #e7e5e4;margin-top:1.5rem}
        .listings a{background:transparent;border-right:1px solid #e7e5e4;padding:16px 14px}
        .listings a:last-child{border-right:0}
        .listings img{height:160px;width:100%;object-fit:cover;filter:grayscale(.12);margin-bottom:12px}
        .listings .body h3{font-family:var(--o-font-headings);font-size:1.15rem;font-weight:400}
        .grid>div{border-top:1px solid #e7e5e4;padding:12px 0}
        .description{border-top:1px solid #e7e5e4;border-bottom:1px solid #e7e5e4;padding:1.8rem 0;white-space:pre-wrap}
        .features span{border:1px solid #e7e5e4;padding:5px 12px;font-size:.8rem;margin:0 6px 6px 0;display:inline-block}
        .card{border-top:1px solid var(--o-dark);padding:24px 0;margin:1.5rem 0}
        """

    if theme_id == "mediterranean":
        return base + """
        body{background:var(--o-light);color:var(--o-primary)}
        header{background:transparent;padding:22px 0}
        header .container{display:flex;align-items:center;gap:14px}
        .brand-name{font-family:var(--o-font-headings);font-size:1.45rem;font-weight:400;color:var(--o-primary)}
        h1{font-size:2.6rem;line-height:1.1;margin:1.8rem 0 .8rem;font-weight:400;color:var(--o-primary)}
        h2{font-family:var(--o-font-headings);font-size:1.5rem;font-weight:400;margin:1.8rem 0 1rem;color:var(--o-primary)}
        .price{font-size:1.7rem;font-weight:500;color:var(--o-accent)}
        .meta{color:rgba(61,79,95,.65);font-size:.88rem;margin-bottom:1.2rem}
        .listings{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;margin-top:1.5rem}
        .listings a{background:#fff;border:1px solid #e8e0d4;border-radius:2px;overflow:hidden}
        .listings img{height:200px;width:100%;object-fit:cover}
        .listings .body{padding:14px 16px}
        .listings .body h3{font-family:var(--o-font-headings);font-size:1.15rem;font-weight:400;color:var(--o-primary)}
        .listings .body strong{color:var(--o-accent)}
        .grid>div{background:#fff;border:1px solid #e8e0d4;padding:14px}
        .description{background:#fff;border:1px solid #e8e0d4;padding:1.6rem;white-space:pre-wrap}
        .features span{background:transparent;border:1px solid var(--o-accent);color:var(--o-primary);padding:5px 12px;font-size:.8rem;margin:0 6px 6px 0;display:inline-block}
        .card{background:#fff;border:1px solid #e8e0d4;padding:20px;margin:1.5rem 0}
        """

    # fallback → minimal
    return _theme_css({**cfg, "theme_id": "minimal"})

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

def _home_css() -> str:
    """Agency home structure + theme slots (D-151: MLS adotta il tema, non lo stravolge)."""
    return """
    body.agency-home{background:#f4f4f4;color:#222;font-family:var(--o-font-body,Arial,Helvetica,sans-serif)}
    body.agency-home a{color:inherit}
    .ah-wrap{max-width:1100px;margin:0 auto;padding:0 12px 40px}
    .ah-top{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 0 10px;flex-wrap:wrap}
    .ah-brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:#222}
    .ah-brand img{height:52px;width:auto;object-fit:contain}
    .ah-brand-name{font-family:var(--o-font-headings,inherit);font-size:1.15rem;font-weight:700;letter-spacing:.04em;text-transform:uppercase}
    .ah-nav{display:flex;flex-wrap:wrap;background:var(--o-primary);border-radius:2px;overflow:hidden}
    .ah-nav a{color:#fff !important;text-decoration:none;padding:10px 14px;font-size:.85rem;font-weight:600;border-right:1px solid rgba(255,255,255,.18)}
    .ah-nav a:last-child{border-right:0}
    .ah-nav a:hover{background:rgba(0,0,0,.12)}
    .ah-hero{margin:8px 0 16px;min-height:260px;border-radius:2px;position:relative;overflow:hidden;display:flex;align-items:flex-end;justify-content:center;background-color:var(--o-primary);background-size:cover;background-position:center center;background-repeat:no-repeat}
    .ah-hero::before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.15) 0%,rgba(0,0,0,.45) 100%);pointer-events:none}
    .ah-hero-inner{position:relative;z-index:1;padding:28px 20px;color:#fff;text-align:center;width:100%}
    .ah-hero-inner strong{display:block;font-family:var(--o-font-headings,inherit);font-size:1.35rem;letter-spacing:.06em;text-transform:uppercase;text-shadow:0 1px 3px rgba(0,0,0,.35)}
    .ah-hero-dots{display:flex;gap:8px;justify-content:center;margin-top:12px}
    .ah-hero-dots span{width:10px;height:10px;border-radius:50%;background:rgba(255,255,255,.55);box-shadow:0 0 0 1px rgba(0,0,0,.15)}
    .ah-hero-dots span.on{background:#fff}
    .ah-search-row{display:grid;grid-template-columns:260px 1fr;gap:14px;margin-bottom:28px}
    .ah-search-row.solo{grid-template-columns:1fr}
    /* Default (bold/luxury fallback): solid primary — Minimal/Classic override below */
    .ah-box{background:var(--o-primary);color:#fff;border-radius:2px;padding:14px 14px 12px}
    .ah-box h2{font-family:var(--o-font-headings,inherit);font-size:1rem;font-weight:700;margin:0 0 12px;color:#fff;letter-spacing:.02em}
    .ah-field{margin-bottom:8px}
    .ah-field label{display:block;font-size:.72rem;margin-bottom:3px;opacity:.95}
    .ah-field select,.ah-field input{width:100%;padding:7px 8px;border:0;border-radius:2px;font-size:.85rem;color:#222;background:#fff}
    .ah-range{display:grid;grid-template-columns:1fr 1fr;gap:6px}
    .ah-btn{display:inline-block;width:100%;margin-top:8px;padding:10px 12px;border:0;border-radius:2px;background:#4a4a4a;color:#fff;font-weight:700;font-size:.9rem;cursor:pointer;text-align:center;text-decoration:none}
    .ah-btn.black{background:#111}
    .ah-btn:hover{opacity:.92}
    .ah-powered{margin-top:10px;text-align:center;font-size:.65rem;letter-spacing:.12em;text-transform:uppercase;opacity:.9}
    .ah-agency-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px 14px}
    .ah-agency-actions{grid-column:1 / -1;display:flex;justify-content:flex-end}
    .ah-agency-actions .ah-btn{width:auto;min-width:220px}
    .ah-section{margin:8px 0 28px}
    .ah-section h2{font-family:var(--o-font-headings,inherit);font-size:1.25rem;font-weight:700;color:#333;margin:0 0 14px;padding-bottom:6px;border-bottom:2px solid var(--o-primary)}
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

    /* —— Minimal (€99): MLS/search come superfici chiare, non blocco pieno primary —— */
    body.agency-home[data-theme="minimal"]{background:var(--o-light,#fafaf9);color:var(--o-dark,#1c1917)}
    body.agency-home[data-theme="minimal"] .ah-brand-name{text-transform:none;letter-spacing:-.01em;font-weight:500;font-size:1.25rem}
    body.agency-home[data-theme="minimal"] .ah-nav{background:transparent;border:1px solid rgba(0,0,0,.1);border-radius:2px}
    body.agency-home[data-theme="minimal"] .ah-nav a{color:var(--o-dark,#1c1917) !important;border-right-color:rgba(0,0,0,.08);font-weight:500}
    body.agency-home[data-theme="minimal"] .ah-nav a:hover{background:rgba(0,0,0,.04)}
    body.agency-home[data-theme="minimal"] .ah-hero{border-radius:2px;min-height:320px}
    body.agency-home[data-theme="minimal"] .ah-box{background:#fff;color:var(--o-dark,#1c1917);border:1px solid rgba(0,0,0,.1);border-radius:2px}
    body.agency-home[data-theme="minimal"] .ah-box h2{color:var(--o-dark,#1c1917);font-weight:500}
    body.agency-home[data-theme="minimal"] .ah-mls{border-top:3px solid var(--o-accent,#1f6b5c)}
    body.agency-home[data-theme="minimal"] .ah-agency{border-top:3px solid var(--o-dark,#1c1917)}
    body.agency-home[data-theme="minimal"] .ah-field label{color:rgba(28,25,23,.65);opacity:1}
    body.agency-home[data-theme="minimal"] .ah-field select,body.agency-home[data-theme="minimal"] .ah-field input{border:1px solid rgba(0,0,0,.12);background:#fafaf9}
    body.agency-home[data-theme="minimal"] .ah-btn{background:var(--o-dark,#1c1917);border-radius:0}
    body.agency-home[data-theme="minimal"] .ah-btn.black{background:var(--o-accent,#1f6b5c)}
    body.agency-home[data-theme="minimal"] .ah-powered{color:var(--o-accent,#1f6b5c);opacity:.85}
    body.agency-home[data-theme="minimal"] .ah-section h2{border-bottom-color:rgba(0,0,0,.12);font-weight:500}
    body.agency-home[data-theme="minimal"] .ah-card{border:1px solid rgba(0,0,0,.08);box-shadow:none}
    body.agency-home[data-theme="minimal"] .ah-card:hover{border-color:var(--o-primary)}
    body.agency-home[data-theme="minimal"] .ah-card-op{background:var(--o-dark,#1c1917)}
    body.agency-home[data-theme="minimal"] .ah-card-price{color:var(--o-accent,#1f6b5c)}

    /* —— Classic (€99): MLS/search bianchi + accenti navy/oro —— */
    body.agency-home[data-theme="classic"]{background:var(--o-light,#f5f3ee);color:var(--o-primary,#0B1E3F)}
    body.agency-home[data-theme="classic"] .ah-brand-name{font-weight:600;letter-spacing:.02em}
    body.agency-home[data-theme="classic"] .ah-nav{background:var(--o-primary,#0B1E3F);border-bottom:3px solid var(--o-accent,#C19A6B);border-radius:0}
    body.agency-home[data-theme="classic"] .ah-hero{border-radius:0;min-height:300px}
    body.agency-home[data-theme="classic"] .ah-box{background:#fff;color:var(--o-primary,#0B1E3F);border:1px solid rgba(11,30,63,.12);border-radius:6px;box-shadow:0 2px 10px rgba(11,30,63,.06)}
    body.agency-home[data-theme="classic"] .ah-box h2{color:var(--o-primary,#0B1E3F);border-bottom:2px solid var(--o-accent,#C19A6B);padding-bottom:6px;display:inline-block}
    body.agency-home[data-theme="classic"] .ah-mls .ah-powered{color:var(--o-accent,#C19A6B)}
    body.agency-home[data-theme="classic"] .ah-field label{color:rgba(11,30,63,.65);opacity:1}
    body.agency-home[data-theme="classic"] .ah-field select,body.agency-home[data-theme="classic"] .ah-field input{border:1px solid rgba(11,30,63,.15);background:#faf9f6}
    body.agency-home[data-theme="classic"] .ah-btn{background:var(--o-accent,#C19A6B);color:var(--o-primary,#0B1E3F);border-radius:4px}
    body.agency-home[data-theme="classic"] .ah-btn.black{background:var(--o-primary,#0B1E3F);color:#fff}
    body.agency-home[data-theme="classic"] .ah-section h2{color:var(--o-primary,#0B1E3F);border-bottom-color:var(--o-accent,#C19A6B)}
    body.agency-home[data-theme="classic"] .ah-card{border:0;border-radius:6px;box-shadow:0 2px 12px rgba(0,0,0,.08)}
    body.agency-home[data-theme="classic"] .ah-card-op{background:var(--o-primary,#0B1E3F)}
    body.agency-home[data-theme="classic"] .ah-card-price{color:var(--o-accent,#C19A6B)}
    body.agency-home[data-theme="classic"] .ah-card-title{font-family:var(--o-font-headings,Georgia,serif);color:var(--o-primary,#0B1E3F)}

    /* —— Bold (€199): search scuro + accent arancio —— */
    body.agency-home[data-theme="bold"]{background:#fff;color:#111}
    body.agency-home[data-theme="bold"] .ah-brand-name{text-transform:uppercase;font-weight:800;letter-spacing:-.02em}
    body.agency-home[data-theme="bold"] .ah-nav{background:#111;border-bottom:4px solid var(--o-primary,#FF5A1F);border-radius:0}
    body.agency-home[data-theme="bold"] .ah-box{background:#111;color:#fff;border-radius:0}
    body.agency-home[data-theme="bold"] .ah-mls{border-left:4px solid var(--o-primary,#FF5A1F)}
    body.agency-home[data-theme="bold"] .ah-box h2{color:#fff;text-transform:uppercase;letter-spacing:-.01em;font-weight:800}
    body.agency-home[data-theme="bold"] .ah-field label{text-transform:uppercase;letter-spacing:.08em;font-size:.65rem;font-weight:700}
    body.agency-home[data-theme="bold"] .ah-btn{background:var(--o-primary,#FF5A1F);text-transform:uppercase;font-weight:800;border-radius:0}
    body.agency-home[data-theme="bold"] .ah-btn.black{background:#fff;color:#111}
    body.agency-home[data-theme="bold"] .ah-powered{color:var(--o-primary,#FF5A1F)}
    body.agency-home[data-theme="bold"] .ah-section h2{text-transform:uppercase;font-weight:800;border-bottom-color:var(--o-primary,#FF5A1F)}
    body.agency-home[data-theme="bold"] .ah-card{border:0}
    body.agency-home[data-theme="bold"] .ah-card-body{background:#111;color:#fff;padding:12px}
    body.agency-home[data-theme="bold"] .ah-card-city,.ah-card-zone{color:#aaa}
    body.agency-home[data-theme="bold"] .ah-card-title{color:#fff;text-transform:uppercase}
    body.agency-home[data-theme="bold"] .ah-card-meta{background:#1a1a1a;border-top-color:#333}
    body.agency-home[data-theme="bold"] .ah-card-meta span{color:#ccc;border-right-color:#333}
    body.agency-home[data-theme="bold"] .ah-card-price{color:var(--o-primary,#FF5A1F)}

    /* —— Luxury (€199): scuro/oro, box glass-dark —— */
    body.agency-home[data-theme="luxury"]{background:#0a0a0a;color:#fafafa}
    body.agency-home[data-theme="luxury"] .ah-brand{color:#fafafa;flex-direction:column;text-align:center;width:100%;justify-content:center}
    body.agency-home[data-theme="luxury"] .ah-top{flex-direction:column;align-items:center}
    body.agency-home[data-theme="luxury"] .ah-brand-name{font-weight:400;letter-spacing:.08em;text-transform:none;font-size:1.6rem}
    body.agency-home[data-theme="luxury"] .ah-nav{background:transparent;border:1px solid rgba(184,157,94,.35);border-radius:0}
    body.agency-home[data-theme="luxury"] .ah-nav a{color:rgba(250,250,250,.7) !important;font-size:.72rem;letter-spacing:.18em;text-transform:uppercase;font-weight:400;border-right-color:rgba(184,157,94,.2)}
    body.agency-home[data-theme="luxury"] .ah-box{background:rgba(255,255,255,.04);color:#fafafa;border:1px solid rgba(184,157,94,.35);border-radius:0}
    body.agency-home[data-theme="luxury"] .ah-box h2{color:var(--o-accent,#B89D5E);font-weight:400;letter-spacing:.2em;text-transform:uppercase;font-size:.78rem}
    body.agency-home[data-theme="luxury"] .ah-field label{letter-spacing:.12em;text-transform:uppercase;font-size:.65rem;color:rgba(250,250,250,.55)}
    body.agency-home[data-theme="luxury"] .ah-btn{background:transparent;border:1px solid var(--o-accent,#B89D5E);color:var(--o-accent,#B89D5E);letter-spacing:.14em;text-transform:uppercase;font-weight:400;font-size:.75rem}
    body.agency-home[data-theme="luxury"] .ah-btn.black{border-color:#fff;color:#fff}
    body.agency-home[data-theme="luxury"] .ah-powered{color:var(--o-accent,#B89D5E);letter-spacing:.2em}
    body.agency-home[data-theme="luxury"] .ah-section h2{color:var(--o-accent,#B89D5E);border-bottom-color:rgba(184,157,94,.35);text-align:center;font-weight:400;letter-spacing:.25em;text-transform:uppercase;font-size:.85rem}
    body.agency-home[data-theme="luxury"] .ah-card{background:transparent;border:0;text-align:center}
    body.agency-home[data-theme="luxury"] .ah-card-op{background:transparent;border:1px solid var(--o-accent,#B89D5E);color:var(--o-accent,#B89D5E);font-weight:400;letter-spacing:.1em}
    body.agency-home[data-theme="luxury"] .ah-card-title{font-weight:400;color:#fafafa}
    body.agency-home[data-theme="luxury"] .ah-card-city,.ah-card-zone{color:rgba(250,250,250,.45);letter-spacing:.15em}
    body.agency-home[data-theme="luxury"] .ah-card-meta{background:transparent;border-top:1px solid rgba(184,157,94,.25)}
    body.agency-home[data-theme="luxury"] .ah-card-meta span{color:rgba(250,250,250,.55);border-right-color:rgba(184,157,94,.2)}
    body.agency-home[data-theme="luxury"] .ah-card-price{background:transparent;color:var(--o-accent,#B89D5E);font-weight:300}
    body.agency-home[data-theme="luxury"] .ah-footer{background:#050505;border-top-color:rgba(184,157,94,.2)}
    body.agency-home[data-theme="luxury"] .ah-footer h3,body.agency-home[data-theme="luxury"] .ah-footer li,body.agency-home[data-theme="luxury"] .ah-footer-contact p{color:rgba(250,250,250,.65)}

    /* —— Atelier (€199) —— */
    body.agency-home[data-theme="atelier"]{background:var(--o-light,#EFEFEF);color:#111}
    body.agency-home[data-theme="atelier"] .ah-brand-name{font-weight:400;text-transform:none;letter-spacing:-.01em}
    body.agency-home[data-theme="atelier"] .ah-nav{background:#fff;border-radius:999px;padding:4px;box-shadow:0 1px 0 rgba(0,0,0,.04)}
    body.agency-home[data-theme="atelier"] .ah-nav a{color:#111 !important;border-right:0;border-radius:999px;font-weight:500}
    body.agency-home[data-theme="atelier"] .ah-nav a:hover{background:#111;color:#fff !important}
    body.agency-home[data-theme="atelier"] .ah-hero{border-radius:20px;min-height:340px}
    body.agency-home[data-theme="atelier"] .ah-box{background:#fff;color:#111;border-radius:16px;border:0;box-shadow:0 2px 12px rgba(0,0,0,.05)}
    body.agency-home[data-theme="atelier"] .ah-box h2{color:#111;font-weight:500}
    body.agency-home[data-theme="atelier"] .ah-mls{outline:2px solid var(--o-accent,#F26522);outline-offset:-2px}
    body.agency-home[data-theme="atelier"] .ah-field select,body.agency-home[data-theme="atelier"] .ah-field input{border:1px solid #e5e5e5;border-radius:10px;background:#fafafa}
    body.agency-home[data-theme="atelier"] .ah-btn{background:var(--o-accent,#F26522);border-radius:999px;font-weight:500}
    body.agency-home[data-theme="atelier"] .ah-btn.black{background:#111}
    body.agency-home[data-theme="atelier"] .ah-powered{color:var(--o-accent,#F26522)}
    body.agency-home[data-theme="atelier"] .ah-section h2{border-bottom:0;font-weight:500;letter-spacing:-.02em}
    body.agency-home[data-theme="atelier"] .ah-card{border:0;border-radius:16px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.05)}

    /* —— Cinematic (€199) —— */
    body.agency-home[data-theme="cinematic"]{background:#061018;color:#fff}
    body.agency-home[data-theme="cinematic"] .ah-brand-name{font-weight:400;text-transform:none;letter-spacing:0;color:#fff}
    body.agency-home[data-theme="cinematic"] .ah-nav{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);border-radius:999px}
    body.agency-home[data-theme="cinematic"] .ah-nav a{color:rgba(255,255,255,.75) !important;border-right:0;font-weight:400}
    body.agency-home[data-theme="cinematic"] .ah-hero{border-radius:4px;min-height:380px}
    body.agency-home[data-theme="cinematic"] .ah-box{background:#0c1822;color:#fff;border:1px solid rgba(255,255,255,.1);border-radius:4px}
    body.agency-home[data-theme="cinematic"] .ah-box h2{color:#fff;font-weight:400}
    body.agency-home[data-theme="cinematic"] .ah-field label{color:rgba(255,255,255,.5)}
    body.agency-home[data-theme="cinematic"] .ah-btn{background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.25);border-radius:999px;font-weight:500}
    body.agency-home[data-theme="cinematic"] .ah-btn.black{background:var(--o-accent,#c4a574);color:#061018;border:0}
    body.agency-home[data-theme="cinematic"] .ah-powered{color:var(--o-accent,#c4a574)}
    body.agency-home[data-theme="cinematic"] .ah-section h2{color:#fff;border-bottom-color:rgba(255,255,255,.15);font-weight:400}
    body.agency-home[data-theme="cinematic"] .ah-card{background:#0c1822;border:0;color:#fff}
    body.agency-home[data-theme="cinematic"] .ah-card-title{color:#fff;font-weight:400}
    body.agency-home[data-theme="cinematic"] .ah-card-city,.ah-card-zone{color:rgba(255,255,255,.45)}
    body.agency-home[data-theme="cinematic"] .ah-card-meta{background:#061018;border-top-color:rgba(255,255,255,.1)}
    body.agency-home[data-theme="cinematic"] .ah-card-meta span{color:rgba(255,255,255,.55);border-right-color:rgba(255,255,255,.08)}
    body.agency-home[data-theme="cinematic"] .ah-card-price{color:var(--o-accent,#c4a574)}
    body.agency-home[data-theme="cinematic"] .ah-footer{background:#040a10;border-top-color:rgba(255,255,255,.08)}
    body.agency-home[data-theme="cinematic"] .ah-footer h3,body.agency-home[data-theme="cinematic"] .ah-footer li,body.agency-home[data-theme="cinematic"] .ah-footer-contact p{color:rgba(255,255,255,.55)}

    /* —— Editorial (€199) —— */
    body.agency-home[data-theme="editorial"]{background:#fafaf9;color:#1c1917}
    body.agency-home[data-theme="editorial"] .ah-wrap{border-left:1px solid #e7e5e4;border-right:1px solid #e7e5e4;max-width:1080px}
    body.agency-home[data-theme="editorial"] .ah-brand-name{font-weight:400;text-transform:none;letter-spacing:0;text-align:center}
    body.agency-home[data-theme="editorial"] .ah-top{border-bottom:1px solid #1c1917;justify-content:center}
    body.agency-home[data-theme="editorial"] .ah-nav{background:transparent;border:0}
    body.agency-home[data-theme="editorial"] .ah-nav a{color:#1c1917 !important;border-right:0;font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:500;opacity:.55}
    body.agency-home[data-theme="editorial"] .ah-hero{border-radius:0;min-height:340px}
    body.agency-home[data-theme="editorial"] .ah-box{background:transparent;color:#1c1917;border:1px solid #e7e5e4;border-radius:0}
    body.agency-home[data-theme="editorial"] .ah-box h2{color:#1c1917;font-weight:400}
    body.agency-home[data-theme="editorial"] .ah-mls{border-top:1px solid #1c1917}
    body.agency-home[data-theme="editorial"] .ah-field select,body.agency-home[data-theme="editorial"] .ah-field input{border:1px solid #e7e5e4;background:#fff;border-radius:0}
    body.agency-home[data-theme="editorial"] .ah-btn{background:transparent;border-bottom:1px solid #1c1917;color:#1c1917;border-radius:0;font-size:12px;letter-spacing:.14em;text-transform:uppercase;font-weight:500;width:auto}
    body.agency-home[data-theme="editorial"] .ah-btn.black{border:1px solid #1c1917}
    body.agency-home[data-theme="editorial"] .ah-section h2{border-bottom-color:#e7e5e4;font-weight:400}
    body.agency-home[data-theme="editorial"] .ah-card{border:0;border-right:1px solid #e7e5e4;border-radius:0;box-shadow:none}
    body.agency-home[data-theme="editorial"] .ah-cards{gap:0;border-top:1px solid #e7e5e4}
    body.agency-home[data-theme="editorial"] .ah-card:last-child{border-right:0}
    body.agency-home[data-theme="editorial"] .ah-card-op{background:transparent;color:#1c1917;border:1px solid #e7e5e4;font-weight:500}

    /* —— Mediterranean (€199) —— */
    body.agency-home[data-theme="mediterranean"]{background:var(--o-light,#f7f3eb);color:var(--o-primary,#3d4f5f)}
    body.agency-home[data-theme="mediterranean"] .ah-brand-name{font-weight:400;text-transform:none;letter-spacing:0;color:var(--o-primary,#3d4f5f)}
    body.agency-home[data-theme="mediterranean"] .ah-nav{background:transparent;border:0}
    body.agency-home[data-theme="mediterranean"] .ah-nav a{color:var(--o-primary,#3d4f5f) !important;border-right:0;opacity:.7;font-weight:500}
    body.agency-home[data-theme="mediterranean"] .ah-hero{border-radius:4px;min-height:360px;border:1px solid #e8e0d4}
    body.agency-home[data-theme="mediterranean"] .ah-box{background:#fff;color:var(--o-primary,#3d4f5f);border:1px solid #e8e0d4;border-radius:2px}
    body.agency-home[data-theme="mediterranean"] .ah-box h2{color:var(--o-primary,#3d4f5f);font-weight:400}
    body.agency-home[data-theme="mediterranean"] .ah-mls{border-top:3px solid var(--o-accent,#c4a574)}
    body.agency-home[data-theme="mediterranean"] .ah-field select,body.agency-home[data-theme="mediterranean"] .ah-field input{border:1px solid #e8e0d4;background:#faf8f4}
    body.agency-home[data-theme="mediterranean"] .ah-btn{background:var(--o-accent,#c4a574);color:#2a3340;border-radius:2px;font-weight:500}
    body.agency-home[data-theme="mediterranean"] .ah-btn.black{background:var(--o-primary,#3d4f5f);color:#fff}
    body.agency-home[data-theme="mediterranean"] .ah-powered{color:var(--o-accent,#c4a574)}
    body.agency-home[data-theme="mediterranean"] .ah-section h2{border-bottom:0;font-weight:400;color:var(--o-primary,#3d4f5f)}
    body.agency-home[data-theme="mediterranean"] .ah-card{border:1px solid #e8e0d4;border-radius:2px;box-shadow:none}
    body.agency-home[data-theme="mediterranean"] .ah-card-op{background:var(--o-primary,#3d4f5f)}
    body.agency-home[data-theme="mediterranean"] .ah-card-price{color:var(--o-accent,#c4a574)}
    body.agency-home[data-theme="mediterranean"] .ah-card-title{font-family:var(--o-font-headings,Georgia,serif);color:var(--o-primary,#3d4f5f);font-weight:400}

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

