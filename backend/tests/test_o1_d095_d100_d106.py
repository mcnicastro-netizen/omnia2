"""O1 — D-095 fascicolo media · D-100 invite · D-106 active_agency_id (unit)."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from apps.immoweb.media import _is_blocked_path
from shared.auth.tenant import optional_agency_id, require_agency


def test_private_media_fascicolo_blocked():
    assert _is_blocked_path("omnia/fascicolo/prop1/doc1") is True
    assert _is_blocked_path("omnia/modulistica/agency/x.pdf") is True
    assert _is_blocked_path("omnia/properties/prop1/photo.jpg") is False


def test_optional_agency_no_fallback_to_first():
    user = {"agency_ids": ["a1", "a2"], "active_agency_id": None}
    assert optional_agency_id(user) is None
    user2 = {"agency_ids": ["a1", "a2"], "active_agency_id": "a2"}
    assert optional_agency_id(user2) == "a2"
    user3 = {"agency_ids": ["a1"], "active_agency_id": "missing"}
    assert optional_agency_id(user3) is None


def test_require_agency_errors():
    with pytest.raises(HTTPException) as ei:
        require_agency({"agency_ids": ["a1"]})
    assert ei.value.detail == "active_agency_required"

    with pytest.raises(HTTPException) as ei2:
        require_agency({"agency_ids": ["a1"], "active_agency_id": "other"})
    assert ei2.value.detail == "active_agency_invalid"

    assert require_agency({"agency_ids": ["a1"], "active_agency_id": "a1"}) == "a1"


def test_fascicolo_get_property_requires_active_agency():
    """IDOR guard: without active_agency_id, fascicolo must not resolve by id alone."""
    from apps.immoweb.fascicolo import _get_property

    db = MagicMock()
    db.properties.find_one = AsyncMock(return_value={"id": "p1", "agency_id": "a1"})
    user = {"id": "u1", "agency_ids": ["a1"], "active_agency_id": None}

    async def _run():
        with pytest.raises(HTTPException) as ei:
            await _get_property(db, user, "p1")
        assert ei.value.detail == "active_agency_required"
        db.properties.find_one.assert_not_called()

    asyncio.run(_run())


def test_fascicolo_get_property_scopes_to_agency():
    from apps.immoweb.fascicolo import _get_property

    db = MagicMock()
    db.properties.find_one = AsyncMock(return_value={"id": "p1", "agency_id": "a1"})
    user = {"id": "u1", "agency_ids": ["a1"], "active_agency_id": "a1"}

    async def _run():
        prop = await _get_property(db, user, "p1", {"_id": 0})
        assert prop["id"] == "p1"
        db.properties.find_one.assert_awaited_once()
        q = db.properties.find_one.await_args.args[0]
        assert q == {"id": "p1", "agency_id": "a1"}

    asyncio.run(_run())


def test_fascicolo_get_property_cross_tenant_404():
    from apps.immoweb.fascicolo import _get_property

    db = MagicMock()
    db.properties.find_one = AsyncMock(return_value=None)
    user = {"id": "u1", "agency_ids": ["agency-b"], "active_agency_id": "agency-b"}

    async def _run():
        with pytest.raises(HTTPException) as ei:
            await _get_property(db, user, "prop-of-agency-a")
        assert ei.value.status_code == 404
        q = db.properties.find_one.await_args.args[0]
        assert q["agency_id"] == "agency-b"

    asyncio.run(_run())


def test_best_effort_purge_doc_blob_calls_delete_object():
    from apps.immoweb import fascicolo as fz
    from unittest.mock import patch

    with patch.object(fz, "delete_object") as dig:
        fz._best_effort_purge_doc_blob({"id": "d1", "storage_path": "omnia/fascicolo/p1/d1"})
        dig.assert_called_once_with("omnia/fascicolo/p1/d1")


def test_best_effort_purge_skips_legacy_base64_docs():
    from apps.immoweb import fascicolo as fz
    from unittest.mock import patch

    with patch.object(fz, "delete_object") as dig:
        fz._best_effort_purge_doc_blob({"id": "d1", "file_data": "AAAA"})
        dig.assert_not_called()


def test_best_effort_purge_swallows_storage_errors():
    from apps.immoweb import fascicolo as fz
    from unittest.mock import patch

    with patch.object(fz, "delete_object", side_effect=RuntimeError("boom")):
        fz._best_effort_purge_doc_blob({"id": "d1", "storage_path": "omnia/fascicolo/p1/d1"})


def test_delete_document_purges_blob_after_mongo_pull():
    from apps.immoweb import fascicolo as fz
    from unittest.mock import AsyncMock, MagicMock, patch

    doc = {"id": "d1", "storage_path": "omnia/fascicolo/p1/d1", "name": "ape.pdf"}
    db = MagicMock()
    db.properties.find_one = AsyncMock(return_value={"id": "p1", "agency_id": "a1", "documents": [doc]})
    db.properties.update_one = AsyncMock(return_value=MagicMock(modified_count=1))
    user = {"id": "u1", "agency_ids": ["a1"], "active_agency_id": "a1"}

    async def _run():
        with patch.object(fz.Database, "get", return_value=db), \
             patch.object(fz, "delete_object") as dig:
            out = await fz.delete_document("p1", "d1", user=user)
            assert out == {"ok": True}
            dig.assert_called_once_with("omnia/fascicolo/p1/d1")
            q = db.properties.update_one.await_args.args[0]
            assert q == {"id": "p1", "agency_id": "a1"}

    asyncio.run(_run())
