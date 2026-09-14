"""M5.S3 — AL Legal backend tests.

Covers:
- Health (no auth)
- Auth gate on /chat (401 without cookie)
- Routing of 5 sub-agents (general, proposta, locazioni, catasto, urbanistica)
- Response schema + citations + confidence
- Session persistence + multi-turn (reuse session_id)
- Audit log persisted in al_legal_audit
- PDF analyze: success / non-pdf rejection / size limit
- Sessions list / detail / delete
- B2C user (no agency) can access /chat

Note: each LLM call costs Tavily + 2-3 LLM. We use only ~8 chat tests max.
"""
from __future__ import annotations

import io
import os
import time
import uuid

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://omnia-crm-docs.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = os.environ["OMNIA_ADMIN_EMAIL"]
ADMIN_PWD = os.environ["OMNIA_ADMIN_PASSWORD"]

# Generous timeout: Tavily ~2s + main LLM ~10s + validator LLM ~8s
LEGAL_TIMEOUT = 120


# ─── Fixtures ──────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def admin_session() -> requests.Session:
    s = requests.Session()
    r = s.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PWD}, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:300]}"
    return s


@pytest.fixture(scope="module")
def b2c_session() -> requests.Session:
    s = requests.Session()
    suffix = uuid.uuid4().hex[:8]
    email = f"TEST_legal_b2c_{suffix}@omnia.it"
    pwd = "B2cLegal2026!"
    payload = {
        "email": email,
        "password": pwd,
        "name": "TEST Legal B2C",
        "intents": ["sell"],
        "notification_channels": ["email"],
        "lang": "it",
        "gdpr_consent": True,
    }
    # B2C register is at /api/cloud/auth/register (immocloud cloud_auth)
    r = s.post(f"{API}/cloud/auth/register", json=payload, timeout=30)
    if r.status_code not in (200, 201):
        pytest.skip(f"b2c register failed: {r.status_code} {r.text[:200]}")
    # auth cookies should be set by register; verify via /auth/me
    me = s.get(f"{API}/auth/me", timeout=15)
    if me.status_code != 200:
        # try explicit login
        r2 = s.post(f"{API}/auth/login", json={"email": email, "password": pwd}, timeout=15)
        assert r2.status_code == 200, f"b2c login failed: {r2.status_code} {r2.text[:200]}"
    return s


