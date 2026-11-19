"""D-175 C4 — structure gates and Founder-driven apply (no invented users)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from shared.dogfood.c4_structure import (
    MANIFEST_SCHEMA,
    ROLE_AUTHORITY_MATRIX,
    analyze_structure,
    assert_c4_seed_target,
    assert_vat_unique_second_cc_denied,
    attach_membership_if_user_exists,
    build_empty_manifest_template,
    ensure_commercial_customer,
    ensure_organization,
    ensure_wallet,
    is_placeholder_email,
    nominate_main_admin_if_user_exists,
    validate_manifest,
)
from shared.models.commercial_customer import normalize_vat_number


class _FakeColl:
    def __init__(self):
        self.docs = []

    def find_one(self, q, proj=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                return {k: v for k, v in d.items() if k != "_id"}
        return None

    def insert_one(self, doc):
        self.docs.append(dict(doc))

    def update_one(self, q, upd):
        d = self.find_one(q)
        if not d:
            return
        for i, x in enumerate(self.docs):
            if all(x.get(k) == v for k, v in q.items()):
                x.update(upd.get("$set") or {})
                self.docs[i] = x
                return

    def update_many(self, q, upd):
        for x in self.docs:
            if all(x.get(k) == v for k, v in q.items()):
                x.update(upd.get("$set") or {})

    def find(self, q, proj=None):
        out = []
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items()):
                out.append({k: v for k, v in d.items() if k != "_id"})
        return out

    def count_documents(self, q):
        return len(list(self.find(q)))


class _FakeDB:
    def __init__(self):
        self.commercial_customers = _FakeColl()
        self.agencies = _FakeColl()
        self.cc_credit_wallets = _FakeColl()
        self.users = _FakeColl()
        self.memberships = _FakeColl()
        self.commercial_main_admin_events = _FakeColl()


def test_c4_manifest_template_validates():
    m = build_empty_manifest_template()
    assert m["schema"] == MANIFEST_SCHEMA
    errs = validate_manifest(m)
    assert errs == []


def test_c4_manifest_requires_two_orgs():
    m = build_empty_manifest_template()
    m["organizations"] = [m["organizations"][0]]
    assert "organizations_need_at_least_two_branches" in validate_manifest(m)


def test_c4_placeholder_email():
    assert is_placeholder_email("FOUNDER_FILLS_AFTER_SIGNUP@example.invalid")
    assert is_placeholder_email("")
    assert not is_placeholder_email("real.user@dogfood.local")


def test_c4_seed_target_denies_permanent():
    with pytest.raises(RuntimeError):
        assert_c4_seed_target("omnia_df_perm_main")
    assert assert_c4_seed_target("omnia_df_clean_c4") == "omnia_df_clean_c4"


def test_c4_cc_org_wallet_idempotent_and_vat_unique():
    db = _FakeDB()
    r1 = ensure_commercial_customer(db, vat_number="IT01234567890", legal_name="Demo SRL")
    r2 = ensure_commercial_customer(db, vat_number="01234567890", legal_name="Demo SRL")
    assert r1["created"] is True
    assert r2["created"] is False
    assert r1["customer"]["id"] == r2["customer"]["id"]
    assert normalize_vat_number("IT01234567890") == r1["customer"]["vat_number_normalized"]
    vat = assert_vat_unique_second_cc_denied(db, "IT01234567890")
    assert vat["ok"] is True and vat["count"] == 1

    cc_id = r1["customer"]["id"]
    o1 = ensure_organization(db, commercial_customer_id=cc_id, org_key="sede", display_name="Sede")
    o2 = ensure_organization(db, commercial_customer_id=cc_id, org_key="nord", display_name="Nord")
    o1b = ensure_organization(db, commercial_customer_id=cc_id, org_key="sede", display_name="Sede")
    assert o1["created"] and o2["created"] and not o1b["created"]
    w1 = ensure_wallet(db, cc_id)
    w2 = ensure_wallet(db, cc_id)
    assert w1["created"] and not w2["created"]
    st = analyze_structure(db, commercial_customer_id=cc_id)
    assert st["organization_count"] == 2
    assert st["wallet_count"] == 1


def test_c4_ma_pending_without_user_and_nominates_when_present():
    db = _FakeDB()
    cc = ensure_commercial_customer(db, vat_number="99999999999", legal_name="X")["customer"]
    pending = nominate_main_admin_if_user_exists(
        db, commercial_customer_id=cc["id"], email="FOUNDER_FILLS@example.invalid"
    )
    assert pending["status"] == "pending_founder"
    missing = nominate_main_admin_if_user_exists(
        db, commercial_customer_id=cc["id"], email="ma@dogfood.local"
    )
    assert missing["status"] == "pending_founder"
    db.users.insert_one(
        {
            "id": "u-ma",
            "email": "ma@dogfood.local",
            "is_active": True,
            "email_verified": True,
        }
    )
    ok = nominate_main_admin_if_user_exists(
        db, commercial_customer_id=cc["id"], email="ma@dogfood.local"
    )
    assert ok["ok"] and ok["status"] == "nominated"
    st = analyze_structure(db, commercial_customer_id=cc["id"])
    assert st["main_admin_user_id"] == "u-ma"


def test_c4_membership_requires_existing_user():
    db = _FakeDB()
    cc = ensure_commercial_customer(db, vat_number="88888888888", legal_name="Y")["customer"]
    org = ensure_organization(
        db, commercial_customer_id=cc["id"], org_key="sede", display_name="Sede"
    )["organization"]
    pending = attach_membership_if_user_exists(
        db, email="missing@dogfood.local", organization_id=org["id"], operational_role="agency_admin"
    )
    assert pending["status"] == "pending_founder"
    db.users.insert_one(
        {"id": "u-adm", "email": "adm@dogfood.local", "is_active": True, "email_verified": True}
    )
    ok = attach_membership_if_user_exists(
        db,
        email="adm@dogfood.local",
        organization_id=org["id"],
        operational_role="agency_admin",
        commercial_customer_id=cc["id"],
    )
    assert ok["ok"] and ok["status"] == "membership_active"
    again = attach_membership_if_user_exists(
        db,
        email="adm@dogfood.local",
        organization_id=org["id"],
        operational_role="agency_admin",
        commercial_customer_id=cc["id"],
    )
    assert again["status"] == "already_active"
    assert db.memberships.count_documents({"membership_status": "active"}) == 1


def test_c4_membership_rejects_wrong_cc_and_ma_user():
    db = _FakeDB()
    cc = ensure_commercial_customer(db, vat_number="77777777777", legal_name="Z")["customer"]
    other = ensure_commercial_customer(db, vat_number="66666666666", legal_name="Other")["customer"]
    org = ensure_organization(
        db, commercial_customer_id=cc["id"], org_key="sede", display_name="Sede"
    )["organization"]
    db.users.insert_one(
        {"id": "u-x", "email": "x@dogfood.local", "is_active": True, "email_verified": True}
    )
    bad_cc = attach_membership_if_user_exists(
        db,
        email="x@dogfood.local",
        organization_id=org["id"],
        operational_role="agent",
        commercial_customer_id=other["id"],
    )
    assert bad_cc["status"] == "rejected"
    assert bad_cc["reason"] == "organization_not_under_commercial_customer"
    forbid = attach_membership_if_user_exists(
        db,
        email="x@dogfood.local",
        organization_id=org["id"],
        operational_role="agent",
        commercial_customer_id=cc["id"],
        forbid_user_ids={"u-x"},
    )
    assert forbid["status"] == "rejected"
    assert "main_admin" in forbid["reason"]


def test_c4_manifest_rejects_ma_membership_overlap_and_unknown_org():
    m = build_empty_manifest_template()
    m["main_admin_email"] = "same@dogfood.local"
    m["organization_admins"][0]["email"] = "same@dogfood.local"
    errs = validate_manifest(m)
    assert "main_admin_email_overlaps_membership_lists" in errs
    m2 = build_empty_manifest_template()
    m2["organization_admins"][0]["org_key"] = "ghost"
    assert any(e.startswith("org_admin_unknown_org_key") for e in validate_manifest(m2))


def test_c4_ma_conflict_second_user():
    db = _FakeDB()
    cc = ensure_commercial_customer(db, vat_number="55555555555", legal_name="C")["customer"]
    db.users.insert_one(
        {"id": "u1", "email": "a@dogfood.local", "is_active": True, "email_verified": True}
    )
    db.users.insert_one(
        {"id": "u2", "email": "b@dogfood.local", "is_active": True, "email_verified": True}
    )
    assert nominate_main_admin_if_user_exists(
        db, commercial_customer_id=cc["id"], email="a@dogfood.local"
    )["status"] == "nominated"
    conflict = nominate_main_admin_if_user_exists(
        db, commercial_customer_id=cc["id"], email="b@dogfood.local"
    )
    assert conflict["status"] == "conflict"
    again = nominate_main_admin_if_user_exists(
        db, commercial_customer_id=cc["id"], email="a@dogfood.local"
    )
    assert again["status"] == "already_nominated"


def test_c4_role_matrix_documents_ma_no_auto_crm():
    assert ROLE_AUTHORITY_MATRIX["main_admin"]["crm_auto_access"] is False
    assert ROLE_AUTHORITY_MATRIX["organization_admin"]["commercial_wallet"] is False


def test_c4_template_file_exists():
    p = Path(__file__).resolve().parents[2] / "docs" / "dogfood" / "c4-manifest.template.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    assert validate_manifest(data) == []
