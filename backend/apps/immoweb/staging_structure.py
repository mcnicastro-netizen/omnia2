"""Stage 1 — structure lock helpers (masks, depth, edges) for D-136.

Uses verified fal endpoints + PIL/numpy (no OpenCV dependency).
Protected mask always wins over removal/furniture masks.
"""
from __future__ import annotations

import io
import logging
from typing import Any, Dict, Optional, Tuple

from PIL import Image, ImageFilter, ImageOps, ImageChops
import numpy as np

logger = logging.getLogger("omnia.staging_structure")

MODEL_DEPTH = "fal-ai/imageutils/depth"


def _pil_from_bytes(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def canny_edge_map(image_bytes: bytes, *, low: int = 80, high: int = 160) -> bytes:
    """Approximate Canny with PIL/numpy (sobel-ish + threshold). Returns PNG bytes."""
    img = _pil_from_bytes(image_bytes).convert("L")
    # Simple gradient magnitude via kernels
    arr = np.asarray(img, dtype=np.float32)
    gx = np.zeros_like(arr)
    gy = np.zeros_like(arr)
    gx[:, 1:-1] = arr[:, 2:] - arr[:, :-2]
    gy[1:-1, :] = arr[2:, :] - arr[:-2, :]
    mag = np.sqrt(gx * gx + gy * gy)
    mag = (mag / (mag.max() + 1e-6) * 255.0).astype(np.uint8)
    edges = np.where(mag >= low, 255, 0).astype(np.uint8)
    # Soft thicken for control maps
    edge_img = Image.fromarray(edges, mode="L").filter(ImageFilter.MaxFilter(3))
    out = io.BytesIO()
    edge_img.save(out, format="PNG")
    return out.getvalue()


def combine_masks(
    *,
    removal: Optional[Image.Image],
    protected: Optional[Image.Image],
    size: Tuple[int, int],
) -> Dict[str, Image.Image]:
    """Build removal / protected / furniture masks. Protected subtracts from removal."""
    w, h = size
    if removal is None:
        removal = Image.new("L", (w, h), 0)
    else:
        removal = removal.convert("L").resize((w, h), Image.NEAREST)
    if protected is None:
        protected = Image.new("L", (w, h), 0)
    else:
        protected = protected.convert("L").resize((w, h), Image.NEAREST)

    rem = np.asarray(removal, dtype=np.uint8)
    prot = np.asarray(protected, dtype=np.uint8)
    rem_safe = np.where(prot > 32, 0, rem)
    # Furniture insert zone ≈ dilated removal (where objects were) minus protected
    dil = Image.fromarray(rem_safe, mode="L").filter(ImageFilter.MaxFilter(9))
    furn = np.asarray(dil, dtype=np.uint8)
    furn = np.where(prot > 32, 0, furn)
    return {
        "removal": Image.fromarray(rem_safe, mode="L"),
        "protected": Image.fromarray(prot, mode="L"),
        "furniture": Image.fromarray(furn, mode="L"),
    }


async def estimate_depth_map(image_url: str) -> Optional[str]:
    """fal-ai/imageutils/depth — returns depth image URL or None."""
    try:
        import fal_client

        handler = await fal_client.submit_async(
            MODEL_DEPTH,
            arguments={"image_url": image_url, "depth_and_normal": False},
        )
        result = await handler.get()
        # Schema ImageutilsDepthOutput — typically image or images
        if isinstance(result, dict):
            if result.get("image") and isinstance(result["image"], dict):
                return result["image"].get("url")
            imgs = result.get("images") or []
            if imgs and isinstance(imgs[0], dict):
                return imgs[0].get("url")
            if isinstance(result.get("depth"), dict):
                return result["depth"].get("url")
        return None
    except Exception as e:
        logger.warning("depth estimate failed: %s", e)
        return None


def style_furniture_rules(style: str, room_internal: str) -> str:
    """Style language only — never invent architecture / change room function."""
    style = (style or "modern").lower()
    room = (room_internal or "living").lower()
    base = {
        "modern": "modern Italian listing: clean lines, light woods, closed storage, cool daylight",
        "scandi": "Scandinavian: light wood, soft textiles, airy, restrained decor",
        "classic": "classic Italian bright (not heavy baroque): cream upholstery, warm wood accents",
        "luxury": "boutique luxury soft furnishings and premium textiles — NO new built-in wardrobes, NO new doors, NO LED cove architecture, NO structural changes",
        "industrial": "industrial accents: metal/leather, daylight, not gloomy",
    }.get(style, "modern Italian listing furniture")
    room_bits = {
        "living": "living room: sofa, coffee table, optional armchair, floor lamp, rug — keep circulation to doors/windows clear",
        "bedroom": "bedroom: bed, nightstands, optional dresser — do not block doors/windows",
        "kitchen": "kitchen: only movable stools/small table if space allows — never redesign cabinets or appliances layout",
        "dining": "dining: table and chairs scaled to room — clear paths",
        "bathroom": "bathroom: only towels/small accessories — never move fixtures",
        "office": "home office: desk and chair — keep openings free",
    }.get(room, "furniture coherent with the room function")
    return f"{base}. {room_bits}. Preserve walls, floor, ceiling, doors, windows, built-ins exactly."