# ─── Health & Auth ─────────────────────────────────────────────────────────
class TestHealthAndAuth:
    def test_health_no_auth(self):
        r = requests.get(f"{API}/app/legal/health", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["service"] == "al-legal"
        assert d["tavily_configured"] is True
        assert d["llm_configured"] is True
        for k in ("general", "proposta", "locazioni", "catasto", "urbanistica", "pdf_analysis"):
            assert k in d["sub_agents"], f"missing sub_agent {k}"

    def test_chat_requires_auth(self):
        r = requests.post(f"{API}/app/legal/chat", json={"message": "Test caparra"}, timeout=15)
        assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"


# ─── Routing & Chat ────────────────────────────────────────────────────────
class TestSubAgentRouting:
    """One chat test per sub-agent (5 calls)."""

    def _chat(self, session: requests.Session, message: str, session_id: str | None = None) -> dict:
        payload = {"message": message}
        if session_id:
            payload["session_id"] = session_id
        r = session.post(f"{API}/app/legal/chat", json=payload, timeout=LEGAL_TIMEOUT)
        assert r.status_code == 200, f"chat failed: {r.status_code} {r.text[:400]}"
        return r.json()

    def test_proposta_caparra(self, admin_session, request):
        d = self._chat(admin_session, "Cos'è la caparra confirmatoria nella proposta d'acquisto?")
        # schema
        for k in ("session_id", "sub_agent", "reply", "citations", "confidence", "low_confidence", "disclaimer"):
            assert k in d, f"missing schema field: {k}"
        assert d["sub_agent"] == "proposta", f"expected proposta got {d['sub_agent']}"
        assert isinstance(d["citations"], list)
        assert len(d["citations"]) >= 1, "expected at least 1 citation"
        assert isinstance(d["confidence"], (int, float))
        assert 0.0 <= d["confidence"] <= 1.0
        # CoT must NOT leak literal headers
        assert "CHAIN OF THOUGHT" not in d["reply"].upper()
        assert "STEP 1" not in d["reply"].upper()
        # share session for next test
        request.config._proposta_sid = d["session_id"]

    def test_locazioni_cedolare(self, admin_session):
        d = self._chat(admin_session, "Cedolare secca 21% o 10% quale conviene per locazione abitativa?")
        assert d["sub_agent"] == "locazioni", f"expected locazioni got {d['sub_agent']}"

    def test_urbanistica_scia_cila(self, admin_session):
        d = self._chat(admin_session, "Qual è la differenza tra SCIA e CILA edilizia?")
        assert d["sub_agent"] == "urbanistica", f"expected urbanistica got {d['sub_agent']}"

    def test_catasto_voltura(self, admin_session):
        d = self._chat(admin_session, "Come si fa la voltura catastale dopo un rogito?")
        assert d["sub_agent"] == "catasto", f"expected catasto got {d['sub_agent']}"

    def test_general_mutuo(self, admin_session):
        d = self._chat(admin_session, "Posso comprare casa con un mutuo al 100% del valore immobile?")
        # general or could route to another — accept general only
        assert d["sub_agent"] == "general", f"expected general got {d['sub_agent']}"

    def test_multi_turn_session_reuse(self, admin_session, request):
        """Reuse session_id from proposta test and verify history grows."""
        sid = getattr(request.config, "_proposta_sid", None)
        if not sid:
            pytest.skip("proposta sid not set (previous test failed)")
        d = self._chat(admin_session, "E se la caparra è penitenziale invece?", session_id=sid)
        assert d["session_id"] == sid
        # verify session persisted with at least 4 messages (2 turns × user+assistant)
        rs = admin_session.get(f"{API}/app/legal/sessions/{sid}", timeout=15)
        assert rs.status_code == 200
        msgs = rs.json().get("messages", [])
        assert len(msgs) >= 4, f"expected >=4 history messages, got {len(msgs)}"


# ─── B2C access ────────────────────────────────────────────────────────────
class TestB2CAccess:
    def test_b2c_can_chat(self, b2c_session):
        r = b2c_session.post(
            f"{API}/app/legal/chat",
            json={"message": "Quali tasse devo pagare quando vendo casa come privato?"},
            timeout=LEGAL_TIMEOUT,
        )
        assert r.status_code == 200, f"b2c chat failed: {r.status_code} {r.text[:300]}"
        d = r.json()
        assert "reply" in d and len(d["reply"]) > 20


# ─── PDF analysis ──────────────────────────────────────────────────────────
class TestPdfAnalysis:
    def _make_pdf(self) -> bytes:
        try:
            from reportlab.pdfgen import canvas
        except ImportError:
            pytest.skip("reportlab not installed")
        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(100, 750, "Contratto preliminare di compravendita immobiliare")
        c.drawString(100, 720, "Caparra confirmatoria: EUR 5.000")
        c.drawString(100, 690, "Prezzo: EUR 250.000")
        c.drawString(100, 660, "Termine rogito: 90 giorni")
        c.showPage()
        c.save()
        return buf.getvalue()

    def test_analyze_valid_pdf(self, admin_session):
        pdf_bytes = self._make_pdf()
        files = {"file": ("preliminare.pdf", pdf_bytes, "application/pdf")}
        data = {"question": "Analizza il documento e segnala criticità."}
        r = admin_session.post(
            f"{API}/app/legal/analyze-pdf", files=files, data=data, timeout=LEGAL_TIMEOUT,
        )
        assert r.status_code == 200, f"pdf analyze failed: {r.status_code} {r.text[:400]}"
        d = r.json()
        assert d.get("sub_agent") == "pdf_analysis"
        assert d.get("page_count", 0) >= 1
        assert isinstance(d.get("reply", ""), str) and len(d["reply"]) > 30
        assert isinstance(d.get("citations"), list)

    def test_reject_non_pdf(self, admin_session):
        files = {"file": ("notes.txt", b"hello world", "text/plain")}
        r = admin_session.post(
            f"{API}/app/legal/analyze-pdf", files=files, data={"question": "x"}, timeout=30,
        )
        assert r.status_code == 400
        assert "only_pdf_allowed" in r.text or "only_pdf" in r.text.lower()

    def test_reject_oversize_pdf(self, admin_session):
        # 6MB of zeros with .pdf extension — must fail extraction OR size check
        big = b"%PDF-1.4\n" + b"0" * (6 * 1024 * 1024)
        files = {"file": ("big.pdf", big, "application/pdf")}
        r = admin_session.post(
            f"{API}/app/legal/analyze-pdf", files=files, data={"question": "x"}, timeout=30,
        )
        assert r.status_code == 400, f"expected 400 got {r.status_code}: {r.text[:200]}"
        body = r.text.lower()
        assert any(k in body for k in ("file_too_large", "too_large", "invalid_pdf", "pdf"))


# ─── Sessions CRUD ─────────────────────────────────────────────────────────
class TestSessionsCRUD:
    def test_list_sessions(self, admin_session):
        r = admin_session.get(f"{API}/app/legal/sessions", timeout=15)
        assert r.status_code == 200
        items = r.json()
        assert isinstance(items, list)
        # we created sessions earlier in module; admin should have >=1
        assert len(items) >= 1
        first = items[0]
        for k in ("id", "created_at", "message_count", "preview"):
            assert k in first

    def test_get_session_not_found(self, admin_session):
        r = admin_session.get(f"{API}/app/legal/sessions/non-existent-sid-xyz", timeout=15)
        assert r.status_code == 404

    def test_delete_session_204(self, admin_session):
        # Create a quick session via chat first
        r = admin_session.post(
            f"{API}/app/legal/chat",
            json={"message": "Devo registrare un contratto di locazione transitoria?"},
            timeout=LEGAL_TIMEOUT,
        )
        if r.status_code == 429:
            pytest.skip("rate limit hit while creating delete-test session")
        assert r.status_code == 200
        sid = r.json()["session_id"]
        # Delete it
        rd = admin_session.delete(f"{API}/app/legal/sessions/{sid}", timeout=15)
        assert rd.status_code == 204
        # Verify 404 after delete
        r3 = admin_session.get(f"{API}/app/legal/sessions/{sid}", timeout=15)
        assert r3.status_code == 404


# ─── Audit log ─────────────────────────────────────────────────────────────
class TestAuditLog:
    def test_audit_persisted(self, admin_session):
        """Verify al_legal_audit collection has entries via Mongo client directly."""
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            import asyncio
        except ImportError:
            pytest.skip("motor not available")
        mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
        db_name = os.environ.get("DB_NAME", "omnia_db")

        async def _check():
            client = AsyncIOMotorClient(mongo_url)
            db = client[db_name]
            # Look for at least one chat audit row from recent tests
            doc = await db.al_legal_audit.find_one({"kind": "chat"}, sort=[("ts", -1)])
            client.close()
            return doc

        doc = asyncio.run(_check())
        assert doc is not None, "no al_legal_audit chat row found"
        for k in ("user_id", "session_id", "kind", "sub_agent", "citation_count", "confidence"):
            assert k in doc, f"missing audit field: {k}"
        assert doc["kind"] == "chat"
