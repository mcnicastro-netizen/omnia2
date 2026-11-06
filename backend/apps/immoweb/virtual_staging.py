"""OMNIA — M5.S4 Virtual Staging (D-033 + D-125 + D-136).

Catalog / erase / furnish / media / B2C / API live in sibling staging_* modules
(MOVE-ONLY split). This module keeps the orchestrator (_run_pipeline) + CRM/URL
helpers and re-exports public symbols for stable imports.

Primary pipeline (Founder OK 19-Ott-2026):
  Nano Banana 2 one-shot (fal = Gemini 3.1 Flash Image) × up to 4 styles
  + vision critic (Gemini Flash) → optional single retry per failed style

Legacy fallback (EVF-SAM + Ideogram + apartment LoRA) if nano engine fails
or OMNIA_STAGING_ENGINE=legacy.

CRM-aware prompt fragment + watermark "Render virtuale OMNIA".
No third-party staging SaaS embed.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

import fal_client
from fastapi import HTTPException

from shared.db.connection import Database
from apps.billing.plans import CREDIT_COSTS
from apps.billing.routes import debit_credits
from apps.immoweb.staging_agent import (
    StagingAgent,
    critique_empty_from_meta,
    critique_furnished_heuristic,
    decide_accept,
    plan_staging,
)

from apps.immoweb.staging_catalog import (
    DEFAULT_MULTI_STYLES,
    EMPTY_ROOM_PROMPT,
    NEGATIVE_PROMPT,
    ROOM_LABELS,
    ROOM_TYPES,
    STYLES,
    _build_prompt,
    _photo_caption,
)
from apps.immoweb.staging_erase import (
    ARCHITECTURE_KEEP_LABELS,
    COST_BRIA,
    COST_EVF_SAM,
    COST_FLORENCE,
    COST_IDEOGRAM,
    COST_SAM2,
    ERASE_LABEL_ORDER,
    EVF_ARCHITECTURE_NEGATIVE,
    EVF_FURNITURE_PROMPTS,
    FURNITURE_DETECT_LABELS,
    MODEL_BRIA_ERASER,
    MODEL_EVF_SAM,
    MODEL_FAL_OBJECT_REMOVAL,
    MODEL_FLORENCE_DET,
    MODEL_IDEOGRAM_ERASE,
    MODEL_SAM2,
    MODEL_SAM2_BOX,
    _architecture_keep_mask,
    _bbox_iou,
    _bria_erase,
    _doorway_brightness,
    _erase_mask_url,
    _erase_once,
    _evf_furniture_union_mask,
    _fal_object_removal,
    _florence_furniture_boxes,
    _ideogram_erase,
    _mask_url_from_entry,
    _merge_furniture_mask_urls,
    _opening_brightness_map,
    _padded_box_mask_url,
    _sam2_mask_from_boxes,
    _sequential_furniture_erase,
    _sort_erase_boxes,
    _stage_sam2_mask,
    _upload_pil_mask,
    _white_ratio,
    merge_furniture_masks_from_images,
    nms_bboxes,
    _ERASE_PASS1_MAX,
    _ERASE_PASS2_MAX,
    _ERASE_PASS3_MAX,
    _MASK_AREA_MAX,
    _MASK_AREA_MIN,
    _MASK_BOX_AREA_MAX,
    _MASK_MERGE_CAP,
)
from apps.immoweb.staging_furnish import (
    COST_FLUX,
    COST_NANO_BANANA,
    COST_STAGING_LORA,
    COST_UPSCALE,
    COST_VISION_CRITIC,
    MODEL_APARTMENT_STAGING,
    MODEL_FLUX_INPAINT,
    MODEL_NANO_BANANA_EDIT,
    MODEL_UPSCALE,
    STAGING_ENGINE,
    VISION_CRITIC_MODEL,
    _STYLE_EN,
    _STYLE_ONESHOT_EN,
    _apartment_stage,
    _flux_inpaint,
    _nano_banana_edit,
    _oneshot_prompt,
    _stage_upscale,
    _staging_lora_prompt,
    _vision_critique_staging,
)

from apps.immoweb.staging_media import (
    MAX_PHOTO_WIDTH,
    _apply_watermark,
    _fetch_variant_bytes,
    _persist_staging_jpeg,
)
from apps.immoweb.staging_b2c import (
    _auto_save_b2c_variant,
    _listing_photo_url,
    _persist_b2c_preview_variants,
    _pick_listing_photo,
    fulfill_paid_staging_render,
    start_b2c_preview_job,
)
from apps.immoweb.staging_api import (
    ALLOWED_MIME,
    MAX_UPLOAD_MB,
    SOFT_RATE_LIMIT_AGENCY_HOUR,
    SOFT_RATE_LIMIT_USER_HOUR,
    SaveToPropertyBody,
    StagingGenerateBody,
    StagingJobOut,
    StagingStages,
    StagingVariantOut,
    _job_to_out,
    _rate_limit,
    delete_job,
    download_watermarked,
    generate_staging,
    get_job,
    list_history,
    list_styles,
    router,
    save_variant_to_property,
    staging_credits_check,
    upload_source_image,
    variant_as_dataurl,
)


logger = logging.getLogger("omnia.staging")

STAGING_CREDIT_COST = int(CREDIT_COSTS.get("virtual_staging_render") or 18)

JOB_TTL_DAYS = 30
STALE_JOB_MINUTES = 10


# ─── Schemas ─────────────────────────────────────────────────────


# ─── Helpers ─────────────────────────────────────────────────────


# ─── CRM-aware prompt (Gemini, best-effort) ──────────────────────
async def _crm_prompt_fragment(db, agency_id: Optional[str], property_id: str) -> tuple[Optional[str], Optional[str]]:
    """Returns (english_prompt_fragment, italian_summary) or (None, None)."""
    query: Dict[str, Any] = {"id": property_id}
    if agency_id:
        query["agency_id"] = agency_id
    prop = await db.properties.find_one(query, {"_id": 0})
    if not prop:
        return None, None

    price = (prop.get("price") or {}).get("amount") if isinstance(prop.get("price"), dict) else prop.get("price")
    ctx = {
        "tipologia": prop.get("property_type"),
        "città": prop.get("city"),
        "zona": prop.get("zone") or prop.get("address"),
        "prezzo": price,
        "superficie_mq": (prop.get("surfaces") or {}).get("total") if isinstance(prop.get("surfaces"), dict) else prop.get("surface"),
        "operazione": prop.get("operation"),
        "titolo": prop.get("title"),
    }
    from shared.llm import try_resolve_api_key

    api_key = try_resolve_api_key()
    if not api_key:
        return None, None
    try:
        from shared.llm.chat import LlmChat, UserMessage  # type: ignore

        chat = LlmChat(
            api_key=api_key,
            session_id=f"staging-crm-{uuid4()}",
            system_message=(
                "Sei un interior designer esperto di virtual staging immobiliare italiano. "
                "Dato il contesto CRM di un immobile, genera UNA breve frase IN INGLESE (max 25 parole) "
                "da aggiungere a un prompt di image generation per arredare la stanza in modo ottimale "
                "per il target buyer di quell'immobile (fascia prezzo, zona, tipologia). "
                "Rispondi SOLO con la frase inglese, senza virgolette né spiegazioni."
            ),
        ).with_model("gemini", "gemini-3-flash-preview")
        import json as _json

        raw = await asyncio.wait_for(
            chat.send_message(UserMessage(text=_json.dumps(ctx, ensure_ascii=False, default=str))),
            timeout=15,
        )
        fragment = str(raw).strip().strip('"').strip()
        if not fragment or len(fragment) > 300:
            return None, None
        summary = f"{ctx.get('tipologia') or 'immobile'} · {ctx.get('città') or '—'}" + (
            f" · €{int(price):,}".replace(",", ".") if price else ""
        )
        return fragment, summary
    except Exception as e:
        logger.warning("CRM-aware prompt failed (%s), using static prompt", e)
        return None, None


# ─── Source URL helpers (B2C private media → fal) ─────────────────


async def _resolve_image_url_for_fal(src: str) -> str:
    """fal.ai needs a fetchable URL; private `/api/media/…` is re-uploaded to fal."""
    raw = (src or "").strip()
    if not raw:
        raise RuntimeError("source_url vuota")
    if not raw.startswith("/api/media/"):
        return raw
    from shared.storage import get_object, ObjStoreError

    storage_path = raw[len("/api/media/"):]
    try:
        data, ct = get_object(storage_path)
    except ObjStoreError as e:
        raise RuntimeError(f"media non leggibile: {e}") from e
    if not data:
        raise RuntimeError("media vuoto")
    import tempfile

    ext = "jpg"
    if ct and "png" in ct:
        ext = "png"
    elif ct and "webp" in ct:
        ext = "webp"
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        return await asyncio.to_thread(fal_client.upload_file, tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ─── Pipeline stages ─────────────────────────────────────────────


async def _run_pipeline(job_id: str, db) -> None:
    from time import monotonic

    doc = await db.virtual_staging_jobs.find_one({"id": job_id})
    if not doc:
        return

    stage_idx = {s["name"]: i for i, s in enumerate(doc.get("stages", []))}

    async def _mark_stage(name: str, patch: dict) -> None:
        i = stage_idx[name]
        await db.virtual_staging_jobs.update_one(
            {"id": job_id},
            {"$set": {f"stages.{i}.{k}": v for k, v in patch.items()}},
        )

    async def _mark_root(patch: dict) -> None:
        await db.virtual_staging_jobs.update_one({"id": job_id}, {"$set": patch})

    async def _fail(stage_name: str, prefix: str, e: Exception) -> None:
        logger.exception("%s stage failed for %s", prefix, job_id)
        await _mark_stage(stage_name, {"status": "failed", "error": str(e)[:300]})
        await _mark_root({
            "status": "failed",
            "error": f"{prefix}: {str(e)[:200]}",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        })

    await _mark_root({"status": "running"})
    src_raw = doc["source_url"]
    mode = doc.get("mode", "standard")
    variant_mode = doc.get("variant_mode", "same_style")
    num_variants = doc.get("num_variants", 1)
    engine_pref = STAGING_ENGINE if STAGING_ENGINE in ("nano_banana", "legacy") else "nano_banana"

    try:
        src = await _resolve_image_url_for_fal(src_raw)
        if src != src_raw:
            await _mark_root({"source_url_fal": src})
    except Exception as e:
        await _fail("sam2_mask", "Resolve source", e)
        return

    # Stage 0 (all engines): bind room type via vision — never silent bedroom default
    from apps.immoweb.staging_room_analysis import analyze_room_image, resolve_room_type

    room_analysis = await analyze_room_image(src)
    bound_room = resolve_room_type(
        analysis=room_analysis,
        user_room_type=doc.get("room_type"),
        user_confirmed=bool(doc.get("room_type_confirmed")),
    )
    doc["room_analysis"] = room_analysis
    doc["room_type"] = bound_room
    await _mark_root({
        "room_analysis": room_analysis,
        "room_type": bound_room,
        "room_confirm_recommended": bool(room_analysis.get("needs_user_confirm")),
    })

    agent = StagingAgent(plan_staging(
        mode=mode,
        style=doc.get("style") or "modern",
        room_type=bound_room,
        num_variants=num_variants,
        variant_mode=variant_mode,
        styles_list=doc.get("styles_list") or DEFAULT_MULTI_STYLES,
        engine=engine_pref,
    ))
    await _mark_root({"agent_plan": agent.plan.to_dict()})

    # CRM-aware prompt (best-effort, silent)
    crm_fragment = None
    if doc.get("property_id"):
        crm_fragment, crm_summary = await _crm_prompt_fragment(db, doc.get("agency_id"), doc["property_id"])
        if crm_summary:
            await _mark_root({"crm_context": crm_summary})

    variants: List[dict] = []
    engine_used = "none"
    nano_ok = False

    # ── Professional pipeline (D-136) — gestionale B2B only by default ────
    from apps.immoweb.staging_professional import (
        pipeline_enabled_for_job,
        run_professional_pipeline,
    )

    if pipeline_enabled_for_job(doc):
        accepted = await run_professional_pipeline(
            job_id=job_id,
            db=db,
            doc=doc,
            src=src,
            agent=agent,
            mark_stage=_mark_stage,
            mark_root=_mark_root,
            fail=_fail,
            sequential_furniture_erase=_sequential_furniture_erase,
            apartment_stage=_apartment_stage,
            flux_inpaint=_flux_inpaint,
            stage_sam2_mask=_stage_sam2_mask,
            oneshot_prompt=_oneshot_prompt,
            nano_banana_edit=_nano_banana_edit,
            resolve_image_url_for_fal=_resolve_image_url_for_fal,
            cost_nano=COST_NANO_BANANA,
            cost_lora=COST_STAGING_LORA,
            cost_flux=COST_FLUX,
        )
        if accepted is None:
            return  # hard fail already marked
        variants = accepted
        engine_used = "professional_v1"
        nano_ok = True  # skip nano/legacy paths
        if not variants:
            await _mark_root({
                "status": "failed",
                "error": "architecture_reject: nessuna variante ha superato i controlli architettonici",
                "qa_verdict": "REJECT",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "agent_summary": agent.summary(),
            })
            return

    # ── Primary: Nano Banana one-shot × styles + vision critic ─────────────
    if (not nano_ok) and agent.plan.engine == "nano_banana":
        try:
            t0 = monotonic()
            await _mark_stage("sam2_mask", {
                "status": "done", "duration_ms": 0, "cost_usd": 0,
                "note": "skipped_nano_banana_oneshot",
            })
            # Keep furniture_removal RUNNING during empty/reverse oneshot so the FE
            # progress label shows "Svuotamento…" instead of jumping to "Arredamento…".
            # standard mode has no furniture_removal stage — skip.
            if "furniture_removal" in stage_idx:
                if agent.plan.need_erase:
                    await _mark_stage("furniture_removal", {
                        "status": "running",
                        "engine": "nano_banana_2",
                        "note": "oneshot_erase_in_progress",
                    })
                else:
                    await _mark_stage("furniture_removal", {
                        "status": "done", "duration_ms": 0, "cost_usd": 0,
                        "note": "skipped_standard",
                        "engine": "nano_banana_2",
                    })
            # Empty mode: generation is the erase itself — keep flux_inpaint queued
            # until erase oneshot finishes, then mark done. Furnish modes run flux as running.
            if mode != "empty":
                await _mark_stage("flux_inpaint", {"status": "running"})

            style_keys = agent.plan.styles[: agent.plan.num_variants]

            async def _gen_style(sk: str) -> dict:
                prompt = _oneshot_prompt(mode, sk, agent.plan.room_type, crm_fragment)
                url = await _nano_banana_edit(src, prompt, resolution="1K")
                return {"url": url, "style": sk, "upscaled": False, "engine": "nano_banana_2"}

            raw_variants = list(await asyncio.gather(
                *[_gen_style(sk) for sk in style_keys],
                return_exceptions=True,
            ))
            variants = []
            for sk, item in zip(style_keys, raw_variants):
                if isinstance(item, Exception):
                    logger.warning("nano oneshot failed style=%s: %s", sk, item)
                    continue
                agent.charge(COST_NANO_BANANA, f"nano_oneshot:{sk}")
                variants.append(item)
            if not variants:
                raise RuntimeError("Nano Banana: nessuna variante generata")

            if agent.plan.need_erase and "furniture_removal" in stage_idx:
                await _mark_stage("furniture_removal", {
                    "status": "done",
                    "duration_ms": int((monotonic() - t0) * 1000) if mode == "empty" else 0,
                    "cost_usd": round(COST_NANO_BANANA, 4) if mode == "empty" else 0,
                    "note": "oneshot_includes_erase",
                    "engine": "nano_banana_2",
                })
            if mode == "empty":
                await _mark_stage("flux_inpaint", {
                    "status": "done", "duration_ms": 0, "cost_usd": 0,
                    "note": "skipped_empty_oneshot",
                    "engine": "nano_banana_2",
                })
            else:
                await _mark_stage("flux_inpaint", {"status": "running"})

            # Vision critic per variant (parallel)
            critiques = list(await asyncio.gather(*[
                _vision_critique_staging(src, v["url"], style=v["style"], mode=mode)
                for v in variants
            ]))
            for v, q in zip(variants, critiques):
                agent.charge(COST_VISION_CRITIC, f"vision_critic:{v['style']}")
                decision = decide_accept(
                    q,
                    retries_left=1 if agent.can_spend(COST_NANO_BANANA) else 0,
                    can_afford=agent.can_spend(COST_NANO_BANANA),
                )
                hard = [i for i in (q.issues or []) if i in (
                    "invented_windows", "architecture_fail", "room_function_changed",
                    "invented_door", "invented_built_in", "geometry_broken",
                )]
                v["quality_score"] = round(q.score, 3)
                v["quality_decision"] = decision
                v["qa_verdict"] = {
                    "accept": "ACCEPT",
                    "accept_with_warning": "ACCEPT",
                    "retry": "RETRY",
                    "reject": "REJECT",
                }.get(decision, "MANUAL_REVIEW")
                v["hard_issues"] = hard
                v["room_type"] = bound_room
                v["publishable"] = decision in ("accept", "accept_with_warning") and not hard
                if hard and decision == "accept":
                    # Aesthetic score cannot override architectural hard fail
                    v["quality_decision"] = "reject"
                    v["qa_verdict"] = "REJECT"
                    v["publishable"] = False
                agent.record_quality(f"style:{v['style']}", q, v["quality_decision"])

            # Retry styles that invent openings / fail architecture (budget-capped, max 2).
            retry_idxs = []
            for i, v in enumerate(variants):
                if v.get("quality_decision") != "retry":
                    continue
                qphase = agent.quality.get(f"style:{v['style']}") or {}
                issues = qphase.get("issues") or []
                # Prefer invented_windows / architecture first
                pri = 0 if ("invented_windows" in issues or "architecture_fail" in issues) else 1
                retry_idxs.append((pri, float(v.get("quality_score") or 0), i))
            retry_idxs.sort()  # architecture fails first, then lowest score
            # Founder: max 1 retry per job (anti-aperture / qualità).
            retries_done = 0
            for _, _, retry_idx in retry_idxs:
                if retries_done >= 1 or not agent.can_spend(COST_NANO_BANANA):
                    break
                if agent.furnish_retries >= 1:
                    break
                agent.furnish_retries += 1
                retries_done += 1
                sk = variants[retry_idx]["style"]
                logger.info(
                    "nano retry style=%s score=%.2f issues=%s",
                    sk, variants[retry_idx].get("quality_score"),
                    (agent.quality.get(f"style:{sk}") or {}).get("issues"),
                )
                prompt = _oneshot_prompt(mode, sk, agent.plan.room_type, crm_fragment)
                prompt = (
                    prompt
                    + " RETRY FIX: the previous edit illegally invented windows. "
                    "Keep EVERY wall blank where the source has no window. "
                    "ZERO new windows, ZERO skylights, ZERO glass wall panels. "
                    "Preserve only the existing door openings on the left. "
                    "No yellow cast; no leftover gym or old furniture."
                )
                try:
                    new_url = await _nano_banana_edit(src, prompt, resolution="1K")
                    agent.charge(COST_NANO_BANANA, f"nano_retry:{sk}")
                    q2 = await _vision_critique_staging(src, new_url, style=sk, mode=mode)
                    agent.charge(COST_VISION_CRITIC, f"vision_critic_retry:{sk}")
                    d2 = decide_accept(q2, retries_left=0, can_afford=False)
                    # Prefer non-invented architecture even if score similar
                    old_inv = bool(
                        (agent.quality.get(f"style:{sk}") or {})
                        .get("signals", {})
                        .get("invented_openings")
                    )
                    new_inv = bool(q2.signals.get("invented_openings"))
                    take = (not new_inv and old_inv) or (
                        q2.score >= float(variants[retry_idx].get("quality_score") or 0)
                        and not new_inv
                    )
                    hard2 = [i for i in (q2.issues or []) if i in (
                        "invented_windows", "architecture_fail", "room_function_changed",
                        "invented_door", "invented_built_in", "geometry_broken",
                    )]
                    if take or (not new_inv and q2.score >= 0.55):
                        pub = d2 in ("accept", "accept_with_warning") and not hard2
                        variants[retry_idx] = {
                            **variants[retry_idx],
                            "url": new_url,
                            "quality_score": round(q2.score, 3),
                            "quality_decision": "reject" if hard2 else d2,
                            "qa_verdict": "REJECT" if hard2 else {
                                "accept": "ACCEPT",
                                "accept_with_warning": "ACCEPT",
                                "retry": "RETRY",
                                "reject": "REJECT",
                            }.get(d2, "MANUAL_REVIEW"),
                            "hard_issues": hard2,
                            "room_type": bound_room,
                            "publishable": pub,
                        }
                    agent.record_quality(f"style:{sk}:retry", q2, variants[retry_idx].get("quality_decision") or d2)
                except Exception as retry_err:
                    logger.warning("nano retry failed style=%s: %s", sk, retry_err)

            # Prefer highest critic score among publishable first; keep rejects for audit
            from apps.immoweb.staging_qa_gate import variant_is_publishable as _vip
            variants.sort(
                key=lambda v: (
                    1 if _vip(v) else 0,
                    float(v.get("quality_score") or 0),
                ),
                reverse=True,
            )
            publishable = [v for v in variants if _vip(v)]
            engine_used = "nano_banana_2_oneshot"
            stage_cost = COST_NANO_BANANA * len(style_keys) + (
                COST_NANO_BANANA if agent.furnish_retries else 0
            )
            if mode != "empty":
                await _mark_stage("flux_inpaint", {
                    "status": "done",
                    "duration_ms": int((monotonic() - t0) * 1000),
                    "cost_usd": round(stage_cost, 4),
                    "engine": engine_used,
                    "note": (
                        "styles=" + ",".join(v["style"] for v in variants)
                        + "|scores=" + ",".join(f"{v.get('quality_score', 0):.2f}" for v in variants)
                    )[:280],
                })
            await _mark_stage("upscale", {
                "status": "done", "duration_ms": 0, "cost_usd": 0,
                "note": "skipped_nano_banana",
            })
            await _mark_root({
                "agent_quality": agent.quality,
                "erase_meta": {"engine": "nano_oneshot"},
                "qa_summary": {
                    "accepted": len(publishable),
                    "total": len(variants),
                    "room_type": bound_room,
                    "pipeline_id": "nano_oneshot",
                },
                "variants_all": variants,
            })
            if not publishable:
                await _mark_root({
                    "status": "failed",
                    "error": "architecture_reject: nessuna variante ha superato i controlli architettonici",
                    "qa_verdict": "REJECT",
                    "variants": variants,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "agent_summary": agent.summary(),
                })
                return
            variants = publishable
            nano_ok = True
        except Exception as e:
            logger.exception("nano_banana primary path failed — legacy fallback: %s", e)
            await _mark_root({"nano_fallback_error": str(e)[:300]})
            # Rebuild agent plan for legacy budgets
            agent = StagingAgent(plan_staging(
                mode=mode,
                style=doc.get("style") or "modern",
                room_type=bound_room,
                num_variants=num_variants,
                variant_mode=variant_mode,
                styles_list=doc.get("styles_list") or DEFAULT_MULTI_STYLES,
                engine="legacy",
            ))
            await _mark_root({"agent_plan": agent.plan.to_dict()})

    # ── Legacy: EVF erase + apartment LoRA ─────────────────────────────────
    if not nano_ok:
        mask_url: Optional[str] = None
        try:
            t0 = monotonic()
            await _mark_stage("sam2_mask", {"status": "running"})
            if agent.plan.need_erase:
                await _mark_stage("sam2_mask", {
                    "status": "done",
                    "duration_ms": int((monotonic() - t0) * 1000),
                    "cost_usd": 0,
                    "note": "florence_detect_inside_erase",
                })
            else:
                mask_url = await _stage_sam2_mask(src, for_furniture=False)
                await _mark_root({"mask_url": mask_url})
                await _mark_stage("sam2_mask", {
                    "status": "done",
                    "duration_ms": int((monotonic() - t0) * 1000),
                    "cost_usd": COST_SAM2,
                })
                agent.charge(COST_SAM2, "sam2_mask")
        except Exception as e:
            await _fail("sam2_mask", "SAM2", e)
            return

        base_image = src
        erase_meta: Dict[str, Any] = {}
        if agent.plan.need_erase:
            try:
                t0 = monotonic()
                await _mark_stage("furniture_removal", {"status": "running"})
                base_image, removal_cost, erase_meta = await _sequential_furniture_erase(src)
                agent.charge(removal_cost, "furniture_removal", engine=erase_meta.get("engine"))
                empty_q = critique_empty_from_meta(erase_meta)
                decision = decide_accept(empty_q, retries_left=0, can_afford=False)
                agent.record_quality("empty", empty_q, decision)
                await _mark_root({"erase_meta": erase_meta, "agent_quality": agent.quality})
                await _mark_stage("furniture_removal", {
                    "status": "done",
                    "duration_ms": int((monotonic() - t0) * 1000),
                    "cost_usd": round(removal_cost, 4),
                    "engine": erase_meta.get("engine"),
                    "note": f"erased={','.join(erase_meta.get('erased') or [])}"[:280],
                })
            except Exception as e:
                await _fail("furniture_removal", "Rimozione arredo", e)
                return

        if not agent.plan.need_furnish:
            variants = [{"url": base_image, "style": "empty", "upscaled": False}]
            await _mark_stage("flux_inpaint", {
                "status": "done", "duration_ms": 0, "cost_usd": 0,
                "note": "skipped_empty_mode", "engine": "none",
            })
        else:
            try:
                t0 = monotonic()
                await _mark_stage("flux_inpaint", {"status": "running"})
                style_keys = agent.plan.styles[: agent.plan.num_variants]
                engine_used = "apartment_staging_lora"
                for sk in style_keys:
                    prompt = _staging_lora_prompt(sk, agent.plan.room_type, crm_fragment)
                    try:
                        urls = await _apartment_stage(
                            base_image, prompt,
                            num_images=1 if variant_mode == "multi_style" else agent.plan.num_variants,
                        )
                    except Exception as lora_err:
                        logger.warning("Apartment staging LoRA failed (%s) — Flux fallback", lora_err)
                        engine_used = "flux_inpaint_fallback"
                        if not mask_url:
                            mask_url = await _stage_sam2_mask(base_image, for_furniture=True)
                            agent.charge(COST_SAM2, "sam2_mask_fallback")
                        urls = await _flux_inpaint(
                            base_image, mask_url,
                            _build_prompt(sk, agent.plan.room_type, crm_fragment),
                            num_images=1 if variant_mode == "multi_style" else agent.plan.num_variants,
                        )
                    variants.extend({"url": u, "style": sk, "upscaled": False} for u in urls)
                    if variant_mode != "multi_style":
                        break
                if not variants:
                    raise RuntimeError("Nessuna variante staging generata")
                stage_cost = (
                    COST_STAGING_LORA if engine_used.startswith("apartment") else COST_FLUX
                ) * len(variants)
                agent.charge(stage_cost, "furnish", engine=engine_used)
                furn_q = critique_furnished_heuristic(
                    style=style_keys[0], engine=engine_used, erase_meta=erase_meta,
                )
                agent.record_quality("furnish", furn_q, decide_accept(furn_q, retries_left=0, can_afford=False))
                await _mark_stage("flux_inpaint", {
                    "status": "done",
                    "duration_ms": int((monotonic() - t0) * 1000),
                    "cost_usd": round(stage_cost, 4),
                    "engine": engine_used,
                })
            except Exception as e:
                await _fail("flux_inpaint", "Staging", e)
                return

        t0 = monotonic()
        await _mark_stage("upscale", {"status": "running"})
        if not agent.plan.need_furnish or not engine_used.startswith("flux_inpaint"):
            await _mark_stage("upscale", {
                "status": "done", "duration_ms": 0, "cost_usd": 0,
                "note": "skipped",
            })
        else:
            async def _up(v: dict) -> dict:
                try:
                    url = await _stage_upscale(v["url"])
                    return {**v, "url": url or v["url"], "upscaled": bool(url)}
                except Exception as e:
                    logger.warning("Upscale failed: %s", e)
                    return v
            variants = list(await asyncio.gather(*[_up(v) for v in variants]))
            upscaled_n = sum(1 for v in variants if v.get("upscaled"))
            up_cost = COST_UPSCALE * upscaled_n
            agent.charge(up_cost, "upscale")
            await _mark_stage("upscale", {
                "status": "done" if upscaled_n else "failed",
                "duration_ms": int((monotonic() - t0) * 1000),
                "cost_usd": round(up_cost, 4),
            })

    # B2C free preview: persist to /api/media so SellPage img is same-origin + smaller
    try:
        variants = await _persist_b2c_preview_variants(job_id, db, variants)
    except Exception:
        logger.exception("b2c preview persist failed job=%s", job_id)

    total_cost = agent.ledger.spent_usd
    await _mark_root({
        "status": "done",
        "variants": variants,
        "variant_url": variants[0]["url"] if variants else None,
        "cost_total_usd": round(total_cost, 4),
        "agent_summary": agent.summary(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    })

    # Debit only after successful pipeline (no charge on mid-fail).
    # B2C Stripe rail already paid via b2c_purchases — skip agency wallet.
    try:
        doc_paid = await db.virtual_staging_jobs.find_one(
            {"id": job_id},
            {"agency_id": 1, "num_variants": 1, "payment_rail": 1},
        )
        rail = (doc_paid or {}).get("payment_rail")
        aid = (doc_paid or {}).get("agency_id")
        n = max(1, int((doc_paid or {}).get("num_variants") or 1))
        if rail == "b2c_stripe":
            await db.virtual_staging_jobs.update_one(
                {"id": job_id},
                {"$set": {"credits_charged": 0, "payment_rail": "b2c_stripe"}},
            )
            if variants:
                try:
                    await _auto_save_b2c_variant(job_id, db)
                except Exception:
                    logger.exception("b2c staging auto-save failed job=%s", job_id)
        elif aid and variants:
            bal = await debit_credits(
                aid,
                STAGING_CREDIT_COST * n,
                reason="virtual_staging_render",
                ref_id=job_id,
                ref_type="virtual_staging_job",
            )
            await db.virtual_staging_jobs.update_one(
                {"id": job_id},
                {"$set": {"credits_charged": STAGING_CREDIT_COST * n, "credits_balance_after": bal}},
            )
    except HTTPException as e:
        logger.warning("staging debit failed job=%s detail=%s", job_id, e.detail)
        await db.virtual_staging_jobs.update_one(
            {"id": job_id},
            {"$set": {"credits_debit_error": str(e.detail)[:300]}},
        )
    except Exception:
        logger.exception("staging debit unexpected job=%s", job_id)


# ─── Stale-job reaper (called at server startup) ─────────────────
async def reap_stale_jobs() -> int:
    db = Database.get()
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=STALE_JOB_MINUTES)).isoformat()
    res = await db.virtual_staging_jobs.update_many(
        {"status": {"$in": ["pending", "running"]}, "created_at": {"$lt": cutoff}},
        {"$set": {
            "status": "failed",
            "error": "Job interrotto da riavvio del server",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }},
    )
    return res.modified_count

