"""PRE-GTM W3 — adversarial verification of TenantCollection inject."""
from __future__ import annotations

import pytest

from shared.db import tenant_guard as tg
from shared.db.connection import Database, set_current_agency_id


class RecordingColl:
    """Minimal Motor-like collection that records filters/docs."""

    def __init__(self):
        self.calls = []

    def find(self, filter=None, *a, **k):
        self.calls.append(("find", filter))
        return filter

    def find_one(self, filter=None, *a, **k):
        self.calls.append(("find_one", filter))
        return filter

    def update_one(self, filter, update, *a, **k):
        self.calls.append(("update_one", filter, update))
        return filter

    def update_many(self, filter, update, *a, **k):
        self.calls.append(("update_many", filter, update))
        return filter

    def delete_one(self, filter, *a, **k):
        self.calls.append(("delete_one", filter))
        return filter

    def delete_many(self, filter, *a, **k):
        self.calls.append(("delete_many", filter))
        return filter

    def replace_one(self, filter, replacement, *a, **k):
        self.calls.append(("replace_one", filter, replacement))
        return filter

    def find_one_and_update(self, filter, update, *a, **k):
        self.calls.append(("find_one_and_update", filter, update))
        return filter

    def find_one_and_delete(self, filter, *a, **k):
        self.calls.append(("find_one_and_delete", filter))
        return filter

    def find_one_and_replace(self, filter, replacement, *a, **k):
        self.calls.append(("find_one_and_replace", filter, replacement))
        return filter

    def count_documents(self, filter=None, *a, **k):
        self.calls.append(("count_documents", filter))
        return 0

    def distinct(self, key, filter=None, *a, **k):
        self.calls.append(("distinct", key, filter))
        return []

    def aggregate(self, pipeline, *a, **k):
        self.calls.append(("aggregate", pipeline))
        return pipeline

    def bulk_write(self, requests, *a, **k):
        self.calls.append(("bulk_write", requests))
        return requests

    async def insert_one(self, document, *a, **k):
        self.calls.append(("insert_one", document))
        return document

    async def insert_many(self, documents, *a, **k):
        self.calls.append(("insert_many", documents))
        return documents


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


def _armed(agency="agency-A") -> tg.TenantCollection:
    tg.set_tenant_enforce(True)
    set_current_agency_id(agency)
    return tg.TenantCollection(RecordingColl())


def test_all_mutations_force_agency_over_client():
    proxy = _armed()
    evil = {"agency_id": "agency-B", "id": "x"}
    proxy.find(evil)
    proxy.find_one(evil)
    proxy.update_one(evil, {"$set": {"t": 1}})
    proxy.update_many(evil, {"$set": {"t": 1}})
    proxy.delete_one(evil)
    proxy.delete_many(evil)
    proxy.replace_one(evil, {"agency_id": "agency-B", "title": "stolen"})
    proxy.find_one_and_update(evil, {"$set": {"t": 1}})
    proxy.find_one_and_delete(evil)
    proxy.find_one_and_replace(evil, {"agency_id": "agency-B"})
    proxy.count_documents(evil)
    proxy.distinct("id", evil)
    for call in proxy._coll.calls:
        flt = call[1] if call[0] != "distinct" else call[2]
        if call[0] == "replace_one":
            assert flt["agency_id"] == "agency-A"
            assert call[2]["agency_id"] == "agency-A"
        elif call[0] == "find_one_and_replace":
            assert flt["agency_id"] == "agency-A"
            assert call[2]["agency_id"] == "agency-A"
        elif call[0] == "distinct":
            assert flt["agency_id"] == "agency-A"
        elif call[0] in ("update_one", "update_many", "find_one_and_update"):
            assert flt["agency_id"] == "agency-A"
        else:
            assert flt["agency_id"] == "agency-A"


def test_insert_forces_agency():
    import asyncio

    proxy = _armed()

    async def _go():
        await proxy.insert_one({"agency_id": "agency-B", "title": "x"})
        await proxy.insert_many([{"agency_id": "agency-B"}, {"agency_id": "agency-C"}])

    asyncio.get_event_loop().run_until_complete(_go())
    assert proxy._coll.calls[0][1]["agency_id"] == "agency-A"
    assert all(d["agency_id"] == "agency-A" for d in proxy._coll.calls[1][1])


def test_or_and_nor_collision_still_scopes_to_caller():
    """Top-level agency_id AND keeps scope even if nested ops claim B."""
    out = None
    tg.set_tenant_enforce(True)
    set_current_agency_id("agency-A")
    out = tg._inject_filter(
        {
            "$or": [{"agency_id": "agency-B"}, {"id": "victim"}],
            "$and": [{"agency_id": "agency-B"}],
            "$nor": [{"status": "x"}],
        }
    )
    assert out["agency_id"] == "agency-A"
    # Nested evil agency_id remains but cannot satisfy AND with agency-A
    assert out["$or"][0]["agency_id"] == "agency-B"
    assert out["$and"][0]["agency_id"] == "agency-B"


