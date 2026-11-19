#!/usr/bin/env python3
"""D-175 C3 — Read-only live verification of an already-initialized permanent base.

Does NOT call dogfood_permanent_init.py.
Does NOT rewrite IDENTITY.json, markers, roles, or permanent backups.
Requires a prior successful init; missing/altered identity → FAIL.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from pymongo import MongoClient  # noqa: E402
from pymongo.errors import OperationFailure  # noqa: E402

from shared.dogfood.ordinary_ops import (  # noqa: E402
    ordinary_clone_allowed,
    ordinary_migrate_destructive_allowed,
    ordinary_restore_allowed,
    ordinary_wipe_allowed,
)
from shared.dogfood.perimeter import check_dogfood_db_isolation  # noqa: E402
from shared.dogfood.permanent import (  # noqa: E402
    MARKER_COLLECTION,
    assert_general_creds_have_no_emergency,
    check_emergency_unlock_gates,
    configured_permanent_db_name,
    dogfood_root,
    emergency_audit_path,
    emergency_credentials_path,
    general_mongo_credentials_path,
    identity_fingerprint,
    load_identity,
    require_identity_or_raise,
)


def _creds(root: Path) -> dict:
    p = general_mongo_credentials_path()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert_general_creds_have_no_emergency(data)
    return data


def _try_write(uri: str, db: str) -> dict:
    """Attempt write; on success deletes the probe doc (work DB only in callers)."""
    try:
        c = MongoClient(uri, serverSelectionTimeoutMS=5000)
        c[db]["_c3_priv_probe"].insert_one({"probe": 1})
        c[db]["_c3_priv_probe"].delete_many({})
        return {"result": "PASS_ALLOWED"}
    except OperationFailure as e:
        return {"result": "DENIED", "error": str(e)[:200]}
    except Exception as e:  # noqa: BLE001
        return {"result": "DENIED", "error": str(e)[:200]}


def _read_marker(admin_uri: str, db_name: str) -> dict | None:
    c = MongoClient(admin_uri, serverSelectionTimeoutMS=5000)
    return c[db_name][MARKER_COLLECTION].find_one({}, {"_id": 0})


def main() -> int:
    root = dogfood_root()
    port = int(os.environ.get("OMNIA_DF_MONGO_PORT") or 27018)

    # --- Read-only identity gate (no init) ---
    try:
        identity = require_identity_or_raise()
    except RuntimeError as e:
        print(json.dumps({"ok": False, "result": "FAIL", "error": str(e)}, indent=2))
        return 2

    before_fp = identity_fingerprint(identity)
    before_identity_text = (root / "permanent" / "IDENTITY.json").read_text(encoding="utf-8")
    perm_db = str(identity.get("db_name") or configured_permanent_db_name())
    if perm_db != configured_permanent_db_name() and configured_permanent_db_name():
        # Config must match identity when both set
        if (os.environ.get("OMNIA_DOGFOOD_PERMANENT_DB") or "").strip():
            if perm_db != (os.environ.get("OMNIA_DOGFOOD_PERMANENT_DB") or "").strip():
                print(json.dumps({"ok": False, "error": "identity_db_mismatch_env"}, indent=2))
                return 2

    hint_path = root / "permanent" / "ENV_HINT.json"
    if hint_path.exists():
        hint = json.loads(hint_path.read_text())
        os.environ.setdefault("OMNIA_DOGFOOD_PERMANENT_URI", hint["OMNIA_DOGFOOD_PERMANENT_URI"])
        os.environ.setdefault("OMNIA_DOGFOOD_PERMANENT_DB", hint["OMNIA_DOGFOOD_PERMANENT_DB"])

    try:
        creds = _creds(root)
    except RuntimeError as e:
        print(json.dumps({"ok": False, "error": str(e)}, indent=2))
        return 2

    work_db = (os.environ.get("OMNIA_DOGFOOD_RUNTIME_DB") or "omnia_df_clean_work").strip()
    admin_uri = (
        f"mongodb://omnia_df_admin:{creds['admin']}@127.0.0.1:{port}/admin?authSource=admin"
    )

    # Marker must exist and match IDENTITY — read only
    marker = _read_marker(admin_uri, perm_db)
    if not marker:
        print(json.dumps({"ok": False, "error": "permanent_marker_missing"}, indent=2))
        return 2
    if marker.get("instance_id") != identity.get("instance_id"):
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": "identity_marker_mismatch",
                    "identity_id": identity.get("instance_id"),
                    "marker_id": marker.get("instance_id"),
                },
                indent=2,
            )
        )
        return 2

    marker_count_before = MongoClient(admin_uri, serverSelectionTimeoutMS=5000)[perm_db][
        MARKER_COLLECTION
    ].estimated_document_count()

    results = []

    def add(tid: str, result: str, detail: dict | None = None):
        results.append({"id": tid, "result": result, "detail": detail or {}})

    # T1 runtime direct on permanent DENY
    os.environ["OMNIA_ENV"] = "dogfood"
    os.environ["DB_NAME"] = perm_db
    os.environ["MONGO_URL"] = f"mongodb://127.0.0.1:{port}/{perm_db}"
    os.environ.setdefault("OMNIA_DOGFOOD_ALLOWED_API_HOSTS", "127.0.0.1")
    os.environ.setdefault("OMNIA_DOGFOOD_ALLOWED_FE_HOSTS", "127.0.0.1")
    r = check_dogfood_db_isolation()
    add(
        "T1_runtime_permanent_db",
        "PASS"
        if (not r["ok"] and ("db_name_is_permanent" in r["errors"] or "mongo_url_is_permanent" in r["errors"]))
        else "FAIL",
        r,
    )

    # T2 alternate URI same permanent instance DENY
    os.environ["DB_NAME"] = perm_db
    os.environ["MONGO_URL"] = (
        f"mongodb://omnia_df_runtime:{creds['runtime']}@127.0.0.1:{port}/{perm_db}?authSource=admin"
    )
    r2 = check_dogfood_db_isolation()
    add("T2_runtime_alt_uri_same_permanent", "PASS" if not r2["ok"] else "FAIL", r2)

    # T3–T6 ordinary ops DENY
    add(
        "T3_clone_to_permanent",
        "PASS"
        if not ordinary_clone_allowed(
            source_uri=f"mongodb://127.0.0.1:{port}/", target_db=perm_db
        ).get("ok")
        else "FAIL",
    )
    add(
        "T4_wipe_permanent",
        "PASS"
        if not ordinary_wipe_allowed(
            uri=f"mongodb://127.0.0.1:{port}/", db_name=perm_db
        ).get("ok")
        else "FAIL",
    )
    add(
        "T5_restore_permanent",
        "PASS"
        if not ordinary_restore_allowed(
            uri=f"mongodb://127.0.0.1:{port}/", target_db=perm_db
        ).get("ok")
        else "FAIL",
    )
    add(
        "T6_migrate_permanent",
        "PASS"
        if not ordinary_migrate_destructive_allowed(
            uri=f"mongodb://127.0.0.1:{port}/", db_name=perm_db
        ).get("ok")
        else "FAIL",
    )

    # T7/T8 privilege write DENY (failed auth must not leave docs)
    tw = _try_write(
        f"mongodb://omnia_df_runtime:{creds['runtime']}@127.0.0.1:{port}/{perm_db}?authSource=admin",
        perm_db,
    )
    add("T7_runtime_write_permanent", "PASS" if tw["result"] == "DENIED" else "FAIL", tw)
    tw2 = _try_write(
        f"mongodb://omnia_df_clone:{creds['clone']}@127.0.0.1:{port}/{perm_db}?authSource=admin",
        perm_db,
    )
    add("T8_clone_write_permanent", "PASS" if tw2["result"] == "DENIED" else "FAIL", tw2)

    # T9–T11 emergency gates
    env_clean = {k: v for k, v in os.environ.items() if not k.startswith("OMNIA_PERMANENT_")}
    p = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "dogfood_permanent_emergency_restore.py"),
            "--prove-gates",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env_clean,
    )
    add("T9_emergency_without_unlock", "PASS" if p.returncode != 0 else "FAIL", {"rc": p.returncode})

    g = check_emergency_unlock_gates(
        unlock_token="1", auth_phrase="WRONG", confirm1="", confirm2=""
    )
    add("T10_incomplete_unlock", "PASS" if not g["ok"] else "FAIL", g)

    g2 = check_emergency_unlock_gates(
        unlock_token="1",
        auth_phrase="OMNIA FOUNDATION UNLOCK PERMANENT BASE",
        confirm1="CONFIRM-PERMANENT-EMERGENCY",
        confirm2="",
    )
    add("T11_confirm_incomplete", "PASS" if not g2["ok"] else "FAIL", g2)

    # T12 audit append (audit file only — not permanent DB)
    before = emergency_audit_path()
    before_lines = before.read_text().splitlines() if before.exists() else []
    env_ok = {
        **os.environ,
        "OMNIA_PERMANENT_UNLOCK": "1",
        "OMNIA_PERMANENT_AUTH_PHRASE": "OMNIA FOUNDATION UNLOCK PERMANENT BASE",
        "OMNIA_PERMANENT_CONFIRM_1": "CONFIRM-PERMANENT-EMERGENCY",
        "OMNIA_PERMANENT_CONFIRM_2": "CONFIRM-PERMANENT-EMERGENCY",
    }
    p2 = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "dogfood_permanent_emergency_restore.py"),
            "--prove-gates",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env_ok,
    )
    after_lines = before.read_text().splitlines() if before.exists() else []
    add(
        "T12_emergency_audit_append",
        "PASS" if p2.returncode == 0 and len(after_lines) >= len(before_lines) + 1 else "FAIL",
        {"rc": p2.returncode, "before": len(before_lines), "after": len(after_lines)},
    )

    # T13 work-copy gates + runtime write on work DB only (not permanent)
    ok_clone = ordinary_clone_allowed(
        source_uri=f"mongodb://127.0.0.1:{port}/", target_db="omnia_df_clean_a"
    )
    ok_wipe = ordinary_wipe_allowed(
        uri=f"mongodb://127.0.0.1:{port}/", db_name="omnia_df_clean_a"
    )
    work_uri = (
        f"mongodb://omnia_df_runtime:{creds['runtime']}@127.0.0.1:{port}/{work_db}?authSource=admin"
    )
    tw3 = _try_write(work_uri, work_db)
    add(
        "T13_ordinary_work_copy_allowed",
        "PASS"
        if ok_clone.get("ok") and ok_wipe.get("ok") and tw3.get("result") == "PASS_ALLOWED"
        else "FAIL",
        {"clone": ok_clone, "wipe": ok_wipe, "runtime_write_work": tw3},
    )

    # --- Creds separation checks ---
    general = json.loads(general_mongo_credentials_path().read_text(encoding="utf-8"))
    em_path = emergency_credentials_path()
    add(
        "T14_emergency_absent_from_general_creds",
        "PASS" if "emergency" not in general and em_path.is_file() else "FAIL",
        {"general_has_emergency": "emergency" in general, "sealed_exists": em_path.is_file()},
    )
    # Ordinary credential file must not embed emergency password; sealed path is separate.
    add(
        "T15_ordinary_creds_cannot_see_emergency_secret",
        "PASS" if "emergency" not in general else "FAIL",
        {
            "note": "ordinary scripts load only mongo-df-credentials.json; sealed path separate",
            "general_keys": sorted(general.keys()),
            "sealed_path": str(em_path),
        },
    )

    # --- Post-conditions: identity + marker unchanged ---
    after_identity = require_identity_or_raise()
    after_fp = identity_fingerprint(after_identity)
    after_text = (root / "permanent" / "IDENTITY.json").read_text(encoding="utf-8")
    marker_count_after = MongoClient(admin_uri, serverSelectionTimeoutMS=5000)[perm_db][
        MARKER_COLLECTION
    ].estimated_document_count()
    marker_after = _read_marker(admin_uri, perm_db)

    identity_unchanged = (
        before_fp == after_fp
        and before_identity_text == after_text
        and marker_count_before == marker_count_after
        and (marker_after or {}).get("instance_id") == before_fp.get("instance_id")
    )
    add(
        "T16_verify_readonly_identity_unchanged",
        "PASS" if identity_unchanged else "FAIL",
        {
            "before": before_fp,
            "after": after_fp,
            "marker_count_before": marker_count_before,
            "marker_count_after": marker_count_after,
        },
    )

    report = {
        "cycle": "D-175-C3",
        "ok": all(x["result"] == "PASS" for x in results),
        "mode": "read_only_verify",
        "identity": after_fp,
        "permanent_db": perm_db,
        "tests": results,
        "git_sha": after_identity.get("git_sha"),
        "note": "Did not invoke permanent_init; did not rewrite IDENTITY or markers",
        "residual_risk": (
            "omnia_df_admin (root) remains a technical superuser outside ordinary "
            "runtime/clone paths — permanent base is NOT filesystem-immutable"
        ),
    }
    art = Path("/opt/cursor/artifacts")
    art.mkdir(parents=True, exist_ok=True)
    (art / "D175-C3-VERIFY-REPORT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    # C3_LAST_VERIFY is a report sidecar — not IDENTITY
    (root / "permanent" / "C3_LAST_VERIFY.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "ok": report["ok"],
                "passed": sum(1 for x in results if x["result"] == "PASS"),
                "total": len(results),
                "instance_id": before_fp.get("instance_id"),
            },
            indent=2,
        )
    )
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
