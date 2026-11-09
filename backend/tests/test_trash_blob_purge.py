"""Unit: trash hard-delete purges Object Storage blobs (D-095 T-02)."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from apps.immoweb.trash import (
    collect_property_blob_paths,
    purge_property_blobs,
    run_trash_purge,
)


def test_collect_paths_from_photos_videos_documents():
    prop = {
        "id": "p1",
        "photos": [
            {"url": "/api/media/omnia/properties/p1/a.jpg"},
            {"storage_path": "omnia/properties/p1/b.jpg", "url": "/api/media/omnia/properties/p1/b.jpg"},
        ],
        "videos": [{"url": "/api/media/omnia/properties/p1/videos/v1.mp4"}],
        "documents": [{"id": "d1", "storage_path": "omnia/fascicolo/p1/d1"}],
        "floor_plans": [{"url": "https://cdn.example/x.png"}],  # external — skip
    }
    paths = collect_property_blob_paths(prop)
    assert "omnia/properties/p1/a.jpg" in paths
    assert "omnia/properties/p1/b.jpg" in paths
    assert paths.count("omnia/properties/p1/b.jpg") == 1  # dedupe
    assert "omnia/properties/p1/videos/v1.mp4" in paths
    assert "omnia/fascicolo/p1/d1" in paths
    assert not any("cdn.example" in p for p in paths)


def test_purge_property_blobs_calls_delete_object():
    prop = {
        "id": "p1",
        "photos": [{"url": "/api/media/omnia/properties/p1/a.jpg"}],
        "documents": [{"storage_path": "omnia/fascicolo/p1/d1"}],
    }
    with patch("apps.immoweb.trash.delete_object") as dig:
        n = purge_property_blobs(prop)
        assert n == 2
        assert dig.call_count == 2


def test_purge_property_blobs_continues_on_error():
    prop = {
        "id": "p1",
        "photos": [
            {"url": "/api/media/omnia/properties/p1/a.jpg"},
            {"url": "/api/media/omnia/properties/p1/b.jpg"},
        ],
    }
    with patch("apps.immoweb.trash.delete_object", side_effect=[RuntimeError("boom"), None]) as dig:
        n = purge_property_blobs(prop)
        assert dig.call_count == 2
        assert n == 1  # second succeeded


def test_run_trash_purge_finds_then_deletes_with_blob_count():
    prop = {
        "id": "p1",
        "photos": [{"url": "/api/media/omnia/properties/p1/a.jpg"}],
        "documents": [],
        "videos": [],
        "floor_plans": [],
    }
    db = MagicMock()
    cursor = MagicMock()
    cursor.to_list = AsyncMock(return_value=[prop])
    db.properties.find = MagicMock(return_value=cursor)
    db.properties.delete_many = AsyncMock(return_value=MagicMock(deleted_count=1))
    db.clients.delete_many = AsyncMock(return_value=MagicMock(deleted_count=0))

    async def _run():
        with patch("apps.immoweb.trash.Database.get", return_value=db), \
             patch("apps.immoweb.trash.delete_object") as dig:
            out = await run_trash_purge()
            assert out["purged_properties"] == 1
            assert out["blobs_purged"] == 1
            dig.assert_called_once_with("omnia/properties/p1/a.jpg")
            # find before delete_many
            db.properties.find.assert_called_once()
            db.properties.delete_many.assert_awaited_once()

    asyncio.run(_run())
