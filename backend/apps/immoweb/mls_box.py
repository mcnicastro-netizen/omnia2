"""OMNIA — MLS Box / Vetrina Immobili: public widget e API.

Due pezzi pubblici (D-170):
  1. Box ricerca rete — drop-in sul sito già proprio (sostituisce solo quel riquadro)
  2. Vetrina featured/latest — iframe griglia (sito OMNIA / vetrina larga)

Endpoint pubblici (no auth):
  GET  /api/mls-box/search/{agency_slug}.html  → form ricerca rete (iframe stretto)
  GET  /api/mls-box/embed-kit/{agency_slug}    → JSON snippet + istruzioni
  GET  /api/mls-box/agency/{agency_slug}       → JSON vetrina
  GET  /api/mls-box/agency/{agency_slug}.html  → HTML vetrina (iframe largo)

Rispetta Privacy Gate L1 (viewer anonimo).
Sempre foto Object Storage (URL assoluto).
"""
import os
import logging
from html import escape
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

from shared.db.connection import Database
from shared.db.trash import with_not_trashed
from shared.utils.privacy_gate import apply_privacy_view
from apps.immoweb.mls import _shareable_listing_filters

logger = logging.getLogger("omnia.mls_box")
router = APIRouter(prefix="/mls-box", tags=["mls_box"])

_EMBED_HEADERS = {
    "X-Frame-Options": "ALLOWALL",
    "Content-Security-Policy": "frame-ancestors *",
    "Cache-Control": "public, max-age=60",
}

_PROVINCE_OPTS = [
    ("", "Scegli"),
    ("CT", "CATANIA"),
    ("ME", "MESSINA"),
    ("PA", "PALERMO"),
    ("RG", "RAGUSA"),
    ("SR", "SIRACUSA"),
    ("EN", "ENNA"),
    ("CL", "CALTANISSETTA"),
    ("AG", "AGRIGENTO"),
    ("RC", "REGGIO CALABRIA"),
    ("RM", "ROMA"),
    ("MI", "MILANO"),
    ("NA", "NAPOLI"),
]


def _public_api_base() -> str:
    return (
        os.environ.get("PUBLIC_BASE_URL")
        or os.environ.get("FRONTEND_BASE_URL")
        or ""
    ).rstrip("/")


def _frontend_base() -> str:
    return (
        os.environ.get("FRONTEND_BASE_URL")
        or os.environ.get("PUBLIC_BASE_URL")
        or ""
    ).rstrip("/")


def _html(content: str) -> HTMLResponse:
    return HTMLResponse(content=content, headers=dict(_EMBED_HEADERS))


def search_iframe_snippet(agency_slug: str, api_base: Optional[str] = None) -> str:
    base = (api_base or _public_api_base()).rstrip("/")
    src = f"{base}/api/mls-box/search/{agency_slug}.html"
    return (
        f'<iframe src="{src}" '
        f'style="width:100%;min-height:540px;border:0;display:block" '
        f'loading="lazy" title="Ricerca immobili rete MLS"></iframe>'
    )


def build_embed_kit(
    agency_slug: str,
    *,
    ready: bool,
    api_base: Optional[str] = None,
) -> Dict[str, Any]:
    """Snippet + copy per il webmaster: solo il box, il resto del sito non si tocca."""
    base = (api_base or _public_api_base()).rstrip("/")
    search_url = f"{base}/api/mls-box/search/{agency_slug}.html"
    return {
        "mode": "iframe_on_own_site",
        "ready": bool(ready),
        "agency_slug": agency_slug,
        "search_url": search_url,
        "iframe_html": search_iframe_snippet(agency_slug, base),
        "how_to": [
            "Apri il pannello del tuo sito (la stessa area dove gestisci la home).",
            "Trova il riquadro di ricerca della rete MLS, di solito a sinistra in home.",
            "Sostituiscilo con il codice qui sotto e pubblica. Il resto del sito resta identico.",
        ],
    }


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
    # Caso 2 (D-149): senza adesione MLS il widget rete non è esposto.
    # La vetrina white-label `/api/p/{slug}/` resta attiva senza box MLS.
    if not agency.get("mls_enabled"):
        raise HTTPException(status_code=404, detail="mls_not_enabled")

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
    return _html(html)


@router.get("/embed-snippet/{agency_slug}", response_class=HTMLResponse)
async def embed_snippet(agency_slug: str):
    """Vetrina larga (retrocompat). Il box ricerca rete è `/embed-kit` (D-170)."""
    base = _public_api_base()
    snippet = (
        f'<iframe src="{base}/api/mls-box/agency/{agency_slug}.html" '
        f'style="width:100%;min-height:1400px;border:0;" '
        f'loading="lazy" title="Immobili disponibili"></iframe>'
    )
    return _html(f"<pre>{escape(snippet)}</pre>")


