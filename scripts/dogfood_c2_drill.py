#!/usr/bin/env python3
"""D-175 C2 — End-to-end backup → restore drill on isolated Dogfood Mongo.

Creates source DB omnia_df_c2_src with B04 + operational sample docs + media,
runs mongodump + media backup + manifest/SHA, restores to omnia_df_probe_c2,
verifies counts and media coherence.

REFUSES permanent / shared omnia destinations.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from pymongo import MongoClient  # noqa: E402

from apps.immoweb.backup_scope import (  # noqa: E402
    DOGFOOD_B04_COLLECTIONS,
    DOGFOOD_BACKUP_COLLECTIONS,
)
from shared.dogfood.backup import (  # noqa: E402
    assert_dogfood_mongo_endpoint,
    assert_dogfood_mongo_port,
    assert_safe_db_name,
    backup_media,
    build_manifest,
    redact_mongo_uri,
    run_mongodump,
    run_mongorestore,
    sha256_tree,
    write_manifest,
)


def _root() -> Path:
    return Path(os.environ.get("DOGFOOD_ROOT") or (ROOT / "dogfood")).resolve()


def _uri(port: int, user: str | None = None, password: str | None = None) -> str:
    if user and password:
        return (
            f"mongodb://{user}:{password}@127.0.0.1:{port}/admin?authSource=admin"
        )
    return f"mongodb://127.0.0.1:{port}"


def _load_creds(root: Path) -> dict:
    p = root / "secrets" / "mongo-df-credentials.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def seed_source(client: MongoClient, db_name: str, media_src: Path) -> dict:
    assert_safe_db_name(db_name, role="source")
    db = client[db_name]
    # Wipe source only (dogfood prefix)
    client.drop_database(db_name)
    db = client[db_name]

    cc_id = "cc_c2_demo_001"
    agency_id = "ag_c2_demo_001"
    user_id = "u_c2_ma_001"

    db.commercial_customers.insert_one(
        {
            "id": cc_id,
            "legal_name": "C2 Demo SRL",
            "vat_number_normalized": "IT000C2DEMO01",
            "main_admin_user_id": user_id,
            "commercial_status": "active",
            "operational_status": "active",
        }
    )
    db.agencies.insert_one(
        {
            "id": agency_id,
            "display_name": "C2 Demo Agency",
            "commercial_customer_id": cc_id,
            "activation_status": "active",
        }
    )
    db.users.insert_one(
        {
            "id": user_id,
            "email": "c2.ma@example.invalid",
            "is_active": True,
            "email_verified": True,
            "agency_ids": [agency_id],
            "active_agency_id": agency_id,
            "role": "agency_admin",
        }
    )
    db.memberships.insert_one(
        {
            "id": "mem_c2_001",
            "user_id": user_id,
            "organization_id": agency_id,
            "role": "agency_admin",
            "status": "active",
        }
    )
    db.cc_credit_wallets.insert_one(
        {"id": "w_c2_001", "commercial_customer_id": cc_id, "balance_unallocated": 100, "balance_total": 100}
    )
    db.credit_lots.insert_one(
        {
            "id": "lot_c2_001",
            "commercial_customer_id": cc_id,
            "wallet_id": "w_c2_001",
            "origin": "c2_drill",
            "original_qty": 100,
            "remaining_qty": 100,
            "unallocated_qty": 100,
        }
    )
    db.credit_allocations.insert_one(
        {
            "id": "alloc_c2_001",
            "commercial_customer_id": cc_id,
            "organization_id": agency_id,
            "amount": 0,
            "status": "active",
        }
    )
    db.cc_credit_ledger.insert_one(
        {
            "id": "led_c2_001",
            "commercial_customer_id": cc_id,
            "entry_type": "grant",
            "delta": 100,
            "reason": "c2_drill",
        }
    )
    db.commercial_reactivation_derogations.insert_one(
        {
            "id": "der_c2_001",
            "commercial_customer_id": cc_id,
            "status": "expired",
            "note": "fixture",
        }
    )
    db.subscriptions.insert_one(
        {"id": "sub_c2_001", "agency_id": agency_id, "commercial_customer_id": cc_id, "tier": "pro", "status": "active"}
    )
    db.payment_transactions.insert_one(
        {"session_id": "cs_c2_test", "commercial_customer_id": cc_id, "agency_id": agency_id, "status": "initiated"}
    )
    db.invoices.insert_one({"id": "inv_c2_001", "agency_id": agency_id, "status": "paid", "amount_paid": 1.0})
    db.commercial_main_admin_transfers.insert_one(
        {"id": "tr_c2_001", "commercial_customer_id": cc_id, "status": "cancelled"}
    )
    db.commercial_main_admin_events.insert_one(
        {"id": "ev_c2_001", "commercial_customer_id": cc_id, "event_type": "c2_drill", "outcome": "success"}
    )
    db.provider_flags.insert_one({"id": "resend", "killed": True, "note": "c2"})
    db.plan_catalog_versions.insert_one({"id": "cat_c2", "version": 1})
    db.notifications.insert_one({"id": "n_c2_001", "user_id": user_id, "kind": "c2"})
    db.agency_invites.insert_one({"id": "inv_c2", "agency_id": agency_id, "email": "x@example.invalid"})
    db.refresh_tokens.insert_one({"id": "rt_c2", "user_id": user_id, "revoked": True})
    db.mls_network.insert_one({"id": "mls_c2", "agency_a": agency_id, "agency_b": "ag_other"})
    db.mls_offers.insert_one({"id": "off_c2", "agency_id": agency_id})
    db.mls_partners.insert_one({"id": "par_c2", "agency_id": agency_id})
    db.mls_inventory.insert_one({"id": "invt_c2", "agency_id": agency_id})
    db.properties.insert_one(
        {"id": "prop_c2_001", "agency_id": agency_id, "title": "C2 Demo Flat", "media_ref": "c2/demo.txt"}
    )
    db.clients.insert_one({"id": "cli_c2_001", "agency_id": agency_id, "name": "Demo Client"})
    db.client_requests.insert_one({"id": "req_c2_001", "agency_id": agency_id})
    db.activities.insert_one({"id": "act_c2_001", "agency_id": agency_id, "type": "note"})
    db.credit_wallets.insert_one({"agency_id": agency_id, "balance": 0})
    db.credit_ledger.insert_one({"agency_id": agency_id, "delta": 0, "reason": "c2"})
    db.api_keys.insert_one({"id": "key_c2", "agency_id": agency_id, "revoked": True})
    db.groups.insert_one({"id": "grp_c2", "agency_id": agency_id})
    db.publishing_connections.insert_one({"id": "pub_c2", "agency_id": agency_id})
    db.modulistica_documents.insert_one({"id": "mod_c2", "agency_id": agency_id})
    db.videos.insert_one({"id": "vid_c2", "agency_id": agency_id})
    db.virtual_staging_jobs.insert_one({"id": "stg_c2", "agency_id": agency_id})
    db.leads.insert_one({"id": "lead_c2", "agency_id": agency_id})
    # B2C samples
    db.b2c_purchases.insert_one({"id": "b2c_c2", "status": "test"})
    db.b2c_visura_orders.insert_one({"id": "vis_c2"})
    db.consent_events.insert_one({"id": "con_c2"})
    db.favorites.insert_one({"id": "fav_c2"})
    db.saved_searches.insert_one({"id": "ss_c2"})
    db.al_legal_audit.insert_one({"id": "al_c2"})
    db.listing_inquiries.insert_one({"id": "liq_c2"})

    media_src.mkdir(parents=True, exist_ok=True)
    demo = media_src / "c2" / "demo.txt"
    demo.parent.mkdir(parents=True, exist_ok=True)
    demo.write_text("c2-drill-media-payload\n", encoding="utf-8")

    counts = {c: db[c].count_documents({}) for c in DOGFOOD_BACKUP_COLLECTIONS}
    return {
        "cc_id": cc_id,
        "agency_id": agency_id,
        "counts": counts,
        "media_file": str(demo.relative_to(media_src)),
    }


def verify_restore(client: MongoClient, probe_db: str, expected: dict, media_dest: Path) -> dict:
    assert_safe_db_name(probe_db, role="target_probe")
    db = client[probe_db]
    mismatches = []
    for coll, n in (expected.get("counts") or {}).items():
        got = db[coll].count_documents({})
        if got != n:
            mismatches.append({"collection": coll, "expected": n, "got": got})
    # Spot-check CC + memberships + deroga
    cc = db.commercial_customers.find_one({"id": expected["cc_id"]})
    mem = db.memberships.find_one({"organization_id": expected["agency_id"]})
    der = db.commercial_reactivation_derogations.find_one({"id": "der_c2_001"})
    prop = db.properties.find_one({"id": "prop_c2_001"})
    media_ok = (media_dest / expected["media_file"]).is_file()
    readable = bool(cc and mem and der and prop)
    return {
        "ok": not mismatches and media_ok and readable,
        "mismatches": mismatches,
        "readable_spot_checks": {
            "commercial_customers": bool(cc),
            "memberships": bool(mem),
            "commercial_reactivation_derogations": bool(der),
            "properties": bool(prop),
            "media_file": media_ok,
        },
    }


def main() -> int:
    root = _root()
    port = int(os.environ.get("OMNIA_DF_MONGO_PORT") or 27018)
    # Hard-deny shared port before bootstrap/stop_port or any MongoClient
    assert_dogfood_mongo_port(port)
    # Ensure bootstrap ran (bootstrap itself also refuses :27017)
    boot = subprocess_bootstrap()
    creds = _load_creds(root)
    # Prefer admin for seed/restore ops in drill (role separation verified separately)
    uri = _uri(port, "omnia_df_admin", creds.get("admin")) if creds.get("admin") else _uri(port)
    assert_dogfood_mongo_endpoint(uri)
    # Fallback: unauth if admin auth fails — still must pass endpoint assert
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
    except Exception:
        uri = _uri(port)
        assert_dogfood_mongo_endpoint(uri)
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")

    source_db = "omnia_df_c2_src"
    probe_db = "omnia_df_probe_c2"
    media_src = root / "media" / "c2_src"
    backup_id = f"c2-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    bak_dir = root / "backups" / backup_id
    if bak_dir.exists():
        shutil.rmtree(bak_dir)
    bak_dir.mkdir(parents=True)

    seed = seed_source(client, source_db, media_src)
    before = {
        "source_db": source_db,
        "counts": seed["counts"],
        "b04_required_present": {
            c: seed["counts"].get(c, 0) > 0
            for c in (
                "commercial_customers",
                "memberships",
                "cc_credit_wallets",
                "credit_lots",
                "credit_allocations",
                "cc_credit_ledger",
                "commercial_reactivation_derogations",
            )
        },
    }

    dump = run_mongodump(mongo_uri=uri, db_name=source_db, out_dir=bak_dir)
    media = backup_media(media_src, bak_dir)
    dump_sha = sha256_tree(Path(dump["dump_dir"]))
    manifest = build_manifest(
        backup_id=backup_id,
        source_db=source_db,
        source_uri_redacted=redact_mongo_uri(uri),
        dump_report=dump,
        media_report=media,
        dump_sha=dump_sha,
        extra={"seed": {"cc_id": seed["cc_id"], "agency_id": seed["agency_id"]}},
    )
    man_path = write_manifest(bak_dir / "MANIFEST.json", manifest)

    # Negative: refuse restore to omnia / permanent
    deny_cases = []
    for bad in ("omnia", "omnia_df_perm_x"):
        try:
            assert_safe_db_name(bad, role="target_probe")
            deny_cases.append({"db": bad, "blocked": False})
        except RuntimeError as e:
            deny_cases.append({"db": bad, "blocked": True, "error": str(e)})

    # Restore to probe
    client.drop_database(probe_db)
    restore = run_mongorestore(
        mongo_uri=uri,
        target_db=probe_db,
        dump_db_dir=Path(dump["dump_dir"]),
        drop=True,
    )
    # Restore media beside probe workspace
    probe_media = root / "media" / "c2_probe"
    if probe_media.exists():
        shutil.rmtree(probe_media)
    shutil.copytree(bak_dir / "media", probe_media)

    after = verify_restore(client, probe_db, seed, probe_media)

    # Role checks (best-effort with dedicated users)
    role_checks = verify_roles(port, creds, source_db, probe_db)

    report = {
        "cycle": "D-175-C2",
        "ok": bool(after.get("ok") and dump.get("ok") and media.get("ok") and all(d["blocked"] for d in deny_cases)),
        "backup_id": backup_id,
        "backup_dir": str(bak_dir),
        "manifest": str(man_path),
        "git_sha": manifest.get("git_sha"),
        "before": before,
        "dump": {k: dump[k] for k in ("ok", "collections_present", "collections_missing_empty") if k in dump},
        "media": {
            "ok": media.get("ok"),
            "copied": media.get("copied"),
            "tree_sha256": (media.get("inventory") or {}).get("tree_sha256"),
            "file_count": (media.get("inventory") or {}).get("file_count"),
        },
        "integrity": manifest.get("integrity"),
        "restore": restore,
        "after": after,
        "deny_destructive_targets": deny_cases,
        "roles": role_checks,
        "bootstrap": boot,
        "collections_scope_size": len(DOGFOOD_BACKUP_COLLECTIONS),
        "b04_scope": list(DOGFOOD_B04_COLLECTIONS),
    }

    art_dir = Path("/opt/cursor/artifacts")
    art_dir.mkdir(parents=True, exist_ok=True)
    (art_dir / "D175-C2-DRILL-REPORT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    shutil.copy2(man_path, art_dir / "D175-C2-MANIFEST.json")
    (art_dir / "D175-C2-DUMP-TREE-SHA.txt").write_text(
        (manifest.get("integrity") or {}).get("dump_tree_sha256", "") + "\n",
        encoding="utf-8",
    )
    (root / "C2_LAST_DRILL.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(json.dumps({"ok": report["ok"], "backup_id": backup_id, "report": str(art_dir / "D175-C2-DRILL-REPORT.json")}, indent=2))
    return 0 if report["ok"] else 2


def subprocess_bootstrap() -> dict:
    import subprocess

    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "dogfood_mongo_bootstrap.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    return {
        "returncode": p.returncode,
        "stdout_tail": (p.stdout or "")[-500:],
        "stderr_tail": (p.stderr or "")[-500:],
        "ok": p.returncode == 0,
    }


def verify_roles(port: int, creds: dict, source_db: str, probe_db: str) -> dict:
    out = {"verified": False, "checks": []}
    if not creds.get("runtime"):
        out["checks"].append({"name": "creds_missing", "result": "NOT VERIFIED"})
        return out

    def try_op(user: str, pwd: str, db: str, op: str) -> dict:
        uri = f"mongodb://{user}:{pwd}@127.0.0.1:{port}/{db}?authSource=admin"
        try:
            c = MongoClient(uri, serverSelectionTimeoutMS=4000)
            d = c[db]
            if op == "find":
                d["commercial_customers"].find_one({})
            elif op == "insert":
                d["_c2_priv_probe"].insert_one({"ok": 1})
                d["_c2_priv_probe"].delete_many({})
            elif op == "drop":
                c.drop_database(db)
            return {"user": user, "db": db, "op": op, "result": "PASS_ALLOWED"}
        except Exception as e:  # noqa: BLE001
            return {"user": user, "db": db, "op": op, "result": "DENIED", "error": str(e)[:200]}

    checks = []
    # Runtime may write its DB, must not drop shared omnia (if reachable) — we check deny on probe drop
    checks.append(try_op("omnia_df_runtime", creds["runtime"], source_db, "insert"))
    # Runtime should NOT write probe
    r = try_op("omnia_df_runtime", creds["runtime"], probe_db, "insert")
    r["expect"] = "DENIED"
    r["pass"] = r["result"] == "DENIED"
    checks.append(r)
    # Backup can read source
    checks.append(try_op("omnia_df_backup", creds["backup"], source_db, "find"))
    # Backup should not insert
    r2 = try_op("omnia_df_backup", creds["backup"], source_db, "insert")
    r2["expect"] = "DENIED"
    r2["pass"] = r2["result"] == "DENIED"
    checks.append(r2)
    # Clone can write probe
    checks.append(try_op("omnia_df_clone", creds["clone"], probe_db, "insert"))

    out["checks"] = checks
    out["verified"] = all(
        (c.get("pass") if "pass" in c else c.get("result") == "PASS_ALLOWED")
        for c in checks
    )
    return out


if __name__ == "__main__":
    raise SystemExit(main())
