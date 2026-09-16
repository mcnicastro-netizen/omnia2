"""B2C private listing media upload — photos (max 30) + floor plans."""
import io
import os
import time

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "http://127.0.0.1:43121").rstrip("/")
API = f"{BASE_URL}/api"
TS = int(time.time())
B2C_EMAIL = f"b2cmedia_{TS}@example.com"
B2C_PASSWORD = "TestB2CMedia2026!"


def _tiny_jpeg():
    return (b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
            b"\xff\xdb\x00C\x00" + b"\x08" * 64 +
            b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
            b"\xff\xc4\x00\x14\x00\x01" + b"\x00" * 15 + b"\x00"
            b"\xff\xc4\x00\x14\x10\x01" + b"\x00" * 15 + b"\x00"
            b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9")


@pytest.fixture(scope="module")
def b2c():
    s = requests.Session()
    r = s.post(f"{API}/cloud/auth/register", json={
        "email": B2C_EMAIL, "password": B2C_PASSWORD, "name": "Media Tester",
        "intents": ["sell"], "lang": "it", "gdpr_consent": True,
    })
    assert r.status_code in (200, 201), f"register failed: {r.status_code} {r.text}"
    return s


def test_upload_tmp_requires_auth():
    files = {"file": ("t.jpg", io.BytesIO(_tiny_jpeg()), "image/jpeg")}
    r = requests.post(f"{API}/cloud/me/properties/media/upload-tmp", files=files, data={"kind": "photo"})
    assert r.status_code in (401, 403), f"got {r.status_code}"


def test_upload_photo_and_floor_plan(b2c):
    files = {"file": ("foto.jpg", io.BytesIO(_tiny_jpeg()), "image/jpeg")}
    r = b2c.post(f"{API}/cloud/me/properties/media/upload-tmp", files=files, data={"kind": "photo"})
    assert r.status_code == 200, r.text
    photo = r.json()
    assert photo["url"].startswith("/api/media/omnia/private/")
    assert "/photos/" in photo["url"]
    assert photo["kind"] == "photo"

    files2 = {"file": ("pianta.jpg", io.BytesIO(_tiny_jpeg()), "image/jpeg")}
    r2 = b2c.post(f"{API}/cloud/me/properties/media/upload-tmp", files=files2, data={"kind": "floor_plan"})
    assert r2.status_code == 200, r2.text
    plan = r2.json()
    assert plan["url"].startswith("/api/media/omnia/private/")
    assert "/floor_plans/" in plan["url"]
    assert plan["kind"] == "floor_plan"

    # Media serve
    for url in (photo["url"], plan["url"]):
        mr = b2c.get(f"{BASE_URL}{url}")
        assert mr.status_code == 200, f"{url} → {mr.status_code}"
        assert mr.headers.get("content-type", "").startswith("image/")


def test_create_listing_with_photos_and_floor_plan(b2c):
    # upload 2 photos + floor plan
    urls = []
    for i in range(2):
        files = {"file": (f"p{i}.jpg", io.BytesIO(_tiny_jpeg()), "image/jpeg")}
        r = b2c.post(f"{API}/cloud/me/properties/media/upload-tmp", files=files, data={"kind": "photo"})
        assert r.status_code == 200, r.text
        urls.append(r.json()["url"])

    files = {"file": ("plan.jpg", io.BytesIO(_tiny_jpeg()), "image/jpeg")}
    fr = b2c.post(f"{API}/cloud/me/properties/media/upload-tmp", files=files, data={"kind": "floor_plan"})
    assert fr.status_code == 200, fr.text
    floor_url = fr.json()["url"]

    photos = [
        {"id": "p0", "url": urls[0], "caption": "soggiorno", "order": 0, "is_cover": True},
        {"id": "p1", "url": urls[1], "caption": "cucina", "order": 1, "is_cover": False},
    ]
    r = b2c.post(f"{API}/cloud/me/properties", json={
        "title": "TEST_Media listing con foto",
        "property_type": "appartamento",
        "operation": "sale",
        "city": "Torino",
        "price": 180000,
        "photos": photos,
        "floor_plan_url": floor_url,
    })
    assert r.status_code == 201, r.text
    doc = r.json()
    assert len(doc.get("photos") or []) == 2
    assert doc.get("floor_plan_url") == floor_url
    pid = doc["id"]

    # photos limit > 30 rejected on patch
    too_many = [
        {"id": f"x{i}", "url": urls[0], "order": i, "is_cover": i == 0}
        for i in range(31)
    ]
    pr = b2c.patch(f"{API}/cloud/me/properties/{pid}", json={"photos": too_many})
    assert pr.status_code == 400, pr.text
    assert "photos_limit_exceeded" in pr.text

    # cleanup
    b2c.delete(f"{API}/cloud/me/properties/{pid}")


def test_reject_bad_mime(b2c):
    files = {"file": ("x.txt", io.BytesIO(b"not an image"), "text/plain")}
    r = b2c.post(f"{API}/cloud/me/properties/media/upload-tmp", files=files, data={"kind": "photo"})
    assert r.status_code == 415, r.text
