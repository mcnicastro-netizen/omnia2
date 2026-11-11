"""D-163 — match KYC vs onboarding + auto-activate path."""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from shared.auth.kyc_auto_activate import compare_declared, maybe_auto_activate_from_kyc


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_compare_declared_match():
    agency = {
        "display_name": "Nicastro Immobiliare",
        "fiscal": {
            "legal_name": "Nicastro Immobiliare S.r.l.",
            "vat_number": "01234567890",
            "fiscal_code": "01234567890",
        },
    }
    owner = {"name": "Marco Nicastro"}
    visura = {
        "legal_name": "NICASTRO IMMOBILIARE SRL",
        "vat_number": "IT01234567890",
        "fiscal_code": "01234567890",
    }
    identity = {"full_name": "Marco Maria Nicastro", "fiscal_code": "NCSTMR..."}
    # CF id soft — leave empty so owner_sim drives
    identity = {"full_name": "Marco Nicastro", "fiscal_code": None}
    out = compare_declared(agency=agency, owner=owner, visura=visura, identity=identity)
    assert out["matched"] is True
    assert out["checks"]["vat_match"] is True


def test_compare_declared_vat_mismatch():
    agency = {
        "display_name": "X",
        "fiscal": {"legal_name": "X SRL", "vat_number": "11111111111", "fiscal_code": "11111111111"},
    }
    out = compare_declared(
        agency=agency,
        owner={"name": "Ada Lovelace"},
        visura={"legal_name": "X SRL", "vat_number": "22222222222"},
        identity={"full_name": "Ada Lovelace"},
    )
    assert out["matched"] is False
    assert "vat_mismatch_or_missing" in out["reasons"]


def test_auto_activate_happy_path(monkeypatch):
    import shared.auth.kyc_auto_activate as mod

    agency = {
        "id": "ag-auto-1",
        "display_name": "Demo Auto",
        "activation_status": "pending",
        "owner_id": "u-1",
        "preferred_plan_tier": "pro",
        "fiscal": {
            "legal_name": "Demo Auto SRL",
            "vat_number": "12345678901",
            "fiscal_code": "12345678901",
        },
        "contact": {"email": "owner@example.com"},
        "kyc": {
            "checklist": {"visura_camerale": True, "id_titolare": True},
            "documents": [
                {
                    "id": "d1",
                    "doc_type": "visura_camerale",
                    "storage_path": "omnia/ops-kyc/ag/v.pdf",
                },
                {
                    "id": "d2",
                    "doc_type": "documento_identita",
                    "storage_path": "omnia/ops-kyc/ag/i.jpg",
                },
            ],
        },
    }
    user = {"id": "u-1", "email": "owner@example.com", "name": "Ada Demo", "lang": "it"}

    class _Ag:
        def __init__(self):
            self.doc = dict(agency)

        async def find_one(self, q, *a, **k):
            if q.get("id") == self.doc["id"]:
                return dict(self.doc)
            return None

        async def update_one(self, q, upd, *a, **k):
            if "$set" in upd:
                # support dotted kyc.auto_verify lightly
                for key, val in upd["$set"].items():
                    if key == "kyc":
                        self.doc["kyc"] = val
                    elif key.startswith("kyc."):
                        kyc = dict(self.doc.get("kyc") or {})
                        kyc[key.split(".", 1)[1]] = val
                        self.doc["kyc"] = kyc
                    else:
                        self.doc[key] = val
            return SimpleNamespace(modified_count=1)

    class _Users:
        async def find_one(self, q, *a, **k):
            if q.get("id") == user["id"]:
                return dict(user)
            return None

    db = SimpleNamespace(agencies=_Ag(), users=_Users())

    monkeypatch.setenv("OMNIA_KYC_AUTO_ACTIVATE", "1")
    monkeypatch.setattr(
        "shared.auth.agency_credentials.agency_payment_ok",
        AsyncMock(return_value=True),
    )
    import shared.storage as storage

    monkeypatch.setattr(
        storage,
        "get_object",
        lambda path: (b"%PDF-1.4", "application/pdf")
        if "v.pdf" in path
        else (b"\xff\xd8\xff", "image/jpeg"),
    )

    async def fake_extract(*, data, mime, doc_type):
        if doc_type == "visura_camerale":
            return {
                "legal_name": "Demo Auto SRL",
                "vat_number": "12345678901",
                "fiscal_code": "12345678901",
                "confidence": 0.9,
            }
        return {"full_name": "Ada Demo", "fiscal_code": None, "confidence": 0.9}

    monkeypatch.setattr(mod, "_gemini_extract_doc", fake_extract)

    act = AsyncMock(
        return_value={
            "ok": True,
            "activation_status": "active",
            "email": {"ok": True, "status": "mock", "to": "owner@example.com"},
            "grant": {"ok": True},
            "tier": "pro",
        }
    )
    monkeypatch.setattr(mod, "_perform_activation", act)

    out = _run(maybe_auto_activate_from_kyc(db, "ag-auto-1"))
    assert out.get("auto_activated") is True
    assert out.get("ok") is True
    act.assert_awaited_once()
    assert db.agencies.doc.get("kyc_auto_activate_at")
    assert (db.agencies.doc.get("kyc") or {}).get("status") == "verified"
