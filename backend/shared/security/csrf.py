"""OMNIA — CSRF protection when cookies use SameSite=None (cross-site).

Double-submit cookie pattern:
  - Cookie `omnia_csrf` (readable by JS, Secure, SameSite=None)
  - Header `X-CSRF-Token` must match on unsafe methods when a session cookie is present

Local/dev (COOKIE_SECURE=false, SameSite=Lax): middleware is a no-op.
"""
from __future__ import annotations

import hmac
import logging
import os
import secrets
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("omnia.csrf")

CSRF_COOKIE = "omnia_csrf"
CSRF_HEADER = "x-csrf-token"
UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}

# Paths that must work before/without a session (or external webhooks)
_EXEMPT_PREFIXES = (
    "/api/health",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/forgot-password",
    "/api/auth/reset-password",
    "/api/auth/google",
    "/api/auth/mfa/verify",
    "/api/cloud/auth/register",
    "/api/billing/webhook",
    "/api/billing/stripe",
    "/api/feed/",
    "/api/publishing/feed/",
    "/api/public/",
    "/api/v1/",  # API-key auth, not cookie
    "/api/mls-box/",
    "/docs",
    "/redoc",
    "/openapi.json",
)


def csrf_enabled() -> bool:
    """Enforce only when cookies are cross-site capable (SameSite=None)."""
    return os.environ.get("COOKIE_SECURE", "true").lower() != "false"


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def set_csrf_cookie(response: Response, token: Optional[str] = None) -> str:
    token = token or new_csrf_token()
    secure = csrf_enabled()
    response.set_cookie(
        CSRF_COOKIE,
        token,
        max_age=7 * 24 * 3600,
        httponly=False,
        secure=secure,
        samesite="none" if secure else "lax",
        path="/",
    )
    return token


class CsrfMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not csrf_enabled():
            return await call_next(request)

        path = request.url.path or ""
        method = (request.method or "GET").upper()

        if method == "OPTIONS":
            return await call_next(request)

        # Issue/refresh CSRF cookie on safe methods
        if method not in UNSAFE:
            response = await call_next(request)
            if not request.cookies.get(CSRF_COOKIE):
                set_csrf_cookie(response)
            return response

        if any(path.startswith(p) for p in _EXEMPT_PREFIXES):
            response = await call_next(request)
            # After login-like flows, ensure cookie exists
            if not request.cookies.get(CSRF_COOKIE):
                set_csrf_cookie(response)
            return response

        # Bearer API keys are not cookie sessions — skip
        auth = request.headers.get("authorization") or ""
        if auth.lower().startswith("bearer ") and not request.cookies.get("access_token"):
            return await call_next(request)

        # Only enforce when browser session cookie is present (or always for cookie auth paths)
        has_session = bool(request.cookies.get("access_token") or request.cookies.get("refresh_token"))
        if not has_session:
            return await call_next(request)

        cookie_tok = request.cookies.get(CSRF_COOKIE) or ""
        header_tok = request.headers.get(CSRF_HEADER) or request.headers.get("X-CSRF-Token") or ""
        if not cookie_tok or not header_tok or not hmac.compare_digest(cookie_tok, header_tok):
            logger.warning("csrf_rejected path=%s", path)
            return JSONResponse(
                status_code=403,
                content={"detail": {"error": "csrf_failed", "hint": "reload_and_retry"}},
            )

        response = await call_next(request)
        return response
