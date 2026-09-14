"""OMNIA — M5.S4 Virtual Staging (Sprint 2: reverse staging + varianti parallele + CRM-aware).

Reference: DECISIONS.md D-033.

Pipeline:
  Stage 1 — SAM 2 segmentation → maschera stanza (fal-ai/sam2/auto-segment)
  Stage 1b (reverse) — Flux inpaint "empty room" → rimozione arredo esistente
  Stage 2 — Flux inpainting → arredamento (1-4 varianti parallele, same-style o multi-style)
  Stage 3 — Real-ESRGAN 4x upscale (parallelo per variante)

Prompt CRM-aware: se il job è collegato a un immobile, Gemini arricchisce il prompt
con zona/prezzo/target buyer. Watermark "Render virtuale OMNIA" server-side.
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

logger = logging.getLogger("omnia.staging")
router = APIRouter(prefix="/staging", tags=["virtual-staging"])

MODEL_SAM2 = "fal-ai/sam2/auto-segment"
MODEL_FLUX_INPAINT = "fal-ai/flux-lora/inpainting"
MODEL_UPSCALE = "fal-ai/esrgan"

MAX_UPLOAD_MB = 12
ALLOWED_MIME = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
SOFT_RATE_LIMIT_USER_HOUR = 20   # renders/ora/utente
SOFT_RATE_LIMIT_AGENCY_HOUR = 80  # renders/ora/agenzia
JOB_TTL_DAYS = 30
STALE_JOB_MINUTES = 10
MAX_PHOTO_WIDTH = 1600

COST_SAM2 = 0.001
COST_FLUX = 0.05
COST_UPSCALE = 0.005

# ─── Style catalog (prompts calibrated for real-estate rooms) ───
STYLES: Dict[str, Dict[str, str]] = {
    "modern": {
        "label": "Moderno",
        "prompt": "modern minimalist interior, neutral colors, clean lines, natural light, high-end contemporary furniture, wooden floor, professional interior photography",
    },
    "classic": {
        "label": "Classico",
        "prompt": "classic elegant italian interior, warm colors, traditional wooden furniture, curtains, chandelier, parquet flooring, refined atmosphere",
    },
    "scandi": {
        "label": "Scandinavo",
        "prompt": "scandinavian interior design, white walls, light wooden floor, minimalist furniture, cozy textiles, natural light, hygge atmosphere",
    },
    "industrial": {
        "label": "Industriale",
        "prompt": "industrial loft style, exposed brick, metal fixtures, concrete floor, leather sofa, edison bulbs, urban chic",
    },
    "luxury": {
        "label": "Luxury",
        "prompt": "luxury interior design, marble floor, designer furniture, gold accents, high ceilings, large windows, premium finishes",
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
    "blurry, low quality, deformed walls, weird perspective"
)

EMPTY_ROOM_PROMPT = (
    "completely empty room, bare walls, clean bare floor, no furniture, "
    "no objects, no decorations, no rugs, no lamps, vacant apartment, "
    "natural light, photorealistic, architectural photography"
)


# ─── Schemas ─────────────────────────────────────────────────────
class StagingGenerateBody(BaseModel):
    image_url: str = Field(..., description="Public URL of the source room photo")
    style: str = Field(default="modern")
    room_type: str = Field(default="living")
    property_id: Optional[str] = None
    mode: str = Field(default="standard", description="standard | reverse")
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
    api_key = os.environ.get("EMERGENT_LLM_KEY")
    if not api_key:
        return None, None
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage  # type: ignore

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


# ─── Pipeline stages ─────────────────────────────────────────────
async def _stage_sam2_mask(image_url: str) -> str:
    handler = await fal_client.submit_async(
        MODEL_SAM2,
        arguments={"image_url": image_url, "points_per_side": 32, "output_format": "png"},
    )
    result = await handler.get()
    masks = result.get("individual_masks") or result.get("combined_mask") or []
    if isinstance(masks, list) and masks:
        mask_url = masks[0].get("url") if isinstance(masks[0], dict) else masks[0]
    elif isinstance(masks, dict):
        mask_url = masks.get("url")
    else:
        mask_url = result.get("combined_mask", {}).get("url") if isinstance(result.get("combined_mask"), dict) else None
    if not mask_url:
        raise RuntimeError(f"SAM2 returned no mask (keys: {list(result.keys())})")
    return mask_url


async def _flux_inpaint(image_url: str, mask_url: str, prompt: str, num_images: int = 1) -> List[str]:
    handler = await fal_client.submit_async(
        MODEL_FLUX_INPAINT,
        arguments={
            "image_url": image_url,
            "mask_url": mask_url,
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
            "num_images": num_images,
            "enable_safety_checker": True,
        },
    )
    result = await handler.get()
    images = result.get("images") or []
    if not images:
        raise RuntimeError(f"Flux returned no images (keys: {list(result.keys())})")
    return [im.get("url") for im in images if im.get("url")]


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
    src = doc["source_url"]
    mode = doc.get("mode", "standard")
    variant_mode = doc.get("variant_mode", "same_style")
    num_variants = doc.get("num_variants", 1)
    total_cost = 0.0

    # CRM-aware prompt (best-effort, silent)
    crm_fragment = None
    if doc.get("property_id"):
        crm_fragment, crm_summary = await _crm_prompt_fragment(db, doc.get("agency_id"), doc["property_id"])
        if crm_summary:
            await _mark_root({"crm_context": crm_summary})

    # Stage 1: SAM 2 mask
    try:
        t0 = monotonic()
        await _mark_stage("sam2_mask", {"status": "running"})
        mask_url = await _stage_sam2_mask(src)
        await _mark_stage("sam2_mask", {
            "status": "done", "duration_ms": int((monotonic() - t0) * 1000), "cost_usd": COST_SAM2,
        })
        total_cost += COST_SAM2
    except Exception as e:
        await _fail("sam2_mask", "SAM2", e)
        return

    # Stage 1b (reverse): furniture removal
    base_image = src
    if mode == "reverse":
        try:
            t0 = monotonic()
            await _mark_stage("furniture_removal", {"status": "running"})
            emptied = await _flux_inpaint(src, mask_url, EMPTY_ROOM_PROMPT, num_images=1)
            base_image = emptied[0]
            await _mark_stage("furniture_removal", {
                "status": "done", "duration_ms": int((monotonic() - t0) * 1000), "cost_usd": COST_FLUX,
            })
            total_cost += COST_FLUX
        except Exception as e:
            await _fail("furniture_removal", "Rimozione arredo", e)
            return

    # Stage 2: Flux furnish — parallel variants
    try:
        t0 = monotonic()
        await _mark_stage("flux_inpaint", {"status": "running"})
        if variant_mode == "multi_style":
            style_keys = (doc.get("styles_list") or DEFAULT_MULTI_STYLES)[:num_variants]
            tasks = [
                _flux_inpaint(base_image, mask_url, _build_prompt(sk, doc["room_type"], crm_fragment), 1)
                for sk in style_keys
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            variants: List[dict] = []
            for sk, res in zip(style_keys, results):
                if isinstance(res, Exception):
                    logger.warning("Variant %s failed: %s", sk, res)
                    continue
                variants.extend({"url": u, "style": sk, "upscaled": False} for u in res)
            if not variants:
                raise RuntimeError("Tutte le varianti multi-style sono fallite")
        else:
            urls = await _flux_inpaint(
                base_image, mask_url,
                _build_prompt(doc["style"], doc["room_type"], crm_fragment),
                num_images=num_variants,
            )
            variants = [{"url": u, "style": doc["style"], "upscaled": False} for u in urls]
        flux_cost = COST_FLUX * len(variants)
        await _mark_stage("flux_inpaint", {
            "status": "done", "duration_ms": int((monotonic() - t0) * 1000), "cost_usd": round(flux_cost, 4),
        })
        total_cost += flux_cost
    except Exception as e:
        await _fail("flux_inpaint", "Flux", e)
        return

    # Stage 3: parallel upscale (non-fatal per variant)
    t0 = monotonic()
    await _mark_stage("upscale", {"status": "running"})

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

    await _mark_root({
        "status": "done",
        "variants": variants,
        "variant_url": variants[0]["url"] if variants else None,
        "cost_total_usd": round(total_cost, 4),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })


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
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(v["url"])
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
            {"key": "standard", "label": "Stanza vuota"},
            {"key": "reverse", "label": "Svuota e ri-arreda (Reverse)"},
        ],
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
    if body.mode not in ("standard", "reverse"):
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

    if body.property_id:
        q: Dict[str, Any] = {"id": body.property_id}
        if agency_id:
            q["agency_id"] = agency_id
        if not await db.properties.find_one(q, {"_id": 1}):
            raise HTTPException(404, "Immobile non trovato")

    stages = [{"name": "sam2_mask", "status": "queued"}]
    if body.mode == "reverse":
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
