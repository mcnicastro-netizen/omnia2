"""OMNIA — MLS Box / Vetrina Immobili: public widget e API.

Replica la struttura della homepage di riferimento (box network + griglia
In evidenza / Ultimi annunci) — layout Track A allineato al white-label.

Endpoint pubblici (no auth — Bearer API-key facoltativo per rev-share):
  GET  /api/mls-box/agency/{agency_slug}       → JSON per widget
  GET  /api/mls-box/agency/{agency_slug}.html  → HTML embeddabile (iframe)

Rispetta Privacy Gate L1 (viewer anonimo).
Sempre foto Object Storage (URL assoluto).
"""
import os
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from shared.db.connection import Database
from shared.utils.privacy_gate import apply_privacy_view

logger = logging.getLogger("omnia.mls_box")
router = APIRouter(prefix="/mls-box", tags=["mls_box"])


def _serialize_property_card(p: dict) -> dict:
    """Extract just the fields the card needs (privacy-safe L1)."""
    photos = p.get("photos") or []
    cover_url = None
    if photos:
        first = photos[0]
        base = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
        raw = first.get("url") or first.get("path") or ""
        cover_url = raw if raw.startswith("http") else f"{base}{raw}"
    price = p.get("price") or p.get("rent_monthly")
    return {
        "id": p.get("id"),
        "reference_code": p.get("reference_code"),
        "operation": p.get("operation"),
        "property_type": p.get("property_type"),
        "title": p.get("title"),
        "city": p.get("city"),
        "zone": p.get("zone"),
        "price": price,
        "price_negotiable": p.get("price_negotiable"),
        "surface_sqm": p.get("surface_sqm"),
        "rooms": p.get("rooms"),
        "bedrooms": p.get("bedrooms"),
        "bathrooms": p.get("bathrooms"),
        "energy_class": (p.get("energy") or {}).get("energy_class"),
        "view_count": p.get("view_count") or 0,
        "cover_url": cover_url,
        "photos_count": len(photos),
        "detail_path": f"/it/cloud/property/{p.get('id')}",
    }


@router.get("/agency/{agency_slug}")
async def mls_box_json(
    agency_slug: str,
    featured_limit: int = Query(3, ge=1, le=10),
    latest_limit: int = Query(6, ge=1, le=24),
):
    """JSON endpoint per widget/embed.

    Struttura risposta:
      { agency: {...},
        featured: [ {card1}, {card2}, {card3} ],
        latest:   [ {card1}, ... {card6} ] }
    """
    if agency_slug.endswith(".html"):
        return await mls_box_html(agency_slug[:-5], featured_limit=featured_limit,
                                  latest_limit=latest_limit)
    db = Database.get()
    agency = await db.agencies.find_one(
        {"slug": agency_slug},
        {"_id": 0, "id": 1, "name": 1, "display_name": 1, "logo_url": 1,
         "slug": 1, "brand_color": 1, "branding": 1, "mls_enabled": 1},
    )
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")

    aid = agency["id"]
    featured_cursor = db.properties.find(
        {"agency_id": aid, "status": "active",
         "visibility": {"$in": ["public", "mls_only"]},
         "is_exclusive": True},
        {"_id": 0},
    ).sort("updated_at", -1).limit(featured_limit)
    featured_raw = await featured_cursor.to_list(length=featured_limit)

    if len(featured_raw) < featured_limit:
        already = {p["id"] for p in featured_raw}
        extra_cursor = db.properties.find(
            {"agency_id": aid, "status": "active",
             "visibility": {"$in": ["public", "mls_only"]},
             "id": {"$nin": list(already)}},
            {"_id": 0},
        ).sort("view_count", -1).limit(featured_limit - len(featured_raw))
        featured_raw += await extra_cursor.to_list(length=featured_limit)

    latest_cursor = db.properties.find(
        {"agency_id": aid, "status": "active",
         "visibility": {"$in": ["public", "mls_only"]}},
        {"_id": 0},
    ).sort("created_at", -1).limit(latest_limit)
    latest_raw = await latest_cursor.to_list(length=latest_limit)

    featured = [_serialize_property_card(apply_privacy_view(p, "L1")) for p in featured_raw]
    latest = [_serialize_property_card(apply_privacy_view(p, "L1")) for p in latest_raw]

    ids = [p["id"] for p in (featured_raw + latest_raw) if p.get("id")]
    if ids:
        try:
            await db.properties.update_many(
                {"id": {"$in": ids}},
                {"$inc": {"view_count": 1}},
            )
        except Exception:  # pragma: no cover
            pass

    primary = ((agency.get("branding") or {}).get("primary_color")
               or agency.get("brand_color")
               or "#3D8B40")
    return {
        "agency": {
            **agency,
            "display_name": agency.get("display_name") or agency.get("name"),
            "primary_color": primary,
        },
        "featured": featured,
        "latest": latest,
    }


_CARD_HTML = """
<a href="{detail_url}" class="mls-card" target="_blank" rel="noopener">
  <div class="mls-card__img" style="background-image:url({cover_url})">
    <span class="mls-card__op">{op_label}</span>
    <span class="mls-card__price">{price}</span>
  </div>
  <div class="mls-card__body">
    <div class="mls-card__city">{city}</div>
    <div class="mls-card__title">{title}</div>
    <div class="mls-card__zone">{zone}</div>
  </div>
  <div class="mls-card__meta">
    <span>{sqm} Mq</span>
    <span>{rooms} Vani</span>
    <span>{beds} Cam.</span>
  </div>
</a>
"""


def _fmt_price(p: dict) -> str:
    price = p.get("price")
    if not price:
        return "Prezzo su richiesta"
    return f"€ {int(price):,}".replace(",", ".")


