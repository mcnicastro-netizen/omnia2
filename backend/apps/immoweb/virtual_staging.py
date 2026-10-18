"""OMNIA — M5.S4 Virtual Staging (quality v2).

Reference: DECISIONS.md D-033.

Pipeline (empty / reverse):
  Stage 1 — EVF-SAM semantic furniture mask (multi-prompt union) + arch keep
  Stage 1b — Ideogram erase on union mask, then Florence/SAM2 remnant passes
  Stage 2 — Flux 2 apartment-staging LoRA (skipped for mode=empty)
  Stage 3 — ESRGAN only on Flux-inpaint fallback

Standard (already-empty room): apartment-staging LoRA directly.
CRM-aware prompt fragment (Gemini) + watermark "Render virtuale OMNIA".
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

logger = logging.getLogger("omnia.staging")
router = APIRouter(prefix="/staging", tags=["virtual-staging"])

STAGING_CREDIT_COST = int(CREDIT_COSTS.get("virtual_staging_render") or 18)

MODEL_SAM2 = "fal-ai/sam2/auto-segment"
MODEL_SAM2_BOX = "fal-ai/sam2/image"
MODEL_FLORENCE_DET = "fal-ai/florence-2-large/open-vocabulary-detection"
MODEL_BRIA_ERASER = "fal-ai/bria/eraser"
MODEL_IDEOGRAM_ERASE = "fal-ai/ideogram/object-removal"
MODEL_FAL_OBJECT_REMOVAL = "fal-ai/object-removal/mask"
MODEL_EVF_SAM = "fal-ai/evf-sam"
MODEL_APARTMENT_STAGING = "fal-ai/flux-2-lora-gallery/apartment-staging"
MODEL_FLUX_INPAINT = "fal-ai/flux-lora/inpainting"
MODEL_UPSCALE = "fal-ai/esrgan"

# Openings / built-ins that must not be painted over during erase (anti wall-invention).
ARCHITECTURE_KEEP_LABELS = (
    "door",
    "doorway",
    "open door",
    "window",
    "sliding door",
)

# EVF-SAM text prompts — unioned into one furniture mask (casalimpia-style semantic split).
EVF_FURNITURE_PROMPTS = (
    "gym machine, exercise equipment, weight bench, weights",
    "bed, mattress, bedding, pillows, nightstand",
    "wardrobe, closet, dresser, cupboard",
    "rug, carpet, mat",
    "shelf, table, chair, lamp, picture frame, hanging decoration",
)
EVF_ARCHITECTURE_NEGATIVE = "walls, floor, ceiling, doors, doorways, windows, baseboards, built-in fixtures"

MAX_UPLOAD_MB = 12
ALLOWED_MIME = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
SOFT_RATE_LIMIT_USER_HOUR = 20   # renders/ora/utente
SOFT_RATE_LIMIT_AGENCY_HOUR = 80  # renders/ora/agenzia
JOB_TTL_DAYS = 30
STALE_JOB_MINUTES = 10
MAX_PHOTO_WIDTH = 1600

COST_SAM2 = 0.001
COST_FLORENCE = 0.001
COST_EVF_SAM = 0.01
COST_BRIA = 0.04
COST_IDEOGRAM = 0.03
COST_STAGING_LORA = 0.06
COST_FLUX = 0.05
COST_UPSCALE = 0.005

# Florence open-vocab labels for lived-in Italian interiors (empty/reverse).
FURNITURE_DETECT_LABELS = (
    "gym machine",
    "exercise equipment",
    "weight bench",
    "bench",
    "wardrobe",
    "closet",
    "bed",
    "sofa",
    "rug",
    "carpet",
    "nightstand",
    "shelf",
    "table",
    "chair",
    "lamp",
    "picture frame",
    "dresser",
    "desk",
    "hanging decoration",
    "curtain",
    "plant",
    "mirror",
)

# Erase largest / most disruptive objects first.
ERASE_LABEL_ORDER = (
    "gym machine",
    "exercise equipment",
    "weight bench",
    "bench",
    "wardrobe",
    "closet",
    "dresser",
    "bed",
    "sofa",
    "desk",
    "table",
    "shelf",
    "rug",
    "carpet",
    "nightstand",
    "chair",
    "curtain",
    "lamp",
    "picture frame",
    "hanging decoration",
    "plant",
    "mirror",
)

# Reject Florence false-positives that cover nearly the whole frame.
_MASK_BOX_AREA_MAX = 0.35
_ERASE_PASS1_MAX = 8
_ERASE_PASS2_MAX = 5
_ERASE_PASS3_MAX = 4

# ─── Style catalog (prompts calibrated for real-estate rooms) ───
STYLES: Dict[str, Dict[str, str]] = {
    "modern": {
        "label": "Moderno",
        "prompt": "modern minimalist interior, neutral colors, clean lines, natural light, high-end contemporary furniture, wooden floor, professional interior photography",
        "staging_prompt": (
            "Furnish this empty room with modern minimalist furniture and decor, "
            "keep existing walls doors windows floor and ceiling unchanged, "
            "photorealistic real estate listing photo"
        ),
    },
    "classic": {
        "label": "Classico",
        "prompt": "classic elegant italian interior, warm colors, traditional wooden furniture, curtains, chandelier, parquet flooring, refined atmosphere",
        "staging_prompt": (
            "Furnish this empty room with classic elegant Italian furniture, warm wood, "
            "keep architecture unchanged, photorealistic real estate listing photo"
        ),
    },
    "scandi": {
        "label": "Scandinavo",
        "prompt": "scandinavian interior design, white walls, light wooden floor, minimalist furniture, cozy textiles, natural light, hygge atmosphere",
        "staging_prompt": (
            "Furnish this empty room with scandinavian furniture, light wood, soft textiles, "
            "bright and airy, keep architecture unchanged, photorealistic real estate photo"
        ),
    },
    "industrial": {
        "label": "Industriale",
        "prompt": "industrial loft style, exposed brick, metal fixtures, concrete floor, leather sofa, edison bulbs, urban chic",
        "staging_prompt": (
            "Furnish this empty room with industrial loft furniture, leather and metal accents, "
            "keep architecture unchanged, photorealistic real estate listing photo"
        ),
    },
    "luxury": {
        "label": "Luxury",
        "prompt": "luxury interior design, marble floor, designer furniture, gold accents, high ceilings, large windows, premium finishes",
        "staging_prompt": (
            "Furnish this empty room with luxury designer furniture and premium finishes, "
            "keep architecture unchanged, photorealistic real estate listing photo"
        ),
    },
}

DEFAULT_MULTI_STYLES = ["modern", "classic", "scandi", "luxury"]

ROOM_TYPES: Dict[str, str] = {
    "living": "spacious living room with sofa, coffee table, TV area, decorative plants",
    "bedroom": "bedroom with double bed, nightstands, wardrobe, soft ambient lighting",
    "kitchen": "modern kitchen with island, appliances, dining area, pendant lights",
    "dining": "dining room with table for 6, chairs, sideboard, elegant lighting",
    "bathroom": "bathroom with modern fixtures, shower, vanity, towels, plants",
    "office": "home office with desk, ergonomic chair, bookshelf, natural light",
}

ROOM_LABELS = {
    "living": "Soggiorno",
    "bedroom": "Camera da letto",
    "kitchen": "Cucina",
    "dining": "Sala da pranzo",
    "bathroom": "Bagno",
    "office": "Studio",
}

NEGATIVE_PROMPT = (
    "people, humans, faces, text, watermark, logo, distorted furniture, "
    "blurry, low quality, deformed walls, weird perspective, "
    "invented architecture, new walls, new windows, melted objects, "
    "glitch, smear, warped geometry, floating fragments"
)

# Region-focused: describe only what replaces the masked furniture area.
# Avoid "bare walls / redesign room" — that causes Flux to invent architecture.
EMPTY_ROOM_PROMPT = (
    "seamless continuation of the existing floor and wall surfaces only, "
    "empty space with no furniture no objects no rugs no lamps no decorations, "
    "same tiles paint lighting and perspective as the surrounding room, "
    "photorealistic interior photograph, no architectural changes"
)

# Mid-sized SAM segments ≈ furniture/objects (exclude wall/floor-sized + noise).
_MASK_AREA_MIN = 0.008
_MASK_AREA_MAX = 0.38
_MASK_MERGE_CAP = 40


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


def _build_prompt(style: str, room_type: str, crm_fragment: Optional[str] = None) -> str:
    s = STYLES.get(style, STYLES["modern"])
    room = ROOM_TYPES.get(room_type, ROOM_TYPES["living"])
    parts = [s["prompt"], room]
    if crm_fragment:
        parts.append(crm_fragment)
    parts.append("photorealistic, 8k, architectural photography")
    return ", ".join(parts)


def _job_to_out(doc: dict) -> StagingJobOut:
    variants = doc.get("variants") or []
    if not variants and doc.get("variant_url"):
        variants = [{"url": doc["variant_url"], "style": doc.get("style", "modern"), "upscaled": True}]
    return StagingJobOut(
        id=doc["id"],
        status=doc["status"],
        source_url=doc["source_url"],
        style=doc["style"],
        room_type=doc["room_type"],
        property_id=doc.get("property_id"),
        mode=doc.get("mode", "standard"),
        variant_mode=doc.get("variant_mode", "same_style"),
        num_variants=doc.get("num_variants", 1),
        stages=[StagingStages(**s) for s in doc.get("stages", [])],
        variants=[StagingVariantOut(**v) for v in variants],
        variant_url=doc.get("variant_url"),
        crm_context=doc.get("crm_context"),
        cost_total_usd=doc.get("cost_total_usd"),
        error=doc.get("error"),
        created_at=doc["created_at"],
        completed_at=doc.get("completed_at"),
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
        return photo.strip()
    if isinstance(photo, dict):
        return str(photo.get("url") or "").strip()
    return ""


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


async def _auto_save_b2c_variant(job_id: str, db) -> None:
    """Attach watermarked variant #0 to the private listing after a paid B2C job."""
    doc = await db.virtual_staging_jobs.find_one({"id": job_id})
    if not doc or doc.get("payment_rail") != "b2c_stripe":
        return
    property_id = doc.get("property_id")
    if not property_id or doc.get("saved_to_property_id"):
        return
    prop = await db.properties.find_one(
        {"id": property_id, "is_private_listing": True, "owner_user_id": doc.get("user_id")},
        {"_id": 0, "photos": 1},
    )
    if prop is None:
        logger.warning("b2c staging auto-save: listing missing job=%s pid=%s", job_id, property_id)
        return
    source_bytes, style_key = await _fetch_variant_bytes(doc, 0)
    wm = "Svuotamento virtuale OMNIA" if doc.get("mode") == "empty" else "Render virtuale OMNIA"
    processed = await asyncio.to_thread(
        _apply_watermark, source_bytes, wm, MAX_PHOTO_WIDTH,
    )
    b64 = base64.b64encode(processed).decode("ascii")
    photos = prop.get("photos") or []
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
    new_photo = {
        "id": str(uuid4()),
        "url": f"data:image/jpeg;base64,{b64}",
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
    logger.info("b2c staging auto-saved job=%s → property=%s photo=%s", job_id, property_id, new_photo["id"])


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
    room_type: str = "living",
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
        raise HTTPException(status_code=400, detail="listing_has_no_photos")

    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    used = await db.virtual_staging_jobs.count_documents({
        "user_id": user_id,
        "payment_rail": "b2c_preview",
        "created_at": {"$gte": start.isoformat()},
    })
    if used >= 3:
        raise HTTPException(status_code=429, detail={
            "error": "preview_daily_cap",
            "message": "Hai raggiunto il limite di 3 anteprime staging al giorno.",
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
        "room_type": room_type,
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
    pay_room = (purchase.get("room_type") or "bedroom").strip() or "bedroom"
    if pay_style not in STYLES:
        pay_style = "modern"
    if pay_room not in ROOM_TYPES:
        pay_room = "bedroom"
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
def _mask_url_from_entry(entry: Any) -> Optional[str]:
    if isinstance(entry, dict):
        u = entry.get("url")
        return str(u) if u else None
    if isinstance(entry, str) and entry.strip():
        return entry.strip()
    return None


def _white_ratio(mask_l: Image.Image) -> float:
    """Fraction of pixels that are 'inpaint' (near-white) in an L mask."""
    hist = mask_l.histogram()
    # L histogram length 256; count bins > 127 as white
    white = sum(hist[128:])
    total = mask_l.size[0] * mask_l.size[1]
    return (white / total) if total else 0.0


def merge_furniture_masks_from_images(masks: List[Image.Image]) -> Image.Image:
    """OR mid-sized SAM masks into one furniture mask (pure helper, unit-tested)."""
    if not masks:
        raise RuntimeError("no masks to merge")
    w, h = masks[0].size
    scored: List[tuple[Image.Image, float]] = []
    for im in masks:
        if im.mode != "L":
            im = im.convert("L")
        if im.size != (w, h):
            im = im.resize((w, h), Image.Resampling.NEAREST)
        scored.append((im, _white_ratio(im)))

    keep = [im for im, a in scored if _MASK_AREA_MIN <= a <= _MASK_AREA_MAX]
    if not keep:
        # Fallback: drop wall-sized (>45%) then take largest remaining up to 8
        ranked = sorted(
            [(im, a) for im, a in scored if a <= 0.45],
            key=lambda x: x[1],
            reverse=True,
        )
        keep = [im for im, _ in ranked[:8]]
    if not keep:
        keep = [im for im, _ in sorted(scored, key=lambda x: x[1], reverse=True)[:5]]

    from PIL import ImageChops, ImageFilter

    merged = Image.new("L", (w, h), 0)
    for im in keep:
        bw = im.point(lambda p: 255 if p > 127 else 0)
        merged = ImageChops.lighter(merged, bw)
    # Soft edge so Flux covers furniture silhouettes cleanly
    merged = merged.filter(ImageFilter.MaxFilter(5))
    return merged


async def _upload_pil_mask(mask: Image.Image) -> str:
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        mask.save(tmp, format="PNG")
        tmp_path = tmp.name
    try:
        return await asyncio.to_thread(fal_client.upload_file, tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


async def _merge_furniture_mask_urls(individuals: List[Any]) -> str:
    """Download individual SAM masks, merge mid-sized ones, re-upload to fal."""
    urls = []
    for entry in individuals[:_MASK_MERGE_CAP]:
        u = _mask_url_from_entry(entry)
        if u:
            urls.append(u)
    if len(urls) < 2:
        raise RuntimeError("need ≥2 individual masks to merge")

    images: List[Image.Image] = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for u in urls:
            resp = await client.get(u)
            resp.raise_for_status()
            images.append(Image.open(io.BytesIO(resp.content)).convert("L"))

    merged = merge_furniture_masks_from_images(images)
    return await _upload_pil_mask(merged)


def _bbox_iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if inter <= 0:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    den = area_a + area_b - inter
    return inter / den if den else 0.0


def nms_bboxes(
    items: List[tuple[float, tuple[float, float, float, float], str]],
    iou_thresh: float = 0.45,
) -> List[tuple[float, tuple[float, float, float, float], str]]:
    """NMS on (area_ratio, abs_box, label) sorted by area desc — unit-tested."""
    ranked = sorted(items, key=lambda x: -x[0])
    kept: List[tuple[float, tuple[float, float, float, float], str]] = []
    for it in ranked:
        if any(_bbox_iou(it[1], k[1]) > iou_thresh for k in kept):
            continue
        kept.append(it)
    return kept


async def _florence_furniture_boxes(image_url: str) -> List[dict]:
    """Detect furniture via Florence-2 (one label per call, then NMS)."""
    async def _one(label: str) -> List[tuple[dict, str]]:
        handler = await fal_client.submit_async(
            MODEL_FLORENCE_DET,
            arguments={"image_url": image_url, "text_input": label},
        )
        det = await handler.get()
        boxes = ((det.get("results") or {}).get("bboxes") or [])
        return [(b, label) for b in boxes if isinstance(b, dict)]

    batches = await asyncio.gather(*[_one(lab) for lab in FURNITURE_DETECT_LABELS], return_exceptions=True)
    raw: List[tuple[dict, str]] = []
    for batch in batches:
        if isinstance(batch, Exception):
            logger.warning("Florence label failed: %s", batch)
            continue
        raw.extend(batch)
    if not raw:
        return []

    # Need image size for area filter — fetch once
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(image_url)
        resp.raise_for_status()
        w, h = Image.open(io.BytesIO(resp.content)).size
    total = float(w * h) or 1.0

    items: List[tuple[float, tuple[float, float, float, float], str]] = []
    for b, lab in raw:
        x, y, bw, bh = float(b.get("x", 0)), float(b.get("y", 0)), float(b.get("w", 0)), float(b.get("h", 0))
        if bw <= 1 or bh <= 1:
            continue
        area = (bw * bh) / total
        # Drop noise + whole-frame false positives (seen as "gym machine" @ 0.99)
        if area < 0.008 or area > _MASK_BOX_AREA_MAX:
            continue
        items.append((area, (x, y, x + bw, y + bh), lab))

    kept = nms_bboxes(items, iou_thresh=0.45)
    out = []
    for area, (x1, y1, x2, y2), lab in kept:
        out.append({
            "label": lab,
            "area": area,
            "x_min": int(max(0, x1)),
            "y_min": int(max(0, y1)),
            "x_max": int(min(w - 1, x2)),
            "y_max": int(min(h - 1, y2)),
        })
    return out


async def _sam2_mask_from_boxes(image_url: str, boxes: List[dict]) -> str:
    """SAM2 box prompts → binary furniture mask uploaded to fal."""
    if not boxes:
        raise RuntimeError("no boxes for SAM2")
    box_prompts = [
        {
            "x_min": b["x_min"],
            "y_min": b["y_min"],
            "x_max": b["x_max"],
            "y_max": b["y_max"],
        }
        for b in boxes
    ]
    handler = await fal_client.submit_async(
        MODEL_SAM2_BOX,
        arguments={
            "image_url": image_url,
            "box_prompts": box_prompts,
            "output_format": "png",
            "apply_mask": False,
        },
    )
    result = await handler.get()
    img = result.get("image") or {}
    url = img.get("url") if isinstance(img, dict) else None
    if not url:
        raise RuntimeError(f"SAM2 box mask missing (keys: {list(result.keys())})")
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        gray = Image.open(io.BytesIO(resp.content)).convert("L")
    mask = gray.point(lambda p: 255 if p > 20 else 0)
    if _white_ratio(mask) > 0.85:
        mask = Image.eval(mask, lambda p: 255 - p)
    from PIL import ImageFilter

    mask = mask.filter(ImageFilter.MaxFilter(7))
    if _white_ratio(mask) < 0.02:
        raise RuntimeError("SAM2 box mask nearly empty")
    return await _upload_pil_mask(mask)


async def _stage_sam2_mask(image_url: str, *, for_furniture: bool = True) -> str:
    """Build inpaint/erase mask.

    For furniture removal (empty/reverse): Florence-2 detect → SAM2 boxes → mask.
    Fallback: auto-segment mid-sized merge (never individual_masks[0] alone).
    For standard furnish: prefer combined_mask from auto-segment.
    """
    if for_furniture:
        try:
            boxes = await _florence_furniture_boxes(image_url)
            if boxes:
                logger.info("Florence furniture boxes=%s labels=%s", len(boxes), [b["label"] for b in boxes])
                return await _sam2_mask_from_boxes(image_url, boxes)
            logger.warning("Florence returned no furniture boxes — SAM2 auto-segment fallback")
        except Exception as e:
            logger.warning("Florence+SAM2 box mask failed, falling back: %s", e)

    handler = await fal_client.submit_async(
        MODEL_SAM2,
        arguments={
            "image_url": image_url,
            "points_per_side": 48,
            "pred_iou_thresh": 0.7,
            "stability_score_thresh": 0.85,
            "output_format": "png",
            "min_mask_region_area": 50,
        },
    )
    result = await handler.get()
    individuals = result.get("individual_masks") or []
    combined = result.get("combined_mask")

    if for_furniture and isinstance(individuals, list) and len(individuals) >= 2:
        try:
            return await _merge_furniture_mask_urls(individuals)
        except Exception as e:
            logger.warning("SAM2 furniture-mask merge failed, falling back: %s", e)

    mask_url = _mask_url_from_entry(combined)
    if not mask_url and isinstance(individuals, list) and individuals:
        mask_url = _mask_url_from_entry(individuals[0])
    if not mask_url:
        raise RuntimeError(f"SAM2 returned no mask (keys: {list(result.keys())})")
    return mask_url


async def _bria_erase(image_url: str, mask_url: str) -> str:
    """Bria eraser — purpose-built object removal (far fewer architecture hallucinations than Flux)."""
    handler = await fal_client.submit_async(
        MODEL_BRIA_ERASER,
        arguments={
            "image_url": image_url,
            "mask_url": mask_url,
            "mask_type": "automatic",
        },
    )
    result = await handler.get()
    image = result.get("image")
    if isinstance(image, dict) and image.get("url"):
        return image["url"]
    if isinstance(image, str) and image:
        return image
    raise RuntimeError(f"Bria eraser returned no image (keys: {list(result.keys())})")


async def _ideogram_erase(image_url: str, mask_url: str) -> str:
    """Ideogram object removal — best clean empty results in OMNIA A/B on cluttered rooms."""
    handler = await fal_client.submit_async(
        MODEL_IDEOGRAM_ERASE,
        arguments={"image_url": image_url, "mask_url": mask_url},
    )
    result = await handler.get()
    image = result.get("image")
    if isinstance(image, dict) and image.get("url"):
        return image["url"]
    if isinstance(image, str) and image:
        return image
    raise RuntimeError(f"Ideogram erase returned no image (keys: {list(result.keys())})")


async def _fal_object_removal(image_url: str, mask_url: str) -> str:
    """fal-ai/object-removal/mask — alternative eraser when Ideogram invents walls."""
    handler = await fal_client.submit_async(
        MODEL_FAL_OBJECT_REMOVAL,
        arguments={
            "image_url": image_url,
            "mask_url": mask_url,
            "model": "best_quality",
            "mask_expansion": 5,
        },
    )
    result = await handler.get()
    images = result.get("images") or []
    if images and isinstance(images[0], dict) and images[0].get("url"):
        return images[0]["url"]
    raise RuntimeError(f"fal object-removal returned no image (keys: {list(result.keys())})")


async def _erase_once(image_url: str, mask_url: str) -> tuple[str, str, float]:
    """Prefer Ideogram, then fal object-removal, then Bria. Returns (url, engine, cost)."""
    try:
        return await _ideogram_erase(image_url, mask_url), "ideogram", COST_IDEOGRAM
    except Exception as e1:
        logger.warning("Ideogram erase failed (%s) — fal object-removal", e1)
        try:
            return await _fal_object_removal(image_url, mask_url), "fal_orm", COST_IDEOGRAM
        except Exception as e2:
            logger.warning("fal object-removal failed (%s) — Bria fallback", e2)
            return await _bria_erase(image_url, mask_url), "bria", COST_BRIA


async def _architecture_keep_mask(image_url: str) -> Image.Image:
    """Binary mask of doors/windows that must stay (prevents inventing walls over openings)."""
    async def _one(label: str) -> List[dict]:
        handler = await fal_client.submit_async(
            MODEL_FLORENCE_DET,
            arguments={"image_url": image_url, "text_input": label},
        )
        det = await handler.get()
        return ((det.get("results") or {}).get("bboxes") or [])

    batches = await asyncio.gather(
        *[_one(lab) for lab in ARCHITECTURE_KEEP_LABELS],
        return_exceptions=True,
    )
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(image_url)
        resp.raise_for_status()
        w, h = Image.open(io.BytesIO(resp.content)).size
    keep = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(keep)
    total = float(w * h) or 1.0
    for batch in batches:
        if isinstance(batch, Exception):
            continue
        for b in batch:
            if not isinstance(b, dict):
                continue
            x, y, bw, bh = float(b.get("x", 0)), float(b.get("y", 0)), float(b.get("w", 0)), float(b.get("h", 0))
            if bw <= 1 or bh <= 1:
                continue
            area = (bw * bh) / total
            if area < 0.015 or area > 0.45:
                continue
            pad = 4
            draw.rectangle(
                [max(0, x - pad), max(0, y - pad), min(w - 1, x + bw + pad), min(h - 1, y + bh + pad)],
                fill=255,
            )
    from PIL import ImageFilter

    # Soft keep: erode so furniture overlapping a door frame can still be erased.
    if keep.getbbox():
        keep = keep.filter(ImageFilter.MinFilter(9))
    return keep


async def _padded_box_mask_url(box: dict, image_url: str, *, pad: int = 12) -> str:
    """Build a padded rectangular erase mask matching the current image size."""
    from PIL import ImageFilter

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(image_url)
        resp.raise_for_status()
        w, h = Image.open(io.BytesIO(resp.content)).size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rectangle(
        [
            max(0, int(box["x_min"]) - pad),
            max(0, int(box["y_min"]) - pad),
            min(w - 1, int(box["x_max"]) + pad),
            min(h - 1, int(box["y_max"]) + pad),
        ],
        fill=255,
    )
    mask = mask.filter(ImageFilter.MaxFilter(5))
    return await _upload_pil_mask(mask)


async def _erase_mask_url(
    box: dict,
    image_url: str,
    *,
    keep: Optional[Image.Image] = None,
    pad: int = 6,
) -> str:
    """SAM2 silhouette mask (preferred) with architecture keep subtracted; box fallback."""
    from PIL import ImageChops, ImageFilter, ImageOps

    mask: Optional[Image.Image] = None
    try:
        sam_url = await _sam2_mask_from_boxes(image_url, [box])
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(sam_url)
            resp.raise_for_status()
            gray = Image.open(io.BytesIO(resp.content)).convert("L")
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(image_url)
            resp.raise_for_status()
            w, h = Image.open(io.BytesIO(resp.content)).size
        if gray.size != (w, h):
            gray = gray.resize((w, h))
        mask = gray.point(lambda p: 255 if p > 20 else 0)
        if _white_ratio(mask) > 0.85:
            mask = ImageOps.invert(mask)
        mask = mask.filter(ImageFilter.MaxFilter(5))
    except Exception as e:
        logger.warning("SAM2 erase mask failed (%s) — padded box", e)
        # Fall through to padded box below
        mask = None

    if mask is None:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(image_url)
            resp.raise_for_status()
            w, h = Image.open(io.BytesIO(resp.content)).size
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        draw.rectangle(
            [
                max(0, int(box["x_min"]) - pad),
                max(0, int(box["y_min"]) - pad),
                min(w - 1, int(box["x_max"]) + pad),
                min(h - 1, int(box["y_max"]) + pad),
            ],
            fill=255,
        )
        mask = mask.filter(ImageFilter.MaxFilter(5))

    if keep is not None and keep.size == mask.size and keep.getbbox():
        mask = ImageChops.subtract(mask, keep)
    if _white_ratio(mask) < 0.002:
        # Keep ate the whole mask — fall back to tiny padded core without keep
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(image_url)
            resp.raise_for_status()
            w, h = Image.open(io.BytesIO(resp.content)).size
        mask = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask)
        cx1 = int(box["x_min"]) + max(2, (int(box["x_max"]) - int(box["x_min"])) // 8)
        cy1 = int(box["y_min"]) + max(2, (int(box["y_max"]) - int(box["y_min"])) // 8)
        cx2 = int(box["x_max"]) - max(2, (int(box["x_max"]) - int(box["x_min"])) // 8)
        cy2 = int(box["y_max"]) - max(2, (int(box["y_max"]) - int(box["y_min"])) // 8)
        draw.rectangle([cx1, cy1, cx2, cy2], fill=255)

    return await _upload_pil_mask(mask)


async def _doorway_brightness(image_url: str, keep: Image.Image) -> Optional[float]:
    """Mean luminance inside architecture-keep region (used to detect wall invention)."""
    if keep is None or not keep.getbbox():
        return None
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(image_url)
        resp.raise_for_status()
        im = Image.open(io.BytesIO(resp.content)).convert("L")
    if im.size != keep.size:
        im = im.resize(keep.size)
    import numpy as np

    arr = np.asarray(im, dtype=np.float32)
    m = np.asarray(keep) > 127
    if not m.any():
        return None
    return float(arr[m].mean())


def _sort_erase_boxes(boxes: List[dict]) -> List[dict]:
    order = {lab: i for i, lab in enumerate(ERASE_LABEL_ORDER)}

    def _key(b: dict) -> tuple:
        return (order.get(b.get("label") or "", 99), -float(b.get("area") or 0))

    return sorted(boxes, key=_key)


async def _evf_furniture_union_mask(
    image_url: str,
    *,
    keep: Optional[Image.Image] = None,
) -> tuple[Optional[str], float, float]:
    """Build furniture mask via EVF-SAM multi-prompt union (architecture subtracted).

    Returns (mask_url_or_None, cost_usd, white_ratio).
    """
    from PIL import ImageChops, ImageFilter
    import numpy as np

    async def _one(prompt: str) -> Optional[Image.Image]:
        try:
            handler = await fal_client.submit_async(
                MODEL_EVF_SAM,
                arguments={
                    "prompt": prompt,
                    "negative_prompt": EVF_ARCHITECTURE_NEGATIVE,
                    "image_url": image_url,
                    "mask_only": True,
                    "semantic_type": True,
                    "fill_holes": True,
                    "expand_mask": 3,
                },
            )
            result = await handler.get()
            img = result.get("image") or {}
            u = img.get("url") if isinstance(img, dict) else None
            if not u:
                return None
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(u)
                resp.raise_for_status()
                return Image.open(io.BytesIO(resp.content)).convert("L")
        except Exception as e:
            logger.warning("EVF-SAM prompt failed (%s): %s", prompt[:40], e)
            return None

    masks = await asyncio.gather(*[_one(p) for p in EVF_FURNITURE_PROMPTS])
    cost = COST_EVF_SAM * len(EVF_FURNITURE_PROMPTS)
    valid = [m for m in masks if isinstance(m, Image.Image)]
    if not valid:
        return None, cost, 0.0

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(image_url)
        resp.raise_for_status()
        w, h = Image.open(io.BytesIO(resp.content)).size

    union = Image.new("L", (w, h), 0)
    for m in valid:
        if m.size != (w, h):
            m = m.resize((w, h))
        m = m.point(lambda p: 255 if p > 127 else 0)
        union = ImageChops.lighter(union, m)
    union = union.filter(ImageFilter.MaxFilter(5))
    if keep is not None and keep.size == union.size and keep.getbbox():
        union = ImageChops.subtract(union, keep)
    wr = float((np.asarray(union) > 127).mean())
    if wr < 0.02:
        return None, cost, wr
    return await _upload_pil_mask(union), cost, wr


async def _sequential_furniture_erase(image_url: str) -> tuple[str, float, dict]:
    """Semantic EVF-SAM pass + Florence/SAM2 remnant erase, arch-protected.

    Inspired by casalimpia (furniture vs architecture split) but via fal EVF-SAM
    instead of self-hosted OneFormer — no local GPU required.
    """
    cost = 0.0
    engines: List[str] = []
    erased_labels: List[str] = []
    wall_retries = 0
    evf_ratio = 0.0

    keep = await _architecture_keep_mask(image_url)
    cost += COST_FLORENCE  # billed roughly as one Florence batch
    bright0 = await _doorway_brightness(image_url, keep)

    url = image_url
    # Pass 0 — semantic furniture union (one Ideogram erase on whole mask)
    try:
        evf_mask_url, evf_cost, evf_ratio = await _evf_furniture_union_mask(image_url, keep=keep)
        cost += evf_cost
        if evf_mask_url:
            new_url, eng, c = await _erase_once(url, evf_mask_url)
            cost += c
            engines.append(f"{eng}_evf")
            erased_labels.append(f"evf_union:{evf_ratio:.2f}")
            if bright0 is not None:
                bright1 = await _doorway_brightness(new_url, keep)
                if bright1 is not None and abs(bright1 - bright0) / max(bright0, 1.0) > 0.18:
                    wall_retries += 1
                    logger.warning(
                        "EVF erase wall-invention suspected bright %.1f→%.1f — keep prior",
                        bright0, bright1,
                    )
                    erased_labels[-1] = "evf_union:skip_wall"
                else:
                    url = new_url
    except Exception as e:
        logger.warning("EVF semantic erase skipped: %s", e)

    async def _erase_box(url: str, box: dict, *, pad: int, tag: str) -> str:
        nonlocal cost, wall_retries
        mask_url = await _erase_mask_url(box, url, keep=keep, pad=pad)
        new_url, eng, c = await _erase_once(url, mask_url)
        cost += c
        engines.append(f"{eng}{tag}")
        erased_labels.append(f"{box.get('label') or '?'}{tag}")
        # Detect wall-invention over openings: keep-region luminance swings hard
        # (dark hallway→bright wall OR bright doorway→filled wall).
        if bright0 is not None and float(box.get("area") or 0) >= 0.08:
            bright1 = await _doorway_brightness(new_url, keep)
            if bright1 is not None:
                delta = abs(bright1 - bright0) / max(bright0, 1.0)
                if delta > 0.18:
                    wall_retries += 1
                    logger.warning(
                        "erase wall-invention suspected label=%s bright %.1f→%.1f (Δ=%.0f%%) — retry fal_orm",
                        box.get("label"), bright0, bright1, delta * 100,
                    )
                    try:
                        alt = await _fal_object_removal(url, mask_url)
                        cost += COST_IDEOGRAM
                        engines.append("fal_orm_retry")
                        bright2 = await _doorway_brightness(alt, keep)
                        if bright2 is not None and abs(bright2 - bright0) < abs(bright1 - bright0):
                            return alt
                    except Exception as e:
                        logger.warning("fal_orm retry failed: %s", e)
                    # Prefer original over invented wall
                    erased_labels[-1] = f"{box.get('label')}:skip_wall"
                    return url
        return new_url

    boxes = await _florence_furniture_boxes(image_url)
    cost += COST_FLORENCE
    boxes = _sort_erase_boxes(boxes)[:_ERASE_PASS1_MAX]
    url = image_url
    for box in boxes:
        url = await _erase_box(url, box, pad=6, tag="")

    # Pass 2/3 — remnants (strict area band avoids whole-frame false positives)
    boxes2: List[dict] = []
    boxes3: List[dict] = []
    for pass_idx, (cap, pad, store) in enumerate(
        ((_ERASE_PASS2_MAX, 8, "boxes2"), (_ERASE_PASS3_MAX, 10, "boxes3")),
        start=2,
    ):
        found = await _florence_furniture_boxes(url)
        cost += COST_FLORENCE
        found = [b for b in found if 0.008 <= float(b.get("area") or 0) <= 0.30]
        found = _sort_erase_boxes(found)[:cap]
        if store == "boxes2":
            boxes2 = found
        else:
            boxes3 = found
        if not found:
            break
        for box in found:
            url = await _erase_box(url, box, pad=pad, tag=f":p{pass_idx}")

    # Final sweep — soft clutter Florence often leaves after big furniture is gone
    leftover = await _florence_furniture_boxes(url)
    cost += COST_FLORENCE
    soft = {"rug", "carpet", "picture frame", "hanging decoration", "plant", "curtain"}
    leftover = [
        b for b in leftover
        if (b.get("label") in soft) and 0.005 <= float(b.get("area") or 0) <= 0.25
    ]
    leftover = _sort_erase_boxes(leftover)[:4]
    for box in leftover:
        url = await _erase_box(url, box, pad=12, tag=":sweep")

    meta = {
        "engine": "+".join(dict.fromkeys(engines)) or "none",
        "erased": erased_labels,
        "pass1": len(boxes),
        "pass2": len(boxes2),
        "pass3": len(boxes3),
        "sweep": len(leftover),
        "wall_retries": wall_retries,
        "arch_keep": bool(keep.getbbox()),
    }
    return url, cost, meta


_STYLE_EN = {
    "modern": "modern minimalist",
    "classic": "classic elegant Italian",
    "scandi": "scandinavian",
    "industrial": "industrial loft",
    "luxury": "luxury designer",
}


def _staging_lora_prompt(style: str, room_type: str, crm_fragment: Optional[str] = None) -> str:
    sk = style if style in STYLES else "modern"
    rt = room_type if room_type in ROOM_TYPES else "living"
    room_en = {
        "living": "living room",
        "bedroom": "bedroom",
        "kitchen": "kitchen",
        "dining": "dining room",
        "bathroom": "bathroom",
        "office": "home office",
    }.get(rt, "living room")
    room_bits = ROOM_TYPES.get(rt, ROOM_TYPES["living"])
    style_en = _STYLE_EN.get(sk, "modern")
    base = (
        f"Furnish this empty {room_en} with {style_en} furniture and decor: {room_bits}. "
        "Keep existing walls, doors, windows, floor material and ceiling completely unchanged. "
        "No surreal objects, no melting furniture, no distorted geometry. "
        "Photorealistic real estate listing photograph, natural light, sharp details."
    )
    if crm_fragment:
        return f"{base} {crm_fragment}"
    return base


async def _apartment_stage(
    image_url: str,
    prompt: str,
    *,
    num_images: int = 1,
    lora_scale: float = 0.95,
) -> List[str]:
    """Purpose-built Flux 2 apartment-staging LoRA (preserves room geometry)."""
    handler = await fal_client.submit_async(
        MODEL_APARTMENT_STAGING,
        arguments={
            "image_urls": [image_url],
            "prompt": prompt,
            "guidance_scale": 2.5,
            "num_inference_steps": 40,
            "lora_scale": lora_scale,
            "output_format": "png",
            "num_images": max(1, min(int(num_images), 4)),
            "enable_safety_checker": True,
        },
    )
    result = await handler.get()
    images = result.get("images") or []
    urls = [im.get("url") for im in images if isinstance(im, dict) and im.get("url")]
    if not urls:
        raise RuntimeError(f"Apartment staging returned no images (keys: {list(result.keys())})")
    return urls


async def _flux_inpaint(
    image_url: str,
    mask_url: str,
    prompt: str,
    num_images: int = 1,
    *,
    strength: float = 0.85,
    guidance_scale: float = 3.5,
    num_inference_steps: int = 28,
) -> List[str]:
    handler = await fal_client.submit_async(
        MODEL_FLUX_INPAINT,
        arguments={
            "image_url": image_url,
            "mask_url": mask_url,
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
            "strength": strength,
            "num_images": num_images,
            "enable_safety_checker": True,
        },
    )
    result = await handler.get()
    images = result.get("images") or []
    if not images:
        raise RuntimeError(f"Flux returned no images (keys: {list(result.keys())})")
    return [im.get("url") for im in images if im.get("url")]


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


async def _stage_upscale(image_url: str) -> str:
    handler = await fal_client.submit_async(
        MODEL_UPSCALE,
        arguments={"image_url": image_url, "scale": 4, "model": "RealESRGAN_x4plus"},
    )
    result = await handler.get()
    return (result.get("image") or {}).get("url") or result.get("image_url")


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
    total_cost = 0.0

    try:
        src = await _resolve_image_url_for_fal(src_raw)
        if src != src_raw:
            await _mark_root({"source_url_fal": src})
    except Exception as e:
        await _fail("sam2_mask", "Resolve source", e)
        return

    # CRM-aware prompt (best-effort, silent)
    crm_fragment = None
    if doc.get("property_id"):
        crm_fragment, crm_summary = await _crm_prompt_fragment(db, doc.get("agency_id"), doc["property_id"])
        if crm_summary:
            await _mark_root({"crm_context": crm_summary})

    # Stage 1 — detect. Empty/reverse: Florence is billed inside sequential erase.
    # Standard: SAM auto-segment kept for Flux fallback path only.
    mask_url: Optional[str] = None
    try:
        t0 = monotonic()
        await _mark_stage("sam2_mask", {"status": "running"})
        if mode in ("reverse", "empty"):
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
            total_cost += COST_SAM2
    except Exception as e:
        await _fail("sam2_mask", "SAM2", e)
        return

    # Stage 1b — sequential Ideogram/Bria erase (empty / reverse only)
    base_image = src
    if mode in ("reverse", "empty"):
        try:
            t0 = monotonic()
            await _mark_stage("furniture_removal", {"status": "running"})
            base_image, removal_cost, erase_meta = await _sequential_furniture_erase(src)
            await _mark_root({"erase_meta": erase_meta})
            await _mark_stage("furniture_removal", {
                "status": "done",
                "duration_ms": int((monotonic() - t0) * 1000),
                "cost_usd": round(removal_cost, 4),
                "engine": erase_meta.get("engine"),
                "note": f"erased={','.join(erase_meta.get('erased') or [])}"[:280],
            })
            total_cost += removal_cost
        except Exception as e:
            await _fail("furniture_removal", "Rimozione arredo", e)
            return

    # Stage 2 — apartment-staging LoRA (furnish). Skipped for empty-only mode.
    if mode == "empty":
        variants = [{"url": base_image, "style": "empty", "upscaled": False}]
        await _mark_stage("flux_inpaint", {
            "status": "done", "duration_ms": 0, "cost_usd": 0,
            "note": "skipped_empty_mode",
            "engine": "none",
        })
    else:
        try:
            t0 = monotonic()
            await _mark_stage("flux_inpaint", {"status": "running"})
            style_keys = (
                (doc.get("styles_list") or DEFAULT_MULTI_STYLES)[:num_variants]
                if variant_mode == "multi_style"
                else [doc.get("style") or "modern"]
            )
            variants = []
            engine_used = "apartment_staging_lora"
            for sk in style_keys:
                prompt = _staging_lora_prompt(sk, doc.get("room_type") or "living", crm_fragment)
                try:
                    urls = await _apartment_stage(base_image, prompt, num_images=1 if variant_mode == "multi_style" else num_variants)
                except Exception as lora_err:
                    logger.warning("Apartment staging LoRA failed (%s) — Flux inpaint fallback", lora_err)
                    engine_used = "flux_inpaint_fallback"
                    if not mask_url:
                        mask_url = await _stage_sam2_mask(base_image, for_furniture=True)
                    urls = await _flux_inpaint(
                        base_image, mask_url, _build_prompt(sk, doc.get("room_type") or "living", crm_fragment),
                        num_images=1 if variant_mode == "multi_style" else num_variants,
                    )
                variants.extend({"url": u, "style": sk, "upscaled": False} for u in urls)
                if variant_mode != "multi_style":
                    break
            if not variants:
                raise RuntimeError("Nessuna variante staging generata")
            stage_cost = (COST_STAGING_LORA if engine_used.startswith("apartment") else COST_FLUX) * len(variants)
            await _mark_stage("flux_inpaint", {
                "status": "done",
                "duration_ms": int((monotonic() - t0) * 1000),
                "cost_usd": round(stage_cost, 4),
                "engine": engine_used,
            })
            total_cost += stage_cost
        except Exception as e:
            await _fail("flux_inpaint", "Staging", e)
            return

    # Stage 3 — upscale only for Flux-inpaint fallback (ESRGAN amplifies erase seams).
    t0 = monotonic()
    await _mark_stage("upscale", {"status": "running"})
    furn_engine = ""
    try:
        stage_doc = await db.virtual_staging_jobs.find_one({"id": job_id}, {"stages": 1})
        furn_stage = next(
            (s for s in (stage_doc or {}).get("stages") or [] if s.get("name") == "flux_inpaint"),
            {},
        )
        furn_engine = furn_stage.get("engine") or ""
    except Exception:
        furn_engine = ""
    if mode == "empty" or not furn_engine.startswith("flux_inpaint"):
        await _mark_stage("upscale", {
            "status": "done", "duration_ms": 0, "cost_usd": 0,
            "note": "skipped_empty_mode" if mode == "empty" else "skipped_apartment_lora",
        })
    else:
        async def _up(v: dict) -> dict:
            try:
                url = await _stage_upscale(v["url"])
                return {**v, "url": url or v["url"], "upscaled": bool(url)}
            except Exception as e:
                logger.warning("Upscale failed for a variant: %s", e)
                return v

        variants = list(await asyncio.gather(*[_up(v) for v in variants]))
        upscaled_n = sum(1 for v in variants if v.get("upscaled"))
        up_cost = COST_UPSCALE * upscaled_n
        await _mark_stage("upscale", {
            "status": "done" if upscaled_n else "failed",
            "duration_ms": int((monotonic() - t0) * 1000),
            "cost_usd": round(up_cost, 4),
        })
        total_cost += up_cost

    # B2C free preview: persist to /api/media so SellPage img is same-origin + smaller
    try:
        variants = await _persist_b2c_preview_variants(job_id, db, variants)
    except Exception:
        logger.exception("b2c preview persist failed job=%s", job_id)

    await _mark_root({
        "status": "done",
        "variants": variants,
        "variant_url": variants[0]["url"] if variants else None,
        "cost_total_usd": round(total_cost, 4),
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


def _photo_caption(style_key: str, room_type: str) -> str:
    style_label = STYLES.get(style_key, {}).get("label", style_key)
    room_label = ROOM_LABELS.get(room_type, room_type)
    return f"Render virtuale OMNIA · {room_label} {style_label}"


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
    """Watermarked + resized (≤1600px) base64 data URL — used to persist the render as property photo."""
    db = Database.get()
    doc = await db.virtual_staging_jobs.find_one({"id": job_id, "user_id": user["id"]})
    if not doc:
        raise HTTPException(404, "Job non trovato")
    source_bytes, style_key = await _fetch_variant_bytes(doc, variant_index)
    processed = await asyncio.to_thread(_apply_watermark, source_bytes, "Render virtuale OMNIA", MAX_PHOTO_WIDTH)
    b64 = base64.b64encode(processed).decode("ascii")
    return {
        "data_url": f"data:image/jpeg;base64,{b64}",
        "caption": _photo_caption(style_key, doc.get("room_type", "living")),
    }


@router.post("/jobs/{job_id}/save-to-property")
async def save_variant_to_property(
    job_id: str,
    body: SaveToPropertyBody,
    user=Depends(get_current_user),
) -> Dict[str, Any]:
    """Persists a variant as a new photo of the linked property (base64, watermarked)."""
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
    b64 = base64.b64encode(processed).decode("ascii")

    photos = prop.get("photos") or []
    new_photo = {
        "id": str(uuid4()),
        "url": f"data:image/jpeg;base64,{b64}",
        "caption": _photo_caption(style_key, doc.get("room_type", "living")),
        "order": len(photos),
        "is_cover": len(photos) == 0,
    }
    await db.properties.update_one(
        {"id": property_id},
        {"$push": {"photos": new_photo}, "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    await db.virtual_staging_jobs.update_one(
        {"id": job_id}, {"$set": {"saved_to_property_id": property_id}}
    )
    return {"ok": True, "photo_id": new_photo["id"], "photo_count": len(photos) + 1}


@router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, user=Depends(get_current_user)) -> Dict[str, bool]:
    db = Database.get()
    res = await db.virtual_staging_jobs.delete_one({"id": job_id, "user_id": user["id"]})
    if res.deleted_count == 0:
        raise HTTPException(404, "Job non trovato")
    return {"ok": True}
