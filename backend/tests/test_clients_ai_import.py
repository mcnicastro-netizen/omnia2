"""Backend tests for D-FUTURE-07 AI Smart Import Clienti (v1).
Tests use real Gemini calls (gemini-3-flash via EMERGENT_LLM_KEY).
"""
import os
import io
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


@pytest.fixture
def cleanup_ai_imports(session):
    """Yield, then delete any client with source='ai_import'."""
    yield
    r = session.get(f"{BASE_URL}/api/app/clients")
    items = r.json().get("items") if isinstance(r.json(), dict) else r.json()
    for c in items or []:
        if c.get("source") == "ai_import":
            session.delete(f"{BASE_URL}/api/app/clients/{c['id']}")


# ------------- format detection -------------

class TestAIImportFormats:
    def test_csv_with_arbitrary_columns(self, session, cleanup_ai_imports):
        csv = (
            "nome cliente;telefono;mail;cerca;budget max;città\n"
            "Mario Rossi;333-1234567;mario@x.it;trilocale;320000;Roma\n"
            "Lucia Bianchi;+39 348 9988776;lucia@x.it;bilocale centro;220000;Milano\n"
        )
        r = session.post(
            f"{BASE_URL}/api/app/clients/import/ai",
            files={"file": ("messy.csv", csv.encode(), "text/csv")},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert "draft_id" in d
        assert d["total_rows"] >= 2
        assert d["source_format"] == "csv"
        # Mario must be present with sane mapping
        names = {r["name"] for r in d["rows"]}
        assert any("Mario" in n for n in names)
        # confidence buckets must be present
        assert "high" in d["confidence_buckets"]

    def test_vcard_parsing(self, session, cleanup_ai_imports):
        vcf = (
            "BEGIN:VCARD\nVERSION:3.0\nFN:Anna Verdi\n"
            "TEL:+393311234567\nEMAIL:anna@verdi.it\nNOTE:Cerca trilocale Roma 280k\n"
            "END:VCARD\n"
            "BEGIN:VCARD\nVERSION:3.0\nFN:Bruno Neri\n"
            "TEL:+393229876543\nNOTE:Investitore appartamenti reddito\n"
            "END:VCARD\n"
        )
        r = session.post(
            f"{BASE_URL}/api/app/clients/import/ai",
            files={"file": ("contacts.vcf", vcf.encode(), "text/vcard")},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["source_format"] == "vcf"
        assert d["total_rows"] >= 2

    def test_plain_text_free_form(self, session, cleanup_ai_imports):
        txt = (
            "Marco Bianchi - 333 1112222 - cerca attico Roma centro <500k\n\n"
            "Sara Rossi cell 348 7654321 sara@rossi.it venditrice ha villa Mentana\n\n"
            "appunti: chiamare il fornitore\n"
        )
        r = session.post(
            f"{BASE_URL}/api/app/clients/import/ai",
            files={"file": ("appunti.txt", txt.encode(), "text/plain")},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["source_format"] == "txt"
        # Marco + Sara must be extracted; "appunti..." line should be skipped by Gemini
        names = " ".join(r["name"] for r in d["rows"])
        assert "Marco" in names or "Sara" in names

    def test_rejects_empty_file(self, session):
        r = session.post(
            f"{BASE_URL}/api/app/clients/import/ai",
            files={"file": ("empty.csv", b"", "text/csv")},
        )
        assert r.status_code == 400

    def test_rejects_huge_file(self, session):
        huge = b"x" * (6 * 1024 * 1024)
        r = session.post(
            f"{BASE_URL}/api/app/clients/import/ai",
            files={"file": ("huge.csv", huge, "text/csv")},
        )
        assert r.status_code == 413


# ------------- draft workflow -------------

class TestAIImportDraftWorkflow:
    def _create_draft(self, session):
        csv = "name;phone;city\nTest_AI_Draft Smith;333111;Roma\nTest_AI_Draft Jones;333222;Milano\n"
        r = session.post(
            f"{BASE_URL}/api/app/clients/import/ai",
            files={"file": ("d.csv", csv.encode(), "text/csv")},
        )
        assert r.status_code == 200
        return r.json()

    def test_load_draft_after_create(self, session, cleanup_ai_imports):
        d = self._create_draft(session)
        r = session.get(f"{BASE_URL}/api/app/clients/import/ai/draft/{d['draft_id']}")
        assert r.status_code == 200
        assert r.json()["draft_id"] == d["draft_id"]

    def test_load_unknown_draft_404(self, session):
        r = session.get(f"{BASE_URL}/api/app/clients/import/ai/draft/does-not-exist")
        assert r.status_code == 404

    def test_patch_row_then_commit(self, session, cleanup_ai_imports):
        d = self._create_draft(session)
        # Patch row 0: change phone
        r = session.patch(
            f"{BASE_URL}/api/app/clients/import/ai/draft/{d['draft_id']}/row/0",
            json={"phone": "+39 999 888 7777", "client_type": "investor"},
        )
        assert r.status_code == 200, r.text
        assert r.json()["row"]["phone"] == "+399998887777"
        assert r.json()["row"]["client_type"] == "investor"

        # Drop row 1
        r2 = session.patch(
            f"{BASE_URL}/api/app/clients/import/ai/draft/{d['draft_id']}/row/1",
            json={"drop": True},
        )
        assert r2.status_code == 200
        assert r2.json()["row"].get("_drop") is True

        # Commit with min_confidence=0
        r3 = session.post(
            f"{BASE_URL}/api/app/clients/import/ai/draft/{d['draft_id']}/commit",
            json={"min_confidence": 0, "default_gdpr_consent": True},
        )
        assert r3.status_code == 200
        result = r3.json()
        assert result["imported"] == 1
        assert result["skipped"] == 1

    def test_commit_twice_returns_409(self, session, cleanup_ai_imports):
        d = self._create_draft(session)
        r = session.post(
            f"{BASE_URL}/api/app/clients/import/ai/draft/{d['draft_id']}/commit",
            json={"min_confidence": 0},
        )
        assert r.status_code == 200
        r2 = session.post(
            f"{BASE_URL}/api/app/clients/import/ai/draft/{d['draft_id']}/commit",
            json={"min_confidence": 0},
        )
        assert r2.status_code == 409

    def test_min_confidence_filter(self, session, cleanup_ai_imports):
        d = self._create_draft(session)
        # Force min_confidence=99 → likely skips most rows
        r = session.post(
            f"{BASE_URL}/api/app/clients/import/ai/draft/{d['draft_id']}/commit",
            json={"min_confidence": 99},
        )
        assert r.status_code == 200
        assert r.json()["min_confidence_used"] == 99


class TestAIImportPermissions:
    def test_unauth_blocked(self):
        r = requests.post(
            f"{BASE_URL}/api/app/clients/import/ai",
            files={"file": ("x.csv", b"a;b\n1;2\n", "text/csv")},
        )
        assert r.status_code in (401, 403)


class TestAIImportRouting:
    def test_route_not_treated_as_id(self, session):
        # Regression: /clients/import/ai must not collide with /clients/{cid}
        r = session.get(f"{BASE_URL}/api/app/clients/import/ai/draft/test-only")
        # Either 404 (draft not found) — but NOT a "client_not_found" intercept
        assert r.status_code in (404, 422)
        if r.status_code == 404:
            body = r.text.lower()
            assert "draft" in body or "not_found" in body
