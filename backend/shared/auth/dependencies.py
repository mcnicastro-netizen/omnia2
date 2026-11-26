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

    try:
        db = Database.get()
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    except Exception as exc:  # noqa: BLE001
        # B14 — fail-closed if session SoT (Mongo) is unreachable.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="session_store_unavailable",
        ) from exc
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user_not_found")

    # B14 / B03 — access JWT must match an active Mongo-backed session.
    from shared.auth.session_store import assert_access_session

    assert_access_session(user, payload)

    # B03 — suspended / inactive accounts cannot use protected routes
    if user.get("is_active") is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="account_inactive")

    # RBAC — prefer membership.operational_role over drifted users.role
    # when an active org membership exists. Never override super_admin / B2C client.
    # Suspended membership without is_active flip still blocks elevated access.
    role = user.get("role")
    if role not in ("super_admin", "client") and user.get("account_type") != "b2c":
        from shared.auth.membership_service import (
            get_active_membership,
            get_suspended_membership,
        )

        membership = await get_active_membership(db, user["id"])
        if not membership:
            suspended = await get_suspended_membership(db, user["id"])
            if suspended:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="membership_suspended",
                )
        op_role = (membership or {}).get("operational_role")
        if op_role:
            user = {**user, "role": op_role, "role_source": "membership"}
        else:
            user = {**user, "role_source": "users.role"}

    # M5 / D-106 — tenant filtering usa solo active_agency_id se legittima (no fallback [0])
    from shared.auth.tenant import optional_agency_id
    from shared.db.tenant_guard import set_current_role
    set_current_role(user.get("role"))
    aid = optional_agency_id(user)
    if aid:
        set_current_agency_id(aid)

    # MC-042 v2 / MC-054 — cessazione lockout + sospensione billing-only
    from shared.billing.commercial_access import enforce_commercial_access

    await enforce_commercial_access(db, user, request)

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

    Do NOT use for CommercialCustomer wallet admin APIs (DES-04 / DES-08): those must use
    `require_roles_exact` so `branch_admin` cannot inherit Main Admin wallet powers.
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
        # D-174 / B03-DEC-01 — gate email su route operative (require_roles)
        from shared.auth.email_gate import assert_email_verified_for_operations
        assert_email_verified_for_operations(user)
        return user
    return _guard


def require_roles_exact(*allowed_roles: str):
    """Role guard without D-041 alias expansion (deny-by-default on role string).

    B04-H2 / DES-08: wallet centrale + allocate/revoke are Main Admin (or group_admin /
    super_admin ops). `branch_admin` must NOT pass via the agency_admin alias.
    """
    allowed = set(allowed_roles)

    async def _guard(request: Request) -> dict:
        user = await get_current_user(request)
        if user.get("role") not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        from shared.auth.email_gate import assert_email_verified_for_operations
        assert_email_verified_for_operations(user)
        return user
    return _guard


async def get_optional_user(request: Request) -> Optional[dict]:
    """Returns user if logged in, None otherwise. Never raises."""
    try:
        return await get_current_user(request)
    except HTTPException:
        return None
