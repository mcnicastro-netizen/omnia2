"""Deterministic synthetic fixtures tagged with d7_run_id — @example.com only."""
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from . import config
from .artifacts import write_json, write_secrets_file
from .mongo_util import connect_staging_db, scoped_filter

# Import hashing from backend when available
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[2] / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def ids(run_id: str) -> dict[str, str]:
    short = run_id[-8:]
    dom = config.EMAIL_DOMAIN
    return {
        "ag_active": f"d7r2-{short}-ag-a",
        "ag_b": f"d7r2-{short}-ag-b",
        "ag_inactive": f"d7r2-{short}-ag-x",
        "user_a": f"d7r2-{short}-user-a",
        "user_b": f"d7r2-{short}-user-b",
        "user_x": f"d7r2-{short}-user-x",
        "email_a": f"d7r2.{short}.admin.a@{dom}",
        "email_b": f"d7r2.{short}.admin.b@{dom}",
        "email_x": f"d7r2.{short}.admin.x@{dom}",
        "email_invitee": f"d7r2.{short}.invitee@{dom}",
        "prop": f"d7r2-{short}-prop",
        "client": f"d7r2-{short}-client",
        "cc": f"d7r2-{short}-cc",
        "org": f"d7r2-{short}-org",
        "key_active": f"d7r2-{short}-key-a",
    }


