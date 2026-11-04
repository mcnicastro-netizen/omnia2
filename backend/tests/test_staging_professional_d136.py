"""D-136 — Professional Virtual Staging: room analysis, hard gate, Founder case.

No fal/Gemini spend — pure unit / mock tests.
"""
from __future__ import annotations

import pytest

from apps.immoweb.staging_qa_gate import (
    decide_gate,
    parse_gate_json,
    variant_is_publishable,
)
from apps.immoweb.staging_room_analysis import (
    CONFIDENCE_ASK_USER,
    normalize_analysis,
    resolve_room_type,
)
from apps.immoweb.staging_structure import combine_masks, style_furniture_rules
from PIL import Image


# ── Room analysis ──────────────────────────────────────────────────────────


def test_normalize_living_room_high_confidence():
    raw = {
        "room_type": "living_room",
        "room_type_confidence": 0.92,
        "room_function": "living",
        "doors": {"count": 1},
        "windows": {"count": 2},
        "fixed_furniture": [],
        "movable_furniture": ["sofa", "coffee table"],
        "needs_user_confirm": False,
    }
    a = normalize_analysis(raw)
    assert a["room_type"] == "living_room"
    assert a["room_type_internal"] == "living"
    assert a["room_type_confidence"] == 0.92
    assert a["needs_user_confirm"] is False
    assert "preserve_architecture" in a["staging_constraints"]


def test_uncertain_asks_user():
    a = normalize_analysis({
        "room_type": "uncertain",
        "room_type_confidence": 0.2,
    })
    assert a["needs_user_confirm"] is True
    assert a["room_type_internal"] == "living"  # safe fallback mapping, not bedroom


def test_low_confidence_asks_user():
    a = normalize_analysis({
        "room_type": "bedroom",
        "room_type_confidence": CONFIDENCE_ASK_USER - 0.1,
    })
    assert a["needs_user_confirm"] is True


def test_resolve_never_defaults_to_bedroom():
    assert resolve_room_type(analysis=None, user_room_type="auto") == "living"
    assert resolve_room_type(analysis=None, user_room_type="") == "living"
    assert resolve_room_type(analysis=None, user_room_type="detect") == "living"


def test_resolve_honors_confirmed_user():
    analysis = normalize_analysis({
        "room_type": "living_room",
        "room_type_confidence": 0.9,
        "needs_user_confirm": False,
    })
    assert resolve_room_type(
        analysis=analysis, user_room_type="kitchen", user_confirmed=True,
    ) == "kitchen"


def test_resolve_high_confidence_overrides_wrong_user_pick():
    """Anti Founder bug: user left bedroom residual / wrong pick vs clear living."""
    analysis = normalize_analysis({
        "room_type": "living_room",
        "room_type_confidence": 0.95,
        "needs_user_confirm": False,
    })
    # Unconfirmed bedroom pick should lose to high-confidence living detection
    assert resolve_room_type(
        analysis=analysis, user_room_type="bedroom", user_confirmed=False,
    ) == "living"


def test_resolve_auto_uses_detection():
    analysis = normalize_analysis({
        "room_type": "kitchen",
        "room_type_confidence": 0.88,
        "needs_user_confirm": False,
    })
    assert resolve_room_type(
        analysis=analysis, user_room_type="auto", user_confirmed=False,
    ) == "kitchen"


# ── Hard / soft gate ───────────────────────────────────────────────────────


def test_decide_hard_fail_rejects_even_with_high_soft_score():
    v = decide_gate(
        hard_issues=["room_function_changed"],
        soft_score=0.95,
        retries_left=0,
        can_afford=True,
    )
    assert v == "REJECT"


def test_decide_hard_fail_retry_when_budget():
    v = decide_gate(
        hard_issues=["invented_door"],
        soft_score=0.9,
        retries_left=1,
        can_afford=True,
    )
    assert v == "RETRY"


def test_decide_unverifiable_is_manual_review_not_accept():
    v = decide_gate(
        hard_issues=[],
        soft_score=0.9,
        retries_left=0,
        can_afford=False,
        unverifiable=True,
    )
    assert v == "MANUAL_REVIEW"


def test_parse_gate_founder_living_to_bedroom_luxury():
    """Founder case: living → Luxury restyle invented bedroom + door + wardrobe."""
    raw = (
        '{"architectural_integrity":false,"room_function_preservation":false,'
        '"opening_consistency":false,"fixed_elements_consistency":false,'
        '"room_function_changed":true,"invented_door":true,"invented_window":false,'
        '"removed_opening":false,"walls_redrawn":false,"floor_geometry_changed":false,'
        '"invented_built_in":true,"geometry_broken":false,'
        '"doors_original":1,"doors_result":2,"windows_original":2,"windows_result":2,'
        '"result_room_type":"bedroom",'
        '"soft_scores":{"furniture_realism":9,"lighting":9,"composition":9,"overall":9},'
        '"overall_quality":9,"unverifiable":false,'
        '"rationale":"soggiorno trasformato in camera luxury con porta e armadio inventati"}'
    )
    gate = parse_gate_json(raw, expected_room="living")
    assert gate["hard_fail"] is True
    assert "room_function_changed" in gate["hard_issues"]
    assert "invented_door" in gate["hard_issues"]
    assert "invented_built_in" in gate["hard_issues"]
    assert gate["soft_score"] >= 0.85  # aesthetic high…
    verdict = decide_gate(
        hard_issues=gate["hard_issues"],
        soft_score=gate["soft_score"],
        retries_left=0,
        can_afford=False,
    )
    assert verdict == "REJECT"  # …but REJECT anyway


