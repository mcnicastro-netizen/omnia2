"""OMNIA — Micro-tour video (M5.S4.3, Sprint 3 · Item #5).

2 modalità:

1. **Ken Burns** (gratuito, sempre disponibile)
   - Zoom + pan su 1..N foto → video 15s H.264 MP4
   - Nessun costo compute esterno, ffmpeg locale
   - Disponibile su portale B2C ImmobilCloud + annunci privati UGC

2. **Sora 2 premium** (12 crediti, riservato al gestionale agenzia)
   - Video AI 15s con generation prompt CRM-aware
   - Costo Sora ~€0.90-1.10, prezzo 12 crediti = €3.60, margine 72%
   - NOTA: integrazione Sora 2 richiede playbook Emergent dedicata → v1 STUB
     con endpoint 501 e TODO in D-063. Ken Burns è completamente funzionante.

Endpoints:
  POST /api/app/videos/kenburns/property/{pid} — genera video da foto del property (auth)
  POST /api/cloud/videos/kenburns/property/{pid} — pubblico per privati listings (M3.S5)
  POST /api/app/videos/sora2/property/{pid}    — stub v1
  GET  /api/app/videos/{video_id}              — status/download
"""
from __future__ import annotations
import asyncio
import io
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from shared.auth.dependencies import require_roles, get_optional_user
from shared.db.connection import Database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/videos", tags=["videos"])
public_router = APIRouter(prefix="/videos", tags=["videos-public"])

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

VIDEO_ROOT = Path("/tmp/omnia_videos")
VIDEO_ROOT.mkdir(exist_ok=True, parents=True)
DEFAULT_DURATION_S = 15
DEFAULT_FPS = 24
DEFAULT_W = 1280
DEFAULT_H = 720
MAX_PHOTOS = 8
WATERMARK_TEXT = "Powered by OMNIA"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class KenBurnsRequest(BaseModel):
    duration_s: int = Field(default=DEFAULT_DURATION_S, ge=5, le=30)
    photo_urls: Optional[List[str]] = None  # if None → use property.photos


class VideoDoc(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    agency_id: Optional[str] = None
    property_id: Optional[str] = None
    mode: Literal["ken_burns", "sora2"]
    status: Literal["pending", "processing", "ready", "failed"] = "pending"
    file_path: Optional[str] = None
    download_url: Optional[str] = None
    duration_s: int = DEFAULT_DURATION_S
    photos_count: int = 0
    error: Optional[str] = None
    credits_charged: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Ken Burns core (ffmpeg)
# ---------------------------------------------------------------------------

async def _download_photo(url: str, dest: Path) -> bool:
    """Fetch a photo URL to disk. Returns True on success."""
    try:
        if url.startswith("/api/public/property/"):
            # Internal endpoint — resolve via backend base
            base = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
            if not base:
                # fallback to localhost:8001 in-container
                base = "http://localhost:8001"
            url = base + url
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            r = await client.get(url)
        if r.status_code >= 400 or len(r.content) < 500:
            return False
        dest.write_bytes(r.content)
        return True
    except Exception as e:
        logger.warning("photo download failed: %s (%s)", url, e)
        return False


def _run_ken_burns_ffmpeg(images: List[Path], out_path: Path, duration_s: int) -> None:
    """Build a video via ffmpeg with slow zoom-in + crossfade transitions.

    Simpler & faster than zoompan-per-frame: uses `scale` with expressions
    for a gentle zoom, then xfade transitions between clips.
    Rendering ~1x realtime (15s video ≈ 15s render).
    """
    n = len(images)
    fade_dur = 1  # 1s crossfade between images
    # Total effective duration = n*per_image - (n-1)*fade → per_image = (dur + (n-1)*fade) / n
    per_image = max(3, (duration_s + (n - 1) * fade_dur + n - 1) // n)
    fps = DEFAULT_FPS

    # Each input: loop image for per_image seconds, scale + very slow zoom pan.
    inputs = []
    filter_parts = []
    for i in range(n):
        # Simple pan: alternate directions per image, very light (5% shift)
        direction = ["e", "w", "n", "s"][i % 4]
        pan_x = {"e": "'iw*0.05*t/{d}'", "w": "'iw*0.05*(1-t/{d})'",
                 "n": "0", "s": "0"}[direction].format(d=per_image)
        pan_y = {"e": "0", "w": "0",
                 "n": "'ih*0.05*t/{d}'", "s": "'ih*0.05*(1-t/{d})'"}[direction].format(d=per_image)
        filter_parts.append(
            f"[{i}:v]scale=1600:900:force_original_aspect_ratio=increase,"
            f"crop=1280:720:x={pan_x}:y={pan_y},"
            f"setsar=1,fps={fps}[v{i}]"
        )

    # Concat with crossfades between consecutive clips
    if n == 1:
        filter_parts.append(f"[v0]null[outv]")
    else:
        current = "v0"
        cumulative_offset = per_image - fade_dur
        for i in range(1, n):
            next_out = f"m{i}" if i < n - 1 else "outv"
            filter_parts.append(
                f"[{current}][v{i}]xfade=transition=fade:duration={fade_dur}:offset={cumulative_offset}[{next_out}]"
            )
            current = next_out
            cumulative_offset += per_image - fade_dur

    filter_complex = ";".join(filter_parts)

    cmd = ["ffmpeg", "-y"]
    for img in images:
        cmd.extend(["-loop", "1", "-t", str(per_image), "-i", str(img)])
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "26",
        "-pix_fmt", "yuv420p",
        "-r", str(fps),
        "-t", str(duration_s),
        "-movflags", "+faststart",
        str(out_path),
    ])
    logger.info("running ffmpeg ken burns: %s (images=%d, duration=%ds)",
                " ".join(cmd[:6]) + " ...", n, duration_s)
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    if result.returncode != 0:
        stderr_text = result.stderr.decode(errors="replace")
        error_lines = [ln for ln in stderr_text.splitlines()
                       if any(m in ln.lower() for m in ("error", "invalid", "no such", "not found", "failed"))]
        tail = "\n".join(error_lines[-6:]) or stderr_text[-800:]
        raise RuntimeError(f"ffmpeg failed rc={result.returncode}: {tail}")


