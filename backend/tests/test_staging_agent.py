"""D-125 — StagingAgent unit tests (no fal spend)."""
from apps.immoweb.staging_agent import (
    BUDGET_HARD_USD,
    BUDGET_PER_EXTRA_STYLE,
    BUDGET_SOFT_USD,
    COST_NANO_BANANA_1K,
    QUALITY_ACCEPT,
    StagingAgent,
    critique_empty_from_meta,
    critique_furnished_heuristic,
    decide_accept,
    parse_vision_critique,
    plan_staging,
)


def test_plan_nano_standard():
    p = plan_staging(mode="standard", style="modern", room_type="living")
    assert p.engine == "nano_banana"
    assert p.need_erase is False and p.need_furnish is True
    assert "nano_banana_2_oneshot" in p.notes
    assert p.budget_hard_usd == BUDGET_HARD_USD["standard"]


def test_plan_empty_single():
    p = plan_staging(mode="empty", style="modern", room_type="bedroom", num_variants=4,
                     variant_mode="multi_style", styles_list=["modern", "classic", "scandi", "luxury"])
    assert p.need_erase and not p.need_furnish
    assert p.styles == ["empty"] and p.num_variants == 1


def test_plan_multi_style_four_budget():
    p = plan_staging(
        mode="reverse",
        style="modern",
        room_type="bedroom",
        num_variants=4,
        variant_mode="multi_style",
        styles_list=["modern", "classic", "scandi", "luxury"],
    )
    assert p.styles == ["modern", "classic", "scandi", "luxury"]
    assert p.num_variants == 4
    assert abs(p.budget_soft_usd - (BUDGET_SOFT_USD["reverse"] + 3 * BUDGET_PER_EXTRA_STYLE)) < 1e-9
    # 4 × $0.08 oneshot fits under hard cap with room for 1 retry
    assert p.budget_hard_usd >= 4 * COST_NANO_BANANA_1K


def test_critique_empty_mask_without_erase_retries():
    report = critique_empty_from_meta({
        "erased": [],
        "evf_ratio": 0.22,
        "pass1": 0,
        "sweep": 0,
        "wall_retries": 0,
    })
    assert report.score < QUALITY_ACCEPT
    assert "re_erase" in report.retry_actions


def test_critique_furnished_gym_remnants():
    report = critique_furnished_heuristic(
        style="modern",
        engine="apartment_staging_lora",
        remnant_labels=["gym machine", "weight bench"],
    )
    assert report.score < QUALITY_ACCEPT
    assert "re_furnish" in report.retry_actions


def test_parse_vision_critique_accept():
    raw = '{"score":8,"architecture_ok":true,"geometry_ok":true,"scale_ok":true,'
    raw += '"lighting_ok":true,"artifacts":[],"verdict":"accept","rationale":"ok"}'
    r = parse_vision_critique(raw)
    assert r.score == 0.8
    assert decide_accept(r, retries_left=1, can_afford=True) == "accept"


def test_parse_vision_critique_retry():
    raw = '{"score":5,"architecture_ok":false,"geometry_ok":true,"scale_ok":true,'
    raw += '"lighting_ok":false,"artifacts":["residuo gym"],"verdict":"retry",'
    raw += '"rationale":"muro alterato"}'
    r = parse_vision_critique(raw)
    assert r.score == 0.5
    assert "architecture_fail" in r.issues
    assert decide_accept(r, retries_left=1, can_afford=True) == "retry"


def test_parse_vision_critique_markdown_fence():
    raw = '```json\n{"score":7.5,"architecture_ok":true,"geometry_ok":true,'
    raw += '"scale_ok":true,"lighting_ok":true,"artifacts":[],"verdict":"accept"}\n```'
    assert parse_vision_critique(raw).score == 0.75


def test_ledger_hard_cap_blocks_spend():
    agent = StagingAgent(plan_staging(mode="standard", style="modern", room_type="living"))
    agent.charge(0.19, "almost_full")
    assert agent.can_spend(0.005) is True
    assert agent.can_spend(0.02) is False


def test_agent_summary_shape():
    agent = StagingAgent(plan_staging(mode="reverse", style="modern", room_type="living"))
    agent.charge(0.08, "nano")
    q = parse_vision_critique('{"score":8,"architecture_ok":true,"geometry_ok":true,'
                              '"scale_ok":true,"lighting_ok":true,"artifacts":[],"verdict":"accept"}')
    agent.record_quality("style:modern", q, "accept")
    s = agent.summary()
    assert s["agent"] == "StagingAgent"
    assert s["plan"]["engine"] == "nano_banana"
    assert "style:modern" in s["quality"]


def test_oneshot_prompt_helpers():
    from apps.immoweb import virtual_staging as vs
    rev = vs._oneshot_prompt("reverse", "luxury", "bedroom")
    assert "Remove ALL existing furniture" in rev
    assert "luxury" in rev.lower() or "boutique" in rev
    assert "Lock:" in rev
    empty = vs._oneshot_prompt("empty", "modern", "living")
    assert "Remove ALL furniture" in empty
    assert vs.MODEL_NANO_BANANA_EDIT == "fal-ai/nano-banana-2/edit"
    assert vs.COST_NANO_BANANA == 0.08