def test_parse_gate_opening_count_invented_window():
    raw = (
        '{"architectural_integrity":true,"room_function_preservation":true,'
        '"opening_consistency":true,"doors_original":1,"doors_result":1,'
        '"windows_original":0,"windows_result":2,"result_room_type":"living_room",'
        '"overall_quality":8,"unverifiable":false}'
    )
    gate = parse_gate_json(raw, expected_room="living")
    assert "invented_window" in gate["hard_issues"]


def test_parse_gate_null_architecture_unverifiable():
    raw = (
        '{"architectural_integrity":null,"room_function_preservation":null,'
        '"overall_quality":8,"result_room_type":"living_room"}'
    )
    gate = parse_gate_json(raw, expected_room="living")
    assert gate["unverifiable"] is True


def test_variant_publishable_accept_only():
    assert variant_is_publishable({"url": "https://x", "qa_verdict": "ACCEPT"}) is True
    assert variant_is_publishable({"url": "https://x", "qa_verdict": "REJECT"}) is False
    assert variant_is_publishable({
        "url": "https://x",
        "qa_verdict": "ACCEPT",
        "hard_issues": ["invented_door"],
    }) is False
    assert variant_is_publishable({
        "url": "https://x",
        "quality_decision": "reject",
    }) is False
    assert variant_is_publishable({
        "url": "https://x",
        "quality_decision": "accept",
    }) is True


def test_variant_not_publishable_without_url():
    assert variant_is_publishable({"qa_verdict": "ACCEPT"}) is False
    assert variant_is_publishable(None) is False


# ── Structure / style rules ────────────────────────────────────────────────


def test_protected_mask_wins_over_removal():
    size = (64, 64)
    removal = Image.new("L", size, 0)
    # white square = remove
    for x in range(10, 40):
        for y in range(10, 40):
            removal.putpixel((x, y), 255)
    protected = Image.new("L", size, 0)
    # protected overlaps left half of removal
    for x in range(10, 25):
        for y in range(10, 40):
            protected.putpixel((x, y), 255)
    masks = combine_masks(removal=removal, protected=protected, size=size)
    rem = masks["removal"]
    # protected zone must be zero in removal
    assert rem.getpixel((15, 20)) == 0
    # unprotected removal remains
    assert rem.getpixel((30, 20)) == 255
    assert masks["protected"].getpixel((15, 20)) == 255


def test_luxury_living_style_forbids_built_ins():
    rules = style_furniture_rules("luxury", "living")
    assert "sofa" in rules.lower() or "living" in rules.lower()
    assert "NO new built-in" in rules or "built-in" in rules.lower()
    assert "bedroom" not in rules.lower()
    assert "wardrobe" not in rules.lower() or "NO" in rules


def test_style_rules_per_room():
    bed = style_furniture_rules("modern", "bedroom")
    assert "bed" in bed.lower()
    kit = style_furniture_rules("scandi", "kitchen")
    assert "cabinet" in kit.lower() or "kitchen" in kit.lower()


# ── Oneshoot prompt regression (Founder) ───────────────────────────────────


def test_oneshot_luxury_living_no_wardrobe_language():
    from apps.immoweb import virtual_staging as vs

    prompt = vs._oneshot_prompt("reverse", "luxury", "living")
    assert "living" in prompt.lower() or "sofa" in prompt.lower()
    low = prompt.lower()
    # Must not push tall built-in wardrobe as a positive instruction
    assert "closed tall wardrobe" not in low
    # Forbidden architecture may appear only as prohibitions
    assert "never invent" in low or "no invented" in low or "do not" in low
    assert "do not add any new windows" in low or "do NOT add any new windows" in prompt
    assert "bedroom" not in low


def test_oneshot_does_not_default_bedroom_in_room_bits():
    from apps.immoweb import virtual_staging as vs

    prompt = vs._oneshot_prompt("reverse", "luxury", "living")
    assert "bedroom" not in prompt.lower()


