"""Backend tests for M2.S6 Custom Domain workflow."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASS = os.environ["OMNIA_ADMIN_PASSWORD"]


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASS})
    assert r.status_code == 200
    return s


@pytest.fixture
def cleanup_domain(session):
    yield
    session.delete(f"{BASE_URL}/api/app/website/domain")


class TestRequestDomain:
    def test_request_creates_pending(self, session, cleanup_domain):
        r = session.post(f"{BASE_URL}/api/app/website/domain/request",
                         json={"domain": "www.nicastroimmobiliare.it"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["domain"] == "www.nicastroimmobiliare.it"
        assert d["status"] == "pending"
        assert d["dns_instructions"]["txt_record"]["host"].startswith("_omnia-challenge.")
        assert d["dns_instructions"]["cname_record"]["value"] == "agencies.omniarealestateecosystem.it"
        token = d["dns_instructions"]["txt_record"]["value"]
        assert token.startswith("omnia-verify=")
        assert len(token) > len("omnia-verify=") + 20

    def test_rejects_invalid_domain(self, session):
        r = session.post(f"{BASE_URL}/api/app/website/domain/request", json={"domain": "not a domain!"})
        assert r.status_code == 400
        assert "invalid_domain" in r.text

    def test_rejects_reserved_domain(self, session):
        r = session.post(f"{BASE_URL}/api/app/website/domain/request",
                         json={"domain": "test.omniarealestateecosystem.it"})
        assert r.status_code == 400
        assert "reserved_domain" in r.text

    def test_normalizes_url(self, session, cleanup_domain):
        # Should strip https:// and trailing path
        r = session.post(f"{BASE_URL}/api/app/website/domain/request",
                         json={"domain": "https://www.nicastroimmobiliare.it/some/path"})
        assert r.status_code == 200
        assert r.json()["domain"] == "www.nicastroimmobiliare.it"

    def test_regenerates_token_on_resubmit(self, session, cleanup_domain):
        r1 = session.post(f"{BASE_URL}/api/app/website/domain/request",
                          json={"domain": "www.example.com"})
        t1 = r1.json()["dns_instructions"]["txt_record"]["value"]
        r2 = session.post(f"{BASE_URL}/api/app/website/domain/request",
                          json={"domain": "www.example.com"})
        t2 = r2.json()["dns_instructions"]["txt_record"]["value"]
        assert t1 != t2  # token regenerated


class TestVerifyDomain:
    def test_verify_returns_error_without_dns(self, session, cleanup_domain):
        session.post(f"{BASE_URL}/api/app/website/domain/request",
                     json={"domain": "definitely-not-configured.example.test"})
        r = session.post(f"{BASE_URL}/api/app/website/domain/verify")
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is False
        assert d["status"] == "error"
        assert len(d["errors"]) >= 1

    def test_verify_without_request_returns_400(self, session, cleanup_domain):
        # Make sure no domain is set
        session.delete(f"{BASE_URL}/api/app/website/domain")
        r = session.post(f"{BASE_URL}/api/app/website/domain/verify")
        assert r.status_code == 400


class TestGetState:
    def test_get_returns_null_when_no_domain(self, session, cleanup_domain):
        session.delete(f"{BASE_URL}/api/app/website/domain")
        r = session.get(f"{BASE_URL}/api/app/website/domain")
        assert r.status_code == 200
        d = r.json()
        assert d["domain"] is None
        assert d["cname_target"] == "agencies.omniarealestateecosystem.it"

    def test_get_returns_state_after_request(self, session, cleanup_domain):
        session.post(f"{BASE_URL}/api/app/website/domain/request",
                     json={"domain": "test-cd.example.com"})
        r = session.get(f"{BASE_URL}/api/app/website/domain")
        d = r.json()
        assert d["domain"] == "test-cd.example.com"
        assert d["status"] == "pending"


class TestDelete:
    def test_delete_clears_domain(self, session):
        session.post(f"{BASE_URL}/api/app/website/domain/request",
                     json={"domain": "delete-test.example.com"})
        r = session.delete(f"{BASE_URL}/api/app/website/domain")
        assert r.status_code == 200
        r2 = session.get(f"{BASE_URL}/api/app/website/domain")
        assert r2.json()["domain"] is None


class TestAdminPending:
    def test_super_admin_can_list_pending(self, session, cleanup_domain):
        session.post(f"{BASE_URL}/api/app/website/domain/request",
                     json={"domain": "pending-test.example.com"})
        r = session.get(f"{BASE_URL}/api/app/website/domain/admin/pending")
        assert r.status_code == 200
        d = r.json()
        assert "items" in d
        assert "counts" in d
        assert d["total"] >= 1


class TestPermissions:
    def test_unauth_blocked(self):
        r = requests.post(f"{BASE_URL}/api/app/website/domain/request",
                          json={"domain": "x.example.com"})
        assert r.status_code in (401, 403)
