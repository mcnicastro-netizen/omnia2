"""Ken Burns video persistence — Object Storage + expired hydration."""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from apps.immoweb import micro_tour_video as mtv


def test_persist_video_mp4_writes_objstore_and_media_url():
    with tempfile.TemporaryDirectory() as td:
        local = Path(td) / "v.mp4"
        local.write_bytes(b"ftyp" + b"x" * 800)
        with patch("shared.storage.objstore.put_object") as put:
            put.return_value = {"path": "omnia/videos/vid-1.mp4", "size": 804}
            out = mtv._persist_video_mp4("vid-1", local)
        put.assert_called_once()
        args, kwargs = put.call_args
        assert args[0] == "omnia/videos/vid-1.mp4"
        assert args[2] == "video/mp4"
        assert out["storage_path"] == "omnia/videos/vid-1.mp4"
        assert out["download_url"] == "/api/media/omnia/videos/vid-1.mp4"
        assert out["file_path"] == str(local)


def test_video_bytes_available_local_storage():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        storage = root / "omnia" / "videos" / "vid-2.mp4"
        storage.parent.mkdir(parents=True)
        storage.write_bytes(b"x" * 1000)
        with patch("shared.storage.objstore._backend", return_value="local"), patch(
            "shared.storage.objstore._local_root", return_value=root
        ):
            assert mtv._video_bytes_available({"id": "vid-2", "storage_path": "omnia/videos/vid-2.mp4"}) is True
            assert mtv._video_bytes_available({"id": "missing", "storage_path": "omnia/videos/nope.mp4"}) is False


def test_hydrate_ready_video_marks_expired_when_bytes_gone():
    async def _run():
        db = MagicMock()
        db.videos.update_one = AsyncMock()
        doc = {
            "id": "vid-3",
            "status": "ready",
            "file_path": "/tmp/omnia_videos/vid-3.mp4",
            "storage_path": None,
            "download_url": "/api/app/videos/vid-3/download",
        }
        with patch.object(mtv, "_video_bytes_available", return_value=False):
            out = await mtv.hydrate_ready_video(db, doc)
        assert out["status"] == "failed"
        assert out["error"] == "video_expired"
        db.videos.update_one.assert_awaited()

    asyncio.run(_run())


def test_hydrate_ready_video_keeps_ready_when_bytes_present():
    async def _run():
        db = MagicMock()
        db.videos.update_one = AsyncMock()
        doc = {
            "id": "vid-4",
            "status": "ready",
            "storage_path": "omnia/videos/vid-4.mp4",
            "download_url": "/api/media/omnia/videos/vid-4.mp4",
        }
        with patch.object(mtv, "_video_bytes_available", return_value=True):
            out = await mtv.hydrate_ready_video(db, doc)
        assert out["status"] == "ready"
        db.videos.update_one.assert_not_awaited()

    asyncio.run(_run())
