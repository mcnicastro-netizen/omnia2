"""OMNIA themes — public site HTML renderers.

MOVE-ONLY split:
  theme_css.py    — _theme_css / _share_css / _home_css
  theme_common.py — formatters, shell, share block
  theme_home.py   — render_index + home widgets
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
    _cover_url,
    _eur,
    _price_str,
    _public_base_url,
    _render_header,
    _share_block,
    _shell,
)
from apps.immoweb.theme_css import _home_css, _share_css, _theme_css
from apps.immoweb.theme_home import render_index

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



__all__ = [
    "render_index",
    "render_property",
    "_theme_css",
    "_home_css",
    "_share_css",
    "_share_block",
    "_shell",
    "_eur",
    "_price_str",
    "_cover_url",
]
