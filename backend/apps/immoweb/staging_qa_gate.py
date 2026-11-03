"""Hard/soft quality gate for professional Virtual Staging (D-136).

Architectural integrity is HARD. Aesthetic quality is SOFT and never overrides a hard fail.
Verdicts: ACCEPT | RETRY | REJECT | MANUAL_REVIEW
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional

from apps.immoweb.staging_agent import QualityReport

logger = logging.getLogger("omnia.staging_qa_gate")

HARD_ISSUE_CODES = {
    "room_function_changed",
    "invented_door",
    "invented_window",
    "removed_opening",
    "walls_redrawn",
    "floor_geometry_changed",
    "invented_built_in",
    "geometry_broken",
    "architecture_fail",
    "invented_windows",
}


def empty_gate(*, reason: str = "unavailable") -> Dict[str, Any]:
    return {
        "verdict": "MANUAL_REVIEW",
        "hard_fail": False,
        "hard_issues": [],
        "soft_score": 0.0,
        "soft_scores": {},
        "rationale": reason,
        "unverifiable": True,
    }


def decide_gate(
    *,
    hard_issues: List[str],
    soft_score: float,
    retries_left: int,
    can_afford: bool,
    unverifiable: bool = False,
) -> str:
    hard = [h for h in hard_issues if h]
    if hard:
        # Structural lies → REJECT (or RETRY once if budget and retryable)
        retryable = {"invented_door", "invented_window", "invented_built_in", "invented_windows", "architecture_fail"}
        if retries_left > 0 and can_afford and any(h in retryable for h in hard):
            return "RETRY"
        return "REJECT"
    if unverifiable:
        return "MANUAL_REVIEW"
    if soft_score >= 0.70:
        return "ACCEPT"
    if retries_left > 0 and can_afford:
        return "RETRY"
    if soft_score >= 0.55:
        return "MANUAL_REVIEW"
    return "REJECT"


def parse_gate_json(raw: str, *, expected_room: str) -> Dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*", "", (raw or "").strip())
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
        return empty_gate(reason="gate_parse_error")

    hard_issues: List[str] = []
    for key in (
        "room_function_changed",
        "invented_door",
        "invented_window",
        "removed_opening",
        "walls_redrawn",
        "floor_geometry_changed",
        "invented_built_in",
        "geometry_broken",
    ):
        if parsed.get(key) is True:
            hard_issues.append(key)
    if parsed.get("architectural_integrity") is False:
        hard_issues.append("architecture_fail")
    if parsed.get("room_function_preservation") is False:
        hard_issues.append("room_function_changed")
    if parsed.get("opening_consistency") is False:
        hard_issues.append("invented_windows")
    if parsed.get("fixed_elements_consistency") is False:
        hard_issues.append("invented_built_in")

    # Count openings if provided
    try:
        d_o = int(parsed.get("doors_original") if parsed.get("doors_original") is not None else -1)
        d_r = int(parsed.get("doors_result") if parsed.get("doors_result") is not None else -1)
        w_o = int(parsed.get("windows_original") if parsed.get("windows_original") is not None else -1)
        w_r = int(parsed.get("windows_result") if parsed.get("windows_result") is not None else -1)
    except Exception:
        d_o = d_r = w_o = w_r = -1
    if d_o >= 0 and d_r >= 0 and d_r > d_o:
        hard_issues.append("invented_door")
    if w_o >= 0 and w_r >= 0 and w_r > w_o:
        hard_issues.append("invented_window")
    if d_o >= 0 and d_r >= 0 and d_r < d_o:
        hard_issues.append("removed_opening")
    if w_o >= 0 and w_r >= 0 and w_r < w_o:
        hard_issues.append("removed_opening")

    result_room = str(parsed.get("result_room_type") or "").strip().lower().replace(" ", "_")
    if result_room and expected_room:
        # Normalize taxonomy vs internal
        from apps.immoweb.staging_room_analysis import TAXONOMY_TO_INTERNAL, INTERNAL_TO_TAXONOMY

        exp = expected_room
        if exp in INTERNAL_TO_TAXONOMY:
            exp_tax = INTERNAL_TO_TAXONOMY[exp]
        else:
            exp_tax = exp
        res_internal = TAXONOMY_TO_INTERNAL.get(result_room, result_room)
        if res_internal not in ("uncertain", "other") and res_internal != exp and result_room != exp_tax:
            hard_issues.append("room_function_changed")

    soft = parsed.get("soft_scores") if isinstance(parsed.get("soft_scores"), dict) else {}
    try:
        overall = float(parsed.get("overall_quality") if parsed.get("overall_quality") is not None else soft.get("overall") or 0)
        if overall > 1.0:
            overall = overall / 10.0
    except Exception:
        overall = 0.0

    hard_issues = list(dict.fromkeys(hard_issues))
    unverifiable = bool(parsed.get("unverifiable"))
    # If model couldn't verify architecture, do NOT auto-accept
    if parsed.get("architectural_integrity") is None and not hard_issues:
        unverifiable = True

    return {
        "verdict": "PENDING",
        "hard_fail": bool(hard_issues),
        "hard_issues": hard_issues,
        "soft_score": max(0.0, min(1.0, overall)),
        "soft_scores": soft,
        "rationale": str(parsed.get("rationale") or "")[:400],
        "unverifiable": unverifiable,
        "doors_original": d_o,
        "doors_result": d_r,
        "windows_original": w_o,
        "windows_result": w_r,
        "result_room_type": result_room,
        "expected_room_type": expected_room,
    }


async def run_architectural_gate(
    source_url: str,
    result_url: str,
    *,
    expected_room: str,
    mode: str,
    style: str,
    analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Independent ORIG vs RESULT architectural gate (Gemini)."""
    try:
        from google import genai
        from google.genai import types
        from shared.llm import try_resolve_api_key
        import httpx
        import os

        api_key = try_resolve_api_key()
        if not api_key:
            return empty_gate(reason="critic_no_key")

        async with httpx.AsyncClient(timeout=60) as client:
            src_b, res_b = await asyncio.gather(
                client.get(source_url),
                client.get(result_url),
            )
            src_b.raise_for_status()
            res_b.raise_for_status()
            src_bytes, res_bytes = src_b.content, res_b.content

        constraints = (analysis or {}).get("staging_constraints") or []
        prompt = (
            "Sei un revisore di Virtual Staging immobiliare. Priorità: FEDELTÀ ARCHITETTONICA. "
            f"Mode={mode} style={style} expected_room={expected_room}. "
            "Confronta ORIGINALE e RISULTATO. Una foto bella ma falsa è REJECT. "
            "Restituisci SOLO JSON:\n"
            '{"architectural_integrity":true|false|null,'
            '"room_function_preservation":true|false|null,'
            '"opening_consistency":true|false|null,'
            '"fixed_elements_consistency":true|false|null,'
            '"perspective_consistency":true|false|null,'
            '"room_function_changed":true|false,'
            '"invented_door":true|false,'
            '"invented_window":true|false,'
            '"removed_opening":true|false,'
            '"walls_redrawn":true|false,'
            '"floor_geometry_changed":true|false,'
            '"invented_built_in":true|false,'
            '"geometry_broken":true|false,'
            '"doors_original":N,"doors_result":N,'
            '"windows_original":N,"windows_result":N,'
            '"result_room_type":"living_room|bedroom|kitchen|bathroom|dining_room|office|uncertain",'
            '"soft_scores":{"furniture_realism":0-10,"lighting":0-10,"composition":0-10,"overall":0-10},'
            '"overall_quality":0-10,'
            '"unverifiable":true|false,'
            '"rationale":"1-2 frasi IT"}\n'
            "HARD FAIL se: cambia funzione stanza; inventa/elimina porte o finestre; ridisegna pareti/pavimenti; "
            "inventa armadi a muro/strutture; deforma geometria. "
            "Se non puoi verificare un requisito, usa null / unverifiable=true — NON dichiararlo superato. "
            f"Vincoli analisi: {constraints}."
        )
        model = os.environ.get("OMNIA_STAGING_CRITIC_MODEL", "gemini-3-flash-preview")
        gclient = genai.Client(api_key=api_key)
        resp = await asyncio.to_thread(
            gclient.models.generate_content,
            model=model,
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
        gate = parse_gate_json(raw, expected_room=expected_room)
        return gate
    except Exception as e:
        logger.warning("architectural gate failed: %s", e)
        return empty_gate(reason=str(e)[:160])


def gate_to_quality_report(gate: Dict[str, Any]) -> QualityReport:
    issues = list(gate.get("hard_issues") or [])
    score = float(gate.get("soft_score") or 0)
    if gate.get("hard_fail"):
        score = min(score, 0.35)
    return QualityReport(
        score=score,
        issues=issues,
        retry_actions=["re_furnish_preserve_architecture"] if issues else ["re_furnish"],
        signals={
            "gate_verdict": gate.get("verdict"),
            "hard_fail": bool(gate.get("hard_fail")),
            "unverifiable": bool(gate.get("unverifiable")),
            "rationale": gate.get("rationale"),
            "doors_original": gate.get("doors_original"),
            "doors_result": gate.get("doors_result"),
            "windows_original": gate.get("windows_original"),
            "windows_result": gate.get("windows_result"),
            "result_room_type": gate.get("result_room_type"),
        },
    )


def variant_is_publishable(variant: Optional[dict]) -> bool:
    if not variant or not isinstance(variant, dict):
        return False
    if not (variant.get("url") or variant.get("fal_url")):
        return False
    hard = variant.get("hard_issues") or []
    if hard:
        return False
    if variant.get("publishable") is False:
        return False
    verdict = str(variant.get("qa_verdict") or variant.get("gate_verdict") or "").upper()
    if verdict in ("REJECT", "RETRY", "MANUAL_REVIEW"):
        return False
    if verdict == "ACCEPT":
        return True
    # Legacy nano path without gate: allow only accept / accept_with_warning without hard issues
    decision = str(variant.get("quality_decision") or "").lower()
    return decision in ("accept", "accept_with_warning", "")
