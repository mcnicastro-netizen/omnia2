"""Unit: orphan Object Storage GC (D-102 / Onda 7)."""
from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from apps.immoweb.orphan_gc import (
    collect_referenced_blob_paths,
    find_orphan_keys,
    run_orphan_gc,
)
from shared.storage.objstore import list_object_keys, put_object


def test_list_object_keys_local(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", str(tmp_path))
    put_object("omnia/properties/p1/a.jpg", b"aaa", "image/jpeg")
    put_object("omnia/videos/v1.mp4", b"bbb", "video/mp4")
    keys = dict(list_object_keys("omnia/"))
    assert "omnia/properties/p1/a.jpg" in keys
    assert "omnia/videos/v1.mp4" in keys


def test_find_orphan_keys_respects_refs_and_grace():
    now = 1_700_000_000.0
    keys = [
        ("omnia/keep.jpg", now - 100_000),
        ("omnia/orphan_old.jpg", now - 100_000),
        ("omnia/orphan_fresh.jpg", now - 60),  # too young
    ]
    orphans = find_orphan_keys(
        referenced={"omnia/keep.jpg"},
        keys=keys,
        min_age_hours=24,
        now=now,
    )
    assert orphans == ["omnia/orphan_old.jpg"]


def test_collect_referenced_includes_props_modulistica_videos_staging():
    db = MagicMock()

    async def _prop_iter():
        yield {
            "photos": [{"url": "/api/media/omnia/properties/p1/a.jpg"}],
            "videos": [],
            "floor_plans": [],
            "documents": [{"storage_path": "omnia/fascicolo/p1/d1"}],
            "floor_plan_url": "/api/media/omnia/properties/p1/fp.png",
        }

    async def _mod_iter():
        yield {"storage_path": "omnia/modulistica/ag1/x.pdf"}

    async def _vid_iter():
        yield {"id": "vid1", "storage_path": "omnia/videos/vid1.mp4"}

    async def _job_iter():
        yield {
            "variants": [{"url": "/api/media/omnia/private/u1/staging-preview/j-0.jpg"}]
        }

    db.properties.find = MagicMock(return_value=_prop_iter())
    db.modulistica_documents.find = MagicMock(return_value=_mod_iter())
    db.videos.find = MagicMock(return_value=_vid_iter())
    db.virtual_staging_jobs.find = MagicMock(return_value=_job_iter())

    async def _run():
        with patch("apps.immoweb.orphan_gc.Database.get", return_value=db):
            refs = await collect_referenced_blob_paths(db)
            assert "omnia/properties/p1/a.jpg" in refs
            assert "omnia/fascicolo/p1/d1" in refs
            assert "omnia/properties/p1/fp.png" in refs
            assert "omnia/modulistica/ag1/x.pdf" in refs
            assert "omnia/videos/vid1.mp4" in refs
            assert "omnia/private/u1/staging-preview/j-0.jpg" in refs

    asyncio.run(_run())


def test_run_orphan_gc_dry_run_does_not_delete(tmp_path: Path):
    now = time.time()
    old = now - 100_000
    keys = [
        ("omnia/keep.jpg", old),
        ("omnia/orphan.jpg", old),
    ]

    db = MagicMock()

    async def _empty():
        if False:  # pragma: no cover
            yield {}

    db.properties.find = MagicMock(return_value=_empty())
    db.modulistica_documents.find = MagicMock(return_value=_empty())
    db.videos.find = MagicMock(return_value=_empty())
    db.virtual_staging_jobs.find = MagicMock(return_value=_empty())

    async def _run():
        with patch("apps.immoweb.orphan_gc.Database.get", return_value=db), patch(
            "apps.immoweb.orphan_gc.list_object_keys", return_value=keys
        ), patch(
            "apps.immoweb.orphan_gc.collect_referenced_blob_paths",
            new=AsyncMock(return_value={"omnia/keep.jpg"}),
        ), patch("apps.immoweb.orphan_gc.delete_object") as dig:
            out = await run_orphan_gc(dry_run=True, min_age_hours=1)
            assert out["orphans_found"] == 1
            assert out["orphans_deleted"] == 0
            assert out["dry_run"] is True
            dig.assert_not_called()

    asyncio.run(_run())


def test_run_orphan_gc_deletes_with_cap():
    now = time.time()
    old = now - 100_000
    keys = [(f"omnia/orphan_{i}.jpg", old) for i in range(5)]

    async def _run():
        with patch("apps.immoweb.orphan_gc.Database.get", return_value=MagicMock()), patch(
            "apps.immoweb.orphan_gc.list_object_keys", return_value=keys
        ), patch(
            "apps.immoweb.orphan_gc.collect_referenced_blob_paths",
            new=AsyncMock(return_value=set()),
        ), patch("apps.immoweb.orphan_gc.delete_object") as dig:
            out = await run_orphan_gc(dry_run=False, max_delete=2, min_age_hours=1)
            assert out["orphans_found"] == 5
            assert out["orphans_deleted"] == 2
            assert dig.call_count == 2

    asyncio.run(_run())


def test_env_dry_run_kill_switch(monkeypatch):
    monkeypatch.setenv("ORPHAN_GC_DRY_RUN", "1")
    now = time.time()
    keys = [("omnia/orphan.jpg", now - 100_000)]

    async def _run():
        with patch("apps.immoweb.orphan_gc.Database.get", return_value=MagicMock()), patch(
            "apps.immoweb.orphan_gc.list_object_keys", return_value=keys
        ), patch(
            "apps.immoweb.orphan_gc.collect_referenced_blob_paths",
            new=AsyncMock(return_value=set()),
        ), patch("apps.immoweb.orphan_gc.delete_object") as dig:
            out = await run_orphan_gc(min_age_hours=1)  # dry_run=None → env
            assert out["dry_run"] is True
            dig.assert_not_called()

    asyncio.run(_run())
    monkeypatch.delenv("ORPHAN_GC_DRY_RUN", raising=False)
