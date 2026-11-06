"""OMNIA — ImmobilCloud B2C Private Listings (M3.S5 v2).

Lets B2C users (role='client') publish their own property ad without going
through an agency. Properties created here have:
  - agency_id = "_private_listings"     # sentinel (no real agency)
  - is_private_listing = True
  - owner_user_id = current user id
  - status = "draft" until approved live
  - moderation_status = "none" until user submits → then "pending"
    (sandbox: OMNIA_B2C_SANDBOX_AUTO_APPROVE=true → approve on submit)

Endpoints (B2C auth required):
  POST   /api/cloud/me/properties        — create new private ad
  GET    /api/cloud/me/properties        — list my own ads (any status)
  GET    /api/cloud/me/properties/{pid}  — detail of my own ad
  PATCH  /api/cloud/me/properties/{pid}  — edit my own ad (resets to pending on substantive change)
  POST   /api/cloud/me/properties/{pid}/submit — submit for moderation
  DELETE /api/cloud/me/properties/{pid}  — delete
  GET/DELETE /api/cloud/me/properties/{pid}/video — micro-tour status / remove
  POST   /api/cloud/me/properties/{pid}/kenburns — genera micro-tour
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
        "show_whatsapp": bool(user.get("whatsapp")),
        "phone": user.get("phone"),
        "whatsapp": user.get("whatsapp"),
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

    from shared.ids import ensure_client_code, ensure_unique_code

    listing_code = (data.get("reference_code") or "").strip() or await ensure_unique_code(
        db, collection="properties", field="reference_code", kind="listing",
    )
    client_code = await ensure_client_code(db, user["id"])

    data.update({
        "id": str(uuid4()),
        "agency_id": PRIVATE_AGENCY_SENTINEL,
        "is_private_listing": True,
        "owner_user_id": user["id"],
        "status": "draft",
        # MLS / matching CRM = B2B only (PRICING_B2C §3)
        "mls_shared": False,
        "visibility": "private",
        "moderation_status": "none",  # bozza locale — live dopo /submit (auto-publish D-137)
        "moderation_notes": None,
        "moderation_reviewed_at": None,
        "moderation_reviewed_by": None,
        "reference_code": listing_code,
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
        "client_code": client_code,
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
    from shared.ids import ensure_client_code, ensure_listing_code
    db = Database.get()
    cursor = db.properties.find(
        with_not_trashed({"owner_user_id": user["id"], "is_private_listing": True}),
        {"_id": 0, "owner": 0},
    ).sort("created_at", -1)
    items = await cursor.to_list(length=50)
    client_code = None
    try:
        client_code = await ensure_client_code(db, user["id"])
    except Exception:
        logger.exception("ensure client_code on list failed user=%s", user.get("id"))
    for it in items:
        try:
            code = await ensure_listing_code(db, it.get("id"))
            if code:
                it["reference_code"] = code
        except Exception:
            logger.exception("ensure listing_code on list failed id=%s", it.get("id"))
        if client_code:
            it["client_code"] = client_code
    return {"items": items, "total": len(items), "client_code": client_code}


@router.get("/{pid}")
async def get_my_private_listing(pid: str, user: dict = Depends(get_current_user)):
    await _ensure_b2c(user)
    from shared.db.trash import with_not_trashed
    from shared.ids import ensure_client_code, ensure_listing_code
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
    # Repair wiped/legacy data: staging photos so cover edit does not lose AI renders
    try:
        from apps.immoweb.virtual_staging import _auto_save_b2c_variant
        jobs = await db.virtual_staging_jobs.find(
            {
                "user_id": user["id"],
                "property_id": pid,
                "payment_rail": "b2c_stripe",
                "status": "done",
            },
            {"_id": 0, "id": 1},
        ).sort("completed_at", -1).to_list(length=3)
        repaired = False
        for j in jobs:
            try:
                await _auto_save_b2c_variant(j["id"], db)
                repaired = True
            except Exception:
                logger.exception("b2c staging ensure-on-listing failed job=%s", j.get("id"))
        if repaired:
            p = await db.properties.find_one(
                with_not_trashed({
                    "id": pid,
                    "owner_user_id": user["id"],
                    "is_private_listing": True,
                }),
                {"_id": 0},
            ) or p
    except Exception:
        logger.exception("b2c staging ensure-on-listing wrapper failed pid=%s", pid)
    try:
        listing_code = await ensure_listing_code(db, pid)
        client_code = await ensure_client_code(db, user["id"])
        if listing_code:
            p["reference_code"] = listing_code
        if client_code:
            p["client_code"] = client_code
    except Exception:
        logger.exception("ensure codes on listing get failed pid=%s", pid)
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
    # Substantive edit: re-run safety gate (Idealista-like reputation protection)
    substantive = any(k in update_doc for k in
                      ("title", "description", "price", "rent_monthly", "address",
                       "street_number", "city", "zone", "surface_sqm", "rooms",
                       "bedrooms", "bathrooms", "floor", "total_floors", "year_built",
                       "condition", "features", "energy", "condo_fees", "furnished",
                       "photos", "floor_plan_url", "contact_public"))
    if substantive and existing.get("moderation_status") in ("approved", "rejected", "pending"):
        try:
            from apps.immocloud.listing_safety_gate import (
                VERDICT_ACCEPT,
                VERDICT_REJECT,
                evaluate_listing_safety,
                notify_founder_safety_flag,
                safety_gate_enabled,
            )
            merged = {**existing, **update_doc}
            if safety_gate_enabled():
                report = await evaluate_listing_safety(merged)
                update_doc["safety_gate"] = report.to_dict()
                if report.verdict == VERDICT_ACCEPT and existing.get("moderation_status") == "approved":
                    # Stay live if previously approved and still clean
                    update_doc["moderation_status"] = "approved"
                    update_doc["status"] = "active"
                    update_doc["visibility"] = "public"
                    update_doc["moderation_notes"] = "safety_gate_accept_on_edit"
                elif report.verdict == VERDICT_REJECT:
                    update_doc["moderation_status"] = "rejected"
                    update_doc["status"] = "draft"
                    update_doc["visibility"] = "private"
                    update_doc["moderation_notes"] = (
                        f"safety_gate:REJECT · " + "; ".join(report.reasons[:5])
                    )[:500]
                    update_doc["moderation_reviewed_by"] = "safety_gate"
                    await notify_founder_safety_flag(merged, report, event="edit")
                else:
                    update_doc["moderation_status"] = "pending"
                    update_doc["status"] = "draft"
                    update_doc["visibility"] = "private"
                    update_doc["moderation_notes"] = (
                        f"safety_gate:{report.verdict} · " + "; ".join(report.reasons[:5])
                    )[:500]
                    if report.verdict != VERDICT_ACCEPT:
                        await notify_founder_safety_flag(merged, report, event="edit")
            else:
                update_doc["moderation_status"] = "pending"
                update_doc["status"] = "draft"
        except Exception:
            logger.exception("safety gate on edit failed pid=%s", pid)
            if existing.get("moderation_status") in ("approved", "rejected"):
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


def _b2c_auto_publish_enabled() -> bool:
    """D-137/D-137b: auto-publish only after safety gate ACCEPT.

    Opt-out: OMNIA_B2C_AUTO_PUBLISH=false → always human queue (gate still runs).
    """
    raw = (os.environ.get("OMNIA_B2C_AUTO_PUBLISH") or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    sandbox = (os.environ.get("OMNIA_B2C_SANDBOX_AUTO_APPROVE") or "").strip().lower()
    if sandbox in ("1", "true", "yes", "on"):
        return True
    return True


def _sandbox_auto_approve_enabled() -> bool:
    """Deprecated alias — use _b2c_auto_publish_enabled."""
    return _b2c_auto_publish_enabled()


async def _load_listing_for_safety(db, pid: str, user_id: str) -> dict:
    p = await db.properties.find_one(
        {"id": pid, "owner_user_id": user_id, "is_private_listing": True},
        {"_id": 0},
    )
    if not p:
        raise HTTPException(status_code=404, detail="listing_not_found")
    return p


class KenBurnsOwnerBody(BaseModel):
    duration_s: int = Field(default=15, ge=5, le=30)


@router.post("/{pid}/kenburns", status_code=202)
async def owner_generate_kenburns(
    pid: str,
    body: KenBurnsOwnerBody = KenBurnsOwnerBody(),
    user: dict = Depends(get_current_user),
):
    """B2C owner: genera micro-tour dalle foto dell'annuncio (anche in bozza).

    Ideale nel flusso Vendi subito dopo le immagini — non richiede annuncio già live.
    """
    await _ensure_b2c(user)
    p = await _load_listing_for_safety(Database.get(), pid, user["id"])
    photos = p.get("photos") or []
    if len(photos) < 1:
        raise HTTPException(status_code=422, detail="no_photos_available")
    from apps.immoweb.micro_tour_video import enqueue_ken_burns_for_property
    return await enqueue_ken_burns_for_property(p, duration_s=body.duration_s)


@router.get("/{pid}/video")
async def owner_listing_video(pid: str, user: dict = Depends(get_current_user)):
    """Latest Ken Burns job for this owner listing (any status except deleted).

    Hydrates ready→failed when the MP4 was lost (ephemeral /tmp after redeploy)
    so Vendi shows Rigenera instead of a black player.
    """
    await _ensure_b2c(user)
    db = Database.get()
    await _load_listing_for_safety(db, pid, user["id"])
    doc = await db.videos.find_one(
        {
            "property_id": pid,
            "mode": "ken_burns",
            "agency_id": None,
            "status": {"$ne": "deleted"},
        },
        {"_id": 0},
        sort=[("created_at", -1)],
    )
    if not doc:
        raise HTTPException(status_code=404, detail="video_not_found")
    from apps.immoweb.micro_tour_video import hydrate_ready_video
    return await hydrate_ready_video(db, doc)


@router.delete("/{pid}/video")
async def owner_delete_listing_video(pid: str, user: dict = Depends(get_current_user)):
    """Remove micro-tour from this listing (scheda pubblica smette di mostrarlo)."""
    await _ensure_b2c(user)
    db = Database.get()
    await _load_listing_for_safety(db, pid, user["id"])
    from apps.immoweb.micro_tour_video import soft_delete_owner_ken_burns
    return await soft_delete_owner_ken_burns(db, pid)


@router.post("/{pid}/submit")
async def submit_for_moderation(pid: str, user: dict = Depends(get_current_user)):
    """Submit private listing: safety gate → auto-publish OR Founder queue.

    Idealista-like: clean ads go live; offensive/scam/reputation risk → pending
    (or rejected if hard block). Founder reviews only the flagged queue.
    """
    await _ensure_b2c(user)
    db = Database.get()
    p = await _load_listing_for_safety(db, pid, user["id"])
    if p.get("moderation_status") == "approved" and p.get("status") == "active":
        raise HTTPException(status_code=409, detail="already_approved_and_active")

    # Minimum viable ad: title, city, AT LEAST one of price/rent_monthly
    if not (p.get("title") and p.get("city") and (p.get("price") or p.get("rent_monthly"))):
        raise HTTPException(status_code=400, detail="missing_required_fields")

    contact = p.get("contact_public") or _default_contact_public(user)
    owner_email = (p.get("owner") or {}).get("email") or user.get("email")
    _assert_contact_reachable(contact, owner_email)
    if not p.get("contact_public"):
        await db.properties.update_one({"id": pid}, {"$set": {"contact_public": contact}})

    from shared.ids import ensure_client_code, ensure_listing_code
    from apps.immocloud.listing_safety_gate import (
        VERDICT_ACCEPT,
        VERDICT_REJECT,
        evaluate_listing_safety,
        notify_founder_safety_flag,
        safety_gate_enabled,
    )

    listing_code = await ensure_listing_code(db, pid)
    client_code = await ensure_client_code(db, user["id"])
    p["reference_code"] = listing_code or p.get("reference_code")

    now = datetime.now(timezone.utc).isoformat()
    safety = None
    if safety_gate_enabled():
        safety = await evaluate_listing_safety(p)
        await db.properties.update_one(
            {"id": pid},
            {"$set": {"safety_gate": safety.to_dict(), "updated_at": now}},
        )

    can_auto = _b2c_auto_publish_enabled() and (
        safety is None or safety.verdict == VERDICT_ACCEPT
    )

    if can_auto:
        await db.properties.update_one(
            {"id": pid},
            {"$set": {
                "moderation_status": "approved",
                "status": "active",
                "visibility": "public",
                "moderation_notes": "auto_publish_safety_accept",
                "moderation_reviewed_at": now,
                "moderation_reviewed_by": "safety_gate",
                "updated_at": now,
                "reference_code": listing_code or p.get("reference_code"),
            }},
        )
        logger.info(
            "private listing auto-published (safety ACCEPT): id=%s code=%s user=%s",
            pid, listing_code, user["id"],
        )
        try:
            from apps.immocloud.alert_fanout import fanout_listing_event
            await fanout_listing_event(pid, event="new")
        except Exception as e:
            logger.warning("fanout after auto-publish failed: %s", e)
        try:
            from apps.immoweb.private_listing_matching import run_private_listing_request_matching
            await run_private_listing_request_matching(property_id=pid)
        except Exception as e:
            logger.warning("matching after auto-publish failed: %s", e)
        return {
            "ok": True,
            "moderation_status": "approved",
            "status": "active",
            "auto_publish": True,
            "safety_verdict": (safety.verdict if safety else VERDICT_ACCEPT),
            "reference_code": listing_code,
            "client_code": client_code,
        }

    # Held for Founder (REVIEW) or hard-rejected
    reject = bool(safety and safety.verdict == VERDICT_REJECT)
    notes = None
    if safety:
        notes = f"safety_gate:{safety.verdict} · " + "; ".join(safety.reasons[:5])
        notes = notes[:500]
        await notify_founder_safety_flag(p, safety, event="submit")

    await db.properties.update_one(
        {"id": pid},
        {"$set": {
            "moderation_status": "rejected" if reject else "pending",
            "status": "draft",
            "visibility": "private",
            "moderation_notes": notes,
            "moderation_reviewed_at": now if reject else None,
            "moderation_reviewed_by": "safety_gate" if reject else None,
            "updated_at": now,
            "reference_code": listing_code or p.get("reference_code"),
        }},
    )
    logger.info(
        "private listing held: id=%s verdict=%s reject=%s user=%s",
        pid, (safety.verdict if safety else "n/a"), reject, user["id"],
    )
    return {
        "ok": True,
        "moderation_status": "rejected" if reject else "pending",
        "status": "draft",
        "auto_publish": False,
        "safety_verdict": (safety.verdict if safety else None),
        "safety_reasons": (safety.reasons if safety else []),
        "reference_code": listing_code,
        "client_code": client_code,
    }


class B2CStagingStartBody(BaseModel):
    """Kick (or re-kick) B2C staging fulfill after Stripe return (P-011)."""
    session_id: str = Field(..., min_length=8, max_length=200)


class B2CStagingPreviewBody(BaseModel):
    """Free anteprima before payment — user chooses photo + mode."""
    photo_id: str | None = Field(default=None, max_length=80)
    mode: Literal["standard", "empty", "reverse"] = "standard"
    style: str = Field(default="modern", max_length=40)
    # auto|detect → vision analysis binds room (never silent bedroom default)
    room_type: str = Field(default="auto", max_length=40)
    room_type_confirmed: bool = False
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
    photos = listing.get("photos") or []
    usable = [
        p for p in photos
        if isinstance(p, dict) and isinstance(p.get("url"), str) and p["url"].strip()
        and not p["url"].startswith("data:")
    ]
    if not usable:
        raise HTTPException(status_code=400, detail={
            "error": "listing_has_no_photos",
            "code": "listing_has_no_photos",
            "message": (
                "Salva l'annuncio con almeno una foto caricata (non solo in bozza locale) "
                "prima di generare l'anteprima Virtual Staging."
            ),
        })

    from apps.immoweb.virtual_staging import start_b2c_preview_job, _job_to_out

    job = await start_b2c_preview_job(
        user_id=user["id"],
        listing_id=pid,
        photo_id=body.photo_id,
        mode=body.mode,
        style=body.style,
        room_type=body.room_type,
        room_type_confirmed=body.room_type_confirmed,
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
    from apps.immoweb.virtual_staging import _job_to_out, _auto_save_b2c_variant

    job = await db.virtual_staging_jobs.find_one({
        "id": job_id,
        "user_id": user["id"],
        "property_id": pid,
        "payment_rail": {"$in": ["b2c_stripe", "b2c_preview"]},
    })
    if not job:
        raise HTTPException(status_code=404, detail="job_not_found")
    # Repair: re-attach / migrate data:→media if SellPage wiped the AI photo
    if job.get("payment_rail") == "b2c_stripe" and job.get("status") == "done":
        try:
            await _auto_save_b2c_variant(job_id, db)
            job = await db.virtual_staging_jobs.find_one({"id": job_id}) or job
        except Exception:
            logger.exception("b2c staging ensure-on-poll failed job=%s", job_id)
    out = _job_to_out(job).model_dump()
    out["source_photo_id"] = job.get("source_photo_id")
    out["source_photo_index"] = job.get("source_photo_index")
    out["payment_rail"] = job.get("payment_rail")
    out["saved_photo_id"] = job.get("saved_photo_id")
    out["room_analysis"] = job.get("room_analysis")
    out["qa_summary"] = job.get("qa_summary")
    out["pipeline_id"] = job.get("pipeline_id")
    out["qa_verdict"] = job.get("qa_verdict")
    out["room_confirm_recommended"] = job.get("room_confirm_recommended")
    return out


class B2CStagingReportBody(BaseModel):
    reason: str = Field(default="architecture_unfaithful", max_length=80)
    note: str = Field(default="", max_length=500)


@router.post("/{pid}/staging/{job_id}/report")
async def report_b2c_staging_result(
    pid: str,
    job_id: str,
    body: B2CStagingReportBody,
    user: dict = Depends(get_current_user),
):
    """User reports an unfaithful / architecturally wrong staging result (QA feedback)."""
    await _ensure_b2c(user)
    db = Database.get()
    listing = await db.properties.find_one(
        {"id": pid, "owner_user_id": user["id"], "is_private_listing": True},
        {"_id": 1},
    )
    if not listing:
        raise HTTPException(status_code=404, detail="listing_not_found")
    job = await db.virtual_staging_jobs.find_one({
        "id": job_id,
        "user_id": user["id"],
        "property_id": pid,
    })
    if not job:
        raise HTTPException(status_code=404, detail="job_not_found")
    from datetime import datetime, timezone
    report = {
        "at": datetime.now(timezone.utc).isoformat(),
        "user_id": user["id"],
        "reason": (body.reason or "architecture_unfaithful")[:80],
        "note": (body.note or "")[:500],
    }
    await db.virtual_staging_jobs.update_one(
        {"id": job_id},
        {"$push": {"user_reports": report}, "$set": {"user_reported_unfaithful": True}},
    )
    return {"ok": True, "job_id": job_id}


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
