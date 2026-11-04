"""Professional Virtual Staging pipeline (D-136).

Feature flag: OMNIA_STAGING_PIPELINE=professional

Default scope (Founder 4-Nov-2026): **gestionale B2B only**.
ImmobilCloud B2C (preview/Stripe) stays on Nano oneshot unless
OMNIA_STAGING_PIPELINE_FORCE_B2C=true.

Stages:
  0 analysis → 1 structure lock → 2 selective erase → 3 empty QA →
  4 furnish (masked / LoRA) → 5 final gate → 6 deliver only ACCEPT

Modes (API-compatible):
  empty    → EMPTY ROOM
  standard → FURNISH empty room
  reverse  → REPLACE / RESTYLE (never change room function)
"""
from __future__ import annotations

import logging
import os
from time import monotonic
from typing import Any, Dict, List, Optional

from apps.immoweb.staging_agent import StagingAgent, decide_accept, plan_staging
from apps.immoweb.staging_qa_gate import (
    decide_gate,
    gate_to_quality_report,
    run_architectural_gate,
)
from apps.immoweb.staging_room_analysis import analyze_room_image, resolve_room_type
from apps.immoweb.staging_structure import estimate_depth_map, style_furniture_rules

logger = logging.getLogger("omnia.staging_professional")

PIPELINE_ID = "professional_v1"

_B2C_RAILS = frozenset({"b2c_preview", "b2c_stripe"})


def pipeline_flag_on() -> bool:
    """Raw env flag — does not mean every job uses professional."""
    v = (os.environ.get("OMNIA_STAGING_PIPELINE") or "nano").strip().lower()
    return v in ("professional", "pro", "geom", "masked")


def pipeline_enabled() -> bool:
    """Backward-compatible alias of pipeline_flag_on()."""
    return pipeline_flag_on()


def _force_b2c_professional() -> bool:
    return (os.environ.get("OMNIA_STAGING_PIPELINE_FORCE_B2C") or "").strip().lower() in (
        "1", "true", "yes", "on",
    )


def job_is_b2b_gestionale(doc: Optional[dict]) -> bool:
    """Agency credit jobs (ImmoWeb gestionale), not ImmobilCloud B2C."""
    if not doc:
        return False
    rail = (doc.get("payment_rail") or "").strip().lower()
    if rail in _B2C_RAILS:
        return False
    agency_id = doc.get("agency_id")
    return bool(agency_id)


def pipeline_enabled_for_job(doc: Optional[dict]) -> bool:
    """Professional path only when flag ON and job is gestionale (unless FORCE_B2C)."""
    if not pipeline_flag_on():
        return False
    if job_is_b2b_gestionale(doc):
        return True
    if _force_b2c_professional():
        return True
    return False


