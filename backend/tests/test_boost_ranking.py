"""Unit: ranking boost D-127 (tier + rotazione + tutti i sort)."""
from __future__ import annotations

from apps.billing.boost_ranking import (
    USER_SORT_FIELDS,
    boost_add_fields_stage,
    boost_sort_stage,
    build_boosted_search_pipeline,
)


def test_all_user_sorts_supported():
    assert set(USER_SORT_FIELDS) >= {"recent", "price_asc", "price_desc", "surface_desc"}


def test_sort_stage_priority_tier_then_rotation():
    stage = boost_sort_stage("price_asc")
    keys = list(stage["$sort"].keys())
    assert keys[0] == "_eff_boost"
    assert keys[1] == "_boost_rotate"
    assert "price" in stage["$sort"]


def test_pipeline_used_for_every_sort():
    for sort in USER_SORT_FIELDS:
        pipe = build_boosted_search_pipeline(
            {"status": "active"},
            sort=sort,
            skip=0,
            limit=20,
            project_fields={"id": 1, "title": 1},
            now_iso="2026-10-19T12:00:00+00:00",
        )
        assert pipe[0]["$match"]["status"] == "active"
        assert "$addFields" in pipe[1]
        assert pipe[2]["$sort"]["_eff_boost"] == -1
        assert pipe[2]["$sort"]["_boost_rotate"] == 1


def test_add_fields_active_boost_uses_rank():
    stage = boost_add_fields_stage("2026-10-19T12:00:00+00:00")
    assert "_eff_boost" in stage["$addFields"]
    assert "_boost_rotate" in stage["$addFields"]


def test_search_endpoint_uses_boost_ranking():
    import inspect
    from apps.immocloud import public_portal as pp

    src = inspect.getsource(pp.public_search)
    assert "build_boosted_search_pipeline" in src
    assert "schedule_boost_impressions" in src


def test_apply_boost_resets_rotation():
    import inspect
    from apps.billing import b2c_boosts

    src = inspect.getsource(b2c_boosts.apply_boost_to_listing)
    assert "apply_boost_rotation_reset_fields" in src
    assert "boost_last_shown_at" in src
