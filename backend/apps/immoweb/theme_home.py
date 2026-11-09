"""OMNIA themes — agency home HTML (MOVE-ONLY from theme_render)."""
from __future__ import annotations

import json
import logging
from html import escape
from typing import Any, Dict, List, Optional, Tuple

from apps.immoweb.theme_catalog import (
    _resolve_hero_image,
    _resolve_theme_config,
)
from apps.immoweb.theme_common import (
    _cover_url,
    _price_str,
    _public_base_url,
)
from apps.immoweb.theme_css import _home_css, _theme_css

logger = logging.getLogger("omnia.themes")

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

