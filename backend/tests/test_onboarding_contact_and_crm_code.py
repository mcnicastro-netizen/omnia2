"""Onboarding contact validation + CRM client_code (OM-K-)."""
from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from apps.immoweb.agencies import _validate_onboarding_contact
from shared.ids import generate_public_code, ensure_crm_client_code


class _Contact:
    def __init__(self, **kw):
        self._d = kw

    def model_dump(self):
        return dict(self._d)


def test_validate_phone_and_pec_ok():
    _validate_onboarding_contact(
        _Contact(phone="+39 333 1234567", pec="agenzia@pec.it")
    )


def test_validate_phone_required():
    with pytest.raises(HTTPException) as ei:
        _validate_onboarding_contact(_Contact(phone="", pec="a@pec.it"))
    assert ei.value.status_code == 400
    assert ei.value.detail == "phone_required_or_invalid"


def test_validate_pec_required():
    with pytest.raises(HTTPException) as ei:
        _validate_onboarding_contact(_Contact(phone="3331234567", pec="not-an-email"))
    assert ei.value.status_code == 400
    assert ei.value.detail == "pec_required_or_invalid"


def test_crm_code_prefix():
    assert generate_public_code("crm").startswith("OM-K-")


class _Coll:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    async def find_one(self, q, *a, **k):
        for d in self.docs:
            if all(d.get(kk) == vv for kk, vv in q.items() if kk != "$or"):
                if "$or" in q:
                    # uniqueness probe by client_code
                    continue
                return d
        if "client_code" in q:
            for d in self.docs:
                if d.get("client_code") == q.get("client_code"):
                    return d
        for d in self.docs:
            if d.get("id") == q.get("id"):
                return d
        return None

    async def update_one(self, q, upd):
        for d in self.docs:
            if d.get("id") == q.get("id"):
                d.update(upd.get("$set") or {})
                return


class _DB:
    def __init__(self):
        self.clients = _Coll(
            [{"id": "c1", "agency_id": "a1", "name": "Mario", "client_code": None}]
        )

    def __getitem__(self, name):
        return getattr(self, name)


def test_ensure_crm_client_code_allocates():
    db = _DB()
    code = asyncio.run(ensure_crm_client_code(db, "c1", agency_id="a1"))
    assert code and code.startswith("OM-K-")
    assert db.clients.docs[0]["client_code"] == code