def _render_card(p: dict, detail_base: str, featured: bool = False) -> str:
    op = p.get("operation") or "sale"
    op_label = "Vendita" if op == "sale" else "Affitto"
    return _CARD_HTML.format(
        detail_url=f"{detail_base}{p.get('detail_path') or ''}",
        cover_url=p.get("cover_url") or "",
        op_label=op_label,
        price=_fmt_price(p),
        city=(p.get("city") or "").upper(),
        title=p.get("title") or "",
        zone=p.get("zone") or "",
        sqm=int(p.get("surface_sqm") or 0) if p.get("surface_sqm") else "—",
        rooms=int(p.get("rooms") or 0) if p.get("rooms") else "—",
        beds=int(p.get("bedrooms") or 0) if p.get("bedrooms") else "—",
    )


@router.get("/agency/{agency_slug}.html", response_class=HTMLResponse)
async def mls_box_html(
    agency_slug: str,
    featured_limit: int = Query(3, ge=1, le=10),
    latest_limit: int = Query(6, ge=1, le=24),
):
    """HTML embeddabile in iframe sul sito dell'agenzia (layout Track A)."""
    data = await mls_box_json(agency_slug, featured_limit=featured_limit,
                              latest_limit=latest_limit)
    base = os.environ.get("FRONTEND_BASE_URL") or os.environ.get("PUBLIC_BASE_URL", "")
    base = base.rstrip("/")

    featured_html = "".join(_render_card(c, base, featured=True) for c in data["featured"])
    latest_html = "".join(_render_card(c, base) for c in data["latest"])
    if not featured_html:
        featured_html = '<div class="mls-empty">Nessun immobile in evidenza.</div>'
    if not latest_html:
        latest_html = '<div class="mls-empty">Nessun annuncio pubblicato.</div>'

    agency_name = (data["agency"].get("display_name") or data["agency"].get("name") or "").strip()
    primary = data["agency"].get("primary_color") or "#3D8B40"

    html = f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Vetrina Immobili · {agency_name}</title>
<style>
  :root {{ --primary:{primary}; --ink:#222; --muted:#777; --bg:#f4f4f4; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:Arial,Helvetica,sans-serif; background:var(--bg); color:var(--ink); }}
  .mls-wrap {{ max-width:1100px; margin:0 auto; padding:16px 12px 32px; }}
  .mls-hero-title {{
    font-size:1.25rem; font-weight:700; color:#333; margin:1.25rem 0 .85rem;
    padding-bottom:6px; border-bottom:2px solid var(--primary);
  }}
  .mls-grid {{
    display:grid; grid-template-columns:repeat(3,minmax(0,1fr));
    gap:16px;
  }}
  .mls-card {{
    display:block; text-decoration:none; color:inherit;
    background:#fff; border:1px solid #ddd; overflow:hidden;
  }}
  .mls-card:hover {{ box-shadow:0 4px 14px rgba(0,0,0,.1); }}
  .mls-card__img {{
    position:relative; aspect-ratio:4/3; background-size:cover; background-position:center;
    background-color:#e8e8e8;
  }}
  .mls-card__op {{
    position:absolute; top:0; left:0; padding:5px 10px;
    font-size:.72rem; font-weight:700; text-transform:uppercase; color:#fff; background:var(--primary);
  }}
  .mls-card__price {{
    position:absolute; right:8px; bottom:8px; padding:4px 8px;
    font-size:.95rem; font-weight:700; color:#111; background:rgba(255,255,255,.95);
  }}
  .mls-card__body {{ padding:10px 12px 0; }}
  .mls-card__city {{ font-size:.85rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }}
  .mls-card__title {{ font-size:.92rem; line-height:1.3; min-height:2.4em; margin-top:4px; }}
  .mls-card__zone {{ font-size:.78rem; color:var(--muted); margin:4px 0 8px; }}
  .mls-card__meta {{
    display:flex; background:#eee; border-top:1px solid #ddd; margin-top:8px;
  }}
  .mls-card__meta span {{
    flex:1; text-align:center; padding:8px 4px; font-size:.75rem; color:#444;
    border-right:1px solid #ddd;
  }}
  .mls-card__meta span:last-child {{ border-right:0; }}
  .mls-empty {{
    grid-column:1/-1; background:#fff; border:1px dashed #ccc; padding:24px; text-align:center; color:#666;
  }}
  .mls-powered {{ text-align:center; margin-top:18px; font-size:.65rem; letter-spacing:.12em; text-transform:uppercase; color:#888; }}
  @media (max-width:900px) {{ .mls-grid {{ grid-template-columns:1fr 1fr; }} }}
  @media (max-width:560px) {{ .mls-grid {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
  <div class="mls-wrap" data-testid="mls-box-embed">
    <h2 class="mls-hero-title">In evidenza</h2>
    <div class="mls-grid mls-grid--featured">{featured_html}</div>

    <h2 class="mls-hero-title">Ultimi annunci inseriti</h2>
    <div class="mls-grid">{latest_html}</div>
    <div class="mls-powered">Powered by OMNIA</div>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.get("/embed-snippet/{agency_slug}", response_class=HTMLResponse)
async def embed_snippet(agency_slug: str):
    """Restituisce il tag <iframe> pronto per copia-incolla sul sito agenzia."""
    base = os.environ.get("FRONTEND_BASE_URL") or os.environ.get("PUBLIC_BASE_URL", "")
    base = base.rstrip("/")
    snippet = (
        f'<iframe src="{base}/api/mls-box/agency/{agency_slug}.html" '
        f'style="width:100%;min-height:1400px;border:0;" '
        f'loading="lazy" title="Immobili disponibili"></iframe>'
    )
    return HTMLResponse(content=f"<pre>{snippet}</pre>")
