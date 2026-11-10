"""OMNIA — ImmoWeb / Agencies routes (create, read, update, members)."""
import logging
import re
from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status, File, UploadFile
from shared.db.connection import Database
from shared.auth.dependencies import get_current_user, require_roles
from shared.auth.tenant import require_agency
from shared.models.agency import (
    AgencyInDB,
    AgencyPublic,
    AgencyCreate,
    AgencyUpdate,
    make_slug,
)
from shared.storage import put_object, ObjStoreError

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


async def _attach_user_to_agency(
    db, user_id: str, agency_id: str, *, force_active: bool = False
) -> None:
    """Add agency_id to membership; set active_agency_id if missing/invalid (D-106).

    force_active=True (create onboarding): always switch to the new agency so the
    owner never stays on a stale seed/demo tenant (false «collaboratori»).
    """
    user = await db.users.find_one(
        {"id": user_id}, {"_id": 0, "agency_ids": 1, "active_agency_id": 1}
    )
    ids = list((user or {}).get("agency_ids") or [])
    active = (user or {}).get("active_agency_id")
    set_fields = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if force_active or not active or active not in (ids + [agency_id]):
        set_fields["active_agency_id"] = agency_id
    await db.users.update_one(
        {"id": user_id},
        {"$addToSet": {"agency_ids": agency_id}, "$set": set_fields},
    )


_EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _validate_onboarding_contact(contact) -> None:
    """PEC + telefono obbligatori — non scaricare sul Founder dati incompleti."""
    c = contact.model_dump() if hasattr(contact, "model_dump") else (contact or {})
    phone = str(c.get("phone") or "").strip()
    digits = re.sub(r"[\s./()-]", "", phone)
    digits = re.sub(r"^(?:\+39|0039)", "", digits)
    if not re.fullmatch(r"\d{8,12}", digits or ""):
        raise HTTPException(status_code=400, detail="phone_required_or_invalid")
    pec = str(c.get("pec") or "").strip().lower()
    if not pec or not _EMAIL_RE.match(pec):
        raise HTTPException(status_code=400, detail="pec_required_or_invalid")


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

    _validate_onboarding_contact(payload.contact)

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
    # Wizard «Crea agenzia» = onboarding chiuso (evita PATCH /me prima del refresh sessione)
    doc["onboarding_completed"] = True
    # CRM locked until Founder Ops activates (email + optional plan grant)
    doc["activation_status"] = "pending"
    doc["activated_at"] = None
    doc["activated_by"] = None
    await db.agencies.insert_one(doc)
    await _attach_user_to_agency(db, user["id"], agency.id, force_active=True)

    # S2 — promozione controllata: il creatore diventa agency_admin
    if user.get("role") not in ("super_admin", "agency_admin"):
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": {"role": "agency_admin", "updated_at": datetime.now(timezone.utc).isoformat()}},
        )

    logger.info(
        "Agency created (pending activation): id=%s slug=%s owner=%s",
        agency.id,
        slug,
        user["email"],
    )
    # Rileggi dopo promote/attach così il client può allineare la sessione
    fresh = await db.agencies.find_one({"id": agency.id}, {"_id": 0})
    return _public(fresh or doc)


# -------------------- GET MINE --------------------

@router.get("/me")
async def get_my_agency(user: dict = Depends(get_current_user)):
    """Return the active agency (D-106 SoT: active_agency_id)."""
    db = Database.get()
    agency_ids = user.get("agency_ids") or []
    if not agency_ids:
        # Also check ownership (agency_admin who hasn't been auto-linked yet)
        owned = await db.agencies.find_one({"owner_id": user["id"]})
        if owned:
            await _attach_user_to_agency(db, user["id"], owned["id"])
            return _public(owned)
        raise HTTPException(status_code=404, detail="no_agency")

    agency_id = require_agency(user)
    doc = await db.agencies.find_one({"id": agency_id})
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
    agency_id = require_agency(user)
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


# -------------------- LOGO UPLOAD (onboarding / settings) --------------------

@router.post("/logo-upload")
async def upload_agency_logo(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Carica logo agenzia (PNG/JPEG/WebP/SVG) → Object Storage → URL /api/media/…

    Usabile in onboarding (prima della create) o da agency_admin.
    """
    ct = (file.content_type or "").lower().split(";")[0].strip()
    allowed = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/webp": "webp",
        "image/svg+xml": "svg",
    }
    if ct not in allowed:
        raise HTTPException(status_code=400, detail="logo_type_unsupported")
    raw = await file.read()
    if not raw or len(raw) > 3 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="logo_too_large")
    ext = allowed[ct]
    path = f"agency-logos/{user['id']}/{uuid4().hex}.{ext}"
    try:
        put_object(path, raw, ct)
    except ObjStoreError as e:
        logger.error("logo upload failed: %s", e)
        raise HTTPException(status_code=500, detail="logo_upload_failed") from e
    url = f"/api/media/{path}"
    return {"ok": True, "url": url, "content_type": ct, "size": len(raw)}


# -------------------- MEMBERS LIST --------------------

@router.get("/me/members")
async def list_members(user: dict = Depends(get_current_user)):
    """List all users belonging to the current user's agency."""
    db = Database.get()
    agency_id = require_agency(user)

    cursor = db.users.find(
        {"agency_ids": agency_id},
        {"_id": 0, "password_hash": 0},
    )
    members = await cursor.to_list(length=200)
    return members


@router.delete("/me/members/{member_id}")
async def remove_member(
    member_id: str,
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Unlink a member from the current agency (does NOT delete the user).

    Guards (A-007):
    - no self-remove
    - no remove of agency owner_id
    - no remove of the last agency_admin in the agency
    """
    db = Database.get()
    agency_id = require_agency(user)

    if member_id == user.get("id"):
        raise HTTPException(403, detail="self_remove_forbidden")

    agency = await db.agencies.find_one({"id": agency_id}, {"_id": 0, "owner_id": 1})
    if agency and agency.get("owner_id") and agency["owner_id"] == member_id:
        raise HTTPException(400, detail="owner_remove_forbidden")

    target = await db.users.find_one(
        {"id": member_id, "agency_ids": agency_id},
        {"_id": 0, "id": 1, "role": 1, "email": 1},
    )
    if not target:
        raise HTTPException(404, detail="member_not_found")

    if target.get("role") in ("agency_admin", "super_admin", "group_admin"):
        admin_count = await db.users.count_documents({
            "agency_ids": agency_id,
            "role": {"$in": ["agency_admin", "super_admin", "group_admin"]},
        })
        if admin_count <= 1:
            raise HTTPException(400, detail="last_owner_forbidden")

    res = await db.users.update_one(
        {"id": member_id},
        {
            "$pull": {"agency_ids": agency_id},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )
    if res.modified_count == 0 and res.matched_count == 0:
        raise HTTPException(404, detail="member_not_found")

    # Clear active_agency if it pointed at this agency
    await db.users.update_one(
        {"id": member_id, "active_agency_id": agency_id},
        {"$set": {"active_agency_id": None}},
    )

    return {"ok": True, "removed_user_id": member_id, "agency_id": agency_id}
