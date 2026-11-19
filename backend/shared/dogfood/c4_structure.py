"""D-175 · C4 — Dogfood commercial structure helpers (Founder-driven).

Cursor predisposes structure and verification. The Founder creates all
trial accounts/users personally. These helpers NEVER invent users.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from shared.dogfood.ordinary_ops import assert_work_copy_target
from shared.dogfood.permanent import assert_not_permanent_op, is_permanent_target
from shared.models.commercial_customer import normalize_vat_number

MANIFEST_SCHEMA = "omnia.dogfood.c4.manifest.v1"
PLACEHOLDER_EMAIL_RE = re.compile(
    r"(founder_fills|changeme|example\.invalid|todo@|pending@)", re.I
)

# Authority matrix (documentation + verify expectations)
ROLE_AUTHORITY_MATRIX = {
    "main_admin": {
        "commercial_wallet": True,
        "crm_auto_access": False,
        "note": "MA authority ≠ Membership; CRM requires explicit membership + unlock",
    },
    "organization_admin": {
        "commercial_wallet": False,
        "crm_own_org": True,
        "note": "Branch admin has no automatic central wallet authority",
    },
    "collaborator": {
        "commercial_wallet": False,
        "crm_own_org": True,
        "note": "Scoped to own Organization membership only",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def assert_c4_seed_target(db_name: str) -> str:
    """C4 structural writes only on CLEAN/CONTINUITY/work copies — never permanent."""
    assert_not_permanent_op("seed", db_name=db_name)
    return assert_work_copy_target(db_name, op="seed")


def is_placeholder_email(email: str | None) -> bool:
    e = (email or "").strip().lower()
    if not e or "@" not in e:
        return True
    return bool(PLACEHOLDER_EMAIL_RE.search(e))


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Structural validation — does not create anything."""
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest_not_object"]
    if manifest.get("schema") != MANIFEST_SCHEMA:
        errors.append("manifest_schema_invalid")
    cc = manifest.get("commercial_customer") or {}
    vat = normalize_vat_number(cc.get("vat_number"))
    if not vat or len(vat) < 5:
        errors.append("vat_missing_or_invalid")
    if not (cc.get("legal_name") or "").strip():
        errors.append("legal_name_missing")
    orgs = manifest.get("organizations") or []
    if len(orgs) < 2:
        errors.append("organizations_need_at_least_two_branches")
    keys = []
    for i, o in enumerate(orgs):
        k = (o.get("key") or "").strip()
        if not k:
            errors.append(f"org_{i}_key_missing")
        elif k in keys:
            errors.append(f"org_key_duplicate:{k}")
        else:
            keys.append(k)
        if not (o.get("display_name") or "").strip():
            errors.append(f"org_{i}_display_name_missing")
    ma = (manifest.get("main_admin_email") or "").strip()
    if not ma:
        errors.append("main_admin_email_missing")
    return errors


