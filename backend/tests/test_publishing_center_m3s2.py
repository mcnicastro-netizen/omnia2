"""OMNIA — M3.S2 Publishing Center backend tests.

Validates:
- POST /api/app/properties with is_listed_on_immobilcloud=false persists false
- POST without field defaults to True
- PATCH toggle to false/true works
- Public /api/cloud/search filters by is_listed_on_immobilcloud
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def agency_id(session):
    """Ensure the super admin user has an agency_ids on the user doc.
    We rely on /app/agencies/me for slug and existence."""
    r = session.get(f"{BASE_URL}/api/app/agencies/me", timeout=15)
    if r.status_code == 200:
        return r.json().get("id")
    # Create agency if missing
    r = session.post(
        f"{BASE_URL}/api/app/agencies",
        json={"display_name": "TEST_Agency_M3S2", "slug": "test-m3s2", "city": "Roma"},
        timeout=15,
    )
    assert r.status_code in (200, 201), f"Agency create failed: {r.status_code} {r.text}"
    return r.json().get("id")


@pytest.fixture
def created_ids():
    ids = []
    yield ids
    # cleanup is best-effort; deletion requires auth, but module session is scope=module


def _cleanup(session, ids):
    for pid in ids:
        try:
            session.delete(f"{BASE_URL}/api/app/properties/{pid}", timeout=10)
        except Exception:
            pass


# ---------- TEST 1: POST with is_listed_on_immobilcloud=false ----------
def test_create_with_immobilcloud_false_persists(session, agency_id, created_ids):
    payload = {
        "title": "TEST_M3S2_off_property",
        "city": "Milano",
        "status": "active",
        "visibility": "public",
        "is_listed_on_immobilcloud": False,
    }
    r = session.post(f"{BASE_URL}/api/app/properties", json=payload, timeout=15)
    assert r.status_code == 201, f"Create failed: {r.text}"
    data = r.json()
    pid = data["id"]
    created_ids.append(pid)
    assert data["is_listed_on_immobilcloud"] is False

    # GET to verify persistence
    g = session.get(f"{BASE_URL}/api/app/properties/{pid}", timeout=15)
    assert g.status_code == 200
    assert g.json()["is_listed_on_immobilcloud"] is False
    _cleanup(session, [pid])
    created_ids.remove(pid)


# ---------- TEST 2: POST without field → default True ----------
def test_create_without_field_defaults_true(session, agency_id, created_ids):
    payload = {"title": "TEST_M3S2_default_property", "city": "Roma"}
    r = session.post(f"{BASE_URL}/api/app/properties", json=payload, timeout=15)
    assert r.status_code == 201, f"Create failed: {r.text}"
    data = r.json()
    pid = data["id"]
    created_ids.append(pid)
    assert data["is_listed_on_immobilcloud"] is True

    g = session.get(f"{BASE_URL}/api/app/properties/{pid}", timeout=15)
    assert g.status_code == 200
    assert g.json()["is_listed_on_immobilcloud"] is True
    _cleanup(session, [pid])
    created_ids.remove(pid)


# ---------- TEST 3: PATCH toggle false → true → false ----------
def test_patch_toggle_immobilcloud(session, agency_id, created_ids):
    # create (default True)
    r = session.post(
        f"{BASE_URL}/api/app/properties",
        json={"title": "TEST_M3S2_patch_property", "city": "Torino"},
        timeout=15,
    )
    assert r.status_code == 201
    pid = r.json()["id"]
    created_ids.append(pid)

    # patch -> false
    p = session.patch(
        f"{BASE_URL}/api/app/properties/{pid}",
        json={"is_listed_on_immobilcloud": False},
        timeout=15,
    )
    assert p.status_code == 200, f"Patch failed: {p.text}"
    assert p.json()["is_listed_on_immobilcloud"] is False
    g = session.get(f"{BASE_URL}/api/app/properties/{pid}", timeout=15)
    assert g.json()["is_listed_on_immobilcloud"] is False

    # patch -> true
    p2 = session.patch(
        f"{BASE_URL}/api/app/properties/{pid}",
        json={"is_listed_on_immobilcloud": True},
        timeout=15,
    )
    assert p2.status_code == 200
    assert p2.json()["is_listed_on_immobilcloud"] is True
    g2 = session.get(f"{BASE_URL}/api/app/properties/{pid}", timeout=15)
    assert g2.json()["is_listed_on_immobilcloud"] is True
    _cleanup(session, [pid])
    created_ids.remove(pid)


# ---------- TEST 4: Public cloud/search filters by is_listed_on_immobilcloud ----------
def test_cloud_search_filters_immobilcloud_flag(session, agency_id, created_ids):
    # create one ON (active + public + immobilcloud=true)
    r_on = session.post(
        f"{BASE_URL}/api/app/properties",
        json={
            "title": "TEST_M3S2_cloud_visible_xyz123",
            "city": "Bologna",
            "status": "active",
            "visibility": "public",
            "is_listed_on_immobilcloud": True,
        },
        timeout=15,
    )
    assert r_on.status_code == 201, r_on.text
    pid_on = r_on.json()["id"]
    created_ids.append(pid_on)

    # create one OFF (active + public + immobilcloud=false)
    r_off = session.post(
        f"{BASE_URL}/api/app/properties",
        json={
            "title": "TEST_M3S2_cloud_hidden_xyz123",
            "city": "Bologna",
            "status": "active",
            "visibility": "public",
            "is_listed_on_immobilcloud": False,
        },
        timeout=15,
    )
    assert r_off.status_code == 201, r_off.text
    pid_off = r_off.json()["id"]
    created_ids.append(pid_off)

    # search (NO auth needed)
    pub = requests.get(
        f"{BASE_URL}/api/cloud/search",
        params={"q": "TEST_M3S2_cloud", "page_size": 60},
        timeout=15,
    )
    assert pub.status_code == 200
    ids = [it["id"] for it in pub.json().get("items", [])]
    assert pid_on in ids, f"ON property must appear in cloud search; got ids={ids}"
    assert pid_off not in ids, f"OFF property must NOT appear in cloud search; got ids={ids}"

    _cleanup(session, [pid_on, pid_off])
    created_ids.remove(pid_on)
    created_ids.remove(pid_off)
