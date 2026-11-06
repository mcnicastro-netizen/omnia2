"""D-139 — Portal news box: RSS parse, merge, API."""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest
import requests

from apps.immocloud.portal_news import (
    FEEDS,
    merge_items,
    news_enabled,
    parse_feed_xml,
)

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>Test</title>
  <item>
    <title>Prezzi case in salita a Milano</title>
    <link>https://example.com/a</link>
    <pubDate>Mon, 03 Nov 2026 10:00:00 GMT</pubDate>
    <description>Mercato residenziale</description>
  </item>
  <item>
    <title>Mutui: tassi fermi</title>
    <link>https://example.com/b</link>
    <pubDate>Tue, 04 Nov 2026 10:00:00 GMT</pubDate>
  </item>
</channel></rss>
"""


def test_parse_feed_xml_rss():
    meta = {"id": "t", "source": "Test Source", "category": "immobiliare", "url": "x"}
    items = parse_feed_xml(SAMPLE_RSS, meta)
    assert len(items) == 2
    assert items[0]["title"].startswith("Prezzi")
    assert items[0]["url"] == "https://example.com/a"
    assert items[0]["category"] == "immobiliare"
    assert items[0]["published_at"]


def test_merge_items_round_robin_and_limit():
    a = [{"url": f"https://a/{i}", "title": f"A{i}", "published_at": f"2026-11-0{i+1}T00:00:00+00:00"} for i in range(3)]
    b = [{"url": f"https://b/{i}", "title": f"B{i}", "published_at": f"2026-11-1{i}T00:00:00+00:00"} for i in range(3)]
    out = merge_items([a, b], limit=4)
    assert len(out) == 4
    urls = {x["url"] for x in out}
    assert len(urls) == 4


def test_news_enabled_flag(monkeypatch):
    monkeypatch.setenv("OMNIA_PORTAL_NEWS", "0")
    assert news_enabled() is False
    monkeypatch.setenv("OMNIA_PORTAL_NEWS", "1")
    assert news_enabled() is True


def test_feeds_curated_three_categories():
    cats = {f["category"] for f in FEEDS}
    assert cats == {"immobiliare", "mutui", "arredo"}
    assert len(FEEDS) == 3


def test_get_news_bundle_disabled(monkeypatch):
    import asyncio
    from apps.immocloud import portal_news as pn

    monkeypatch.setenv("OMNIA_PORTAL_NEWS", "false")
    pn._mem_cache = None
    out = asyncio.run(pn.get_news_bundle())
    assert out["enabled"] is False
    assert out["items"] == []


def test_get_news_bundle_from_mock_fetch(monkeypatch):
    import asyncio
    from apps.immocloud import portal_news as pn

    monkeypatch.setenv("OMNIA_PORTAL_NEWS", "1")
    pn._mem_cache = None

    fake = {
        "enabled": True,
        "items": [
            {
                "id": "1",
                "title": "Titolo",
                "url": "https://example.com/x",
                "source": "Casa24",
                "category": "immobiliare",
                "published_at": "2026-11-04T12:00:00+00:00",
            }
        ],
        "cached_at": "2026-11-05T08:00:00+00:00",
        "sources": [],
        "stale": False,
    }

    async def _fake_fresh(limit=8):
        return fake

    with patch.object(pn, "fetch_fresh", side_effect=_fake_fresh), patch.object(
        pn, "_load_mongo_cache", new=AsyncMock(return_value=None)
    ), patch.object(pn, "_save_mongo_cache", new=AsyncMock()):
        out = asyncio.run(pn.get_news_bundle(limit=5))
    assert out["enabled"] is True
    assert len(out["items"]) == 1
    assert out["items"][0]["title"] == "Titolo"


def test_api_news_live():
    if not BASE_URL:
        pytest.skip("no backend")
    r = requests.get(f"{API}/cloud/news", params={"limit": 8}, timeout=30)
    assert r.status_code == 200, r.text[:300]
    d = r.json()
    assert "enabled" in d
    assert "items" in d
    if d["enabled"] and d["items"]:
        it = d["items"][0]
        assert it.get("title")
        assert it.get("url", "").startswith("http")
        assert it.get("category") in {"immobiliare", "mutui", "arredo"}
        assert it.get("source")
