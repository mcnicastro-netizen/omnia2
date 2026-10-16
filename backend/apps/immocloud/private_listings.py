"""OMNIA — ImmobilCloud B2C Private Listings (M3.S5 v2).

Lets B2C users (role='client') publish their own property ad without going
through an agency. Properties created here have:
  - agency_id = "_private_listings"     # sentinel (no real agency)
  - is_private_listing = True
  - owner_user_id = current user id
<<<<<<< HEAD
  - status = "draft" until approved live
  - moderation_status = "none" until user submits → then "pending"
=======
  - status = "draft" until user submits
  - moderation_status = "pending"       # admin must approve
    (sandbox: OMNIA_B2C_SANDBOX_AUTO_APPROVE=true → approve on submit)
>>>>>>> b6d2079 (feat(b2c): sandbox Founder — auto-approve annunci privati)

Endpoints (B2C auth required):
  POST   /api/cloud/me/properties        — create new private ad
  GET    /api/cloud/me/properties        — list my own ads (any status)
  GET    /api/cloud/me/properties/{pid}  — detail of my own ad
  PATCH  /api/cloud/me/properties/{pid}  — edit my own ad (resets to pending on substantive change)
  POST   /api/cloud/me/properties/{pid}/submit — submit for moderation
  DELETE /api/cloud/me/properties/{pid}  — delete
  POST   /api/cloud/me/properties/media/upload-tmp — upload photo or floor plan (max 30 photos)

Free tier: 2 annunci (bozza/attivo) senza scadenza. Dal 3° serve slot Stripe
(b2c_listing_extra_90 / b2c_listing_premium) — credito consumato alla create.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database
from shared.models.property import PropertyCreate, PropertyUpdate, PrivateContactPublic
from shared.storage import put_object, ObjStoreError
from apps.immocloud.geocoding import schedule_geocode
from apps.billing.b2c_listing_publish import (
    BASE_PHOTO_LIMIT,
    FREE_TIER_MAX_ACTIVE,
    HARD_PHOTO_CAP,
    consume_listing_slot_credit,
    count_slot_usage,
    count_unused_slot_credits,
    listing_requires_premium_sku,
    photo_limit_for,
    slot_fields_from_purchase,
)

logger = logging.getLogger("omnia.private_listings")
router = APIRouter(prefix="/me/properties", tags=["cloud-private-listings"])

PRIVATE_AGENCY_SENTINEL = "_private_listings"
B2C_MAX_PHOTOS = HARD_PHOTO_CAP
_ALLOWED_PHOTO_MIME = {"image/jpeg", "image/png", "image/webp"}
_MAX_PHOTO_BYTES = 8 * 1024 * 1024  # 8MB


def _default_contact_public(user: dict, override: dict | None = None) -> dict:
    """Build contact_public for a private listing from user profile + optional payload."""
    name = (user.get("name") or "").strip()
    display = name.split()[0] if name else "Privato"
    base = {
        "display_name": display,
        "show_email": True,
        "show_phone": bool(user.get("phone")),
        "show_whatsapp": False,
        "phone": user.get("phone"),
        "whatsapp": None,
    }
    if override:
        # Accept dict or PrivateContactPublic
        if hasattr(override, "model_dump"):
            ov = override.model_dump(exclude_unset=True)
        else:
            ov = {k: v for k, v in dict(override).items() if v is not None or k.startswith("show_")}
        for k, v in ov.items():
            if k in base or k in ("display_name", "show_email", "show_phone", "show_whatsapp", "phone", "whatsapp"):
                base[k] = v
    # Normalize empty strings → None
    for k in ("phone", "whatsapp", "display_name"):
        if isinstance(base.get(k), str) and not base[k].strip():
            base[k] = None if k != "display_name" else display
    return PrivateContactPublic(**base).model_dump()


def _assert_contact_reachable(contact: dict, owner_email: str | None) -> None:
    """At least one usable channel: form (account email) and/or public phone/WA."""
    has_form = bool(owner_email)
    has_phone = bool(contact.get("show_phone") and (contact.get("phone") or "").strip())
    has_wa = bool(contact.get("show_whatsapp") and (contact.get("whatsapp") or "").strip())
    has_public_email = bool(contact.get("show_email") and owner_email)
    if not (has_form or has_phone or has_wa or has_public_email):
        raise HTTPException(status_code=400, detail="contact_channel_required")
    if contact.get("show_phone") and not (contact.get("phone") or "").strip():
        raise HTTPException(status_code=400, detail="contact_phone_required")
    if contact.get("show_whatsapp") and not (contact.get("whatsapp") or "").strip():
        raise HTTPException(status_code=400, detail="contact_whatsapp_required")


async def _ensure_b2c(user: dict) -> None:
    if user.get("account_type") != "b2c":
        raise HTTPException(status_code=403, detail="b2c_account_required")
    if user.get("role") != "client":
        raise HTTPException(status_code=403, detail="b2c_account_required")


def _strip(doc: dict) -> dict:
    doc.pop("_id", None)
    return doc


def _compose_street(address: str | None, street_number: str | None) -> str | None:
    """Via + civico (o 'snc') for geocoding / display helpers."""
    street = (address or "").strip()
    num = (street_number or "").strip()
    if not street and not num:
        return None
    if not num:
        return street or None
    if not street:
        return num
    return f"{street} {num}"


def _validate_photos_limit(photos, *, limit: int = BASE_PHOTO_LIMIT) -> None:
    if photos is not None and len(photos) > limit:
        raise HTTPException(status_code=400, detail="photos_limit_exceeded")


@router.post("/media/upload-tmp")
async def upload_private_media_tmp(
    file: UploadFile = File(...),
    kind: Literal["photo", "floor_plan"] = Form("photo"),
    user: dict = Depends(get_current_user),
):
    """Upload a photo or floor-plan binary before/while editing a private listing.

    Stores under the private-listings namespace and returns the media URL to
    embed in `photos` or `floor_plan_url` on save. Max 30 photos per listing
    is enforced on create/patch; this endpoint only validates file type/size.
    """
    await _ensure_b2c(user)
    ct = (file.content_type or "").lower()
    if ct not in _ALLOWED_PHOTO_MIME:
        raise HTTPException(status_code=415, detail="unsupported_media_type")
    data = await file.read()
    if len(data) > _MAX_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="file_too_large")
    if not data:
        raise HTTPException(status_code=400, detail="empty_file")

    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}[ct]
    media_id = str(uuid4())
    folder = "floor_plans" if kind == "floor_plan" else "photos"
    storage_path = f"omnia/private/{user['id']}/{folder}/{media_id}.{ext}"
    try:
        put_object(storage_path, data, ct)
    except ObjStoreError as e:
        logger.exception("b2c media upload failed user=%s kind=%s: %s", user["id"], kind, e)
        raise HTTPException(status_code=502, detail="storage_upload_failed") from e
    return {"id": media_id, "url": f"/api/media/{storage_path}", "kind": kind}


@router.post("", status_code=201)
async def create_private_listing(
    payload: PropertyCreate,
    user: dict = Depends(get_current_user),
):
    await _ensure_b2c(user)
    db = Database.get()

    # Free tier: 2 senza scadenza. Dal 3° consuma credito Stripe (slot).
    active_count = await count_slot_usage(user["id"])
    paid_slot_fields = None
    if active_count >= FREE_TIER_MAX_ACTIVE:
        credit = await consume_listing_slot_credit(user["id"])
        if not credit:
            credits_left = await count_unused_slot_credits(user["id"])
            raise HTTPException(status_code=409, detail={
                "code": "free_tier_listing_limit_reached",
                "free_max": FREE_TIER_MAX_ACTIVE,
                "active_count": active_count,
                "unused_credits": credits_left,
                "message": (
                    f"Hai raggiunto i {FREE_TIER_MAX_ACTIVE} annunci gratuiti. "
                    "Acquista uno slot (dal 3°) per continuare."
                ),
                "products": ["b2c_listing_extra_90", "b2c_listing_premium"],
            })
        # Premium property must use premium SKU
        draft_probe = payload.model_dump()
        if listing_requires_premium_sku(draft_probe) and credit.get("product_key") != "b2c_listing_premium":
            # restore credit — wrong SKU
            await db.b2c_purchases.update_one(
                {"id": credit.get("id")},
                {"$set": {"slot_consumed": False}, "$unset": {"slot_consumed_at": ""}},
            )
            raise HTTPException(status_code=409, detail={
                "code": "premium_listing_sku_required",
                "message": "Per immobili >€1M o affitti >€2.500/mese serve lo slot premium.",
                "products": ["b2c_listing_premium"],
            })
        paid_slot_fields = slot_fields_from_purchase(credit)

    _validate_photos_limit(payload.photos, limit=BASE_PHOTO_LIMIT)

    now = datetime.now(timezone.utc).isoformat()
    data = payload.model_dump()
    contact_override = data.pop("contact_public", None)
    contact_public = _default_contact_public(user, contact_override)
    # Soft-validate on create (hard on submit)
    owner_email = user.get("email")
    if contact_public.get("show_phone") and not (contact_public.get("phone") or "").strip():
        contact_public["show_phone"] = False
    if contact_public.get("show_whatsapp") and not (contact_public.get("whatsapp") or "").strip():
        contact_public["show_whatsapp"] = False

    data.update({
        "id": str(uuid4()),
        "agency_id": PRIVATE_AGENCY_SENTINEL,
        "is_private_listing": True,
        "owner_user_id": user["id"],
        "status": "draft",
        # MLS / matching CRM = B2B only (PRICING_B2C §3)
        "mls_shared": False,
        "visibility": "private",
        "moderation_status": "none",  # bozza locale — pending solo dopo /submit
        "moderation_notes": None,
        "moderation_reviewed_at": None,
        "moderation_reviewed_by": None,
        "view_count": 0,
        "lead_count": 0,
        "photo_pack_extra": 0,
        "created_at": now,
        "updated_at": now,
        "contact_public": contact_public,
    })
    if paid_slot_fields:
        data.update(paid_slot_fields)
    # Owner contact pre-populated from user profile (private/internal field)
    data["owner"] = {
        "name": user.get("name"),
        "phone": contact_public.get("phone") or user.get("phone"),
        "email": owner_email,
        "notes": None,
    }
    await db.properties.insert_one(data)

    if not data.get("lat") and not data.get("lng"):
        schedule_geocode(db, data["id"], {
            "address": _compose_street(data.get("address"), data.get("street_number")),
            "city": data.get("city"),
            "province": data.get("province"),
            "postal_code": data.get("postal_code"),
        })

    logger.info("private listing created: id=%s user=%s", data["id"], user["id"])
    return _strip(data)


@router.get("")
async def list_my_private_listings(user: dict = Depends(get_current_user)):
    await _ensure_b2c(user)
    from shared.db.trash import with_not_trashed
    db = Database.get()
    cursor = db.properties.find(
        with_not_trashed({"owner_user_id": user["id"], "is_private_listing": True}),
        {"_id": 0, "owner": 0},
    ).sort("created_at", -1)
    items = await cursor.to_list(length=50)
    return {"items": items, "total": len(items)}


@router.get("/{pid}")
async def get_my_private_listing(pid: str, user: dict = Depends(get_current_user)):
    await _ensure_b2c(user)
    from shared.db.trash import with_not_trashed
    db = Database.get()
    p = await db.properties.find_one(
        with_not_trashed({
            "id": pid,
            "owner_user_id": user["id"],
            "is_private_listing": True,
        }),
        {"_id": 0},
    )
    if not p:
        raise HTTPException(status_code=404, detail="listing_not_found")
    return p


@router.get("/{pid}/stats")
async def get_my_private_listing_stats(
    pid: str,
    days: int = 30,
    user: dict = Depends(get_current_user),
):
    """D-093 / A-029 — views + contacts for the private seller dashboard.

    `days` clamped 1–90. Series starts filling from first tracked day after ship;
    lifetime totals come from `view_count` / `lead_count` on the property.
    """
    await _ensure_b2c(user)
    db = Database.get()
    p = await db.properties.find_one(
        {"id": pid, "owner_user_id": user["id"], "is_private_listing": True},
        {"_id": 0, "id": 1, "view_count": 1, "lead_count": 1},
    )
    if not p:
        raise HTTPException(status_code=404, detail="listing_not_found")
    from apps.immocloud.listing_stats import get_listing_stats
    return await get_listing_stats(
        db,
        pid,
        days=days,
        lifetime_views=int(p.get("view_count") or 0),
        lifetime_leads=int(p.get("lead_count") or 0),
    )


@router.patch("/{pid}")
async def update_my_private_listing(
    pid: str, payload: PropertyUpdate, user: dict = Depends(get_current_user),
):
    await _ensure_b2c(user)
    db = Database.get()
    existing = await db.properties.find_one(
        {"id": pid, "owner_user_id": user["id"], "is_private_listing": True},
        {"_id": 0},
    )
    if not existing:
        raise HTTPException(status_code=404, detail="listing_not_found")

    update_doc = payload.model_dump(exclude_unset=True)
    if "status" in update_doc:
        # Users can only set status to draft (we expose /submit for active)
        update_doc.pop("status", None)
    _validate_photos_limit(
        update_doc.get("photos"),
        limit=photo_limit_for(existing),
    )

    if "contact_public" in update_doc:
        merged = _default_contact_public(
            user,
            {**(existing.get("contact_public") or {}), **(update_doc.get("contact_public") or {})},
        )
        update_doc["contact_public"] = merged
        # Keep internal owner phone in sync when public phone changes
        owner = dict(existing.get("owner") or {})
        if merged.get("phone"):
            owner["phone"] = merged["phone"]
        if user.get("email"):
            owner["email"] = user.get("email")
        update_doc["owner"] = owner

    update_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
    # If previously rejected/approved and substantive edit → back to pending
    substantive = any(k in update_doc for k in
                      ("title", "description", "price", "rent_monthly", "address",
                       "street_number", "city", "zone", "surface_sqm", "rooms",
                       "bedrooms", "bathrooms", "floor", "total_floors", "year_built",
                       "condition", "features", "energy", "condo_fees", "furnished",
                       "photos", "floor_plan_url", "contact_public"))
    if substantive and existing.get("moderation_status") in ("approved", "rejected"):
        update_doc["moderation_status"] = "pending"
        update_doc["status"] = "draft"

    if "price" in update_doc or "rent_monthly" in update_doc:
        try:
            from apps.immocloud.price_watch import record_price_change
            await record_price_change(
                db,
                property_id=pid,
                existing=existing,
                new_price=update_doc.get("price", existing.get("price")),
                new_rent=update_doc.get("rent_monthly", existing.get("rent_monthly")),
                touched_price="price" in update_doc,
                touched_rent="rent_monthly" in update_doc,
            )
        except Exception:
            pass

    await db.properties.update_one({"id": pid}, {"$set": update_doc})

    if any(k in update_doc for k in ("address", "street_number", "city", "province", "postal_code")):
        full = await db.properties.find_one({"id": pid}, {"_id": 0})
        schedule_geocode(db, pid, {
            "address": _compose_street(full.get("address"), full.get("street_number")),
            "city": full.get("city"),
            "province": full.get("province"),
            "postal_code": full.get("postal_code"),
        })

    updated = await db.properties.find_one({"id": pid}, {"_id": 0})
    return updated


def _sandbox_auto_approve_enabled() -> bool:
    """Cloud/local sandbox: skip human moderation so Founder can dogfood B2C end-to-end."""
    return (os.environ.get("OMNIA_B2C_SANDBOX_AUTO_APPROVE") or "").strip().lower() in (
        "1", "true", "yes", "on",
    )


@router.post("/{pid}/submit")
async def submit_for_moderation(pid: str, user: dict = Depends(get_current_user)):
    """Move a draft listing into the moderation queue. Status stays 'draft'
    until admin approves (then becomes 'active'), or 'rejected'.

    If OMNIA_B2C_SANDBOX_AUTO_APPROVE is on, publish immediately (sandbox only)."""
    await _ensure_b2c(user)
    db = Database.get()
    p = await db.properties.find_one(
        {"id": pid, "owner_user_id": user["id"], "is_private_listing": True},
        {"_id": 0, "id": 1, "title": 1, "city": 1, "price": 1, "rent_monthly": 1,
         "moderation_status": 1, "status": 1, "contact_public": 1, "owner": 1},
    )
    if not p:
        raise HTTPException(status_code=404, detail="listing_not_found")
    if p.get("moderation_status") == "approved" and p.get("status") == "active":
        raise HTTPException(status_code=409, detail="already_approved_and_active")

    # Minimum viable ad: title, city, AT LEAST one of price/rent_monthly
    if not (p.get("title") and p.get("city") and (p.get("price") or p.get("rent_monthly"))):
        raise HTTPException(status_code=400, detail="missing_required_fields")

    contact = p.get("contact_public") or _default_contact_public(user)
    owner_email = (p.get("owner") or {}).get("email") or user.get("email")
    _assert_contact_reachable(contact, owner_email)
    # Persist defaults if listing was created before contact_public existed
    if not p.get("contact_public"):
        await db.properties.update_one({"id": pid}, {"$set": {"contact_public": contact}})

    now = datetime.now(timezone.utc).isoformat()
    if _sandbox_auto_approve_enabled():
        await db.properties.update_one(
            {"id": pid},
            {"$set": {
                "moderation_status": "approved",
                "status": "active",
                "visibility": "public",
                "moderation_notes": "sandbox_auto_approve",
                "moderation_reviewed_at": now,
                "moderation_reviewed_by": "sandbox_auto",
                "updated_at": now,
            }},
        )
        logger.info("private listing sandbox auto-approved: id=%s user=%s", pid, user["id"])
        try:
            from apps.immocloud.alert_fanout import fanout_listing_event
            await fanout_listing_event(pid, event="new")
        except Exception as e:
            logger.warning("fanout after sandbox auto-approve failed: %s", e)
        return {
            "ok": True,
            "moderation_status": "approved",
            "status": "active",
            "sandbox_auto_approve": True,
        }

    await db.properties.update_one(
        {"id": pid},
        {"$set": {
            "moderation_status": "pending",
            "moderation_notes": None,
            "updated_at": now,
        }},
    )
    logger.info("private listing submitted: id=%s user=%s", pid, user["id"])
    return {"ok": True, "moderation_status": "pending"}


class B2CStagingStartBody(BaseModel):
    """Kick (or re-kick) B2C staging fulfill after Stripe return (P-011)."""
    session_id: str = Field(..., min_length=8, max_length=200)


class B2CStagingPreviewBody(BaseModel):
    """Free anteprima before payment — user chooses photo + mode."""
    photo_id: str | None = Field(default=None, max_length=80)
    mode: Literal["standard", "empty", "reverse"] = "standard"
    style: str = Field(default="modern", max_length=40)
    room_type: str = Field(default="living", max_length=40)
    variant_mode: Literal["same_style", "multi_style"] = "same_style"
    num_variants: int = Field(default=1, ge=1, le=4)
    styles: list[str] | None = Field(default=None, max_length=4)


@router.post("/{pid}/staging/preview")
async def start_b2c_staging_preview(
    pid: str,
    body: B2CStagingPreviewBody,
    user: dict = Depends(get_current_user),
):
    """Generate a free staging/empty preview for a chosen photo (max 3/day)."""
    await _ensure_b2c(user)
    db = Database.get()
    listing = await db.properties.find_one(
        {"id": pid, "owner_user_id": user["id"], "is_private_listing": True},
        {"_id": 0, "id": 1, "photos": 1},
    )
    if not listing:
        raise HTTPException(status_code=404, detail="listing_not_found")
    if not (listing.get("photos") or []):
        raise HTTPException(status_code=400, detail="listing_has_no_photos")

    from apps.immoweb.virtual_staging import start_b2c_preview_job, _job_to_out

    job = await start_b2c_preview_job(
        user_id=user["id"],
        listing_id=pid,
        photo_id=body.photo_id,
        mode=body.mode,
        style=body.style,
        room_type=body.room_type,
        variant_mode=body.variant_mode,
        num_variants=body.num_variants,
        styles=body.styles,
    )
    out = _job_to_out(job)
    return {
        "ok": True,
        "job": out.model_dump(),
        "listing_id": pid,
        "photo_id": job.get("source_photo_id"),
        "photo_index": job.get("source_photo_index"),
        "mode": job.get("mode"),
    }


@router.post("/{pid}/staging")
async def start_b2c_staging(
    pid: str,
    body: B2CStagingStartBody,
    user: dict = Depends(get_current_user),
):
    """Consume paid `b2c_staging_render` and start AI job for this listing.

    Idempotent when webhook already fulfilled the same `session_id`.
    """
    await _ensure_b2c(user)
    db = Database.get()
    listing = await db.properties.find_one(
        {"id": pid, "owner_user_id": user["id"], "is_private_listing": True},
        {"_id": 0, "id": 1, "photos": 1},
    )
    if not listing:
        raise HTTPException(status_code=404, detail="listing_not_found")
    if not (listing.get("photos") or []):
        raise HTTPException(status_code=400, detail="listing_has_no_photos")

    purchase = await db.b2c_purchases.find_one({
        "stripe_session_id": body.session_id,
        "user_id": user["id"],
        "product_key": "b2c_staging_render",
    })
    if not purchase:
        raise HTTPException(status_code=404, detail="purchase_not_found")
    if purchase.get("listing_id") and purchase["listing_id"] != pid:
        raise HTTPException(status_code=400, detail="listing_mismatch")
    if purchase.get("status") != "paid":
        raise HTTPException(status_code=402, detail={
            "error": "staging_payment_required",
            "message": "Pagamento staging non ancora confermato.",
        })

    from apps.immoweb.virtual_staging import fulfill_paid_staging_render, _job_to_out

    result = await fulfill_paid_staging_render(body.session_id)
    job = (result or {}).get("job") if isinstance(result, dict) else None
    if not job:
        # Re-read if fulfill returned bare purchase
        purchase = await db.b2c_purchases.find_one(
            {"stripe_session_id": body.session_id}, {"_id": 0},
        ) or purchase
        if purchase.get("fulfillment_error"):
            raise HTTPException(status_code=400, detail=purchase["fulfillment_error"])
        if purchase.get("job_id"):
            job = await db.virtual_staging_jobs.find_one(
                {"id": purchase["job_id"], "user_id": user["id"]},
            )
    if not job:
        raise HTTPException(status_code=409, detail="staging_fulfill_failed")

    # Normalize job dict (may include Mongo _id)
    if job.get("_id") is not None:
        job = {k: v for k, v in job.items() if k != "_id"}
    out = _job_to_out(job)
    return {
        "ok": True,
        "job": out.model_dump(),
        "session_id": body.session_id,
        "listing_id": pid,
        "photo_id": job.get("source_photo_id"),
        "photo_index": job.get("source_photo_index"),
        "mode": job.get("mode"),
        "saved_photo_id": job.get("saved_photo_id"),
    }


@router.get("/{pid}/staging/{job_id}")
async def get_b2c_staging_job(
    pid: str,
    job_id: str,
    user: dict = Depends(get_current_user),
):
    """Poll B2C staging job (paid or free preview) for caller's listing."""
    await _ensure_b2c(user)
    db = Database.get()
    listing = await db.properties.find_one(
        {"id": pid, "owner_user_id": user["id"], "is_private_listing": True},
        {"_id": 1},
    )
    if not listing:
        raise HTTPException(status_code=404, detail="listing_not_found")
    from apps.immoweb.virtual_staging import _job_to_out

    job = await db.virtual_staging_jobs.find_one({
        "id": job_id,
        "user_id": user["id"],
        "property_id": pid,
        "payment_rail": {"$in": ["b2c_stripe", "b2c_preview"]},
    })
    if not job:
        raise HTTPException(status_code=404, detail="job_not_found")
    out = _job_to_out(job).model_dump()
    out["source_photo_id"] = job.get("source_photo_id")
    out["source_photo_index"] = job.get("source_photo_index")
    out["payment_rail"] = job.get("payment_rail")
    out["saved_photo_id"] = job.get("saved_photo_id")
    return out


@router.delete("/{pid}", status_code=204)
async def delete_my_private_listing(pid: str, user: dict = Depends(get_current_user)):
    """P-048 — soft-delete (cestino) come CRM, non hard delete."""
    await _ensure_b2c(user)
    from shared.db.trash import soft_delete_fields, with_not_trashed
    db = Database.get()
    r = await db.properties.update_one(
        with_not_trashed({
            "id": pid,
            "owner_user_id": user["id"],
            "is_private_listing": True,
        }),
        {"$set": {
            **soft_delete_fields(user["id"]),
            "status": "withdrawn",
            "visibility": "private",
            "is_listed_on_immobilcloud": False,
        }},
    )
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="listing_not_found")
    return None
