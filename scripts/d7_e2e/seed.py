"""Deterministic synthetic fixtures tagged with d7_run_id — @example.com only."""
from __future__ import annotations

import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import config
from .artifacts import write_json, write_secrets_file
from .inventory import CreatedInventory, load_inventory
from .mongo_util import connect_staging_db, scoped_filter
from .run_id import validate_run_id

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
        # FIX4 — third ACTIVE independent tenant (iso), own CC
        "ag_iso": f"d7r2-{short}-ag-iso",
        "user_a": f"d7r2-{short}-user-a",
        "user_b": f"d7r2-{short}-user-b",
        "user_x": f"d7r2-{short}-user-x",
        "user_iso": f"d7r2-{short}-user-iso",
        "email_a": f"d7r2.{short}.admin.a@{dom}",
        "email_b": f"d7r2.{short}.admin.b@{dom}",
        "email_x": f"d7r2.{short}.admin.x@{dom}",
        "email_iso": f"d7r2.{short}.admin.iso@{dom}",
        "email_invitee": f"d7r2.{short}.invitee@{dom}",
        "prop": f"d7r2-{short}-prop",
        "client": f"d7r2-{short}-client",
        "cc": f"d7r2-{short}-cc",
        "org": f"d7r2-{short}-org",
        "cc_iso": f"d7r2-{short}-cc-iso",
        "org_iso": f"d7r2-{short}-org-iso",
        "key_active": f"d7r2-{short}-key-a",
    }


