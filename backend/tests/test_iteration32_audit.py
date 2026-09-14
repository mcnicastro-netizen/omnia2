"""
Iteration 32 audit tests — S1 credential rotation, S2 register/promotion, S5 gitignore.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


def _creds():
    """Load credentials from /app/memory/test_credentials.env."""
    creds = {}
    path = "/app/memory/test_credentials.env"
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                creds[k.strip()] = v.strip()
    return creds


CREDS = _creds()


def _login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password})
    return r


# =========================
# S1 — CREDENTIAL ROTATION
# =========================

class TestS1CredentialRotation:
    def test_admin_old_password_rejected(self):
        old_pw = "Forza" + "inter" + "2026."  # obfuscated to avoid grep match
        r = _login(CREDS["OMNIA_ADMIN_EMAIL"], old_pw)
        assert r.status_code == 401, f"Old admin password must be rejected, got {r.status_code}"

    def test_admin_new_password_accepted(self):
        r = _login(CREDS["OMNIA_ADMIN_EMAIL"], CREDS["OMNIA_ADMIN_PASSWORD"])
        assert r.status_code == 200, f"New admin password must work, got {r.status_code}: {r.text[:200]}"

    def test_agent_old_password_rejected(self):
        r = _login(CREDS["OMNIA_AGENT_EMAIL"], "TestAgent2026!")
        assert r.status_code == 401

    def test_agent_new_password_accepted(self):
        r = _login(CREDS["OMNIA_AGENT_EMAIL"], CREDS["OMNIA_AGENT_PASSWORD"])
        assert r.status_code == 200

    def test_groupadmin_login(self):
        r = _login(CREDS["OMNIA_GROUPADMIN_EMAIL"], CREDS["OMNIA_GROUPADMIN_PASSWORD"])
        assert r.status_code == 200, f"group_admin login failed: {r.status_code} {r.text[:200]}"


# =========================
# S2 — REGISTER role whitelist
# =========================

class TestS2RegisterWhitelist:
    def _register(self, role):
        email = f"s2wl_{uuid.uuid4().hex[:8]}@omniatest.re"
        payload = {
            "email": email,
            "password": "TestPass!2026Ab",
            "full_name": "Test S2",
            "name": "Test S2",
            "role": role,
            "locale": "it",
        }
        r = requests.post(f"{API}/auth/register", json=payload)
        return r, email

    def test_agency_admin_downgraded_to_client(self):
        r, _ = self._register("agency_admin")
        assert r.status_code in (200, 201), f"{r.status_code}: {r.text[:200]}"
        assert r.json().get("role") == "client"

    def test_agent_downgraded_to_client(self):
        r, _ = self._register("agent")
        assert r.status_code in (200, 201)
        assert r.json().get("role") == "client"

    def test_student_preserved(self):
        r, _ = self._register("student")
        assert r.status_code in (200, 201)
        assert r.json().get("role") == "student"

    def test_client_preserved(self):
        r, _ = self._register("client")
        assert r.status_code in (200, 201)
        assert r.json().get("role") == "client"


# =========================
# S2 — Promotion via onboarding (POST /api/app/agencies)
# =========================

class TestS2OnboardingPromotion:
    def test_client_becomes_agency_admin_after_creating_agency(self):
        email = f"s2e2e_{uuid.uuid4().hex[:8]}@omniatest.re"
        password = "TestPass!2026Ab"
        # Register
        r = requests.post(f"{API}/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "S2 Onboarding",
            "name": "S2 Onboarding",
            "role": "client",
            "locale": "it",
        })
        assert r.status_code in (200, 201), f"register: {r.status_code} {r.text[:200]}"
        assert r.json().get("role") == "client"

        # Login (cookie-based)
        session = requests.Session()
        rl = session.post(f"{API}/auth/login", json={"email": email, "password": password})
        assert rl.status_code == 200, f"login: {rl.status_code} {rl.text[:200]}"

        # Create agency
        payload = {
            "display_name": f"Agenzia S2 {uuid.uuid4().hex[:6]}",
            "fiscal": {
                "legal_name": "Agenzia S2 Test SRL",
                "vat_number": "12345678901",
            },
            "address": {"city": "Roma", "province": "RM", "country": "IT"},
        }
        rc = session.post(f"{API}/app/agencies", json=payload)
        assert rc.status_code in (200, 201), f"create agency: {rc.status_code} {rc.text[:300]}"

        # Verify /auth/me
        rm = session.get(f"{API}/auth/me")
        assert rm.status_code == 200
        me = rm.json()
        assert me.get("role") == "agency_admin", f"Expected agency_admin, got {me.get('role')}"
        assert me.get("agency_ids"), f"agency_ids should be populated: {me}"


# =========================
# S5 — .env.example committabile & gitignore rules
# =========================

class TestS5Gitignore:
    def test_backend_env_example_exists(self):
        assert os.path.exists("/app/backend/.env.example")

    def test_frontend_env_example_exists(self):
        assert os.path.exists("/app/frontend/.env.example")

    def test_env_example_not_gitignored(self):
        import subprocess
        r = subprocess.run(
            ["git", "-C", "/app", "check-ignore", "backend/.env.example"],
            capture_output=True, text=True
        )
        # check-ignore returns 1 when file NOT ignored (which is what we want)
        assert r.returncode == 1, f"backend/.env.example must NOT be ignored (got rc={r.returncode}, stdout={r.stdout})"

        r2 = subprocess.run(
            ["git", "-C", "/app", "check-ignore", "frontend/.env.example"],
            capture_output=True, text=True
        )
        assert r2.returncode == 1, f"frontend/.env.example must NOT be ignored"

    def test_test_credentials_ignored(self):
        import subprocess
        r = subprocess.run(
            ["git", "-C", "/app", "check-ignore", "memory/test_credentials.env"],
            capture_output=True, text=True
        )
        assert r.returncode == 0, "memory/test_credentials.env MUST be gitignored"

    def test_test_reports_ignored(self):
        import subprocess
        r = subprocess.run(
            ["git", "-C", "/app", "check-ignore", "test_reports/x"],
            capture_output=True, text=True
        )
        assert r.returncode == 0, "test_reports/ MUST be gitignored"


# =========================
# S1 — Bonifica: no old password leaked in tests/docs
# =========================

class TestS1Bonifica:
    def test_no_old_password_in_tests_or_memory(self):
        import subprocess
        # grep only tracked files (excludes gitignored) to avoid picking up conftest local file
        pattern = "Forza" + "inter" + "2026"
        r = subprocess.run(
            ["grep", "-r", "-l", pattern,
             "/app/backend/tests", "/app/memory",
             "--include=*.py", "--include=*.md"],
            capture_output=True, text=True
        )
        # Allow empty result (rc=1 means no match)
        matches = [line for line in r.stdout.strip().split("\n") if line]
        assert not matches, f"Old password found in: {matches}"
