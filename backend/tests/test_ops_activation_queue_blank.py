"""Activation queue enrichment + blank slate keeps Founder."""
from __future__ import annotations

import asyncio

from apps.immoweb.demo_retire import blank_slate_platform


class _Coll:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    async def find_one(self, q, *a, **k):
        if "agency_id" in q and q["agency_id"] == {"$exists": True}:
            return self.docs[0] if self.docs else None
        for d in self.docs:
            ok = True
            for kk, vv in q.items():
                if kk == "$in":
                    continue
                if d.get(kk) != vv:
                    ok = False
                    break
            if ok:
                return d
        if "id" in q:
            for d in self.docs:
                if d.get("id") == q["id"]:
                    return d
        return None

    async def delete_many(self, q):
        before = len(self.docs)
        if q == {} or (isinstance(q.get("agency_id"), dict) and "$exists" in q["agency_id"]):
            self.docs = []
        elif "id" in q and isinstance(q["id"], dict) and "$in" in q["id"]:
            ids = set(q["id"]["$in"])
            self.docs = [d for d in self.docs if d.get("id") not in ids]
        else:
            self.docs = [d for d in self.docs if not all(d.get(k) == v for k, v in q.items())]
        class R:
            deleted_count = before - len(self.docs)
        return R()

    async def update_one(self, q, upd):
        for d in self.docs:
            if d.get("id") == q.get("id"):
                d.update((upd.get("$set") or {}))
                return
        return None

    async def update_many(self, q, upd):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                d.update((upd.get("$set") or {}))
        class R:
            modified_count = 1
        return R()

    def find(self, q, *a, **k):
        class C:
            async def to_list(self2, n=None, length=None):
                return list(self.docs)
        return C()


class _DB:
    def __init__(self):
        self.agencies = _Coll(
            [{"id": "a1", "slug": "x", "display_name": "X", "activation_status": "pending"}]
        )
        self.users = _Coll(
            [
                {"id": "founder", "role": "super_admin", "email": "f@x.it", "agency_ids": ["a1"]},
                {"id": "admin1", "role": "agency_admin", "email": "a@x.it", "agency_ids": ["a1"]},
                {"id": "b2c1", "role": "client", "account_type": "b2c", "email": "c@x.it"},
            ]
        )
        self.properties = _Coll([{"agency_id": "a1", "title": "p"}])
        self.agency_invites = _Coll([{"agency_id": "a1"}])
        self._names = ["agencies", "users", "properties", "agency_invites"]

    async def list_collection_names(self):
        return self._names

    def __getitem__(self, name):
        return getattr(self, name)


def test_blank_slate_keeps_founder_and_b2c():
    db = _DB()
    out = asyncio.run(blank_slate_platform(db, keep_user_id="founder"))
    assert out["ok"] is True
    assert out["agencies_deleted"] == 1
    assert out["users_deleted"] == 1  # agency_admin
    assert len(db.agencies.docs) == 0
    assert len(db.properties.docs) == 0
    ids = {u["id"] for u in db.users.docs}
    assert "founder" in ids
    assert "b2c1" in ids
    assert "admin1" not in ids
    founder = next(u for u in db.users.docs if u["id"] == "founder")
    assert founder.get("agency_ids") == []
