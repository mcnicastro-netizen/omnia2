"""Regression tests for OMNIA Fase 2-3 refactor (iteration 31).
Covers: M5 multi-agency, L12 refresh revocation, M23 async XML import,
M24 fascicolo multipart, M13 portals removal, public photo endpoint fix.
"""
import io
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
SUPER_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
SUPER_PASS = os.environ["OMNIA_ADMIN_PASSWORD"]


def _login(session: requests.Session, email: str, password: str) -> requests.Response:
    return session.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )


@pytest.fixture(scope="module")
def super_session() -> requests.Session:
    s = requests.Session()
    r = _login(s, SUPER_EMAIL, SUPER_PASS)
    assert r.status_code == 200, f"super login failed: {r.status_code} {r.text[:200]}"
    return s


# ---------- M5 multi-agency ----------
class TestM5MultiAgency:
    def test_my_agencies_shape(self, super_session):
        r = super_session.get(f"{BASE_URL}/api/auth/my-agencies", timeout=15)
        assert r.status_code == 200, r.text[:200]
        data = r.json()
        assert "items" in data and "active_agency_id" in data
        assert isinstance(data["items"], list)

    def test_active_agency_foreign_forbidden(self, super_session):
        r = super_session.post(
            f"{BASE_URL}/api/auth/active-agency",
            json={"agency_id": "00000000-0000-0000-0000-000000000000"},
            timeout=15,
        )
        assert r.status_code in (403, 404), r.text[:200]

    def test_active_agency_own_ok(self, super_session):
        my = super_session.get(f"{BASE_URL}/api/auth/my-agencies", timeout=15).json()
        if not my["items"]:
            pytest.skip("no agencies for super_admin")
        first = my["items"][0]
        aid = first.get("agency_id") or first.get("id") if isinstance(first, dict) else first
        r = super_session.post(
            f"{BASE_URL}/api/auth/active-agency",
            json={"agency_id": aid},
            timeout=15,
        )
        assert r.status_code == 200, r.text[:200]
        me = super_session.get(f"{BASE_URL}/api/auth/me", timeout=15).json()
        assert me.get("active_agency_id") == aid


# ---------- L12 refresh revocation ----------
class TestL12RefreshRevocation:
    def test_logout_revokes_refresh(self):
        s = requests.Session()
        assert _login(s, SUPER_EMAIL, SUPER_PASS).status_code == 200
        r_ok = s.post(f"{BASE_URL}/api/auth/refresh", timeout=15)
        assert r_ok.status_code == 200
        s.post(f"{BASE_URL}/api/auth/logout", timeout=15)
        # try refresh with the same (now revoked) cookie
        r_rev = requests.post(
            f"{BASE_URL}/api/auth/refresh",
            cookies=s.cookies,
            timeout=15,
        )
        assert r_rev.status_code == 401, f"expected 401 got {r_rev.status_code}"


# ---------- M23 async XML import ----------
class TestM23Import:
    def test_xml_inline_sync(self, super_session):
        xml = "<annunci><annuncio><titolo>Test M23</titolo><citta>Roma</citta><prezzo>100000</prezzo></annuncio></annunci>"
        r = super_session.post(
            f"{BASE_URL}/api/app/properties/import/xml",
            json={"xml_content": xml},
            timeout=30,
        )
        assert r.status_code == 200, r.text[:300]
        data = r.json()
        assert data.get("imported", 0) >= 1 or data.get("total", 0) >= 1

    def test_ssrf_blocked(self, super_session):
        r = super_session.post(
            f"{BASE_URL}/api/app/properties/import/xml",
            json={"feed_url": "http://127.0.0.1/x.xml"},
            timeout=15,
        )
        assert r.status_code == 400
        assert "url_not_allowed" in r.text or "not_allowed" in r.text.lower()


# ---------- M24 fascicolo multipart upload ----------
class TestM24Fascicolo:
    def test_multipart_upload_and_download(self, super_session):
        pr = super_session.get(f"{BASE_URL}/api/app/properties?limit=1", timeout=15)
        assert pr.status_code == 200
        items = pr.json().get("items") or pr.json().get("properties") or []
        if not items:
            pytest.skip("no properties available")
        prop_id = items[0].get("id") or items[0].get("_id")
        assert prop_id
        files = {"file": ("planim.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")}
        data = {"doc_type": "planimetria_catastale"}
        up = super_session.post(
            f"{BASE_URL}/api/app/fascicolo/{prop_id}/documents/upload",
            files=files,
            data=data,
            timeout=30,
        )
        assert up.status_code == 200, up.text[:300]
        doc = up.json().get("document") or up.json()
        assert doc.get("storage_path")
        doc_id = doc.get("id") or doc.get("_id")
        if doc_id:
            dl = super_session.get(
                f"{BASE_URL}/api/app/fascicolo/{prop_id}/documents/{doc_id}/download",
                timeout=15,
            )
            assert dl.status_code == 200
            assert len(dl.content) > 0


# ---------- M13 portals removed ----------
class TestM13PortalsRemoved:
    def test_portals_endpoint_404(self, super_session):
        r = super_session.get(f"{BASE_URL}/api/app/portals", timeout=15)
        assert r.status_code == 404
        r2 = super_session.get(f"{BASE_URL}/api/app/portals/list", timeout=15)
        assert r2.status_code == 404


# ---------- Public photo endpoint (no more 500) ----------
class TestPublicPhoto:
    def test_public_photo_status(self):
        s = requests.Session()
        r = s.get(f"{BASE_URL}/api/cloud/search?operation=sale&limit=5", timeout=20)
        assert r.status_code == 200, r.text[:200]
        js = r.json()
        items = js.get("items") or js.get("results") or []
        if not items:
            pytest.skip("no public listings")
        pid = items[0].get("id") or items[0].get("_id")
        assert pid
        rr = s.get(
            f"{BASE_URL}/api/public/property/{pid}/photo/0",
            allow_redirects=False,
            timeout=15,
        )
        assert rr.status_code in (200, 302, 404), f"unexpected {rr.status_code}"
        assert rr.status_code != 500


# ---------- Cloud search returns results ----------
class TestCloudSearch:
    def test_sale_search(self):
        r = requests.get(f"{BASE_URL}/api/cloud/search?operation=sale", timeout=20)
        assert r.status_code == 200
        js = r.json()
        total = js.get("total") or js.get("count") or len(js.get("items") or [])
        assert total >= 1
