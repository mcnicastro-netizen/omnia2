"""OMNIA — tenant-aware Mongo collection proxy (defense in depth).

When a request has an agency context (set by TenantContextMiddleware / JWT),
reads/writes on tenant collections auto-inject `agency_id` if the filter/doc
does not already specify one. Super-admin and explicit bypass skip injection.
Auto-inject is enabled only when tenant_enforce is True (/api/app/*).
"""
from __future__ import annotations

import logging
from contextvars import ContextVar
from typing import Any, Dict, Optional, Set

logger = logging.getLogger("omnia.tenant_db")

_current_role: ContextVar[Optional[str]] = ContextVar("current_role", default=None)
_tenant_bypass: ContextVar[bool] = ContextVar("tenant_bypass", default=False)
_tenant_enforce: ContextVar[bool] = ContextVar("tenant_enforce", default=False)

TENANT_COLLECTIONS: Set[str] = {
    "properties",
    "clients",
    "client_requests",
    "matches",
    "leads",
    "credit_transactions",
    "publishing_connections",
    "api_keys",
    "api_usage_log",
    "api_credit_ledger",
    "lead_score_cache",
    "agency_invites",
    "modulistica_docs",
    "virtual_staging_jobs",
    "social_posts",
}


def set_current_role(role: Optional[str]) -> None:
    _current_role.set(role)


def get_current_role() -> Optional[str]:
    return _current_role.get()


def tenant_bypass(enabled: bool = True) -> None:
    _tenant_bypass.set(bool(enabled))


def set_tenant_enforce(enabled: bool) -> None:
    """Only /api/app/* should auto-inject agency_id (not public cloud search)."""
    _tenant_enforce.set(bool(enabled))


def is_tenant_bypass() -> bool:
    if not _tenant_enforce.get():
        return True
    return bool(_tenant_bypass.get()) or get_current_role() == "super_admin"


def _inject_filter(flt: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    from shared.db.connection import get_current_agency_id

    base = dict(flt or {})
    if is_tenant_bypass():
        return base
    aid = get_current_agency_id()
    if not aid:
        return base
    if "agency_id" not in base:
        base["agency_id"] = aid
    return base


def _inject_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    from shared.db.connection import get_current_agency_id

    out = dict(doc or {})
    if is_tenant_bypass():
        return out
    aid = get_current_agency_id()
    if aid and "agency_id" not in out:
        out["agency_id"] = aid
    return out


class TenantCollection:
    """Proxy around AsyncIOMotorCollection with auto agency_id injection."""

    def __init__(self, coll):
        self._coll = coll

    def __getattr__(self, item):
        return getattr(self._coll, item)

    def find(self, filter=None, *args, **kwargs):
        return self._coll.find(_inject_filter(filter), *args, **kwargs)

    def find_one(self, filter=None, *args, **kwargs):
        return self._coll.find_one(_inject_filter(filter), *args, **kwargs)

    def find_one_and_update(self, filter, update, *args, **kwargs):
        return self._coll.find_one_and_update(_inject_filter(filter), update, *args, **kwargs)

    def find_one_and_delete(self, filter, *args, **kwargs):
        return self._coll.find_one_and_delete(_inject_filter(filter), *args, **kwargs)

    def update_one(self, filter, update, *args, **kwargs):
        return self._coll.update_one(_inject_filter(filter), update, *args, **kwargs)

    def update_many(self, filter, update, *args, **kwargs):
        return self._coll.update_many(_inject_filter(filter), update, *args, **kwargs)

    def delete_one(self, filter, *args, **kwargs):
        return self._coll.delete_one(_inject_filter(filter), *args, **kwargs)

    def delete_many(self, filter, *args, **kwargs):
        return self._coll.delete_many(_inject_filter(filter), *args, **kwargs)

    def count_documents(self, filter=None, *args, **kwargs):
        return self._coll.count_documents(_inject_filter(filter), *args, **kwargs)

    def aggregate(self, pipeline, *args, **kwargs):
        from shared.db.connection import get_current_agency_id

        aid = get_current_agency_id()
        pipe = list(pipeline or [])
        if aid and not is_tenant_bypass():
            if not pipe or "$match" not in (pipe[0] or {}) or "agency_id" not in pipe[0].get("$match", {}):
                pipe.insert(0, {"$match": {"agency_id": aid}})
        return self._coll.aggregate(pipe, *args, **kwargs)

    async def insert_one(self, document, *args, **kwargs):
        return await self._coll.insert_one(_inject_doc(document), *args, **kwargs)

    async def insert_many(self, documents, *args, **kwargs):
        docs = [_inject_doc(d) for d in documents]
        return await self._coll.insert_many(docs, *args, **kwargs)


class TenantAwareDatabase:
    """Wraps Motor database; tenant collections return TenantCollection."""

    def __init__(self, db):
        self._db = db

    def __getattr__(self, item: str):
        if item in (
            "command",
            "list_collection_names",
            "create_collection",
            "delegate",
            "with_options",
            "client",
            "name",
            "codec_options",
            "read_preference",
            "write_concern",
            "read_concern",
        ):
            return getattr(self._db, item)
        coll = self._db[item]
        if item in TENANT_COLLECTIONS:
            return TenantCollection(coll)
        return coll

    def __getitem__(self, item: str):
        coll = self._db[item]
        if item in TENANT_COLLECTIONS:
            return TenantCollection(coll)
        return coll
