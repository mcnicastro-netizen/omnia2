"""Unit: GDPR erase_user_data (D-099 / Onda 9)."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from shared.privacy.erasure import erase_user_data


def test_erase_anonymizes_user_and_clears_satellites():
    db = MagicMock()
    deleted = MagicMock(deleted_count=2)
    modified = MagicMock(modified_count=1)

    def _coll(_name: str):
        c = MagicMock()
        c.delete_many = AsyncMock(return_value=deleted)
        c.update_many = AsyncMock(return_value=modified)
        c.update_one = AsyncMock()
        return c

    db.__getitem__.side_effect = _coll
    db.favorites = _coll("favorites")
    db.saved_searches = _coll("saved_searches")
    db.notifications = _coll("notifications")
    db.password_reset_tokens = _coll("password_reset_tokens")
    db.refresh_tokens = _coll("refresh_tokens")
    db.mortgage_leads = _coll("mortgage_leads")
    db.visura_orders = _coll("visura_orders")
    db.cloud_contact_leads = _coll("cloud_contact_leads")
    db.contact_leads = _coll("contact_leads")
    db.properties = _coll("properties")
    db.api_keys = _coll("api_keys")
    db.users = _coll("users")

    user = {"id": "u-erase-1", "email": "person@example.com", "name": "Person"}

    async def _run():
        with patch("shared.privacy.erasure.Database.get", return_value=db):
            report = await erase_user_data(user)
            assert report["status"] == "erased"
            assert report["deleted"]["favorites"] == 2
            db.users.update_one.assert_awaited_once()
            args, kwargs = db.users.update_one.await_args
            assert args[0] == {"id": "u-erase-1"}
            set_doc = args[1]["$set"]
            assert set_doc["is_active"] is False
            assert set_doc["email"].endswith("@erased.omnia.local")
            assert set_doc["name"] == "Utente eliminato"
            assert set_doc["password_hash"].startswith("!erased:")

    asyncio.run(_run())