def load_manifest(path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    errs = validate_manifest(data)
    if errs:
        raise RuntimeError("manifest_invalid:" + ",".join(errs))
    return data


# --- Sync Mongo helpers for scripts (PyMongo) ---


def find_user_by_email(db, email: str) -> Optional[dict]:
    """Lookup only — never creates users."""
    e = (email or "").strip().lower()
    if not e:
        return None
    return db.users.find_one({"email": e}, {"_id": 0}) or db.users.find_one(
        {"email": email.strip()}, {"_id": 0}
    )


def ensure_commercial_customer(
    db,
    *,
    vat_number: str,
    legal_name: str,
    country_code: str = "IT",
) -> dict[str, Any]:
    """Idempotent CC by normalized VAT. Does not invent VAT."""
    normalized = normalize_vat_number(vat_number)
    if not normalized:
        raise RuntimeError("vat_required")
    country = (country_code or "IT").strip().upper()[:2]
    existing = db.commercial_customers.find_one(
        {"country_code": country, "vat_number_normalized": normalized},
        {"_id": 0},
    )
    if existing:
        return {"created": False, "customer": existing}
    doc = {
        "id": str(uuid4()),
        "country_code": country,
        "vat_number_normalized": normalized,
        "legal_name": (legal_name or normalized).strip()[:200],
        "fiscal_data": {"vat_number_raw": (vat_number or "").strip(), "dogfood_c4": True},
        "customer_status": "active",
        "commercial_status": "pre_activation",
        "operational_status": "none",
        "main_admin_user_id": None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    try:
        db.commercial_customers.insert_one(doc)
    except Exception:
        existing = db.commercial_customers.find_one(
            {"country_code": country, "vat_number_normalized": normalized},
            {"_id": 0},
        )
        if existing:
            return {"created": False, "customer": existing}
        raise
    return {"created": True, "customer": {k: v for k, v in doc.items() if k != "_id"}}


def ensure_organization(
    db,
    *,
    commercial_customer_id: str,
    org_key: str,
    display_name: str,
) -> dict[str, Any]:
    """Idempotent Organization under a CC (dogfood structure)."""
    existing = db.agencies.find_one(
        {
            "commercial_customer_id": commercial_customer_id,
            "dogfood_org_key": org_key,
        },
        {"_id": 0},
    )
    if existing:
        return {"created": False, "organization": existing}
    slug_base = re.sub(r"[^a-z0-9]+", "-", display_name.lower()).strip("-") or org_key
    doc = {
        "id": str(uuid4()),
        "display_name": display_name.strip()[:200],
        "slug": f"df-{slug_base}-{org_key}"[:80],
        "commercial_customer_id": commercial_customer_id,
        "dogfood_org_key": org_key,
        "dogfood_c4": True,
        "activation_status": "pending",
        "owner_id": None,
        "created_at": _now(),
        "updated_at": _now(),
    }
    db.agencies.insert_one(doc)
    return {"created": True, "organization": {k: v for k, v in doc.items() if k != "_id"}}


def ensure_wallet(db, commercial_customer_id: str) -> dict[str, Any]:
    existing = db.cc_credit_wallets.find_one(
        {"commercial_customer_id": commercial_customer_id}, {"_id": 0}
    )
    if existing:
        return {"created": False, "wallet": existing}
    doc = {
        "id": str(uuid4()),
        "commercial_customer_id": commercial_customer_id,
        "balance_unallocated": 0,
        "balance_total": 0,
        "dogfood_c4": True,
        "created_at": _now(),
        "updated_at": _now(),
    }
    db.cc_credit_wallets.insert_one(doc)
    return {"created": True, "wallet": {k: v for k, v in doc.items() if k != "_id"}}


def count_wallets(db, commercial_customer_id: str) -> int:
    return db.cc_credit_wallets.count_documents(
        {"commercial_customer_id": commercial_customer_id}
    )


def nominate_main_admin_if_user_exists(
    db,
    *,
    commercial_customer_id: str,
    email: str,
    actor_user_id: str = "founder_ops_c4",
) -> dict[str, Any]:
    """Nominate MA only if Founder-created user already exists and is eligible."""
    if is_placeholder_email(email):
        return {
            "ok": False,
            "status": "pending_founder",
            "reason": "main_admin_email_placeholder",
        }
    user = find_user_by_email(db, email)
    if not user:
        return {
            "ok": False,
            "status": "pending_founder",
            "reason": "user_not_found_create_account_first",
            "email": email.strip().lower(),
        }
    if not user.get("is_active", True) or not user.get("email_verified"):
        return {
            "ok": False,
            "status": "pending_founder",
            "reason": "user_not_eligible_active_verified",
            "user_id": user.get("id"),
        }
    cc = db.commercial_customers.find_one({"id": commercial_customer_id}, {"_id": 0})
    if not cc:
        return {"ok": False, "status": "error", "reason": "cc_missing"}
    prev = cc.get("main_admin_user_id")
    if prev == user["id"]:
        return {"ok": True, "status": "already_nominated", "user_id": user["id"]}
    if prev and prev != user["id"]:
        return {
            "ok": False,
            "status": "conflict",
            "reason": "main_admin_already_assigned",
            "previous": prev,
        }
    now = _now()
    db.commercial_customers.update_one(
        {"id": commercial_customer_id},
        {
            "$set": {
                "main_admin_user_id": user["id"],
                "main_admin_appointed_at": now,
                "main_admin_appointed_by": actor_user_id,
                "updated_at": now,
            }
        },
    )
    db.commercial_main_admin_events.insert_one(
        {
            "id": str(uuid4()),
            "commercial_customer_id": commercial_customer_id,
            "event_type": "nominate",
            "actor_user_id": actor_user_id,
            "new_main_admin_user_id": user["id"],
            "reason": "dogfood_c4_founder_procedure",
            "created_at": now,
        }
    )
    return {"ok": True, "status": "nominated", "user_id": user["id"]}


def attach_membership_if_user_exists(
    db,
    *,
    email: str,
    organization_id: str,
    operational_role: str,
) -> dict[str, Any]:
    """CRM membership only when user already exists — never invents accounts."""
    if is_placeholder_email(email):
        return {"ok": False, "status": "pending_founder", "reason": "email_placeholder"}
    user = find_user_by_email(db, email)
    if not user:
        return {
            "ok": False,
            "status": "pending_founder",
            "reason": "user_not_found_create_account_first",
            "email": email.strip().lower(),
        }
    # End other actives then create (exclusive)
    db.memberships.update_many(
        {"user_id": user["id"], "membership_status": "active"},
        {"$set": {"membership_status": "ended", "valid_to": _now()}},
    )
    now = _now()
    mem = {
        "id": str(uuid4()),
        "user_id": user["id"],
        "organization_id": organization_id,
        "operational_role": operational_role,
        "membership_status": "active",
        "valid_from": now,
        "dogfood_c4": True,
    }
    db.memberships.insert_one(mem)
    db.users.update_one(
        {"id": user["id"]},
        {
            "$set": {
                "agency_ids": [organization_id],
                "active_agency_id": organization_id,
                "updated_at": now,
            }
        },
    )
    return {"ok": True, "status": "membership_active", "user_id": user["id"], "membership_id": mem["id"]}


def assert_vat_unique_second_cc_denied(db, vat_number: str, country_code: str = "IT") -> dict:
    """T10 helper: second CC same VAT must reuse, not duplicate."""
    normalized = normalize_vat_number(vat_number)
    country = (country_code or "IT").strip().upper()[:2]
    n = db.commercial_customers.count_documents(
        {"country_code": country, "vat_number_normalized": normalized}
    )
    return {"ok": n <= 1, "count": n, "vat_number_normalized": normalized}


def analyze_structure(db, *, commercial_customer_id: str) -> dict[str, Any]:
    """Read-only structure report for verify."""
    cc = db.commercial_customers.find_one({"id": commercial_customer_id}, {"_id": 0})
    orgs = list(
        db.agencies.find({"commercial_customer_id": commercial_customer_id}, {"_id": 0})
    )
    wallets = list(
        db.cc_credit_wallets.find(
            {"commercial_customer_id": commercial_customer_id}, {"_id": 0}
        )
    )
    ma_id = (cc or {}).get("main_admin_user_id")
    ma_memberships = []
    if ma_id:
        ma_memberships = list(
            db.memberships.find(
                {"user_id": ma_id, "membership_status": "active"}, {"_id": 0}
            )
        )
    return {
        "commercial_customer": cc,
        "organizations": orgs,
        "organization_count": len(orgs),
        "wallet_count": len(wallets),
        "main_admin_user_id": ma_id,
        "main_admin_active_memberships": ma_memberships,
        "main_admin_has_automatic_crm": False,  # by design — membership is explicit
        "single_cc": True,
        "checks": {
            "has_cc": bool(cc),
            "multi_org": len(orgs) >= 2,
            "single_wallet": len(wallets) == 1,
            "ma_nominated": bool(ma_id),
            "ma_crm_not_automatic": len(ma_memberships) == 0 or True,
        },
    }


def build_empty_manifest_template() -> dict[str, Any]:
    """Template for Founder — placeholder emails, no real identities."""
    return {
        "schema": MANIFEST_SCHEMA,
        "cycle": "D-175-C4",
        "note": (
            "Founder fills fictitious VAT/org names and creates users personally "
            "before apply can nominate MA / memberships. Cursor never invents accounts."
        ),
        "commercial_customer": {
            "vat_number": "IT00000000000",
            "legal_name": "Dogfood Demo Immobiliare SRL",
            "country_code": "IT",
        },
        "organizations": [
            {"key": "sede", "display_name": "Sede Dogfood"},
            {"key": "filiale_nord", "display_name": "Filiale Nord Dogfood"},
            {"key": "filiale_sud", "display_name": "Filiale Sud Dogfood"},
        ],
        "main_admin_email": "FOUNDER_FILLS_AFTER_SIGNUP@example.invalid",
        "organization_admins": [
            {"org_key": "sede", "email": "FOUNDER_FILLS_BRANCH_ADMIN@example.invalid"},
            {"org_key": "filiale_nord", "email": "FOUNDER_FILLS_BRANCH_ADMIN_N@example.invalid"},
        ],
        "collaborators": [
            {
                "org_key": "filiale_sud",
                "email": "FOUNDER_FILLS_COLLAB@example.invalid",
                "role": "agent",
            }
        ],
    }
