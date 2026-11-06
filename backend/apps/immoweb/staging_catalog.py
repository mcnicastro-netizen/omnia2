"""OMNIA staging — style/room catalog + prompt helpers (extracted from virtual_staging).

MOVE-ONLY split: no behavior change. Public symbols re-exported via virtual_staging.
"""
from __future__ import annotations

from typing import Dict, Optional

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
        "prompt": (
            "luxury movable furnishings and premium textiles only, designer seating and lamps, "
            "preserve existing floor/walls/windows/doors exactly, no new openings or built-ins"
        ),
        "staging_prompt": (
            "Furnish this empty room with luxury movable furniture and premium textiles only, "
            "keep architecture, floor, doors and windows unchanged, photorealistic real estate listing photo"
        ),
    },
}

DEFAULT_MULTI_STYLES = ["modern", "classic", "scandi", "luxury"]

ROOM_TYPES: Dict[str, str] = {
    "living": "spacious living room with sofa, coffee table, optional armchair, decorative plants",
    "bedroom": "bedroom with double bed, nightstands, optional freestanding dresser, soft ambient lighting",
    "kitchen": "kitchen movable accents only (stools/small table) — never redesign fixed cabinets",
    "dining": "dining room with table and chairs scaled to the room, sideboard if space allows",
    "bathroom": "bathroom accessories only (towels/small decor) — never move fixtures",
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

EMPTY_ROOM_PROMPT = (
    "seamless continuation of the existing floor and wall surfaces only, "
    "empty space with no furniture no objects no rugs no lamps no decorations, "
    "same tiles paint lighting and perspective as the surrounding room, "
    "photorealistic interior photograph, no architectural changes"
)

def _build_prompt(style: str, room_type: str, crm_fragment: Optional[str] = None) -> str:
    s = STYLES.get(style, STYLES["modern"])
    room = ROOM_TYPES.get(room_type, ROOM_TYPES["living"])
    parts = [s["prompt"], room]
    if crm_fragment:
        parts.append(crm_fragment)
    parts.append("photorealistic, 8k, architectural photography")
    return ", ".join(parts)

def _photo_caption(style_key: str, room_type: str) -> str:
    style_label = STYLES.get(style_key, {}).get("label", style_key)
    room_label = ROOM_LABELS.get(room_type, room_type)
    return f"Render virtuale OMNIA · {room_label} {style_label}"

