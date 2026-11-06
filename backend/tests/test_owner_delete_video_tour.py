"""B2C owner can soft-delete Ken Burns micro-tour from a listing."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from apps.immoweb.micro_tour_video import soft_delete_owner_ken_burns


def test_soft_delete_owner_ken_burns_marks_deleted_and_purges():
    async def _run():
        pid = uuid4().hex
        vid = uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": vid,
            "property_id": pid,
            "mode": "ken_burns",
            "agency_id": None,
            "status": "ready",
            "file_path": f"/tmp/{vid}.mp4",
            "storage_path": f"omnia/videos/{vid}.mp4",
            "created_at": now,
        }
        db = MagicMock()
        cursor = MagicMock()
        cursor.to_list = AsyncMock(return_value=[doc])
        db.videos.find = MagicMock(return_value=cursor)
        db.videos.update_many = AsyncMock()

        with patch(
            "apps.immoweb.micro_tour_video._best_effort_purge_video_bytes"
        ) as purge:
            out = await soft_delete_owner_ken_burns(db, pid)

        assert out == {"ok": True, "deleted": 1}
        db.videos.update_many.assert_awaited()
        args, kwargs = db.videos.update_many.await_args
        assert args[0]["id"]["$in"] == [vid]
        assert args[1]["$set"]["status"] == "deleted"
        assert args[1]["$set"]["error"] == "owner_deleted"
        purge.assert_called_once_with(doc)

    asyncio.run(_run())


def test_soft_delete_owner_ken_burns_noop_when_empty():
    async def _run():
        db = MagicMock()
        cursor = MagicMock()
        cursor.to_list = AsyncMock(return_value=[])
        db.videos.find = MagicMock(return_value=cursor)
        db.videos.update_many = AsyncMock()
        out = await soft_delete_owner_ken_burns(db, "pid-x")
        assert out == {"ok": True, "deleted": 0}
        db.videos.update_many.assert_not_awaited()

    asyncio.run(_run())
