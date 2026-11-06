"""OMNIA staging — media helpers (watermark / persist / fetch). MOVE-ONLY extract."""
from __future__ import annotations

import asyncio
import io
import logging
from typing import Optional

import httpx
from fastapi import HTTPException
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("omnia.staging")

MAX_PHOTO_WIDTH = 1600

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

