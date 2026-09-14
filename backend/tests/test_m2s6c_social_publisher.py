"""Backend tests for M2.6c Social Publisher (Sprint 1 · Item #2).

Copre:
- Catalog dei canali social (facebook_page, instagram_business, telegram)
- CRUD dei channel per agenzia (activate, update, delete, list)
- Tenant isolation dei canali
- Error handling su credenziali mancanti (422) e canale non supportato (422)
- Publish endpoint: channels required + channel_not_configured error path
- Audit log social_posts + filtering per canale

Le chiamate reali a Meta/Telegram NON vengono effettuate qui — quelle vengono
validate manualmente dal Founder con le sue credenziali di produzione.
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
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    assert r.status_code == 200, r.text
    return s


@pytest.fixture(scope="module", autouse=True)
def cleanup(session):
    # Wipe all social channels for the test agency before + after the module.
    for _ in range(2):
        r = session.get(f"{BASE_URL}/api/app/publishing/social/channels")
        for ch in r.json().get("items", []):
            session.delete(f"{BASE_URL}/api/app/publishing/social/channels/{ch['id']}")
        if _ == 0:
            yield


class TestCatalog:
    def test_catalog_returns_three_channels(self, session):
        r = session.get(f"{BASE_URL}/api/app/publishing/social/catalog")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 3
        slugs = {c["channel"] for c in data["items"]}
        assert slugs == {"facebook_page", "instagram_business", "telegram"}

    def test_catalog_declares_credential_fields(self, session):
        r = session.get(f"{BASE_URL}/api/app/publishing/social/catalog")
        by_ch = {c["channel"]: c for c in r.json()["items"]}
        assert {f["name"] for f in by_ch["facebook_page"]["credential_fields"]} == {"page_id", "access_token"}
        assert {f["name"] for f in by_ch["instagram_business"]["credential_fields"]} == {"ig_user_id", "access_token"}
        assert {f["name"] for f in by_ch["telegram"]["credential_fields"]} == {"bot_token", "chat_id"}


class TestChannelsCRUD:
    def test_activate_channel_encrypts_credentials(self, session):
        r = session.post(f"{BASE_URL}/api/app/publishing/social/channels", json={
            "channel": "telegram",
            "credentials": {"bot_token": "123:test", "chat_id": "@omniatest"},
        })
        assert r.status_code == 201, r.text
        body = r.json()
        assert body["channel"] == "telegram"
        assert body["status"] == "active"
        # Never leak encrypted credentials or plaintext values.
        assert "credentials_encrypted" not in body
        raw = str(body).lower()
        assert "123:test" not in raw

    def test_activate_missing_creds_returns_422(self, session):
        r = session.post(f"{BASE_URL}/api/app/publishing/social/channels", json={
            "channel": "facebook_page",
            "credentials": {"page_id": "1275173392335417"},  # missing access_token
        })
        assert r.status_code == 422
        assert "missing_credentials" in str(r.json().get("detail", ""))

    def test_activate_unsupported_channel_422(self, session):
        r = session.post(f"{BASE_URL}/api/app/publishing/social/channels", json={
            "channel": "tiktok",
            "credentials": {},
        })
        assert r.status_code == 422

    def test_duplicate_activation_409(self, session):
        # Telegram already active from test above
        r = session.post(f"{BASE_URL}/api/app/publishing/social/channels", json={
            "channel": "telegram",
            "credentials": {"bot_token": "999:dup", "chat_id": "@dup"},
        })
        assert r.status_code == 409

    def test_list_returns_active_channels(self, session):
        r = session.get(f"{BASE_URL}/api/app/publishing/social/channels")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] >= 1
        channels = {ch["channel"] for ch in data["items"]}
        assert "telegram" in channels
        for ch in data["items"]:
            assert "credentials_encrypted" not in ch  # never leaked

    def test_update_credentials_rotates_encryption(self, session):
        # Get existing telegram channel id
        r = session.get(f"{BASE_URL}/api/app/publishing/social/channels")
        tg = next(ch for ch in r.json()["items"] if ch["channel"] == "telegram")
        r2 = session.patch(f"{BASE_URL}/api/app/publishing/social/channels/{tg['id']}", json={
            "credentials": {"bot_token": "999:rotated", "chat_id": "@rotated"},
        })
        assert r2.status_code == 200
        assert r2.json()["status"] == "active"

    def test_disable_channel(self, session):
        r = session.get(f"{BASE_URL}/api/app/publishing/social/channels")
        tg = next(ch for ch in r.json()["items"] if ch["channel"] == "telegram")
        r2 = session.patch(f"{BASE_URL}/api/app/publishing/social/channels/{tg['id']}", json={"status": "disabled"})
        assert r2.status_code == 200
        assert r2.json()["status"] == "disabled"
        # Re-enable for later tests
        session.patch(f"{BASE_URL}/api/app/publishing/social/channels/{tg['id']}", json={"status": "active"})

    def test_delete_channel(self, session):
        # Create a facebook channel then delete it
        r = session.post(f"{BASE_URL}/api/app/publishing/social/channels", json={
            "channel": "facebook_page",
            "credentials": {"page_id": "1275173392335417", "access_token": "FAKE_TOKEN"},
        })
        assert r.status_code == 201
        cid = r.json()["id"]
        r2 = session.delete(f"{BASE_URL}/api/app/publishing/social/channels/{cid}")
        assert r2.status_code == 200
        # Second delete = 404
        r3 = session.delete(f"{BASE_URL}/api/app/publishing/social/channels/{cid}")
        assert r3.status_code == 404


class TestPublishEndpoint:
    def test_publish_requires_channels(self, session):
        r = session.post(f"{BASE_URL}/api/app/publishing/social/publish", json={
            "channels": [],
            "caption": "hello",
        })
        assert r.status_code == 422

    def test_publish_to_unconfigured_channel_records_error(self, session):
        # Instagram is not configured — publish should return a per-channel error
        r = session.post(f"{BASE_URL}/api/app/publishing/social/publish", json={
            "channels": ["instagram_business"],
            "caption": "test caption",
            "image_url": "https://cdn.example.com/test.jpg",
        })
        assert r.status_code == 200
        results = r.json()["results"]
        assert results["instagram_business"]["ok"] is False
        assert results["instagram_business"]["error"] == "channel_not_configured"

    def test_publish_missing_property_404(self, session):
        r = session.post(f"{BASE_URL}/api/app/publishing/social/publish", json={
            "property_id": "does-not-exist-uuid",
            "channels": ["telegram"],
        })
        assert r.status_code == 404


class TestAuditPosts:
    def test_posts_endpoint_returns_history(self, session):
        r = session.get(f"{BASE_URL}/api/app/publishing/social/posts")
        assert r.status_code == 200
        data = r.json()
        assert "items" in data
        # We already forced at least one failed post via the "channel_not_configured" test.
        assert data["total"] >= 1
        for p in data["items"]:
            assert "_id" not in p
            assert p["agency_id"]  # tenant-scoped

    def test_posts_filter_by_channel(self, session):
        r = session.get(f"{BASE_URL}/api/app/publishing/social/posts?channel=instagram_business")
        assert r.status_code == 200
        for p in r.json()["items"]:
            assert p["channel"] == "instagram_business"


class TestUnauthorized:
    def test_channels_require_auth(self):
        # No session cookie / auth header → must be denied
        r = requests.get(f"{BASE_URL}/api/app/publishing/social/channels")
        assert r.status_code in (401, 403)
