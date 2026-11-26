"""Ops Attiva / wipe CRM — policy Founder 26-Nov-2026.

Attiva ordinaria: wipe_crm default False; wipe_crm=True rifiutato.
Seconda Attiva su già active: nessun wipe.
Wipe solo via endpoint dedicato con confirm+reason.
"""
from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from apps.immoweb.founder_ops import (
    ActivateAgencyBody,
    WipeAgencyCrmBody,
    ops_activate_agency,
    ops_wipe_agency_crm,
)


def test_activate_default_wipe_crm_false():
    body = ActivateAgencyBody(agency_id="ag1")
    assert body.wipe_crm is False


def test_activate_source_never_calls_wipe_helper():
    src = inspect.getsource(ops_activate_agency)
    assert "wipe_agency_crm_data" not in src
    assert "wipe_not_allowed_on_activate" in src


def test_wipe_body_requires_confirm_and_reason():
    with pytest.raises(Exception):
        WipeAgencyCrmBody(agency_id="ag1", confirm="NO", reason="short")
    ok = WipeAgencyCrmBody(
        agency_id="ag1",
        confirm="WIPE_CRM",
        reason="Pulizia staging sintetica autorizzata",
    )
    assert ok.confirm == "WIPE_CRM"


def _agency(status="pending", **extra):
    base = {
        "id": "ag-1",
        "slug": "ag-1",
        "display_name": "Agenzia Test",
        "activation_status": status,
        "owner_id": "u-owner",
        "kyc": {"status": "verified"},
        "commercial_customer_id": "",
    }
    base.update(extra)
    return base


def _db_for_activate(agency):
    db = MagicMock()
    db.agencies.find_one = AsyncMock(return_value=agency)
    db.agencies.update_one = AsyncMock()
    db.ops_security_events.insert_one = AsyncMock()
    db.users.find_one = AsyncMock(
        return_value={"id": "u-owner", "email": "owner@example.com", "name": "O", "lang": "it"}
    )
    db.commercial_customers.find_one = AsyncMock(return_value=None)
    return db


@pytest.mark.asyncio
async def test_activate_rejects_wipe_crm_true():
    agency = _agency("pending")
    db = _db_for_activate(agency)
    body = ActivateAgencyBody(
        agency_id="ag-1",
        wipe_crm=True,
        require_kyc_verified=False,
        require_payment=False,
        grant_plan=False,
        send_email=False,
    )
    user = {"id": "sa", "email": "ops@example.com", "role": "super_admin"}
    with patch("apps.immoweb.founder_ops.Database.get", return_value=db), patch(
        "apps.immoweb.assisted_billing.resolve_agency",
        new=AsyncMock(return_value={"ok": True, "agency_id": "ag-1", "agency": agency}),
    ):
        with pytest.raises(HTTPException) as ei:
            await ops_activate_agency(body, user)
    assert ei.value.status_code == 400
    assert ei.value.detail["error"] == "wipe_not_allowed_on_activate"
    db.ops_security_events.insert_one.assert_not_awaited()


@pytest.mark.asyncio
async def test_activate_ordinary_no_wipe_omitted_param():
    agency = _agency("pending")
    db = _db_for_activate(agency)
    body = ActivateAgencyBody(
        agency_id="ag-1",
        require_kyc_verified=False,
        require_payment=False,
        grant_plan=False,
        send_email=False,
    )
    assert body.wipe_crm is False
    user = {"id": "sa", "email": "ops@example.com", "role": "super_admin"}
    with patch("apps.immoweb.founder_ops.Database.get", return_value=db), patch(
        "apps.immoweb.assisted_billing.resolve_agency",
        new=AsyncMock(return_value={"ok": True, "agency_id": "ag-1", "agency": agency}),
    ):
        out = await ops_activate_agency(body, user)
    assert out["activation_status"] == "active"
    assert out.get("wipe") is None
    assert out["previous_status"] == "pending"
    db.agencies.update_one.assert_awaited()
    db.ops_security_events.insert_one.assert_awaited()


