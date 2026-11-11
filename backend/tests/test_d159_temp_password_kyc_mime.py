"""D-159 — password temporanea B2B + sniff MIME KYC octet-stream."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, UploadFile
from io import BytesIO


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_agency_register_requires_password(monkeypatch):
    from apps.core import auth as mod
    from shared.models.user import RegisterRequest

    class DummyDB:
        users = MagicMock()
        users.find_one = AsyncMock(return_value=None)
        users.insert_one = AsyncMock()
        password_reset_tokens = MagicMock()
        password_reset_tokens.insert_one = AsyncMock()

    monkeypatch.setattr(mod.Database, "get", staticmethod(lambda: DummyDB()))
    monkeypatch.setattr(mod, "store_refresh", AsyncMock())
    monkeypatch.setattr(mod, "send_email", AsyncMock())
    monkeypatch.setattr(mod, "_set_auth_cookies", lambda *a, **k: "refresh")

    req = RegisterRequest(
        email="x@example.com",
        name="X",
        role="client",
        password=None,
        domain_sovereignty_confirmed=True,
        preferred_plan="pro",
    )
    with pytest.raises(HTTPException) as ei:
        _run(mod.register(req, MagicMock(), MagicMock(), accept_language="it"))
    assert ei.value.status_code == 400


def test_kyc_octet_stream_pdf_sniff(monkeypatch):
    from apps.immoweb import agencies as mod

    user = {
        "id": "u1",
        "email": "a@x.it",
        "role": "agency_admin",
        "agency_ids": ["ag1"],
        "active_agency_id": "ag1",
    }
    agency = {
        "id": "ag1",
        "owner_id": "u1",
        "kyc": {"status": "incomplete", "documents": [], "checklist": {}},
    }

    class DB:
        agencies = MagicMock()
        agencies.find_one = AsyncMock(return_value=agency)
        agencies.update_one = AsyncMock()
        users = MagicMock()
        users.find_one = AsyncMock(return_value=user)
        users.update_one = AsyncMock()

    monkeypatch.setattr(mod.Database, "get", staticmethod(lambda: DB()))
    monkeypatch.setattr(mod, "put_object", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(mod, "require_agency", lambda u: "ag1")

    upload = UploadFile(
        filename="visura.pdf",
        file=BytesIO(b"%PDF-1.4 test"),
        headers={"content-type": "application/octet-stream"},
    )
    out = _run(mod.upload_my_kyc_document(upload, "visura_camerale", user))
    assert out["ok"] is True
    assert out["kyc"]["checklist"]["visura_camerale"] is True
