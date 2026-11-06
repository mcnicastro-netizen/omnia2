"""OMNIA — M5.S4 Virtual Staging (D-033 + D-125 + D-136).

Catalog / erase / furnish engines live in staging_catalog, staging_erase,
staging_furnish (MOVE-ONLY split). This module keeps orchestrator + B2C + API
and re-exports public symbols for stable imports.

Primary pipeline (Founder OK 19-Ott-2026):
  Nano Banana 2 one-shot (fal = Gemini 3.1 Flash Image) × up to 4 styles
  + vision critic (Gemini Flash) → optional single retry per failed style

Legacy fallback (EVF-SAM + Ideogram + apartment LoRA) if nano engine fails
or OMNIA_STAGING_ENGINE=legacy.

CRM-aware prompt fragment + watermark "Render virtuale OMNIA".
No third-party staging SaaS embed.
"""
from __future__ import annotations

import asyncio
import base64
import io
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import fal_client
import httpx
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
)
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database
from shared.utils.net_guard import assert_public_url
from apps.billing.plans import CREDIT_COSTS
from apps.billing.routes import debit_credits
from apps.immoweb.staging_agent import (
    StagingAgent,
    critique_empty_from_meta,
    critique_furnished_heuristic,
    decide_accept,
    plan_staging,
)

from apps.immoweb.staging_catalog import (
    DEFAULT_MULTI_STYLES,
    EMPTY_ROOM_PROMPT,
    NEGATIVE_PROMPT,
    ROOM_LABELS,
    ROOM_TYPES,
    STYLES,
    _build_prompt,
    _photo_caption,
)
from apps.immoweb.staging_erase import (
    ARCHITECTURE_KEEP_LABELS,
    COST_BRIA,
    COST_EVF_SAM,
    COST_FLORENCE,
    COST_IDEOGRAM,
    COST_SAM2,
    ERASE_LABEL_ORDER,
    EVF_ARCHITECTURE_NEGATIVE,
    EVF_FURNITURE_PROMPTS,
    FURNITURE_DETECT_LABELS,
    MODEL_BRIA_ERASER,
    MODEL_EVF_SAM,
    MODEL_FAL_OBJECT_REMOVAL,
    MODEL_FLORENCE_DET,
    MODEL_IDEOGRAM_ERASE,
    MODEL_SAM2,
    MODEL_SAM2_BOX,
    _architecture_keep_mask,
    _bbox_iou,
    _bria_erase,
    _doorway_brightness,
    _erase_mask_url,
    _erase_once,
    _evf_furniture_union_mask,
    _fal_object_removal,
    _florence_furniture_boxes,
    _ideogram_erase,
    _mask_url_from_entry,
    _merge_furniture_mask_urls,
    _opening_brightness_map,
    _padded_box_mask_url,
    _sam2_mask_from_boxes,
    _sequential_furniture_erase,
    _sort_erase_boxes,
    _stage_sam2_mask,
    _upload_pil_mask,
    _white_ratio,
    merge_furniture_masks_from_images,
    nms_bboxes,
    _ERASE_PASS1_MAX,
    _ERASE_PASS2_MAX,
    _ERASE_PASS3_MAX,
    _MASK_AREA_MAX,
    _MASK_AREA_MIN,
    _MASK_BOX_AREA_MAX,
    _MASK_MERGE_CAP,
)
from apps.immoweb.staging_furnish import (
    COST_FLUX,
    COST_NANO_BANANA,
    COST_STAGING_LORA,
    COST_UPSCALE,
    COST_VISION_CRITIC,
    MODEL_APARTMENT_STAGING,
    MODEL_FLUX_INPAINT,
    MODEL_NANO_BANANA_EDIT,
    MODEL_UPSCALE,
    STAGING_ENGINE,
    VISION_CRITIC_MODEL,
    _STYLE_EN,
    _STYLE_ONESHOT_EN,
    _apartment_stage,
    _flux_inpaint,
    _nano_banana_edit,
    _oneshot_prompt,
    _stage_upscale,
    _staging_lora_prompt,
    _vision_critique_staging,
)


logger = logging.getLogger("omnia.staging")
router = APIRouter(prefix="/staging", tags=["virtual-staging"])

STAGING_CREDIT_COST = int(CREDIT_COSTS.get("virtual_staging_render") or 18)

MAX_UPLOAD_MB = 12
ALLOWED_MIME = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
SOFT_RATE_LIMIT_USER_HOUR = 20   # renders/ora/utente
SOFT_RATE_LIMIT_AGENCY_HOUR = 80  # renders/ora/agenzia
JOB_TTL_DAYS = 30
STALE_JOB_MINUTES = 10
MAX_PHOTO_WIDTH = 1600


# ─── Schemas ─────────────────────────────────────────────────────
class StagingGenerateBody(BaseModel):
    image_url: str = Field(..., description="Public URL of the source room photo")
    style: str = Field(default="modern")
    room_type: str = Field(default="living")
    property_id: Optional[str] = None
    mode: str = Field(default="standard", description="standard | reverse | empty")
    num_variants: int = Field(default=1, ge=1, le=4)
    variant_mode: str = Field(default="same_style", description="same_style | multi_style")
    styles: Optional[List[str]] = Field(default=None, description="Styles for multi_style mode")


class StagingVariantOut(BaseModel):
    url: str
    style: str
    upscaled: bool = True
    qa_verdict: Optional[str] = None
    hard_issues: Optional[List[str]] = None
    room_type: Optional[str] = None
    quality_score: Optional[float] = None
    publishable: Optional[bool] = None


class StagingStages(BaseModel):
    name: str
    status: str  # queued|running|done|failed
    duration_ms: Optional[int] = None
    cost_usd: Optional[float] = None
    error: Optional[str] = None
    note: Optional[str] = None
    engine: Optional[str] = None


class StagingJobOut(BaseModel):
    id: str
    status: str  # pending|running|done|failed
    source_url: str
    style: str
    room_type: str
    property_id: Optional[str]
    mode: str = "standard"
    variant_mode: str = "same_style"
    num_variants: int = 1
    stages: List[StagingStages]
    variants: List[StagingVariantOut] = []
    variant_url: Optional[str] = None
    crm_context: Optional[str] = None
    cost_total_usd: Optional[float] = None
    error: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    pipeline_id: Optional[str] = None
    qa_verdict: Optional[str] = None
    room_analysis: Optional[Dict[str, Any]] = None
    qa_summary: Optional[Dict[str, Any]] = None


