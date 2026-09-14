"""Backend tests for M5.S4.3 Micro-tour video (Sprint 3 · Item #5).

Ken Burns funzionante (ffmpeg locale), Sora 2 stub in v1.
"""
import asyncio
import os
import time
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://omnia-crm-docs.preview.emergentagent.com",
).rstrip("/")
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def test_property_with_photos(session):
    """Create a test property with 3 external photo URLs (public HTTPS)."""
    # small public JPGs (~10-30KB) that we know exist
    photo_urls = [
        "https://picsum.photos/seed/omnia-a/800/600",
        "https://picsum.photos/seed/omnia-b/800/600",
        "https://picsum.photos/seed/omnia-c/800/600",
    ]
    r = session.post(f"{BASE_URL}/api/app/properties", json={
        "title": "Video Test Property",
        "property_type": "appartamento",
        "operation": "sale",
        "price": 200000,
        "city": "Roma",
        "status": "active",
        "photos": [{"url": u, "order": i, "is_cover": i == 0} for i, u in enumerate(photo_urls)],
    })
    assert r.status_code == 201, r.text
    pid = r.json()["id"]
    yield pid, photo_urls
    session.delete(f"{BASE_URL}/api/app/properties/{pid}")


class TestKenBurnsGeneration:
    """D-064 · Ken Burns è disabilitato nel gestionale — riservato al portale B2C."""

    def test_kenburns_requires_auth(self, test_property_with_photos):
        pid, _ = test_property_with_photos
        r = requests.post(f"{BASE_URL}/api/app/videos/kenburns/property/{pid}", json={})
        assert r.status_code in (401, 403)

    def test_kenburns_in_agency_returns_501(self, session, test_property_with_photos):
        """Ken Burns è disabled sul gestionale per proteggere revenue Sora 2."""
        pid, urls = test_property_with_photos
        r = session.post(f"{BASE_URL}/api/app/videos/kenburns/property/{pid}",
                         json={"duration_s": 15, "photo_urls": urls})
        assert r.status_code == 501
        detail = str(r.json().get("detail", "")).lower()
        assert "kenburns_disabled" in detail or "sora" in detail

    def test_kenburns_property_not_owned_still_501(self, session):
        r = session.post(f"{BASE_URL}/api/app/videos/kenburns/property/does-not-exist",
                         json={"duration_s": 15})
        # Endpoint returns 501 regardless of property existence
        assert r.status_code == 501


class TestKenBurnsPublicPortal:
    """Ken Burns è funzionante SOLO sul portale B2C /api/cloud/*."""

    def test_public_endpoint_404_for_non_public_property(self):
        r = requests.post(
            f"{BASE_URL}/api/cloud/videos/kenburns/property/00000000-0000-0000-0000-000000000000",
            json={"duration_s": 15})
        assert r.status_code == 404


class TestFfmpegAvailable:
    def test_ffmpeg_installed_or_documented(self):
        """ffmpeg è dipendenza runtime — se manca skip con messaggio chiaro.

        Nel container di produzione va installato via apt-get in build step
        (D-063), non runtime install."""
        import shutil
        if shutil.which("ffmpeg") is None:
            pytest.skip("ffmpeg not installed in test container — install via apt-get in build step")


class TestKlingEndpoint:
    """D-065 · Kling 1.6 Pro image-to-video (fal.ai) replaces Sora 2."""

    def test_sora2_endpoint_deprecated(self, session, test_property_with_photos):
        pid, _ = test_property_with_photos
        r = session.post(f"{BASE_URL}/api/app/videos/sora2/property/{pid}")
        assert r.status_code == 410
        assert "kling" in str(r.json().get("detail", "")).lower()

    def test_kling_requires_auth(self, test_property_with_photos):
        pid, _ = test_property_with_photos
        r = requests.post(f"{BASE_URL}/api/app/videos/kling/property/{pid}")
        assert r.status_code in (401, 403)

    def test_kling_charges_credits_or_402(self, session, test_property_with_photos):
        """Endpoint charges 10 crediti (D-066) — either 202 accepted or 402."""
        pid, _ = test_property_with_photos
        r = session.post(f"{BASE_URL}/api/app/videos/kling/property/{pid}")
        assert r.status_code in (202, 402, 422)
        if r.status_code == 402:
            assert "insufficient_credits" in str(r.json().get("detail", ""))
        elif r.status_code == 202:
            data = r.json()
            assert data["mode"] == "kling_1_6_pro"
            assert data["duration_s"] == 10
            assert data["credits_charged"] == 10
