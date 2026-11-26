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
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import RedirectResponse

from shared.db.trash import with_not_trashed
from shared.db.public_visibility import (
    AGENCY_PUBLIC_PROJ,
    brand_photo_filter,
    brand_site_filter,
    portal_photo_filter,
    strip_internal_property_fields,
)
from shared.db.connection import Database
from shared.storage import get_object, ObjStoreError
from apps.immoweb.themes import render_index, render_listing, render_property

router = APIRouter(tags=["public-site"])

# D02/S2 — foto soggette a revoca: niente cache condivisa/browser riusabile.
# `private, no-store` forza nuova verifica ACL a ogni richiesta (max-age>0 non sufficiente).
_PHOTO_CACHE_HEADERS = {
    "Cache-Control": "private, no-store",
    "Pragma": "no-cache",
}


# ---------------- Binary photo serving ----------------

@router.get("/public/property/{pid}/photo/{idx}")
async def serve_property_photo(
    pid: str,
    idx: int,
    surface: Literal["portal", "brand", "mls_network"] = Query("portal"),
    agency_slug: Optional[str] = Query(None),
):
    """Return one property photo if authorized for the requested surface (D02).

    - surface=portal → ImmobilCloud SoT (`portal_listing_filter`)
    - surface=brand → brand SoT (`brand_site_filter`) + agency_slug obbligatorio
    - surface=mls_network → listing MLS condiviso attivo (box rete sul brand)

    Handles storage formats: data: base64 · /api/media/... · http(s) URL (302).
    """
    db = Database.get()
    if surface == "brand":
        if not (agency_slug or "").strip():
            raise HTTPException(status_code=400, detail="agency_slug_required_for_brand_surface")
        agency = await db.agencies.find_one(
            {"slug": agency_slug.strip(), "is_active": True},
            {"_id": 0, "id": 1},
        )
        if not agency:
            raise HTTPException(status_code=404, detail="property_not_found")
        flt = brand_photo_filter(agency["id"], pid)
    elif surface == "mls_network":
        flt = with_not_trashed({
            "id": pid,
            "status": "active",
            "mls_shared": True,
            "visibility": {"$in": ["public", "mls_only"]},
            "is_private_listing": {"$ne": True},
        })
    else:
        flt = portal_photo_filter(pid)

    p = await db.properties.find_one(flt, {"_id": 0, "photos": 1})
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
            headers=dict(_PHOTO_CACHE_HEADERS),
        )

    if raw.startswith("http://") or raw.startswith("https://"):
        # External redirect — still gated by surface ACL above.
        # Header no-store sul 302: il client non deve riusare il redirect come cache di auth.
        return RedirectResponse(
            raw,
            status_code=302,
            headers=dict(_PHOTO_CACHE_HEADERS),
        )

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
        headers=dict(_PHOTO_CACHE_HEADERS),
    )


# ---------------- Helpers ----------------

async def _resolve(slug: str) -> Dict[str, Any]:
    """Resolve agency for brand site — projection stretta + id solo per query (D01/S1)."""
    db = Database.get()
    a = await db.agencies.find_one(
        {"slug": slug, "is_active": True},
        {**AGENCY_PUBLIC_PROJ, "id": 1, "mls_enabled": 1, "website": 1, "theme": 1,
         "brand_profile": 1, "name": 1},
    )
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
            network_raw_safe: list = []
            for p in network_raw:
                partner = names.get(p.get("agency_id") or "", "")
                cleaned = strip_internal_property_fields(p)
                cleaned["_partner_name"] = partner
                network_raw_safe.append(cleaned)
            agency["_mls_network_props"] = network_raw_safe
        except Exception:
            agency["_mls_network_count"] = 0
            agency["_mls_network_props"] = []
    safe_props = [strip_internal_property_fields(p) for p in props]
    html = render_index(agency, safe_props, slug)
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
    safe_props = [strip_internal_property_fields(p) for p in props]
    html = render_listing(agency, safe_props, slug, operation=op or None)
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
    html = render_property(agency, strip_internal_property_fields(p), slug)
    return Response(content=html, media_type="text/html; charset=utf-8")
