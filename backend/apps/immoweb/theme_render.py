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

def _brand_mark(logo: Optional[str], name: str, *, img_class: str = "brand-logo") -> str:
    """Logo OR testo agenzia — mai entrambi (evita doppia scritta)."""
    safe = escape(name or "")
    if logo:
        return f'<img src="{escape(logo)}" class="{escape(img_class)}" alt="{safe}"/>'
    return f'<span class="brand-name ah-brand-name">{safe}</span>'


def _render_header(cfg: Dict[str, Any], agency: Dict[str, Any]) -> str:
    name = agency.get("display_name") or ""
    logo = cfg.get("logo_url")
    tagline = cfg.get("tagline")
    tagline_html = (
        f'<div class="brand-tagline">{escape(tagline)}</div>'
        if tagline and cfg["theme_id"] == "luxury" else ""
    )
    return f"""
    <header>
      <div class="container">
        {_brand_mark(logo, name)}
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
    """Fixed structure CSS for the public agency home (chrome uses --o-primary)."""
    return """
    body.agency-home{background:#f4f4f4;color:#222;font-family:Arial,Helvetica,sans-serif}
    body.agency-home a{color:inherit}
    .ah-wrap{max-width:1100px;margin:0 auto;padding:0 12px 40px}
    .ah-top{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:14px 0 10px;flex-wrap:wrap}
    .ah-brand{display:flex;align-items:center;gap:12px;text-decoration:none;color:#222}
    .ah-brand img{height:56px;width:auto;object-fit:contain;display:block}
    .ah-brand-name{font-size:1.05rem;font-weight:700;letter-spacing:.03em;text-transform:uppercase;font-family:Georgia,'Times New Roman',serif}
    .ah-nav{display:flex;flex-wrap:wrap;background:var(--o-primary);border-radius:0;overflow:hidden;box-shadow:0 1px 0 rgba(0,0,0,.08)}
    .ah-nav a{color:#fff;text-decoration:none;padding:12px 18px;font-size:.92rem;font-weight:600;letter-spacing:.02em;border-right:1px solid rgba(255,255,255,.28);line-height:1.2}
    .ah-nav a:last-child{border-right:0}
    .ah-nav a:hover,.ah-nav a.on{background:rgba(255,255,255,.16)}
    .ah-hero{margin:8px 0 16px;min-height:280px;border-radius:0;position:relative;overflow:hidden;display:flex;align-items:flex-end;justify-content:center;background-color:var(--o-primary);background-size:cover;background-position:center center;background-repeat:no-repeat}
    .ah-hero::before{content:"";position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.08) 0%,rgba(0,0,0,.28) 100%);pointer-events:none}
    .ah-hero-inner{position:relative;z-index:1;padding:18px 20px;color:#fff;text-align:center;width:100%}
    .ah-hero-dots{display:flex;gap:8px;justify-content:center;margin-top:0}
    .ah-hero-dots span{width:10px;height:10px;border-radius:50%;background:rgba(255,255,255,.55);box-shadow:0 0 0 1px rgba(0,0,0,.15)}
    .ah-hero-dots span.on{background:#fff}
    .ah-search-row{display:grid;grid-template-columns:250px 1fr;gap:16px;margin-bottom:28px;align-items:start}
    .ah-search-row.solo{grid-template-columns:1fr}
    .ah-box{border-radius:0;padding:0;overflow:hidden}
    .ah-box h2{font-family:inherit;font-size:.98rem;font-weight:700;margin:0;letter-spacing:.01em}
    .ah-box-body{padding:12px 12px 14px}
    .ah-field{margin-bottom:8px}
    .ah-field label{display:block;font-size:.72rem;margin-bottom:3px;opacity:.95}
    .ah-field select,.ah-field input,.ah-field textarea{width:100%;padding:8px 9px;border:1px solid #d0d0d0;border-radius:2px;font-size:.85rem;color:#222;background:#fff;box-sizing:border-box}
    .ah-field textarea{min-height:88px;resize:vertical;font-family:inherit}
    .ah-range{display:grid;grid-template-columns:1fr 1fr;gap:6px}
    .ah-btn{display:inline-block;width:100%;margin-top:8px;padding:10px 12px;border:0;border-radius:2px;background:#5a5a5a;color:#fff;font-weight:700;font-size:.9rem;cursor:pointer;text-align:center;text-decoration:none}
    .ah-btn.black{background:#111}
    .ah-btn:hover{opacity:.92}
    .ah-powered{margin-top:10px;text-align:center;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase}
    .ah-powered strong{font-weight:800}
    /* MLS box: bianco + header verde (stile riferimento Agestanet) */
    .ah-mls{background:#fff;color:#222;border:1px solid var(--o-primary);box-shadow:0 1px 3px rgba(0,0,0,.06)}
    .ah-mls .ah-mls-head{background:var(--o-primary);color:#fff;padding:10px 12px}
    .ah-mls .ah-mls-head h2{color:#fff;font-size:.92rem}
    .ah-mls .ah-box-body{padding:12px}
    .ah-mls .ah-field label{color:#444;opacity:1}
    .ah-mls .ah-powered{color:#666}
    .ah-mls .ah-powered strong{color:#c62828}
    /* Box agenzia: verde pieno */
    .ah-agency{background:var(--o-primary);color:#fff}
    .ah-agency .ah-box-body{padding:14px 14px 16px}
    .ah-agency h2{color:#fff;margin:0 0 12px;padding-bottom:6px;border-bottom:1px solid rgba(255,255,255,.35)}
    .ah-agency .ah-field label{color:#fff}
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
    .ah-card-mls{position:absolute;left:8px;bottom:8px;background:#0f172a;color:#fff;font-size:.68rem;font-weight:700;padding:3px 7px;letter-spacing:.04em;text-transform:uppercase}
    .ah-card-mls.ah-card,.ah-card.ah-card-mls{box-shadow:inset 0 0 0 2px #0f172a}
    .ah-mls-network-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:10px}
    .ah-mls-network-head h2{margin:0}
    .ah-mls-badge{display:inline-block;background:#0f172a;color:#fff;font-size:.72rem;font-weight:700;padding:4px 10px;letter-spacing:.06em;text-transform:uppercase}
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
    .ah-list-layout{display:grid;grid-template-columns:1fr 280px;gap:18px;align-items:start}
    .ah-list-main{min-width:0}
    .ah-list-side .ah-agency,.ah-list-side .ah-mls{position:sticky;top:12px}
    .ah-prop-layout{display:grid;grid-template-columns:1fr 280px;gap:20px;align-items:start;margin-top:12px}
    .ah-prop-main{min-width:0}
    .ah-prop-main .photos{display:grid;grid-template-columns:1fr;gap:10px;margin:1rem 0}
    .ah-prop-main .photos img{width:100%;max-height:420px;object-fit:cover;display:block}
    .ah-prop-main h1{font-size:1.45rem;margin:0 0 6px;color:#222}
    .ah-prop-main .meta{color:#666;margin:0 0 4px}
    .ah-prop-main .price{font-size:1.35rem;font-weight:700;margin:8px 0 14px}
    .ah-prop-main .grid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px;margin:12px 0}
    .ah-prop-main .grid label{display:block;font-size:.68rem;color:#888;text-transform:uppercase;letter-spacing:.06em}
    .ah-consent{font-size:.75rem;color:#fff;margin:10px 0;line-height:1.45}
    .ah-consent label{margin-right:10px}
    .ah-contact-agency{margin-top:14px;font-size:.8rem;opacity:.9}
    @media (max-width:900px){
      .ah-search-row,.ah-search-row.solo,.ah-list-layout,.ah-prop-layout{grid-template-columns:1fr}
      .ah-agency-grid{grid-template-columns:1fr}
      .ah-cards{grid-template-columns:1fr 1fr}
      .ah-footer-inner{grid-template-columns:1fr}
      .ah-list-side .ah-agency,.ah-list-side .ah-mls{position:static}
    }
    @media (max-width:560px){
      .ah-cards{grid-template-columns:1fr}
      .ah-nav{width:100%}
      .ah-prop-main .grid{grid-template-columns:1fr}
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

def _home_card(
    p: Dict[str, Any],
    slug: str,
    *,
    mls: bool = False,
    href: Optional[str] = None,
) -> str:
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
    link = href or f"/api/p/{escape(slug)}/{escape(p.get('id') or '')}"
    badge = ""
    if mls:
        partner = escape(p.get("_partner_name") or "Rete MLS")
        badge = f'<span class="ah-card-mls" data-testid="agency-home-mls-chip">MLS · {partner}</span>'
    card_cls = "ah-card ah-card-mls" if mls else "ah-card"
    return f"""
    <a class="{card_cls}" href="{escape(link)}"{" target=\"_blank\" rel=\"noopener\"" if mls else ""}>
      <div class="ah-card-img" {bg}>
        <span class="ah-card-op">{op_label}</span>
        <span class="ah-card-price">{escape(price)}</span>
        {badge}
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


def _mls_network_section(network_props: List[Dict[str, Any]]) -> str:
    """Sezione immobili rete — solo caso 1 (mls_enabled)."""
    if network_props:
        cards = "".join(
            _home_card(
                p,
                slug="",
                mls=True,
                href=f"/it/cloud/property/{escape(p.get('id') or '')}",
            )
            for p in network_props
        )
    else:
        cards = (
            '<div class="ah-empty" data-testid="agency-home-mls-empty">'
            "Nessun immobile di rete disponibile al momento. "
            "La sezione resta pronta per il network OMNIA."
            "</div>"
        )
    return f"""
    <section class="ah-section ah-mls-network" id="rete-mls" data-testid="agency-home-mls-network">
      <div class="ah-mls-network-head">
        <h2>Immobili dalla Rete MLS Partner</h2>
        <span class="ah-mls-badge">Network OMNIA</span>
      </div>
      <div class="ah-cards">{cards}</div>
    </section>"""

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
      <div class="ah-mls-head"><h2>{escape(claim)} immobili condivisi</h2></div>
      <div class="ah-box-body">
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
        <button type="button" class="ah-btn" onclick="location.href='/it/cloud?mls=1'">avvia la ricerca</button>
        <div class="ah-powered">Powered by <strong>OMNIA</strong></div>
      </div>
    </aside>"""

def _agency_search_box(lista_href: str = "#ultimi") -> str:
    return f"""
    <section class="ah-box ah-agency" data-testid="agency-home-agency-search">
      <div class="ah-box-body">
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
            <button type="button" class="ah-btn black" onclick="location.href='{escape(lista_href)}'">Avvia la ricerca</button>
          </div>
        </div>
      </div>
    </section>"""


def _contact_form(agency: Dict[str, Any], property_ref: str = "") -> str:
    """Form Contattaci laterale (scheda immobile — stile riferimento)."""
    name = agency.get("display_name") or agency.get("name") or "agenzia"
    rif = property_ref or ""
    default_msg = (
        f"Buongiorno, sono interessato all'immobile rif. {rif}. Vi prego di ricontattarmi. Grazie."
        if rif else
        f"Buongiorno, vorrei informazioni. Grazie."
    )
    return f"""
    <aside class="ah-box ah-agency ah-contact-form" data-testid="agency-property-contact">
      <div class="ah-box-body">
        <h2>Contattaci</h2>
        <form action="mailto:{(agency.get('contact') or {}).get('email') or ''}" method="get" enctype="text/plain">
          <div class="ah-field"><label>Nominativo*</label><input type="text" name="nominativo" required/></div>
          <div class="ah-field"><label>Telefono*</label><input type="tel" name="telefono" required/></div>
          <div class="ah-field"><label>E-mail*</label><input type="email" name="email" required/></div>
          <div class="ah-field"><label>Richiesta*</label>
            <textarea name="body" required>{escape(default_msg)}</textarea>
          </div>
          <p class="ah-consent">Autorizzazione al trattamento dei dati personali
            <label><input type="radio" name="privacy" value="si" required/> Sì</label>
            <label><input type="radio" name="privacy" value="no"/> No</label>
          </p>
          <button type="submit" class="ah-btn black">Invia il modulo</button>
        </form>
        <p class="ah-contact-agency">{escape(name)}</p>
      </div>
    </aside>"""

def _cards_section(title: str, section_id: str, cards_html: str) -> str:
    inner = cards_html or '<div class="ah-empty">Nessun immobile pubblicato al momento.</div>'
    return f"""
    <section class="ah-section" id="{escape(section_id)}" data-testid="agency-home-{escape(section_id)}">
      <h2>{escape(title)}</h2>
      <div class="ah-cards">{inner}</div>
    </section>"""

def render_index(agency: Dict[str, Any], props: List[Dict[str, Any]], slug: str) -> str:
    """Public agency home — struttura allineata al box MLS / vetrina di riferimento.

    Caso 1 (`agency.mls_enabled`): box ricerca rete + sezione Immobili MLS.
    Caso 2 (flag off): solo ricerca agenzia + portafoglio proprio (D-149).
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
    brand_html = _brand_mark(logo, name)
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
    lista_href = f"/api/p/{escape(slug)}/lista"
    mls_html = _mls_search_box(network_count) if mls_on else ""
    network_props = list(agency.get("_mls_network_props") or []) if mls_on else []
    mls_network_html = _mls_network_section(network_props) if mls_on else ""

    nav = f"""
      <nav class="ah-nav" aria-label="Principale">
        <a href="#contatti">Contatti</a>
        <a href="#links">Links</a>
        <a class="on" href="/api/p/{escape(slug)}/">Home</a>
        <a href="#chi-siamo">Chi siamo</a>
        <a href="/api/p/{escape(slug)}/lista?op=sale">Vendita</a>
        <a href="/api/p/{escape(slug)}/lista?op=rent">Affitto</a>
      </nav>
    """

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
      <a class="ah-brand" href="/api/p/{escape(slug)}/" data-testid="agency-home-brand">
        {brand_html}
      </a>
      {nav}
    </div>
    <div class="ah-hero" data-testid="agency-home-hero" {hero_style}>
      <div class="ah-hero-inner">
        <div class="ah-hero-dots" aria-hidden="true"><span class="on"></span><span></span><span></span></div>
      </div>
    </div>
    <div class="{search_row_cls}" data-testid="agency-home-search-row">
      {mls_html}
      {_agency_search_box(lista_href)}
    </div>
    {_cards_section("In evidenza", "evidenza", featured_html)}
    {_cards_section("Ultimi annunci inseriti", "ultimi", latest_html)}
    {mls_network_html}
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

def render_listing(
    agency: Dict[str, Any],
    props: List[Dict[str, Any]],
    slug: str,
    *,
    operation: Optional[str] = None,
) -> str:
    """Pagina lista immobili (clone P0 — home + lista + scheda)."""
    cfg = _resolve_theme_config(agency)
    base = _public_base_url()
    canonical_rel = f"/api/p/{slug}/lista"
    canonical = f"{base}{canonical_rel}" if base else canonical_rel
    name = agency.get("display_name") or agency.get("name") or ""
    op = (operation or "").lower().strip()
    if op in ("rent", "affitto", "a"):
        filtered = [p for p in props if (p.get("operation") or "").lower() in ("rent", "affitto")]
        heading = "Immobili in affitto"
        op_q = "rent"
    elif op in ("sale", "vendita", "v"):
        filtered = [p for p in props if (p.get("operation") or "").lower() in ("sale", "vendita")]
        heading = "Immobili in vendita"
        op_q = "sale"
    else:
        filtered = list(props)
        heading = "Immobili"
        op_q = ""
    title = f"{heading} — {name}"
    desc = f"{len(filtered)} annunci pubblicati da {name} su OMNIA."
    brand_html = _brand_mark(cfg.get("logo_url"), name)
    cards = "".join(_home_card(p, slug) for p in filtered[:48]) or (
        '<div class="ah-empty">Nessun immobile in questa lista.</div>'
    )
    count_line = (
        f'<p class="ah-list-count">Sono stati trovati <strong>{len(filtered)}</strong> immobili.</p>'
        if filtered else ""
    )
    nav = f"""
      <nav class="ah-nav" aria-label="Principale">
        <a href="/api/p/{escape(slug)}/#contatti">Contatti</a>
        <a href="/api/p/{escape(slug)}/#links">Links</a>
        <a href="/api/p/{escape(slug)}/">Home</a>
        <a href="/api/p/{escape(slug)}/#chi-siamo">Chi siamo</a>
        <a class="{'on' if op_q == 'sale' else ''}" href="/api/p/{escape(slug)}/lista?op=sale">Vendita</a>
        <a class="{'on' if op_q == 'rent' else ''}" href="/api/p/{escape(slug)}/lista?op=rent">Affitto</a>
      </nav>
    """
    mls_on = bool(agency.get("mls_enabled"))
    network_count = int(agency.get("_mls_network_count") or 0)
    side_bits = []
    if mls_on:
        side_bits.append(_mls_search_box(network_count))
    side_bits.append(_agency_search_box(f"/api/p/{escape(slug)}/lista"))
    side_html = "".join(side_bits)
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}"/>
<link rel="canonical" href="{escape(canonical)}"/>
<meta name="generator" content="OMNIA Real Estate Ecosystem"/>
<style>{_theme_css(cfg)}
{_home_css()}
.ah-list-count{{font-size:.9rem;color:#555;margin:0 0 14px}}
</style>
</head>
<body class="agency-home" data-theme="{cfg['theme_id']}" data-testid="agency-listing">
  <div class="ah-wrap">
    <div class="ah-top">
      <a class="ah-brand" href="/api/p/{escape(slug)}/" data-testid="agency-listing-brand">{brand_html}</a>
      {nav}
    </div>
    <div class="ah-list-layout">
      <section class="ah-section ah-list-main" id="lista">
        <h2>{escape(heading)}</h2>
        {count_line}
        <div class="ah-cards" data-testid="agency-listing-cards">{cards}</div>
      </section>
      <aside class="ah-list-side" data-testid="agency-listing-search-side">
        {side_html}
      </aside>
    </div>
  </div>
  <footer class="ah-footer">
    <div class="ah-footer-inner">
      <div><h3>{escape(name)}</h3><p>Portafoglio su OMNIA</p></div>
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
    name = agency.get("display_name") or agency.get("name") or ""
    title = f"{p.get('title')} — {name}"
    price = _price_str(p)
    desc = (
        f"{p.get('property_type','')} in {p.get('operation','')} a {p.get('city','')} · "
        f"{p.get('surface_sqm') or '—'} m² · {p.get('rooms') or '—'} locali · {price}"
    ).strip()

    photo_html = "".join(
        f'<img src="/api/public/property/{p["id"]}/photo/{i}" alt="{escape(p.get("title") or "")} foto {i+1}" loading="lazy"/>'
        for i in range(len(photos))
    )
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
    share_title = f"{p.get('title') or ''} — {name}".strip(" —")
    share_text = f"{share_title} · {price}"
    share_html = _share_block(absolute_url, share_title, share_text)
    brand_html = _brand_mark(cfg.get("logo_url"), name)
    contact_html = _contact_form(agency, str(p.get("reference_code") or p.get("id") or ""))
    nav = f"""
      <nav class="ah-nav" aria-label="Principale">
        <a href="/api/p/{escape(slug)}/#contatti">Contatti</a>
        <a href="/api/p/{escape(slug)}/">Home</a>
        <a href="/api/p/{escape(slug)}/lista?op=sale">Vendita</a>
        <a href="/api/p/{escape(slug)}/lista?op=rent">Affitto</a>
      </nav>
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
            "seller": {"@type": "RealEstateAgent", "name": name},
        },
        "areaServed": p.get("city"),
        "url": absolute_url,
    }
    og_img = f'<meta property="og:image" content="{escape(og_image_abs)}"/>' if og_image_abs else ""
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{escape(title)}</title>
<meta name="description" content="{escape(desc)}"/>
<link rel="canonical" href="{escape(absolute_url)}"/>
<meta property="og:type" content="website"/>
<meta property="og:title" content="{escape(title)}"/>
<meta property="og:description" content="{escape(desc)}"/>
<meta property="og:url" content="{escape(absolute_url)}"/>
{og_img}
<meta name="generator" content="OMNIA Real Estate Ecosystem"/>
<style>{_theme_css(cfg)}
{_home_css()}
{_share_css()}</style>
<script type="application/ld+json">{json.dumps(jsonld_obj, ensure_ascii=False)}</script>
</head>
<body class="agency-home" data-theme="{cfg['theme_id']}" data-testid="agency-property">
  <div class="ah-wrap">
    <div class="ah-top">
      <a class="ah-brand" href="/api/p/{escape(slug)}/" data-testid="agency-property-brand">{brand_html}</a>
      {nav}
    </div>
    <div class="ah-prop-layout">
      <article class="ah-prop-main">
        <h1>{escape(p.get('title') or '—')}</h1>
        <p class="meta">{escape(p.get('city') or '')}{(' · ' + escape(p.get('zone'))) if p.get('zone') else ''} · Rif. {escape(p.get('reference_code') or '—')}</p>
        <p class="price">{escape(price)}</p>
        {f'<div class="photos">{photo_html}</div>' if photos else ''}
        <h2>Caratteristiche principali</h2>
        <div class="grid">{cells}</div>
        {description_block}
        {share_html}
      </article>
      <div class="ah-list-side">
        {contact_html}
      </div>
    </div>
  </div>
</body>
</html>"""

