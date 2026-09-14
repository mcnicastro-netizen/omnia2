"""Backend tests for Sprint 1.5 recovery (GAP #3 widgets + GAP #4 feed bidirezionale).

Copre:
- GAP #3: 2 widget mancanti nel loader (staging + legal) + asset HTML servibili
- GAP #4: POST /api/v1/feed/properties (ingest da CRM esterni)
         GET  /api/v1/leads/export (lead export back al CRM Track B)

Tenant isolation garantita dal make_key_dep (agency_id derivato dall'API key).
"""
import os
import re
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
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module")
def api_key(session):
    """Create a fresh API key on the caller's agency."""
    r = session.post(
        f"{BASE_URL}/api/app/api-keys",
        json={"name": "audit-sprint15-test", "credits_balance": 100},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    key = body.get("plaintext_key") or body.get("key") or body.get("api_key")
    assert key and key.startswith("omk_live_"), f"missing plaintext key: {body}"
    yield key
    # cleanup key
    key_id = body.get("id")
    if key_id:
        session.delete(f"{BASE_URL}/api/app/api-keys/{key_id}")


class TestWidgetGap3:
    """GAP #3 — Widget M2.5.3 dichiarati 4, prima solo 2 riconosciuti dal loader."""

    def test_loader_now_accepts_staging_and_legal(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/loader.js")
        assert r.status_code == 200
        # loader deve elencare TUTTI e 4 i widget
        text = r.text
        assert '"valuator"' in text
        assert '"mortgages"' in text
        assert '"staging"' in text
        assert '"legal"' in text

    def test_staging_widget_html_served(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/staging.html?key=demo&lang=it")
        assert r.status_code == 200
        assert "text/html" in r.headers.get("content-type", "")
        # sanity: contiene i placeholder sostituiti e la CTA form
        assert 'data-testid="widget-staging"' in r.text
        assert "__BACKEND_BASE__" not in r.text  # placeholder must be replaced
        assert "Virtual Staging" in r.text

    def test_legal_widget_html_served(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/legal.html?key=demo&lang=it")
        assert r.status_code == 200
        assert 'data-testid="widget-legal"' in r.text
        assert "HAL Legal" in r.text
        assert "L. 247/2012" in r.text  # disclaimer obbligatorio
        assert "__PRIMARY_COLOR__" not in r.text  # placeholder must be replaced

    def test_unknown_widget_still_404(self):
        r = requests.get(f"{BASE_URL}/api/widgets/v1/tiktok.html")
        assert r.status_code == 404


class TestFeedIngestGap4:
    """GAP #4 — Feed bidirezionale INBOUND (D-041 modalità 3)."""

    def test_feed_ingest_requires_api_key(self):
        r = requests.post(
            f"{BASE_URL}/api/v1/feed/properties",
            json={"items": [{"external_id": "test-1"}]},
        )
        assert r.status_code in (401, 403)

    def test_feed_ingest_inserts_new(self, api_key):
        payload = {
            "mode": "upsert",
            "items": [
                {
                    "external_id": "ext-audit-001",
                    "title": "Bilocale test ingest 001",
                    "property_type": "apartment",
                    "operation": "sale",
                    "price": 180000,
                    "surface_sqm": 65,
                    "rooms": 2,
                    "city": "Roma",
                    "province": "RM",
                    "energy_class": "C",
                    "photo_urls": ["https://cdn.example.com/1.jpg", "https://cdn.example.com/2.jpg"],
                }
            ],
        }
        r = requests.post(
            f"{BASE_URL}/api/v1/feed/properties",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        assert r.status_code == 201, r.text
        body = r.json()["data"]
        assert body["inserted"] + body["updated"] >= 1
        assert body["total_received"] == 1

    def test_feed_ingest_upsert_is_idempotent(self, api_key):
        payload = {
            "mode": "upsert",
            "items": [
                {
                    "external_id": "ext-audit-002",
                    "title": "Trilocale test ingest 002 v1",
                    "price": 250000,
                    "city": "Milano",
                }
            ],
        }
        r1 = requests.post(
            f"{BASE_URL}/api/v1/feed/properties",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        assert r1.status_code == 201
        payload["items"][0]["title"] = "Trilocale test ingest 002 v2"
        payload["items"][0]["price"] = 260000
        r2 = requests.post(
            f"{BASE_URL}/api/v1/feed/properties",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
        assert r2.status_code == 201
        assert r2.json()["data"]["updated"] >= 1

    def test_feed_ingest_rejects_empty_items(self, api_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/feed/properties",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"items": []},
        )
        assert r.status_code == 422

    def test_feed_ingest_rejects_bad_operation(self, api_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/feed/properties",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"items": [{"external_id": "bad", "operation": "swap"}]},
        )
        assert r.status_code == 422


class TestLeadsExportGap4:
    """GAP #4 — Lead export back al CRM Track B."""

    def test_export_requires_api_key(self):
        r = requests.get(f"{BASE_URL}/api/v1/leads/export")
        assert r.status_code in (401, 403)

    def test_export_returns_tenant_scoped_leads(self, api_key):
        r = requests.get(
            f"{BASE_URL}/api/v1/leads/export",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_export_respects_since_filter(self, api_key):
        # future timestamp → zero leads
        r = requests.get(
            f"{BASE_URL}/api/v1/leads/export?since=2099-01-01T00:00:00%2B00:00",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert r.status_code == 200
        assert r.json()["data"]["total"] == 0

    def test_export_respects_limit(self, api_key):
        r = requests.get(
            f"{BASE_URL}/api/v1/leads/export?limit=5",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["limit"] == 5
        assert len(data["items"]) <= 5


class TestWidgetLeadRegression:
    """Regression: /api/v1/widgets/lead accepts staging (new widget) but rejects tiktok."""

    def test_widget_lead_accepts_staging(self, api_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/widgets/lead",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"widget": "staging", "email": "x@y.com", "consent": True},
        )
        assert r.status_code in (200, 201), r.text
        body = r.json()
        assert "data" in body and "id" in body["data"]

    def test_widget_lead_accepts_legal(self, api_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/widgets/lead",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"widget": "legal", "email": "z@y.com", "consent": True},
        )
        assert r.status_code in (200, 201), r.text

    def test_widget_lead_rejects_unknown_widget(self, api_key):
        r = requests.post(
            f"{BASE_URL}/api/v1/widgets/lead",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"widget": "tiktok", "email": "x@y.com", "consent": True},
        )
        assert r.status_code == 422