async def _generate_ken_burns(video_id: str, property_id: Optional[str],
                              photo_urls: List[str], duration_s: int, db) -> None:
    """Async task: download photos → run ffmpeg → update video doc."""
    workdir = Path(tempfile.mkdtemp(prefix=f"kb_{video_id[:8]}_"))
    try:
        # Download photos
        images: List[Path] = []
        for i, url in enumerate(photo_urls[:MAX_PHOTOS]):
            dest = workdir / f"img_{i:02d}.jpg"
            if await _download_photo(url, dest):
                images.append(dest)
        if not images:
            await db.videos.update_one({"id": video_id}, {"$set": {
                "status": "failed", "error": "no_photos_downloaded",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }})
            return
        # Render
        out_path = VIDEO_ROOT / f"{video_id}.mp4"
        await db.videos.update_one({"id": video_id}, {"$set": {"status": "processing"}})
        await asyncio.to_thread(_run_ken_burns_ffmpeg, images, out_path, duration_s)
        # Save
        await db.videos.update_one({"id": video_id}, {"$set": {
            "status": "ready",
            "file_path": str(out_path),
            "download_url": f"/api/app/videos/{video_id}/download",
            "photos_count": len(images),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }})
    except Exception as e:
        logger.exception("ken burns generation failed")
        await db.videos.update_one({"id": video_id}, {"$set": {
            "status": "failed",
            "error": f"{type(e).__name__}: {str(e)[:200]}",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }})
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _load_property(db, pid: str, agency_id: Optional[str] = None) -> dict:
    q: Dict[str, Any] = {"id": pid}
    if agency_id:
        q["agency_id"] = agency_id
    p = await db.properties.find_one(q)
    if not p:
        raise HTTPException(status_code=404, detail="property_not_found")
    return p


def _property_photo_urls(prop: dict, base_url: str) -> List[str]:
    photos = prop.get("photos") or []
    pid = prop["id"]
    urls: List[str] = []
    for i, ph in enumerate(photos):
        if ph.get("url"):
            urls.append(ph["url"])
        else:
            # base64-stored photos → use the public serve endpoint
            urls.append(f"{base_url}/api/public/property/{pid}/photo/{i}")
    return urls


from shared.auth.tenant import optional_agency_id as _agency_id


# ---------------------------------------------------------------------------
# Ken Burns endpoints
# ---------------------------------------------------------------------------

@router.post("/kenburns/property/{pid}", status_code=501)
async def kenburns_from_property_gated(
    pid: str,
    body: KenBurnsRequest,
    user: dict = Depends(require_roles("agent", "agency_admin", "super_admin")),
):
    """D-064 · Ken Burns NON è disponibile nel gestionale agenzia.

    Strategia commerciale: nel gestionale l'agente usa **Sora 2 premium**
    (12 crediti = €3.60, margine 72%). Ken Burns gratuito è riservato al
    portale B2C ImmobilCloud + annunci privati UGC, dove è funzionale a
    riempire il portale di contenuti video senza costi per l'utente finale.

    Ken Burns qui dentro cannibalizzerebbe la revenue Sora 2.
    """
    raise HTTPException(
        status_code=501,
        detail=(
            "kenburns_disabled_in_agency: usa Sora 2 premium (12 crediti) — "
            "Ken Burns è disponibile solo sul portale B2C /api/cloud/videos/..."
        ),
    )


