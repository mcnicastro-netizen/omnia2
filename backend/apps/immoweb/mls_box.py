"""OMNIA — MLS Box: public widget e API per griglia immobili embed.

Replica la struttura della homepage www.nicastroimmobiliare.it:
- 3 immobili "in evidenza" (slider top)
- 6 "ultimi annunci inseriti" (griglia 3x2)

Endpoint pubblici (no auth — Bearer API-key facoltativo per rev-share):
  GET  /api/mls-box/agency/{agency_slug}       → JSON per widget
  GET  /api/mls-box/agency/{agency_slug}.html  → HTML embeddabile (iframe)

Rispetta Privacy Gate L1 (viewer anonimo):
- indirizzo esatto oscurato
- proprietario / prezzo trattabile / note interne rimossi
- energy_class visibile (fix P0-A)

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
        # objstore path or absolute URL
        base = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
        raw = first.get("url") or first.get("path") or ""
        cover_url = raw if raw.startswith("http") else f"{base}{raw}"
    price = p.get("price") or p.get("rent_monthly")
    return {
        "id": p.get("id"),
        "reference_code": p.get("reference_code"),  # es. "Rif 25002"
        "operation": p.get("operation"),  # sale / rent
        "property_type": p.get("property_type"),
        "title": p.get("title"),
        "city": p.get("city"),
        "zone": p.get("zone"),
        "price": price,
        "price_negotiable": p.get("price_negotiable"),
        "surface_sqm": p.get("surface_sqm"),
        "rooms": p.get("rooms"),
        "bedrooms": p.get("bedrooms"),
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
    # Route disambiguation: `.html` variant is a separate endpoint below.
    if agency_slug.endswith(".html"):
        return await mls_box_html(agency_slug[:-5], featured_limit=featured_limit,
                                  latest_limit=latest_limit)
    db = Database.get()
    agency = await db.agencies.find_one(
        {"slug": agency_slug},
        {"_id": 0, "id": 1, "name": 1, "logo_url": 1, "slug": 1, "brand_color": 1},
    )
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")

    aid = agency["id"]
    # Featured: is_exclusive OR view_count top, active + public
    featured_cursor = db.properties.find(
        {"agency_id": aid, "status": "active",
         "visibility": {"$in": ["public", "mls_only"]},
         "is_exclusive": True},
        {"_id": 0},
    ).sort("updated_at", -1).limit(featured_limit)
    featured_raw = await featured_cursor.to_list(length=featured_limit)

    # Se meno di N featured → completa con top-view immobili
    if len(featured_raw) < featured_limit:
        already = {p["id"] for p in featured_raw}
        extra_cursor = db.properties.find(
            {"agency_id": aid, "status": "active",
             "visibility": {"$in": ["public", "mls_only"]},
             "id": {"$nin": list(already)}},
            {"_id": 0},
        ).sort("view_count", -1).limit(featured_limit - len(featured_raw))
        featured_raw += await extra_cursor.to_list(length=featured_limit)

    # Latest: last inserted
    latest_cursor = db.properties.find(
        {"agency_id": aid, "status": "active",
         "visibility": {"$in": ["public", "mls_only"]}},
        {"_id": 0},
    ).sort("created_at", -1).limit(latest_limit)
    latest_raw = await latest_cursor.to_list(length=latest_limit)

    # Apply Privacy Gate L1 (anonymous viewer)
    featured = [_serialize_property_card(apply_privacy_view(p, "L1")) for p in featured_raw]
    latest = [_serialize_property_card(apply_privacy_view(p, "L1")) for p in latest_raw]

    # Increment view_count on rendered properties (best-effort, batched)
    ids = [p["id"] for p in (featured_raw + latest_raw) if p.get("id")]
    if ids:
        try:
            await db.properties.update_many(
                {"id": {"$in": ids}},
                {"$inc": {"view_count": 1}},
            )
        except Exception:  # pragma: no cover
            pass

    return {
        "agency": agency,
        "featured": featured,
        "latest": latest,
    }


# ---------- HTML embed (iframe-friendly, self-styled Mediterranean Future 2035) ----------

_CARD_HTML = """
<a href="{detail_url}" class="mls-card" target="_blank" rel="noopener">
  <div class="mls-card__img" style="background-image:url({cover_url})">
    <span class="mls-card__op mls-card__op--{op}">{op_label}</span>
    {featured_badge}
  </div>
  <div class="mls-card__body">
    <div class="mls-card__ref">{ref}</div>
    <div class="mls-card__price">{price}</div>
    <div class="mls-card__city">{city}</div>
    <div class="mls-card__title">{title}</div>
    <div class="mls-card__zone">{zone}</div>
    <div class="mls-card__meta">
      <span>{sqm} m²</span>
      <span>{rooms} vani</span>
      <span class="mls-card__energy mls-card__energy--{energy}">{energy}</span>
    </div>
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
    energy = (p.get("energy_class") or "-").upper()[:2]
    return _CARD_HTML.format(
        detail_url=f"{detail_base}{p.get('detail_path') or ''}",
        cover_url=p.get("cover_url") or "",
        op=op,
        op_label=op_label,
        featured_badge='<span class="mls-card__featured">In evidenza</span>' if featured else "",
        ref=p.get("reference_code") or "",
        price=_fmt_price(p),
        city=(p.get("city") or "").upper(),
        title=p.get("title") or "",
        zone=p.get("zone") or "",
        sqm=int(p.get("surface_sqm") or 0),
        rooms=int(p.get("rooms") or 0),
        energy=energy,
    )


