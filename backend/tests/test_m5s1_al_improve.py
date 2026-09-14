"""M5.S1+ — AL Inline Improve endpoint tests.

Validates POST /api/app/al/improve:
- 200 + JSON {field,lang,tone,improved} for title and description
- Plausible Italian title <= ~100 chars, no wrapping quotes
- Description >= 300 chars typically, no markdown/emoji
- target_lang='en' returns English, 'es' returns Spanish
- 422 validation on invalid field / missing field / oversize current_text
- 401 unauth without cookies
- Works for B2C users (no agency membership) → 200, not 403
- Prompt safety: price NOT in suggested output
- Audit log: entry written to al_audit with kind='improve'
- SYSTEM_PROMPT brand: self-identifies as 'AL' (uppercase)
"""
import os
import re
import uuid
import time
import requests
import pytest
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["OMNIA_ADMIN_PASSWORD"]

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "omnia_db")


# ---------- Fixtures ----------

@pytest.fixture(scope="module")
def mongo_db():
    client = MongoClient(MONGO_URL)
    return client[DB_NAME]


@pytest.fixture(scope="module")
def admin_session():
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
    return s


@pytest.fixture(scope="module")
def b2c_session():
    """Register a fresh B2C user (no agency membership) via /api/auth/register."""
    s = requests.Session()
    email = f"TEST_alimprove_b2c_{uuid.uuid4().hex[:8]}@omnia.it"
    pwd = "TestB2C2026!"
    # Try B2C-specific registration first; fall back to plain register if endpoint shape differs.
    payload = {
        "email": email, "password": pwd, "name": "Test B2C Improve",
        "role": "b2c", "account_type": "b2c", "intent": "sell", "lang": "it",
    }
    r = s.post(f"{API}/auth/register", json=payload, timeout=30)
    if r.status_code not in (200, 201):
        # retry without unsupported fields
        r = s.post(f"{API}/auth/register", json={
            "email": email, "password": pwd, "name": "Test B2C Improve", "lang": "it",
        }, timeout=30)
    if r.status_code not in (200, 201):
        pytest.skip(f"B2C register failed: {r.status_code} {r.text[:200]}")
    # Verify user has no agency_ids
    me = s.get(f"{API}/auth/me", timeout=15).json()
    if me.get("agency_ids"):
        pytest.skip(f"B2C user unexpectedly has agency_ids: {me.get('agency_ids')}")
    return s, email


# ---------- Helpers ----------

PROPERTY_SAMPLE = {
    "property_type": "trilocale",
    "operation": "vendita",
    "city": "Roma",
    "zone": "Prati",
    "surface_sqm": 85,
    "rooms": 3,
    "bathrooms": 2,
    "energy": {"energy_class": "B", "heating": "autonomo"},
    "features": {"balcone": True, "ascensore": True, "cantina": True, "aria_condizionata": True},
    "price": 550000,  # MUST NOT appear in output
}


