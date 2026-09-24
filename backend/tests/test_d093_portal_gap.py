"""D-093 / A-029–A-030 — private listing stats + favorite ended alerts."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from apps.immocloud.listing_stats import bump_daily_stat, get_listing_stats
from apps.immocloud.favorite_watch import (
    TERMINAL_STATUSES,
    record_listing_ended,
)


def test_bump_and_get_listing_stats():
    async def _run():
        db = MagicMock()
        db.property_stat_days = MagicMock()
        db.property_stat_days.update_one = AsyncMock()

        today = datetime.now(timezone.utc).date().isoformat()
        yday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()

        class _C:
            async def __aiter__(self):
                yield {"day": today, "views": 3, "leads": 1}
                yield {"day": yday, "views": 2, "leads": 0}

        db.property_stat_days.find = MagicMock(return_value=_C())

        await bump_daily_stat(db, "prop-1", "view")
        db.property_stat_days.update_one.assert_awaited()
        call = db.property_stat_days.update_one.await_args
        assert call.args[0]["property_id"] == "prop-1"
        assert call.args[0]["day"] == today
        assert call.args[1]["$inc"]["views"] == 1

        stats = await get_listing_stats(
            db, "prop-1", days=7, lifetime_views=10, lifetime_leads=2,
        )
        assert stats["lifetime"]["views"] == 10
        assert stats["lifetime"]["leads"] == 2
        assert stats["period"]["views"] == 5
        assert stats["period"]["leads"] == 1
        assert stats["period"]["contact_rate"] == 20.0
        assert len(stats["series"]) == 7

    asyncio.run(_run())


def test_record_listing_ended_notifies():
    async def _run():
        db = MagicMock()
        db.properties = MagicMock()
        db.properties.update_one = AsyncMock()
        existing = {"id": "p1", "status": "active", "title": "Casa"}

        with patch(
            "apps.immocloud.favorite_watch.notify_favoriters_listing_ended",
            new_callable=AsyncMock,
            return_value={"notified": 1},
        ) as notify:
            for st in TERMINAL_STATUSES:
                db.properties.update_one.reset_mock()
                notify.reset_mock()
                out = await record_listing_ended(
                    db, property_id="p1", existing=existing, new_status=st,
                )
                assert out is not None
                assert out["listing_end_status"] == st
                notify.assert_awaited_once()

            out2 = await record_listing_ended(
                db, property_id="p1", existing={"status": "sold"}, new_status="sold",
            )
            assert out2 is None

            out3 = await record_listing_ended(
                db, property_id="p1", existing={"status": "active"}, new_status="draft",
            )
            assert out3 is None

    asyncio.run(_run())