async def run_professional_pipeline(
    *,
    job_id: str,
    db,
    doc: dict,
    src: str,
    agent: StagingAgent,
    mark_stage,
    mark_root,
    fail,
    # injected from virtual_staging to avoid circular imports at module load
    sequential_furniture_erase,
    apartment_stage,
    flux_inpaint,
    stage_sam2_mask,
    oneshot_prompt,
    nano_banana_edit,
    resolve_image_url_for_fal,
    cost_nano: float,
    cost_lora: float,
    cost_flux: float,
) -> Optional[List[dict]]:
    """Returns variants list (possibly empty if all REJECT) or None on hard pipeline fail."""
    mode = doc.get("mode") or "standard"
    style = doc.get("style") or "modern"
    user_room = doc.get("room_type") or "auto"
    user_confirmed = bool(doc.get("room_type_confirmed"))
    variant_mode = doc.get("variant_mode") or "same_style"
    styles_list = doc.get("styles_list") or []
    crm_fragment = None

    # ── Stage 0: analysis (reuse job analysis if Stage 0 already ran) ─
    t0 = monotonic()
    await mark_stage("sam2_mask", {"status": "running", "note": "stage0_room_analysis"})
    analysis = doc.get("room_analysis") if isinstance(doc.get("room_analysis"), dict) else None
    if not analysis or analysis.get("analysis_error"):
        analysis = await analyze_room_image(src)
        agent.charge(0.002, "room_analysis")
    room = resolve_room_type(
        analysis=analysis,
        user_room_type=user_room,
        user_confirmed=user_confirmed,
    )
    # Bind room on job for prompts / captions
    await mark_root({
        "room_analysis": analysis,
        "room_type": room,
        "pipeline_id": PIPELINE_ID,
        "staging_pipeline": "professional",
    })
    if analysis.get("needs_user_confirm") and not user_confirmed and (user_room in ("", "auto", "detect", None)):
        # Soft-block: still proceed with detected/living, but mark for FE
        await mark_root({"room_confirm_recommended": True})

    depth_url = await estimate_depth_map(src)
    structure = {
        "depth_url": depth_url,
        "protected_labels": ["door", "window", "built-in"],
        "engine_notes": ["florence_evf_sam_reuse", "fal_imageutils_depth"],
    }
    await mark_root({"structure_lock": structure})
    await mark_stage("sam2_mask", {
        "status": "done",
        "duration_ms": int((monotonic() - t0) * 1000),
        "note": f"analysis:{analysis.get('room_type')}:{analysis.get('room_type_confidence')}",
        "cost_usd": 0.002,
    })

    base_image = src
    erase_meta: Dict[str, Any] = {}

    # ── Stage 2: selective erase (empty + reverse) ────────────────────
    if mode in ("reverse", "empty"):
        t0 = monotonic()
        await mark_stage("furniture_removal", {"status": "running", "note": "selective_erase_masked"})
        try:
            base_image, removal_cost, erase_meta = await sequential_furniture_erase(src)
            agent.charge(removal_cost, "furniture_removal", engine=erase_meta.get("engine"))
            await mark_root({"erase_meta": erase_meta, "empty_url": base_image})
            await mark_stage("furniture_removal", {
                "status": "done",
                "duration_ms": int((monotonic() - t0) * 1000),
                "cost_usd": round(removal_cost, 4),
                "engine": erase_meta.get("engine"),
                "note": "professional_selective_erase",
            })
        except Exception as e:
            await fail("furniture_removal", "Rimozione arredo", e)
            return None

        # ── Stage 3: empty QA ─────────────────────────────────────────
        empty_gate = await run_architectural_gate(
            src, base_image, expected_room=room, mode="empty", style="empty", analysis=analysis,
        )
        empty_gate["verdict"] = decide_gate(
            hard_issues=list(empty_gate.get("hard_issues") or []),
            soft_score=float(empty_gate.get("soft_score") or 0),
            retries_left=0,
            can_afford=False,
            unverifiable=bool(empty_gate.get("unverifiable")),
        )
        agent.record_quality("empty_gate", gate_to_quality_report(empty_gate), empty_gate["verdict"])
        await mark_root({"empty_qa": empty_gate})
        if empty_gate["verdict"] == "REJECT":
            await mark_root({
                "status": "failed",
                "error": "architecture_reject_empty:" + ",".join(empty_gate.get("hard_issues") or [])[:180],
                "qa_verdict": "REJECT",
            })
            return []

    variants: List[dict] = []

    if mode == "empty":
        await mark_stage("flux_inpaint", {
            "status": "done", "duration_ms": 0, "cost_usd": 0,
            "note": "skipped_empty_mode", "engine": "none",
        })
        eg = empty_gate if "empty_gate" in locals() else {"verdict": "ACCEPT", "hard_issues": []}
        variants = [{
            "url": base_image,
            "style": "empty",
            "upscaled": False,
            "engine": erase_meta.get("engine") or "erase",
            "qa_verdict": eg.get("verdict") or "ACCEPT",
            "hard_issues": eg.get("hard_issues") or [],
            "room_type": room,
            "quality_score": float(eg.get("soft_score") or 0.8),
            "quality_decision": "accept" if (eg.get("verdict") == "ACCEPT") else "reject",
        }]
        await mark_stage("upscale", {"status": "done", "duration_ms": 0, "cost_usd": 0, "note": "skipped"})
        return [v for v in variants if str(v.get("qa_verdict")).upper() == "ACCEPT"]

    # ── Stage 4: furnish / restyle ────────────────────────────────────
    t0 = monotonic()
    await mark_stage("flux_inpaint", {"status": "running", "note": "professional_furnish"})
    style_keys = styles_list[: max(1, int(doc.get("num_variants") or 1))] if variant_mode == "multi_style" and styles_list else [style]
    if mode == "empty":
        style_keys = ["empty"]

    # Rebuild agent styles with binding room
    agent.plan.room_type = room
    agent.plan.styles = style_keys
    agent.plan.num_variants = len(style_keys)

    engine_used = "apartment_staging_lora"
    for sk in style_keys:
        rules = style_furniture_rules(sk, room)
        prompt = (
            f"Virtually stage this {room} photo for an Italian real-estate listing. "
            f"Style rules: {rules}. "
            "CRITICAL: do not change room function; do not add/remove doors or windows; "
            "do not invent built-in wardrobes or walls; keep camera angle and architecture identical."
        )
        if crm_fragment:
            prompt = f"{prompt} {crm_fragment}"
        urls: List[str] = []
        try:
            urls = await apartment_stage(base_image, prompt, num_images=1)
            agent.charge(cost_lora, f"furnish_lora:{sk}")
        except Exception as lora_err:
            logger.warning("apartment LoRA failed style=%s: %s — flux inpaint fallback", sk, lora_err)
            engine_used = "flux_inpaint_fallback"
            try:
                mask_url = await stage_sam2_mask(base_image, for_furniture=True)
                urls = await flux_inpaint(base_image, mask_url, prompt, num_images=1)
                agent.charge(cost_flux, f"furnish_flux:{sk}")
            except Exception as flux_err:
                logger.warning("flux furnish failed style=%s: %s", sk, flux_err)
                urls = []

        # Optional nano creative pass — only kept if gate ACCEPT
        nano_url = None
        if urls and agent.can_spend(cost_nano) and (os.environ.get("OMNIA_STAGING_NANO_CREATIVE") or "").lower() in ("1", "true", "yes"):
            try:
                nano_prompt = oneshot_prompt(mode, sk, room, crm_fragment)
                nano_prompt += (
                    f" The room function is {room}. NEVER turn it into a different room. "
                    "NEVER invent doors, windows, or built-in wardrobes."
                )
                nano_url = await nano_banana_edit(src if mode == "standard" else base_image, nano_prompt, resolution="1K")
                agent.charge(cost_nano, f"nano_creative:{sk}")
            except Exception as ne:
                logger.warning("nano creative skipped: %s", ne)

        candidates = list(urls) + ([nano_url] if nano_url else [])
        accepted_for_style = None
        last_gate = None
        for cand in candidates:
            gate = await run_architectural_gate(
                src, cand, expected_room=room, mode=mode, style=sk, analysis=analysis,
            )
            gate["verdict"] = decide_gate(
                hard_issues=list(gate.get("hard_issues") or []),
                soft_score=float(gate.get("soft_score") or 0),
                retries_left=1 if agent.can_spend(cost_lora) else 0,
                can_afford=agent.can_spend(cost_lora),
                unverifiable=bool(gate.get("unverifiable")),
            )
            last_gate = gate
            agent.record_quality(f"final_gate:{sk}", gate_to_quality_report(gate), gate["verdict"])
            if gate["verdict"] == "ACCEPT":
                accepted_for_style = {
                    "url": cand,
                    "style": sk,
                    "upscaled": False,
                    "engine": engine_used,
                    "qa_verdict": "ACCEPT",
                    "hard_issues": [],
                    "soft_score": gate.get("soft_score"),
                    "qa": gate,
                    "room_type": room,
                    "quality_score": float(gate.get("soft_score") or 0),
                    "quality_decision": "accept",
                }
                break
            if gate["verdict"] == "RETRY" and agent.can_spend(cost_lora):
                # One targeted retry with stronger architecture lock
                try:
                    retry_prompt = prompt + (
                        " RETRY: previous result violated architecture or room function. "
                        "Keep EXACT same doors/windows/walls/floor. Only movable furniture."
                    )
                    retry_urls = await apartment_stage(base_image, retry_prompt, num_images=1)
                    agent.charge(cost_lora, f"furnish_retry:{sk}")
                    agent.furnish_retries += 1
                    if retry_urls:
                        gate2 = await run_architectural_gate(
                            src, retry_urls[0], expected_room=room, mode=mode, style=sk, analysis=analysis,
                        )
                        gate2["verdict"] = decide_gate(
                            hard_issues=list(gate2.get("hard_issues") or []),
                            soft_score=float(gate2.get("soft_score") or 0),
                            retries_left=0,
                            can_afford=False,
                            unverifiable=bool(gate2.get("unverifiable")),
                        )
                        last_gate = gate2
                        if gate2["verdict"] == "ACCEPT":
                            accepted_for_style = {
                                "url": retry_urls[0],
                                "style": sk,
                                "upscaled": False,
                                "engine": engine_used + "_retry",
                                "qa_verdict": "ACCEPT",
                                "hard_issues": [],
                                "soft_score": gate2.get("soft_score"),
                                "qa": gate2,
                                "room_type": room,
                                "quality_score": float(gate2.get("soft_score") or 0),
                                "quality_decision": "accept",
                            }
                            break
                except Exception as re:
                    logger.warning("furnish retry failed: %s", re)

        if accepted_for_style:
            variants.append(accepted_for_style)
        elif last_gate:
            # Keep rejected for audit but not publishable
            variants.append({
                "url": candidates[0] if candidates else base_image,
                "style": sk,
                "upscaled": False,
                "engine": engine_used,
                "qa_verdict": last_gate.get("verdict") or "REJECT",
                "hard_issues": last_gate.get("hard_issues") or [],
                "soft_score": last_gate.get("soft_score"),
                "qa": last_gate,
                "room_type": room,
                "quality_score": float(last_gate.get("soft_score") or 0),
                "quality_decision": "reject",
                "publishable": False,
            })

    await mark_stage("flux_inpaint", {
        "status": "done",
        "duration_ms": int((monotonic() - t0) * 1000),
        "cost_usd": round(sum(1 for v in variants if v.get("qa_verdict") == "ACCEPT") * cost_lora, 4),
        "engine": engine_used,
        "note": f"accepted={sum(1 for v in variants if v.get('qa_verdict')=='ACCEPT')}/{len(style_keys)}",
    })
    await mark_stage("upscale", {"status": "done", "duration_ms": 0, "cost_usd": 0, "note": "skipped_professional"})

    accepted = [v for v in variants if str(v.get("qa_verdict")).upper() == "ACCEPT"]
    await mark_root({
        "qa_summary": {
            "accepted": len(accepted),
            "total": len(variants),
            "room_type": room,
            "pipeline_id": PIPELINE_ID,
        },
        "variants_all": variants,  # audit trail including rejects
    })
    return accepted
