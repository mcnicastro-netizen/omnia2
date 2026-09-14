"""MLS Network v1 — smoke against running API (evita Motor event-loop cross-test)."""
import os
import httpx

BASE = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:43121").rstrip("/")


def test_public_mls_search_ok():
    r = httpx.get(f"{BASE}/api/app/mls/search/public", params={"province": "CT", "limit": 5}, timeout=30)
    assert r.status_code == 200
    data = r.json()
    assert "total" in data and "items" in data and "claim" in data
    assert data["total"] >= 1


def test_public_mls_search_pagination():
    r = httpx.get(f"{BASE}/api/app/mls/search/public", params={"limit": 2, "skip": 0}, timeout=30)
    assert r.status_code == 200
    body = r.json()
    assert body["limit"] == 2
    assert len(body["items"]) <= 2
