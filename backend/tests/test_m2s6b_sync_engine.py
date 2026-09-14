"""Backend tests for M2.6b (D-053): Sync Engine + Compliance Validator.

Covers:
- Compliance validator hard/soft rules (pure unit tests, no HTTP)
- POST /publishing/connections/{id}/sync-now (auth, 404, disabled)
- GET  /publishing/connections/{id}/compliance
- POST /publishing/sync/run-all (admin only)
- Sync log records + connection metadata updates after sync
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


@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login",
               json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200
    return s


@pytest.fixture(scope="module", autouse=True)
def cleanup(session):
    # Clean up before + after
    def _wipe():
        r = session.get(f"{BASE_URL}/api/app/publishing/connections")
        for c in r.json().get("items", []):
            session.delete(f"{BASE_URL}/api/app/publishing/connections/{c['id']}")
    _wipe()
    yield
    _wipe()


# -----------------------------
# Unit tests — validator itself
# -----------------------------

class TestComplianceValidator:
    def test_fully_compliant_property_is_publishable(self):
        from shared.validators.compliance import validate_property
        prop = {
            "operation": "sale", "price": 250000, "surface_sqm": 90,
            "city": "Napoli", "province": "NA",
            "title": "Bilocale luminoso ristrutturato",
            "description": "Bilocale ristrutturato di 90 mq al secondo piano con ascensore, doppia esposizione e balcone.",
            "energy": {"energy_class": "B", "ipe": 85.5},
            "photos": [{"url": "a"}, {"url": "b"}, {"url": "c"}, {"url": "d"}],
            "rooms": 3,
        }
        r = validate_property(prop)
        assert r["publishable"] is True
        assert r["hard_violations"] == []

    def test_missing_price_hard_blocks(self):
        from shared.validators.compliance import validate_property
        r = validate_property({"operation": "sale", "surface_sqm": 90,
                               "energy": {"energy_class": "B"},
                               "photos": [{"url": "a"}, {"url": "b"}, {"url": "c"}],
                               "city": "Milano", "province": "MI"})
        assert r["publishable"] is False
        assert "missing_price" in r["hard_violations"]

    def test_rent_operation_needs_rent_monthly(self):
        from shared.validators.compliance import validate_property
        r = validate_property({"operation": "rent", "rent_monthly": 800,
                               "surface_sqm": 60,
                               "energy": {"energy_class": "C"},
                               "photos": [{"url": "a"}, {"url": "b"}, {"url": "c"}],
                               "city": "Roma", "province": "RM"})
        assert r["publishable"] is True

    def test_missing_energy_class_blocks(self):
        from shared.validators.compliance import validate_property
        r = validate_property({"operation": "sale", "price": 200000, "surface_sqm": 80,
                               "photos": [{"url": "a"}, {"url": "b"}, {"url": "c"}],
                               "city": "Torino", "province": "TO"})
        assert r["publishable"] is False
        assert "missing_energy_class" in r["hard_violations"]

    def test_invalid_energy_class_blocks(self):
        from shared.validators.compliance import validate_property
        r = validate_property({"operation": "sale", "price": 200000, "surface_sqm": 80,
                               "energy": {"energy_class": "Z9"},
                               "photos": [{"url": "a"}, {"url": "b"}, {"url": "c"}],
                               "city": "Firenze", "province": "FI"})
        assert "invalid_energy_class" in r["hard_violations"]

    def test_less_than_3_photos_blocks(self):
        from shared.validators.compliance import validate_property
        r = validate_property({"operation": "sale", "price": 200000, "surface_sqm": 80,
                               "energy": {"energy_class": "A2"},
                               "photos": [{"url": "a"}, {"url": "b"}],
                               "city": "Bologna", "province": "BO"})
        assert "less_than_3_photos" in r["hard_violations"]

    def test_missing_address_blocks(self):
        from shared.validators.compliance import validate_property
        r = validate_property({"operation": "sale", "price": 200000, "surface_sqm": 80,
                               "energy": {"energy_class": "B"},
                               "photos": [{"url": "a"}, {"url": "b"}, {"url": "c"}]})
        assert "missing_address" in r["hard_violations"]

    def test_soft_warnings_do_not_block(self):
        from shared.validators.compliance import validate_property
        r = validate_property({"operation": "sale", "price": 200000, "surface_sqm": 80,
                               "title": "corto", "description": "breve",
                               "energy": {"energy_class": "B"},
                               "photos": [{"url": "a"}, {"url": "b"}, {"url": "c"}],
                               "city": "Palermo", "province": "PA"})
        assert r["publishable"] is True
        assert "title_too_short" in r["soft_warnings"]
        assert "description_too_short" in r["soft_warnings"]

    def test_summarize_aggregates(self):
        from shared.validators.compliance import summarize_agency_compliance
        props = [
            {"operation": "sale", "price": 100, "surface_sqm": 50,
             "energy": {"energy_class": "B"}, "photos": [{"url": "a"}, {"url": "b"}, {"url": "c"}],
             "city": "X", "province": "Y", "title": "A" * 20,
             "description": "D" * 60, "rooms": 2},
            {"operation": "sale", "surface_sqm": 50},  # blocked: missing everything
            {"operation": "sale", "price": 200, "surface_sqm": 50,
             "energy": {"energy_class": "C"}, "photos": [{"url": "a"}],
             "city": "X", "province": "Y"},  # blocked: less than 3 photos + soft warnings
        ]
        s = summarize_agency_compliance(props)
        assert s["total"] == 3
        assert s["publishable"] == 1
        assert s["blocked"] == 2
        # Most common blocking reason should surface
        reasons = dict(s["top_hard_reasons"])
        assert "less_than_3_photos" in reasons


# -----------------------------
# Integration — sync endpoints
# -----------------------------

class TestSyncEndpoints:
    @pytest.fixture(autouse=True)
    def _make_conn(self, session):
        # Activate one PULL (bakeca) and one PUSH (facebook-marketplace)
        for slug, creds in [("bakeca", {"email": "test@x.it"}),
                            ("facebook-marketplace", {"page_id": "1", "access_token": "tok"})]:
            r = session.post(f"{BASE_URL}/api/app/publishing/connections",
                             json={"portal_slug": slug, "credentials": creds})
            assert r.status_code in (201, 409)  # 409 if leftover

    def _conn(self, session, slug):
        r = session.get(f"{BASE_URL}/api/app/publishing/connections")
        return next(c for c in r.json()["items"] if c["portal_slug"] == slug)

    def test_sync_now_pull_portal(self, session):
        c = self._conn(session, "bakeca")
        r = session.post(f"{BASE_URL}/api/app/publishing/connections/{c['id']}/sync-now")
        assert r.status_code == 200
        d = r.json()
        assert "publishable" in d and "blocked" in d
        assert d["integration_type"] == "feed_pull"

    def test_sync_now_push_portal_simulated(self, session):
        c = self._conn(session, "facebook-marketplace")
        r = session.post(f"{BASE_URL}/api/app/publishing/connections/{c['id']}/sync-now")
        assert r.status_code == 200
        assert r.json()["integration_type"] == "api_push"

    def test_sync_now_404_unknown_id(self, session):
        r = session.post(f"{BASE_URL}/api/app/publishing/connections/does-not-exist/sync-now")
        assert r.status_code == 404

    def test_sync_now_409_when_disabled(self, session):
        c = self._conn(session, "bakeca")
        session.patch(f"{BASE_URL}/api/app/publishing/connections/{c['id']}",
                      json={"status": "disabled"})
        r = session.post(f"{BASE_URL}/api/app/publishing/connections/{c['id']}/sync-now")
        assert r.status_code == 409
        # Restore active for later tests
        session.patch(f"{BASE_URL}/api/app/publishing/connections/{c['id']}",
                      json={"status": "active"})

    def test_sync_updates_last_sync_at(self, session):
        c_before = self._conn(session, "bakeca")
        session.post(f"{BASE_URL}/api/app/publishing/connections/{c_before['id']}/sync-now")
        c_after = self._conn(session, "bakeca")
        assert c_after.get("last_sync_at") is not None
        assert c_after.get("next_sync_at") is not None

    def test_sync_writes_log(self, session):
        c = self._conn(session, "bakeca")
        session.post(f"{BASE_URL}/api/app/publishing/connections/{c['id']}/sync-now")
        logs = session.get(
            f"{BASE_URL}/api/app/publishing/connections/{c['id']}/logs?limit=5"
        ).json()["items"]
        assert len(logs) >= 1
        assert logs[0]["status"] in ("success", "partial", "failed")
        assert logs[0]["trigger"] == "manual"


class TestCompliance:
    def _conn(self, session, slug):
        r = session.get(f"{BASE_URL}/api/app/publishing/connections")
        return next(c for c in r.json()["items"] if c["portal_slug"] == slug)

    def test_compliance_endpoint(self, session):
        # Ensure at least one connection exists
        session.post(f"{BASE_URL}/api/app/publishing/connections",
                     json={"portal_slug": "bakeca", "credentials": {"email": "x@y.it"}})
        c = self._conn(session, "bakeca")
        r = session.get(f"{BASE_URL}/api/app/publishing/connections/{c['id']}/compliance")
        assert r.status_code == 200
        d = r.json()
        assert "summary" in d
        assert "blocked_details" in d
        assert "total" in d["summary"]

    def test_compliance_404(self, session):
        r = session.get(f"{BASE_URL}/api/app/publishing/connections/nope/compliance")
        assert r.status_code == 404


class TestAdminSyncAll:
    def test_run_all_super_admin(self, session):
        r = session.post(f"{BASE_URL}/api/app/publishing/sync/run-all")
        assert r.status_code == 200
        d = r.json()
        assert "triggered_at" in d
        assert "results" in d
        assert isinstance(d["results"], list)


class TestAuthBoundary:
    def test_sync_now_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/app/publishing/connections/x/sync-now")
        assert r.status_code in (401, 403)

    def test_run_all_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/app/publishing/sync/run-all")
        assert r.status_code in (401, 403)
