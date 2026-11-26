"""Integration coexistence: D-193 wallet + CMJ visits + A4 MLS on one tree.

Read-only of product decisions: asserts the three perimeters are present and
do not clobber each other's contracts (no staging, no Stripe).
"""
from __future__ import annotations

import ast
import inspect
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parents[2]


def test_all_three_perimeter_modules_importable():
    from apps.billing import routes as billing_routes
    from apps.immoweb import collaborations as collab
    from apps.immoweb import mls as mls_mod
    from shared.billing import credit_wallet_service as wallet

    assert hasattr(wallet, "recover_pending_debit_compensations")
    assert hasattr(wallet, "allocate_credits")
    assert "Idempotency-Key" in inspect.getsource(billing_routes.allocate_wallet_credits)
    assert hasattr(collab, "require_min_proposed_slots")
    assert hasattr(mls_mod, "_mls_raw_count_shareable")
    assert hasattr(mls_mod, "_PUBLIC_SEARCH_PROJECTION")


def test_cmj_rejects_insufficient_slots_without_touching_mls():
    from apps.immoweb.collaborations import require_min_proposed_slots

    with pytest.raises(HTTPException) as ei:
        require_min_proposed_slots(["2026-12-01T10:00:00+00:00"])
    assert ei.value.status_code == 400
    detail = ei.value.detail
    assert isinstance(detail, dict)
    assert detail.get("error") == "proposed_slots_min"


def test_cmj_accepts_three_distinct_slots():
    from apps.immoweb.collaborations import require_min_proposed_slots

    slots = [
        "2026-12-01T10:00:00+00:00",
        "2026-12-01T11:00:00+00:00",
        "2026-12-01T12:00:00+00:00",
    ]
    assert require_min_proposed_slots(slots) == slots


def test_collaborations_page_does_not_post_empty_slots_operative():
    src = (ROOT / "frontend/src/apps/immoweb/pages/CollaborationsPage.jsx").read_text(
        encoding="utf-8"
    )
    assert "VisitSlotsPicker" in src
    assert "proposed_slots: []" not in src
    assert "check.slots" in src or "proposed_slots: check" in src


def test_a4_public_projection_excludes_agency_id_key():
    from apps.immoweb import mls as mls_mod

    assert "agency_id" not in mls_mod._PUBLIC_SEARCH_PROJECTION
    assert "agency_id" not in mls_mod._PUBLIC_ITEM_KEYS


def test_a4_shareable_query_always_merges_filters():
    from apps.immoweb import mls as mls_mod

    q = mls_mod._mls_shareable_query({"agency_id": {"$ne": "agX"}})
    blob = str(q)
    assert "public" in blob and "mls_shared" in blob


def test_wallet_routes_expose_compensate_recover_and_idempotency():
    src = (ROOT / "backend/apps/billing/routes.py").read_text(encoding="utf-8")
    assert "compensate-journal/recover" in src
    assert 'Header(None, alias="Idempotency-Key")' in src
    assert "allocate_wallet_credits" in src


def test_mls_inventory_gate_independent_of_wallet_symbols():
    """MLS inventory module must not import wallet allocate (no cross-leak)."""
    mls_path = ROOT / "backend/apps/immoweb/mls.py"
    tree = ast.parse(mls_path.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert not any("billing" in (m or "") or "credit_wallet" in (m or "") for m in imported)


def test_frontend_components_all_present():
    assert (ROOT / "frontend/src/apps/immoweb/components/VisitSlotsPicker.jsx").is_file()
    assert (ROOT / "frontend/src/apps/immoweb/pages/BillingPage.jsx").is_file()
    assert (ROOT / "frontend/src/apps/immoweb/pages/MlsPage.jsx").is_file()
    billing = (ROOT / "frontend/src/apps/immoweb/pages/BillingPage.jsx").read_text(
        encoding="utf-8"
    )
    assert "newIdempotencyKey" in billing
    assert "/billing/wallet/allocate" in billing
    mls = (ROOT / "frontend/src/apps/immoweb/pages/MlsPage.jsx").read_text(encoding="utf-8")
    assert "mls-inventory-scope-" in mls


def test_a4_inventory_and_cmj_visits_coexist_via_existing_harness():
    """Smoke: A4 national inventory still works with CMJ modules imported."""
    from apps.immoweb import collaborations  # noqa: F401
    from apps.immoweb import mls as mls_mod
    from tests.test_a4_mls_inventory import _DB, _run, _seed_props, _user, FakeDB
    from shared.db.connection import set_current_agency_id
    from shared.db.tenant_guard import set_current_role, set_tenant_enforce, tenant_bypass

    db = FakeDB()
    _seed_props(db)
    _DB._inst = db
    _DB._raw = db

    def agency_from_user(user):
        return user["agency_id"]

    async def ensure_idx(d):
        return None

    set_tenant_enforce(True)
    set_current_role("agency_admin")
    tenant_bypass(False)
    set_current_agency_id("agA")
    try:
        with patch("apps.immoweb.mls.Database", _DB), patch(
            "apps.immoweb.mls._agency_id", agency_from_user
        ), patch("apps.immoweb.mls.ensure_mls_indexes", ensure_idx):
            out = _run(
                mls_mod.my_mls_inventory(
                    scope="national", limit=50, skip=0, user=_user("agA")
                )
            )
        ids = {i["id"] for i in out["items"]}
        assert "pB-share" in ids
        assert "pB-private" not in ids
    finally:
        set_tenant_enforce(False)
        set_current_agency_id(None)
        set_current_role(None)
        tenant_bypass(False)


def test_dashboard_mls_off_zeros_network_while_wallet_module_loaded():
    from shared.billing import credit_wallet_service as wallet  # noqa: F401
    from apps.immoweb import mls as mls_mod
    from tests.test_a4_mls_inventory import _DB, _run, _seed_props, _user, FakeDB
    from shared.db.connection import set_current_agency_id
    from shared.db.tenant_guard import set_current_role, set_tenant_enforce, tenant_bypass

    db = FakeDB()
    _seed_props(db)
    _DB._inst = db
    _DB._raw = db

    def agency_from_user(user):
        return user["agency_id"]

    async def ensure_idx(d):
        return None

    set_tenant_enforce(True)
    set_current_role("agency_admin")
    set_current_agency_id("agOff")
    try:
        with patch("apps.immoweb.mls.Database", _DB), patch(
            "apps.immoweb.mls._agency_id", agency_from_user
        ), patch("apps.immoweb.mls.ensure_mls_indexes", ensure_idx):
            dash = _run(mls_mod.mls_dashboard(_user("agOff")))
        assert dash["mls_enabled"] is False
        assert dash["network"]["national_listings"] == 0
        assert dash["network"]["agencies"] == 0
    finally:
        set_tenant_enforce(False)
        set_current_agency_id(None)
        set_current_role(None)
        tenant_bypass(False)
