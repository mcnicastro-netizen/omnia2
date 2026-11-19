#!/usr/bin/env python3
"""D-175 C4 — Apply Founder manifest to a work-copy DB (never permanent).

Creates CC + Organizations + wallet structure.
Nominates Main Admin / memberships ONLY when users already exist.
Never invents accounts.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from pymongo import MongoClient  # noqa: E402

from shared.dogfood.c4_structure import (  # noqa: E402
    analyze_structure,
    assert_c4_seed_target,
    assert_vat_unique_second_cc_denied,
    attach_membership_if_user_exists,
    ensure_commercial_customer,
    ensure_organization,
    ensure_wallet,
    load_manifest,
    nominate_main_admin_if_user_exists,
)
from shared.dogfood.permanent import dogfood_root  # noqa: E402


def _client(port: int, creds: dict) -> MongoClient:
    uri = (
        f"mongodb://omnia_df_admin:{creds['admin']}@127.0.0.1:{port}/admin?authSource=admin"
    )
    return MongoClient(uri, serverSelectionTimeoutMS=8000)


def _creds(root: Path) -> dict:
    p = root / "secrets" / "mongo-df-credentials.json"
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, help="Path to Founder-filled C4 manifest JSON")
    ap.add_argument(
        "--db",
        default=os.environ.get("OMNIA_DOGFOOD_RUNTIME_DB") or "omnia_df_clean_c4",
        help="Work-copy DB (clean/cont) — permanent DENY",
    )
    ap.add_argument("--dry-run", action="store_true", help="Validate only — no writes")
    args = ap.parse_args()

    root = dogfood_root()
    port = int(os.environ.get("OMNIA_DF_MONGO_PORT") or 27018)
    assert_c4_seed_target(args.db)
    manifest = load_manifest(Path(args.manifest))

    if args.dry_run:
        print(json.dumps({"ok": True, "dry_run": True, "db": args.db, "manifest_ok": True}, indent=2))
        return 0

    creds = _creds(root)
    client = _client(port, creds)
    client.admin.command("ping")
    db = client[args.db]

    cc_spec = manifest["commercial_customer"]
    cc_res = ensure_commercial_customer(
        db,
        vat_number=cc_spec["vat_number"],
        legal_name=cc_spec["legal_name"],
        country_code=cc_spec.get("country_code") or "IT",
    )
    cc = cc_res["customer"]
    # Idempotent second ensure must not create duplicate
    ensure_commercial_customer(
        db,
        vat_number=cc_spec["vat_number"],
        legal_name=cc_spec["legal_name"],
        country_code=cc_spec.get("country_code") or "IT",
    )
    vat_check = assert_vat_unique_second_cc_denied(db, cc_spec["vat_number"])

    org_map = {}
    org_results = []
    for o in manifest["organizations"]:
        r = ensure_organization(
            db,
            commercial_customer_id=cc["id"],
            org_key=o["key"],
            display_name=o["display_name"],
        )
        org_map[o["key"]] = r["organization"]
        org_results.append(r)

    wallet = ensure_wallet(db, cc["id"])

    ma = nominate_main_admin_if_user_exists(
        db,
        commercial_customer_id=cc["id"],
        email=manifest.get("main_admin_email") or "",
    )

    admin_results = []
    for a in manifest.get("organization_admins") or []:
        org = org_map.get(a.get("org_key"))
        if not org:
            admin_results.append({"ok": False, "reason": "org_key_unknown", "org_key": a.get("org_key")})
            continue
        admin_results.append(
            attach_membership_if_user_exists(
                db,
                email=a.get("email") or "",
                organization_id=org["id"],
                operational_role="agency_admin",
            )
        )

    collab_results = []
    for c in manifest.get("collaborators") or []:
        org = org_map.get(c.get("org_key"))
        if not org:
            collab_results.append({"ok": False, "reason": "org_key_unknown"})
            continue
        collab_results.append(
            attach_membership_if_user_exists(
                db,
                email=c.get("email") or "",
                organization_id=org["id"],
                operational_role=c.get("role") or "agent",
            )
        )

    structure = analyze_structure(db, commercial_customer_id=cc["id"])
    report = {
        "cycle": "D-175-C4",
        "ok": True,
        "db": args.db,
        "commercial_customer_id": cc["id"],
        "vat_unique": vat_check,
        "cc": cc_res,
        "organizations": org_results,
        "wallet": {"count": structure["wallet_count"], **wallet},
        "main_admin": ma,
        "organization_admins": admin_results,
        "collaborators": collab_results,
        "structure": structure,
        "pending_founder": [
            x
            for x in [ma, *admin_results, *collab_results]
            if x.get("status") == "pending_founder"
        ],
        "ts": datetime.now(timezone.utc).isoformat(),
    }

    out_dir = root / "c4"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "LAST_APPLY.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    audit = out_dir / "APPLY_AUDIT.jsonl"
    with audit.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": report["ts"], "db": args.db, "cc_id": cc["id"], "pending": len(report["pending_founder"])}) + "\n")

    art = Path("/opt/cursor/artifacts")
    art.mkdir(parents=True, exist_ok=True)
    (art / "D175-C4-APPLY-REPORT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "ok": True,
                "db": args.db,
                "cc_id": cc["id"],
                "orgs": len(org_results),
                "pending_founder": len(report["pending_founder"]),
                "main_admin_status": ma.get("status"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"FAIL {e}", file=sys.stderr)
        raise SystemExit(2)
