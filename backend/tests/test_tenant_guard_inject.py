"""PRE-GTM W3 — TenantAwareDatabase inject must not trust client agency_id."""
from __future__ import annotations

import pytest

from shared.db import tenant_guard as tg
from shared.db.connection import set_current_agency_id


@pytest.fixture(autouse=True)
def _reset_tenant_ctx():
    set_current_agency_id(None)
    tg.set_current_role(None)
    tg.tenant_bypass(False)
    tg.set_tenant_enforce(False)
    yield
    set_current_agency_id(None)
    tg.set_current_role(None)
    tg.tenant_bypass(False)
    tg.set_tenant_enforce(False)


def test_inject_filter_overwrites_client_agency_id():
    tg.set_tenant_enforce(True)
    set_current_agency_id("agency-A")
    out = tg._inject_filter({"agency_id": "agency-B", "id": "prop-1"})
    assert out["agency_id"] == "agency-A"
    assert out["id"] == "prop-1"


def test_inject_filter_adds_when_missing():
    tg.set_tenant_enforce(True)
    set_current_agency_id("agency-A")
    out = tg._inject_filter({"id": "prop-1"})
    assert out == {"id": "prop-1", "agency_id": "agency-A"}


def test_inject_filter_bypass_preserves_client_agency():
    tg.set_tenant_enforce(True)
    tg.tenant_bypass(True)
    set_current_agency_id("agency-A")
    out = tg._inject_filter({"agency_id": "agency-B"})
    assert out["agency_id"] == "agency-B"


def test_inject_filter_no_enforce_skips():
    tg.set_tenant_enforce(False)
    set_current_agency_id("agency-A")
    out = tg._inject_filter({"agency_id": "agency-B"})
    assert out["agency_id"] == "agency-B"


def test_inject_doc_forces_agency():
    tg.set_tenant_enforce(True)
    set_current_agency_id("agency-A")
    out = tg._inject_doc({"agency_id": "evil", "title": "x"})
    assert out["agency_id"] == "agency-A"


def test_activities_in_tenant_collections():
    assert "activities" in tg.TENANT_COLLECTIONS
    assert "modulistica_documents" in tg.TENANT_COLLECTIONS
    assert "mandate_opportunities" in tg.TENANT_COLLECTIONS
    assert "social_channels" in tg.TENANT_COLLECTIONS


def test_deals_not_blindly_in_tenant_collections():
    """Deals use agency_id OR partner_agency_id — auto-inject would break partners."""
    assert "deals" not in tg.TENANT_COLLECTIONS
    assert "mls_visits" not in tg.TENANT_COLLECTIONS
    assert "mls_chat_threads" not in tg.TENANT_COLLECTIONS
    assert "videos" not in tg.TENANT_COLLECTIONS  # mixed public/agency
