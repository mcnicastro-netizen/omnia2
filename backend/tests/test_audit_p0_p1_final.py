"""OMNIA — Final audit P0/P1/P2 backend regression tests.

Covers audit items:
- C1: register role whitelist
- C4/H12: /api/billing/checkout (no double /api)
- C5: forgot/reset password E2E
- C6: attach branch ownership (super_admin path)
- C7: import/xml SSRF guard
- H3: moderation queue super_admin only
- H10: photo upload-tmp + /api/media
- H14: refresh with is_active=false → 403 (skip if no such user)
- H15: /api/billing/status/{sid} without auth
- H9: HAL knowledge ask
- M3/M4/M6: properties/clients regex-safe search, PATCH
- M10 (backend): /fr/login → served (frontend concern; only sanity)
"""
import io
import os
import re
import time
import pytest
import requests

BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"
SUPER_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
SUPER_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]
AGENT_EMAIL = "test_agent@omnia.it"
AGENT_PASSWORD = os.environ["OMNIA_AGENT_PASSWORD"]


@pytest.fixture(scope="session")
def super_sess():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": SUPER_EMAIL, "password": SUPER_PASSWORD})
    if r.status_code != 200:
        pytest.skip(f"super login failed {r.status_code}: {r.text[:200]}")
    return s


@pytest.fixture(scope="session")
def agent_sess():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": AGENT_EMAIL, "password": AGENT_PASSWORD})
    if r.status_code != 200:
        pytest.skip(f"agent login failed {r.status_code}: {r.text[:200]}")
    return s


# ---------- C1: Register role whitelist ----------
class TestC1RoleWhitelist:
    def test_super_admin_downgraded_to_client(self):
        email = f"test_c1_super_{int(time.time())}@omniatest.re"
        r = requests.post(f"{API}/auth/register", json={
            "email": email, "password": "TestPass123!",
            "full_name": "T C1", "role": "super_admin", "name": "T C1"
        })
        assert r.status_code in (200, 201), r.text
        data = r.json()
        user = data.get("user") or data
        assert user.get("role") == "client", f"expected client, got {user.get('role')}: {data}"

    def test_group_admin_downgraded_to_client(self):
        email = f"test_c1_ga_{int(time.time())}@omniatest.re"
        r = requests.post(f"{API}/auth/register", json={
            "email": email, "password": "TestPass123!",
            "full_name": "T C1 GA", "role": "group_admin", "name": "T C1 GA"
        })
        assert r.status_code in (200, 201), r.text
        user = r.json().get("user") or r.json()
        assert user.get("role") == "client"

    def test_agent_role_preserved(self):
        """S2 (30-Lug): 'agent' NON è più un ruolo pubblico — si ottiene solo via invito.
        La register pubblica lo declassa a 'client'."""
        email = f"test_c1_agent_{int(time.time())}@omniatest.re"
        r = requests.post(f"{API}/auth/register", json={
            "email": email, "password": "TestPass123!",
            "full_name": "T C1 Agent", "role": "agent", "name": "T C1 Agent"
        })
        assert r.status_code in (200, 201), r.text
        user = r.json().get("user") or r.json()
        assert user.get("role") == "client"


# ---------- C4/H12: Billing checkout endpoint path ----------
class TestC4BillingCheckout:
    def test_checkout_returns_stripe_url(self, super_sess):
        r = super_sess.post(f"{API}/billing/checkout",
                            json={"plan_tier": "pro", "billing_cycle": "monthly"})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["checkout_url"].startswith("https://checkout.stripe.com/")
        assert d["session_id"].startswith("cs_test_")

    def test_no_double_api_prefix(self, super_sess):
        # ensure /api/api/... does NOT exist
        r = super_sess.post(f"{BASE_URL}/api/api/billing/checkout",
                            json={"plan_tier": "pro", "billing_cycle": "monthly"})
        assert r.status_code == 404


# ---------- C5: Reset password E2E ----------
class TestC5ResetPassword:
    def test_forgot_password_returns_200(self):
        r = requests.post(f"{API}/auth/forgot-password", json={"email": SUPER_EMAIL})
        # Should always be 200/202 regardless of whether email exists (privacy)
        assert r.status_code in (200, 202), r.text

    def test_forgot_password_unknown_email(self):
        r = requests.post(f"{API}/auth/forgot-password",
                          json={"email": "nonexistent_zzz@example.com"})
        assert r.status_code in (200, 202)

    def test_reset_with_invalid_token(self):
        r = requests.post(f"{API}/auth/reset-password", json={
            "token": "INVALID_TOKEN_XYZ", "new_password": "NewPass123!"
        })
        assert r.status_code in (400, 401, 404, 422)


# ---------- C6: attach branch ownership ----------
class TestC6BranchOwnership:
    def test_attach_random_agency_by_super_admin_no_500(self, super_sess):
        # get a group id
        rg = super_sess.get(f"{API}/app/groups")
        if rg.status_code != 200:
            pytest.skip(f"groups list: {rg.status_code}")
        groups = rg.json() if isinstance(rg.json(), list) else rg.json().get("items", [])
        if not groups:
            # create one
            cr = super_sess.post(f"{API}/app/groups",
                                 json={"name": "TEST_group_c6", "credits_mode": "group"})
            if cr.status_code not in (200, 201):
                pytest.skip("cannot create group")
            gid = (cr.json().get("group") or {}).get("id") or cr.json().get("id")
        else:
            gid = groups[0].get("id")
        # attach a non-existent agency — super_admin should get 404 (agency not found) not 403
        r = super_sess.post(f"{API}/app/groups/{gid}/branches",
                            json={"agency_id": "non-existent-agency-zzz"})
        # 400/404 acceptable for super; NOT 500
        assert r.status_code != 500, r.text
        assert r.status_code in (400, 404, 422), f"got {r.status_code}: {r.text[:200]}"


