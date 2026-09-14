"""Sprint 4 · GAP #1 — Object Storage integration tests.

Verifies:
1. POST /api/app/properties/{id}/photos/upload accepts JPG/PNG/WEBP,
   rejects other MIME types and files > 8MB.
2. The uploaded photo returns a `/api/media/...` URL served by the backend.
3. GET /api/media/{path} is public (no auth required) and returns the same
   bytes with the correct content-type.
4. Setting `is_cover=true` clears the flag on other photos.
"""
from __future__ import annotations

import base64
import io
import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"
API = BASE_URL.rstrip("/")

SUPER = (os.environ["OMNIA_ADMIN_EMAIL"], os.environ["OMNIA_ADMIN_PASSWORD"])

# 1x1 transparent PNG
_PNG_1x1 = base64.b64decode(
    b"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{API}/api/auth/login", json={"email": SUPER[0], "password": SUPER[1]}, timeout=15)
    r.raise_for_status()
    return s


@pytest.fixture(scope="module")
def property_id(session):
    r = session.get(f"{API}/api/app/properties?page=1&page_size=1", timeout=15)
    r.raise_for_status()
    items = r.json().get("items") or []
    if items:
        return items[0]["id"]
    # Create a stub property
    r = session.post(
        f"{API}/api/app/properties",
        json={
            "title": f"Objstore test {uuid.uuid4().hex[:6]}",
            "property_type": "appartamento",
            "operation": "sale",
            "city": "Roma",
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json()["id"]


class TestPhotoUpload:
    def test_upload_png_ok(self, session, property_id):
        files = {"file": ("t.png", _PNG_1x1, "image/png")}
        r = session.post(
            f"{API}/api/app/properties/{property_id}/photos/upload?is_cover=true",
            files=files,
            timeout=30,
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert "photo" in body and "url" in body["photo"]
        assert body["photo"]["url"].startswith("/api/media/omnia/properties/")
        assert body["photo"]["is_cover"] is True

    def test_public_media_serve(self, session, property_id):
        files = {"file": ("t.png", _PNG_1x1, "image/png")}
        r = session.post(
            f"{API}/api/app/properties/{property_id}/photos/upload",
            files=files,
            timeout=30,
        )
        assert r.status_code == 200
        url = r.json()["photo"]["url"]
        # Public GET (no cookies)
        r2 = requests.get(f"{API}{url}", timeout=15)
        assert r2.status_code == 200
        assert r2.headers["content-type"] == "image/png"
        assert r2.content == _PNG_1x1

    def test_reject_wrong_mime(self, session, property_id):
        files = {"file": ("t.txt", b"hello", "text/plain")}
        r = session.post(
            f"{API}/api/app/properties/{property_id}/photos/upload",
            files=files,
            timeout=15,
        )
        assert r.status_code == 415

    def test_reject_too_large(self, session, property_id):
        big = b"\x89PNG\r\n\x1a\n" + os.urandom(9 * 1024 * 1024)
        files = {"file": ("big.png", big, "image/png")}
        r = session.post(
            f"{API}/api/app/properties/{property_id}/photos/upload",
            files=files,
            timeout=30,
        )
        assert r.status_code == 413

    def test_setting_cover_clears_other(self, session, property_id):
        # Upload 2 photos, second with is_cover=true → first should not be cover
        r1 = session.post(
            f"{API}/api/app/properties/{property_id}/photos/upload?is_cover=true",
            files={"file": ("a.png", _PNG_1x1, "image/png")},
            timeout=15,
        )
        assert r1.status_code == 200
        r2 = session.post(
            f"{API}/api/app/properties/{property_id}/photos/upload?is_cover=true",
            files={"file": ("b.png", _PNG_1x1, "image/png")},
            timeout=15,
        )
        assert r2.status_code == 200
        photos = r2.json()["photos"]
        covers = [p for p in photos if p.get("is_cover")]
        assert len(covers) == 1, f"expected exactly 1 cover, got {len(covers)}"


class TestMediaEndpoint:
    def test_media_404_on_bogus_path(self):
        r = requests.get(f"{API}/api/media/omnia/does/not/exist.png", timeout=10)
        assert r.status_code == 404

    def test_media_400_on_dotdot_segment(self):
        # Path traversal segments arrive server-side only when NOT normalized
        # client-side. Use raw HTTP via urllib3 to keep `..` intact.
        import urllib.request
        req = urllib.request.Request(f"{API}/api/media/foo/..%2F..%2Fetc%2Fpasswd")
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
        assert status in (400, 403, 404)
