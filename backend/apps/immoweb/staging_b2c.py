"""OMNIA staging — B2C preview / paid fulfill / auto-save. MOVE-ONLY extract.

Schedules pipeline via lazy import of virtual_staging._run_pipeline (no cycle).
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import uuid4

import httpx
from fastapi import HTTPException
from PIL import Image

from shared.db.connection import Database
from apps.immoweb.staging_catalog import (
    DEFAULT_MULTI_STYLES,
    ROOM_TYPES,
    STYLES,
    _photo_caption,
)
from apps.immoweb.staging_media import (
    MAX_PHOTO_WIDTH,
    _apply_watermark,
    _fetch_variant_bytes,
    _persist_staging_jpeg,
)

logger = logging.getLogger("omnia.staging")


def _schedule_pipeline(job_id: str, db) -> None:
    """Lazy import avoids circular import with virtual_staging orchestrator."""
    from apps.immoweb.virtual_staging import _run_pipeline
    try:
        asyncio.create_task(_run_pipeline(job_id, db))
    except RuntimeError:
        logger.warning("staging fulfill: no event loop to schedule job=%s", job_id)


def _listing_photo_url(photo: Any) -> str:
    if isinstance(photo, str):
        u = photo.strip()
    elif isinstance(photo, dict):
        u = str(photo.get("url") or "").strip()
    else:
        return ""
    # Local/draft data-URLs are not fetchable by fal — treat as missing.
    if not u or u.startswith("data:"):
        return ""
    return u

async def _auto_save_b2c_variant(job_id: str, db) -> None:
    """Attach watermarked publishable variant to the private listing after paid B2C job.

    Re-attaches if a previous save used a data: URL that SellPage later stripped,
    or if saved_photo_id is no longer on the listing.
    """
    doc = await db.virtual_staging_jobs.find_one({"id": job_id})
    if not doc or doc.get("payment_rail") != "b2c_stripe":
        return
    property_id = doc.get("property_id")
    if not property_id:
        return
    prop = await db.properties.find_one(
        {"id": property_id, "is_private_listing": True, "owner_user_id": doc.get("user_id")},
        {"_id": 0, "photos": 1},
    )
    if prop is None:
        logger.warning("b2c staging auto-save: listing missing job=%s pid=%s", job_id, property_id)
        return

    photos = list(prop.get("photos") or [])
    saved_photo_id = doc.get("saved_photo_id")
    migrate_idx = None
    if saved_photo_id:
        for i, ph in enumerate(photos):
            if not isinstance(ph, dict) or ph.get("id") != saved_photo_id:
                continue
            url = str(ph.get("url") or "")
            if url.startswith("/api/media/") or url.startswith("https://"):
                return  # already durable
            if url.startswith("data:"):
                migrate_idx = i
                break
            return
        else:
            # saved_photo_id wiped by SellPage data: filter — re-attach below
            logger.warning(
                "b2c staging photo missing on listing — re-attach job=%s pid=%s photo=%s",
                job_id, property_id, saved_photo_id,
            )

    from apps.immoweb.staging_qa_gate import variant_is_publishable

    variants = doc.get("variants") or []
    publishable_idx = next((i for i, v in enumerate(variants) if variant_is_publishable(v)), None)
    if publishable_idx is None and variants:
        # Legacy jobs without qa_verdict: allow index 0 only if no hard reject markers
        if not variant_is_publishable({**variants[0], "qa_verdict": variants[0].get("qa_verdict") or "ACCEPT"}):
            logger.warning("b2c staging auto-save blocked — no publishable variant job=%s", job_id)
            await db.virtual_staging_jobs.update_one(
                {"id": job_id},
                {"$set": {"fulfillment_error": "architecture_reject_no_publishable_variant"}},
            )
            return
        publishable_idx = 0
    if publishable_idx is None:
        logger.warning("b2c staging auto-save blocked — empty variants job=%s", job_id)
        return
    source_bytes, style_key = await _fetch_variant_bytes(doc, publishable_idx)
    wm = "Svuotamento virtuale OMNIA" if doc.get("mode") == "empty" else "Render virtuale OMNIA"
    processed = await asyncio.to_thread(
        _apply_watermark, source_bytes, wm, MAX_PHOTO_WIDTH,
    )
    media_url = await _persist_staging_jpeg(
        doc.get("user_id") or "anon",
        job_id,
        processed,
        suffix=f"v{publishable_idx}",
    )
    caption = (
        "Svuotamento virtuale OMNIA · stanza svuotata"
        if doc.get("mode") == "empty"
        else _photo_caption(style_key, doc.get("room_type", "living"))
    )
    source_photo_id = doc.get("source_photo_id")
    source_index = None
    if source_photo_id:
        for i, ph in enumerate(photos):
            if isinstance(ph, dict) and ph.get("id") == source_photo_id:
                source_index = i
                break

    if migrate_idx is not None:
        ph = photos[migrate_idx]
        photos[migrate_idx] = {
            **ph,
            "url": media_url,
            "caption": caption or ph.get("caption"),
            "is_virtual_staging": True,
            "source_photo_id": source_photo_id or ph.get("source_photo_id"),
            "staging_mode": doc.get("mode") or ph.get("staging_mode") or "standard",
        }
        await db.properties.update_one(
            {"id": property_id},
            {"$set": {"photos": photos, "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        logger.info(
            "b2c staging migrated data:→media job=%s photo=%s", job_id, saved_photo_id,
        )
        return

    new_photo = {
        "id": str(uuid4()),
        "url": media_url,
        "caption": caption,
        "order": len(photos),
        "is_cover": False,
        "is_virtual_staging": True,
        "source_photo_id": source_photo_id,
        "staging_mode": doc.get("mode") or "standard",
    }
    await db.properties.update_one(
        {"id": property_id},
        {"$push": {"photos": new_photo}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await db.virtual_staging_jobs.update_one(
        {"id": job_id},
        {"$set": {
            "saved_to_property_id": property_id,
            "saved_photo_id": new_photo["id"],
            "source_photo_index": source_index,
        }},
    )
    logger.info(
        "b2c staging auto-saved job=%s → property=%s photo=%s url=%s",
        job_id, property_id, new_photo["id"], media_url,
    )

def _pick_listing_photo(photos: list, photo_id: Optional[str] = None) -> tuple[str, Optional[str], Optional[int]]:
    """Return (url, photo_id, index). Prefer explicit photo_id, else first usable."""
    if not photos:
        return "", None, None
    if photo_id:
        for i, ph in enumerate(photos):
            if isinstance(ph, dict) and ph.get("id") == photo_id:
                u = _listing_photo_url(ph)
                if u:
                    return u, photo_id, i
    for i, ph in enumerate(photos):
        u = _listing_photo_url(ph)
        if u:
            pid = ph.get("id") if isinstance(ph, dict) else None
            return u, pid, i
    return "", None, None

async def start_b2c_preview_job(
    *,
    user_id: str,
    listing_id: str,
    photo_id: Optional[str] = None,
    mode: str = "standard",
    style: str = "modern",
    room_type: str = "auto",
    room_type_confirmed: bool = False,
    variant_mode: str = "same_style",
    num_variants: int = 1,
    styles: Optional[List[str]] = None,
) -> dict:
    """Free preview render (rate-limited). Does not attach to listing until paid."""
    if mode not in ("standard", "reverse", "empty"):
        raise HTTPException(status_code=400, detail="unsupported_staging_mode")
    if variant_mode not in ("same_style", "multi_style"):
        raise HTTPException(status_code=400, detail="unsupported_variant_mode")
    db = Database.get()
    listing = await db.properties.find_one(
        {"id": listing_id, "owner_user_id": user_id, "is_private_listing": True},
        {"_id": 0, "id": 1, "photos": 1},
    )
    if not listing:
        raise HTTPException(status_code=404, detail="listing_not_found")
    photos = listing.get("photos") or []
    source_url, resolved_photo_id, source_index = _pick_listing_photo(photos, photo_id)
    if not source_url:
        raise HTTPException(status_code=400, detail={
            "error": "listing_has_no_photos",
            "code": "listing_has_no_photos",
            "message": (
                "Salva l'annuncio con almeno una foto caricata "
                "prima di generare l'anteprima Virtual Staging."
            ),
        })

    # Daily free-preview cap (anti-abuse).
    # OMNIA_B2C_STAGING_PREVIEW_DAILY_CAP: default 3; 0 = unlimited (dogfood).
    # Exempt emails: ADMIN* + OMNIA_B2C_STAGING_PREVIEW_CAP_EXEMPT_EMAILS
    # Exempt domains: built-in dogfood + OMNIA_B2C_STAGING_PREVIEW_CAP_EXEMPT_DOMAINS
    try:
        daily_cap = max(0, int(os.environ.get("OMNIA_B2C_STAGING_PREVIEW_DAILY_CAP") or "3"))
    except Exception:
        daily_cap = 3
    exempt = {
        (os.environ.get("ADMIN_EMAIL") or "").strip().lower(),
        (os.environ.get("OMNIA_ADMIN_EMAIL") or "").strip().lower(),
        (os.environ.get("SUPER_ADMIN_EMAIL") or "").strip().lower(),
    }
    for part in (os.environ.get("OMNIA_B2C_STAGING_PREVIEW_CAP_EXEMPT_EMAILS") or "").split(","):
        p = part.strip().lower()
        if p:
            exempt.add(p)
    exempt.discard("")
    exempt_domains = {
        "omniaecosystem.it",
        "example.com",
        "test.com",
        "localhost",
        "virgilio.it",  # Founder account di prova B2C
    }
    for part in (os.environ.get("OMNIA_B2C_STAGING_PREVIEW_CAP_EXEMPT_DOMAINS") or "").split(","):
        p = part.strip().lower().lstrip("@")
        if p:
            exempt_domains.add(p)
    skip_cap = daily_cap == 0
    u = await db.users.find_one({"id": user_id}, {"_id": 0, "email": 1, "role": 1})
    email = ((u or {}).get("email") or "").strip().lower()
    role = ((u or {}).get("role") or "").strip().lower()
    domain = email.split("@", 1)[-1] if "@" in email else ""
    if email in exempt or role in ("super_admin", "founder"):
        skip_cap = True
    elif domain in exempt_domains or any(email.endswith("@" + d) for d in exempt_domains):
        skip_cap = True
    if not skip_cap and daily_cap > 0:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        used = await db.virtual_staging_jobs.count_documents({
            "user_id": user_id,
            "payment_rail": "b2c_preview",
            "created_at": {"$gte": start.isoformat()},
        })
        if used >= daily_cap:
            raise HTTPException(status_code=429, detail={
                "error": "preview_daily_cap",
                "code": "preview_daily_cap",
                "message": f"Hai raggiunto il limite di {daily_cap} anteprime staging al giorno.",
            })

    n_var = max(1, min(int(num_variants or 1), 4))
    styles_list: Optional[List[str]] = None
    if mode != "empty" and variant_mode == "multi_style":
        styles_list = [s for s in (styles or DEFAULT_MULTI_STYLES) if s in STYLES][:n_var]
        if not styles_list:
            raise HTTPException(status_code=400, detail="no_valid_styles")
        n_var = len(styles_list)
        style = styles_list[0]
    else:
        variant_mode = "same_style"
        n_var = 1

    job_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    stages = [{"name": "sam2_mask", "status": "queued"}]
    if mode in ("reverse", "empty"):
        stages.append({"name": "furniture_removal", "status": "queued"})
    stages.extend([
        {"name": "flux_inpaint", "status": "queued"},
        {"name": "upscale", "status": "queued"},
    ])
    doc = {
        "id": job_id,
        "user_id": user_id,
        "agency_id": None,
        "property_id": listing_id,
        "source_url": source_url,
        "source_photo_id": resolved_photo_id,
        "source_photo_index": source_index,
        "style": style if mode != "empty" else "empty",
        "room_type": room_type or "auto",
        "room_type_confirmed": bool(room_type_confirmed),
        "mode": mode,
        "num_variants": n_var,
        "variant_mode": variant_mode,
        "styles_list": styles_list,
        "status": "pending",
        "stages": stages,
        "variants": [],
        "variant_url": None,
        "crm_context": None,
        "cost_total_usd": None,
        "error": None,
        "created_at": now,
        "completed_at": None,
        "payment_rail": "b2c_preview",
    }
    await db.virtual_staging_jobs.insert_one(doc)
    try:
        _schedule_pipeline(job_id, db)
    except RuntimeError:
        logger.warning("b2c preview: no event loop to schedule job=%s", job_id)
    logger.info(
        "b2c staging preview job=%s listing=%s photo=%s mode=%s",
        job_id, listing_id, resolved_photo_id, mode,
    )
    return doc

async def fulfill_paid_staging_render(session_id: str) -> Optional[dict]:
    """Idempotent webhook/API fulfill: consume purchase + start/attach B2C staging job (P-011)."""
    if not session_id:
        return None
    db = Database.get()
    purchase = await db.b2c_purchases.find_one({
        "stripe_session_id": session_id,
        "product_key": "b2c_staging_render",
    })
    if not purchase:
        logger.warning("staging fulfill: no purchase session=%s", session_id)
        return None
    if purchase.get("status") != "paid":
        return purchase
    if purchase.get("job_id"):
        job = await db.virtual_staging_jobs.find_one({"id": purchase["job_id"]}, {"_id": 0})
        return {"purchase": purchase, "job": job}

    listing_id = purchase.get("listing_id")
    user_id = purchase.get("user_id")
    if not listing_id or not user_id:
        logger.error("staging fulfill: missing listing/user session=%s", session_id)
        return purchase

    listing = await db.properties.find_one(
        {
            "id": listing_id,
            "owner_user_id": user_id,
            "is_private_listing": True,
        },
        {"_id": 0, "id": 1, "photos": 1},
    )
    if not listing:
        logger.error("staging fulfill: listing not found session=%s listing=%s", session_id, listing_id)
        return purchase

    preview_job_id = (purchase.get("preview_job_id") or "").strip() or None
    photo_id = (purchase.get("photo_id") or "").strip() or None
    mode = (purchase.get("staging_mode") or "standard").strip() or "standard"
    if mode not in ("standard", "reverse", "empty"):
        mode = "standard"

    # Path A — promote an already-generated free preview (no second AI run)
    if preview_job_id:
        preview = await db.virtual_staging_jobs.find_one({
            "id": preview_job_id,
            "user_id": user_id,
            "property_id": listing_id,
            "payment_rail": "b2c_preview",
        })
        if preview and preview.get("status") == "done" and not preview.get("saved_to_property_id"):
            from apps.immoweb.staging_qa_gate import variant_is_publishable
            preview_variants = preview.get("variants") or []
            if preview_variants and not any(variant_is_publishable(v) for v in preview_variants):
                logger.warning(
                    "staging fulfill blocked — preview not publishable job=%s", preview_job_id,
                )
                await db.b2c_purchases.update_one(
                    {"stripe_session_id": session_id},
                    {"$set": {"fulfillment_error": "architecture_reject_preview"}},
                )
                return purchase
            from apps.billing.b2c_entitlements import consume_b2c_staging_render
            claimed = await consume_b2c_staging_render(
                user_id,
                listing_id=listing_id,
                stripe_session_id=session_id,
                job_id=preview_job_id,
            )
            if not claimed:
                purchase = await db.b2c_purchases.find_one({"stripe_session_id": session_id}) or purchase
                if purchase.get("job_id"):
                    job = await db.virtual_staging_jobs.find_one({"id": purchase["job_id"]}, {"_id": 0})
                    return {"purchase": purchase, "job": job}
                return purchase
            await db.virtual_staging_jobs.update_one(
                {"id": preview_job_id},
                {"$set": {
                    "payment_rail": "b2c_stripe",
                    "b2c_stripe_session_id": session_id,
                    "b2c_purchase_id": claimed.get("id"),
                }},
            )
            try:
                await _auto_save_b2c_variant(preview_job_id, db)
            except Exception:
                logger.exception("b2c staging promote-preview save failed job=%s", preview_job_id)
            job = await db.virtual_staging_jobs.find_one({"id": preview_job_id}, {"_id": 0})
            return {"purchase": claimed, "job": job}

    photos = listing.get("photos") or []
    source_url, resolved_photo_id, source_index = _pick_listing_photo(photos, photo_id)
    if not source_url:
        await db.b2c_purchases.update_one(
            {"stripe_session_id": session_id},
            {"$set": {"fulfillment_error": "listing_has_no_photos"}},
        )
        logger.error("staging fulfill: no photos session=%s listing=%s", session_id, listing_id)
        return purchase

    job_id = str(uuid4())
    from apps.billing.b2c_entitlements import consume_b2c_staging_render

    claimed = await consume_b2c_staging_render(
        user_id,
        listing_id=listing_id,
        stripe_session_id=session_id,
        job_id=job_id,
    )
    if not claimed:
        # Race: another fulfill already claimed
        purchase = await db.b2c_purchases.find_one({"stripe_session_id": session_id}) or purchase
        if purchase.get("job_id"):
            job = await db.virtual_staging_jobs.find_one({"id": purchase["job_id"]}, {"_id": 0})
            return {"purchase": purchase, "job": job}
        return purchase

    now = datetime.now(timezone.utc).isoformat()
    pay_style = (purchase.get("style") or "modern").strip() or "modern"
    pay_room = (purchase.get("room_type") or "living").strip() or "living"
    if pay_room in ("auto", "detect", "empty"):
        pay_room = "living"
    if pay_style not in STYLES:
        pay_style = "modern"
    if pay_room not in ROOM_TYPES:
        pay_room = "living"
    stages = [{"name": "sam2_mask", "status": "queued"}]
    if mode in ("reverse", "empty"):
        stages.append({"name": "furniture_removal", "status": "queued"})
    stages.extend([
        {"name": "flux_inpaint", "status": "queued"},
        {"name": "upscale", "status": "queued"},
    ])
    doc = {
        "id": job_id,
        "user_id": user_id,
        "agency_id": None,
        "property_id": listing_id,
        "source_url": source_url,
        "source_photo_id": resolved_photo_id,
        "source_photo_index": source_index,
        "style": pay_style if mode != "empty" else "empty",
        "room_type": pay_room,
        "mode": mode,
        "num_variants": 1,
        "variant_mode": "same_style",
        "styles_list": None,
        "status": "pending",
        "stages": stages,
        "variants": [],
        "variant_url": None,
        "crm_context": None,
        "cost_total_usd": None,
        "error": None,
        "created_at": now,
        "completed_at": None,
        "payment_rail": "b2c_stripe",
        "b2c_stripe_session_id": session_id,
        "b2c_purchase_id": claimed.get("id"),
    }
    await db.virtual_staging_jobs.insert_one(doc)
    try:
        _schedule_pipeline(job_id, db)
    except RuntimeError:
        # No running loop (sync test harness) — caller may invoke pipeline later
        logger.warning("staging fulfill: no event loop to schedule job=%s", job_id)
    logger.info(
        "b2c staging job started job=%s session=%s listing=%s photo=%s mode=%s",
        job_id, session_id, listing_id, resolved_photo_id, mode,
    )
    return {"purchase": claimed, "job": doc}

async def _persist_b2c_preview_variants(job_id: str, db, variants: List[dict]) -> List[dict]:
    """Copy fal preview URLs into private media so the Sell UI loads same-origin."""
    doc = await db.virtual_staging_jobs.find_one(
        {"id": job_id},
        {"user_id": 1, "payment_rail": 1},
    )
    if not doc or doc.get("payment_rail") != "b2c_preview":
        return variants
    user_id = doc.get("user_id") or "anon"
    from shared.storage import put_object

    out: List[dict] = []
    async with httpx.AsyncClient(timeout=90.0) as client:
        for i, v in enumerate(variants):
            url = v.get("url")
            if not url or str(url).startswith("/api/media/"):
                out.append(v)
                continue
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.content
                ct = (resp.headers.get("content-type") or "image/jpeg").split(";")[0].strip()
                ext = "png" if "png" in ct else "jpg"
                # Downscale huge ESRGAN outputs for fast preview in the browser
                im = Image.open(io.BytesIO(data)).convert("RGB")
                if im.width > 1600:
                    im.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                im.save(buf, format="JPEG", quality=88, optimize=True)
                data = buf.getvalue()
                ct = "image/jpeg"
                ext = "jpg"
                path = f"omnia/private/{user_id}/staging-preview/{job_id}-{i}.{ext}"
                await asyncio.to_thread(put_object, path, data, ct)
                out.append({**v, "url": f"/api/media/{path}", "fal_url": url})
            except Exception as e:
                logger.warning("persist preview variant failed job=%s i=%s: %s", job_id, i, e)
                out.append(v)
    return out