class SaveToPropertyBody(BaseModel):
    variant_index: int = Field(default=0, ge=0, le=3)
    property_id: Optional[str] = None  # override job.property_id


# ─── Helpers ─────────────────────────────────────────────────────
async def _rate_limit(db, user_id: str, agency_id: Optional[str], renders_requested: int) -> None:
    since = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()

    async def _renders_since(match: dict) -> int:
        pipeline = [
            {"$match": {**match, "created_at": {"$gte": since}}},
            {"$group": {"_id": None, "n": {"$sum": {"$ifNull": ["$num_variants", 1]}}}},
        ]
        rows = await db.virtual_staging_jobs.aggregate(pipeline).to_list(length=1)
        return rows[0]["n"] if rows else 0

    user_count = await _renders_since({"user_id": user_id})
    if user_count + renders_requested > SOFT_RATE_LIMIT_USER_HOUR:
        raise HTTPException(429, f"Limite orario utente raggiunto ({SOFT_RATE_LIMIT_USER_HOUR} render/ora)")
    if agency_id:
        ag_count = await _renders_since({"agency_id": agency_id})
        if ag_count + renders_requested > SOFT_RATE_LIMIT_AGENCY_HOUR:
            raise HTTPException(429, f"Limite orario agenzia raggiunto ({SOFT_RATE_LIMIT_AGENCY_HOUR} render/ora)")


def _job_to_out(doc: dict) -> StagingJobOut:
    variants = doc.get("variants") or []
    if not variants and doc.get("variant_url"):
        variants = [{"url": doc["variant_url"], "style": doc.get("style", "modern"), "upscaled": True}]
    out_variants: List[StagingVariantOut] = []
    for v in variants:
        if not isinstance(v, dict) or not v.get("url"):
            continue
        out_variants.append(StagingVariantOut(
            url=v["url"],
            style=v.get("style") or doc.get("style") or "modern",
            upscaled=bool(v.get("upscaled", True)),
            qa_verdict=v.get("qa_verdict"),
            hard_issues=v.get("hard_issues"),
            room_type=v.get("room_type"),
            quality_score=v.get("quality_score"),
            publishable=v.get("publishable"),
        ))
    return StagingJobOut(
        id=doc["id"],
        status=doc["status"],
        source_url=doc["source_url"],
        style=doc["style"],
        room_type=doc.get("room_type") or "living",
        property_id=doc.get("property_id"),
        mode=doc.get("mode", "standard"),
        variant_mode=doc.get("variant_mode", "same_style"),
        num_variants=doc.get("num_variants", 1),
        stages=[StagingStages(**{k: s.get(k) for k in ("name", "status", "duration_ms", "cost_usd", "error", "note", "engine")}) for s in doc.get("stages", [])],
        variants=out_variants,
        variant_url=doc.get("variant_url"),
        crm_context=doc.get("crm_context"),
        cost_total_usd=doc.get("cost_total_usd"),
        error=doc.get("error"),
        created_at=doc["created_at"],
        completed_at=doc.get("completed_at"),
        pipeline_id=doc.get("pipeline_id"),
        qa_verdict=doc.get("qa_verdict"),
        room_analysis=doc.get("room_analysis"),
        qa_summary=doc.get("qa_summary"),
    )


# ─── CRM-aware prompt (Gemini, best-effort) ──────────────────────
async def _crm_prompt_fragment(db, agency_id: Optional[str], property_id: str) -> tuple[Optional[str], Optional[str]]:
    """Returns (english_prompt_fragment, italian_summary) or (None, None)."""
    query: Dict[str, Any] = {"id": property_id}
    if agency_id:
        query["agency_id"] = agency_id
    prop = await db.properties.find_one(query, {"_id": 0})
    if not prop:
        return None, None

    price = (prop.get("price") or {}).get("amount") if isinstance(prop.get("price"), dict) else prop.get("price")
    ctx = {
        "tipologia": prop.get("property_type"),
        "città": prop.get("city"),
        "zona": prop.get("zone") or prop.get("address"),
        "prezzo": price,
        "superficie_mq": (prop.get("surfaces") or {}).get("total") if isinstance(prop.get("surfaces"), dict) else prop.get("surface"),
        "operazione": prop.get("operation"),
        "titolo": prop.get("title"),
    }
    from shared.llm import try_resolve_api_key

    api_key = try_resolve_api_key()
    if not api_key:
        return None, None
    try:
        from shared.llm.chat import LlmChat, UserMessage  # type: ignore

        chat = LlmChat(
            api_key=api_key,
            session_id=f"staging-crm-{uuid4()}",
            system_message=(
                "Sei un interior designer esperto di virtual staging immobiliare italiano. "
                "Dato il contesto CRM di un immobile, genera UNA breve frase IN INGLESE (max 25 parole) "
                "da aggiungere a un prompt di image generation per arredare la stanza in modo ottimale "
                "per il target buyer di quell'immobile (fascia prezzo, zona, tipologia). "
                "Rispondi SOLO con la frase inglese, senza virgolette né spiegazioni."
            ),
        ).with_model("gemini", "gemini-3-flash-preview")
        import json as _json

        raw = await asyncio.wait_for(
            chat.send_message(UserMessage(text=_json.dumps(ctx, ensure_ascii=False, default=str))),
            timeout=15,
        )
        fragment = str(raw).strip().strip('"').strip()
        if not fragment or len(fragment) > 300:
            return None, None
        summary = f"{ctx.get('tipologia') or 'immobile'} · {ctx.get('città') or '—'}" + (
            f" · €{int(price):,}".replace(",", ".") if price else ""
        )
        return fragment, summary
    except Exception as e:
        logger.warning("CRM-aware prompt failed (%s), using static prompt", e)
        return None, None


# ─── Source URL helpers (B2C private media → fal) ─────────────────
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


