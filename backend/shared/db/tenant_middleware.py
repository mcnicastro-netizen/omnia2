"""OMNIA — early JWT → tenant context middleware."""
from __future__ import annotations

import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("omnia.tenant_mw")


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Decode access_token (if present) and set agency/role contextvars early.

    Auto-inject of agency_id is enabled only for `/api/app/*` so public
    ImmobilCloud search is not accidentally scoped to the logged-in agency.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        from shared.db.connection import set_current_agency_id
        from shared.db.tenant_guard import (
            set_current_role,
            tenant_bypass,
            set_tenant_enforce,
        )

        set_current_agency_id(None)
        set_current_role(None)
        tenant_bypass(False)
        path = request.url.path or ""
        enforce = path.startswith("/api/app")
        set_tenant_enforce(enforce)

        token = request.cookies.get("access_token")
        if not token:
            auth = request.headers.get("authorization") or ""
            if auth.lower().startswith("bearer "):
                token = auth[7:].strip()

        if token and enforce:
            try:
                from shared.auth.jwt_tokens import decode_token
                from shared.db.connection import Database
                from shared.auth.tenant import optional_agency_id

                payload = decode_token(token)
                if payload and payload.get("type") == "access":
                    set_current_role(payload.get("role"))
                    raw = Database.get_raw()
                    user = await raw.users.find_one(
                        {"id": payload.get("sub")},
                        {"_id": 0, "agency_ids": 1, "active_agency_id": 1, "role": 1},
                    )
                    if user:
                        set_current_role(user.get("role") or payload.get("role"))
                        aid = optional_agency_id(user)
                        if aid:
                            set_current_agency_id(aid)
            except Exception as e:
                logger.debug("tenant context skip: %s", e)

        try:
            return await call_next(request)
        finally:
            set_current_agency_id(None)
            set_current_role(None)
            tenant_bypass(False)
            set_tenant_enforce(False)
