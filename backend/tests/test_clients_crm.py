"""Backend tests for M2.S3 — CRM Clients + Agency Website settings.

Covers:
- Auth (cookie session)
- Clients CRUD: POST/GET/PATCH/DELETE /api/app/clients
- Filters: q, client_type, status
- CSV template + CSV import with mixed valid/invalid rows
- Agency website mode update via PATCH /api/app/agencies/me
- Multi-tenant: 401 without auth
"""
import os
import io
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

SUPER_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
SUPER_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]


@pytest.fixture(scope="session")
def session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": SUPER_EMAIL, "password": SUPER_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="session")
def created_ids():
    return []


# --- AUTH / NEGATIVE ---
def test_unauth_clients_returns_401():
    r = requests.get(f"{API}/app/clients", timeout=15)
    assert r.status_code == 401, f"expected 401 got {r.status_code}: {r.text[:200]}"


def test_me_endpoint(session):
    r = session.get(f"{API}/auth/me", timeout=15)
    assert r.status_code == 200
    me = r.json()
    assert me["email"] == SUPER_EMAIL
    assert me.get("agency_ids"), "super admin must have agency_ids"


# --- CLIENTS CRUD ---
def test_create_client_full(session, created_ids):
    payload = {
        "name": "TEST_Marco",
        "surname": "Verdi",
        "email": "TEST_marco@example.it",
        "phone": "+39 333 1112222",
        "client_type": "buyer",
        "status": "new",
        "source": "Idealista",
        "preferences": {
            "operation": "sale",
            "property_types": ["appartamento", "attico"],
            "cities": ["Roma", "Milano"],
            "zones": ["Trastevere"],
            "price_min": 150000,
            "price_max": 300000,
            "surface_min": 60,
            "rooms_min": 2,
            "bathrooms_min": 1,
            "conditions": ["buone", "ristrutturato"],
            "floor_preferences": ["intermedi", "ultimo"],
            "must_have_features": ["ascensore", "balcone"],
            "energy_min_class": "C",
            "needs_photos": True,
            "needs_virtual_tour": False,
            "notes": "Cliente prioritario",
        },
        "notes": "Test notes",
        "gdpr_consent": True,
    }
    r = session.post(f"{API}/app/clients", json=payload, timeout=15)
    assert r.status_code == 201, f"create failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["name"] == "TEST_Marco"
    assert data["preferences"]["price_min"] == 150000
    assert "appartamento" in data["preferences"]["property_types"]
    assert "buone" in data["preferences"]["conditions"]
    assert "intermedi" in data["preferences"]["floor_preferences"]
    assert data["preferences"]["energy_min_class"] == "C"
    assert data["preferences"]["needs_photos"] is True
    assert data["gdpr_consent"] is True
    assert "_id" not in data
    created_ids.append(data["id"])


def test_get_client(session, created_ids):
    if not created_ids:
        pytest.skip("no client created")
    cid = created_ids[0]
    r = session.get(f"{API}/app/clients/{cid}", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == cid
    assert data["preferences"]["cities"] == ["Roma", "Milano"]


def test_list_clients(session, created_ids):
    r = session.get(f"{API}/app/clients", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body
    ids = [c["id"] for c in body["items"]]
    if created_ids:
        assert created_ids[0] in ids


def test_filter_by_type_and_status(session, created_ids):
    r = session.get(f"{API}/app/clients?client_type=buyer&status=new", timeout=15)
    assert r.status_code == 200
    body = r.json()
    for c in body["items"]:
        assert c["client_type"] == "buyer"
        assert c["status"] == "new"


def test_search_q(session):
    r = session.get(f"{API}/app/clients?q=TEST_Marco", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert any("TEST_Marco" in c["name"] for c in body["items"])


def test_patch_client_status(session, created_ids):
    cid = created_ids[0]
    r = session.patch(f"{API}/app/clients/{cid}", json={"status": "qualified"}, timeout=15)
    assert r.status_code == 200, r.text
    # Verify persisted
    g = session.get(f"{API}/app/clients/{cid}", timeout=15).json()
    assert g["status"] == "qualified"


def test_csv_template(session):
    r = session.get(f"{API}/app/clients/_template/csv", timeout=15)
    assert r.status_code == 200
    content = r.content
    assert content.startswith(b"\xef\xbb\xbf"), "Missing UTF-8 BOM"
    text = content.decode("utf-8-sig")
    assert "name" in text and "pref_property_types" in text and "gdpr_consent" in text


def test_csv_import_mixed(session):
    payload = {
        "rows": [
            {
                "name": "TEST_Anna", "surname": "Bianchi",
                "email": "TEST_anna@example.it", "phone": "+39 333 9990001",
                "client_type": "buyer", "status": "new", "source": "Idealista",
                "pref_operation": "sale", "pref_cities": "Roma;Napoli",
                "pref_property_types": "appartamento;loft",
                "pref_price_min": "100000", "pref_price_max": "200000",
                "pref_surface_min": "50", "pref_rooms_min": "2",
                "gdpr_consent": "true",
            },
            {
                "name": "TEST_Luca", "client_type": "seller", "status": "new",
                "gdpr_consent": "false",
            },
            {
                # missing name -> should error
                "surname": "NoName",
                "email": "noname@example.it",
                "gdpr_consent": "true",
            },
        ]
    }
    r = session.post(f"{API}/app/clients/import/csv", json=payload, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["imported"] == 2
    assert body["total_rows"] == 3
    assert len(body["errors"]) == 1
    assert body["errors"][0]["row"] == 3
    assert body["status"] == "completed_with_errors"


def test_delete_client(session, created_ids):
    cid = created_ids[0]
    r = session.delete(f"{API}/app/clients/{cid}", timeout=15)
    assert r.status_code == 200
    g = session.get(f"{API}/app/clients/{cid}", timeout=15)
    assert g.status_code == 404


def test_cleanup_test_clients(session):
    """Delete TEST_ prefixed clients created by CSV import."""
    r = session.get(f"{API}/app/clients?q=TEST_", timeout=15).json()
    for c in r.get("items", []):
        if c["name"].startswith("TEST_"):
            session.delete(f"{API}/app/clients/{c['id']}", timeout=15)


# --- AGENCY WEBSITE ---
def test_agency_me_get(session):
    r = session.get(f"{API}/app/agencies/me", timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "website" in body


def test_agency_website_external_update(session):
    payload = {"website": {"mode": "external", "external_url": "https://www.testagenzia.it"}}
    r = session.patch(f"{API}/app/agencies/me", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["website"]["mode"] == "external"
    assert body["website"]["external_url"] == "https://www.testagenzia.it"


def test_agency_website_template_update(session):
    payload = {"website": {"mode": "omnia_template", "template_id": "modern-01"}}
    r = session.patch(f"{API}/app/agencies/me", json=payload, timeout=15)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["website"]["mode"] == "omnia_template"
    assert body["website"]["template_id"] == "modern-01"
    # restore to external for UI test reproducibility
    session.patch(f"{API}/app/agencies/me", json={"website": {"mode": "external", "external_url": "https://www.testagenzia.it"}}, timeout=15)
