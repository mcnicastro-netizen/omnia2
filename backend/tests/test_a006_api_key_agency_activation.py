"""A-006 — require_api_key agency gate aligned with D-152 resolve_activation_status."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from shared.auth import api_key as ak


class _Agencies:
    def __init__(self, doc):
        self.doc = doc

    async def find_one(self, query, projection=None):
        # Simulate Mongo projection semantics for tests
        if self.doc is None:
            return None
        if self.doc.get("id") != query.get("id"):
            return None
        if not projection:
            return dict(self.doc)
        out = {}
        for k, v in projection.items():
            if k == "_id":
                continue
            if v and k in self.doc:
                out[k] = self.doc[k]
            # missing field → omitted (critical for empty-projection bug)
        # Always include projected keys that exist; if only is_active projected and missing → {}
        return out


class _ApiKeys:
    def __init__(self, key_doc):
        self.key_doc = key_doc

    async def find_one(self, query):
        if self.key_doc and self.key_doc.get("key_hash") == query.get("key_hash"):
            return dict(self.key_doc)
        return None


def _db(agency_doc, key_doc):
    return SimpleNamespace(
        agencies=_Agencies(agency_doc),
        api_keys=_ApiKeys(key_doc),
    )


def _request(token: str):
    req = SimpleNamespace(
        headers={"Authorization": f"Bearer {token}"},
        state=SimpleNamespace(),
    )
    return req


def _valid_key(**overrides):
    plaintext = ak.KEY_PREFIX + ("a" * 28)
    doc = {
        "id": "key-1",
        "agency_id": "ag-1",
        "key_hash": ak.hash_key(plaintext),
        "is_active": True,
        "revoked_at": None,
        "credits_balance": 100,
        "allowed_origins": [],
    }
    doc.update(overrides)
    return plaintext, doc


async def _call(agency_doc, key_doc=None, token=None, endpoint="feed_properties"):
    plaintext, default_key = _valid_key()
    key_doc = default_key if key_doc is None else key_doc
    token = plaintext if token is None else token
    req = _request(token)

    async def _no_rl(**kwargs):
        return None

    with patch.object(ak.Database, "get", return_value=_db(agency_doc, key_doc)):
        with patch("shared.security.rate_limit.enforce_rate_limit", new=AsyncMock(side_effect=_no_rl)):
            return await ak.require_api_key(req, endpoint)


def test_legacy_no_activation_status_no_is_active_allowed():
    """D-152 grandfather: missing activation_status → active; missing is_active OK."""
    agency = {"id": "ag-1"}  # no is_active, no activation_status
    out = asyncio.run(_call(agency))
    assert out["id"] == "key-1"


def test_legacy_is_active_true_no_activation_status_allowed():
    agency = {"id": "ag-1", "is_active": True}
    out = asyncio.run(_call(agency))
    assert out["agency_id"] == "ag-1"


def test_active_agency_allowed():
    agency = {"id": "ag-1", "is_active": True, "activation_status": "active"}
    out = asyncio.run(_call(agency))
    assert out["id"] == "key-1"


def test_pending_agency_denied():
    agency = {"id": "ag-1", "is_active": True, "activation_status": "pending"}
    with pytest.raises(HTTPException) as ei:
        asyncio.run(_call(agency))
    assert ei.value.status_code == 403
    assert ei.value.detail == "agency_inactive"


def test_suspended_agency_denied():
    agency = {"id": "ag-1", "is_active": True, "activation_status": "suspended"}
    with pytest.raises(HTTPException) as ei:
        asyncio.run(_call(agency))
    assert ei.value.status_code == 403
    assert ei.value.detail == "agency_inactive"


def test_is_active_false_always_denied_even_if_activation_active():
    agency = {"id": "ag-1", "is_active": False, "activation_status": "active"}
    with pytest.raises(HTTPException) as ei:
        asyncio.run(_call(agency))
    assert ei.value.status_code == 403
    assert ei.value.detail == "agency_inactive"


def test_missing_agency_denied():
    with pytest.raises(HTTPException) as ei:
        asyncio.run(_call(None))
    assert ei.value.status_code == 403
    assert ei.value.detail == "agency_inactive"


def test_empty_projection_bug_fixed_when_id_present():
    """Agency exists without is_active: projection includes id → not falsy {}."""
    agency = {"id": "ag-1", "activation_status": "active"}
    # Explicitly ensure is_active key absent
    assert "is_active" not in agency
    out = asyncio.run(_call(agency))
    assert out["id"] == "key-1"


def test_revoked_api_key_denied():
    plaintext, key = _valid_key(is_active=False, revoked_at="2026-01-01T00:00:00+00:00")
    agency = {"id": "ag-1", "is_active": True, "activation_status": "active"}
    with pytest.raises(HTTPException) as ei:
        asyncio.run(_call(agency, key_doc=key, token=plaintext))
    assert ei.value.status_code == 403
    assert ei.value.detail == "api_key_revoked"


def test_invalid_api_key_denied():
    agency = {"id": "ag-1", "is_active": True, "activation_status": "active"}
    with pytest.raises(HTTPException) as ei:
        asyncio.run(_call(agency, token=ak.KEY_PREFIX + ("z" * 28)))
    assert ei.value.status_code == 401
    assert ei.value.detail == "invalid_api_key"


def test_is_active_null_with_active_status_allowed():
    agency = {"id": "ag-1", "is_active": None, "activation_status": "active"}
    out = asyncio.run(_call(agency))
    assert out["id"] == "key-1"
