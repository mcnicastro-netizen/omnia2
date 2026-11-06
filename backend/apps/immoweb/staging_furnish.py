"""OMNIA staging — furnish engines (nano / LoRA / Flux) (extracted from virtual_staging).

MOVE-ONLY split: prompts + fal edit/inpaint/upscale + vision critic. Re-exported via virtual_staging.
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import List, Optional

import fal_client
import httpx

from apps.immoweb.staging_agent import (
    COST_NANO_BANANA_1K,
    parse_vision_critique,
)
from apps.immoweb.staging_catalog import (
    NEGATIVE_PROMPT,
    ROOM_TYPES,
    STYLES,
)

logger = logging.getLogger("omnia.staging")

MODEL_APARTMENT_STAGING = "fal-ai/flux-2-lora-gallery/apartment-staging"

MODEL_FLUX_INPAINT = "fal-ai/flux-lora/inpainting"

MODEL_UPSCALE = "fal-ai/esrgan"

MODEL_NANO_BANANA_EDIT = "fal-ai/nano-banana-2/edit"

VISION_CRITIC_MODEL = os.environ.get("OMNIA_STAGING_CRITIC_MODEL", "gemini-3-flash-preview")

STAGING_ENGINE = (os.environ.get("OMNIA_STAGING_ENGINE") or "nano_banana").strip().lower()

COST_STAGING_LORA = 0.06

COST_FLUX = 0.05

COST_UPSCALE = 0.005

COST_NANO_BANANA = COST_NANO_BANANA_1K  # $0.08 @ 1K

COST_VISION_CRITIC = 0.002

_STYLE_ONESHOT_EN = {
    "modern": (
        "bright modern hotel-apartment style, crisp white linens, light oak, "
        "closed wardrobe doors, soft daylight, airy, aspirational MLS photo"
    ),
    "classic": (
        "refined Italian classic but bright and fresh (not heavy or dark), "
        "cream upholstery, warm wood accents, inviting daylight"
    ),
    "scandi": (
        "bright Scandinavian, light wood, white textiles, soft greenery, "
        "cool daylight, clean and airy"
    ),
    "industrial": (
        "bright industrial loft, metal and leather accents, lots of daylight, not gloomy"
    ),
    "luxury": (
        "boutique luxury movable furnishings only: plush neutrals, designer floor/table lamps, "
        "premium textiles — never invent tall built-in wardrobes, doors, LED coves, or new walls"
    ),
}

_STYLE_EN = {
    "modern": (
        "bright modern hotel-apartment style, crisp white linens, light oak, "
        "closed wardrobe doors, soft daylight, airy"
    ),
    "classic": (
        "refined Italian classic but bright and fresh (not heavy or dark), "
        "cream upholstery, warm wood accents, inviting daylight"
    ),
    "scandi": (
        "bright Scandinavian, light wood, white textiles, soft greenery, "
        "cool daylight, clean and airy"
    ),
    "industrial": (
        "bright industrial loft, metal and leather accents, lots of daylight, "
        "not gloomy"
    ),
    "luxury": (
        "boutique luxury movable furnishings only: plush neutrals, designer lamps, "
        "premium textiles — no invented built-in wardrobes or architectural LED strips"
    ),
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
    style_en = _STYLE_EN.get(sk, _STYLE_EN["modern"])
    base = (
        f"Furnish this empty {room_en} for a 2025 Italian real-estate listing photo. "
        f"Style: {style_en}. Furniture: {room_bits}. "
        "Keep walls, door frames, open doorways, windows, floor material and camera angle identical. "
        "Do not invent new doors or walls. Do not leave wardrobe doors open. "
        "No pedestals, no gym remnants, no hanging wind chimes, no clutter, no yellow color cast. "
        "Cool natural daylight, sharp details, aspirational MLS hero photograph."
    )
    if crm_fragment:
        return f"{base} {crm_fragment}"
    return base

def _oneshot_prompt(
    mode: str,
    style: str,
    room_type: str,
    crm_fragment: Optional[str] = None,
) -> str:
    """Nano Banana one-shot prompt — lock architecture, then empty and/or furnish."""
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
    style_en = _STYLE_ONESHOT_EN.get(sk, _STYLE_ONESHOT_EN["modern"])
    room_bits = ROOM_TYPES.get(rt, ROOM_TYPES["living"])
    lock = (
        "Edit THIS photo only. Do not create a different room. "
        f"The room function is and MUST remain a {room_en} — never turn it into another room type. "
        "Lock: camera angle, crop, perspective, walls, ceiling, floor material and pattern, "
        "door frames, open doorways, existing windows only, built-in fixtures, lighting direction. "
        "CRITICAL ARCHITECTURE: do NOT add any new windows, skylights, glass panels, doors, or openings. "
        "If a wall has no window in the source photo, keep it as a solid blank wall. "
        "Do NOT invent built-in wardrobes, wall niches, LED coves, or structural changes. "
        "Do NOT invent daylight sources through new openings — use existing light only. "
        "No renovation, no invented walls, no closed-over real doorways, no people, no text, no logos. "
    )
    if mode == "empty":
        body = (
            "Remove ONLY movable furniture and objects (sofas, beds, freestanding wardrobes, rugs, clutter, "
            "decorations, gym equipment). Preserve built-in cabinets, fixed kitchens, bathrooms fixtures, "
            "doors and windows. Fill erased areas with seamless continuation of existing floor and walls. "
            "Do NOT add any new furniture. Photoreal empty Italian room ready for listing photography."
        )
    elif mode == "reverse":
        body = (
            f"Remove ONLY movable furniture and clutter, then re-furnish this same {room_en} as a "
            f"2025 Italian real-estate listing photo. Style: {style_en}. Furniture: {room_bits}. "
            "Cool natural daylight, sharp details, aspirational MLS hero photograph. "
            "No gym remnants, no open wardrobe doors, no yellow color cast, no clutter."
        )
    else:
        body = (
            f"Furnish this empty {room_en} for a 2025 Italian real-estate listing photo. "
            f"Style: {style_en}. Furniture: {room_bits}. "
            "Cool natural daylight, sharp details, aspirational MLS hero photograph. "
            "Do not invent new doors, windows, or walls. No open wardrobe doors, no clutter."
        )
    out = lock + body
    if crm_fragment:
        out = f"{out} {crm_fragment}"
    return out

async def _nano_banana_edit(
    image_url: str,
    prompt: str,
    *,
    resolution: str = "1K",
) -> str:
    """fal Nano Banana 2 edit (= Gemini 3.1 Flash Image). Returns result image URL."""
    handler = await fal_client.submit_async(
        MODEL_NANO_BANANA_EDIT,
        arguments={
            "prompt": prompt,
            "image_urls": [image_url],
            "num_images": 1,
            "output_format": "jpeg",
            "resolution": resolution if resolution in ("0.5K", "1K", "2K", "4K") else "1K",
        },
    )
    result = await handler.get()
    images = result.get("images") or []
    if images and isinstance(images[0], dict) and images[0].get("url"):
        return images[0]["url"]
    raise RuntimeError(f"Nano Banana returned no image (keys: {list(result.keys())})")

async def _vision_critique_staging(
    source_url: str,
    result_url: str,
    *,
    style: str,
    mode: str,
):
    """Gemini Flash vision critic — listing rubric. Best-effort on quota errors."""
    from apps.immoweb.staging_agent import QualityReport

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            src_b, res_b = await asyncio.gather(
                client.get(source_url),
                client.get(result_url),
            )
            src_b.raise_for_status()
            res_b.raise_for_status()
            src_bytes, res_bytes = src_b.content, res_b.content
    except Exception as e:
        logger.warning("vision critic download failed: %s", e)
        return QualityReport(
            score=0.68, issues=["critic_download_failed"], retry_actions=[],
            signals={"error": str(e)[:120]},
        )

    prompt = (
        "Sei un revisore staging immobiliare per annunci italiani. "
        f"Mode={mode} style={style}. Confronta ORIGINALE e RISULTATO. "
        "Restituisci SOLO JSON valido (no markdown):\n"
        '{"score":0-10,"architecture_ok":true|false,"geometry_ok":true|false,'
        '"scale_ok":true|false,"lighting_ok":true|false,'
        '"windows_original":N,"windows_result":N,'
        '"invented_openings":true|false,'
        '"artifacts":["..."],"verdict":"accept"|"retry",'
        '"rationale":"1-2 frasi in italiano"}\n'
        "REGOLA DURA aperture: conta finestre/lucernari visibili nell'ORIGINALE vs RISULTATO. "
        "Se il risultato ha PIÙ finestre/aperture/vetri a muro → invented_openings=true, "
        "architecture_ok=false, verdict=retry, score<=4. "
        "Boccia anche se: porte chiuse/inventate, muri nuovi, residui gym/arredo vecchio, "
        "look triste/giallo, prospettiva rotta. "
        "Accetta (score>=7) solo se listing-ready E zero aperture inventate."
    )
    try:
        from google import genai
        from google.genai import types
        from shared.llm import try_resolve_api_key

        api_key = try_resolve_api_key()
        if not api_key:
            return QualityReport(
                score=0.68, issues=["critic_no_key"], retry_actions=[],
                signals={},
            )
        gclient = genai.Client(api_key=api_key)
        resp = await asyncio.to_thread(
            gclient.models.generate_content,
            model=VISION_CRITIC_MODEL,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text="ORIGINALE:"),
                        types.Part.from_bytes(data=src_bytes, mime_type="image/jpeg"),
                        types.Part.from_text(text="RISULTATO:"),
                        types.Part.from_bytes(data=res_bytes, mime_type="image/jpeg"),
                        types.Part.from_text(text=prompt),
                    ],
                )
            ],
        )
        raw = (getattr(resp, "text", None) or "").strip()
        return parse_vision_critique(raw)
    except Exception as e:
        logger.warning("vision critic LLM failed: %s", e)
        return QualityReport(
            score=0.68, issues=["critic_llm_failed"], retry_actions=[],
            signals={"error": str(e)[:160]},
        )

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

async def _stage_upscale(image_url: str) -> str:
    handler = await fal_client.submit_async(
        MODEL_UPSCALE,
        arguments={"image_url": image_url, "scale": 4, "model": "RealESRGAN_x4plus"},
    )
    result = await handler.get()
    return (result.get("image") or {}).get("url") or result.get("image_url")

