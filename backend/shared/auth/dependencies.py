"""OMNIA — FastAPI auth dependencies (get_current_user, role guards)."""
from typing import List, Optional
from fastapi import Request, HTTPException, status

from shared.auth.jwt_tokens import decode_token
from shared.db.connection import Database, set_current_agency_id


async def get_token_from_request(request: Request) -> Optional[str]:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    return token


async def get_current_user(request: Request) -> dict:
    token = await get_token_from_request(request)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not_authenticated")

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")

    db = Database.get()
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found")

    # M5 — tenant filtering usa l'agenzia attiva (active_agency_id se legittima, altrimenti la prima)
    from shared.auth.tenant import optional_agency_id
    aid = optional_agency_id(user)
    if aid:
        set_current_agency_id(aid)

    return user


async def get_current_user_optional(request: Request) -> Optional[dict]:
    """Same as get_current_user but returns None when no valid session (public routes)."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


def require_roles(*allowed_roles: str):
    """Dependency factory: returns a dependency that checks the role of current user.

    M2.S5.1 — Franchising role aliases (D-041):
      - `agency_admin` implicitly includes `branch_admin` and `group_admin`
      - `agent` implicitly includes `branch_agent`, `branch_admin`, and `group_admin`
    Existing endpoints keep working without changes; new franchising roles inherit permissions.
    """
    role_aliases = {
        "agency_admin": {"agency_admin", "branch_admin", "group_admin"},
        "agent": {"agent", "branch_agent", "branch_admin", "group_admin"},
    }
    expanded: set = set()
    for r in allowed_roles:
        expanded.update(role_aliases.get(r, {r}))

    async def _guard(request: Request) -> dict:
        user = await get_current_user(request)
        if user.get("role") not in expanded:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return user
    return _guard


async def get_optional_user(request: Request) -> Optional[dict]:
    """Returns user if logged in, None otherwise. Never raises."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
