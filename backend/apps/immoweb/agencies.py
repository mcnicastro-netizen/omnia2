"""OMNIA — ImmoWeb / Agencies routes (create, read, update, members)."""
import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, status
from shared.db.connection import Database
from shared.auth.dependencies import get_current_user, require_roles
from shared.models.agency import (
    AgencyInDB,
    AgencyPublic,
    AgencyCreate,
    AgencyUpdate,
    make_slug,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agencies", tags=["agencies"])


def _public(doc: dict) -> dict:
    """Strip MongoDB-internal fields before returning."""
    return {k: v for k, v in doc.items() if k != "_id"}


async def _ensure_unique_slug(db, base_slug: str) -> str:
    """Append -2, -3... until slug is unique."""
    slug = base_slug
    counter = 2
    while await db.agencies.find_one({"slug": slug}):
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


async def _attach_user_to_agency(db, user_id: str, agency_id: str) -> None:
    """Add agency_id to user's agency_ids list (idempotent)."""
    await db.users.update_one(
        {"id": user_id},
        {
            "$addToSet": {"agency_ids": agency_id},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )


# -------------------- CREATE (during onboarding) --------------------

@router.post("", status_code=201)
async def create_agency(
    payload: AgencyCreate,
    user: dict = Depends(get_current_user),
):
    """Create a new agency. Caller becomes owner (and is promoted to agency_admin).

    S2 — la registrazione pubblica non assegna più ruoli privilegiati: chi completa
    l'onboarding creando la propria agenzia viene promosso qui, server-side.
    """
    db = Database.get()
    if user.get("role") in ("group_admin", "branch_admin", "branch_agent"):
        raise HTTPException(status_code=403, detail="franchising_roles_use_group_flow")

    # Each agency_admin can own at most one agency in MVP scope
    existing = await db.agencies.find_one({"owner_id": user["id"]})
    if existing:
        raise HTTPException(
            status_code=400,
            detail="agency_already_exists",
        )

    base_slug = make_slug(payload.display_name)
    slug = await _ensure_unique_slug(db, base_slug)

    agency = AgencyInDB(
        slug=slug,
        display_name=payload.display_name,
        fiscal=payload.fiscal,
        address=payload.address or {},
        contact=payload.contact or {},
        branding=payload.branding or {},
        owner_id=user["id"],
        # M2.5.5 — Transfer Domain Vault preferences captured at signup
        domain_sovereignty_confirmed=bool(user.get("signup_domain_sovereignty_confirmed")),
        domain_sovereignty_confirmed_at=(
            datetime.now(timezone.utc).isoformat()
            if user.get("signup_domain_sovereignty_confirmed") else None
        ),
        existing_domain=user.get("signup_existing_domain") or None,
    )
    doc = agency.model_dump()
    await db.agencies.insert_one(doc)
    await _attach_user_to_agency(db, user["id"], agency.id)

    # S2 — promozione controllata: il creatore diventa agency_admin
    if user.get("role") not in ("super_admin", "agency_admin"):
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"role": "agency_admin", "updated_at": datetime.now(timezone.utc).isoformat()}},
        )

    logger.info("Agency created: id=%s slug=%s owner=%s", agency.id, slug, user["email"])
    return _public(doc)


# -------------------- GET MINE --------------------

@router.get("/me")
async def get_my_agency(user: dict = Depends(get_current_user)):
    """Return the agency belonging to the current user (first if multiple)."""
    db = Database.get()
    agency_ids = user.get("agency_ids") or []
    if not agency_ids:
        # Also check ownership (agency_admin who hasn't been auto-linked yet)
        owned = await db.agencies.find_one({"owner_id": user["id"]})
        if owned:
            await _attach_user_to_agency(db, user["id"], owned["id"])
            return _public(owned)
        raise HTTPException(status_code=404, detail="no_agency")

    doc = await db.agencies.find_one({"id": agency_ids[0]})
    if not doc:
        raise HTTPException(status_code=404, detail="agency_not_found")
    return _public(doc)


# -------------------- UPDATE --------------------

@router.patch("/me")
async def update_my_agency(
    payload: AgencyUpdate,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Update the current user's agency. Owner only."""
    db = Database.get()
    agency_ids = user.get("agency_ids") or []
    if not agency_ids:
        raise HTTPException(status_code=404, detail="no_agency")

    agency_id = agency_ids[0]
    existing = await db.agencies.find_one({"id": agency_id})
    if not existing:
        raise HTTPException(status_code=404, detail="agency_not_found")
    if existing["owner_id"] != user["id"] and user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="not_owner")

    update_doc = {"updated_at": datetime.now(timezone.utc).isoformat()}
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        if v is None:
            continue
        if hasattr(v, "model_dump"):
            update_doc[k] = v.model_dump()
        elif isinstance(v, dict):
            update_doc[k] = v
        else:
            update_doc[k] = v

    await db.agencies.update_one({"id": agency_id}, {"$set": update_doc})
    updated = await db.agencies.find_one({"id": agency_id})
    return _public(updated)


# -------------------- MEMBERS LIST --------------------

@router.get("/me/members")
async def list_members(user: dict = Depends(get_current_user)):
    """List all users belonging to the current user's agency."""
    db = Database.get()
    agency_ids = user.get("agency_ids") or []
    if not agency_ids:
        return []
    agency_id = agency_ids[0]

    cursor = db.users.find(
        {"agency_ids": agency_id},
        {"_id": 0, "password_hash": 0},
    )
    members = await cursor.to_list(length=200)
    return members
