"""OMNIA — Public Site-as-Feed (M2.S5 Layer C + Layer D Phase 2).

Server-rendered HTML pages for agency property portfolio. Designed for SEO &
external crawlers (Idealista, Google, social shares).

In M2.S5 Layer D Phase 2 the actual HTML/CSS is delegated to the Theme Registry
(`themes.py`) so that each agency's public site reflects its brand identity
(palette/typography/structure) — either explicitly chosen or auto-derived
from the Brand Extractor (Phase 1).

Endpoints (public, NO auth):
  GET /api/public/property/{pid}/photo/{i}  → binary JPEG (resolves base64)
  GET /api/p/{slug}/sitemap.xml             → XML sitemap of all active props
  GET /api/p/{slug}/                        → agency listings index (themed)
  GET /api/p/{slug}/{pid}                   → single property page (themed, schema.org)
"""
import base64
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import RedirectResponse

from shared.db.trash import with_not_trashed
from shared.db.public_visibility import brand_site_filter
from shared.db.connection import Database
from shared.storage import get_object, ObjStoreError
from apps.immoweb.themes import render_index, render_listing, render_property

router = APIRouter(tags=["public-site"])


# ---------------- Binary photo serving ----------------

@router.get("/public/property/{pid}/photo/{idx}")
async def serve_property_photo(pid: str, idx: int):
    """Return one property photo. Handles the 3 storage formats:
    data: base64 (legacy) · /api/media/... (Object Storage, H10) · http(s) URL (302).
    """
    db = Database.get()
    p = await db.properties.find_one(
        with_not_trashed({"id": pid, "status": "active"}), {"_id": 0, "photos": 1},
    )
    if not p:
        raise HTTPException(status_code=404, detail="property_not_found")
    photos = p.get("photos") or []
    if idx < 0 or idx >= len(photos):
        raise HTTPException(status_code=404, detail="photo_not_found")
    raw = photos[idx].get("url") or ""

    if raw.startswith("/api/media/"):
        storage_path = raw[len("/api/media/"):]
        try:
            binary, mime = get_object(storage_path)
        except ObjStoreError:
            raise HTTPException(status_code=404, detail="photo_not_found")
        return Response(
            content=binary, media_type=mime or "image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    if raw.startswith("http://") or raw.startswith("https://"):
        return RedirectResponse(raw, status_code=302)

    if raw.startswith("data:"):
        try:
            header, b64 = raw.split(",", 1)
            mime = header.split(";")[0].split(":")[1] or "image/jpeg"
        except (ValueError, IndexError):
            raise HTTPException(status_code=404, detail="invalid_photo_data")
    else:
        mime = "image/jpeg"
        b64 = raw
    try:
        binary = base64.b64decode(b64)
    except Exception:
        raise HTTPException(status_code=404, detail="photo_not_found")
    return Response(
        content=binary, media_type=mime,
        headers={"Cache-Control": "public, max-age=86400"},
    )


# ---------------- Helpers ----------------

async def _resolve(slug: str) -> Dict[str, Any]:
    db = Database.get()
    a = await db.agencies.find_one({"slug": slug, "is_active": True}, {"_id": 0})
    if not a:
        raise HTTPException(status_code=404, detail="agency_not_found")
    return a


# ---------------- Sitemap ----------------

@router.get("/p/{slug}/sitemap.xml")
async def site_sitemap(slug: str):
    agency = await _resolve(slug)
    db = Database.get()
    props = await db.properties.find(
        brand_site_filter(agency["id"]),
        {"_id": 0, "id": 1, "updated_at": 1},
    ).to_list(length=5000)
    urls = []
    base = f"/api/p/{slug}"
    urls.append(f"  <url><loc>{base}/</loc><changefreq>hourly</changefreq><priority>1.0</priority></url>")
    for p in props:
        lastmod = (p.get("updated_at") or "")[:10] or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        urls.append(
            f"  <url><loc>{base}/{p['id']}</loc>"
            f"<lastmod>{lastmod}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>"
        )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls)
        + "\n</urlset>"
    )
    return Response(content=xml, media_type="application/xml; charset=utf-8")


# ---------------- Agency listing index (themed) ----------------