def _cover_abs(p: dict) -> str:
    photos = p.get("photos") or []
    if not photos:
        return ""
    first = photos[0] if isinstance(photos[0], dict) else {}
    raw = first.get("url") or first.get("path") or ""
    if not raw:
        return ""
    if raw.startswith("http"):
        return raw
    return f"{_public_api_base()}{raw}"


def render_mls_search_html(
    *,
    agency_name: str,
    primary: str,
    network_count: int,
    default_province: str,
    operation: str,
    categoria: str,
    province: str,
    city: str,
    price_min: str,
    price_max: str,
    searched: bool,
    items: List[dict],
    result_total: int,
    detail_base: str,
) -> str:
    """Box ricerca rete — stesso schema del riquadro home (contratto/provincia/prezzo)."""
    claim_n = f"{network_count:,}".replace(",", ".") if network_count else "Rete"
    head = f"{claim_n} immobili condivisi"
    name = escape(agency_name or "")
    primary = escape(primary or "#3D8B40")
    city_val = escape(city or "")
    pmin = escape(price_min or "")
    pmax = escape(price_max or "")

    def _opts(pairs, selected):
        bits = []
        for v, lbl in pairs:
            sel = " selected" if v == selected else ""
            bits.append(f'<option value="{escape(v)}"{sel}>{escape(lbl)}</option>')
        return "".join(bits)

    prov_selected = (province or default_province or "").upper()[:2]
    results_html = ""
    if searched:
        if items:
            cards = []
            for p in items:
                href = escape(f"{detail_base}/it/cloud/property/{p.get('id') or ''}")
                cover = escape(p.get("cover_url") or "")
                bg = f'style="background-image:url(\'{cover}\')"' if cover else ""
                price = _fmt_price(p)
                title = escape(p.get("title") or "Immobile")
                city_l = escape((p.get("city") or "").upper())
                cards.append(
                    f'<a class="res" href="{href}" target="_blank" rel="noopener">'
                    f'<div class="res-img" {bg}></div>'
                    f'<div class="res-body"><div class="res-price">{escape(price)}</div>'
                    f'<div class="res-title">{title}</div>'
                    f'<div class="res-city">{city_l}</div></div></a>'
                )
            results_html = (
                f'<p class="res-count">{result_total} in rete</p>'
                + "".join(cards)
            )
        else:
            results_html = (
                '<p class="res-empty">Nessun immobile in rete con questi filtri.</p>'
            )

    return f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Rete MLS · {name}</title>
