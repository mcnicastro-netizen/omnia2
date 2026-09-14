"""M5.S4.2 — Virtual Staging tests (reverse staging + varianti + CRM-aware + persistenza).

Live API tests (no FAL cost: only validation paths) + unit tests on pure helpers.
Full pipeline E2E is gated behind RUN_STAGING_LIVE=1 (spends ~$0.06 on fal.ai).
"""
import base64
import io
import os
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
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return s


# ─── API: catalog ────────────────────────────────────────────────
def test_styles_endpoint_includes_modes():
    r = requests.get(f"{API}/app/staging/styles", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert {s["key"] for s in data["styles"]} >= {"modern", "classic", "scandi", "industrial", "luxury"}
    assert {m["key"] for m in data["modes"]} == {"standard", "reverse"}
    assert len(data["room_types"]) == 6


# ─── API: validation (no FAL cost) ───────────────────────────────
def test_generate_requires_auth():
    r = requests.post(f"{API}/app/staging/generate", json={"image_url": "https://x/y.jpg"}, timeout=15)
    assert r.status_code in (401, 403)


def test_generate_invalid_style(admin_session):
    r = admin_session.post(f"{API}/app/staging/generate", json={
        "image_url": "https://example.com/room.jpg", "style": "baroque",
    }, timeout=15)
    assert r.status_code == 400


def test_generate_invalid_mode(admin_session):
    r = admin_session.post(f"{API}/app/staging/generate", json={
        "image_url": "https://example.com/room.jpg", "mode": "sideways",
    }, timeout=15)
    assert r.status_code == 400


def test_generate_invalid_variant_mode(admin_session):
    r = admin_session.post(f"{API}/app/staging/generate", json={
        "image_url": "https://example.com/room.jpg", "variant_mode": "random",
    }, timeout=15)
    assert r.status_code == 400


def test_generate_num_variants_bounds(admin_session):
    r = admin_session.post(f"{API}/app/staging/generate", json={
        "image_url": "https://example.com/room.jpg", "num_variants": 9,
    }, timeout=15)
    assert r.status_code == 422  # pydantic ge/le


def test_generate_unknown_property(admin_session):
    r = admin_session.post(f"{API}/app/staging/generate", json={
        "image_url": "https://example.com/room.jpg", "property_id": str(uuid.uuid4()),
    }, timeout=15)
    assert r.status_code == 404


def test_history_shape(admin_session):
    r = admin_session.get(f"{API}/app/staging/history", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and isinstance(data["items"], list)
    for it in data["items"][:3]:
        assert "mode" in it and "variants" in it and "num_variants" in it


def test_save_to_property_unknown_job(admin_session):
    r = admin_session.post(f"{API}/app/staging/jobs/{uuid.uuid4()}/save-to-property", json={"variant_index": 0}, timeout=15)
    assert r.status_code == 404


def test_dataurl_unknown_job(admin_session):
    r = admin_session.get(f"{API}/app/staging/jobs/{uuid.uuid4()}/variants/0/dataurl", timeout=15)
    assert r.status_code == 404


# ─── Unit: pure helpers (direct import) ──────────────────────────
def _import_module():
    from apps.immoweb import virtual_staging as vs
    return vs


def test_build_prompt_with_crm_fragment():
    vs = _import_module()
    p = vs._build_prompt("luxury", "living", "premium seaside penthouse for affluent buyers")
    assert "luxury interior design" in p
    assert "premium seaside penthouse" in p
    assert p.endswith("photorealistic, 8k, architectural photography")


def test_build_prompt_fallbacks():
    vs = _import_module()
    p = vs._build_prompt("nonexistent", "nonexistent")
    assert "modern minimalist" in p and "living room" in p


def test_empty_room_prompt_exists():
    vs = _import_module()
    assert "no furniture" in vs.EMPTY_ROOM_PROMPT


def test_default_multi_styles_valid():
    vs = _import_module()
    assert all(s in vs.STYLES for s in vs.DEFAULT_MULTI_STYLES)
    assert len(vs.DEFAULT_MULTI_STYLES) == 4


def test_watermark_and_resize():
    vs = _import_module()
    img = Image.new("RGB", (3200, 2400), (200, 180, 160))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    out = vs._apply_watermark(buf.getvalue(), max_width=1600)
    result = Image.open(io.BytesIO(out))
    assert result.size[0] == 1600
    assert result.format == "JPEG"


def test_watermark_no_resize_below_max():
    vs = _import_module()
    img = Image.new("RGB", (800, 600), (100, 100, 100))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    out = vs._apply_watermark(buf.getvalue(), max_width=1600)
    assert Image.open(io.BytesIO(out)).size == (800, 600)


def test_photo_caption():
    vs = _import_module()
    cap = vs._photo_caption("scandi", "bedroom")
    assert cap == "Render virtuale OMNIA · Camera da letto Scandinavo"


def test_job_to_out_backward_compat():
    """Old S4.1 docs (no variants/mode fields) must still serialize."""
    vs = _import_module()
    doc = {
        "id": "j1", "status": "done", "source_url": "https://x/y.jpg",
        "style": "modern", "room_type": "living", "stages": [],
        "variant_url": "https://x/out.jpg", "created_at": "2026-07-03T00:00:00Z",
    }
    out = vs._job_to_out(doc)
    assert out.mode == "standard" and out.num_variants == 1
    assert len(out.variants) == 1 and out.variants[0].url == "https://x/out.jpg"


# ─── E2E full pipeline (spends FAL credit — opt-in) ──────────────
@pytest.mark.skipif(os.environ.get("RUN_STAGING_LIVE") != "1", reason="Set RUN_STAGING_LIVE=1 to spend fal.ai credit")
def test_full_pipeline_live(admin_session):
    import time
    img = Image.new("RGB", (1024, 768), (220, 210, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    up = admin_session.post(f"{API}/app/staging/upload", files={"file": ("room.jpg", buf, "image/jpeg")}, timeout=60)
    assert up.status_code == 200
    r = admin_session.post(f"{API}/app/staging/generate", json={
        "image_url": up.json()["url"], "style": "modern", "room_type": "living", "num_variants": 1,
    }, timeout=30)
    assert r.status_code == 200
    job_id = r.json()["id"]
    for _ in range(60):
        time.sleep(5)
        j = admin_session.get(f"{API}/app/staging/jobs/{job_id}", timeout=15).json()
        if j["status"] in ("done", "failed"):
            break
    assert j["status"] == "done", j.get("error")
    assert j["variants"]
