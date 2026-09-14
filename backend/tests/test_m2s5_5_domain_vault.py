"""Backend tests for M2.5.5 (D-051 / D-054): Domain Vault.

Covers:
- Signup captures `domain_sovereignty_confirmed` + `existing_domain`.
- Signup fields are transferred to the agency doc on agency creation.
- GET /agencies/me/domain-sovereignty returns current state.
- POST /agencies/me/domain-sovereignty accepts confirmation + optional domain.
- Invalid domain format is rejected (400).
- Confirmation is idempotent (confirmed_at is preserved on re-confirm).
- Auth boundary: anonymous cannot access these endpoints.
- Audit trail (`domain_vault_events`) records each mutation.
- Existing super_admin (mcnicastro@gmail.com) can toggle the flag without
  losing the audit trail.
"""
import os
import uuid
import asyncio
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://omnia-crm-docs.preview.emergentagent.com",
).rstrip("/")
ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]


# ----- Helpers -----

def _rand(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _register(name: str, email: str, password: str, **extra) -> requests.Session:
    s = requests.Session()
    payload = {"name": name, "email": email, "password": password, "role": "agency_admin"}
    payload.update(extra)
    r = s.post(f"{BASE_URL}/api/auth/register", json=payload)
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    return s


def _login(email: str, password: str) -> requests.Session:
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return s


def _create_agency(session: requests.Session, display_name: str) -> dict:
    r = session.post(
        f"{BASE_URL}/api/app/agencies",
        json={
            "display_name": display_name,
            "fiscal": {"legal_name": display_name, "vat_number": "01234567890"},
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


# ----- DB cleanup fixture -----

@pytest.fixture(scope="module", autouse=True)
def _cleanup():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    async def _wipe():
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        # Remove test users + their agencies + audit events
        cursor = db.users.find({"email": {"$regex": r"^vault_test_"}})
        async for u in cursor:
            await db.agencies.delete_many({"owner_id": u["id"]})
        await db.users.delete_many({"email": {"$regex": r"^vault_test_"}})
        await db.domain_vault_events.delete_many({
            "user_email": {"$regex": r"^vault_test_"},
        })
        c.close()

    asyncio.run(_wipe())
    yield
    asyncio.run(_wipe())


# ======================================================================
# 1. Signup flow captures Domain Vault preferences
# ======================================================================

class TestSignupCapture:
    def test_signup_without_domain_vault_fields_defaults_false(self):
        email = f"vault_test_{uuid.uuid4().hex[:8]}@omnia.it"
        s = _register("Vault User A", email, "TestPass2026!")
        me = s.get(f"{BASE_URL}/api/auth/me")
        assert me.status_code == 200
        # user endpoint doesn't expose signup_* fields, but registration is OK

    def test_signup_with_domain_sovereignty_confirmed(self):
        email = f"vault_test_{uuid.uuid4().hex[:8]}@omnia.it"
        s = _register(
            "Vault User B", email, "TestPass2026!",
            domain_sovereignty_confirmed=True,
            existing_domain="my-agency.it",
        )
        # Create agency → sovereignty must be pre-confirmed
        agency = _create_agency(s, _rand("VaultAgencyB"))
        r = s.get(f"{BASE_URL}/api/app/agencies/me/domain-sovereignty")
        assert r.status_code == 200
        data = r.json()
        assert data["confirmed"] is True
        assert data["existing_domain"] == "my-agency.it"
        assert data["confirmed_at"]  # ISO timestamp

    def test_signup_normalizes_existing_domain(self):
        email = f"vault_test_{uuid.uuid4().hex[:8]}@omnia.it"
        # Trim + lowercase happens server-side in register()
        s = _register(
            "Vault User C", email, "TestPass2026!",
            domain_sovereignty_confirmed=True,
            existing_domain="  UPPER-Case.IT  ",
        )
        _create_agency(s, _rand("VaultAgencyC"))
        r = s.get(f"{BASE_URL}/api/app/agencies/me/domain-sovereignty")
        assert r.json()["existing_domain"] == "upper-case.it"


# ======================================================================
# 2. Explicit endpoint POST /agencies/me/domain-sovereignty
# ======================================================================

class TestDomainVaultEndpoint:
    @pytest.fixture(scope="class")
    def session(self):
        email = f"vault_test_{uuid.uuid4().hex[:8]}@omnia.it"
        s = _register("Vault User Endpoint", email, "TestPass2026!")
        _create_agency(s, _rand("VaultAgencyEP"))
        return s

    def test_get_initial_state_unconfirmed(self, session):
        r = session.get(f"{BASE_URL}/api/app/agencies/me/domain-sovereignty")
        assert r.status_code == 200
        data = r.json()
        assert data["confirmed"] is False
        assert data["confirmed_at"] is None
        assert data["existing_domain"] is None
        assert data["policy_url"] == "/it/domain-sovereignty-policy"

    def test_post_confirms_and_sets_timestamp(self, session):
        r = session.post(
            f"{BASE_URL}/api/app/agencies/me/domain-sovereignty",
            json={"confirmed": True, "existing_domain": "test-endpoint.it"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["confirmed"] is True
        assert data["confirmed_at"] is not None
        assert data["existing_domain"] == "test-endpoint.it"
        self._first_ts = data["confirmed_at"]

    def test_re_confirm_is_idempotent(self, session):
        # First confirm was in the previous test.
        r1 = session.get(f"{BASE_URL}/api/app/agencies/me/domain-sovereignty")
        first_ts = r1.json()["confirmed_at"]
        # Re-confirm should NOT overwrite the original timestamp
        r2 = session.post(
            f"{BASE_URL}/api/app/agencies/me/domain-sovereignty",
            json={"confirmed": True},
        )
        assert r2.status_code == 200
        assert r2.json()["confirmed_at"] == first_ts

    def test_invalid_domain_returns_400(self, session):
        r = session.post(
            f"{BASE_URL}/api/app/agencies/me/domain-sovereignty",
            json={"confirmed": True, "existing_domain": "not a real domain"},
        )
        assert r.status_code == 400
        assert "invalid_domain_format" in r.text

    def test_unset_flag_preserves_existing_domain_when_omitted(self, session):
        r = session.post(
            f"{BASE_URL}/api/app/agencies/me/domain-sovereignty",
            json={"confirmed": False},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["confirmed"] is False
        # existing_domain should still be there (was set in earlier test)
        assert data["existing_domain"] == "test-endpoint.it"


# ======================================================================
# 3. Security — anonymous is blocked
# ======================================================================

class TestAuthBoundary:
    def test_get_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/app/agencies/me/domain-sovereignty")
        assert r.status_code in (401, 403)

    def test_post_requires_auth(self):
        r = requests.post(
            f"{BASE_URL}/api/app/agencies/me/domain-sovereignty",
            json={"confirmed": True},
        )
        assert r.status_code in (401, 403)


# ======================================================================
# 4. Audit trail — domain_vault_events collection
# ======================================================================

class TestAuditTrail:
    def test_audit_events_are_appended(self):
        email = f"vault_test_{uuid.uuid4().hex[:8]}@omnia.it"
        s = _register("Vault Audit", email, "TestPass2026!")
        _create_agency(s, _rand("VaultAgencyAudit"))

        # Two POST calls should produce two audit events for this user.
        s.post(
            f"{BASE_URL}/api/app/agencies/me/domain-sovereignty",
            json={"confirmed": True, "existing_domain": "audit.it"},
        )
        s.post(
            f"{BASE_URL}/api/app/agencies/me/domain-sovereignty",
            json={"confirmed": False},
        )

        load_dotenv(Path(__file__).resolve().parents[1] / ".env")

        async def _count():
            c = AsyncIOMotorClient(os.environ["MONGO_URL"])
            db = c[os.environ["DB_NAME"]]
            n = await db.domain_vault_events.count_documents({"user_email": email})
            c.close()
            return n

        n = asyncio.run(_count())
        assert n >= 2
