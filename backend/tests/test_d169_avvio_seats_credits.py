"""D-169 — posti agenti da piano + contesto Avvio (team / crediti)."""
from apps.billing.plans import get_plan, LAUNCH_PLANS
from apps.immoweb.setup_journey import default_setup_journey


def test_plan_max_agents_launch():
    assert get_plan("starter").max_agents == 3
    assert get_plan("pro").max_agents == 10
    assert get_plan("agency").max_agents == -1
    assert LAUNCH_PLANS["pro"].credits_included_monthly == 1200


def test_default_journey_has_team_optional():
    j = default_setup_journey()
    assert j["steps"]["team"]["optional"] is True
    assert j["steps"]["team"]["done"] is False
