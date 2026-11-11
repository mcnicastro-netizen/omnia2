"""D-158 — logo file non obbligatorio se c'è website/dominio."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException


class _Agencies:
    def __init__(self):
        self._docs = []

    async def find_one(self, q, *a, **k):
        if not q:
            return None
        if "owner_id" in q:
            for d in self._docs:
                if d.get("owner_id") == q["owner_id"]:
                    return dict(d)
        if "slug" in q:
            for d in self._docs:
                if d.get("slug") == q["slug"]:
                    return dict(d)
        if "id" in q:
            for d in self._docs:
                if d.get("id") == q["id"]:
                    return dict(d)
        return None

    async def insert_one(self, doc):
        self._docs.append(dict(doc))
        return SimpleNamespace(inserted_id="x")


class _Users:
    def __init__(self, user):
        self.user = dict(user)

    async def update_one(self, *a, **k):
        return SimpleNamespace(modified_count=1)

    async def find_one(self, q, *a, **k):
        if q.get("id") == self.user.get("id"):
            return dict(self.user)
        return None


class _DB:
    def __init__(self, user):
        self.agencies = _Agencies()
        self.users = _Users(user)


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_create_agency_allows_missing_logo_when_website_present(monkeypatch):
    from apps.immoweb import agencies as mod

    user = {
        "id": "u-1",
        "email": "a@example.com",
        "name": "Ada",
        "role": "client",
        "agency_ids": [],
        "signup_domain_sovereignty_confirmed": True,
        "signup_existing_domain": "nicastroimmobiliare.it",
        "signup_preferred_plan": "pro",
        "lang": "it",
    }
    db = _DB(user)
    monkeypatch.setattr(mod.Database, "get", staticmethod(lambda: db))

    # email import interno: stub modulo
    fake_email = MagicMock()
    fake_email.send_email = AsyncMock()
    monkeypatch.setitem(__import__("sys").modules, "shared.email.client", fake_email)
    monkeypatch.setitem(
        __import__("sys").modules,
        "shared.public_base",
        SimpleNamespace(get_public_base_url=lambda: "https://example.com"),
    )

    payload = SimpleNamespace(
        display_name="Nicastro Immobiliare",
        fiscal={
            "legal_name": "Nicastro SRL",
            "vat_number": "12345678901",
            "fiscal_code": "12345678901",
            "rea": "CT-123456",
        },
        address={
            "street": "Via Etnea 1",
            "city": "Catania",
            "province": "CT",
            "postal_code": "95131",
        },
        contact={
            "website": "https://www.nicastroimmobiliare.it",
            "email": "a@example.com",
            "phone": "+39095123456",
            "pec": "pec@example.com",
        },
        branding={"primary_color": "#0B1E3F"},  # no logo_url
        preferred_plan_tier="pro",
    )

    out = _run(mod.create_agency(payload, user))
    assert out["id"]
    assert out["activation_status"] == "pending"
    assert not (out.get("branding") or {}).get("logo_url")


def test_create_agency_rejects_without_logo_and_without_website(monkeypatch):
    from apps.immoweb import agencies as mod

    user = {
        "id": "u-2",
        "email": "b@example.com",
        "name": "Bob",
        "role": "client",
        "agency_ids": [],
        "signup_domain_sovereignty_confirmed": True,
        "signup_existing_domain": None,
        "signup_preferred_plan": "starter",
        "lang": "it",
    }
    db = _DB(user)
    monkeypatch.setattr(mod.Database, "get", staticmethod(lambda: db))

    payload = SimpleNamespace(
        display_name="No Brand Agency",
        fiscal={
            "legal_name": "No Brand SRL",
            "vat_number": "12345678901",
            "fiscal_code": "12345678901",
            "rea": "RM-1",
        },
        address={
            "street": "Via Roma 1",
            "city": "Roma",
            "province": "RM",
            "postal_code": "00100",
        },
        contact={
            "email": "b@example.com",
            "phone": "+3906123456",
            "pec": "pecb@example.com",
        },
        branding={},
        preferred_plan_tier="starter",
    )

    with pytest.raises(HTTPException) as ei:
        _run(mod.create_agency(payload, user))
    assert ei.value.status_code == 400
    assert ei.value.detail["error"] == "logo_required"