@router.get("/p/{slug}/", response_class=Response)
async def site_index(slug: str):
    agency = await _resolve(slug)
    db = Database.get()
    props = await db.properties.find(
        brand_site_filter(agency["id"]), {"_id": 0},
    ).sort("updated_at", -1).to_list(length=200)
    # Caso 1 (mls_enabled): box ricerca rete + griglia immobili network.
    # Caso 2 (!mls_enabled): nessun pezzo MLS sul sito white-label (D-149).
    if agency.get("mls_enabled"):
        agency = dict(agency)
        try:
            share_filter = with_not_trashed({
                "status": "active",
                "mls_shared": True,
                "visibility": {"$in": ["public", "mls_only"]},
                "agency_id": {"$ne": agency["id"]},
                "is_private_listing": {"$ne": True},
            })
            network_count = await db.properties.count_documents(share_filter)
            agency["_mls_network_count"] = int(network_count)
            network_raw = await db.properties.find(
                share_filter,
                {
                    "_id": 0, "id": 1, "title": 1, "city": 1, "zone": 1,
                    "operation": 1, "price": 1, "rent_monthly": 1,
                    "surface_sqm": 1, "rooms": 1, "bedrooms": 1, "photos": 1,
                    "agency_id": 1,
                },
            ).sort("updated_at", -1).to_list(length=6)
            # Resolve partner agency display names for Co-Agency chip.
            partner_ids = list({p.get("agency_id") for p in network_raw if p.get("agency_id")})
            names: Dict[str, str] = {}
            if partner_ids:
                async for ag in db.agencies.find(
                    {"id": {"$in": partner_ids}},
                    {"_id": 0, "id": 1, "display_name": 1, "name": 1},
                ):
                    names[ag["id"]] = ag.get("display_name") or ag.get("name") or ""
            for p in network_raw:
                p["_partner_name"] = names.get(p.get("agency_id") or "", "")
            agency["_mls_network_props"] = network_raw
        except Exception:
            agency["_mls_network_count"] = 0
            agency["_mls_network_props"] = []
    html = render_index(agency, props, slug)
    return Response(content=html, media_type="text/html; charset=utf-8")


@router.get("/p/{slug}/lista", response_class=Response)
async def site_listing(slug: str, op: str = ""):
    """Lista immobili — pezzo obbligatorio clone P0 (home + lista + scheda)."""
    agency = await _resolve(slug)
    db = Database.get()
    props = await db.properties.find(
        brand_site_filter(agency["id"]), {"_id": 0},
    ).sort("updated_at", -1).to_list(length=200)
    if agency.get("mls_enabled"):
        agency = dict(agency)
        try:
            agency["_mls_network_count"] = int(
                await db.properties.count_documents(
                    with_not_trashed({
                        "status": "active",
                        "mls_shared": True,
                        "visibility": {"$in": ["public", "mls_only"]},
                        "agency_id": {"$ne": agency["id"]},
                        "is_private_listing": {"$ne": True},
                    })
                )
            )
        except Exception:
            agency["_mls_network_count"] = 0
    html = render_listing(agency, props, slug, operation=op or None)
    return Response(content=html, media_type="text/html; charset=utf-8")


@router.get("/p/{slug}/clone-scheda-preview", response_class=Response)
async def site_clone_scheda_preview(slug: str):
    """Scheda preview clone quando non c'è ancora un immobile reale in portafoglio."""
    agency = await _resolve(slug)
    website = agency.get("website") or {}
    capture = website.get("clone_capture") or {}
    sample = next(
        (p for p in (capture.get("pages") or []) if p.get("role") == "property"),
        None,
    )
    title = (sample or {}).get("h1") or (sample or {}).get("title") or "Scheda immobile (preview clone)"
    stub = {
        "id": "clone-preview",
        "title": title,
        "city": (agency.get("address") or {}).get("city") or "Catania",
        "zone": "",
        "operation": "sale",
        "price": None,
        "surface_sqm": None,
        "rooms": None,
        "bedrooms": None,
        "bathrooms": None,
        "description": (
            "Anteprima scheda generata dal clone-from-URL. "
            "I dati vivi arriveranno dal portafoglio OMNIA dell'agenzia."
        ),
        "photos": [],
        "features": {},
        "energy": {},
        "reference_code": "CLONE-PREVIEW",
        "property_type": "apartment",
    }
    html = render_property(agency, stub, slug)
    return Response(
        content=html,
        media_type="text/html; charset=utf-8",
        headers={"X-Robots-Tag": "noindex"},
    )


# ---------------- Single property page (themed) ----------------

@router.get("/p/{slug}/{pid}", response_class=Response)
async def site_property(slug: str, pid: str):
    agency = await _resolve(slug)
    db = Database.get()
    p = await db.properties.find_one(
        brand_site_filter(agency["id"], {"id": pid}),
        {"_id": 0, "owner": 0},
    )
    if not p:
        raise HTTPException(status_code=404, detail="property_not_found")
    html = render_property(agency, p, slug)
    return Response(content=html, media_type="text/html; charset=utf-8")
