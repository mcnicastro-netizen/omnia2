"""OMNIA themes — shared HTML shell/helpers (MOVE-ONLY from theme_render)."""
from __future__ import annotations

import logging
import os
from html import escape
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from apps.immoweb.theme_css import _share_css, _theme_css

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

