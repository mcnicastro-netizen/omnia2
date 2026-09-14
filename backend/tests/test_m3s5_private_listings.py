"""M3.S5 v2 — Backend tests for B2C private listings + admin moderation.

Covers:
  - POST /api/cloud/auth/register (B2C)
  - CRUD /api/cloud/me/properties (auth, owner filter, free-tier limit, edit reset, submit, delete)
  - GET /api/cloud/search (excludes pending/rejected, includes approved)
  - Admin moderation /api/app/moderation/{queue,approve,reject}
"""
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")

ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]

TS = int(time.time())
B2C_EMAIL_1 = f"b2cseller_{TS}_a@example.com"
B2C_EMAIL_2 = f"b2cseller_{TS}_b@example.com"
B2C_PASSWORD = "TestB2C2026!"


# ---------- helpers ----------

def _new_session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


def _register_b2c(email: str) -> requests.Session:
    s = _new_session()
    r = s.post(f"{BASE_URL}/api/cloud/auth/register", json={
        "email": email, "password": B2C_PASSWORD, "name": "B2C Tester",
        "intents": ["sell"], "lang": "it", "gdpr_consent": True,
    })
    assert r.status_code in (200, 201), f"register failed: {r.status_code} {r.text}"
    return s


def _login_admin() -> requests.Session:
    s = _new_session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
    })
    if r.status_code != 200:
        pytest.skip(f"admin login failed ({r.status_code}); skipping admin tests")
    return s


# ---------- shared session fixtures (module scoped to chain state) ----------

@pytest.fixture(scope="module")
def b2c_a():
    return _register_b2c(B2C_EMAIL_1)


@pytest.fixture(scope="module")
def b2c_b():
    return _register_b2c(B2C_EMAIL_2)


@pytest.fixture(scope="module")
def admin():
    return _login_admin()


# ---------- 1. Registration ----------

def test_01_register_b2c_returns_user(b2c_a):
    r = b2c_a.get(f"{BASE_URL}/api/auth/me")
    assert r.status_code == 200, r.text
    me = r.json()
    assert me.get("role") == "client"
    assert me.get("email") == B2C_EMAIL_1
    # account_type may or may not be exposed by /auth/me; if present, must be b2c
    if "account_type" in me:
        assert me["account_type"] == "b2c"


# ---------- 2. Create private listing ----------

@pytest.fixture(scope="module")
def listing_a(b2c_a):
    payload = {
        "title": "TEST_Casa privata Roma",
        "property_type": "appartamento",
        "operation": "sale",
        "city": "Roma",
        "address": "Via Test 1",
        "price": 250000,
        "surface_sqm": 90,
        "rooms": 3,
        "bedrooms": 2,
        "bathrooms": 1,
        "description": "Annuncio di test M3.S5",
    }
    r = b2c_a.post(f"{BASE_URL}/api/cloud/me/properties", json=payload)
    assert r.status_code == 201, f"create failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["status"] == "draft"
    assert data["moderation_status"] == "pending"
    assert data["is_private_listing"] is True
    assert data["agency_id"] == "_private_listings"
    assert data["owner_user_id"]
    return data


def test_02_create_listing(listing_a):
    assert listing_a["id"]


# ---------- 3. Unauthorized create ----------

def test_03_create_without_auth_rejected():
    s = _new_session()
    r = s.post(f"{BASE_URL}/api/cloud/me/properties", json={
        "title": "TEST_unauthorized", "city": "Roma", "operation": "sale",
        "property_type": "appartamento", "price": 100000,
    })
    assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code} {r.text}"


def test_03b_create_with_non_b2c_rejected():
    # admin (super_admin) is not b2c → must be rejected
    s = _login_admin()
    r = s.post(f"{BASE_URL}/api/cloud/me/properties", json={
        "title": "TEST_admin_attempt", "city": "Roma", "operation": "sale",
        "property_type": "appartamento", "price": 100000,
    })
    assert r.status_code == 403, f"expected 403 got {r.status_code} {r.text}"
    assert "b2c_account_required" in r.text


# ---------- 4. GET /me/properties returns only my listings ----------

def test_04_list_mine_only(b2c_a, b2c_b, listing_a):
    # b2c_b should see empty
    rb = b2c_b.get(f"{BASE_URL}/api/cloud/me/properties")
    assert rb.status_code == 200
    assert rb.json()["total"] == 0

    ra = b2c_a.get(f"{BASE_URL}/api/cloud/me/properties")
    assert ra.status_code == 200
    items = ra.json()["items"]
    assert any(i["id"] == listing_a["id"] for i in items)


# ---------- 5. Free-tier limit ----------

def test_05_free_tier_limit(b2c_a, listing_a):
    r = b2c_a.post(f"{BASE_URL}/api/cloud/me/properties", json={
        "title": "TEST_Second", "city": "Milano", "operation": "sale",
        "property_type": "appartamento", "price": 100000,
    })
    assert r.status_code == 409, f"expected 409 got {r.status_code} {r.text}"
    assert "free_tier_listing_limit_reached" in r.text


# ---------- 6/7. PATCH ownership ----------

def test_06_patch_own_listing(b2c_a, listing_a):
    r = b2c_a.patch(f"{BASE_URL}/api/cloud/me/properties/{listing_a['id']}",
                    json={"description": "updated description M3S5"})
    assert r.status_code == 200, r.text
    assert r.json().get("description") == "updated description M3S5"


