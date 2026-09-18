"""Smoke: agency video upload-tmp (MP4) + media serve + Range."""
from __future__ import annotations

import io
import os

import pytest
import requests

API = os.environ.get("API_BASE", "http://127.0.0.1:43121/api").rstrip("/")


def _minimal_mp4() -> bytes:
    # Minimal ftyp+mdat stub — enough for MIME/storage, not a real player file.
    return (
        b"\x00\x00\x00\x18ftypmp42"
        b"\x00\x00\x00\x00mp42isom"
        b"\x00\x00\x00\x08mdat"
    )


@pytest.fixture(scope="module")
def agency_sess():
    email = os.environ.get("OMNIA_TEST_EMAIL", "mcnicastro@gmail.com")
    password = os.environ.get("OMNIA_TEST_PASSWORD", "OmniaFounder2026!")
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"login failed: {r.status_code} {r.text[:200]}")
    if not s.cookies.get("access_token"):
        pytest.skip("login ok but no access_token cookie")
    return s


def test_video_upload_tmp_and_media_range(agency_sess):
    files = {"file": ("demo.mp4", io.BytesIO(_minimal_mp4()), "video/mp4")}
    r = agency_sess.post(f"{API}/app/properties/videos/upload-tmp", files=files, timeout=60)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["url"].startswith("/api/media/")
    assert body["content_type"] == "video/mp4"
    assert body["size_bytes"] > 0

    media_url = f"http://127.0.0.1:43121{body['url']}"
    g = requests.get(media_url, timeout=20)
    assert g.status_code == 200
    assert "video" in (g.headers.get("Content-Type") or "")
    assert g.headers.get("Accept-Ranges") == "bytes"

    rng = requests.get(media_url, headers={"Range": "bytes=0-7"}, timeout=20)
    assert rng.status_code == 206
    assert len(rng.content) == 8


def test_video_rejects_bad_mime(agency_sess):
    files = {"file": ("x.txt", io.BytesIO(b"hello"), "text/plain")}
    r = agency_sess.post(f"{API}/app/properties/videos/upload-tmp", files=files, timeout=30)
    assert r.status_code == 415
