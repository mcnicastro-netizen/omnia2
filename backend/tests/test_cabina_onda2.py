"""Cabina onda 2: kill-switch, impersonation, erase, B2B override."""
from __future__ import annotations

import asyncio

import pytest
from fastapi import HTTPException

from apps.immoweb import founder_bridge as fb
from shared.security import circuit as circuit_mod


class _Cur:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *a, **k):
        return self

    def limit(self, n):
        self.docs = self.docs[:n]
        return self

    async def to_list(self, length=None):
        return list(self.docs)


class _Coll:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    async def count_documents(self, q):
        return len(self._match(q))

    def find(self, q=None, *a, **k):
        return _Cur(self._match(q or {}))

    async def find_one(self, q, *a, **k):
        hits = self._match(q)
        return hits[0] if hits else None

    async def update_one(self, q, upd, upsert=False):
        hits = self._match(q)
        class R:
            matched_count = len(hits)
            modified_count = len(hits)

        if hits:
            d = hits[0]
            if "$set" in upd:
                d.update(upd["$set"])
            if "$unset" in upd:
                for k in upd["$unset"]:
                    d.pop(k, None)
        elif upsert:
            doc = dict(q)
            doc.update(upd.get("$set") or {})
            self.docs.append(doc)
            R.matched_count = 1
        return R()

    async def update_many(self, q, upd):
        hits = self._match(q)
        for d in hits:
            if "$set" in upd:
                d.update(upd["$set"])
            if "$pull" in upd:
                for k, v in upd["$pull"].items():
                    if isinstance(d.get(k), list) and v in d[k]:
                        d[k] = [x for x in d[k] if x != v]
        class R:
            modified_count = len(hits)
        return R()

    async def delete_many(self, q):
        before = len(self.docs)
        self.docs = [d for d in self.docs if d not in self._match(q)]
        class R:
            deleted_count = before - len(self.docs)
        return R()

    async def insert_one(self, doc):
        self.docs.append(doc)

    def _match(self, q):
        if not q:
            return list(self.docs)
        out = []
        for d in self.docs:
            ok = True
            for k, v in q.items():
                if k.startswith("$"):
                    continue
                if isinstance(v, dict) and "$in" in v:
                    if d.get(k) not in v["$in"]:
                        ok = False
                    continue
                if d.get(k) != v:
                    ok = False
            if ok:
                out.append(d)
        return out


class _DB:
    def __init__(self):
        self.agencies = _Coll(
            [
                {
                    "id": "agency-01",
                    "slug": "demo-ag",
                    "display_name": "Demo AG",
                    "activation_status": "active",
                    "owner_id": "u1",
                }
            ]
        )
        self.users = _Coll(
            [
                {
                    "id": "founder",
                    "email": "f@x.it",
                    "role": "super_admin",
                    "agency_ids": [],
                    "active_agency_id": None,
                },
                {
                    "id": "u1",
                    "email": "a@x.it",
                    "role": "agency_admin",
                    "agency_ids": ["agency-01"],
                    "name": "Ada",
                },
                {
                    "id": "b2c1",
                    "email": "c@x.it",
                    "role": "client",
                    "account_type": "b2c",
                    "name": "Bob",
                },
            ]
        )
        self.clients = _Coll([])
        self.properties = _Coll([])
        self.api_keys = _Coll([])
        self.ops_alerts = _Coll([])
        self.pricing_overrides = _Coll([])
        self.provider_flags = _Coll([])
        self.favorites = _Coll([])
        self.saved_searches = _Coll([])
        self.notifications = _Coll([])
        self.password_reset_tokens = _Coll([])
        self.refresh_tokens = _Coll([])
        self.agency_invites = _Coll([])

    async def list_collection_names(self):
        return ["clients", "properties", "api_keys", "agency_invites"]

    def __getitem__(self, name):
        if not hasattr(self, name):
            setattr(self, name, _Coll([]))
        return getattr(self, name)


@pytest.fixture
def patch_db(monkeypatch):
    db = _DB()
    monkeypatch.setattr(fb.Database, "get", staticmethod(lambda: db))
    circuit_mod.clear_hold("resend")
    circuit_mod.clear_hold("gemini")
    circuit_mod.clear_hold("llm")
    return db


def test_circuit_hold():
    circuit_mod.clear_hold("resend")
    circuit_mod.force_hold("resend", "test")
    assert circuit_mod.is_held("resend")
    assert circuit_mod.circuit_open("resend")
    circuit_mod.record_success("resend")  # must not clear hold
    assert circuit_mod.is_held("resend")
    circuit_mod.clear_hold("resend")
    assert not circuit_mod.is_held("resend")


def test_impersonate_enter_exit(patch_db):
    founder = {"id": "founder", "email": "f@x.it", "role": "super_admin", "agency_ids": []}
    out = asyncio.run(
        fb.bridge_impersonate(fb.ImpersonateBody(agency_id="agency-01"), user=founder)
    )
    assert out["ok"] is True
    u = patch_db.users.docs[0]
    assert u["active_agency_id"] == "agency-01"
    assert u["ops_impersonation"]["agency_id"] == "agency-01"
    founder2 = {**u, "role": "super_admin"}
    ex = asyncio.run(fb.bridge_impersonate_exit(user=founder2))
    assert ex["ok"] is True
    u2 = patch_db.users.docs[0]
    assert u2.get("ops_impersonation") is None
    assert u2.get("agency_ids") == []


def test_erase_user(patch_db):
    out = asyncio.run(
        fb.bridge_erase_user(
            "b2c1",
            fb.EraseUserBody(confirm="CANCELLA_UTENTE"),
            user={"id": "founder", "email": "f@x.it", "role": "super_admin"},
        )
    )
    assert out["status"] == "erased"
    bob = next(d for d in patch_db.users.docs if d["id"] == "b2c1")
    assert bob["is_active"] is False
    assert "@erased." in bob["email"]


def test_erase_confirm_required(patch_db):
    with pytest.raises(HTTPException) as ei:
        asyncio.run(
            fb.bridge_erase_user(
                "b2c1",
                fb.EraseUserBody(confirm="NOPE"),
                user={"id": "founder", "role": "super_admin"},
            )
        )
    assert ei.value.status_code == 400


def test_b2b_patch_no_stripe(patch_db, monkeypatch):
    monkeypatch.delenv("STRIPE_ENABLED", raising=False)
    out = asyncio.run(
        fb.bridge_patch_b2b_plan(
            "founders",
            "pro",
            fb.B2BPlanPatch(price_monthly=111.0, price_yearly=1111.0, sync_stripe=True),
            user={"id": "founder", "email": "f@x.it"},
        )
    )
    assert out["ok"] is True
    assert out["override"]["price_monthly"] == 111.0
    assert out["stripe"].get("skipped") or out["stripe"].get("ok") is False
