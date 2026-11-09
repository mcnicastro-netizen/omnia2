"""Onda 6 — AuthZ storage_path prefix + modulistica agency scope (D-095)."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from shared.auth.storage_paths import (
    assert_storage_under_prefix,
    fascicolo_prefix,
    modulistica_prefix,
)


def test_assert_storage_accepts_owned_prefix():
    p = assert_storage_under_prefix(
        "omnia/modulistica/ag-1/doc.pdf",
        modulistica_prefix("ag-1"),
    )
    assert p == "omnia/modulistica/ag-1/doc.pdf"


def test_assert_storage_rejects_cross_tenant_prefix():
    with pytest.raises(HTTPException) as ei:
        assert_storage_under_prefix(
            "omnia/modulistica/ag-OTHER/doc.pdf",
            modulistica_prefix("ag-1"),
        )
    assert ei.value.status_code == 404


def test_assert_storage_rejects_traversal():
    with pytest.raises(HTTPException):
        assert_storage_under_prefix(
            "omnia/modulistica/ag-1/../ag-OTHER/x.pdf",
            modulistica_prefix("ag-1"),
        )


def test_fascicolo_prefix_helper():
    assert fascicolo_prefix("prop-9") == "omnia/fascicolo/prop-9/"


def test_modulistica_get_document_scopes_agency():
    from apps.immoweb import modulistica as mod

    db = MagicMock()
    db.modulistica_documents.find_one = AsyncMock(return_value=None)
    user = {"id": "u1", "agency_ids": ["ag-b"], "active_agency_id": "ag-b"}

    async def _run():
        with patch.object(mod, "Database") as DB:
            DB.get.return_value = db
            with pytest.raises(HTTPException) as ei:
                await mod.get_document("doc-of-ag-a", user)
            assert ei.value.status_code == 404
            q = db.modulistica_documents.find_one.await_args.args[0]
            assert q == {"id": "doc-of-ag-a", "agency_id": "ag-b"}

    asyncio.run(_run())


def test_modulistica_download_rejects_spoofed_storage_path():
    from apps.immoweb import modulistica as mod

    db = MagicMock()
    db.modulistica_documents.find_one = AsyncMock(
        return_value={
            "id": "d1",
            "agency_id": "ag-1",
            "slug": "proposta",
            "storage_path": "omnia/modulistica/ag-OTHER/secret.pdf",
        }
    )
    user = {"id": "u1", "agency_ids": ["ag-1"], "active_agency_id": "ag-1"}

    async def _run():
        with patch.object(mod, "Database") as DB:
            DB.get.return_value = db
            with patch.object(mod, "get_object") as go:
                with pytest.raises(HTTPException) as ei:
                    await mod.download_document("d1", user)
                assert ei.value.status_code == 404
                go.assert_not_called()

    asyncio.run(_run())


def test_fascicolo_download_rejects_spoofed_storage_path():
    from apps.immoweb import fascicolo as fz

    db = MagicMock()
    user = {"id": "u1", "agency_ids": ["ag-1"], "active_agency_id": "ag-1"}
    prop = {
        "id": "p1",
        "agency_id": "ag-1",
        "documents": [
            {
                "id": "d1",
                "name": "ape.pdf",
                "mime": "application/pdf",
                "storage_path": "omnia/fascicolo/OTHER/d1",
            }
        ],
    }

    async def _run():
        with patch.object(fz, "_get_property", AsyncMock(return_value=prop)):
            with patch.object(fz, "get_object") as go:
                with pytest.raises(HTTPException) as ei:
                    await fz.download_document("p1", "d1", user)
                assert ei.value.status_code == 404
                go.assert_not_called()

    asyncio.run(_run())
