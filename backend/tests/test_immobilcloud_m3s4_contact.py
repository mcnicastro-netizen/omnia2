"""M3.S4 — ImmobilCloud B2C Property Detail + Contact Form tests."""
import os
import time
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
PROPERTY_ID = "3b81db11-2988-47a7-ae26-f4396913c3a7"  # Appartamento Centro Storico Roma
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia")

TS = int(time.time())


@pytest.fixture(scope="module")
def db():
    client = MongoClient(MONGO_URL)
    yield client[DB_NAME]
    # Cleanup all test data created
    client[DB_NAME].clients.delete_many({"source": "ImmobilCloud", "email": {"$regex": "m3s4test"}})
    client[DB_NAME].leads.delete_many({"source": "ImmobilCloud", "notes": {"$regex": "M3S4-TEST"}})
    client.close()


@pytest.fixture(scope="module")
def agency_id(db):
    p = db.properties.find_one({"id": PROPERTY_ID}, {"agency_id": 1})
    assert p, "Test property must exist"
    return p["agency_id"]


# ===== GET /property/{pid} =====

class TestGetPropertyDetail:
    def test_get_property_public_fields(self):
        r = requests.get(f"{BASE_URL}/api/cloud/property/{PROPERTY_ID}")
        assert r.status_code == 200
        d = r.json()
        # Required public fields
        assert d["id"] == PROPERTY_ID
        assert "title" in d
        assert "city" in d
        assert isinstance(d.get("photos"), list)
        # Agency present
        assert d.get("agency") is not None
        assert "slug" in d["agency"]
        assert "display_name" in d["agency"]
        # Private fields should NOT be present
        for forbidden in ("owner", "seller_client_id", "commission_pct", "listing_agent_id", "lead_count", "view_count"):
            assert forbidden not in d, f"private field leaked: {forbidden}"

    def test_get_property_increments_view_count(self, db):
        before = db.properties.find_one({"id": PROPERTY_ID}, {"view_count": 1})
        before_count = (before or {}).get("view_count", 0) or 0
        r = requests.get(f"{BASE_URL}/api/cloud/property/{PROPERTY_ID}")
        assert r.status_code == 200
        time.sleep(0.3)
        after = db.properties.find_one({"id": PROPERTY_ID}, {"view_count": 1})
        assert after["view_count"] == before_count + 1

    def test_get_property_not_found(self):
        r = requests.get(f"{BASE_URL}/api/cloud/property/non-exists-xyz")
        assert r.status_code == 404
        assert r.json().get("detail") == "property_not_found"


# ===== POST /property/{pid}/contact =====

