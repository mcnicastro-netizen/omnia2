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
    "/api/auth/refresh",  # HttpOnly refresh cookie is the proof; FE often cannot read cross-site CSRF cookie
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


def _cookie_domain() -> Optional[str]:
    """Optional parent domain so FE on cloud./www. can read omnia_csrf via document.cookie."""
    raw = (os.environ.get("COOKIE_DOMAIN") or "").strip()
    return raw or None


def set_csrf_cookie(response: Response, token: Optional[str] = None) -> str:
    token = token or new_csrf_token()
    secure = csrf_enabled()
    kwargs = dict(
        max_age=7 * 24 * 3600,
        httponly=False,
        secure=secure,
        samesite="none" if secure else "lax",
        path="/",
    )
    domain = _cookie_domain()
    if domain:
        kwargs["domain"] = domain
    response.set_cookie(CSRF_COOKIE, token, **kwargs)
    # Cross-origin SPAs cannot always read the cookie; mirror for axios/sessionStorage.
    response.headers["X-CSRF-Token"] = token
    # Expose to browser JS on cross-origin XHR
    response.headers["Access-Control-Expose-Headers"] = "X-CSRF-Token"
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
            else:
                # Keep header mirror so cross-site FE can store token
                response.headers.setdefault("X-CSRF-Token", request.cookies.get(CSRF_COOKIE) or "")
                response.headers.setdefault("Access-Control-Expose-Headers", "X-CSRF-Token")
            return response

        if any(path.startswith(p) for p in _EXEMPT_PREFIXES):
            response = await call_next(request)
            # After login-like flows, ensure cookie exists
            if not request.cookies.get(CSRF_COOKIE):
                set_csrf_cookie(response)
            else:
                response.headers.setdefault("X-CSRF-Token", request.cookies.get(CSRF_COOKIE) or "")
                response.headers.setdefault("Access-Control-Expose-Headers", "X-CSRF-Token")
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