async def _resolve_image_url_for_fal(src: str) -> str:
    """fal.ai needs a fetchable URL; private `/api/media/…` is re-uploaded to fal."""
    raw = (src or "").strip()
    if not raw:
        raise RuntimeError("source_url vuota")
    if not raw.startswith("/api/media/"):
        return raw
    from shared.storage import get_object, ObjStoreError

    storage_path = raw[len("/api/media/"):]
    try:
        data, ct = get_object(storage_path)
    except ObjStoreError as e:
        raise RuntimeError(f"media non leggibile: {e}") from e
    if not data:
        raise RuntimeError("media vuoto")
    import tempfile

    ext = "jpg"
    if ct and "png" in ct:
        ext = "png"
    elif ct and "webp" in ct:
        ext = "webp"
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        return await asyncio.to_thread(fal_client.upload_file, tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


async def _persist_staging_jpeg(
    user_id: str,
    job_id: str,
    jpeg_bytes: bytes,
    *,
    suffix: str = "render",
) -> str:
    """Store watermarked staging JPEG in private Object Storage; return /api/media URL.

    SellPage intentionally drops `data:` photo URLs on save — staging must never
    persist as base64 or a later cover/edit wipe removes the AI photo.
    """
    from shared.storage import put_object

    safe_uid = (user_id or "anon").replace("/", "_")
    safe_suffix = "".join(c for c in suffix if c.isalnum() or c in "-_")[:48] or "render"
    path = f"omnia/private/{safe_uid}/staging/{job_id}-{safe_suffix}.jpg"
    await asyncio.to_thread(put_object, path, jpeg_bytes, "image/jpeg")
    return f"/api/media/{path}"


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
        asyncio.create_task(_run_pipeline(job_id, db))
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
        asyncio.create_task(_run_pipeline(job_id, db))
    except RuntimeError:
        # No running loop (sync test harness) — caller may invoke pipeline later
        logger.warning("staging fulfill: no event loop to schedule job=%s", job_id)
    logger.info(
        "b2c staging job started job=%s session=%s listing=%s photo=%s mode=%s",
        job_id, session_id, listing_id, resolved_photo_id, mode,
    )
    return {"purchase": claimed, "job": doc}


# ─── Pipeline stages ─────────────────────────────────────────────

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


async def _run_pipeline(job_id: str, db) -> None:
    from time import monotonic

    doc = await db.virtual_staging_jobs.find_one({"id": job_id})
    if not doc:
        return

    stage_idx = {s["name"]: i for i, s in enumerate(doc.get("stages", []))}

    async def _mark_stage(name: str, patch: dict) -> None:
        i = stage_idx[name]
        await db.virtual_staging_jobs.update_one(
            {"id": job_id},
            {"$set": {f"stages.{i}.{k}": v for k, v in patch.items()}},
        )

    async def _mark_root(patch: dict) -> None:
        await db.virtual_staging_jobs.update_one({"id": job_id}, {"$set": patch})

    async def _fail(stage_name: str, prefix: str, e: Exception) -> None:
        logger.exception("%s stage failed for %s", prefix, job_id)
        await _mark_stage(stage_name, {"status": "failed", "error": str(e)[:300]})
        await _mark_root({
            "status": "failed",
            "error": f"{prefix}: {str(e)[:200]}",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })

    await _mark_root({"status": "running"})
    src_raw = doc["source_url"]
    mode = doc.get("mode", "standard")
    variant_mode = doc.get("variant_mode", "same_style")
    num_variants = doc.get("num_variants", 1)
    engine_pref = STAGING_ENGINE if STAGING_ENGINE in ("nano_banana", "legacy") else "nano_banana"

    try:
        src = await _resolve_image_url_for_fal(src_raw)
        if src != src_raw:
            await _mark_root({"source_url_fal": src})
    except Exception as e:
        await _fail("sam2_mask", "Resolve source", e)
        return

    # Stage 0 (all engines): bind room type via vision — never silent bedroom default
    from apps.immoweb.staging_room_analysis import analyze_room_image, resolve_room_type

    room_analysis = await analyze_room_image(src)
    bound_room = resolve_room_type(
        analysis=room_analysis,
        user_room_type=doc.get("room_type"),
        user_confirmed=bool(doc.get("room_type_confirmed")),
    )
    doc["room_analysis"] = room_analysis
    doc["room_type"] = bound_room
    await _mark_root({
        "room_analysis": room_analysis,
        "room_type": bound_room,
        "room_confirm_recommended": bool(room_analysis.get("needs_user_confirm")),
    })

    agent = StagingAgent(plan_staging(
        mode=mode,
        style=doc.get("style") or "modern",
        room_type=bound_room,
        num_variants=num_variants,
        variant_mode=variant_mode,
        styles_list=doc.get("styles_list") or DEFAULT_MULTI_STYLES,
        engine=engine_pref,
    ))
    await _mark_root({"agent_plan": agent.plan.to_dict()})

    # CRM-aware prompt (best-effort, silent)
    crm_fragment = None
    if doc.get("property_id"):
        crm_fragment, crm_summary = await _crm_prompt_fragment(db, doc.get("agency_id"), doc["property_id"])
        if crm_summary:
            await _mark_root({"crm_context": crm_summary})

    variants: List[dict] = []
    engine_used = "none"
    nano_ok = False

    # ── Professional pipeline (D-136) — gestionale B2B only by default ────
    from apps.immoweb.staging_professional import (
        pipeline_enabled_for_job,
        run_professional_pipeline,
    )

    if pipeline_enabled_for_job(doc):
        accepted = await run_professional_pipeline(
            job_id=job_id,
            db=db,
            doc=doc,
            src=src,
            agent=agent,
            mark_stage=_mark_stage,
            mark_root=_mark_root,
            fail=_fail,
            sequential_furniture_erase=_sequential_furniture_erase,
            apartment_stage=_apartment_stage,
            flux_inpaint=_flux_inpaint,
            stage_sam2_mask=_stage_sam2_mask,
            oneshot_prompt=_oneshot_prompt,
            nano_banana_edit=_nano_banana_edit,
            resolve_image_url_for_fal=_resolve_image_url_for_fal,
            cost_nano=COST_NANO_BANANA,
            cost_lora=COST_STAGING_LORA,
            cost_flux=COST_FLUX,
        )
        if accepted is None:
            return  # hard fail already marked
        variants = accepted
        engine_used = "professional_v1"
        nano_ok = True  # skip nano/legacy paths
        if not variants:
            await _mark_root({
                "status": "failed",
                "error": "architecture_reject: nessuna variante ha superato i controlli architettonici",
                "qa_verdict": "REJECT",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "agent_summary": agent.summary(),
            })
            return

    # ── Primary: Nano Banana one-shot × styles + vision critic ─────────────
    if (not nano_ok) and agent.plan.engine == "nano_banana":
        try:
            t0 = monotonic()
            await _mark_stage("sam2_mask", {
                "status": "done", "duration_ms": 0, "cost_usd": 0,
                "note": "skipped_nano_banana_oneshot",
            })
            # Keep furniture_removal RUNNING during empty/reverse oneshot so the FE
            # progress label shows "Svuotamento…" instead of jumping to "Arredamento…".
            # standard mode has no furniture_removal stage — skip.
            if "furniture_removal" in stage_idx:
                if agent.plan.need_erase:
                    await _mark_stage("furniture_removal", {
                        "status": "running",
                        "engine": "nano_banana_2",
                        "note": "oneshot_erase_in_progress",
                    })
                else:
                    await _mark_stage("furniture_removal", {
                        "status": "done", "duration_ms": 0, "cost_usd": 0,
                        "note": "skipped_standard",
                        "engine": "nano_banana_2",
                    })
            # Empty mode: generation is the erase itself — keep flux_inpaint queued
            # until erase oneshot finishes, then mark done. Furnish modes run flux as running.
            if mode != "empty":
                await _mark_stage("flux_inpaint", {"status": "running"})

            style_keys = agent.plan.styles[: agent.plan.num_variants]

            async def _gen_style(sk: str) -> dict:
                prompt = _oneshot_prompt(mode, sk, agent.plan.room_type, crm_fragment)
                url = await _nano_banana_edit(src, prompt, resolution="1K")
                return {"url": url, "style": sk, "upscaled": False, "engine": "nano_banana_2"}

            raw_variants = list(await asyncio.gather(
                *[_gen_style(sk) for sk in style_keys],
                return_exceptions=True,
            ))
            variants = []
            for sk, item in zip(style_keys, raw_variants):
                if isinstance(item, Exception):
                    logger.warning("nano oneshot failed style=%s: %s", sk, item)
                    continue
                agent.charge(COST_NANO_BANANA, f"nano_oneshot:{sk}")
                variants.append(item)
            if not variants:
                raise RuntimeError("Nano Banana: nessuna variante generata")

            if agent.plan.need_erase and "furniture_removal" in stage_idx:
                await _mark_stage("furniture_removal", {
                    "status": "done",
                    "duration_ms": int((monotonic() - t0) * 1000) if mode == "empty" else 0,
                    "cost_usd": round(COST_NANO_BANANA, 4) if mode == "empty" else 0,
                    "note": "oneshot_includes_erase",
                    "engine": "nano_banana_2",
                })
            if mode == "empty":
                await _mark_stage("flux_inpaint", {
                    "status": "done", "duration_ms": 0, "cost_usd": 0,
                    "note": "skipped_empty_oneshot",
                    "engine": "nano_banana_2",
                })
            else:
                await _mark_stage("flux_inpaint", {"status": "running"})

            # Vision critic per variant (parallel)
            critiques = list(await asyncio.gather(*[
                _vision_critique_staging(src, v["url"], style=v["style"], mode=mode)
                for v in variants
            ]))
            for v, q in zip(variants, critiques):
                agent.charge(COST_VISION_CRITIC, f"vision_critic:{v['style']}")
                decision = decide_accept(
                    q,
                    retries_left=1 if agent.can_spend(COST_NANO_BANANA) else 0,
                    can_afford=agent.can_spend(COST_NANO_BANANA),
                )
                hard = [i for i in (q.issues or []) if i in (
                    "invented_windows", "architecture_fail", "room_function_changed",
                    "invented_door", "invented_built_in", "geometry_broken",
                )]
                v["quality_score"] = round(q.score, 3)
                v["quality_decision"] = decision
                v["qa_verdict"] = {
                    "accept": "ACCEPT",
                    "accept_with_warning": "ACCEPT",
                    "retry": "RETRY",
                    "reject": "REJECT",
                }.get(decision, "MANUAL_REVIEW")
                v["hard_issues"] = hard
                v["room_type"] = bound_room
                v["publishable"] = decision in ("accept", "accept_with_warning") and not hard
                if hard and decision == "accept":
                    # Aesthetic score cannot override architectural hard fail
                    v["quality_decision"] = "reject"
                    v["qa_verdict"] = "REJECT"
                    v["publishable"] = False
                agent.record_quality(f"style:{v['style']}", q, v["quality_decision"])

            # Retry styles that invent openings / fail architecture (budget-capped, max 2).
            retry_idxs = []
            for i, v in enumerate(variants):
                if v.get("quality_decision") != "retry":
                    continue
                qphase = agent.quality.get(f"style:{v['style']}") or {}
                issues = qphase.get("issues") or []
                # Prefer invented_windows / architecture first
                pri = 0 if ("invented_windows" in issues or "architecture_fail" in issues) else 1
                retry_idxs.append((pri, float(v.get("quality_score") or 0), i))
            retry_idxs.sort()  # architecture fails first, then lowest score
            # Founder: max 1 retry per job (anti-aperture / qualità).
            retries_done = 0
            for _, _, retry_idx in retry_idxs:
                if retries_done >= 1 or not agent.can_spend(COST_NANO_BANANA):
                    break
                if agent.furnish_retries >= 1:
                    break
                agent.furnish_retries += 1
                retries_done += 1
                sk = variants[retry_idx]["style"]
                logger.info(
                    "nano retry style=%s score=%.2f issues=%s",
                    sk, variants[retry_idx].get("quality_score"),
                    (agent.quality.get(f"style:{sk}") or {}).get("issues"),
                )
                prompt = _oneshot_prompt(mode, sk, agent.plan.room_type, crm_fragment)
                prompt = (
                    prompt
                    + " RETRY FIX: the previous edit illegally invented windows. "
                    "Keep EVERY wall blank where the source has no window. "
                    "ZERO new windows, ZERO skylights, ZERO glass wall panels. "
                    "Preserve only the existing door openings on the left. "
                    "No yellow cast; no leftover gym or old furniture."
                )
                try:
                    new_url = await _nano_banana_edit(src, prompt, resolution="1K")
                    agent.charge(COST_NANO_BANANA, f"nano_retry:{sk}")
                    q2 = await _vision_critique_staging(src, new_url, style=sk, mode=mode)
                    agent.charge(COST_VISION_CRITIC, f"vision_critic_retry:{sk}")
                    d2 = decide_accept(q2, retries_left=0, can_afford=False)
                    # Prefer non-invented architecture even if score similar
                    old_inv = bool(
                        (agent.quality.get(f"style:{sk}") or {})
                        .get("signals", {})
                        .get("invented_openings")
                    )
                    new_inv = bool(q2.signals.get("invented_openings"))
                    take = (not new_inv and old_inv) or (
                        q2.score >= float(variants[retry_idx].get("quality_score") or 0)
                        and not new_inv
                    )
                    hard2 = [i for i in (q2.issues or []) if i in (
                        "invented_windows", "architecture_fail", "room_function_changed",
                        "invented_door", "invented_built_in", "geometry_broken",
                    )]
                    if take or (not new_inv and q2.score >= 0.55):
                        pub = d2 in ("accept", "accept_with_warning") and not hard2
                        variants[retry_idx] = {
                            **variants[retry_idx],
                            "url": new_url,
                            "quality_score": round(q2.score, 3),
                            "quality_decision": "reject" if hard2 else d2,
                            "qa_verdict": "REJECT" if hard2 else {
                                "accept": "ACCEPT",
                                "accept_with_warning": "ACCEPT",
                                "retry": "RETRY",
                                "reject": "REJECT",
                            }.get(d2, "MANUAL_REVIEW"),
                            "hard_issues": hard2,
                            "room_type": bound_room,
                            "publishable": pub,
                        }
                    agent.record_quality(f"style:{sk}:retry", q2, variants[retry_idx].get("quality_decision") or d2)
                except Exception as retry_err:
                    logger.warning("nano retry failed style=%s: %s", sk, retry_err)

            # Prefer highest critic score among publishable first; keep rejects for audit
            from apps.immoweb.staging_qa_gate import variant_is_publishable as _vip
            variants.sort(
                key=lambda v: (
                    1 if _vip(v) else 0,
                    float(v.get("quality_score") or 0),
                ),
                reverse=True,
            )
            publishable = [v for v in variants if _vip(v)]
            engine_used = "nano_banana_2_oneshot"
            stage_cost = COST_NANO_BANANA * len(style_keys) + (
                COST_NANO_BANANA if agent.furnish_retries else 0
            )
            if mode != "empty":
                await _mark_stage("flux_inpaint", {
                    "status": "done",
                    "duration_ms": int((monotonic() - t0) * 1000),
                    "cost_usd": round(stage_cost, 4),
                    "engine": engine_used,
                    "note": (
                        "styles=" + ",".join(v["style"] for v in variants)
                        + "|scores=" + ",".join(f"{v.get('quality_score', 0):.2f}" for v in variants)
                    )[:280],
                })
            await _mark_stage("upscale", {
                "status": "done", "duration_ms": 0, "cost_usd": 0,
                "note": "skipped_nano_banana",
            })
            await _mark_root({
                "agent_quality": agent.quality,
                "erase_meta": {"engine": "nano_oneshot"},
                "qa_summary": {
                    "accepted": len(publishable),
                    "total": len(variants),
                    "room_type": bound_room,
                    "pipeline_id": "nano_oneshot",
                },
                "variants_all": variants,
            })
            if not publishable:
                await _mark_root({
                    "status": "failed",
                    "error": "architecture_reject: nessuna variante ha superato i controlli architettonici",
                    "qa_verdict": "REJECT",
                    "variants": variants,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "agent_summary": agent.summary(),
                })
                return
            variants = publishable
            nano_ok = True
        except Exception as e:
            logger.exception("nano_banana primary path failed — legacy fallback: %s", e)
            await _mark_root({"nano_fallback_error": str(e)[:300]})
            # Rebuild agent plan for legacy budgets
            agent = StagingAgent(plan_staging(
                mode=mode,
                style=doc.get("style") or "modern",
                room_type=bound_room,
                num_variants=num_variants,
                variant_mode=variant_mode,
                styles_list=doc.get("styles_list") or DEFAULT_MULTI_STYLES,
                engine="legacy",
            ))
            await _mark_root({"agent_plan": agent.plan.to_dict()})

    # ── Legacy: EVF erase + apartment LoRA ─────────────────────────────────
    if not nano_ok:
        mask_url: Optional[str] = None
        try:
            t0 = monotonic()
            await _mark_stage("sam2_mask", {"status": "running"})
            if agent.plan.need_erase:
                await _mark_stage("sam2_mask", {
                    "status": "done",
                    "duration_ms": int((monotonic() - t0) * 1000),
                    "cost_usd": 0,
                    "note": "florence_detect_inside_erase",
                })
            else:
                mask_url = await _stage_sam2_mask(src, for_furniture=False)
                await _mark_root({"mask_url": mask_url})
                await _mark_stage("sam2_mask", {
                    "status": "done",
                    "duration_ms": int((monotonic() - t0) * 1000),
                    "cost_usd": COST_SAM2,
                })
                agent.charge(COST_SAM2, "sam2_mask")
        except Exception as e:
            await _fail("sam2_mask", "SAM2", e)
            return

        base_image = src
        erase_meta: Dict[str, Any] = {}
        if agent.plan.need_erase:
            try:
                t0 = monotonic()
                await _mark_stage("furniture_removal", {"status": "running"})
                base_image, removal_cost, erase_meta = await _sequential_furniture_erase(src)
                agent.charge(removal_cost, "furniture_removal", engine=erase_meta.get("engine"))
                empty_q = critique_empty_from_meta(erase_meta)
                decision = decide_accept(empty_q, retries_left=0, can_afford=False)
                agent.record_quality("empty", empty_q, decision)
                await _mark_root({"erase_meta": erase_meta, "agent_quality": agent.quality})
                await _mark_stage("furniture_removal", {
                    "status": "done",
                    "duration_ms": int((monotonic() - t0) * 1000),
                    "cost_usd": round(removal_cost, 4),
                    "engine": erase_meta.get("engine"),
                    "note": f"erased={','.join(erase_meta.get('erased') or [])}"[:280],
                })
            except Exception as e:
                await _fail("furniture_removal", "Rimozione arredo", e)
                return

        if not agent.plan.need_furnish:
            variants = [{"url": base_image, "style": "empty", "upscaled": False}]
            await _mark_stage("flux_inpaint", {
                "status": "done", "duration_ms": 0, "cost_usd": 0,
                "note": "skipped_empty_mode", "engine": "none",
            })
        else:
            try:
                t0 = monotonic()
                await _mark_stage("flux_inpaint", {"status": "running"})
                style_keys = agent.plan.styles[: agent.plan.num_variants]
                engine_used = "apartment_staging_lora"
                for sk in style_keys:
                    prompt = _staging_lora_prompt(sk, agent.plan.room_type, crm_fragment)
                    try:
                        urls = await _apartment_stage(
                            base_image, prompt,
                            num_images=1 if variant_mode == "multi_style" else agent.plan.num_variants,
                        )
                    except Exception as lora_err:
                        logger.warning("Apartment staging LoRA failed (%s) — Flux fallback", lora_err)
                        engine_used = "flux_inpaint_fallback"
                        if not mask_url:
                            mask_url = await _stage_sam2_mask(base_image, for_furniture=True)
                            agent.charge(COST_SAM2, "sam2_mask_fallback")
                        urls = await _flux_inpaint(
                            base_image, mask_url,
                            _build_prompt(sk, agent.plan.room_type, crm_fragment),
                            num_images=1 if variant_mode == "multi_style" else agent.plan.num_variants,
                        )
                    variants.extend({"url": u, "style": sk, "upscaled": False} for u in urls)
                    if variant_mode != "multi_style":
                        break
                if not variants:
                    raise RuntimeError("Nessuna variante staging generata")
                stage_cost = (
                    COST_STAGING_LORA if engine_used.startswith("apartment") else COST_FLUX
                ) * len(variants)
                agent.charge(stage_cost, "furnish", engine=engine_used)
                furn_q = critique_furnished_heuristic(
                    style=style_keys[0], engine=engine_used, erase_meta=erase_meta,
                )
                agent.record_quality("furnish", furn_q, decide_accept(furn_q, retries_left=0, can_afford=False))
                await _mark_stage("flux_inpaint", {
                    "status": "done",
                    "duration_ms": int((monotonic() - t0) * 1000),
                    "cost_usd": round(stage_cost, 4),
                    "engine": engine_used,
                })
            except Exception as e:
                await _fail("flux_inpaint", "Staging", e)
                return

        t0 = monotonic()
        await _mark_stage("upscale", {"status": "running"})
        if not agent.plan.need_furnish or not engine_used.startswith("flux_inpaint"):
            await _mark_stage("upscale", {
                "status": "done", "duration_ms": 0, "cost_usd": 0,
                "note": "skipped",
            })
        else:
            async def _up(v: dict) -> dict:
                try:
                    url = await _stage_upscale(v["url"])
                    return {**v, "url": url or v["url"], "upscaled": bool(url)}
                except Exception as e:
                    logger.warning("Upscale failed: %s", e)
                    return v
            variants = list(await asyncio.gather(*[_up(v) for v in variants]))
            upscaled_n = sum(1 for v in variants if v.get("upscaled"))
            up_cost = COST_UPSCALE * upscaled_n
            agent.charge(up_cost, "upscale")
            await _mark_stage("upscale", {
                "status": "done" if upscaled_n else "failed",
                "duration_ms": int((monotonic() - t0) * 1000),
                "cost_usd": round(up_cost, 4),
            })

    # B2C free preview: persist to /api/media so SellPage img is same-origin + smaller
    try:
        variants = await _persist_b2c_preview_variants(job_id, db, variants)
    except Exception:
        logger.exception("b2c preview persist failed job=%s", job_id)

    total_cost = agent.ledger.spent_usd
    await _mark_root({
        "status": "done",
        "variants": variants,
        "variant_url": variants[0]["url"] if variants else None,
        "cost_total_usd": round(total_cost, 4),
        "agent_summary": agent.summary(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })

    # Debit only after successful pipeline (no charge on mid-fail).
    # B2C Stripe rail already paid via b2c_purchases — skip agency wallet.
    try:
        doc_paid = await db.virtual_staging_jobs.find_one(
            {"id": job_id},
            {"agency_id": 1, "num_variants": 1, "payment_rail": 1},
        )
        rail = (doc_paid or {}).get("payment_rail")
        aid = (doc_paid or {}).get("agency_id")
        n = max(1, int((doc_paid or {}).get("num_variants") or 1))
        if rail == "b2c_stripe":
            await db.virtual_staging_jobs.update_one(
                {"id": job_id},
                {"$set": {"credits_charged": 0, "payment_rail": "b2c_stripe"}},
            )
            if variants:
                try:
                    await _auto_save_b2c_variant(job_id, db)
                except Exception:
                    logger.exception("b2c staging auto-save failed job=%s", job_id)
        elif aid and variants:
            bal = await debit_credits(
                aid,
                STAGING_CREDIT_COST * n,
                reason="virtual_staging_render",
                ref_id=job_id,
                ref_type="virtual_staging_job",
            )
            await db.virtual_staging_jobs.update_one(
                {"id": job_id},
                {"$set": {"credits_charged": STAGING_CREDIT_COST * n, "credits_balance_after": bal}},
            )
    except HTTPException as e:
        logger.warning("staging debit failed job=%s detail=%s", job_id, e.detail)
        await db.virtual_staging_jobs.update_one(
            {"id": job_id},
            {"$set": {"credits_debit_error": str(e.detail)[:300]}},
        )
    except Exception:
        logger.exception("staging debit unexpected job=%s", job_id)


# ─── Stale-job reaper (called at server startup) ─────────────────
async def reap_stale_jobs() -> int:
    db = Database.get()
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=STALE_JOB_MINUTES)).isoformat()
    res = await db.virtual_staging_jobs.update_many(
        {"status": {"$in": ["pending", "running"]}, "created_at": {"$lt": cutoff}},
        {"$set": {
            "status": "failed",
            "error": "Job interrotto da riavvio del server",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return res.modified_count


# ─── Image post-processing ───────────────────────────────────────
def _apply_watermark(image_bytes: bytes, text: str = "Render virtuale OMNIA", max_width: Optional[int] = None) -> bytes:
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    if max_width and img.size[0] > max_width:
        h = int(img.size[1] * max_width / img.size[0])
        img = img.resize((max_width, h), Image.LANCZOS)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(20, img.size[0] // 40)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    padding = font_size // 2
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    box_x0 = img.size[0] - tw - padding * 3
    box_y0 = img.size[1] - th - padding * 3
    draw.rectangle(
        [box_x0, box_y0, img.size[0] - padding, img.size[1] - padding],
        fill=(0, 0, 0, 160),
    )
    draw.text((box_x0 + padding, box_y0 + padding), text, font=font, fill=(255, 255, 255, 255))
    watermarked = Image.alpha_composite(img, overlay).convert("RGB")
    out = io.BytesIO()
    watermarked.save(out, format="JPEG", quality=90)
    return out.getvalue()


async def _fetch_variant_bytes(doc: dict, variant_index: int) -> tuple[bytes, str]:
    """Downloads variant image → (bytes, style_key). Raises HTTPException on bad state."""
    if doc["status"] != "done":
        raise HTTPException(409, "Job non ancora completato")
    variants = doc.get("variants") or (
        [{"url": doc["variant_url"], "style": doc.get("style", "modern")}] if doc.get("variant_url") else []
    )
    if variant_index >= len(variants):
        raise HTTPException(404, f"Variante {variant_index} non trovata")
    v = variants[variant_index]
    # Prefer original fal URL (full-res) when preview was persisted as /api/media
    url = (v.get("fal_url") or v.get("url") or "").strip()
    if not url:
        raise HTTPException(404, "URL variante mancante")
    if url.startswith("/api/media/"):
        from shared.storage import get_object, ObjStoreError

        try:
            data, _ct = get_object(url[len("/api/media/"):])
        except ObjStoreError as e:
            raise HTTPException(404, f"Media variante non leggibile: {e}") from e
        return data, v.get("style", "modern")
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url)
        r.raise_for_status()
    return r.content, v.get("style", "modern")


# ─── Endpoints ───────────────────────────────────────────────────
@router.get("/styles")
async def list_styles() -> Dict[str, Any]:
    return {
        "styles": [{"key": k, "label": v["label"]} for k, v in STYLES.items()],
        "room_types": [{"key": k, "label": ROOM_LABELS.get(k, k.capitalize())} for k in ROOM_TYPES.keys()],
        "modes": [
            {"key": "standard", "label": "Arreda (staging)"},
            {"key": "empty", "label": "Svuota stanza"},
            {"key": "reverse", "label": "Svuota e ri-arreda"},
        ],
        "credit_cost_per_variant": STAGING_CREDIT_COST,
    }


@router.get("/credits-check")
async def staging_credits_check(
    num_variants: int = 1,
    user=Depends(get_current_user),
) -> Dict[str, Any]:
    """A-013 — pre-check saldo before starting an expensive AI render."""
    n = max(1, min(int(num_variants or 1), 4))
    required = STAGING_CREDIT_COST * n
    agency_id = user.get("agency_id") or (user.get("agency_ids") or [None])[0]
    balance = 0
    if agency_id:
        db = Database.get()
        wallet = await db.credit_wallets.find_one({"agency_id": agency_id}, {"_id": 0, "balance": 1})
        balance = int((wallet or {}).get("balance") or 0)
    return {
        "agency_id": agency_id,
        "balance": balance,
        "required": required,
        "credit_cost_per_variant": STAGING_CREDIT_COST,
        "num_variants": n,
        "ok": balance >= required if agency_id else False,
    }


@router.post("/upload")
async def upload_source_image(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
) -> Dict[str, str]:
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(400, f"MIME non supportato: {file.content_type}")
    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File troppo grande (max {MAX_UPLOAD_MB} MB)")

    import tempfile

    suffix = ".jpg" if "jpeg" in file.content_type or "jpg" in file.content_type else ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        url = await asyncio.to_thread(fal_client.upload_file, tmp_path)
        return {"url": url}
    except Exception as e:
        logger.exception("fal upload failed")
        raise HTTPException(502, f"Upload fallito: {str(e)[:200]}")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


@router.post("/generate", response_model=StagingJobOut)
async def generate_staging(
    body: StagingGenerateBody,
    background: BackgroundTasks,
    user=Depends(get_current_user),
) -> StagingJobOut:
    db = Database.get()

    if body.style not in STYLES:
        raise HTTPException(400, f"Stile non supportato: {body.style}")
    if body.room_type not in ROOM_TYPES:
        raise HTTPException(400, f"Tipo stanza non supportato: {body.room_type}")
    if body.mode not in ("standard", "reverse", "empty"):
        raise HTTPException(400, f"Modalità non supportata: {body.mode}")
    if body.variant_mode not in ("same_style", "multi_style"):
        raise HTTPException(400, f"variant_mode non supportato: {body.variant_mode}")

    # M12 — SSRF/abuse guard: accetta solo media interni (/api/media/...) o URL http(s) pubblici
    src = (body.image_url or "").strip()
    if not src:
        raise HTTPException(400, "image_url mancante")
    if not src.startswith("/api/media/") and "/api/media/" not in src.split("?")[0][:200]:
        assert_public_url(src)

    styles_list: Optional[List[str]] = None
    if body.variant_mode == "multi_style":
        styles_list = [s for s in (body.styles or DEFAULT_MULTI_STYLES) if s in STYLES]
        if not styles_list:
            raise HTTPException(400, "Nessuno stile valido per multi_style")
        styles_list = styles_list[: body.num_variants]

    agency_id = user.get("agency_id") or (user.get("agency_ids") or [None])[0]
    await _rate_limit(db, user["id"], agency_id, body.num_variants)

    # A-013 — hard-gate crediti PRIMA di avviare SAM2/Flux
    n_var = max(1, min(int(body.num_variants or 1), 4))
    required = STAGING_CREDIT_COST * n_var
    if not agency_id:
        raise HTTPException(status_code=402, detail={
            "error": "insufficient_credits",
            "message": "Serve un'agenzia con wallet crediti per generare render.",
            "required": required,
            "balance": 0,
        })
    wallet = await db.credit_wallets.find_one({"agency_id": agency_id}, {"_id": 0, "balance": 1})
    balance = int((wallet or {}).get("balance") or 0)
    if balance < required:
        raise HTTPException(status_code=402, detail={
            "error": "insufficient_credits",
            "message": f"Crediti insufficienti: servono {required}, saldo {balance}. Ricarica da Impostazioni → Billing.",
            "required": required,
            "balance": balance,
        })

    if body.property_id:
        q: Dict[str, Any] = {"id": body.property_id}
        if agency_id:
            q["agency_id"] = agency_id
        if not await db.properties.find_one(q, {"_id": 1}):
            raise HTTPException(404, "Immobile non trovato")

    stages = [{"name": "sam2_mask", "status": "queued"}]
    if body.mode in ("reverse", "empty"):
        stages.append({"name": "furniture_removal", "status": "queued"})
    stages.append({"name": "flux_inpaint", "status": "queued"})
    stages.append({"name": "upscale", "status": "queued"})

    job_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()
    doc = {
        "id": job_id,
        "user_id": user["id"],
        "agency_id": agency_id,
        "property_id": body.property_id,
        "source_url": body.image_url,
        "style": body.style,
        "room_type": body.room_type,
        "mode": body.mode,
        "num_variants": body.num_variants,
        "variant_mode": body.variant_mode,
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
    }
    await db.virtual_staging_jobs.insert_one(doc)

    background.add_task(_run_pipeline, job_id, db)
    return _job_to_out(doc)


@router.get("/jobs/{job_id}", response_model=StagingJobOut)
async def get_job(job_id: str, user=Depends(get_current_user)) -> StagingJobOut:
    db = Database.get()
    doc = await db.virtual_staging_jobs.find_one({"id": job_id, "user_id": user["id"]})
    if not doc:
        raise HTTPException(404, "Job non trovato")
    return _job_to_out(doc)


@router.get("/history")
async def list_history(user=Depends(get_current_user), limit: int = 50) -> Dict[str, Any]:
    db = Database.get()
    cursor = db.virtual_staging_jobs.find(
        {"user_id": user["id"]}, {"_id": 0}
    ).sort("created_at", -1).limit(min(limit, 100))
    items = [_job_to_out(d).model_dump() for d in await cursor.to_list(length=100)]
    return {"items": items, "count": len(items)}


@router.get("/jobs/{job_id}/download")
async def download_watermarked(job_id: str, variant: int = 0, user=Depends(get_current_user)) -> Response:
    db = Database.get()
    doc = await db.virtual_staging_jobs.find_one({"id": job_id, "user_id": user["id"]})
    if not doc:
        raise HTTPException(404, "Job non trovato")
    source_bytes, _style = await _fetch_variant_bytes(doc, variant)
    watermarked = await asyncio.to_thread(_apply_watermark, source_bytes)
    filename = f"omnia-staging-{job_id[:8]}-v{variant}.jpg"
    return Response(
        content=watermarked,
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/jobs/{job_id}/variants/{variant_index}/dataurl")
async def variant_as_dataurl(job_id: str, variant_index: int, user=Depends(get_current_user)) -> Dict[str, str]:
    """Watermarked + resized (≤1600px) Object Storage URL for property photo persistence.

    Historically returned a `data:` URL; SellPage drops those on save, so we now
    persist to private media and return `/api/media/…` (also as `data_url` alias).
    """
    db = Database.get()
    doc = await db.virtual_staging_jobs.find_one({"id": job_id, "user_id": user["id"]})
    if not doc:
        raise HTTPException(404, "Job non trovato")
    source_bytes, style_key = await _fetch_variant_bytes(doc, variant_index)
    processed = await asyncio.to_thread(_apply_watermark, source_bytes, "Render virtuale OMNIA", MAX_PHOTO_WIDTH)
    media_url = await _persist_staging_jpeg(
        user["id"], job_id, processed, suffix=f"add-v{variant_index}",
    )
    caption = _photo_caption(style_key, doc.get("room_type", "living"))
    return {
        "url": media_url,
        "data_url": media_url,  # alias — FE StagingStudio historically read data_url
        "caption": caption,
    }


@router.post("/jobs/{job_id}/save-to-property")
async def save_variant_to_property(
    job_id: str,
    body: SaveToPropertyBody,
    user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Persists a variant as a new photo of the linked property (Object Storage, watermarked)."""
    db = Database.get()
    doc = await db.virtual_staging_jobs.find_one({"id": job_id, "user_id": user["id"]})
    if not doc:
        raise HTTPException(404, "Job non trovato")

    property_id = body.property_id or doc.get("property_id")
    if not property_id:
        raise HTTPException(400, "Nessun immobile collegato al job")

    agency_id = user.get("agency_id") or (user.get("agency_ids") or [None])[0]
    q: Dict[str, Any] = {"id": property_id}
    if agency_id:
        q["agency_id"] = agency_id
    prop = await db.properties.find_one(q, {"_id": 0, "photos": 1})
    if prop is None:
        raise HTTPException(404, "Immobile non trovato")

    source_bytes, style_key = await _fetch_variant_bytes(doc, body.variant_index)
    processed = await asyncio.to_thread(_apply_watermark, source_bytes, "Render virtuale OMNIA", MAX_PHOTO_WIDTH)
    media_url = await _persist_staging_jpeg(
        user["id"], job_id, processed, suffix=f"prop-v{body.variant_index}",
    )

    photos = prop.get("photos") or []
    new_photo = {
        "id": str(uuid4()),
        "url": media_url,
        "caption": _photo_caption(style_key, doc.get("room_type", "living")),
        "order": len(photos),
        "is_cover": len(photos) == 0,
        "is_virtual_staging": True,
        "staging_mode": doc.get("mode") or "standard",
        "source_photo_id": doc.get("source_photo_id"),
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
        }},
    )
    return {"ok": True, "photo_id": new_photo["id"], "photo_count": len(photos) + 1, "url": media_url}


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, user=Depends(get_current_user)) -> Dict[str, bool]:
    db = Database.get()
    res = await db.virtual_staging_jobs.delete_one({"id": job_id, "user_id": user["id"]})
    if res.deleted_count == 0:
        raise HTTPException(404, "Job non trovato")
    return {"ok": True}