@public_router.post("/kenburns/property/{pid}", status_code=202)
async def kenburns_public(pid: str, body: KenBurnsRequest):
    """Public Ken Burns generation for private listings (M3.S5 UGC)."""
    db = Database.get()
    prop = await db.properties.find_one({
        "id": pid,
        "is_listed_on_immobilcloud": True,
        "status": "active",
        "visibility": "public",
    })
    if not prop:
        raise HTTPException(status_code=404, detail="property_not_found")
    base = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/") or "http://localhost:8001"
    photo_urls = body.photo_urls or _property_photo_urls(prop, base)
    if not photo_urls:
        raise HTTPException(status_code=422, detail="no_photos_available")
    doc = VideoDoc(
        property_id=pid, mode="ken_burns", status="pending",
        duration_s=body.duration_s, photos_count=len(photo_urls),
    ).model_dump()
    await db.videos.insert_one(doc)
    asyncio.create_task(_generate_ken_burns(doc["id"], pid, photo_urls, body.duration_s, db))
    return {"video_id": doc["id"], "status": "pending", "poll_url": f"/api/cloud/videos/{doc['id']}"}


@router.get("/{video_id}")
async def video_status(
    video_id: str,
    user: dict = Depends(require_roles("agent", "agency_admin", "super_admin")),
):
    db = Database.get()
    aid = _agency_id(user)
    q = {"id": video_id}
    if aid:
        q["$or"] = [{"agency_id": aid}, {"agency_id": None}]
    doc = await db.videos.find_one(q, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="video_not_found")
    return doc


@public_router.get("/{video_id}")
async def video_status_public(video_id: str):
    """Public poll for UGC/private listings videos."""
    db = Database.get()
    doc = await db.videos.find_one({"id": video_id, "agency_id": None}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="video_not_found")
    return doc


@router.get("/{video_id}/download")
async def video_download(video_id: str, request: Request):
    """Serve the generated MP4.

    M11 — agency-owned videos require auth (agency match or super_admin);
    public UGC videos (agency_id=None, private listings) stay public.
    """
    db = Database.get()
    doc = await db.videos.find_one({"id": video_id})
    if not doc or doc.get("status") != "ready" or not doc.get("file_path"):
        raise HTTPException(status_code=404, detail="video_not_ready")
    if doc.get("agency_id"):
        user = await get_optional_user(request)
        if not user:
            raise HTTPException(status_code=401, detail="not_authenticated")
        if user.get("role") != "super_admin" and doc["agency_id"] not in (user.get("agency_ids") or []):
            raise HTTPException(status_code=403, detail="forbidden")
    fp = Path(doc["file_path"])
    if not fp.exists():
        raise HTTPException(status_code=410, detail="video_expired")
    return FileResponse(str(fp), media_type="video/mp4", filename=f"omnia-{video_id}.mp4")


# ---------------------------------------------------------------------------
# fal.ai Kling 1.6 Pro image-to-video (D-047, D-065)
# ---------------------------------------------------------------------------

FAL_KLING_MODEL = "fal-ai/kling-video/v1.6/pro/image-to-video"
KLING_DURATION_S = 10    # 10s Pro (D-066, upgrade da 5s originale)
KLING_CREDIT_COST = 10   # 10 crediti (D-066) — corretto in PRICING_OMNIA v2.1
KLING_COST_EUR_ESTIMATE = 0.88  # $0.95 per 10s ≈ €0.88 (margine 71% a €3.00)


def _build_kling_prompt(prop: dict) -> str:
    """CRM-aware cinematic prompt from property fields."""
    parts = ["Cinematic real estate walkthrough, slow dolly-in, natural sunlight"]
    pt = prop.get("property_type")
    if pt:
        parts.append(pt)
    city = prop.get("city")
    if city:
        parts.append(f"in {city}")
    for f in ("balcony", "garden", "parquet", "modern kitchen", "large windows"):
        if (prop.get("features") or {}).get(f.replace(" ", "_")):
            parts.append(f)
    parts.append("realistic, high quality, 24fps, elegant")
    return ", ".join(parts)