def _has_emoji(text: str) -> bool:
    # Common emoji ranges
    return bool(re.search(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF]", text))


def _has_markdown(text: str) -> bool:
    # Headings / bullets / bold / code fences
    return bool(re.search(r"(^|\n)(#{1,6}\s|\*\s|-\s|\d+\.\s|```)", text)) or "**" in text


# ---------- Tests ----------

class TestAlImproveTitle:
    """field='title' core flow"""

    def test_title_it_returns_200_and_schema(self, admin_session):
        r = admin_session.post(f"{API}/app/al/improve", json={
            "field": "title",
            "current_text": "trilo roma",
            "property_data": PROPERTY_SAMPLE,
            "target_lang": "it",
            "tone": "standard",
        }, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("field", "lang", "tone", "improved"):
            assert k in d, f"missing key {k}"
        assert d["field"] == "title"
        assert d["lang"] == "it"
        assert isinstance(d["improved"], str)
        improved = d["improved"]
        # length constraint <= ~100 chars (allow a touch over)
        assert len(improved) <= 110, f"title too long: {len(improved)} chars: {improved!r}"
        assert len(improved) > 5, "title too short"
        # no wrapping quotes
        assert not (improved.startswith('"') and improved.endswith('"')), "title still quote-wrapped"
        assert not (improved.startswith("«") and improved.endswith("»")), "title quote-wrapped"
        # no emoji
        assert not _has_emoji(improved), f"title contains emoji: {improved!r}"
        # save for cross-test reuse
        pytest.improve_title_it = improved

    def test_title_does_not_contain_price(self, admin_session):
        r = admin_session.post(f"{API}/app/al/improve", json={
            "field": "title",
            "current_text": "appartamento bello",
            "property_data": PROPERTY_SAMPLE,
            "target_lang": "it",
        }, timeout=60)
        assert r.status_code == 200
        improved = r.json()["improved"]
        assert "550000" not in improved, f"price leaked: {improved!r}"
        assert "550.000" not in improved, f"price leaked: {improved!r}"
        assert "€" not in improved or "550" not in improved, f"price leaked: {improved!r}"


class TestAlImproveDescription:
    """field='description' core flow + language matrix"""

    def test_description_it_long_form_no_markdown_no_emoji(self, admin_session):
        r = admin_session.post(f"{API}/app/al/improve", json={
            "field": "description",
            "current_text": "appartamento in centro",
            "property_data": PROPERTY_SAMPLE,
            "target_lang": "it",
            "tone": "standard",
        }, timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        improved = d["improved"]
        assert len(improved) >= 300, f"description too short ({len(improved)}): {improved!r}"
        assert not _has_emoji(improved), "description contains emoji"
        assert not _has_markdown(improved), f"description contains markdown: {improved[:200]!r}"
        # contains some Italian content
        low = improved.lower()
        assert any(w in low for w in ("il ", "la ", "lo ", "una ", "un ", "che ", "è ", "del ", "della ")), \
            f"not italian-looking: {improved[:200]!r}"

    def test_description_en(self, admin_session):
        r = admin_session.post(f"{API}/app/al/improve", json={
            "field": "description",
            "current_text": "nice flat",
            "property_data": PROPERTY_SAMPLE,
            "target_lang": "en",
            "tone": "standard",
        }, timeout=90)
        assert r.status_code == 200, r.text
        improved = r.json()["improved"]
        assert len(improved) >= 150
        low = improved.lower()
        en_signals = sum(1 for w in (" the ", " and ", " with ", " of ", " in ") if w in f" {low} ")
        assert en_signals >= 2, f"text doesn't look English (signals={en_signals}): {improved[:300]!r}"
        # Italian-only signals should be very rare
        it_only = sum(1 for w in (" è ", " della ", " sono ", " gli ") if w in f" {low} ")
        assert it_only <= 1, f"text looks Italian: {improved[:300]!r}"

    def test_description_es(self, admin_session):
        r = admin_session.post(f"{API}/app/al/improve", json={
            "field": "description",
            "current_text": "piso bonito",
            "property_data": PROPERTY_SAMPLE,
            "target_lang": "es",
            "tone": "standard",
        }, timeout=90)
        assert r.status_code == 200, r.text
        improved = r.json()["improved"]
        assert len(improved) >= 150
        low = improved.lower()
        es_signals = sum(1 for w in (" el ", " la ", " los ", " las ", " con ", " de ", " en ", "ñ", " es ", "ción") if w in f" {low} " or w in low)
        assert es_signals >= 2, f"text doesn't look Spanish (signals={es_signals}): {improved[:300]!r}"


class TestAlImproveValidation:
    """Pydantic-level validation"""

    def test_invalid_field_returns_422(self, admin_session):
        r = admin_session.post(f"{API}/app/al/improve", json={
            "field": "foo",
            "current_text": "x",
            "property_data": {},
        }, timeout=30)
        assert r.status_code == 422, r.text

    def test_missing_field_returns_422(self, admin_session):
        r = admin_session.post(f"{API}/app/al/improve", json={
            "current_text": "x",
            "property_data": {},
        }, timeout=30)
        assert r.status_code == 422, r.text

    def test_oversize_current_text_returns_422(self, admin_session):
        r = admin_session.post(f"{API}/app/al/improve", json={
            "field": "title",
            "current_text": "x" * 10001,
            "property_data": {},
        }, timeout=30)
        assert r.status_code == 422, r.text

    def test_invalid_target_lang_returns_422(self, admin_session):
        r = admin_session.post(f"{API}/app/al/improve", json={
            "field": "title",
            "current_text": "x",
            "property_data": {},
            "target_lang": "fr",
        }, timeout=30)
        assert r.status_code == 422, r.text


class TestAlImproveAuth:
    """Auth contract"""

    def test_no_cookies_returns_401(self):
        anon = requests.Session()
        r = anon.post(f"{API}/app/al/improve", json={
            "field": "title", "current_text": "x", "property_data": {},
        }, timeout=30)
        assert r.status_code == 401, f"expected 401, got {r.status_code}: {r.text[:200]}"


class TestAlImproveB2C:
    """B2C user without agency membership must still be able to use improve"""

    def test_b2c_user_can_improve_title(self, b2c_session):
        s, email = b2c_session
        r = s.post(f"{API}/app/al/improve", json={
            "field": "title",
            "current_text": "casa mia",
            "property_data": {
                "property_type": "bilocale", "city": "Milano", "surface_sqm": 60,
                "rooms": 2, "features": {"balcone": True},
            },
            "target_lang": "it",
        }, timeout=60)
        assert r.status_code == 200, f"B2C improve failed: {r.status_code} {r.text[:300]}"
        d = r.json()
        assert d["field"] == "title"
        assert isinstance(d["improved"], str) and len(d["improved"]) > 5


class TestAlImproveAudit:
    """Audit log entry written"""

    def test_improve_writes_audit_entry(self, admin_session, mongo_db):
        marker = f"AUDITMARK_{uuid.uuid4().hex[:8]}"
        r = admin_session.post(f"{API}/app/al/improve", json={
            "field": "title",
            "current_text": marker,
            "property_data": PROPERTY_SAMPLE,
            "target_lang": "it",
            "tone": "lusso",
        }, timeout=60)
        assert r.status_code == 200, r.text
        improved = r.json()["improved"]
        out_len = len(improved)

        # Allow a brief moment for the insert to flush
        time.sleep(0.3)
        # Look for any improve audit entry written in the last few seconds matching this output_len
        # (we used a unique marker; the input_len reflects len(marker))
        expected_in_len = len(marker)
        cursor = mongo_db.al_audit.find({"kind": "improve"}).sort("ts", -1).limit(20)
        found = None
        for doc in cursor:
            if doc.get("input_len") == expected_in_len and doc.get("output_len") == out_len:
                found = doc
                break
        assert found is not None, "no matching al_audit entry found"
        assert found["kind"] == "improve"
        assert found["field"] == "title"
        assert found["lang"] == "it"
        assert found["tone"] == "lusso"
        assert isinstance(found["input_len"], int)
        assert isinstance(found["output_len"], int)


# ---------- Static asserts (brand rename to 'HAL') ----------

def test_system_prompt_uppercase_al():
    """SYSTEM_PROMPT identifies the assistant as 'HAL' (uppercase, current brand)."""
    path = "/app/backend/apps/immoweb/al_agent.py"
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    assert "Sei HAL," in src, "SYSTEM_PROMPT does not start with 'Sei HAL,'"
    # Make sure the stale lowercase brand greetings are no longer present
    assert "Sei Al," not in src, "stale 'Sei Al,' still present"