@router.get("/agency/{agency_slug}.html", response_class=HTMLResponse)
async def mls_box_html(
    agency_slug: str,
    featured_limit: int = Query(3, ge=1, le=10),
    latest_limit: int = Query(6, ge=1, le=24),
):
    """HTML embeddabile in iframe sul sito dell'agenzia."""
    data = await mls_box_json(agency_slug, featured_limit=featured_limit,
                              latest_limit=latest_limit)
    base = os.environ.get("FRONTEND_BASE_URL") or os.environ.get("PUBLIC_BASE_URL", "")
    base = base.rstrip("/")

    featured_html = "".join(_render_card(c, base, featured=True) for c in data["featured"])
    latest_html = "".join(_render_card(c, base) for c in data["latest"])

    agency_name = (data["agency"].get("name") or "").strip()

    html = f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MLS Box · {agency_name}</title>
<style>
  :root {{
    --navy:#0B1E3F; --emerald:#0F6B5B; --gold:#C69F4C; --offwhite:#FAF8F3;
    --stone:#6B6B6B; --ink:#0E1419;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:'Fraunces',Georgia,serif; background:var(--offwhite); color:var(--ink); }}
  .mls-hero-title {{
    font-size:1.35rem; letter-spacing:.08em; text-transform:uppercase;
    color:var(--navy); margin:2rem 0 1rem; padding-left:1rem; border-left:3px solid var(--gold);
  }}
  .mls-grid {{
    display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr));
    gap:1.25rem; padding:0 1rem 2rem;
  }}
  .mls-grid--featured {{ grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); }}
  .mls-card {{
    display:block; text-decoration:none; color:inherit;
    background:#fff; border:1px solid #E9E4D6; overflow:hidden;
    transition:transform .25s ease, box-shadow .25s ease;
  }}
  .mls-card:hover {{ transform:translateY(-2px); box-shadow:0 12px 28px rgba(11,30,63,.10); }}
  .mls-card__img {{
    position:relative; aspect-ratio:16/10; background-size:cover; background-position:center;
    background-color:#E9E4D6;
  }}
  .mls-card__op {{
    position:absolute; top:.75rem; left:.75rem; padding:.25rem .6rem;
    font-family:'Inter',sans-serif; font-size:.7rem; letter-spacing:.1em;
    text-transform:uppercase; color:#fff; background:var(--navy);
  }}
  .mls-card__op--rent {{ background:var(--emerald); }}
  .mls-card__featured {{
    position:absolute; top:.75rem; right:.75rem; padding:.25rem .6rem;
    font-family:'Inter',sans-serif; font-size:.65rem; letter-spacing:.15em;
    text-transform:uppercase; color:var(--navy); background:var(--gold);
  }}
  .mls-card__body {{ padding:1rem 1.1rem 1.25rem; }}
  .mls-card__ref {{ font-family:'Inter',sans-serif; font-size:.7rem; letter-spacing:.1em; color:var(--stone); }}
  .mls-card__price {{ font-size:1.5rem; font-weight:600; color:var(--navy); margin:.15rem 0 .35rem; }}
  .mls-card__city {{ font-size:.9rem; letter-spacing:.14em; color:var(--emerald); text-transform:uppercase; }}
  .mls-card__title {{ font-size:1rem; margin:.35rem 0 .25rem; color:var(--ink); line-height:1.35; }}
  .mls-card__zone {{ font-family:'Inter',sans-serif; font-size:.8rem; color:var(--stone); }}
  .mls-card__meta {{
    display:flex; gap:.85rem; margin-top:.75rem; padding-top:.6rem;
    border-top:1px dashed #E4DFCE; font-family:'Inter',sans-serif;
    font-size:.78rem; color:var(--stone);
  }}
  .mls-card__energy {{
    margin-left:auto; padding:0 .5rem; color:#fff; font-weight:600; letter-spacing:.05em;
    background:var(--stone);
  }}
  .mls-card__energy--A, .mls-card__energy--A1, .mls-card__energy--A2,
  .mls-card__energy--A3, .mls-card__energy--A4 {{ background:#1E8449; }}
  .mls-card__energy--B, .mls-card__energy--C {{ background:#28B463; }}
  .mls-card__energy--D, .mls-card__energy--E {{ background:#D68910; }}
  .mls-card__energy--F, .mls-card__energy--G {{ background:#C0392B; }}
  @media (max-width:640px) {{
    .mls-grid, .mls-grid--featured {{ grid-template-columns:1fr; }}
  }}
</style>
</head>
<body>
  <h2 class="mls-hero-title">In evidenza</h2>
  <div class="mls-grid mls-grid--featured">{featured_html}</div>

  <h2 class="mls-hero-title">Ultimi annunci inseriti</h2>
  <div class="mls-grid">{latest_html}</div>
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
