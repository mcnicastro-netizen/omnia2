"""MLS Network v1 — public search smoke (seed is a separate ops script)."""
import os
import pytest
from httpx import AsyncClient, ASGITransport

os.environ.setdefault("MONGO_URL", "mongodb://127.0.0.1:27017")
os.environ.setdefault("DB_NAME", "omnia")
os.environ.setdefault("JWT_SECRET", "test-secret-mls-v1-not-for-prod")
os.environ.setdefault("STORAGE_BACKEND", "local")
os.environ.setdefault("CORS_ORIGINS", "*")

from server import app  # noqa: E402


@pytest.mark.anyio
async def test_public_mls_search_ok():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/app/mls/search/public", params={"province": "CT", "limit": 5})
        assert r.status_code == 200
        data = r.json()
        assert "total" in data
        assert "items" in data
        assert "claim" in data
        assert isinstance(data["items"], list)


@pytest.mark.anyio
async def test_public_mls_search_pagination():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/app/mls/search/public", params={"limit": 2, "skip": 0})
        assert r.status_code == 200
        body = r.json()
        assert body["limit"] == 2
        assert len(body["items"]) <= 2
