"""OMNIA staging — furniture erase / mask pipeline (extracted from virtual_staging).

MOVE-ONLY split: Florence/SAM2/EVF + Ideogram/Bria erase. Re-exported via virtual_staging.
"""
from __future__ import annotations

import asyncio
import io
import logging
import os
from typing import Any, List, Optional

import fal_client
import httpx
from PIL import Image, ImageDraw

logger = logging.getLogger("omnia.staging")

MODEL_SAM2 = "fal-ai/sam2/auto-segment"

MODEL_SAM2_BOX = "fal-ai/sam2/image"

MODEL_FLORENCE_DET = "fal-ai/florence-2-large/open-vocabulary-detection"

MODEL_BRIA_ERASER = "fal-ai/bria/eraser"

MODEL_IDEOGRAM_ERASE = "fal-ai/ideogram/object-removal"

MODEL_FAL_OBJECT_REMOVAL = "fal-ai/object-removal/mask"

MODEL_EVF_SAM = "fal-ai/evf-sam"

ARCHITECTURE_KEEP_LABELS = (
    "door",
    "doorway",
    "open door",
    "window",
    "sliding door",
)

EVF_FURNITURE_PROMPTS = (
    "gym machine, exercise equipment, weight bench, weights, cables",
    "bed, mattress, bedding, pillows, nightstand",
    "wardrobe, closet, dresser, cupboard, armoire",
    "desk, shelf, shelving unit, cabinet, console, sideboard",
    "rug, carpet, mat, runner",
    "picture frame, hanging decoration, wind chime, mobile, freestanding lamp, sailboat, plant pot",
    "bench, stool, chair, pedestal, pillar object, column remnant",
)

EVF_ARCHITECTURE_NEGATIVE = (
    "walls, floor tiles, ceiling, door frames, doorways, open doorways, windows, "
    "baseboards, built-in fixtures, structural beams"
)

COST_SAM2 = 0.001

COST_FLORENCE = 0.001

COST_EVF_SAM = 0.01

COST_BRIA = 0.04

COST_IDEOGRAM = 0.03

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

_MASK_BOX_AREA_MAX = 0.35

_ERASE_PASS1_MAX = 8

_ERASE_PASS2_MAX = 5

_ERASE_PASS3_MAX = 4

_MASK_AREA_MIN = 0.008

_MASK_AREA_MAX = 0.38

_MASK_MERGE_CAP = 40

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

async def _opening_brightness_map(image_url: str, keep: Image.Image) -> Optional[dict]:
    """Per-component luminance for door/window keep regions (avoid false wall-skips)."""
    if keep is None or not keep.getbbox():
        return None
    from PIL import ImageFilter
    import numpy as np

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.get(image_url)
        resp.raise_for_status()
        im = Image.open(io.BytesIO(resp.content)).convert("L")
    if im.size != keep.size:
        im = im.resize(keep.size)
    arr = np.asarray(im, dtype=np.float32)
    mask = (np.asarray(keep) > 127).astype(np.uint8) * 255
    # Connected components via simple flood — use scipy if available, else global fallback
    try:
        from scipy import ndimage  # type: ignore

        labeled, n = ndimage.label(mask)
        out: dict = {"n": int(n), "means": []}
        for i in range(1, n + 1):
            sel = labeled == i
            if sel.sum() < 80:
                continue
            out["means"].append(float(arr[sel].mean()))
        if not out["means"]:
            return None
        return out
    except Exception:
        m = mask > 127
        if not m.any():
            return None
        return {"n": 1, "means": [float(arr[m].mean())]}

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
    open0 = await _opening_brightness_map(image_url, keep)

    def _opening_delta(before: Optional[dict], after: Optional[dict]) -> float:
        if not before or not after:
            return 0.0
        a, b = before.get("means") or [], after.get("means") or []
        if not a or not b:
            return 0.0
        # Compare sorted means pairwise (same # openings assumed)
        n = min(len(a), len(b))
        if n == 0:
            return 0.0
        deltas = [abs(b[i] - a[i]) / max(a[i], 1.0) for i in range(n)]
        return max(deltas)

    def _box_overlaps_keep(box: dict) -> bool:
        if keep is None or not keep.getbbox():
            return False
        import numpy as np
        x1, y1 = int(box["x_min"]), int(box["y_min"])
        x2, y2 = int(box["x_max"]), int(box["y_max"])
        crop = keep.crop((x1, y1, max(x1 + 1, x2), max(y1 + 1, y2)))
        return float((np.asarray(crop) > 127).mean()) > 0.12

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
            open1 = await _opening_brightness_map(new_url, keep)
            if _opening_delta(open0, open1) > 0.35:
                wall_retries += 1
                logger.warning("EVF erase wall-invention suspected — keep prior")
                erased_labels[-1] = "evf_union:skip_wall"
            else:
                url = new_url
                open0 = open1 or open0
    except Exception as e:
        logger.warning("EVF semantic erase skipped: %s", e)

    async def _erase_box(url: str, box: dict, *, pad: int, tag: str) -> str:
        nonlocal cost, wall_retries, open0
        mask_url = await _erase_mask_url(box, url, keep=keep, pad=pad)
        new_url, eng, c = await _erase_once(url, mask_url)
        cost += c
        engines.append(f"{eng}{tag}")
        erased_labels.append(f"{box.get('label') or '?'}{tag}")
        # Only gate erases that heavily overlap openings (avoids false skip on wardrobe).
        if open0 is not None and _box_overlaps_keep(box) and float(box.get("area") or 0) >= 0.08:
            open1 = await _opening_brightness_map(new_url, keep)
            delta = _opening_delta(open0, open1)
            if delta > 0.35:
                wall_retries += 1
                logger.warning(
                    "erase wall-invention suspected label=%s openingΔ=%.0f%% — retry fal_orm",
                    box.get("label"), delta * 100,
                )
                try:
                    alt = await _fal_object_removal(url, mask_url)
                    cost += COST_IDEOGRAM
                    engines.append("fal_orm_retry")
                    open2 = await _opening_brightness_map(alt, keep)
                    if _opening_delta(open0, open2) < delta:
                        open0 = open2 or open0
                        return alt
                except Exception as e:
                    logger.warning("fal_orm retry failed: %s", e)
                erased_labels[-1] = f"{box.get('label')}:skip_wall"
                return url
            open0 = open1 or open0
        return new_url

    # Remnant detection on post-EVF image (do not reset url — keep semantic erase)
    boxes = await _florence_furniture_boxes(url)
    cost += COST_FLORENCE
    boxes = _sort_erase_boxes(boxes)[:_ERASE_PASS1_MAX]
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
        "evf_ratio": round(evf_ratio, 3),
        "pass1": len(boxes),
        "pass2": len(boxes2),
        "pass3": len(boxes3),
        "sweep": len(leftover),
        "wall_retries": wall_retries,
        "arch_keep": bool(keep.getbbox()),
    }
    return url, cost, meta

