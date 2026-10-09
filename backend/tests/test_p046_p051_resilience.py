"""P-046/047/049/050/051/033/048 — resilienza portale (D-118 vai)."""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def test_p046_backup_collections_include_b2c():
    from apps.immoweb.backup_job import _COLLECTIONS

    for name in (
        "b2c_purchases",
        "b2c_visura_orders",
        "consent_events",
        "favorites",
        "saved_searches",
        "al_legal_audit",
        "listing_inquiries",
    ):
        assert name in _COLLECTIONS, name


def test_p047_restore_manual_mentions_b2c():
    text = Path("/workspace/docs/ops/RESTORE_MANUAL.md").read_text(encoding="utf-8")
    assert "b2c_purchases" in text
    assert "consent_events" in text
    assert "P-046" in text or "P-047" in text


def test_p051_sync_public_base_sets_cookie_secure(tmp_path, monkeypatch):
    import importlib.util
    import sys

    env = tmp_path / ".env"
    env.write_text("COOKIE_SECURE=false\nFRONTEND_URL=http://localhost:43122\n", encoding="utf-8")
    path = Path("/workspace/scripts/sync-public-base-url.py")
    spec = importlib.util.spec_from_file_location("sync_public_base_url", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    monkeypatch.setattr(sys, "argv", [
        "sync-public-base-url.py",
        "--url", "https://example-tunnel.trycloudflare.com",
        "--env", str(env),
    ])
    assert mod.main() == 0
    body = env.read_text(encoding="utf-8")
    assert "COOKIE_SECURE=true" in body
    assert os.environ.get("COOKIE_SECURE") == "true"


def test_p033_base_filter_excludes_l3_l4():
    from apps.immocloud.public_portal import _base_filter

    flt = _base_filter()
    # with_not_trashed wraps in $and
    and_parts = flt.get("$and") or [flt]
    privacy = None
    for part in and_parts:
        if isinstance(part, dict) and "privacy_level" in part:
            privacy = part["privacy_level"]
    assert privacy == {"$nin": ["L3", "L4"]}


def test_p048_soft_delete_private_listing():
    import asyncio
    from apps.immocloud import private_listings as pl

    user = {"id": "u1", "account_type": "b2c", "role": "client"}
    db = MagicMock()
    db.properties.update_one = AsyncMock(return_value=MagicMock(matched_count=1))

    async def _run():
        with patch.object(pl, "_ensure_b2c", new=AsyncMock()), \
             patch("shared.db.connection.Database.get", return_value=db):
            return await pl.delete_my_private_listing("prop-1", user)

    out = asyncio.run(_run())
    assert out is None
    db.properties.update_one.assert_awaited_once()
    args, _kwargs = db.properties.update_one.await_args
    assert args[1]["$set"]["deleted_at"]
    assert args[1]["$set"]["status"] == "withdrawn"


def test_p049_b2c_status_stripe_fallback():
    import asyncio
    from apps.billing import b2c_checkout as bc

    user = {"id": "u1"}
    pending = {
        "stripe_session_id": "cs_test_1",
        "user_id": "u1",
        "status": "pending",
        "product_key": "b2c_hal_legal_query",
    }
    paid = {**pending, "status": "paid", "paid_at": "2026-10-09T00:00:00+00:00"}

    db = MagicMock()
    db.b2c_purchases.find_one = AsyncMock(side_effect=[pending, paid])

    class FakeSession:
        def to_dict(self):
            return {
                "id": "cs_test_1",
                "payment_status": "paid",
                "status": "complete",
                "amount_total": 100,
                "metadata": {"b2c_product_key": "b2c_hal_legal_query", "user_id": "u1"},
            }

    async def _run():
        with patch("shared.db.connection.Database.get", return_value=db), \
             patch.object(bc.stripe.checkout.Session, "retrieve", return_value=FakeSession()), \
             patch.object(bc, "apply_b2c_purchase_side_effects", new=AsyncMock()) as apply:
            out = await bc.b2c_status("cs_test_1", user)
            apply.assert_awaited_once()
            return out

    out = asyncio.run(_run())
    assert out["status"] == "paid"
