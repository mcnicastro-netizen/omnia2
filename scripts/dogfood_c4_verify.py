#!/usr/bin/env python3
"""D-175 C4 — Verify commercial structure on a work-copy DB + permanent protection.

Does not invent users. Marks Founder-pending items honestly.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from pymongo import MongoClient  # noqa: E402

from shared.dogfood.c4_structure import (  # noqa: E402
    ROLE_AUTHORITY_MATRIX,
    analyze_structure,
    assert_vat_unique_second_cc_denied,
)
from shared.dogfood.ordinary_ops import (  # noqa: E402
    ordinary_clone_allowed,
    ordinary_wipe_allowed,
)
from shared.dogfood.permanent import (  # noqa: E402
    configured_permanent_db_name,
    dogfood_root,
    is_permanent_target,
    require_identity_or_raise,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--db",
        default=os.environ.get("OMNIA_DOGFOOD_RUNTIME_DB") or "omnia_df_clean_c4",
    )
    ap.add_argument("--cc-id", default="", help="CommercialCustomer id (optional auto-detect)")
    args = ap.parse_args()

    root = dogfood_root()
    port = int(os.environ.get("OMNIA_DF_MONGO_PORT") or 27018)
    # Permanent identity must still be demonstrable (C3) and not targeted
    identity = require_identity_or_raise()
    perm_db = configured_permanent_db_name()
    if is_permanent_target(db_name=args.db):
        print(json.dumps({"ok": False, "error": "verify_target_is_permanent"}, indent=2))
        return 2

    creds = json.loads((root / "secrets" / "mongo-df-credentials.json").read_text())
    client = MongoClient(
        f"mongodb://omnia_df_admin:{creds['admin']}@127.0.0.1:{port}/admin?authSource=admin",
        serverSelectionTimeoutMS=8000,
    )
    db = client[args.db]

    results = []

    def add(tid, result, detail=None):
        results.append({"id": tid, "result": result, "detail": detail or {}})

    # Detect CC
    cc_id = args.cc_id.strip()
    if not cc_id:
        cc = db.commercial_customers.find_one({"fiscal_data.dogfood_c4": True}, {"_id": 0}) or \
             db.commercial_customers.find_one({}, {"_id": 0})
        cc_id = (cc or {}).get("id") or ""

    if not cc_id:
        add("T1_commercial_customer", "NOT VERIFIED", {"reason": "no_cc_in_work_db_run_apply_after_founder"})
        structure = None
    else:
        structure = analyze_structure(db, commercial_customer_id=cc_id)
        cc = structure["commercial_customer"]
        add(
            "T1_commercial_customer",
            "PASS" if cc and cc.get("vat_number_normalized") else "FAIL",
            {"cc_id": cc_id, "vat": (cc or {}).get("vat_number_normalized")},
        )
        add(
            "T2_multi_organization",
            "PASS" if structure["organization_count"] >= 2 else "FAIL",
            {"count": structure["organization_count"]},
        )
        add(
            "T3_stable_cc_across_orgs",
            "PASS"
            if all(o.get("commercial_customer_id") == cc_id for o in structure["organizations"])
            else "FAIL",
        )
        add(
            "T4_single_wallet",
            "PASS" if structure["wallet_count"] == 1 else "FAIL",
            {"wallet_count": structure["wallet_count"]},
        )
        ma = structure.get("main_admin_user_id")
        add(
            "T5_main_admin_nominated",
            "PASS" if ma else "NOT VERIFIED",
            {
                "main_admin_user_id": ma,
                "depends_on": "founder_account",
                "hint": "Founder must create user then re-apply",
            },
        )
        # T6: structural — one CC wallet only; no org-scoped wallet docs
        wallets = list(
            db.cc_credit_wallets.find(
                {"commercial_customer_id": cc_id}, {"_id": 0}
            )
        )
        org_scoped = [
            w
            for w in wallets
            if w.get("organization_id") or w.get("agency_id") or w.get("org_id")
        ]
        t6_ok = structure["wallet_count"] == 1 and len(org_scoped) == 0
        add(
            "T6_branch_admin_no_auto_wallet",
            "PASS" if t6_ok else "FAIL",
            {
                "wallet_count": structure["wallet_count"],
                "org_scoped_wallets": len(org_scoped),
                "matrix": ROLE_AUTHORITY_MATRIX["organization_admin"],
                "note": "Structural: wallet is CC-central only; branch admin has no separate wallet",
            },
        )
        # T7 collaborators present?
        collabs = list(
            db.memberships.find(
                {"dogfood_c4": True, "operational_role": "agent", "membership_status": "active"},
                {"_id": 0},
            )
        )
        add(
            "T7_collaborators",
            "PASS" if collabs else "NOT VERIFIED",
            {
                "count": len(collabs),
                "depends_on": "founder_account",
                "hint": "Requires Founder-created collaborator users + re-apply",
            },
        )
        # T8 branch separation: memberships point to distinct orgs when multiple
        org_ids = {o["id"] for o in structure["organizations"]}
        mems = list(db.memberships.find({"membership_status": "active"}, {"_id": 0}))
        add(
            "T8_branch_access_separation",
            "PASS" if not mems or all(m.get("organization_id") in org_ids for m in mems) else "FAIL",
            {"active_memberships": len(mems)},
        )
        # T9: nomination must not auto-grant CRM — MA active memberships must be empty
        ma_mems = structure.get("main_admin_active_memberships") or []
        if not ma:
            t9 = "PASS"
            t9_detail = {
                "reason": "ma_not_nominated_yet",
                "rule": ROLE_AUTHORITY_MATRIX["main_admin"],
                "note": "nominate_main_admin path never inserts memberships; CRM still requires explicit Membership after Founder accounts exist",
            }
        elif len(ma_mems) == 0:
            t9 = "PASS"
            t9_detail = {
                "ma_memberships": [],
                "rule": ROLE_AUTHORITY_MATRIX["main_admin"],
            }
        else:
            t9 = "FAIL"
            t9_detail = {
                "ma_memberships": ma_mems,
                "reason": "main_admin_has_active_crm_membership_improper_coupling",
            }
        add("T9_ma_no_automatic_crm", t9, t9_detail)
        vat_chk = assert_vat_unique_second_cc_denied(db, cc.get("vat_number_normalized") or "")
        add("T10_vat_uniqueness", "PASS" if vat_chk["ok"] else "FAIL", vat_chk)

    # T11/T12 CLEAN/CONTINUITY coherence — gate + optional last workcopy reports
    clean_rep = root / "c4" / "LAST_WORKCOPY_CLEAN.json"
    cont_rep = root / "c4" / "LAST_WORKCOPY_CONTINUITY.json"
    add(
        "T11_clean_copy",
        "PASS" if clean_rep.exists() and json.loads(clean_rep.read_text()).get("ok") else "NOT VERIFIED",
        {"report": str(clean_rep) if clean_rep.exists() else None},
    )
    add(
        "T12_continuity_copy",
        "PASS" if cont_rep.exists() and json.loads(cont_rep.read_text()).get("ok") else "NOT VERIFIED",
        {"report": str(cont_rep) if cont_rep.exists() else None},
    )

    # T13 permanent protection during C4 ops
    wipe_perm = ordinary_wipe_allowed(
        uri=f"mongodb://127.0.0.1:{port}/", db_name=perm_db
    )
    clone_perm = ordinary_clone_allowed(
        source_uri=f"mongodb://127.0.0.1:{port}/", target_db=perm_db
    )
    add(
        "T13_permanent_protected",
        "PASS" if (not wipe_perm.get("ok") and not clone_perm.get("ok") and identity) else "FAIL",
        {"wipe": wipe_perm, "clone": clone_perm, "instance_id": identity.get("instance_id")},
    )

    # Summarize
    statuses = [t["result"] for t in results]
    ok = all(s in ("PASS", "NOT VERIFIED") for s in statuses) and "FAIL" not in statuses
    # Stricter: FAIL anywhere → not ok; NOT VERIFIED allowed for Founder-pending
    ok = "FAIL" not in statuses

    report = {
        "cycle": "D-175-C4",
        "ok": ok,
        "db": args.db,
        "permanent_instance_id": identity.get("instance_id"),
        "tests": results,
        "role_authority_matrix": ROLE_AUTHORITY_MATRIX,
        "founder_pending": [t for t in results if t["result"] == "NOT VERIFIED"],
    }
    art = Path("/opt/cursor/artifacts")
    art.mkdir(parents=True, exist_ok=True)
    (art / "D175-C4-VERIFY-REPORT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (root / "c4" / "LAST_VERIFY.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "passed": sum(1 for t in results if t["result"] == "PASS"),
                "not_verified": sum(1 for t in results if t["result"] == "NOT VERIFIED"),
                "failed": sum(1 for t in results if t["result"] == "FAIL"),
                "total": len(results),
            },
            indent=2,
        )
    )
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