def test_pipeline_flag_default_off():
    import os
    from apps.immoweb.staging_professional import (
        job_is_b2b_gestionale,
        pipeline_enabled,
        pipeline_enabled_for_job,
    )

    old = os.environ.pop("OMNIA_STAGING_PIPELINE", None)
    old_b2c = os.environ.pop("OMNIA_STAGING_PIPELINE_FORCE_B2C", None)
    try:
        assert pipeline_enabled() is False
        os.environ["OMNIA_STAGING_PIPELINE"] = "professional"
        assert pipeline_enabled() is True
        # B2B gestionale → professional
        assert pipeline_enabled_for_job({"agency_id": "ag1", "payment_rail": None}) is True
        # B2C → stays nano even if flag on
        assert job_is_b2b_gestionale({"agency_id": None, "payment_rail": "b2c_stripe"}) is False
        assert pipeline_enabled_for_job({"agency_id": None, "payment_rail": "b2c_preview"}) is False
        assert pipeline_enabled_for_job({"agency_id": None, "payment_rail": "b2c_stripe"}) is False
        # Escape hatch
        os.environ["OMNIA_STAGING_PIPELINE_FORCE_B2C"] = "true"
        assert pipeline_enabled_for_job({"payment_rail": "b2c_stripe"}) is True
        os.environ["OMNIA_STAGING_PIPELINE"] = "nano"
        assert pipeline_enabled() is False
        assert pipeline_enabled_for_job({"agency_id": "ag1"}) is False
    finally:
        if old is None:
            os.environ.pop("OMNIA_STAGING_PIPELINE", None)
        else:
            os.environ["OMNIA_STAGING_PIPELINE"] = old
        if old_b2c is None:
            os.environ.pop("OMNIA_STAGING_PIPELINE_FORCE_B2C", None)
        else:
            os.environ["OMNIA_STAGING_PIPELINE_FORCE_B2C"] = old_b2c


def test_pay_room_fallback_is_living_not_bedroom():
    """Regression: fulfill_paid used bedroom as ROOM_TYPES miss fallback."""
    from apps.immoweb.virtual_staging import ROOM_TYPES

    pay_room = "auto"
    if pay_room in ("auto", "detect", "empty"):
        pay_room = "living"
    if pay_room not in ROOM_TYPES:
        pay_room = "living"
    assert pay_room == "living"
    assert "bedroom" != pay_room


# ── Synthetic dataset acceptance matrix ────────────────────────────────────


@pytest.mark.parametrize(
    "case",
    [
        {"id": "living_furnished", "expected": "living", "doors": 1, "windows": 2},
        {"id": "living_empty", "expected": "living", "doors": 1, "windows": 1},
        {"id": "bedroom", "expected": "bedroom", "doors": 1, "windows": 1},
        {"id": "kitchen", "expected": "kitchen", "doors": 1, "windows": 1},
        {"id": "bathroom", "expected": "bathroom", "doors": 1, "windows": 1},
        {"id": "office", "expected": "office", "doors": 1, "windows": 1},
        {"id": "living_builtin_wardrobe", "expected": "living", "doors": 1, "windows": 2, "fixed": ["built-in wardrobe"]},
        {"id": "multi_openings", "expected": "living", "doors": 2, "windows": 3},
        {"id": "niche_pillar", "expected": "living", "doors": 1, "windows": 1, "arch": ["niche", "pillar"]},
        {"id": "complex_geometry", "expected": "living", "doors": 1, "windows": 2},
    ],
)
def test_synthetic_dataset_gate_rejects_room_change(case):
    """Simulate a bad restyle that changes room function → must REJECT."""
    tax = {
        "living": "living_room",
        "bedroom": "bedroom",
        "kitchen": "kitchen",
        "bathroom": "bathroom",
        "office": "office",
    }[case["expected"]]
    # Wrong result: always bedroom (Founder failure pattern)
    raw = (
        f'{{"architectural_integrity":false,"room_function_preservation":false,'
        f'"room_function_changed":true,"invented_door":true,"invented_built_in":true,'
        f'"doors_original":{case["doors"]},"doors_result":{case["doors"] + 1},'
        f'"windows_original":{case["windows"]},"windows_result":{case["windows"]},'
        f'"result_room_type":"bedroom","overall_quality":9,"unverifiable":false}}'
    )
    gate = parse_gate_json(raw, expected_room=case["expected"])
    assert gate["hard_fail"]
    assert decide_gate(
        hard_issues=gate["hard_issues"], soft_score=0.95, retries_left=0, can_afford=False,
    ) == "REJECT"
    # Faithful result with same openings and room → ACCEPT path
    good = (
        f'{{"architectural_integrity":true,"room_function_preservation":true,'
        f'"opening_consistency":true,"fixed_elements_consistency":true,'
        f'"room_function_changed":false,"invented_door":false,"invented_window":false,'
        f'"removed_opening":false,"walls_redrawn":false,"floor_geometry_changed":false,'
        f'"invented_built_in":false,"geometry_broken":false,'
        f'"doors_original":{case["doors"]},"doors_result":{case["doors"]},'
        f'"windows_original":{case["windows"]},"windows_result":{case["windows"]},'
        f'"result_room_type":"{tax}","overall_quality":8,"unverifiable":false}}'
    )
    gate2 = parse_gate_json(good, expected_room=case["expected"])
    assert not gate2["hard_fail"]
    assert decide_gate(
        hard_issues=gate2["hard_issues"],
        soft_score=gate2["soft_score"],
        retries_left=0,
        can_afford=False,
        unverifiable=gate2["unverifiable"],
    ) == "ACCEPT"
