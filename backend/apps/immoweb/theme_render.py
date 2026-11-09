"""OMNIA themes — public site HTML renderers.

MOVE-ONLY split:
  theme_css.py    — _theme_css / _share_css / _home_css
  theme_common.py — formatters, shell, share block
  theme_home.py   — render_index + render_listing + home widgets
This module keeps render_property + stable re-exports.
"""
from __future__ import annotations

import json
import logging
from html import escape
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

from apps.immoweb.theme_catalog import (
    _resolve_hero_image,
    _resolve_theme_config,
)
from apps.immoweb.theme_common import (
    _brand_mark,
    _contact_form,
    _cover_url,
    _eur,
    _label_it,
    _price_str,
    _public_base_url,
    _render_header,
    _share_block,
    _shell,
)
from apps.immoweb.theme_css import _home_css, _share_css, _theme_css
from apps.immoweb.theme_home import render_index, render_listing

logger = logging.getLogger("omnia.themes")

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
    tipo_it = _label_it("property_type", p.get("property_type"))
    op_it = _label_it("operation", p.get("operation"))
    desc = (
        f"{tipo_it} in {op_it} a {p.get('city','')} · "
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
        cell("Tipologia", tipo_it),
        cell("Operazione", op_it),
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

