"""Cabina di regia — endpoint bridge (super_admin)."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import pytest
from fastapi import HTTPException

from apps.immoweb import founder_bridge as fb


class _Cur:
    def __init__(self, docs: List[dict]):
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
        if hits:
            hits[0].update((upd.get("$set") or {}))
        elif upsert:
            doc = dict(q)
            doc.update(upd.get("$set") or {})
            self.docs.append(doc)
            R.matched_count = 1
        return R()

    async def insert_one(self, doc):
        self.docs.append(doc)

    def _match(self, q: dict) -> List[dict]:
        if not q:
            return list(self.docs)
        out = []
        for d in self.docs:
            ok = True
            for k, v in q.items():
                if k == "$or":
                    continue
                if k == "trashed_at" and isinstance(v, dict) and "$exists" in v:
                    exists = "trashed_at" in d and d.get("trashed_at") is not None
                    if v["$exists"] is False and exists:
                        ok = False
                    continue
                if isinstance(v, dict) and "$in" in v:
                    if d.get(k) not in v["$in"]:
                        ok = False
                    continue
                if isinstance(v, dict) and "$exists" in v:
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
                    "id": "a1",
                    "slug": "demo",
                    "display_name": "Demo",
                    "activation_status": "pending",
                    "owner_id": "u1",
                    "created_at": "2026-01-01T00:00:00+00:00",
                }
            ]
        )
        self.users = _Coll(
            [
                {"id": "u1", "email": "a@x.it", "name": "Ada", "account_type": "b2b", "role": "agency_admin"},
                {"id": "b1", "email": "c@x.it", "name": "Bob", "account_type": "b2c", "client_code": "OM-C-TEST01"},
            ]
        )
        self.clients = _Coll([])
        self.properties = _Coll([])
        self.api_keys = _Coll(
            [
                {
                    "id": "k1",
                    "agency_id": "a1",
                    "name": "prod",
                    "key_prefix": "om_live_xxxx",
                    "is_active": True,
                    "credits_balance": 10,
                    "key_hash": "x",
                }
            ]
        )
        self.ops_alerts = _Coll([])
        self.pricing_overrides = _Coll([])


@pytest.fixture
def patch_db(monkeypatch):
    db = _DB()
    monkeypatch.setattr(fb.Database, "get", staticmethod(lambda: db))
    return db


def test_bridge_summary(patch_db):
    out = asyncio.run(fb.bridge_summary({"role": "super_admin"}))
    assert out["ok"] is True
    assert out["activation_pending"] == 1
    assert out["agencies_total"] == 1
    assert out["b2c_users"] == 1
    assert out["api_keys_active"] == 1


def test_bridge_tenants(patch_db):
    out = asyncio.run(fb.bridge_tenants(q="", status="pending", limit=50, user={"role": "super_admin"}))
    assert out["count"] == 1
    assert out["items"][0]["owner_email"] == "a@x.it"


def test_bridge_revoke(patch_db):
    out = asyncio.run(
        fb.bridge_revoke_key("k1", user={"role": "super_admin", "id": "f", "email": "f@x.it"})
    )
    assert out["ok"] is True
    assert patch_db.api_keys.docs[0]["is_active"] is False


def test_bridge_catalog_and_patch(patch_db, monkeypatch):
    out = asyncio.run(fb.bridge_catalog({"role": "super_admin"}))
    assert out["ok"] is True
    assert out["b2c"]
    key = out["b2c"][0]["key"]
    patched = asyncio.run(
        fb.bridge_patch_b2c_price(
            key,
            fb.B2CPricePatch(price_eur=9.99, note="test"),
            user={"role": "super_admin", "id": "f", "email": "f@x.it"},
        )
    )
    assert patched["ok"] is True
    assert patched["override"]["price_eur"] == 9.99
