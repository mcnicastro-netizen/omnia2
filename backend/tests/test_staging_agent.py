"""D-125 — StagingAgent unit tests (no fal spend)."""
from apps.immoweb.staging_agent import (
    BUDGET_HARD_USD,
    BUDGET_SOFT_USD,
    QUALITY_ACCEPT,
    StagingAgent,
    critique_empty_from_meta,
    critique_furnished_heuristic,
    decide_accept,
    plan_staging,
)


def test_plan_standard_no_erase():
    p = plan_staging(mode="standard", style="modern", room_type="living")
    assert p.need_erase is False and p.need_furnish is True
    assert p.budget_hard_usd == BUDGET_HARD_USD["standard"]
    assert "no_third_party_staging_saas_embed" in p.notes


def test_plan_empty_and_reverse_budgets():
    empty = plan_staging(mode="empty", style="modern", room_type="bedroom")
    rev = plan_staging(mode="reverse", style="scandi", room_type="bedroom", num_variants=2)
    assert empty.need_erase and not empty.need_furnish
    assert rev.need_erase and rev.need_furnish
    assert empty.budget_hard_usd == BUDGET_HARD_USD["empty"]
    assert rev.budget_hard_usd > BUDGET_HARD_USD["reverse"]  # +variant uplift
    assert rev.budget_soft_usd > BUDGET_SOFT_USD["reverse"]


def test_plan_multi_style_truncates():
    p = plan_staging(
        mode="reverse",
        style="modern",
        room_type="living",
        num_variants=3,
        variant_mode="multi_style",
        styles_list=["modern", "classic", "scandi", "luxury"],
    )
    assert p.styles == ["modern", "classic", "scandi"]
    assert p.num_variants == 3


def test_critique_empty_clean_pass():
    report = critique_empty_from_meta({
        "erased": ["evf_union:0.18", "bed", "rug:sweep"],
        "evf_ratio": 0.18,
        "pass1": 2,
        "sweep": 1,
        "wall_retries": 0,
    })
    assert report.score >= QUALITY_ACCEPT
    assert decide_accept(report, retries_left=1, can_afford=True) == "accept"


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
    assert decide_accept(report, retries_left=1, can_afford=True) == "retry"


def test_critique_empty_wall_skip_does_not_force_reerase_over_openings():
    report = critique_empty_from_meta({
        "erased": ["evf_union:skip_wall", "wardrobe:skip_wall"],
        "evf_ratio": 0.15,
        "pass1": 1,
        "sweep": 0,
        "wall_retries": 2,
    })
    # Geometry-safe: may warn, but must not demand re_erase over openings alone.
    assert "wall_invention_guard_fired:2" in report.issues
    assert "re_erase" not in report.retry_actions


def test_critique_furnished_gym_remnants():
    report = critique_furnished_heuristic(
        style="modern",
        engine="apartment_staging_lora",
        remnant_labels=["gym machine", "weight bench"],
    )
    assert report.score < QUALITY_ACCEPT
    assert "re_erase_remnants" in report.retry_actions
    assert "re_furnish" in report.retry_actions


def test_critique_furnished_flux_fallback():
    report = critique_furnished_heuristic(
        style="luxury",
        engine="flux_inpaint_fallback",
        remnant_labels=[],
    )
    assert "fallback_flux_inpaint" in report.issues
    assert "re_furnish_lora" in report.retry_actions


def test_ledger_hard_cap_blocks_spend():
    agent = StagingAgent(plan_staging(mode="standard", style="modern", room_type="living"))
    agent.charge(0.13, "almost_full")
    assert agent.can_spend(0.005) is True
    assert agent.can_spend(0.02) is False
    assert agent.over_soft() is True


def test_agent_summary_shape():
    agent = StagingAgent(plan_staging(mode="reverse", style="modern", room_type="living"))
    agent.charge(0.05, "erase")
    q = critique_empty_from_meta({"erased": ["bed"], "evf_ratio": 0.1, "pass1": 1, "sweep": 0})
    agent.record_quality("empty", q, "accept")
    s = agent.summary()
    assert s["agent"] == "StagingAgent"
    assert s["within_hard_budget"] is True
    assert s["plan"]["mode"] == "reverse"
    assert "empty" in s["quality"]


def test_decide_accept_warning_when_broke():
    report = critique_furnished_heuristic(
        style="modern",
        engine="apartment_staging_lora",
        remnant_labels=["gym machine"],
    )
    assert decide_accept(report, retries_left=1, can_afford=False) == "accept_with_warning"
    assert decide_accept(report, retries_left=0, can_afford=True) == "accept_with_warning"
