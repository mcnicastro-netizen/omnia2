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

from shared.db.connection import Database
from apps.immoweb.themes import render_index, render_property

router = APIRouter(tags=["public-site"])


# ---------------- Binary photo serving ----------------

@router.get("/public/property/{pid}/photo/{idx}")
async def serve_property_photo(pid: str, idx: int):
    """Return one property photo. Handles the 3 storage formats:
    data: base64 (legacy) · /api/media/... (Object Storage, H10) · http(s) URL (302).
    """
    db = Database.get()
    p = await db.properties.find_one(
        {"id": pid, "status": "active"}, {"_id": 0, "photos": 1},
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
        {"agency_id": agency["id"], "status": "active"},
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
        {"agency_id": agency["id"], "status": "active"}, {"_id": 0},
    ).sort("updated_at", -1).to_list(length=200)
    html = render_index(agency, props, slug)
    return Response(content=html, media_type="text/html; charset=utf-8")


# ---------------- Single property page (themed) ----------------

@router.get("/p/{slug}/{pid}", response_class=Response)
async def site_property(slug: str, pid: str):
    agency = await _resolve(slug)
    db = Database.get()
    p = await db.properties.find_one(
        {"id": pid, "agency_id": agency["id"], "status": "active"},
        {"_id": 0, "owner": 0},
    )
    if not p:
        raise HTTPException(status_code=404, detail="property_not_found")
    html = render_property(agency, p, slug)
    return Response(content=html, media_type="text/html; charset=utf-8")
