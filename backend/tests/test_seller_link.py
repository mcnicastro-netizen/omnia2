"""Backend tests for M2.S3.5 (D-026): bidirectional Property<->Client link."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return s


@pytest.fixture(scope="module")
def seller_client(session):
    """Create a TEST_ seller client for this run."""
    payload = {
        "name": f"TEST_Seller_{uuid.uuid4().hex[:6]}",
        "surname": "Linker",
        "email": f"test_seller_{uuid.uuid4().hex[:6]}@example.it",
        "phone": "+39 333 0000000",
        "client_type": "seller",
        "status": "new",
        "gdpr_consent": True,
    }
    r = session.post(f"{BASE_URL}/api/app/clients", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    yield data
    session.delete(f"{BASE_URL}/api/app/clients/{data['id']}")


@pytest.fixture(scope="module")
def buyer_client(session):
    payload = {
        "name": f"TEST_Buyer_{uuid.uuid4().hex[:6]}",
        "client_type": "buyer",
        "status": "new",
        "gdpr_consent": True,
    }
    r = session.post(f"{BASE_URL}/api/app/clients", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    yield data
    session.delete(f"{BASE_URL}/api/app/clients/{data['id']}")


@pytest.fixture(scope="module")
def landlord_client(session):
    payload = {
        "name": f"TEST_Landlord_{uuid.uuid4().hex[:6]}",
        "client_type": "landlord",
        "status": "new",
        "gdpr_consent": True,
    }
    r = session.post(f"{BASE_URL}/api/app/clients", json=payload)
    assert r.status_code == 201, r.text
    data = r.json()
    yield data
    session.delete(f"{BASE_URL}/api/app/clients/{data['id']}")


# ---------- GET /clients/sellers ----------

class TestSellersAutocomplete:
    def test_sellers_returns_only_seller_landlord(self, session, seller_client, buyer_client, landlord_client):
        r = session.get(f"{BASE_URL}/api/app/clients/sellers")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        types = {it["client_type"] for it in data["items"]}
        # buyer must NOT appear; seller/landlord allowed
        assert "buyer" not in types
        assert "tenant" not in types
        assert "investor" not in types
        ids = [it["id"] for it in data["items"]]
        assert seller_client["id"] in ids
        assert landlord_client["id"] in ids
        assert buyer_client["id"] not in ids

    def test_sellers_query_regex(self, session, seller_client):
        # search by prefix of name (case-insensitive)
        q = seller_client["name"][:8].lower()
        r = session.get(f"{BASE_URL}/api/app/clients/sellers", params={"q": q})
        assert r.status_code == 200
        ids = [it["id"] for it in r.json()["items"]]
        assert seller_client["id"] in ids

    def test_sellers_query_no_match(self, session):
        r = session.get(f"{BASE_URL}/api/app/clients/sellers", params={"q": "zzzz_no_such_seller_zzz"})
        assert r.status_code == 200
        assert r.json()["items"] == []

    def test_sellers_unauth(self):
        r = requests.get(f"{BASE_URL}/api/app/clients/sellers")
        assert r.status_code in (401, 403)


# ---------- POST /properties with seller_client_id ----------

class TestPropertySellerLink:
    def test_create_property_with_seller(self, session, seller_client):
        payload = {
            "title": "TEST_PROP_LINK_create",
            "city": "Roma",
            "operation": "sale",
            "property_type": "appartamento",
            "seller_client_id": seller_client["id"],
            "owner": {"name": "auto", "phone": "+39 333 1", "email": "auto@example.it"},
        }
        r = session.post(f"{BASE_URL}/api/app/properties", json=payload)
        assert r.status_code in (200, 201), r.text
        pid = r.json()["id"]
        # GET to verify persistence
        g = session.get(f"{BASE_URL}/api/app/properties/{pid}")
        assert g.status_code == 200
        assert g.json().get("seller_client_id") == seller_client["id"]
        # cleanup
        session.delete(f"{BASE_URL}/api/app/properties/{pid}")

    def test_patch_set_change_and_null_semantics(self, session, seller_client, landlord_client):
        # create empty
        r = session.post(f"{BASE_URL}/api/app/properties", json={
            "title": "TEST_PROP_LINK_patch", "city": "Milano",
        })
        assert r.status_code in (200, 201), r.text
        pid = r.json()["id"]
        assert r.json().get("seller_client_id") in (None, "")

        # set
        r = session.patch(f"{BASE_URL}/api/app/properties/{pid}", json={"seller_client_id": seller_client["id"]})
        assert r.status_code == 200, r.text
        assert r.json()["seller_client_id"] == seller_client["id"]

        # change
        r = session.patch(f"{BASE_URL}/api/app/properties/{pid}", json={"seller_client_id": landlord_client["id"]})
        assert r.status_code == 200, r.text
        assert r.json()["seller_client_id"] == landlord_client["id"]

        # PATCH semantics: seller_client_id is a NULLABLE_FIELD — explicit null CLEARS it
        # (the frontend "Rimuovi" action relies on this explicit-clear behaviour)
        r = session.patch(f"{BASE_URL}/api/app/properties/{pid}", json={"seller_client_id": None})
        assert r.status_code == 200, r.text
        assert r.json()["seller_client_id"] is None, \
            "PATCH with explicit null must clear seller_client_id (NULLABLE_FIELDS semantics)"

        # re-set, then omit -> value persists (exclude_unset semantics for omitted fields)
        r = session.patch(f"{BASE_URL}/api/app/properties/{pid}", json={"seller_client_id": landlord_client["id"]})
        assert r.status_code == 200, r.text
        r = session.patch(f"{BASE_URL}/api/app/properties/{pid}", json={"title": "TEST_PROP_LINK_patch_v2"})
        assert r.status_code == 200, r.text
        assert r.json()["seller_client_id"] == landlord_client["id"]

        session.delete(f"{BASE_URL}/api/app/properties/{pid}")


# ---------- GET /clients/{cid}/properties ----------

class TestCarriedProperties:
    def test_returns_only_linked_properties(self, session, seller_client, landlord_client):
        # create 2 properties under seller, 1 under landlord
        ids_seller = []
        for i in range(2):
            r = session.post(f"{BASE_URL}/api/app/properties", json={
                "title": f"TEST_CARRIED_S_{i}", "city": "Roma",
                "seller_client_id": seller_client["id"],
            })
            assert r.status_code in (200, 201)
            ids_seller.append(r.json()["id"])

        r = session.post(f"{BASE_URL}/api/app/properties", json={
            "title": "TEST_CARRIED_L", "city": "Roma",
            "seller_client_id": landlord_client["id"],
        })
        assert r.status_code in (200, 201)
        landlord_pid = r.json()["id"]

        # GET seller's properties
        r = session.get(f"{BASE_URL}/api/app/clients/{seller_client['id']}/properties")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "items" in data and "total" in data
        ret_ids = {it["id"] for it in data["items"]}
        assert set(ids_seller).issubset(ret_ids)
        assert landlord_pid not in ret_ids
        # essential fields only, no description, no owner, no _id
        for it in data["items"]:
            assert "id" in it and "title" in it and "city" in it
            assert "cover_photo_url" in it  # must be present (even if None)
            assert "_id" not in it
            assert "description" not in it
            assert "owner" not in it

        # cleanup
        for pid in ids_seller + [landlord_pid]:
            session.delete(f"{BASE_URL}/api/app/properties/{pid}")

    def test_carried_404_for_unknown_client(self, session):
        r = session.get(f"{BASE_URL}/api/app/clients/{uuid.uuid4().hex}/properties")
        assert r.status_code == 404

    def test_carried_empty_when_no_linked(self, session, buyer_client):
        # a buyer client has no properties — endpoint should return [] not 404
        r = session.get(f"{BASE_URL}/api/app/clients/{buyer_client['id']}/properties")
        assert r.status_code == 200
        assert r.json()["items"] == []
        assert r.json()["total"] == 0


# ---------- Auth boundary ----------

class TestAuthBoundary:
    def test_carried_unauth(self):
        r = requests.get(f"{BASE_URL}/api/app/clients/abc/properties")
        assert r.status_code in (401, 403)
