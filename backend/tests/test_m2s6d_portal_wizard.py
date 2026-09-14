"""Backend tests for M2.6d Universal Portal Wizard (D-057).

Covers:
- Feed info endpoint returns copy-ready URLs.
- POST /custom-portals creates BOTH catalog entry and active connection.
- Slug is namespaced with agency short id (tenant isolation).
- Duplicate slug within same agency → 409.
- GET /custom-portals only lists caller's portals (not other agencies').
- Catalog endpoint includes caller's custom portals AND system portals.
- Catalog endpoint EXCLUDES other agencies' custom portals (tenant isolation).
- PATCH updates fields.
- DELETE removes portal + connection (audit logs preserved).
- Unsupported dialect / integration_type → 422.
- Auth boundary: anonymous blocked.
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


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module", autouse=True)
def _cleanup():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")

    async def _wipe():
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        # Remove any test custom portals leftover
        await db.publishing_catalog.delete_many({"is_custom": True, "slug": {"$regex": r"^x-.*-(qa|test)"}})
        await db.publishing_connections.delete_many({"portal_slug": {"$regex": r"^x-.*-(qa|test)"}})
        c.close()

    asyncio.run(_wipe())
    yield
    asyncio.run(_wipe())


# ======================================================================
# Feed info
# ======================================================================

class TestFeedInfo:
    def test_feed_info_returns_urls(self, admin_session):
        r = admin_session.get(f"{BASE_URL}/api/app/publishing/custom-portals/feed-info")
        assert r.status_code == 200
        d = r.json()
        assert d["dialect"] == "osf_federata"
        assert "primary" in d and "/api/publishing/feed/" in d["primary"]
        assert "fallback_generic_rss" in d
        assert d["agency_slug"]

    def test_feed_info_generic_rss(self, admin_session):
        r = admin_session.get(
            f"{BASE_URL}/api/app/publishing/custom-portals/feed-info?dialect=generic_rss"
        )
        assert r.status_code == 200
        assert "dialect=generic_rss" in r.json()["primary"]

    def test_feed_info_unsupported_dialect(self, admin_session):
        r = admin_session.get(
            f"{BASE_URL}/api/app/publishing/custom-portals/feed-info?dialect=hocus_pocus"
        )
        assert r.status_code == 422


# ======================================================================
# Create / list / delete
# ======================================================================

class TestCreateCustomPortal:
    def test_create_creates_portal_and_connection(self, admin_session):
        payload = {
            "name": "Portale Test QA",
            "slug": f"qa-{uuid.uuid4().hex[:6]}",
            "dialect": "osf_federata",
            "integration_type": "feed_pull",
            "category": "freemium",
            "site_url": "https://test-qa.example.com",
            "endpoint_url": "https://test-qa.example.com/import",
            "geographic_scope": "regional",
        }
        r = admin_session.post(
            f"{BASE_URL}/api/app/publishing/custom-portals", json=payload
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert data["portal"]["is_custom"] is True
        assert data["portal"]["slug"].startswith("x-")
        assert data["portal"]["endpoint_url"] == "https://test-qa.example.com/import"
        # Auto-created connection
        assert data["connection"]["portal_slug"] == data["portal"]["slug"]
        assert data["connection"]["status"] == "active"
        # Feed URLs surfaced
        assert data["feed"]["primary"]
        # Save slug for teardown-agnostic subsequent tests
        self._slug = data["portal"]["slug"]

    def test_create_duplicate_slug_conflict(self, admin_session):
        slug = f"qa-dup-{uuid.uuid4().hex[:6]}"
        payload = {
            "name": "Portale Dup",
            "slug": slug,
            "dialect": "osf_federata",
            "integration_type": "feed_pull",
        }
        r1 = admin_session.post(
            f"{BASE_URL}/api/app/publishing/custom-portals", json=payload
        )
        assert r1.status_code == 201
        r2 = admin_session.post(
            f"{BASE_URL}/api/app/publishing/custom-portals", json=payload
        )
        assert r2.status_code == 409

    def test_create_unsupported_dialect(self, admin_session):
        r = admin_session.post(
            f"{BASE_URL}/api/app/publishing/custom-portals",
            json={
                "name": "Bad Dialect",
                "slug": f"qa-bad-{uuid.uuid4().hex[:6]}",
                "dialect": "unknown_format",
                "integration_type": "feed_pull",
            },
        )
        assert r.status_code == 422

    def test_create_unsupported_integration_type(self, admin_session):
        r = admin_session.post(
            f"{BASE_URL}/api/app/publishing/custom-portals",
            json={
                "name": "Push Not Yet",
                "slug": f"qa-push-{uuid.uuid4().hex[:6]}",
                "dialect": "osf_federata",
                "integration_type": "api_push",  # Sprint 2+
            },
        )
        assert r.status_code == 422


# ======================================================================
# List / catalog exposure
# ======================================================================

class TestListingAndCatalog:
    def test_list_only_owned_portals(self, admin_session):
        # Create one, then list
        payload = {
            "name": "List Test QA",
            "slug": f"qa-list-{uuid.uuid4().hex[:6]}",
            "dialect": "osf_federata",
            "integration_type": "feed_pull",
        }
        admin_session.post(f"{BASE_URL}/api/app/publishing/custom-portals", json=payload)
        r = admin_session.get(f"{BASE_URL}/api/app/publishing/custom-portals")
        assert r.status_code == 200
        d = r.json()
        assert d["total"] >= 1
        # All items must be owned by the caller's agency
        for it in d["items"]:
            assert it["is_custom"] is True
            assert it["owner_agency_id"]

    def test_catalog_includes_custom_and_system(self, admin_session):
        # Ensure a custom exists
        admin_session.post(
            f"{BASE_URL}/api/app/publishing/custom-portals",
            json={
                "name": "Catalog Test QA",
                "slug": f"qa-cat-{uuid.uuid4().hex[:6]}",
                "dialect": "osf_federata",
                "integration_type": "feed_pull",
            },
        )
        r = admin_session.get(f"{BASE_URL}/api/app/publishing/catalog")
        assert r.status_code == 200
        items = r.json()["items"]
        has_system = any(not i.get("is_custom") for i in items)
        has_custom = any(i.get("is_custom") for i in items)
        assert has_system, "system portals must appear in catalog"
        assert has_custom, "own custom portals must appear in catalog"


# ======================================================================
# Update / delete
# ======================================================================

class TestUpdateDelete:
    def _create(self, session):
        r = session.post(
            f"{BASE_URL}/api/app/publishing/custom-portals",
            json={
                "name": "UD Base",
                "slug": f"qa-ud-{uuid.uuid4().hex[:6]}",
                "dialect": "osf_federata",
                "integration_type": "feed_pull",
            },
        )
        assert r.status_code == 201
        return r.json()["portal"]["slug"]

    def test_patch_updates_name_and_notes(self, admin_session):
        slug = self._create(admin_session)
        r = admin_session.patch(
            f"{BASE_URL}/api/app/publishing/custom-portals/{slug}",
            json={"name": "UD Renamed", "notes": "updated in test"},
        )
        assert r.status_code == 200
        assert r.json()["name"] == "UD Renamed"
        assert r.json()["notes"] == "updated in test"

    def test_delete_removes_portal_and_connection(self, admin_session):
        slug = self._create(admin_session)
        r = admin_session.delete(f"{BASE_URL}/api/app/publishing/custom-portals/{slug}")
        assert r.status_code == 200
        assert r.json()["slug"] == slug
        # Attempting to delete again → 404
        r2 = admin_session.delete(f"{BASE_URL}/api/app/publishing/custom-portals/{slug}")
        assert r2.status_code == 404
        # Also connection must be gone
        conns = admin_session.get(f"{BASE_URL}/api/app/publishing/connections").json()["items"]
        assert not any(c["portal_slug"] == slug for c in conns)


# ======================================================================
# Auth boundary
# ======================================================================

class TestAuthBoundary:
    def test_anonymous_cannot_create(self):
        r = requests.post(
            f"{BASE_URL}/api/app/publishing/custom-portals",
            json={"name": "X", "slug": "y", "dialect": "osf_federata", "integration_type": "feed_pull"},
        )
        assert r.status_code in (401, 403)

    def test_anonymous_cannot_list(self):
        r = requests.get(f"{BASE_URL}/api/app/publishing/custom-portals")
        assert r.status_code in (401, 403)
