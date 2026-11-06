"""Stage 0 — visual room analysis for professional Virtual Staging (D-136).

Uses Gemini vision (same key stack as staging critic). Never invents bedroom
when uncertain. Maps taxonomy → internal ROOM_TYPES keys used by the pipeline.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Dict, Optional

logger = logging.getLogger("omnia.staging_room_analysis")

# Public taxonomy (Founder spec) → internal pipeline keys (ROOM_TYPES).
TAXONOMY_TO_INTERNAL = {
    "living_room": "living",
    "bedroom": "bedroom",
    "kitchen": "kitchen",
    "bathroom": "bathroom",
    "dining_room": "dining",
    "office": "office",
    "hallway": "living",  # no dedicated hallway furnish set — treat as living constraints
    "studio": "office",
    "other": "living",
    "uncertain": "living",
}

INTERNAL_TO_TAXONOMY = {
    "living": "living_room",
    "bedroom": "bedroom",
    "kitchen": "kitchen",
    "bathroom": "bathroom",
    "dining": "dining_room",
    "office": "office",
}

CONFIDENCE_ASK_USER = 0.55


def empty_analysis(*, reason: str = "unavailable") -> Dict[str, Any]:
    return {
        "room_type": "uncertain",
        "room_type_internal": "living",
        "room_type_confidence": 0.0,
        "room_function": "uncertain",
        "architectural_elements": [],
        "doors": {"count": None, "notes": ""},
        "windows": {"count": None, "notes": ""},
        "floor": {"material": None, "notes": ""},
        "walls": {"notes": ""},
        "ceiling": {"notes": ""},
        "fixed_furniture": [],
        "movable_furniture": [],
        "obstacles": [],
        "camera_perspective": {"notes": ""},
        "depth_information": {"available": False},
        "staging_constraints": [
            "preserve_architecture",
            "preserve_room_function",
            "no_invented_openings",
            "no_invented_built_ins",
        ],
        "needs_user_confirm": True,
        "analysis_error": reason,
        "pipeline": "professional_v1",
    }


def normalize_analysis(raw: Dict[str, Any]) -> Dict[str, Any]:
    out = empty_analysis(reason="")
    out.pop("analysis_error", None)
    tax = str(raw.get("room_type") or "uncertain").strip().lower().replace(" ", "_")
    if tax not in TAXONOMY_TO_INTERNAL:
        tax = "uncertain"
    try:
        conf = float(raw.get("room_type_confidence") or 0)
    except Exception:
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    out["room_type"] = tax
    out["room_type_internal"] = TAXONOMY_TO_INTERNAL[tax]
    out["room_type_confidence"] = round(conf, 3)
    out["room_function"] = str(raw.get("room_function") or tax)
    for key in (
        "architectural_elements",
        "fixed_furniture",
        "movable_furniture",
        "obstacles",
        "staging_constraints",
    ):
        v = raw.get(key)
        if isinstance(v, list):
            out[key] = [str(x)[:120] for x in v if x][:24]
    for key in ("doors", "windows", "floor", "walls", "ceiling", "camera_perspective"):
        v = raw.get(key)
        if isinstance(v, dict):
            out[key] = v
        elif isinstance(v, (int, float)) and key in ("doors", "windows"):
            out[key] = {"count": int(v), "notes": ""}
    out["needs_user_confirm"] = bool(
        raw.get("needs_user_confirm")
        or tax in ("uncertain", "other")
        or conf < CONFIDENCE_ASK_USER
    )
    # Always enforce core constraints
    for c in (
        "preserve_architecture",
        "preserve_room_function",
        "no_invented_openings",
        "no_invented_built_ins",
    ):
        if c not in out["staging_constraints"]:
            out["staging_constraints"].append(c)
    return out


def resolve_room_type(
    *,
    analysis: Optional[Dict[str, Any]],
    user_room_type: Optional[str],
    user_confirmed: bool = False,
) -> str:
    """Pick binding room type. Never silently default to bedroom."""
    from apps.immoweb.staging_catalog import ROOM_TYPES

    user = (user_room_type or "").strip().lower()
    if user in ("auto", "detect", ""):
        user = ""
    if user_confirmed and user in ROOM_TYPES:
        return user
    if analysis and not analysis.get("needs_user_confirm"):
        internal = analysis.get("room_type_internal")
        if internal in ROOM_TYPES:
            return internal
    if user in ROOM_TYPES:
        # User picked explicitly in UI — honor unless analysis is high-confidence conflict
        if analysis and float(analysis.get("room_type_confidence") or 0) >= 0.8:
            detected = analysis.get("room_type_internal")
            if detected in ROOM_TYPES and detected != user:
                # Prefer detection when very confident (anti Founder bedroom bug)
                return detected
        return user
    if analysis and analysis.get("room_type_internal") in ROOM_TYPES:
        return analysis["room_type_internal"]
    return "living"


async def analyze_room_image(image_url: str, *, image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """Gemini Flash structured room analysis. Best-effort; never raises to caller pipeline."""
    try:
        from google import genai
        from google.genai import types
        from shared.llm import try_resolve_api_key
        import httpx

        api_key = try_resolve_api_key()
        if not api_key:
            return empty_analysis(reason="critic_no_key")

        data = image_bytes
        if not data:
            async with httpx.AsyncClient(timeout=45) as client:
                r = await client.get(image_url)
                r.raise_for_status()
                data = r.content

        prompt = (
            "Sei un analista di fotografie immobiliari italiane. "
            "Analizza SOLO ciò che vedi. NON inventare stanze o aperture. "
            "Restituisci SOLO JSON valido (no markdown) con chiavi:\n"
            '{"room_type":"living_room|bedroom|kitchen|bathroom|dining_room|office|hallway|studio|other|uncertain",'
            '"room_type_confidence":0.0-1.0,'
            '"room_function":"string",'
            '"architectural_elements":["door","window",...],'
            '"doors":{"count":N,"notes":"..."},'
            '"windows":{"count":N,"notes":"..."},'
            '"floor":{"material":"...","notes":"..."},'
            '"walls":{"notes":"..."},'
            '"ceiling":{"notes":"..."},'
            '"fixed_furniture":["built-in wardrobe","kitchen cabinets",...],'
            '"movable_furniture":["sofa","bed",...],'
            '"obstacles":[],'
            '"camera_perspective":{"notes":"..."},'
            '"staging_constraints":["preserve_architecture","preserve_room_function"],'
            '"needs_user_confirm":true|false}\n'
            "Se non sei sicuro del room_type usa uncertain e needs_user_confirm=true. "
            "Un soggiorno con divano NON è bedroom. Un armadio a muro è fixed_furniture."
        )
        model = __import__("os").environ.get("OMNIA_STAGING_CRITIC_MODEL", "gemini-3-flash-preview")
        gclient = genai.Client(api_key=api_key)
        resp = await asyncio.to_thread(
            gclient.models.generate_content,
            model=model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=data, mime_type="image/jpeg"),
                        types.Part.from_text(text=prompt),
                    ],
                )
            ],
        )
        raw_text = (getattr(resp, "text", None) or "").strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        parsed: Dict[str, Any] = {}
        try:
            parsed = json.loads(cleaned)
        except Exception:
            m = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
            if m:
                try:
                    parsed = json.loads(m.group(0))
                except Exception:
                    parsed = {}
        if not parsed:
            return empty_analysis(reason="analysis_parse_error")
        return normalize_analysis(parsed)
    except Exception as e:
        logger.warning("room analysis failed: %s", e)
        return empty_analysis(reason=str(e)[:160])