def seed(run_id: str, run_path) -> dict[str, Any]:
    from shared.auth.api_key import KEY_PREFIX, generate_plaintext_key, hash_key
    from shared.auth.hashing import hash_password

    rid = validate_run_id(run_id)
    db = connect_staging_db()
    inv = CreatedInventory(run_path, rid)
    _scoped_cleanup(db, rid, inventory=inv)

    now = datetime.now(timezone.utc).isoformat()
    I = ids(rid)
    tag = {config.RUN_TAG_FIELD: rid}

    agencies = [
        {
            "_id": I["ag_active"],
            "id": I["ag_active"],
            "slug": I["ag_active"],
            "name": f"D7R2 Active {rid[-8:]}",
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
            "name": f"D7R2 Branch {rid[-8:]}",
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
            "name": f"D7R2 Inactive {rid[-8:]}",
            "status": "inactive",
            "is_active": False,
            "activation_status": "pending",
            **tag,
            "created_at": now,
            "updated_at": now,
        },
        {
            "_id": I["ag_iso"],
            "id": I["ag_iso"],
            "slug": I["ag_iso"],
            "name": f"D7R2 Iso Active {rid[-8:]}",
            "status": "active",
            "is_active": True,
            "activation_status": "active",
            "mls_enabled": True,
            **tag,
            "created_at": now,
            "updated_at": now,
        },
    ]
    db.agencies.insert_many(agencies)
    inv.register_many("agencies", [a["id"] for a in agencies], source="seed")

    password = "D7R2-" + secrets.token_urlsafe(12)
    users = []
    for uid, email, aids, active in [
        (I["user_a"], I["email_a"], [I["ag_active"]], I["ag_active"]),
        (I["user_b"], I["email_b"], [I["ag_b"]], I["ag_b"]),
        (I["user_x"], I["email_x"], [I["ag_inactive"]], I["ag_inactive"]),
        (I["user_iso"], I["email_iso"], [I["ag_iso"]], I["ag_iso"]),
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
    inv.register_many("users", [u["id"] for u in users], source="seed")

    prop = {
        "id": I["prop"],
        "title": f"D7R2 Property {rid[-8:]}",
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
    inv.register("properties", I["prop"], source="seed")

    client = {
        "id": I["client"],
        "agency_id": I["ag_active"],
        "name": "D7R2 Client",
        "email": f"d7r2.{rid[-8:]}.client@{config.EMAIL_DOMAIN}",
        "type": "buyer",
        **tag,
        "created_at": now,
        "updated_at": now,
    }
    db.clients.insert_one(client)
    inv.register("clients", I["client"], source="seed")

    cc = {
        "_id": I["cc"],
        "id": I["cc"],
        "legal_name": f"D7R2 CC {rid[-8:]}",
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
        "name": f"D7R2 Org {rid[-8:]}",
        "commercial_customer_id": I["cc"],
        "type": "main",
        **tag,
        "created_at": now,
    }
    # Independent CC for iso tenant — NOT the CC under test
    cc_iso = {
        "_id": I["cc_iso"],
        "id": I["cc_iso"],
        "legal_name": f"D7R2 CC Iso {rid[-8:]}",
        "country_code": "IT",
        "vat_number_normalized": f"IT{secrets.randbelow(10**11):011d}",
        "customer_status": "active",
        "commercial_status": "active",
        "operational_status": "operable",
        "main_admin_user_id": I["user_iso"],
        "main_admin_appointed_at": now,
        **tag,
        "created_at": now,
        "updated_at": now,
    }
    org_iso = {
        "_id": I["org_iso"],
        "id": I["org_iso"],
        "name": f"D7R2 Org Iso {rid[-8:]}",
        "commercial_customer_id": I["cc_iso"],
        "type": "main",
        **tag,
        "created_at": now,
    }
    db.commercial_customers.insert_many([cc, cc_iso])
    db.organizations.insert_many([org, org_iso])
    inv.register_many("commercial_customers", [I["cc"], I["cc_iso"]], source="seed")
    inv.register_many("organizations", [I["org"], I["org_iso"]], source="seed")

    db.agencies.update_one(
        {"id": I["ag_active"], **scoped_filter(rid)},
        {
            "$set": {
                "commercial_customer_id": I["cc"],
                "organization_id": I["org"],
                "is_main_branch": True,
            }
        },
    )
    db.agencies.update_one(
        {"id": I["ag_b"], **scoped_filter(rid)},
        {
            "$set": {
                "commercial_customer_id": I["cc"],
                "organization_id": I["org"],
                "is_main_branch": False,
                "parent_agency_id": I["ag_active"],
            }
        },
    )
    db.agencies.update_one(
        {"id": I["ag_iso"], **scoped_filter(rid)},
        {
            "$set": {
                "commercial_customer_id": I["cc_iso"],
                "organization_id": I["org_iso"],
                "is_main_branch": True,
            }
        },
    )
    db.users.update_one(
        {"id": I["user_a"], **scoped_filter(rid)},
        {"$set": {"commercial_customer_id": I["cc"]}},
    )
    db.users.update_one(
        {"id": I["user_b"], **scoped_filter(rid)},
        {"$set": {"commercial_customer_id": I["cc"]}},
    )
    db.users.update_one(
        {"id": I["user_iso"], **scoped_filter(rid)},
        {"$set": {"commercial_customer_id": I["cc_iso"]}},
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
    inv.register("api_keys", I["key_active"], source="seed")

    secrets_obj = {
        "password": password,
        "api_key_active": plain,
        "api_key_invalid": KEY_PREFIX + ("z" * 28),
        "run_id": rid,
        "note": "synthetic staging only — mode 0600 under artifacts/d7/<run_id>/secrets/",
    }
    secrets_path = write_secrets_file(run_path, secrets_obj)

    meta = {
        "run_id": rid,
        "ids": I,
        "emails": {
            "admin_a": I["email_a"],
            "admin_b": I["email_b"],
            "admin_inactive": I["email_x"],
            "admin_iso": I["email_iso"],
            "invitee": I["email_invitee"],
        },
        "relations": {
            "cc_under_test": I["cc"],
            "main_admin_user": I["user_a"],
            "branch_user": I["user_b"],
            "iso_agency": I["ag_iso"],
            "iso_user": I["user_iso"],
            "iso_cc": I["cc_iso"],
            "iso_note": (
                "iso tenant is ACTIVE, independent CC; T4 iso calls "
                "GET /api/billing/commercial/main-admin?commercial_customer_id=<cc_under_test> "
                "expecting 403 forbidden"
            ),
        },
        "secrets_path": str(secrets_path),
        "inventory_path": str(inv.path),
        "forensic_note": (
            "D7-1 used @example.invalid then patched to @example.com; "
            "this harness seeds @example.com natively. Historical A6 is not SoT."
        ),
    }
    write_json(run_path / "seed_meta.json", meta)
    return meta


def _delete_by_ids(db, collection: str, ids: list[str]) -> int:
    if not ids:
        return 0
    # Exact id match only — never bare filters (no email/agency/role/date)
    return db[collection].delete_many({"id": {"$in": list(ids)}}).deleted_count


def _collection_exists(db, name: str) -> bool:
    try:
        return name in db.list_collection_names()
    except Exception:
        # FakeDB in unit tests may always succeed via __getitem__
        return True


def _scoped_cleanup(db, run_id: str, inventory: CreatedInventory | None = None) -> dict[str, Any]:
    """Delete ONLY docs for this validated run_id via inventory IDs + tagged seed.

    Never deletes uncertain / ambiguous records. Never deletes by email/agency alone.
    Returns counts + classification (CLEAN|DIRTY|BLOCKED).
    """
    rid = validate_run_id(run_id)
    counts: dict[str, Any] = {}
    notes: list[str] = []
    uncertain: list[Any] = []

    inv = inventory
    if inv is not None:
        if inv.has_pending():
            notes.append("pending_unflushed_ids_present")
        if inv.has_open_intents():
            notes.append("open_intents_present")
        if inv.has_uncertain():
            notes.append("uncertain_present")
            uncertain = list(inv.as_dict().get("uncertain") or [])

        # 1a) Pending keys parsed as collection:id (D2) — exact id only
        pending_by_coll: dict[str, list[str]] = {}
        for coll, doc_id in inv.pending_id_pairs():
            pending_by_coll.setdefault(coll, []).append(doc_id)
        for coll, id_list in pending_by_coll.items():
            n = _delete_by_ids(db, coll, id_list)
            counts[f"pending:{coll}"] = n

        # 1b) Confirmed inventory IDs
        for coll, id_list in inv.all_ids().items():
            # Skip users not created_by_run (pre-existing protection)
            if coll == "users":
                deletable = []
                for uid in id_list:
                    meta = inv.meta_for(coll, uid)
                    if meta.get("created_by_run", True):
                        deletable.append(uid)
                    else:
                        notes.append(f"skip_preexisting_user:{uid}")
                counts[f"inv:{coll}"] = _delete_by_ids(db, coll, deletable)
            else:
                counts[f"inv:{coll}"] = _delete_by_ids(db, coll, id_list)

    # 2) Tagged seed cleanup (exact d7_run_id)
    flt = scoped_filter(rid)
    for coll in config.SEED_TAGGED_COLLECTIONS:
        if _collection_exists(db, coll):
            counts[f"tag:{coll}"] = db[coll].delete_many(flt).deleted_count

    # 3) Tagged delete on MLS/deals/side-effects if somehow tagged
    for coll in (
        *config.MLS_RUNTIME_COLLECTIONS,
        config.DEALS_COLLECTION,
        *config.SIDE_EFFECT_COLLECTIONS,
    ):
        if _collection_exists(db, coll):
            n = db[coll].delete_many(flt).deleted_count
            if n:
                counts[f"tag:{coll}"] = n

    # Classification — never CLEAN with pending/intents/uncertain
    dirty = bool(notes) or bool(uncertain)
    if inv is not None and not inv.certification_ok():
        dirty = True
    classification = "DIRTY" if dirty else "CLEAN"

    out: dict[str, Any] = {
        **{k: v for k, v in counts.items() if not str(k).startswith("_")},
        "classification": classification,
        "run_id": rid,
    }
    if notes:
        out["_notes"] = notes
    if uncertain:
        out["uncertain"] = uncertain
        out["classification"] = "DIRTY"
    return out


def cleanup_run(run_id: str, run_path: Path | None = None) -> dict[str, Any]:
    rid = validate_run_id(run_id)
    db = connect_staging_db()
    inv = None
    path: Path | None = None
    if run_path is not None:
        path = Path(run_path)
        inv = load_inventory(path, rid)
    else:
        from .artifacts import artifacts_d7_root

        candidate = artifacts_d7_root() / rid
        if candidate.exists():
            path = candidate
            inv = load_inventory(candidate, rid)
    result = _scoped_cleanup(db, rid, inventory=inv)
    if path is not None:
        from .artifacts import write_json_overwrite

        write_json_overwrite(path / "cleanup.json", result)
        # Update / write cleanup classification sidecar
        write_json_overwrite(
            path / "cleanup_classification.json",
            {
                "classification": result.get("classification"),
                "run_id": rid,
                "notes": result.get("_notes"),
            },
        )
    return result


def post_cleanup_verify(
    db,
    run_id: str,
    inventory: CreatedInventory | None,
) -> dict[str, Any]:
    """Verify ledger IDs are gone; tag count for run_id is 0 on scoped collections."""
    rid = validate_run_id(run_id)
    remaining: dict[str, list[str]] = {}
    if inventory is not None:
        for coll, id_list in inventory.all_ids().items():
            left = []
            for doc_id in id_list:
                meta = inventory.meta_for(coll, doc_id)
                if coll == "users" and not meta.get("created_by_run", True):
                    continue
                doc = db[coll].find_one({"id": doc_id}, {"_id": 0, "id": 1})
                if doc:
                    left.append(doc_id)
            if left:
                remaining[coll] = left
    tag_left: dict[str, int] = {}
    flt = scoped_filter(rid)
    for coll in (
        *config.SEED_TAGGED_COLLECTIONS,
        *config.MLS_RUNTIME_COLLECTIONS,
        config.DEALS_COLLECTION,
        *config.SIDE_EFFECT_COLLECTIONS,
    ):
        if _collection_exists(db, coll):
            n = db[coll].count_documents(flt)
            if n:
                tag_left[coll] = n
    ok = not remaining and not tag_left
    return {
        "ok": ok,
        "remaining_ids": remaining,
        "tag_remaining": tag_left,
        "classification": "CLEAN" if ok else "DIRTY",
    }


# Collection mapping exposed for unit tests
CLEANUP_REAL_COLLECTIONS = (
    *config.SEED_TAGGED_COLLECTIONS,
    *config.MLS_RUNTIME_COLLECTIONS,
    config.DEALS_COLLECTION,
    *config.SIDE_EFFECT_COLLECTIONS,
)
PHANTOM_COLLECTIONS_REMOVED = (
    "collaborations",
    "visits",
    "visit_feedback",
    "deal_proposals",
    "collab_chat_threads",
    "collab_chat_messages",
    "chat_threads",
    "chat_messages",
)