class TestContactForm:
    def test_happy_path_creates_client_and_lead(self, db, agency_id):
        email = f"m3s4test+happy{TS}@example.com"
        payload = {
            "name": "Test M3S4 Happy",
            "email": email,
            "phone": "3331112222",
            "message": "M3S4-TEST happy — sono interessato a visitare questo immobile, contattatemi.",
            "gdpr_consent": True,
            "visit_requested": True,
        }
        leads_before = db.leads.count_documents({"property_id": PROPERTY_ID})
        prop_before = db.properties.find_one({"id": PROPERTY_ID}, {"lead_count": 1})
        lead_count_before = (prop_before or {}).get("lead_count", 0) or 0

        r = requests.post(f"{BASE_URL}/api/cloud/property/{PROPERTY_ID}/contact", json=payload)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["ok"] is True
        assert "lead_id" in d and "client_id" in d

        # Verify client persisted
        cli = db.clients.find_one({"id": d["client_id"]})
        assert cli is not None
        assert cli["agency_id"] == agency_id
        assert cli["source"] == "ImmobilCloud"
        assert cli["client_type"] == "buyer"
        assert cli["gdpr_consent"] is True
        assert cli["email"] == email.lower()

        # Verify lead persisted
        lead = db.leads.find_one({"id": d["lead_id"]})
        assert lead is not None
        assert lead["status"] == "new"
        assert lead["client_id"] == d["client_id"]
        assert lead["property_id"] == PROPERTY_ID
        assert "[richiesta visita immobile]" in lead["notes"]
        assert "M3S4-TEST happy" in lead["notes"]

        # lead_count incremented
        prop_after = db.properties.find_one({"id": PROPERTY_ID}, {"lead_count": 1})
        assert (prop_after or {}).get("lead_count", 0) == lead_count_before + 1

        # Total leads for property incremented
        assert db.leads.count_documents({"property_id": PROPERTY_ID}) == leads_before + 1

    def test_duplicate_email_reuses_client(self, db, agency_id):
        email = f"m3s4test+dup{TS}@example.com"
        payload = {
            "name": "Dup User",
            "email": email,
            "message": "M3S4-TEST dup — first submission with sufficiently long message.",
            "gdpr_consent": True,
        }
        # First submission
        r1 = requests.post(f"{BASE_URL}/api/cloud/property/{PROPERTY_ID}/contact", json=payload)
        assert r1.status_code == 200
        cid1 = r1.json()["client_id"]

        clients_count_before = db.clients.count_documents({"agency_id": agency_id, "email": email.lower()})
        leads_before = db.leads.count_documents({"client_id": cid1})

        # Second submission with same email
        payload["message"] = "M3S4-TEST dup — second submission, must reuse the client."
        r2 = requests.post(f"{BASE_URL}/api/cloud/property/{PROPERTY_ID}/contact", json=payload)
        assert r2.status_code == 200
        cid2 = r2.json()["client_id"]

        # Same client_id reused
        assert cid1 == cid2
        # Clients count unchanged
        assert db.clients.count_documents({"agency_id": agency_id, "email": email.lower()}) == clients_count_before
        # New lead added
        assert db.leads.count_documents({"client_id": cid1}) == leads_before + 1

    def test_gdpr_consent_required(self):
        payload = {
            "name": "NoGdpr",
            "email": f"m3s4test+nogdpr{TS}@example.com",
            "message": "M3S4-TEST nogdpr — message length is over ten characters.",
            "gdpr_consent": False,
        }
        r = requests.post(f"{BASE_URL}/api/cloud/property/{PROPERTY_ID}/contact", json=payload)
        assert r.status_code == 400
        assert r.json().get("detail") == "gdpr_consent_required"

    def test_short_message_422(self):
        payload = {
            "name": "Short",
            "email": f"m3s4test+short{TS}@example.com",
            "message": "too",
            "gdpr_consent": True,
        }
        r = requests.post(f"{BASE_URL}/api/cloud/property/{PROPERTY_ID}/contact", json=payload)
        assert r.status_code == 422

    def test_invalid_email_422(self):
        payload = {
            "name": "BadMail",
            "email": "not-an-email",
            "message": "M3S4-TEST bademail — sufficiently long message here.",
            "gdpr_consent": True,
        }
        r = requests.post(f"{BASE_URL}/api/cloud/property/{PROPERTY_ID}/contact", json=payload)
        assert r.status_code == 422

    def test_property_not_found_404(self):
        payload = {
            "name": "Ghost",
            "email": f"m3s4test+ghost{TS}@example.com",
            "message": "M3S4-TEST ghost — sufficiently long message body.",
            "gdpr_consent": True,
        }
        r = requests.post(f"{BASE_URL}/api/cloud/property/non-existing-xyz/contact", json=payload)
        assert r.status_code == 404
        assert r.json().get("detail") == "property_not_found"

    def test_private_property_returns_404(self, db):
        """Try contacting a property with visibility != public — should 404."""
        priv = db.properties.find_one({"$or": [
            {"visibility": "private"},
            {"status": "draft"},
            {"is_listed_on_immobilcloud": False},
        ]}, {"id": 1})
        if not priv:
            pytest.skip("No private/draft property in DB to test against")
        payload = {
            "name": "Priv",
            "email": f"m3s4test+priv{TS}@example.com",
            "message": "M3S4-TEST priv — sufficiently long message body here.",
            "gdpr_consent": True,
        }
        r = requests.post(f"{BASE_URL}/api/cloud/property/{priv['id']}/contact", json=payload)
        assert r.status_code == 404