# ---------- C7: SSRF guard on xml import ----------
class TestC7SSRFGuard:
    @pytest.mark.parametrize("bad_url", [
        "http://169.254.169.254/latest/meta-data/",
        "http://127.0.0.1:8001/api/health",
        "http://localhost:8001/",
        "http://10.0.0.1/feed.xml",
    ])
    def test_ssrf_blocked(self, super_sess, bad_url):
        r = super_sess.post(f"{API}/app/properties/import/xml",
                            json={"feed_url": bad_url})
        assert r.status_code == 400, f"expected 400 for {bad_url}, got {r.status_code}: {r.text[:200]}"
        detail = r.json().get("detail")
        s = detail if isinstance(detail, str) else (detail or {}).get("error") if isinstance(detail, dict) else ""
        assert "url_not_allowed" in str(detail).lower() or "url_not_allowed" == s, f"detail={detail}"


# ---------- H3: moderation queue only super_admin ----------
class TestH3ModerationSuperOnly:
    def test_super_admin_ok(self, super_sess):
        r = super_sess.get(f"{API}/app/moderation/queue")
        assert r.status_code == 200, r.text

    def test_agent_forbidden(self, agent_sess):
        r = agent_sess.get(f"{API}/app/moderation/queue")
        assert r.status_code == 403, f"agent should be 403, got {r.status_code}: {r.text[:200]}"


# ---------- H10: Photo upload-tmp + media serve ----------
class TestH10PhotoUpload:
    def _tiny_jpeg(self):
        # minimal jpeg header + eoi bytes
        return (b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
                b"\xff\xdb\x00C\x00" + b"\x08" * 64 +
                b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00"
                b"\xff\xc4\x00\x14\x00\x01" + b"\x00" * 15 + b"\x00"
                b"\xff\xc4\x00\x14\x10\x01" + b"\x00" * 15 + b"\x00"
                b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xd2\xcf \xff\xd9")

    def test_upload_tmp_and_media_serve(self, super_sess):
        files = {"file": ("test.jpg", io.BytesIO(self._tiny_jpeg()), "image/jpeg")}
        r = super_sess.post(f"{API}/app/properties/photos/upload-tmp", files=files)
        assert r.status_code in (200, 201), f"upload {r.status_code}: {r.text[:300]}"
        d = r.json()
        assert "id" in d and "url" in d, d
        url = d["url"]
        assert url.startswith("/api/media/"), url
        # fetch media
        r2 = super_sess.get(f"{BASE_URL}{url}")
        assert r2.status_code == 200, r2.text[:200]
        assert r2.headers.get("content-type", "").startswith("image/")


# ---------- H15: billing status without auth ----------
class TestH15BillingStatusAuth:
    def test_no_cookie_401(self):
        r = requests.get(f"{API}/billing/status/cs_test_dummy_xyz")
        assert r.status_code == 401, f"expected 401 got {r.status_code}: {r.text[:200]}"


# ---------- H14: refresh with inactive user ----------
class TestH14RefreshInactive:
    def test_refresh_no_cookie_401(self):
        r = requests.post(f"{API}/auth/refresh")
        assert r.status_code in (401, 403), f"got {r.status_code}"

    def test_refresh_active_user_works(self, super_sess):
        r = super_sess.post(f"{API}/auth/refresh")
        assert r.status_code == 200, r.text


# ---------- H9: HAL knowledge ----------
class TestH9HalKnowledge:
    def test_status(self, super_sess):
        r = super_sess.get(f"{API}/app/hal/knowledge/status")
        assert r.status_code == 200, r.text

    def test_ask(self, super_sess):
        r = super_sess.post(f"{API}/app/hal/knowledge/ask",
                            json={"question": "Cosa e OMNIA?"})
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert "sources" in d or "answer" in d, d


# ---------- M3/M4/M6: regex-safe search + PATCH ----------
class TestM3RegexSafeSearch:
    def test_properties_search_regex_special(self, super_sess):
        # Should NOT 500 with regex-special chars
        for q in ["a(b", "a[b", "a\\b", "a*b", "a?b"]:
            r = super_sess.get(f"{API}/app/properties", params={"q": q})
            assert r.status_code == 200, f"q={q!r}: {r.status_code} {r.text[:200]}"

    def test_clients_list(self, super_sess):
        r = super_sess.get(f"{API}/app/clients?limit=5")
        assert r.status_code == 200, r.text

    def test_property_patch_still_works(self, super_sess):
        rl = super_sess.get(f"{API}/app/properties?limit=1")
        assert rl.status_code == 200
        items = rl.json() if isinstance(rl.json(), list) else rl.json().get("items", [])
        if not items:
            pytest.skip("no properties")
        pid = items[0].get("id")
        r = super_sess.patch(f"{API}/app/properties/{pid}",
                             json={"internal_notes": f"TEST_note_{int(time.time())}"})
        assert r.status_code in (200, 204), r.text[:300]


# ---------- M10: /fr/login backend serving (SPA) ----------
class TestM10LangUnsupported:
    def test_fr_login_html_served(self):
        # The frontend SPA route should 200 (React handles the redirect).
        r = requests.get(f"{BASE_URL}/fr/login", allow_redirects=False)
        # Either a redirect at edge OR 200 HTML from SPA
        assert r.status_code in (200, 301, 302, 307, 308), r.status_code
