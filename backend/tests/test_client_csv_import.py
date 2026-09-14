"""Backend regression: client CSV template + import endpoints (already in clients.py).
Frontend ClientImportPage uses these endpoints."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")

ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASS = os.environ["OMNIA_ADMIN_PASSWORD"]


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200
    return s


class TestClientCSVTemplate:
    def test_template_csv_downloadable(self, session):
        r = session.get(f"{BASE_URL}/api/app/clients/_template/csv")
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        text = r.text
        assert "name;surname;email" in text or "name,surname,email" in text
        assert "pref_operation" in text
        # BOM for Excel
        assert text.startswith("\ufeff") or "name" in text

    def test_template_includes_example_row(self, session):
        r = session.get(f"{BASE_URL}/api/app/clients/_template/csv")
        # second line should have a Mario Rossi example
        lines = r.text.strip().splitlines()
        assert len(lines) >= 2
        assert "Mario" in r.text or "Rossi" in r.text


class TestClientCSVImport:
    def test_import_two_clients(self, session):
        payload = {
            "rows": [
                {
                    "name": "ImportTest_A", "surname": "Verdi",
                    "email": "import_a@test.it", "phone": "+39 333 1234567",
                    "client_type": "buyer", "status": "new",
                    "pref_operation": "sale", "pref_cities": "Roma;Milano",
                    "pref_property_types": "appartamento", "pref_price_max": "300000",
                    "gdpr_consent": "true",
                },
                {
                    "name": "ImportTest_B", "surname": "Neri",
                    "client_type": "seller", "status": "new",
                },
            ]
        }
        r = session.post(f"{BASE_URL}/api/app/clients/import/csv", json=payload)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["imported"] == 2
        assert d["total_rows"] == 2
        assert d["status"] == "completed"
        # cleanup
        list_r = session.get(f"{BASE_URL}/api/app/clients?q=ImportTest_")
        for c in (list_r.json().get("items") or []):
            if c.get("name", "").startswith("ImportTest_"):
                session.delete(f"{BASE_URL}/api/app/clients/{c['id']}")

    def test_import_rejects_missing_name(self, session):
        r = session.post(f"{BASE_URL}/api/app/clients/import/csv", json={
            "rows": [{"surname": "NoName", "email": "x@y.it"}],
        })
        assert r.status_code == 200
        d = r.json()
        assert d["imported"] == 0
        assert len(d["errors"]) == 1
        assert "nome" in d["errors"][0]["message"].lower()
