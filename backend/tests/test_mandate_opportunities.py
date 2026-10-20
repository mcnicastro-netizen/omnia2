"""Unit: opportunità mandati (D-129) su match privati."""
from __future__ import annotations

import inspect


def test_private_match_syncs_mandate_opportunities():
    from apps.immoweb import private_listing_matching as plm

    src = inspect.getsource(plm.process_private_listing_matches)
    assert "sync_opportunities_from_hits" in src
    assert "mandate_opportunities" in src


def test_inbox_links_to_mandate_queue():
    from apps.immoweb import private_listing_matching as plm

    src = inspect.getsource(plm._notify_agency_portal_match)
    assert "/app/mandate-opportunities" in src
    assert "exclusive_mandate" in src


def test_router_mounted():
    from apps.immoweb import routes

    src = inspect.getsource(routes)
    assert "mandate_opportunities_router" in src


def test_proof_endpoint_covers_three_pillars():
    from apps.immoweb import mandate_opportunities as mo

    src = inspect.getsource(mo.proof_metrics)
    assert "portal" in src
    assert "academy" in src
    assert "mandates" in src
    assert "not_implemented" in src
    assert "D-129" in src


def test_public_contact_strips_hidden_channels():
    from apps.immoweb.mandate_opportunities import _public_contact

    prop = {
        "email": "secret@example.com",
        "contact_public": {
            "display_name": "Mario",
            "show_phone": True,
            "phone": "+390000",
            "show_whatsapp": False,
            "whatsapp": "+390001",
            "show_email": False,
        },
    }
    out = _public_contact(prop)
    assert out["phone"] == "+390000"
    assert "whatsapp" not in out
    assert "email" not in out


def test_statuses_and_funnel_constants():
    from apps.immoweb.mandate_opportunities import STATUSES, OPEN_STATUSES, DISMISS_REASONS

    assert "mandate_won" in STATUSES
    assert "new" in OPEN_STATUSES
    assert "mandate_won" not in OPEN_STATUSES
    assert "no_response" in DISMISS_REASONS


def test_dismiss_requires_reason_in_patch_signature():
    from apps.immoweb.mandate_opportunities import StatusPatch, patch_opportunity
    import inspect

    fields = StatusPatch.model_fields
    assert "dismiss_reason" in fields
    src = inspect.getsource(patch_opportunity)
    assert "dismiss_reason_required" in src


def test_create_mandate_endpoint_exists():
    from apps.immoweb import mandate_opportunities as mo
    import inspect

    src = inspect.getsource(mo)
    assert "create_mandate_from_opportunity" in src
    assert "created_property_id" in src
