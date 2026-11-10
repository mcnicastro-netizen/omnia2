"""OMNIA — ImmoWeb / Agencies routes (create, read, update, members)."""
import logging
from typing import List, Optional
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, Depends, UploadFile, status
from fastapi.responses import Response
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
from shared.storage import put_object, get_object, ObjStoreError

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

    preferred = (payload.preferred_plan_tier or user.get("signup_preferred_plan") or "").strip().lower()
    if preferred not in ("starter", "pro", "agency"):
        preferred = None

    contact_pec = None
    if payload.contact is not None:
        if isinstance(payload.contact, dict):
            contact_pec = payload.contact.get("pec")
        else:
            contact_pec = getattr(payload.contact, "pec", None)
    vat = getattr(payload.fiscal, "vat_number", None) if payload.fiscal else None

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
        preferred_plan_tier=preferred,
        kyc={
            "status": "incomplete",
            "notes": "",
            "verified_at": None,
            "verified_by": None,
            "documents": [],
            "checklist": {
                "visura_camerale": False,
                "id_titolare": False,
                "pec": bool(contact_pec),
                "piva_ok": bool(vat),
            },
        },
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

    # Email «richiesta ricevuta» (non è lo sblocco CRM)
    try:
        from shared.email.client import send_email
        from shared.public_base import get_public_base_url

        frontend = get_public_base_url()
        lang = (user.get("lang") or "it")[:2]
        await send_email(
            to=user.get("email"),
            template="agency_pending",
            lang=lang if lang in ("it", "en", "es") else "it",
            variables={
                "name": user.get("name") or "Colleague",
                "agency_name": payload.display_name,
                "plan_tier": (preferred or "pro").upper(),
                "login_url": f"{frontend}/{lang}/login",
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("agency_pending email failed: %s", exc)

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


# -------------------- ONBOARDING LOGO (pre-agency) --------------------

_ALLOWED_LOGO_MIME = {"image/png", "image/jpeg", "image/webp", "image/svg+xml"}
_MAX_LOGO_BYTES = 2 * 1024 * 1024
_KYC_DOC_TYPES = {"visura_camerale", "documento_identita", "altro"}
_ALLOWED_KYC_MIME = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/webp",
}
_MAX_KYC_BYTES = 8 * 1024 * 1024


@router.post("/onboarding/logo")
async def upload_onboarding_logo(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """Upload marchio/logo prima della create agency (path privato user)."""
    ct = (file.content_type or "").lower()
    if ct not in _ALLOWED_LOGO_MIME:
        raise HTTPException(status_code=415, detail="unsupported_media_type")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty_file")
    if len(data) > _MAX_LOGO_BYTES:
        raise HTTPException(status_code=413, detail="file_too_large")
    ext = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/svg+xml": "svg",
    }[ct]
    uid = user["id"]
    storage_path = f"omnia/private/{uid}/branding/logo-{uuid4().hex[:10]}.{ext}"
    try:
        put_object(storage_path, data, ct)
    except ObjStoreError as e:
        logger.exception("onboarding logo upload failed user=%s", uid)
        raise HTTPException(status_code=502, detail="storage_upload_failed") from e
    return {"ok": True, "url": f"/api/media/{storage_path}", "size_bytes": len(data)}


# -------------------- KYC (owner upload during waiting) --------------------

def _kyc_doc_entry(*, doc_type: str, filename: str, storage_path: str, user: dict) -> dict:
    return {
        "id": str(uuid4()),
        "doc_type": doc_type,
        "filename": filename[:180],
        "storage_path": storage_path,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "uploaded_by": user.get("id"),
        "uploaded_by_email": user.get("email"),
    }


def _refresh_kyc_checklist(kyc: dict) -> dict:
    docs = kyc.get("documents") or []
    types = {d.get("doc_type") for d in docs}
    cl = dict(kyc.get("checklist") or {})
    cl["visura_camerale"] = "visura_camerale" in types
    cl["id_titolare"] = "documento_identita" in types
    kyc["checklist"] = cl
    if kyc.get("status") in (None, "incomplete") and cl.get("visura_camerale") and cl.get("id_titolare"):
        kyc["status"] = "submitted"
    return kyc


@router.post("/me/kyc/documents")
async def upload_my_kyc_document(
    file: UploadFile = File(...),
    doc_type: str = Form("altro"),
    user: dict = Depends(require_roles("agency_admin", "super_admin")),
):
    """Owner carica PDF/visura per identificazione clientela (pre-attivazione)."""
    dt = (doc_type or "altro").strip().lower()
    if dt not in _KYC_DOC_TYPES:
        raise HTTPException(400, detail="invalid_doc_type")
    ct = (file.content_type or "").lower()
    if ct not in _ALLOWED_KYC_MIME:
        raise HTTPException(415, detail="unsupported_media_type")
    data = await file.read()
    if not data or len(data) > _MAX_KYC_BYTES:
        raise HTTPException(413 if data else 400, detail="file_invalid")

    db = Database.get()
    agency_id = require_agency(user)
    agency = await db.agencies.find_one({"id": agency_id}, {"_id": 0})
    if not agency:
        raise HTTPException(404, detail="agency_not_found")
    if agency.get("owner_id") != user["id"] and user.get("role") != "super_admin":
        raise HTTPException(403, detail="not_owner")

    ext = {"application/pdf": "pdf", "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[ct]
    storage_path = f"omnia/ops-kyc/{agency_id}/{dt}-{uuid4().hex[:10]}.{ext}"
    try:
        put_object(storage_path, data, ct)
    except ObjStoreError as e:
        raise HTTPException(502, detail="storage_upload_failed") from e

    kyc = dict(agency.get("kyc") or {"status": "incomplete", "documents": [], "checklist": {}})
    docs = list(kyc.get("documents") or [])
    entry = _kyc_doc_entry(
        doc_type=dt,
        filename=file.filename or f"{dt}.{ext}",
        storage_path=storage_path,
        user=user,
    )
    docs.append(entry)
    kyc["documents"] = docs
    kyc = _refresh_kyc_checklist(kyc)
    await db.agencies.update_one(
        {"id": agency_id},
        {"$set": {"kyc": kyc, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return {"ok": True, "document": entry, "kyc": kyc}
