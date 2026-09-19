"""D-085 storage quota: usage meter + block upload when full."""
import os
import uuid

import pytest
import requests

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:43121").rstrip("/")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")


@pytest.fixture(scope="module")
def session():
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        pytest.skip("ADMIN_EMAIL/PASSWORD not set")
    s = requests.Session()
    r = s.post(f"{BASE}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    return s


def test_storage_usage_shape(session):
    r = session.get(f"{BASE}/api/app/storage/usage", timeout=30)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "quota_gb" in d and "used_bytes" in d and "full" in d
    assert "addon" in d and d["addon"]["gb"] == 100
    assert d["addon"]["price_eur_monthly"] == 15


def test_plans_expose_storage_addons(session):
    r = session.get(f"{BASE}/api/billing/plans", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert d.get("storage_included_gb", {}).get("pro") == 100
    assert any(a.get("key") == "storage_100gb" for a in d.get("storage_addons") or [])


def test_quota_blocks_when_full(session):
    """Force tiny quota via storage_extra_gb trick: set included via free + zero room."""
    # Use grant then shrink by setting storage_extra_gb negative? not allowed.
    # Instead: set agency storage_extra_gb so total is tiny using direct mongo via grant
    # and inflate used — easier: monkey via grant-extra then... 
    # Super_admin: set storage_extra_gb to -included by updating agency to force full.
    from pymongo import MongoClient
    mongo = MongoClient(os.environ["MONGO_URL"])[os.environ.get("DB_NAME", "omnia")]
    # find admin's agency
    me = session.get(f"{BASE}/api/auth/me", timeout=30)
    if me.status_code != 200:
        me = session.get(f"{BASE}/api/app/agencies/me", timeout=30)
    # get usage for agency id
    usage = session.get(f"{BASE}/api/app/storage/usage", timeout=30).json()
    aid = usage["agency_id"]
    prev = mongo.agencies.find_one({"id": aid}, {"storage_extra_gb": 1, "plan": 1})
    # Force quota = 0 GB effectively: set a flag by using FREE and negative not allowed.
    # Set storage_extra_gb such that included+extra = 0 — set plan free and extra 0,
    # then if used > 0 already full; else upload after setting quota bytes to 1 via hack:
    # store temporary field by setting storage_extra_gb = -included won't work.
    # Practical test: set extra so quota_gb becomes 0 by patching included path —
    # use Mongo to set storage_extra_gb = -30 and tier starter... quota clamps extra to >=0.
    # So: set used artificially by inserting a fake property with huge size_bytes.
    fake_id = f"quota-test-{uuid.uuid4().hex[:8]}"
    mongo.properties.insert_one({
        "id": fake_id,
        "agency_id": aid,
        "title": "Quota filler",
        "property_type": "appartamento",
        "operation": "sale",
        "status": "draft",
        "city": "Roma",
        "photos": [{"id": "x", "url": "/x", "size_bytes": 10 * 1024 ** 3}],  # 10 GB
        "videos": [],
        "floor_plans": [],
        "documents": [],
        "created_at": "2026-09-19T00:00:00+00:00",
        "updated_at": "2026-09-19T00:00:00+00:00",
    })
    try:
        # Shrink quota: free (5GB) + 0 extra — 10GB fake exceeds
        mongo.agencies.update_one({"id": aid}, {"$set": {"plan": "free", "storage_extra_gb": 0}})
        mongo.subscriptions.delete_many({"agency_id": aid})
        usage2 = session.get(f"{BASE}/api/app/storage/usage", timeout=30).json()
        assert usage2["full"] is True or usage2["used_bytes"] > usage2["quota_bytes"]
        # tmp photo upload should 413
        files = {"file": ("t.jpg", b"\xff\xd8\xff" + b"0" * 1000, "image/jpeg")}
        up = session.post(f"{BASE}/api/app/properties/photos/upload-tmp", files=files, timeout=30)
        assert up.status_code == 413, up.text
        detail = up.json().get("detail") or {}
        if isinstance(detail, dict):
            assert detail.get("error") == "storage_quota_exceeded"
    finally:
        mongo.properties.delete_one({"id": fake_id})
        if prev:
            mongo.agencies.update_one(
                {"id": aid},
                {"$set": {"storage_extra_gb": prev.get("storage_extra_gb") or 0, "plan": prev.get("plan") or "free"}},
            )