async def _generate_kling_video(video_id: str, property_id: str, image_url: str,
                                prompt: str, db) -> None:
    """Async task: call fal.ai Kling → download output → apply watermark."""
    import fal_client
    try:
        await db.videos.update_one({"id": video_id}, {"$set": {"status": "processing"}})
        handler = await fal_client.submit_async(
            FAL_KLING_MODEL,
            arguments={
                "image_url": image_url,
                "prompt": prompt,
                "duration": "10",          # 10s Pro (D-066)
                "aspect_ratio": "16:9",
                "negative_prompt": "blur, low quality, distortion, watermark, text",
                "cfg_scale": 0.5,
            },
        )
        result = await handler.get()
        video_url = (result.get("video") or {}).get("url")
        if not video_url:
            raise RuntimeError(f"fal_response_missing_video_url: {result}")
        # Download output
        raw_path = VIDEO_ROOT / f"{video_id}_raw.mp4"
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            r = await client.get(video_url)
        raw_path.write_bytes(r.content)
        # Apply watermark via ffmpeg
        final_path = VIDEO_ROOT / f"{video_id}.mp4"
        cmd = [
            "ffmpeg", "-y", "-i", str(raw_path),
            "-vf",
            "drawtext=text='Powered by OMNIA':fontcolor=white:fontsize=18:"
            "box=1:boxcolor=black@0.4:boxborderw=6:x=w-tw-14:y=h-th-14",
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(final_path),
        ]
        result_ff = subprocess.run(cmd, capture_output=True, timeout=120)
        if result_ff.returncode != 0:
            raise RuntimeError(f"watermark_failed: {result_ff.stderr.decode()[-300:]}")
        raw_path.unlink(missing_ok=True)
        await db.videos.update_one({"id": video_id}, {"$set": {
            "status": "ready",
            "file_path": str(final_path),
            "download_url": f"/api/app/videos/{video_id}/download",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }})
    except Exception as e:
        logger.exception("kling video generation failed")
        await db.videos.update_one({"id": video_id}, {"$set": {
            "status": "failed",
            "error": f"{type(e).__name__}: {str(e)[:200]}",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }})


# ---------------------------------------------------------------------------
# Sora 2 endpoint replaced by Kling 1.6 Pro (D-047 · fal.ai, non Sora)
# ---------------------------------------------------------------------------

@router.post("/kling/property/{pid}", status_code=202)
async def kling_from_property(
    pid: str,
    user: dict = Depends(require_roles("agent", "agency_admin", "super_admin")),
):
    """Genera micro-tour video 5s via fal.ai Kling 1.6 Pro image-to-video.

    Costo agente: 12 crediti (€3,60 a €0,30/credito).
    Costo interno OMNIA: ~$0,475 (~€0,44), margine 88%.
    """
    db = Database.get()
    aid = _agency_id(user)
    if not aid:
        raise HTTPException(status_code=404, detail="no_agency")
    prop = await _load_property(db, pid, aid)

    # Wallet check + charge (12 crediti)
    agency = await db.agencies.find_one({"id": aid}, {"credits_balance": 1})
    balance = int((agency or {}).get("credits_balance") or 0)
    if balance < KLING_CREDIT_COST:
        raise HTTPException(
            status_code=402,
            detail=f"insufficient_credits: {balance}/{KLING_CREDIT_COST}",
        )

    # Get cover photo URL (must be public HTTPS for fal.ai)
    photos = prop.get("photos") or []
    cover = next((p for p in photos if p.get("is_cover")), photos[0] if photos else None)
    if not cover or not cover.get("url"):
        raise HTTPException(status_code=422, detail="no_cover_photo")
    image_url = cover["url"]
    if not image_url.startswith("http"):
        base = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
        image_url = f"{base}{image_url}"

    # Deduct credits atomically
    r = await db.agencies.update_one(
        {"id": aid, "credits_balance": {"$gte": KLING_CREDIT_COST}},
        {"$inc": {"credits_balance": -KLING_CREDIT_COST}},
    )
    if r.modified_count == 0:
        raise HTTPException(status_code=402, detail="credit_charge_failed")

    doc = VideoDoc(
        agency_id=aid, property_id=pid, mode="sora2",  # keep "sora2" mode name for BC
        status="pending", duration_s=KLING_DURATION_S, photos_count=1,
        credits_charged=KLING_CREDIT_COST,
    ).model_dump()
    await db.videos.insert_one(doc)
    prompt = _build_kling_prompt(prop)
    asyncio.create_task(_generate_kling_video(doc["id"], pid, image_url, prompt, db))
    return {
        "video_id": doc["id"],
        "status": "pending",
        "mode": "kling_1_6_pro",
        "duration_s": KLING_DURATION_S,
        "credits_charged": KLING_CREDIT_COST,
        "poll_url": f"/api/app/videos/{doc['id']}",
    }


@router.post("/sora2/property/{pid}")
async def sora2_from_property(
    pid: str,
    user: dict = Depends(require_roles("agent", "agency_admin", "super_admin")),
):
    """DEPRECATED — use /kling/property/{pid} instead (D-065 · fal.ai Kling replaces Sora 2)."""
    raise HTTPException(
        status_code=410,
        detail="deprecated_use_kling_endpoint: POST /api/app/videos/kling/property/{pid}",
    )
