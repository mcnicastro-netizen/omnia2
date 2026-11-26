"""D02 residuo — cache foto + revoca pubblicazione (no reuse senza nuova ACL)."""
from __future__ import annotations

import base64
import inspect
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from apps.immoweb import site as site_mod


TINY_JPEG = base64.b64decode(
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a"
    "HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy"
    "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIA"
    "AhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEB"
    "AQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k="
)
PHOTO = {"url": "data:image/jpeg;base64," + base64.b64encode(TINY_JPEG).decode(), "is_cover": True}


def _assert_no_store(resp):
    cc = (resp.headers.get("cache-control") or "").lower()
    assert "no-store" in cc, cc
    assert "private" in cc, cc
    # Nessuna finestra di freschezza condivisa
    assert "public" not in cc
    if "max-age=" in cc:
        assert "max-age=0" in cc


@pytest.mark.asyncio
async def test_photo_authorized_portal_returns_body_and_no_store():
    db = MagicMock()
    db.properties.find_one = AsyncMock(return_value={"id": "p1", "photos": [PHOTO]})
    with patch.object(site_mod.Database, "get", return_value=db):
        resp = await site_mod.serve_property_photo("p1", 0, surface="portal")
    assert resp.status_code == 200
    assert len(resp.body) > 10
    _assert_no_store(resp)


@pytest.mark.asyncio
async def test_photo_private_not_found():
    db = MagicMock()
    db.properties.find_one = AsyncMock(return_value=None)  # filtro ACL non matcha
    with patch.object(site_mod.Database, "get", return_value=db):
        with pytest.raises(HTTPException) as ei:
            await site_mod.serve_property_photo("p-priv", 0, surface="portal")
    assert ei.value.status_code == 404


@pytest.mark.asyncio
async def test_photo_pending_moderation_not_found():
    db = MagicMock()
    db.properties.find_one = AsyncMock(return_value=None)
    with patch.object(site_mod.Database, "get", return_value=db):
        with pytest.raises(HTTPException) as ei:
            await site_mod.serve_property_photo("p-pend", 0, surface="portal")
    assert ei.value.status_code == 404


@pytest.mark.asyncio
async def test_photo_withdrawn_or_trashed_not_found():
    db = MagicMock()
    db.properties.find_one = AsyncMock(return_value=None)
    with patch.object(site_mod.Database, "get", return_value=db):
        with pytest.raises(HTTPException) as ei:
            await site_mod.serve_property_photo("p-gone", 0, surface="portal")
    assert ei.value.status_code == 404


@pytest.mark.asyncio
async def test_photo_revocation_after_prior_authorized_fetch():
    """Simula: prima 200, poi ACL fallisce (ritiro) → 404. Nessun riuso del body precedente via API."""
    db = MagicMock()
    db.properties.find_one = AsyncMock(
        side_effect=[
            {"id": "p1", "photos": [PHOTO]},
            None,  # dopo revoca il filtro non restituisce più il documento
        ]
    )
    with patch.object(site_mod.Database, "get", return_value=db):
        ok = await site_mod.serve_property_photo("p1", 0, surface="portal")
        assert ok.status_code == 200
        _assert_no_store(ok)
        with pytest.raises(HTTPException) as ei:
            await site_mod.serve_property_photo("p1", 0, surface="portal")
    assert ei.value.status_code == 404


@pytest.mark.asyncio
async def test_photo_cache_headers_brand_surface():
    db = MagicMock()
    db.agencies.find_one = AsyncMock(return_value={"id": "agA"})
    db.properties.find_one = AsyncMock(return_value={"id": "p1", "photos": [PHOTO]})
    with patch.object(site_mod.Database, "get", return_value=db):
        resp = await site_mod.serve_property_photo(
            "p1", 0, surface="brand", agency_slug="slug-a"
        )
    assert resp.status_code == 200
    _assert_no_store(resp)


@pytest.mark.asyncio
async def test_photo_cache_headers_mls_network_surface():
    db = MagicMock()
    db.properties.find_one = AsyncMock(return_value={"id": "p1", "photos": [PHOTO]})
    with patch.object(site_mod.Database, "get", return_value=db):
        resp = await site_mod.serve_property_photo("p1", 0, surface="mls_network")
    assert resp.status_code == 200
    _assert_no_store(resp)


@pytest.mark.asyncio
async def test_photo_brand_cross_agency_isolation():
    db = MagicMock()
    db.agencies.find_one = AsyncMock(return_value={"id": "agB"})
    db.properties.find_one = AsyncMock(return_value=None)  # brand_photo_filter no match
    with patch.object(site_mod.Database, "get", return_value=db):
        with pytest.raises(HTTPException) as ei:
            await site_mod.serve_property_photo(
                "p-of-A", 0, surface="brand", agency_slug="slug-b"
            )
    assert ei.value.status_code == 404


def test_photo_cache_constant_is_no_store():
    assert site_mod._PHOTO_CACHE_HEADERS["Cache-Control"] == "private, no-store"
    src = inspect.getsource(site_mod.serve_property_photo)
    assert "_PHOTO_CACHE_HEADERS" in src
    assert "max-age=60" not in inspect.getsource(site_mod)
    assert "must-revalidate" not in site_mod._PHOTO_CACHE_HEADERS["Cache-Control"]


@pytest.mark.asyncio
async def test_photo_external_redirect_carries_no_store():
    db = MagicMock()
    db.properties.find_one = AsyncMock(
        return_value={"id": "p1", "photos": [{"url": "https://cdn.example/x.jpg"}]}
    )
    with patch.object(site_mod.Database, "get", return_value=db):
        resp = await site_mod.serve_property_photo("p1", 0, surface="portal")
    assert resp.status_code in (302, 307)
    _assert_no_store(resp)
