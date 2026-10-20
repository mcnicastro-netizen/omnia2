"""Unit: match annunci privati → richieste CRM (tutte le agenzie)."""
from __future__ import annotations

import inspect


def test_private_portal_query_requires_approved_active():
    from apps.immoweb.private_listing_matching import private_portal_listing_query
    import json

    q = private_portal_listing_query()
    blob = json.dumps(q)
    assert "is_private_listing" in blob
    assert "approved" in blob
    assert "active" in blob


def test_match_request_scans_portal_and_keeps_mls_isolation():
    src = inspect.getsource(
        __import__("apps.immoweb.client_requests_service", fromlist=["match_request"]).match_request
    )
    assert "portal_matches" in src
    assert "_score_portal_private_listings" in src or "is_private_listing" in src


def test_approve_triggers_private_match():
    from apps.immoweb import moderation

    src = inspect.getsource(moderation.approve_listing)
    assert "run_private_listing_request_matching" in src


def test_scheduler_and_cron_wired():
    from apps.immoweb import sync_engine, cron

    src = inspect.getsource(sync_engine.start_scheduler)
    assert "private_listing_request_matching" in src
    assert "IntervalTrigger" in src
    assert "match-private" in inspect.getsource(cron)
    assert "run_private_listing_request_matching" in inspect.getsource(cron)


def test_match_private_ignores_mls_shared_flag_on_requests():
    """Il filtro richieste non deve richiedere mls_shared=True."""
    from apps.immoweb import private_listing_matching as plm

    src = inspect.getsource(plm.match_private_listing_to_requests)
    # Query block must not filter on mls_shared=True
    assert '"mls_shared": True' not in src and "'mls_shared': True" not in src
    assert "auto_match" in src
    assert "open" in src
    assert "is_auto_match_ready" in src


def test_auto_match_ready_gate():
    from apps.immoweb.matching import is_auto_match_ready

    assert is_auto_match_ready({}) is False
    assert is_auto_match_ready({"cities": ["Catania"]}) is False
    assert is_auto_match_ready({"cities": ["Catania"], "price_max": 200000}) is False
    assert is_auto_match_ready({
        "cities": ["Catania"],
        "price_max": 200000,
        "surface_min": 60,
    }) is True
    assert is_auto_match_ready({
        "cities": "  ",
        "price_min": 1,
        "surface_max": 90,
    }) is False
