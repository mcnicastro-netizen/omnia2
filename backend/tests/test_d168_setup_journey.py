"""D-168 — percorso Avvio + biforcazione sito/MLS."""
from apps.immoweb.setup_journey import (
    default_setup_journey,
    ensure_journey,
    _next_step,
    _progress,
)


def test_default_journey_order_and_requests_default():
    j = default_setup_journey()
    assert j["status"] == "in_progress"
    assert j["current_step"] == "site"
    assert j["steps"]["mls"]["share_requests"] is True
    assert j["steps"]["team"]["optional"] is True


def test_next_step_after_site_done():
    j = default_setup_journey()
    j["steps"]["site"]["done"] = True
    assert _next_step(j) == "import_properties"
    prog = _progress(j)
    assert prog["done"] == 1
    assert prog["total"] == 6


def test_ensure_journey_merges_legacy():
    agency = {"setup_journey": {"status": "in_progress", "steps": {"site": {"done": True, "choice": "omnia_theme"}}}}
    j = ensure_journey(agency)
    assert j["steps"]["site"]["done"] is True
    assert j["steps"]["site"]["choice"] == "omnia_theme"
    assert "mls" in j["steps"]


def test_client_request_default_true():
    from shared.models.client_request import ClientRequestCreate

    # pydantic default
    fields = ClientRequestCreate.model_fields
    assert fields["mls_shared"].default is True
