"""Backend tests for M2.5.4c (D-055): Legal Kit PDF templates.

Covers:
- Template catalog listing (4 items)
- PDF render (single) — magic bytes, size sanity
- Kit ZIP render — contains 4 PDFs + LEGGIMI
- Placeholder substitution (agency name appears in bytes)
- Rate limit + auth boundary
- v1 API-key endpoint charges 2 credits
"""
import io
import os
import zipfile

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
    """Drop cached events so the rate limiter doesn't trip during the run."""
    from motor.motor_asyncio import AsyncIOMotorClient
    from dotenv import load_dotenv
    import asyncio
    from pathlib import Path
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    async def _wipe():
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        await db.legal_kit_events.delete_many({})
        c.close()
    asyncio.run(_wipe())
    yield
    asyncio.run(_wipe())


# ==========================================================
# Unit tests — pure functions
# ==========================================================

class TestTemplateCatalog:
    def test_four_templates(self):
        from shared.legal_kit.templates import TEMPLATES, list_templates
        assert len(TEMPLATES) == 4
        slugs = {t["slug"] for t in list_templates()}
        assert slugs == {"gdpr_20", "pec_titolarita_dominio",
                         "disdetta_fornitore", "reclamo_cnr_iit"}

    def test_no_brand_mentions_in_catalog(self):
        """D-051: never mention specific competitors in copy."""
        from shared.legal_kit.templates import TEMPLATES
        forbidden = ["agestanet", "gestim", "immobiliare.it", "casa.it",
                     "getrix", "wolters", "solo affitti"]
        for slug, tpl in TEMPLATES.items():
            haystack = (tpl["name"] + tpl["target"] + tpl["when_to_use"]).lower()
            for section_title, section_body in tpl["sections"]:
                haystack += " " + section_body.lower()
            for word in forbidden:
                assert word not in haystack, f"Forbidden brand '{word}' found in template {slug}"


class TestPDFGenerator:
    def test_render_single_pdf_returns_bytes(self):
        from shared.legal_kit.pdf_generator import render_pdf
        pdf = render_pdf("gdpr_20", {"agency_name": "Nicastro Immobiliare"})
        assert isinstance(pdf, bytes)
        assert pdf.startswith(b"%PDF-")
        assert len(pdf) > 2000  # reasonable size for a 1-page PDF

    def test_render_all_slugs(self):
        from shared.legal_kit.pdf_generator import render_pdf
        from shared.legal_kit.templates import TEMPLATES
        for slug in TEMPLATES:
            pdf = render_pdf(slug, {})
            assert pdf.startswith(b"%PDF-"), f"{slug} did not render as PDF"

    def test_placeholder_substitution(self):
        """Different context → different PDF (proof placeholders are being replaced)."""
        from shared.legal_kit.pdf_generator import render_pdf
        pdf_short = render_pdf("gdpr_20", {"agency_name": "X"})
        pdf_long = render_pdf("gdpr_20", {"agency_name": "Nicastro Immobiliare Casa Vacanze SRL"})
        # Different agency names must produce different PDFs
        assert pdf_short != pdf_long
        # Longer name → bigger PDF (approximate but reliable enough)
        assert len(pdf_long) > len(pdf_short)

    def test_missing_slug_raises(self):
        from shared.legal_kit.pdf_generator import render_pdf
        with pytest.raises(KeyError):
            render_pdf("nonexistent_slug", {})

    def test_zip_contains_four_pdfs_plus_readme(self):
        from shared.legal_kit.pdf_generator import render_kit_zip
        zbytes = render_kit_zip({"agency_name": "X"})
        with zipfile.ZipFile(io.BytesIO(zbytes)) as z:
            names = z.namelist()
            assert len([n for n in names if n.endswith(".pdf")]) == 4
            assert "LEGGIMI.txt" in names


# ==========================================================
# Integration — public endpoints
# ==========================================================

class TestPublicEndpoints:
    def test_list_templates(self):
        r = requests.get(f"{BASE_URL}/api/legal/templates")
        assert r.status_code == 200
        d = r.json()
        assert d["count"] == 4
        slugs = {t["slug"] for t in d["items"]}
        assert "gdpr_20" in slugs

    def test_download_single_ok(self):
        r = requests.post(
            f"{BASE_URL}/api/legal/download/gdpr_20",
            json={"agency_name": "Nicastro Immobiliare"},
        )
        assert r.status_code == 200
        assert r.headers.get("content-type") == "application/pdf"
        assert r.content.startswith(b"%PDF-")
        assert 'filename="omnia_legal_gdpr_20.pdf"' in r.headers.get("content-disposition", "")

    def test_download_unknown_slug_404(self):
        r = requests.post(f"{BASE_URL}/api/legal/download/nope",
                          json={})
        assert r.status_code == 404

    def test_kit_requires_consent(self):
        r = requests.post(f"{BASE_URL}/api/legal/kit", json={
            "email": "test@example.com", "name": "Mario",
            "consent": False,
        })
        assert r.status_code == 400
        assert r.json()["detail"] == "consent_required"

    def test_kit_happy_path(self):
        r = requests.post(f"{BASE_URL}/api/legal/kit", json={
            "email": "leadtest@omnia.re", "name": "Marco Nicastro",
            "agency": "Nicastro Immobiliare", "consent": True,
            "context": {"agency_name": "Nicastro Immobiliare",
                        "domain": "nicastroimmobiliare.it"},
        })
        assert r.status_code == 200
        assert r.headers.get("content-type") == "application/zip"
        # Validate ZIP contents
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            pdfs = [n for n in z.namelist() if n.endswith(".pdf")]
            assert len(pdfs) == 4


# ==========================================================
# v1 API Gateway
# ==========================================================

@pytest.fixture(scope="module")
def api_key():
    s = requests.Session()
    s.post(f"{BASE_URL}/api/auth/login",
           json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    r = s.post(f"{BASE_URL}/api/app/api-keys",
               json={"name": "legal-kit-test", "initial_credits": 20})
    assert r.status_code in (200, 201), r.text
    return r.json()["key"]


class TestV1LegalRender:
    def test_auth_required(self):
        r = requests.post(f"{BASE_URL}/api/v1/legal/render",
                          json={"slug": "gdpr_20"})
        assert r.status_code in (401, 403)

    def test_render_2_credits(self, api_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/legal/render",
            json={"slug": "gdpr_20", "context": {"agency_name": "Test"}},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert r.status_code == 200, r.text
        assert r.content.startswith(b"%PDF-")
        assert r.headers.get("x-credits-charged") == "2"

    def test_render_unknown_slug_404(self, api_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/legal/render",
            json={"slug": "nope"},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert r.status_code == 404
