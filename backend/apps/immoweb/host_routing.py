"""OMNIA — Host-based routing for verified custom domains (M2.S6).

When a verified custom domain (e.g. www.nicastroimmobiliare.it) hits the
backend, we rewrite the incoming request path so that the public themed site
of the corresponding agency is served — without changing any other endpoint.

Mounted as a Starlette middleware in `server.py`.
"""
import logging
import os
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from shared.db.connection import Database

logger = logging.getLogger("omnia.host_routing")


# Internal hosts that bypass the routing (preview / API)
INTERNAL_HOST_SUFFIXES = (
    ".emergentagent.com",
    ".emergent.host",
    "localhost",
    "127.0.0.1",
    "omniarealestateecosystem.it",
)

# Simple in-process cache: { host: agency_slug | None }
_HOST_CACHE: dict = {}
_HOST_CACHE_TTL = 60  # seconds (TTL stored as (slug, expires_ts))


async def _lookup_agency_slug(host: str) -> Optional[str]:
    """Return the agency slug if `host` is a verified custom domain, else None."""
    import time
    now = time.time()
    cached = _HOST_CACHE.get(host)
    if cached and cached[1] > now:
        return cached[0]
    db = Database.get()
    try:
        a = await db.agencies.find_one(
            {
                "website.custom_domain": host,
                "website.custom_domain_status": "verified",
                "is_active": True,
            },
            {"_id": 0, "slug": 1},
        )
    except Exception as e:
        logger.warning("host lookup failed for %s: %s", host, e)
        return None
    slug = (a or {}).get("slug")
    _HOST_CACHE[host] = (slug, now + _HOST_CACHE_TTL)
    return slug


class HostRoutingMiddleware(BaseHTTPMiddleware):
    """Rewrite '/' on a custom domain → '/api/p/{slug}/' (themed agency site)."""

    async def dispatch(self, request: Request, call_next):
        host = (request.headers.get("host") or "").split(":")[0].lower()
        if not host or any(host.endswith(s) for s in INTERNAL_HOST_SUFFIXES):
            return await call_next(request)

        slug = await _lookup_agency_slug(host)
        if not slug:
            return await call_next(request)

        path = request.url.path
        # Don't rewrite API/internal routes; only the "root" experience
        if path.startswith("/api/"):
            return await call_next(request)

        # Rewrite "/" or "/something" → "/api/p/{slug}/..."
        new_path = f"/api/p/{slug}/" if path in ("", "/") else f"/api/p/{slug}{path}"
        request.scope["path"] = new_path
        request.scope["raw_path"] = new_path.encode()
        return await call_next(request)
