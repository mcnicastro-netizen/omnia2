"""OMNIA — tenant-aware Mongo collection proxy (defense in depth).

When a request has an agency context (set by TenantContextMiddleware / JWT),
reads/writes on tenant collections force `agency_id` from that context (client
values are overwritten). Super-admin and explicit bypass skip injection.
Auto-inject is enabled only when tenant_enforce is True (/api/app/*).
Cross-collection aggregate stages ($lookup/$unionWith/…) are rejected under
enforce. bulk_write is refused under enforce (fail-closed).
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
    "credit_wallets",
    "publishing_connections",
    "api_keys",
    "api_usage_log",
    "api_credit_ledger",
    "lead_score_cache",
    "agency_invites",
    # Legacy alias kept; real collection name is modulistica_documents.
    "modulistica_docs",
    "modulistica_documents",
    "virtual_staging_jobs",
    "social_posts",
    "social_channels",
    # PRE-GTM W3 — single-agency CRM / funnel / ledger / calendar.
    "activities",
    "mandate_opportunities",
    "ai_client_import_drafts",
    "calendar_events",
    "credit_ledger",
    "match_audit",
    # W3 staging readiness — import / publishing sync are single-agency.
    "import_jobs",
    "publishing_sync_logs",
    # Intentionally NOT here (owner/partner, mixed public, or non-agency key):
    # deals, mls_*, videos (mixed public/agency), property_stat_days (keyed by
    # property_id; ownership checked in handlers), users, agencies, memberships,
    # commercial_*, cc_*, notifications (user-scoped), favorites, marketing leads,
    # payment_transactions (Stripe webhook path without tenant context).
}

# Aggregation stages that can pull data from other collections without the
# tenant $match applying to the foreign side. Reject under enforce.
_TENANT_FORBIDDEN_AGG_STAGES = frozenset(
    {"$lookup", "$unionWith", "$graphLookup", "$out", "$merge"}
)


class TenantContextRequired(RuntimeError):
    """Enforce is on but no trusted agency context — fail closed."""


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
    """Force caller agency_id when enforce is on.

    PRE-GTM W3 / explore finding: previously we only injected when the key was
    absent, so a client-supplied ``agency_id`` in the filter was trusted and
    could enable cross-tenant IDOR if a route forwarded query/body into Mongo.
    """
    from shared.db.connection import get_current_agency_id

    base = dict(flt or {})
    if is_tenant_bypass():
        return base
    aid = get_current_agency_id()
    if not aid:
        # W3 secondary paths: never run unscoped queries on guarded collections
        # when /api/app enforce is active but agency context is missing.
        raise TenantContextRequired("tenant_context_required")
    base["agency_id"] = aid
    return base


def _inject_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    from shared.db.connection import get_current_agency_id

    out = dict(doc or {})
    if is_tenant_bypass():
        return out
    aid = get_current_agency_id()
    if not aid:
        raise TenantContextRequired("tenant_context_required")
    out["agency_id"] = aid
    return out


def _scrub_update_agency_id(update: Any) -> Any:
    """Prevent tenant reassignment via $set/$unset/$rename under enforce.

    Filter injection alone does not stop ``{$set: {agency_id: other}}`` on a
    document already scoped to the caller. Under enforce we force the trusted
    agency_id into $set and strip conflicting unset/rename ops.
    """
    from shared.db.connection import get_current_agency_id

    if is_tenant_bypass():
        return update
    aid = get_current_agency_id()
    if not aid:
        raise TenantContextRequired("tenant_context_required")
    if not isinstance(update, dict):
        return update
    out = dict(update)
    # Operator-style update document
    if any(str(k).startswith("$") for k in out.keys()):
        aset = dict(out.get("$set") or {})
        aset["agency_id"] = aid
        out["$set"] = aset
        if "$unset" in out and isinstance(out["$unset"], dict):
            unset = dict(out["$unset"])
            unset.pop("agency_id", None)
            if unset:
                out["$unset"] = unset
            else:
                out.pop("$unset", None)
        if "$rename" in out and isinstance(out["$rename"], dict):
            rename = dict(out["$rename"])
            rename.pop("agency_id", None)
            # Also block renaming *into* agency_id
            rename = {k: v for k, v in rename.items() if v != "agency_id"}
            if rename:
                out["$rename"] = rename
            else:
                out.pop("$rename", None)
        return out
    # Replacement-style body used rarely with update_*: force agency
    out["agency_id"] = aid
    return out


def _reject_cross_collection_stages(pipe: list) -> None:
    for stage in pipe:
        if not isinstance(stage, dict):
            continue
        for key in stage:
            if key in _TENANT_FORBIDDEN_AGG_STAGES:
                raise ValueError(
                    f"tenant_guard_forbidden_agg_stage:{key}"
                )


class TenantCollection:
    """Proxy around AsyncIOMotorCollection with auto agency_id injection."""

    def __init__(self, coll):
        self._coll = coll

    def __getattr__(self, item):
        # Defense in depth: mutation/query helpers that take filters must not
        # silently bypass injection via Motor passthrough.
        if item in {
            "replace_one",
            "bulk_write",
            "distinct",
            "find_one_and_replace",
            "update_one",
            "update_many",
            "delete_one",
            "delete_many",
            "find",
            "find_one",
            "aggregate",
            "count_documents",
            "estimated_document_count",
            "insert_one",
            "insert_many",
            "find_one_and_update",
            "find_one_and_delete",
        }:
            raise AttributeError(
                f"TenantCollection.{item} must use the wrapped implementation"
            )
        return getattr(self._coll, item)

    def find(self, filter=None, *args, **kwargs):
        return self._coll.find(_inject_filter(filter), *args, **kwargs)

    def find_one(self, filter=None, *args, **kwargs):
        return self._coll.find_one(_inject_filter(filter), *args, **kwargs)

    def find_one_and_update(self, filter, update, *args, **kwargs):
        return self._coll.find_one_and_update(
            _inject_filter(filter), _scrub_update_agency_id(update), *args, **kwargs
        )

    def find_one_and_delete(self, filter, *args, **kwargs):
        return self._coll.find_one_and_delete(_inject_filter(filter), *args, **kwargs)

    def find_one_and_replace(self, filter, replacement, *args, **kwargs):
        return self._coll.find_one_and_replace(
            _inject_filter(filter), _inject_doc(dict(replacement or {})), *args, **kwargs
        )

    def update_one(self, filter, update, *args, **kwargs):
        return self._coll.update_one(
            _inject_filter(filter), _scrub_update_agency_id(update), *args, **kwargs
        )

    def update_many(self, filter, update, *args, **kwargs):
        return self._coll.update_many(
            _inject_filter(filter), _scrub_update_agency_id(update), *args, **kwargs
        )

    def estimated_document_count(self, *args, **kwargs):
        # Unscoped estimate would leak cross-tenant cardinality under enforce.
        if not is_tenant_bypass():
            raise ValueError("tenant_guard_estimated_document_count_forbidden_under_enforce")
        return self._coll.estimated_document_count(*args, **kwargs)

    def replace_one(self, filter, replacement, *args, **kwargs):
        return self._coll.replace_one(
            _inject_filter(filter), _inject_doc(dict(replacement or {})), *args, **kwargs
        )

    def delete_one(self, filter, *args, **kwargs):
        return self._coll.delete_one(_inject_filter(filter), *args, **kwargs)

    def delete_many(self, filter, *args, **kwargs):
        return self._coll.delete_many(_inject_filter(filter), *args, **kwargs)

    def count_documents(self, filter=None, *args, **kwargs):
        return self._coll.count_documents(_inject_filter(filter), *args, **kwargs)

    def distinct(self, key, filter=None, *args, **kwargs):
        return self._coll.distinct(key, _inject_filter(filter), *args, **kwargs)

    def bulk_write(self, requests, *args, **kwargs):
        # No in-app usages today. Under enforce, refuse rather than risk an
        # unscoped bulk write slipping through incomplete request rewriting.
        if not is_tenant_bypass():
            raise ValueError("tenant_guard_bulk_write_forbidden_under_enforce")
        return self._coll.bulk_write(requests, *args, **kwargs)

    def aggregate(self, pipeline, *args, **kwargs):
        from shared.db.connection import get_current_agency_id

        aid = get_current_agency_id()
        pipe = list(pipeline or [])
        if not is_tenant_bypass():
            if not aid:
                raise TenantContextRequired("tenant_context_required")
            _reject_cross_collection_stages(pipe)
            if pipe and isinstance(pipe[0], dict) and "$match" in pipe[0]:
                match = dict(pipe[0]["$match"] or {})
                match["agency_id"] = aid
                pipe[0] = {"$match": match}
            else:
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
