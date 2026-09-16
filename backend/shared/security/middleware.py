"""OMNIA — HTTP security middleware (headers, global public rate limit, bot friction)."""
from __future__ import annotations

import logging
import os
import re
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("omnia.security.mw")

_PUBLIC_SCRAPE_RE = re.compile(
    r"^/api/(cloud/(search|map|facets|property)|feed/|publishing/feed/|mls-box/|public/)",
)

_EMPTY_UA_PROD = True


def _is_prod() -> bool:
    return (os.environ.get("OMNIA_ENV") or "").strip().lower() in ("production", "prod")


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for") or ""
    if forwarded:
        return forwarded.split(",")[0].strip()[:64] or "unknown"
    if request.client and request.client.host:
        return request.client.host[:64]
    return "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault(
            "Permissions-Policy",
            "geolocation=(self), microphone=(), camera=()",
        )
        response.headers.setdefault("X-OMNIA-Protected", "1")
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("X-Robots-Tag", "noindex, nofollow, noarchive")
        return response


class PublicAbuseGuardMiddleware(BaseHTTPMiddleware):
    """Global IP budget on public scrape surfaces.

    Fail-open if rate-limit storage is unavailable (auth must keep working).
    In production, empty User-Agent on scrape GETs is rejected.
    """

    def __init__(self, app, max_public_per_hour: int = 300):
        super().__init__(app)
        self.max_public_per_hour = max_public_per_hour

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path or ""
        if request.method == "OPTIONS":
            return await call_next(request)

        if _PUBLIC_SCRAPE_RE.search(path):
            ua = (request.headers.get("user-agent") or "").strip()
            if _is_prod() and _EMPTY_UA_PROD and request.method == "GET" and not ua:
                return JSONResponse(
                    status_code=429,
                    content={"detail": {"error": "bot_friction", "hint": "user_agent_required"}},
                    headers={"Retry-After": "3600"},
                )

            try:
                from shared.security.rate_limit import enforce_rate_limit
                await enforce_rate_limit(
                    bucket="public_scrape_global",
                    key=_client_ip(request),
                    max_requests=self.max_public_per_hour,
                    window_seconds=3600,
                )
            except Exception as e:
                from fastapi import HTTPException
                if isinstance(e, HTTPException):
                    return JSONResponse(
                        status_code=e.status_code,
                        content={"detail": e.detail},
                        headers=dict(e.headers or {}),
                    )
                logger.warning("rate_limit fail-open: %s", e)

        return await call_next(request)
