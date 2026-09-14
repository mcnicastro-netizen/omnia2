"""M5.S4.2 — ONE live FAL generation + downstream endpoints.

Spends ~$0.11 on fal.ai (num_variants=2, same_style, standard mode).
Guarded by RUN_STAGING_LIVE=1.
"""
import base64
import io
import os
import time
import uuid

import pytest
import requests
from PIL import Image

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def live_job(admin_session):
    """ONE live generation reused across downstream tests."""
    if os.environ.get("RUN_STAGING_LIVE") != "1":
        pytest.skip("RUN_STAGING_LIVE=1 required (spends FAL money)")

    # Use a real interior room photo from Unsplash for better SAM2 segmentation
    src = "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1200"
    try:
        img_bytes = requests.get(src, timeout=30).content
    except Exception:
        img = Image.new("RGB", (1024, 768), (220, 210, 200))
        b = io.BytesIO(); img.save(b, format="JPEG"); img_bytes = b.getvalue()

    up = admin_session.post(
        f"{API}/app/staging/upload",
        files={"file": ("room.jpg", img_bytes, "image/jpeg")},
        timeout=90,
    )
    assert up.status_code == 200, up.text
    image_url = up.json()["url"]
    assert image_url.startswith("http")

    r = admin_session.post(f"{API}/app/staging/generate", json={
        "image_url": image_url,
        "style": "modern",
        "room_type": "living",
        "mode": "standard",
        "num_variants": 2,
        "variant_mode": "same_style",
    }, timeout=30)
    assert r.status_code == 200, r.text
    job = r.json()
    job_id = job["id"]
    assert job["status"] in ("pending", "running")
    assert job["num_variants"] == 2

    # Poll up to 5 min
    final = None
    for _ in range(60):
        time.sleep(5)
        j = admin_session.get(f"{API}/app/staging/jobs/{job_id}", timeout=15).json()
        if j["status"] in ("done", "failed"):
            final = j
            break
    assert final is not None, "Timeout waiting for job"
    assert final["status"] == "done", f"Job failed: {final.get('error')} stages={final.get('stages')}"
    return final


def test_live_job_done_with_2_variants(live_job):
    assert live_job["status"] == "done"
    assert len(live_job["variants"]) == 2
    for v in live_job["variants"]:
        assert v["url"].startswith("http")
        assert v["style"] == "modern"
    assert all(s["status"] == "done" for s in live_job["stages"])
    # 1 sam2 + 2 flux + up to 2 upscales ≈ 0.111
    assert live_job["cost_total_usd"] is not None
    assert 0.05 < live_job["cost_total_usd"] < 0.20


def test_download_watermarked_jpeg(admin_session, live_job):
    r = admin_session.get(
        f"{API}/app/staging/jobs/{live_job['id']}/download",
        params={"variant": 1}, timeout=60,
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/jpeg"
    assert r.content[:3] == b"\xff\xd8\xff"  # JPEG SOI
    assert len(r.content) > 5000


def test_dataurl_variant0(admin_session, live_job):
    r = admin_session.get(
        f"{API}/app/staging/jobs/{live_job['id']}/variants/0/dataurl", timeout=60,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["data_url"].startswith("data:image/jpeg;base64,")
    assert "Render virtuale OMNIA" in data["caption"]
    # Decode & verify JPEG
    b64 = data["data_url"].split(",", 1)[1]
    raw = base64.b64decode(b64)
    assert raw[:3] == b"\xff\xd8\xff"


def test_save_variant_to_property_full_lifecycle(admin_session):
    # 0) Reuse latest DONE live job from history (no extra FAL cost)
    h = admin_session.get(f"{API}/app/staging/history", timeout=15)
    assert h.status_code == 200
    done_jobs = [j for j in h.json()["items"] if j["status"] == "done" and j.get("variants")]
    if not done_jobs:
        pytest.skip("No done staging job available in history")
    job = done_jobs[0]

    # 1) Create test property
    payload = {
        "title": f"TEST Staging Prop {uuid.uuid4().hex[:6]}",
        "operation": "sale",
        "property_type": "appartamento",
        "city": "Catania",
        "price": 250000,
    }
    c = admin_session.post(f"{API}/app/properties", json=payload, timeout=20)
    assert c.status_code in (200, 201), c.text
    prop_id = c.json().get("id") or c.json().get("_id") or c.json().get("property", {}).get("id")
    assert prop_id, c.json()

    try:
        # 2) Save variant 0
        s = admin_session.post(
            f"{API}/app/staging/jobs/{job['id']}/save-to-property",
            json={"variant_index": 0, "property_id": prop_id},
            timeout=60,
        )
        assert s.status_code == 200, s.text
        assert s.json().get("ok") is True

        # 3) GET property → assert photo present
        g = admin_session.get(f"{API}/app/properties/{prop_id}", timeout=15)
        assert g.status_code == 200
        prop = g.json()
        photos = prop.get("photos") or []
        assert len(photos) >= 1
        p0 = photos[0]
        assert p0["url"].startswith("data:image/jpeg;base64,")
        assert "Render virtuale OMNIA" in p0["caption"]
    finally:
        # 4) Cleanup
        admin_session.delete(f"{API}/app/properties/{prop_id}", timeout=15)
