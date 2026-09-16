"""Unit tests: Scout gaps on thin listings + VAPID bootstrap."""
from __future__ import annotations

import os

from apps.immocloud.buyer_brief import build_brief, completeness_score, seller_gaps
from shared.notifications.web_push import ensure_vapid_keys, is_push_configured, vapid_public_key


def test_seller_gaps_on_thin_listing():
    thin = {
        "id": "thin-1",
        "title": "Appartamento",
        "description": "Breve",
        "city": "Milano",
        "operation": "sale",
        "price": 300000,
        "photos": [],
    }
    comp = completeness_score(thin)
    assert comp["score"] < 70
    assert comp["grade"] in ("C", "D")
    gaps = seller_gaps(comp)
    keys = {g["key"] for g in gaps}
    assert "foto" in keys
    assert "ape" in keys or "descrizione" in keys
    brief = build_brief(thin)
    assert brief["insight"]
    assert brief["seller_gaps"]
    assert brief["product"] == "scout_hal"


def test_vapid_ensure_keys(tmp_path, monkeypatch):
    monkeypatch.delenv("VAPID_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("VAPID_PRIVATE_KEY", raising=False)
    cache = tmp_path / ".vapid_local.json"
    monkeypatch.setattr("shared.notifications.web_push._VAPID_CACHE_FILE", cache)
    out = ensure_vapid_keys()
    assert out.get("configured") is True
    assert is_push_configured()
    assert len(vapid_public_key()) > 20
    # Second call hits cache / env
    out2 = ensure_vapid_keys()
    assert out2.get("configured") is True
    assert cache.exists() or os.environ.get("VAPID_PUBLIC_KEY")