def seed(run_id: str, run_path) -> dict[str, Any]:
    from shared.auth.api_key import KEY_PREFIX, generate_plaintext_key, hash_key
    from shared.auth.hashing import hash_password

    db = connect_staging_db()
    # Safety: only delete same run_id (never legacy d7_tag alone)
    _scoped_cleanup(db, run_id)

    now = datetime.now(timezone.utc).isoformat()
    I = ids(run_id)
    tag = {config.RUN_TAG_FIELD: run_id}

    agencies = [
        {
            "_id": I["ag_active"],
            "id": I["ag_active"],
            "slug": I["ag_active"],
            "name": f"D7R2 Active {run_id[-8:]}",
            "status": "active",
            "is_active": True,
            "activation_status": "active",
            "mls_enabled": True,
            **tag,
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": I["ag_b"],
            "id": I["ag_b"],
            "slug": I["ag_b"],
            "name": f"D7R2 Branch {run_id[-8:]}",
            "status": "active",
            "is_active": True,
            "activation_status": "active",
            "mls_enabled": True,
            **tag,
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": I["ag_inactive"],
            "id": I["ag_inactive"],
            "slug": I["ag_inactive"],
            "name": f"D7R2 Inactive {run_id[-8:]}",
            "status": "inactive",
            "is_active": False,
            "activation_status": "pending",
            **tag,
            "created_at": now,
            "updated_at": now,
        },
    ]
    db.agencies.insert_many(agencies)

    password = "D7R2-" + secrets.token_urlsafe(12)
    users = []
    for uid, email, aids, active in [
        (I["user_a"], I["email_a"], [I["ag_active"]], I["ag_active"]),
        (I["user_b"], I["email_b"], [I["ag_b"]], I["ag_b"]),
        (I["user_x"], I["email_x"], [I["ag_inactive"]], I["ag_inactive"]),
    ]:
        users.append(
            {
                "id": uid,
                "email": email,
                "password_hash": hash_password(password),
                "name": f"D7R2 {uid}",
                "role": "agency_admin",
                "agency_ids": aids,
                "active_agency_id": active,
                "is_active": True,
                "email_verified": True,
                "lang": "it",
                **tag,
                "created_at": now,
                "updated_at": now,
            }
        )
    db.users.insert_many(users)

    prop = {
        "id": I["prop"],
        "title": f"D7R2 Property {run_id[-8:]}",
        "property_type": "appartamento",
        "operation": "sale",
        "status": "active",
        "city": "Milano",
        "price": 250000,
        "photos": [{"url": "https://example.com/d7r2-a.jpg"}],
        "description": "x" * 80,
        "agency_id": I["ag_active"],
        "mls_shareable": True,
        "share_on_mls": True,
        "visibility": "mls",
        "created_at": now,
        "updated_at": now,
        **tag,
    }
    db.properties.insert_one(prop)

    client = {
        "id": I["client"],
        "agency_id": I["ag_active"],
        "name": "D7R2 Client",
        "email": f"d7r2.{run_id[-8:]}.client@{config.EMAIL_DOMAIN}",
        "type": "buyer",
        **tag,
        "created_at": now,
        "updated_at": now,
    }
    db.clients.insert_one(client)

    cc = {
        "_id": I["cc"],
        "id": I["cc"],
        "legal_name": f"D7R2 CC {run_id[-8:]}",
        "country_code": "IT",
        "vat_number_normalized": f"IT{secrets.randbelow(10**11):011d}",
        "customer_status": "active",
        "commercial_status": "active",
        "operational_status": "operable",
        "main_admin_user_id": I["user_a"],
        "main_admin_appointed_at": now,
        **tag,
        "created_at": now,
        "updated_at": now,
    }
    org = {
        "_id": I["org"],
        "id": I["org"],
        "name": f"D7R2 Org {run_id[-8:]}",
        "commercial_customer_id": I["cc"],
        "type": "main",
        **tag,
        "created_at": now,
    }
    db.commercial_customers.insert_one(cc)
    db.organizations.insert_one(org)
    db.agencies.update_one(
        {"id": I["ag_active"], **scoped_filter(run_id)},
        {
            "$set": {
                "commercial_customer_id": I["cc"],
                "organization_id": I["org"],
                "is_main_branch": True,
            }
        },
    )
    db.agencies.update_one(
        {"id": I["ag_b"], **scoped_filter(run_id)},
        {
            "$set": {
                "commercial_customer_id": I["cc"],
                "organization_id": I["org"],
                "is_main_branch": False,
                "parent_agency_id": I["ag_active"],
            }
        },
    )
    db.users.update_one(
        {"id": I["user_a"], **scoped_filter(run_id)},
        {"$set": {"commercial_customer_id": I["cc"]}},
    )
    db.users.update_one(
        {"id": I["user_b"], **scoped_filter(run_id)},
        {"$set": {"commercial_customer_id": I["cc"]}},
    )

    plain = generate_plaintext_key()
    db.api_keys.insert_one(
        {
            "id": I["key_active"],
            "agency_id": I["ag_active"],
            "key_hash": hash_key(plain),
            "is_active": True,
            "revoked_at": None,
            "credits_balance": 100,
            "allowed_origins": [],
            "name": "d7r2-active",
            **tag,
            "created_at": now,
        }
    )

    secrets_obj = {
        "password": password,
        "api_key_active": plain,
        "api_key_invalid": KEY_PREFIX + ("z" * 28),
        "run_id": run_id,
        "note": "synthetic staging only — mode 0600 under artifacts/d7/<run_id>/secrets/",
    }
    secrets_path = write_secrets_file(run_path, secrets_obj)

    meta = {
        "run_id": run_id,
        "ids": I,
        "emails": {
            "admin_a": I["email_a"],
            "admin_b": I["email_b"],
            "admin_inactive": I["email_x"],
            "invitee": I["email_invitee"],
        },
        "secrets_path": str(secrets_path),
        "forensic_note": (
            "D7-1 used @example.invalid then patched to @example.com; "
            "this harness seeds @example.com natively. Historical A6 is not SoT."
        ),
    }
    write_json(run_path / "seed_meta.json", meta)
    return meta


def _scoped_cleanup(db, run_id: str) -> dict[str, int]:
    """Delete ONLY docs with this run_id. Never wipe by legacy d7_tag alone."""
    flt = scoped_filter(run_id)
    if not run_id or len(run_id) < 12:
        raise RuntimeError("refusing_cleanup_weak_run_id")
    counts = {}
    for coll in (
        "users",
        "agencies",
        "properties",
        "api_keys",
        "clients",
        "commercial_customers",
        "organizations",
        "branches",
        "agency_invites",
        "collaborations",
        "visits",
        "visit_feedback",
        "deals",
        "deal_proposals",
        "collab_chat_threads",
        "collab_chat_messages",
        "chat_threads",
        "chat_messages",
    ):
        if coll in db.list_collection_names():
            counts[coll] = db[coll].delete_many(flt).deleted_count
    return counts


def cleanup_run(run_id: str) -> dict[str, int]:
    db = connect_staging_db()
    return _scoped_cleanup(db, run_id)
