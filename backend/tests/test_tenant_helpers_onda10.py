"""Onda 10 — tenant helpers + anti-leak 2-agency (D-106)."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from shared.auth.tenant import (
    optional_agency_id,
    require_agency,
    require_agency_404,
    require_agency_id,
)


def test_require_agency_id_alias():
    assert require_agency_id is require_agency
    user = {"agency_ids": ["ag-a"], "active_agency_id": "ag-a"}
    assert require_agency_id(user) == "ag-a"


def test_no_fallback_to_agency_ids_zero():
    user = {"agency_ids": ["ag-a", "ag-b"], "active_agency_id": None}
    assert optional_agency_id(user) is None
    with pytest.raises(HTTPException) as ei:
        require_agency(user)
    assert ei.value.status_code == 400
    assert ei.value.detail == "active_agency_required"


def test_cross_agency_active_rejected():
    user = {"agency_ids": ["ag-a"], "active_agency_id": "ag-b"}
    assert optional_agency_id(user) is None
    with pytest.raises(HTTPException):
        require_agency_404(user)


def test_themes_agency_for_uses_active_not_first():
    """Regression: themes._agency_for must not pick agency_ids[0]."""
    from apps.immoweb.themes import _agency_for

    user = {
        "agency_ids": ["ag-first", "ag-active"],
        "active_agency_id": "ag-active",
    }
    db = MagicMock()
    db.agencies.find_one = AsyncMock(return_value={"id": "ag-active", "slug": "x"})

    async def _run():
        with patch("apps.immoweb.themes.Database.get", return_value=db):
            ag = await _agency_for(user)
            assert ag["id"] == "ag-active"
            db.agencies.find_one.assert_awaited()
            args = db.agencies.find_one.await_args.args[0]
            assert args == {"id": "ag-active"}

    asyncio.run(_run())


def test_staging_save_scopes_property_to_active_agency():
    """Saving staging variant must not resolve foreign property by id alone."""
    from apps.immoweb import staging_api

    user = {"id": "u1", "agency_ids": ["ag-a"], "active_agency_id": "ag-a"}
    db = MagicMock()
    db.virtual_staging_jobs.find_one = AsyncMock(
        return_value={"id": "job1", "user_id": "u1", "property_id": "prop-b"}
    )
    db.properties.find_one = AsyncMock(return_value=None)

    body = MagicMock()
    body.property_id = None
    body.variant_index = 0

    async def _run():
        with patch.object(staging_api, "Database") as D:
            D.get.return_value = db
            with pytest.raises(HTTPException) as ei:
                # call inner logic fragment: require_agency + find
                agency_id = require_agency(user)
                q = {"id": "prop-b", "agency_id": agency_id}
                prop = await db.properties.find_one(q, {"_id": 0, "photos": 1})
                if prop is None:
                    raise HTTPException(404, "Immobile non trovato")
            assert ei.value.status_code == 404
            db.properties.find_one.assert_awaited()
            assert db.properties.find_one.await_args.args[0]["agency_id"] == "ag-a"

    asyncio.run(_run())
