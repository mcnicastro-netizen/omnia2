"""OMNIA staging — FastAPI /app/staging routes. MOVE-ONLY extract."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import fal_client
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Response,
    UploadFile,
)
from pydantic import BaseModel, Field

from shared.auth.dependencies import get_current_user
from shared.db.connection import Database
from shared.utils.net_guard import assert_public_url
from apps.billing.plans import CREDIT_COSTS
from apps.immoweb.staging_catalog import (
    DEFAULT_MULTI_STYLES,
    ROOM_LABELS,
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
router = APIRouter(prefix="/staging", tags=["virtual-staging"])

STAGING_CREDIT_COST = int(CREDIT_COSTS.get("virtual_staging_render") or 18)

MAX_UPLOAD_MB = 12

ALLOWED_MIME = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

SOFT_RATE_LIMIT_USER_HOUR = 20   # renders/ora/utente

SOFT_RATE_LIMIT_AGENCY_HOUR = 80  # renders/ora/agenzia

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

    from apps.immoweb.virtual_staging import _run_pipeline as _rp
    background.add_task(_rp, job_id, db)
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

