"""wipe_agency_crm_data clears CRM docs but keeps agency + users."""
from __future__ import annotations

import asyncio

from apps.immoweb.demo_retire import wipe_agency_crm_data


class _FakeColl:
    def __init__(self, docs=None):
        self.docs = list(docs or [])

    async def count_documents(self, q):
        aid = q.get("agency_id")
        return sum(1 for d in self.docs if d.get("agency_id") == aid)

    async def delete_many(self, q):
        aid = q.get("agency_id")
        before = len(self.docs)
        self.docs = [d for d in self.docs if d.get("agency_id") != aid]
        deleted = before - len(self.docs)

        class R:
            deleted_count = deleted

        return R()

    async def find_one(self, q, *a, **k):
        for d in self.docs:
            if d.get("id") == q.get("id") or d.get("slug") == q.get("slug"):
                return d
        return None


class _FakeDB:
    def __init__(self):
        aid = "ag-1"
        self.agencies = _FakeColl([{"id": aid, "slug": "demo-slug"}])
        self.properties = _FakeColl([{"agency_id": aid}, {"agency_id": aid}])
        self.clients = _FakeColl([{"agency_id": aid}])
        self.users = _FakeColl([{"id": "u1", "agency_ids": [aid]}])
        self.subscriptions = _FakeColl([{"agency_id": aid}])
        self.credit_wallets = _FakeColl([{"agency_id": aid}])
        self.agency_invites = _FakeColl([{"agency_id": aid}])
        self._names = [
            "agencies",
            "users",
            "properties",
            "clients",
            "subscriptions",
            "credit_wallets",
            "agency_invites",
        ]

    async def list_collection_names(self):
        return self._names

    def __getitem__(self, name):
        return getattr(self, name)


def test_wipe_keeps_agency_users_billing():
    db = _FakeDB()
    out = asyncio.get_event_loop().run_until_complete(wipe_agency_crm_data(db, "ag-1"))
    assert out["ok"] is True
    assert out["total_deleted"] == 4  # 2 props + 1 client + 1 invite
    assert len(db.properties.docs) == 0
    assert len(db.clients.docs) == 0
    assert len(db.agencies.docs) == 1
    assert len(db.users.docs) == 1
    assert len(db.subscriptions.docs) == 1
    assert len(db.credit_wallets.docs) == 1