@pytest.mark.asyncio
async def test_second_activate_already_active_no_wipe():
    agency = _agency("active", activated_at="2026-01-01T00:00:00+00:00")
    db = _db_for_activate(agency)
    body = ActivateAgencyBody(
        agency_id="ag-1",
        wipe_crm=False,
        require_kyc_verified=False,
        require_payment=False,
        grant_plan=False,
        send_email=False,
    )
    user = {"id": "sa", "email": "ops@example.com", "role": "super_admin"}
    with patch("apps.immoweb.founder_ops.Database.get", return_value=db), patch(
        "apps.immoweb.assisted_billing.resolve_agency",
        new=AsyncMock(return_value={"ok": True, "agency_id": "ag-1", "agency": agency}),
    ):
        out = await ops_activate_agency(body, user)
    assert out["previous_status"] == "active"
    assert out.get("wipe") is None
    # activated_at storico non riscritto
    set_arg = db.agencies.update_one.await_args.args[1]["$set"]
    assert "activated_at" not in set_arg


@pytest.mark.asyncio
async def test_wipe_without_confirm_rejected():
    body = WipeAgencyCrmBody(
        agency_id="ag-1",
        confirm="WIPE_NOPE",  # ≥8 chars but not WIPE_CRM
        reason="Motivazione abbastanza lunga",
    )
    user = {"id": "sa", "email": "ops@example.com", "role": "super_admin"}
    with pytest.raises(HTTPException) as ei:
        await ops_wipe_agency_crm(body, user)
    assert ei.value.status_code == 400
    assert ei.value.detail["error"] == "confirm_required"


@pytest.mark.asyncio
async def test_wipe_explicit_authorized():
    agency = _agency("active")
    db = MagicMock()
    db.agencies.find_one_and_update = AsyncMock(return_value=agency)
    db.agencies.update_one = AsyncMock()
    db.ops_security_events.insert_one = AsyncMock()
    body = WipeAgencyCrmBody(
        agency_id="ag-1",
        confirm="WIPE_CRM",
        reason="Pulizia staging sintetica autorizzata Founder",
        confirm_agency_id="ag-1",
    )
    user = {"id": "sa", "email": "ops@example.com", "role": "super_admin"}
    with patch("apps.immoweb.founder_ops.Database.get", return_value=db), patch(
        "apps.immoweb.assisted_billing.resolve_agency",
        new=AsyncMock(return_value={"ok": True, "agency_id": "ag-1", "agency": agency}),
    ), patch(
        "apps.immoweb.demo_retire.wipe_agency_crm_data",
        new=AsyncMock(return_value={"ok": True, "agency_id": "ag-1", "total_deleted": 3, "deleted": {"clients": 1}}),
    ):
        out = await ops_wipe_agency_crm(body, user)
    assert out["ok"] is True
    assert out["wipe"]["total_deleted"] == 3
    db.ops_security_events.insert_one.assert_awaited()


@pytest.mark.asyncio
async def test_wipe_concurrent_lock_409():
    agency = _agency("active")
    db = MagicMock()
    db.agencies.find_one_and_update = AsyncMock(return_value=None)
    db.agencies.find_one = AsyncMock(return_value={"id": "ag-1"})
    body = WipeAgencyCrmBody(
        agency_id="ag-1",
        confirm="WIPE_CRM",
        reason="Secondo tentativo concorrente di wipe",
    )
    user = {"id": "sa", "email": "ops@example.com", "role": "super_admin"}
    with patch("apps.immoweb.founder_ops.Database.get", return_value=db), patch(
        "apps.immoweb.assisted_billing.resolve_agency",
        new=AsyncMock(return_value={"ok": True, "agency_id": "ag-1", "agency": agency}),
    ):
        with pytest.raises(HTTPException) as ei:
            await ops_wipe_agency_crm(body, user)
    assert ei.value.status_code == 409


@pytest.mark.asyncio
async def test_wipe_confirm_agency_id_mismatch():
    agency = _agency("active")
    db = MagicMock()
    body = WipeAgencyCrmBody(
        agency_id="ag-1",
        confirm="WIPE_CRM",
        reason="Motivazione valida per wipe CRM",
        confirm_agency_id="ag-OTHER",
    )
    user = {"id": "sa", "email": "ops@example.com", "role": "super_admin"}
    with patch("apps.immoweb.founder_ops.Database.get", return_value=db), patch(
        "apps.immoweb.assisted_billing.resolve_agency",
        new=AsyncMock(return_value={"ok": True, "agency_id": "ag-1", "agency": agency}),
    ):
        with pytest.raises(HTTPException) as ei:
            await ops_wipe_agency_crm(body, user)
    assert ei.value.status_code == 400
    assert ei.value.detail["error"] == "confirm_agency_id_mismatch"