def test_07_patch_other_user_listing_404(b2c_b, listing_a):
    r = b2c_b.patch(f"{BASE_URL}/api/cloud/me/properties/{listing_a['id']}",
                    json={"title": "hacker"})
    assert r.status_code == 404


# ---------- 8. Submit ----------

def test_08_submit_success(b2c_a, listing_a):
    r = b2c_a.post(f"{BASE_URL}/api/cloud/me/properties/{listing_a['id']}/submit")
    assert r.status_code == 200, r.text
    assert r.json()["moderation_status"] == "pending"


def test_08b_submit_missing_fields(b2c_b):
    # b2c_b creates a stub without title via direct payload — but the model may require title.
    # Workaround: create then patch out the title is non-trivial. Instead, simulate by creating
    # with placeholder title then DELETE and re-create minimal that doesn't have required.
    # Many PropertyCreate variants require title — so just attempt to create with missing pieces.
    r = b2c_b.post(f"{BASE_URL}/api/cloud/me/properties", json={
        "title": "TEST_Minimal_stub", "city": "Napoli", "operation": "sale",
        "property_type": "appartamento",
        # no price, no rent → submit later must fail
    })
    if r.status_code != 201:
        pytest.skip(f"could not create stub: {r.status_code} {r.text}")
    pid = r.json()["id"]
    sr = b2c_b.post(f"{BASE_URL}/api/cloud/me/properties/{pid}/submit")
    assert sr.status_code == 400, f"expected 400 got {sr.status_code} {sr.text}"
    assert "missing_required_fields" in sr.text


# ---------- 9. Admin moderation: queue/approve/reject ----------

def test_09_queue_requires_admin():
    s = _new_session()
    r = s.get(f"{BASE_URL}/api/app/moderation/queue")
    assert r.status_code in (401, 403)


def test_10_queue_pending_lists_listing(admin, listing_a):
    r = admin.get(f"{BASE_URL}/api/app/moderation/queue", params={"status": "pending"})
    assert r.status_code == 200, r.text
    ids = [i["id"] for i in r.json()["items"]]
    assert listing_a["id"] in ids


def test_11_reject_requires_min_notes(admin, listing_a):
    r = admin.post(f"{BASE_URL}/api/app/moderation/{listing_a['id']}/reject", json={"notes": "xx"})
    assert r.status_code == 422, f"expected 422 got {r.status_code} {r.text}"


def test_12_approve_makes_public(admin, listing_a):
    r = admin.post(f"{BASE_URL}/api/app/moderation/{listing_a['id']}/approve")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["moderation_status"] == "approved"
    assert data["status"] == "active"

    # Public search must include it now (search may take a tick; try a few times)
    found = False
    for _ in range(3):
        sr = requests.get(f"{BASE_URL}/api/cloud/search", params={"city": "Roma", "page_size": 60})
        if sr.status_code == 200:
            ids = [i["id"] for i in sr.json().get("items", [])]
            if listing_a["id"] in ids:
                found = True
                break
        time.sleep(0.5)
    assert found, "approved listing should appear in /api/cloud/search"


def test_13_patch_substantive_after_approval_resets_to_pending(b2c_a, listing_a):
    r = b2c_a.patch(f"{BASE_URL}/api/cloud/me/properties/{listing_a['id']}",
                    json={"title": "TEST_Casa privata Roma EDIT", "price": 260000})
    assert r.status_code == 200, r.text
    doc = r.json()
    assert doc["moderation_status"] == "pending"
    assert doc["status"] == "draft"

    # And: no longer in /search
    sr = requests.get(f"{BASE_URL}/api/cloud/search",
                      params={"city": "Roma", "page_size": 60})
    assert sr.status_code == 200
    ids = [i["id"] for i in sr.json().get("items", [])]
    assert listing_a["id"] not in ids


def test_14_reject_with_valid_notes(admin, listing_a):
    r = admin.post(f"{BASE_URL}/api/app/moderation/{listing_a['id']}/reject",
                   json={"notes": "Foto non chiare, riprova"})
    assert r.status_code == 200, r.text
    assert r.json()["moderation_status"] == "rejected"

    # Search must NOT include rejected
    sr = requests.get(f"{BASE_URL}/api/cloud/search",
                      params={"city": "Roma", "page_size": 60})
    ids = [i["id"] for i in sr.json().get("items", [])]
    assert listing_a["id"] not in ids


def test_15_moderate_non_private_listing_404(admin):
    # Random uuid for a non-existent / non-private listing
    fake_id = str(uuid.uuid4())
    r = admin.post(f"{BASE_URL}/api/app/moderation/{fake_id}/approve")
    assert r.status_code == 404


# ---------- 16. DELETE ----------

def test_16_delete_own(b2c_a, listing_a):
    r = b2c_a.delete(f"{BASE_URL}/api/cloud/me/properties/{listing_a['id']}")
    assert r.status_code in (200, 204)
    # GET → 404
    r2 = b2c_a.get(f"{BASE_URL}/api/cloud/me/properties/{listing_a['id']}")
    assert r2.status_code == 404


# ---------- Cleanup ----------

def test_99_cleanup_test_data(b2c_b):
    # Delete b2c_b stub property if exists
    r = b2c_b.get(f"{BASE_URL}/api/cloud/me/properties")
    if r.status_code == 200:
        for it in r.json().get("items", []):
            b2c_b.delete(f"{BASE_URL}/api/cloud/me/properties/{it['id']}")