def test_operator_agency_id_ne_overwritten():
    tg.set_tenant_enforce(True)
    set_current_agency_id("agency-A")
    out = tg._inject_filter({"agency_id": {"$ne": "agency-A"}, "id": "x"})
    assert out["agency_id"] == "agency-A"


def test_aggregate_prefixes_match_and_overwrites():
    proxy = _armed()
    proxy.aggregate(
        [{"$match": {"agency_id": "agency-B", "status": "open"}}, {"$group": {"_id": "$status"}}]
    )
    pipe = proxy._coll.calls[0][1]
    assert pipe[0] == {"$match": {"agency_id": "agency-A", "status": "open"}}


@pytest.mark.parametrize(
    "stage",
    [
        {"$lookup": {"from": "clients", "localField": "id", "foreignField": "property_id", "as": "c"}},
        {"$unionWith": "clients"},
        {"$graphLookup": {"from": "clients", "startWith": "$id", "connectFromField": "id", "connectToField": "parent", "as": "x"}},
        {"$out": "leak"},
        {"$merge": {"into": "leak"}},
    ],
)
def test_aggregate_rejects_cross_collection_stages(stage):
    proxy = _armed()
    with pytest.raises(ValueError, match="tenant_guard_forbidden_agg_stage"):
        proxy.aggregate([{"$match": {"status": "open"}}, stage])


def test_bulk_write_forbidden_under_enforce():
    proxy = _armed()
    with pytest.raises(ValueError, match="tenant_guard_bulk_write_forbidden"):
        proxy.bulk_write([])


def test_update_scrubs_agency_id_in_set_unset():
    proxy = _armed()
    proxy.update_one(
        {"id": "x", "agency_id": "agency-B"},
        {"$set": {"agency_id": "agency-B", "t": 1}, "$unset": {"agency_id": ""}},
    )
    _op, flt, upd = proxy._coll.calls[0]
    assert flt["agency_id"] == "agency-A"
    assert upd["$set"]["agency_id"] == "agency-A"
    assert "agency_id" not in (upd.get("$unset") or {})


def test_estimated_document_count_forbidden():
    proxy = _armed()
    with pytest.raises(ValueError, match="estimated_document_count_forbidden"):
        proxy.estimated_document_count()


def test_bulk_write_allowed_on_bypass():
    tg.set_tenant_enforce(True)
    tg.tenant_bypass(True)
    set_current_agency_id("agency-A")
    proxy = tg.TenantCollection(RecordingColl())
    proxy.bulk_write(["noop"])
    assert proxy._coll.calls[0][0] == "bulk_write"


def test_missing_agency_context_fail_closed():
    tg.set_tenant_enforce(True)
    set_current_agency_id(None)
    with pytest.raises(tg.TenantContextRequired):
        tg._inject_filter({"agency_id": "agency-B", "id": "x"})
    with pytest.raises(tg.TenantContextRequired):
        tg._inject_doc({"title": "x"})


def test_tenant_filter_helper_overwrites_extra_agency():
    set_current_agency_id("agency-A")
    flt = Database.tenant_filter({"agency_id": "agency-B", "id": "p1"})
    assert flt == {"agency_id": "agency-A", "id": "p1"}


def test_aware_db_wraps_new_single_agency_collections():
    class Raw:
        def __getitem__(self, name):
            return RecordingColl()

        def __getattr__(self, name):
            return RecordingColl()

    db = tg.TenantAwareDatabase(Raw())
    for name in (
        "activities",
        "modulistica_documents",
        "mandate_opportunities",
        "social_channels",
        "ai_client_import_drafts",
        "credit_wallets",
    ):
        assert isinstance(getattr(db, name), tg.TenantCollection)
        assert isinstance(db[name], tg.TenantCollection)


def test_aware_db_does_not_wrap_deals_or_mls():
    class Raw:
        def __getitem__(self, name):
            return RecordingColl()

        def __getattr__(self, name):
            return RecordingColl()

    db = tg.TenantAwareDatabase(Raw())
    for name in ("deals", "mls_visits", "mls_collaborations", "mls_chat_threads", "users"):
        assert not isinstance(getattr(db, name), tg.TenantCollection)


def test_middleware_context_source_is_not_query_param():
    """Regression sniff: tenant middleware must not read agency from query/body."""
    import inspect
    from shared.db import tenant_middleware as tm

    src = inspect.getsource(tm.TenantContextMiddleware.dispatch)
    assert "request.query" not in src
    assert "query_params" not in src
    assert ".json()" not in src
    assert "optional_agency_id" in src
    assert "decode_token" in src
