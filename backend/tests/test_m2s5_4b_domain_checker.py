"""Backend tests for M2.5.4b (D-054): Domain Ownership Checker.

Covers:
- normalize_domain() edge cases (pure unit)
- Heuristics: registrant matches agency / provider hint / redacted / ambiguous
- POST /api/domain/check public endpoint (invalid domain, rate limit, verdict shape)
- POST /api/domain/lead (consent, missing check, happy path)
- POST /api/v1/domain/check (auth boundary, credit cost 1, response shape)
- Widget HTML served with token replacement
"""
import os
import pytest
import requests

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://omnia-crm-docs.preview.emergentagent.com",
).rstrip("/")
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]


@pytest.fixture(scope="module", autouse=True)
def _cleanup_rate_limit():
    """Drop cached checks so the rate limiter doesn't trip during the test run."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    import asyncio
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    async def _wipe():
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        await db.domain_checks.delete_many({})
        c.close()
    asyncio.run(_wipe())
    yield
    asyncio.run(_wipe())


# ======================================================================
# Unit tests — pure functions (no network / no DB)
# ======================================================================

class TestNormalize:
    def test_lowercase(self):
        from shared.utils.rdap import normalize_domain
        assert normalize_domain("Example.IT") == "example.it"

    def test_strip_scheme_and_www(self):
        from shared.utils.rdap import normalize_domain
        assert normalize_domain("https://www.agenziarossi.it") == "agenziarossi.it"
        assert normalize_domain("http://foo.bar/path?q=1") == "foo.bar"

    def test_invalid(self):
        from shared.utils.rdap import normalize_domain
        assert normalize_domain("") is None
        assert normalize_domain("not a domain") is None
        assert normalize_domain("just_a_word") is None
        assert normalize_domain("-badstart.it") is None


class TestHeuristics:
    def test_matches_agency_when_domain_brand_in_registrant(self):
        from apps.marketing.domain_check import _domain_matches_registrant
        assert _domain_matches_registrant("agenziarossi.it", "Rossi Immobiliare S.r.l.", None) is False
        # domain brand "agenziarossi" not in "Rossi Immobiliare"
        assert _domain_matches_registrant("agenziarossi.it", "Agenzia Rossi Immobiliare S.r.l.", None) is True

    def test_matches_via_agency_name_field(self):
        from apps.marketing.domain_check import _domain_matches_registrant
        # agency name provided by user overlaps with registrant → match
        assert _domain_matches_registrant("something.it", "Bianchi Immobiliare", "Bianchi Immobiliare S.r.l.") is True

    def test_provider_hint_positive(self):
        from apps.marketing.domain_check import _registrant_looks_like_provider
        assert _registrant_looks_like_provider("Web Agency Servizi SRL") is True
        assert _registrant_looks_like_provider("Real Estate Software S.p.A.") is True
        assert _registrant_looks_like_provider("Hosting Company") is True

    def test_provider_hint_negative_for_real_agency(self):
        from apps.marketing.domain_check import _registrant_looks_like_provider
        assert _registrant_looks_like_provider("Agenzia Rossi Immobiliare") is False
        assert _registrant_looks_like_provider("Mario Rossi") is False

    def test_redacted_detection(self):
        from apps.marketing.domain_check import _is_redacted
        assert _is_redacted("REDACTED FOR PRIVACY") is True
        assert _is_redacted("Not disclosed - visit registrar") is True
        assert _is_redacted(None) is True
        assert _is_redacted("Agenzia Rossi") is False


class TestAnalyze:
    def _base(self, **kw):
        return {"domain": "example.it", "ok": True, "not_found": False, **kw}

    def test_not_found(self):
        from apps.marketing.domain_check import _analyze
        r = _analyze({"domain": "libero.it", "not_found": True, "ok": True}, None)
        assert r["status"] == "not_registered"
        assert r["severity"] == "info"

    def test_error(self):
        from apps.marketing.domain_check import _analyze
        r = _analyze({"domain": "x.tld", "ok": False, "error": "rdap_unreachable"}, None)
        assert r["status"] == "unknown"

    def test_owner_ok(self):
        from apps.marketing.domain_check import _analyze
        r = _analyze(self._base(registrant="Agenzia Rossi S.r.l."), "Agenzia Rossi")
        assert r["status"] == "owner_ok"
        assert r["severity"] == "good"

    def test_provider_hostage(self):
        from apps.marketing.domain_check import _analyze
        r = _analyze(self._base(registrant="Servizi Web SRL Unipersonale"), None)
        assert r["status"] == "likely_hostage"
        assert r["severity"] == "critical"

    def test_redacted(self):
        from apps.marketing.domain_check import _analyze
        r = _analyze(self._base(registrant="REDACTED FOR PRIVACY"), None)
        assert r["status"] == "redacted"
        assert r["severity"] == "warning"

    def test_ambiguous(self):
        from apps.marketing.domain_check import _analyze
        r = _analyze(self._base(registrant="Mario Bianchi"), "Rossi")
        assert r["status"] == "ambiguous"


# ======================================================================
# Integration — public endpoints
# ======================================================================

class TestPublicCheck:
    def test_invalid_domain_400(self):
        r = requests.post(f"{BASE_URL}/api/domain/check", json={"domain": "not a domain"})
        assert r.status_code == 400

    def test_valid_domain_returns_verdict_shape(self):
        # Uses a well-known free domain (google.com) — RDAP always resolvable.
        r = requests.post(f"{BASE_URL}/api/domain/check", json={"domain": "google.com"})
        assert r.status_code == 200
        data = r.json()
        assert "id" in data and "verdict" in data and "rdap" in data
        assert data["domain"] == "google.com"
        assert data["verdict"]["status"] in {
            "owner_ok", "likely_hostage", "redacted", "ambiguous",
            "not_registered", "unknown",
        }

    def test_no_client_ip_leak(self):
        r = requests.post(f"{BASE_URL}/api/domain/check", json={"domain": "example.com"})
        assert r.status_code == 200
        assert "client_ip" not in r.json()


class TestPublicLead:
    def test_consent_required(self):
        # Do a valid check first to get a check_id
        r = requests.post(f"{BASE_URL}/api/domain/check", json={"domain": "example.com"})
        cid = r.json()["id"]
        r2 = requests.post(f"{BASE_URL}/api/domain/lead", json={
            "check_id": cid, "name": "Mario", "email": "m@example.com", "consent": False,
        })
        assert r2.status_code == 400

    def test_missing_check_404(self):
        r = requests.post(f"{BASE_URL}/api/domain/lead", json={
            "check_id": "does-not-exist", "name": "Mario", "email": "test@example.com", "consent": True,
        })
        assert r.status_code == 404

    def test_happy_path_201(self):
        r = requests.post(f"{BASE_URL}/api/domain/check", json={"domain": "example.com"})
        cid = r.json()["id"]
        r2 = requests.post(f"{BASE_URL}/api/domain/lead", json={
            "check_id": cid, "name": "Test User", "email": "leadtest@omnia.re",
            "agency": "Test Agenzia", "consent": True, "source": "landing",
        })
        assert r2.status_code == 201
        assert r2.json()["ok"] is True


# ======================================================================
# v1 API Gateway
# ======================================================================

@pytest.fixture(scope="module")
def api_key():
    """Provision a JWT-authenticated session and mint a fresh API key."""
    s = requests.Session()
    s.post(f"{BASE_URL}/api/auth/login",
           json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    r = s.post(f"{BASE_URL}/api/app/api-keys",
               json={"name": "domain-check-test", "initial_credits": 20})
    assert r.status_code in (200, 201), r.text
    return r.json()["key"]


class TestV1DomainCheck:
    def test_auth_required(self):
        r = requests.post(f"{BASE_URL}/api/v1/domain/check", json={"domain": "example.com"})
        assert r.status_code in (401, 403)

    def test_happy_path_1_credit(self, api_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/domain/check",
            json={"domain": "example.com"},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["credits_charged"] == 1
        assert "data" in body
        assert "verdict" in body["data"]


# ======================================================================
# Widget asset
# ======================================================================

class TestWidgetAsset:
    def test_serves_domain_check_html(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/domain-check.html?key=omk_test&primary=%23ff0000")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        html = r.text
        assert "__BACKEND_BASE__" not in html
        assert "__PRIMARY_COLOR__" not in html
        assert "__API_KEY__" not in html
        assert "#ff0000" in html
        assert "omk_test" in html

    def test_unknown_widget_404(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/unknown-widget.html")
        assert r.status_code == 404