<style>
  :root {{ --primary:{primary}; --ink:#222; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:Arial,Helvetica,sans-serif; background:#fff; color:var(--ink); }}
  .box {{ border:1px solid var(--primary); }}
  .head {{ background:var(--primary); color:#fff; padding:10px 12px; }}
  .head h1 {{ margin:0; font-size:.92rem; font-weight:700; }}
  form {{ padding:12px; }}
  label {{ display:block; font-size:.72rem; margin:0 0 3px; color:#444; }}
  .field {{ margin-bottom:8px; }}
  select, input {{ width:100%; padding:8px 9px; border:1px solid #d0d0d0; border-radius:2px; font-size:.85rem; }}
  .range {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; }}
  button {{ display:block; width:100%; margin-top:8px; padding:10px 12px; border:0; background:#5a5a5a; color:#fff; font-weight:700; font-size:.9rem; cursor:pointer; }}
  .powered {{ text-align:center; padding:0 12px 12px; font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; color:#666; }}
  .powered strong {{ color:#c62828; font-weight:800; }}
  .res-count {{ margin:0; padding:8px 12px 0; font-size:.75rem; color:#555; }}
  .res {{ display:flex; gap:8px; padding:8px 12px; text-decoration:none; color:inherit; border-top:1px solid #eee; }}
  .res:hover {{ background:#fafafa; }}
  .res-img {{ width:64px; height:48px; flex:none; background:#e8e8e8 center/cover no-repeat; }}
  .res-price {{ font-weight:700; font-size:.85rem; }}
  .res-title {{ font-size:.78rem; line-height:1.25; }}
  .res-city {{ font-size:.68rem; color:#777; letter-spacing:.04em; }}
  .res-empty {{ margin:0; padding:12px; font-size:.8rem; color:#666; }}
</style>
</head>
<body>
  <div class="box" data-testid="mls-search-embed">
    <div class="head"><h1>{escape(head)}</h1></div>
    <form method="get" action="">
      <div class="field"><label>Contratto</label>
        <select name="operation">{_opts([("sale", "Vendita"), ("rent", "Affitto")], operation or "sale")}</select>
      </div>
      <div class="field"><label>Categoria</label>
        <select name="categoria">{_opts([("", "Tutte"), ("residential", "Residenziale"), ("commercial", "Commerciale")], categoria or "residential")}</select>
      </div>
      <div class="field"><label>Provincia</label>
        <select name="province">{_opts(_PROVINCE_OPTS, prov_selected)}</select>
      </div>
      <div class="field"><label>Comune</label>
        <input type="text" name="city" value="{city_val}" placeholder="es. Catania" autocomplete="off"/>
      </div>
      <div class="field"><label>Prezzo</label>
        <div class="range">
          <input type="number" name="price_min" value="{pmin}" placeholder="Min" min="0"/>
          <input type="number" name="price_max" value="{pmax}" placeholder="Max" min="0"/>
        </div>
      </div>
      <input type="hidden" name="go" value="1"/>
      <button type="submit">avvia la ricerca</button>
    </form>
    {results_html}
    <div class="powered">Powered by <strong>OMNIA</strong></div>
  </div>
</body>
</html>"""


async def _require_mls_agency(agency_slug: str) -> dict:
    db = Database.get()
    agency = await db.agencies.find_one(
        {"slug": agency_slug},
        {"_id": 0, "id": 1, "name": 1, "display_name": 1, "slug": 1,
         "brand_color": 1, "branding": 1, "mls_enabled": 1, "address": 1},
    )
    if not agency:
        raise HTTPException(status_code=404, detail="agency_not_found")
    if not agency.get("mls_enabled"):
        raise HTTPException(status_code=404, detail="mls_not_enabled")
    return agency


def _default_province(agency: dict) -> str:
    addr = agency.get("address") or {}
    raw = (addr.get("province_sigla") or addr.get("province") or "").strip().upper()
    if len(raw) == 2:
        return raw
    return "CT"


@router.get("/embed-kit/{agency_slug}")
async def embed_kit_json(agency_slug: str):
    """JSON per CRM / webmaster: iframe del box ricerca rete."""
    agency = await _require_mls_agency(agency_slug)
    kit = build_embed_kit(agency["slug"], ready=True)
    return JSONResponse(kit)


@router.get("/search/{agency_slug}.html", response_class=HTMLResponse)
async def mls_search_html(
    agency_slug: str,
    operation: str = Query("sale"),
    categoria: str = Query("residential"),
    province: str = Query(""),
    city: str = Query(""),
    price_min: str = Query(""),
    price_max: str = Query(""),
    go: str = Query(""),
):
    """Box ricerca rete embeddabile sul sito già proprio (D-170)."""
    agency = await _require_mls_agency(agency_slug)
    db = Database.get()
    network_count = await db.properties.count_documents(
        with_not_trashed(_shareable_listing_filters())
    )

    items: List[dict] = []
    result_total = 0
    searched = (go or "").strip() in ("1", "true", "yes") or bool(
        (province or city or price_min or price_max or "").strip()
    )
    if searched:
        q: Dict[str, Any] = dict(_shareable_listing_filters())
        op = (operation or "").strip().lower()
        if op in ("sale", "rent"):
            q["operation"] = op
        prov = (province or "").strip().upper()[:2]
        if prov:
            q["$or"] = [
                {"province_sigla": prov},
                {"province": prov},
                {"province": {"$regex": f"^{prov}$", "$options": "i"}},
            ]
        if (city or "").strip():
            q["city"] = {"$regex": f"^{city.strip()}$", "$options": "i"}
        try:
            pmn = float(price_min) if price_min else None
        except ValueError:
            pmn = None
        try:
            pmx = float(price_max) if price_max else None
        except ValueError:
            pmx = None
        if pmn is not None or pmx is not None:
            price_q: Dict[str, Any] = {}
            if pmn is not None:
                price_q["$gte"] = pmn
            if pmx is not None:
                price_q["$lte"] = pmx
            q["price"] = price_q
        cat = (categoria or "").strip().lower()
        if cat == "commercial":
            q["property_type"] = {"$in": ["commerciale", "negozio", "ufficio", "capannone", "commercial"]}
        q = with_not_trashed(q)
        result_total = await db.properties.count_documents(q)
        raw = await db.properties.find(q, {"_id": 0}).sort("created_at", -1).limit(12).to_list(12)
        items = [
            {
                "id": p.get("id"),
                "title": p.get("title"),
                "city": p.get("city"),
                "price": p.get("price") or p.get("rent_monthly"),
                "cover_url": _cover_abs(p),
            }
            for p in raw
        ]
        searched = True
    else:
        searched = False

    primary = (
        ((agency.get("branding") or {}).get("primary_color"))
        or agency.get("brand_color")
        or "#3D8B40"
    )
    html = render_mls_search_html(
        agency_name=agency.get("display_name") or agency.get("name") or "",
        primary=primary,
        network_count=int(network_count or 0),
        default_province=_default_province(agency),
        operation=operation if operation in ("sale", "rent") else "sale",
        categoria=categoria if categoria in ("", "residential", "commercial") else "residential",
        province=province,
        city=city,
        price_min=price_min,
        price_max=price_max,
        searched=searched,
        items=items,
        result_total=result_total,
        detail_base=_frontend_base(),
    )
    return _html(html)
