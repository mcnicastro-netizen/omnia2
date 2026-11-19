#!/usr/bin/env python3
"""D-175 C3 — Live verification of permanent base protections (no destructive restore)."""
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
    check_emergency_unlock_gates,
    configured_permanent_db_name,
    dogfood_root,
    emergency_audit_path,
    load_identity,
    require_identity_or_raise,
)


def _creds(root: Path) -> dict:
    return json.loads((root / "secrets" / "mongo-df-credentials.json").read_text())


def _try_write(uri: str, db: str) -> dict:
    try:
        c = MongoClient(uri, serverSelectionTimeoutMS=5000)
        c[db]["_c3_priv_probe"].insert_one({"probe": 1})
        c[db]["_c3_priv_probe"].delete_many({})
        return {"result": "PASS_ALLOWED"}
    except OperationFailure as e:
        return {"result": "DENIED", "error": str(e)[:200]}
    except Exception as e:  # noqa: BLE001
        return {"result": "DENIED", "error": str(e)[:200]}


def main() -> int:
    root = dogfood_root()
    port = int(os.environ.get("OMNIA_DF_MONGO_PORT") or 27018)
    # Ensure init ran
    init = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "dogfood_permanent_init.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**os.environ, "OMNIA_DF_MONGO_PORT": str(port)},
    )
    if init.returncode != 0:
        print(init.stderr, file=sys.stderr)
        raise SystemExit(2)

    identity = require_identity_or_raise()
    perm_db = configured_permanent_db_name()
    creds = _creds(root)
    work_db = (os.environ.get("OMNIA_DOGFOOD_RUNTIME_DB") or "omnia_df_clean_work").strip()

    # Load env hint into process for perimeter checks
    hint_path = root / "permanent" / "ENV_HINT.json"
    if hint_path.exists():
        hint = json.loads(hint_path.read_text())
        os.environ.setdefault("OMNIA_DOGFOOD_PERMANENT_URI", hint["OMNIA_DOGFOOD_PERMANENT_URI"])
        os.environ.setdefault("OMNIA_DOGFOOD_PERMANENT_DB", hint["OMNIA_DOGFOOD_PERMANENT_DB"])

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
    add("T1_runtime_permanent_db", "PASS" if (not r["ok"] and "db_name_is_permanent" in r["errors"]) or (not r["ok"] and "mongo_url_is_permanent" in r["errors"]) else "FAIL", r)

    # T2 alternate URI same permanent instance DENY
    os.environ["DB_NAME"] = perm_db
    os.environ["MONGO_URL"] = (
        f"mongodb://omnia_df_runtime:{creds['runtime']}@127.0.0.1:{port}/{perm_db}?authSource=admin"
    )
    r2 = check_dogfood_db_isolation()
    add(
        "T2_runtime_alt_uri_same_permanent",
        "PASS" if not r2["ok"] else "FAIL",
        r2,
    )

    # T3 clone destination permanent DENY
    c = ordinary_clone_allowed(source_uri=f"mongodb://127.0.0.1:{port}/", target_db=perm_db)
    add("T3_clone_to_permanent", "PASS" if not c.get("ok") else "FAIL", c)

    # T4 wipe permanent DENY
    w = ordinary_wipe_allowed(uri=f"mongodb://127.0.0.1:{port}/", db_name=perm_db)
    add("T4_wipe_permanent", "PASS" if not w.get("ok") else "FAIL", w)

    # T5 restore ordinary permanent DENY
    rst = ordinary_restore_allowed(uri=f"mongodb://127.0.0.1:{port}/", target_db=perm_db)
    add("T5_restore_permanent", "PASS" if not rst.get("ok") else "FAIL", rst)

    # T6 migrate destructive DENY
    mig = ordinary_migrate_destructive_allowed(
        uri=f"mongodb://127.0.0.1:{port}/", db_name=perm_db
    )
    add("T6_migrate_permanent", "PASS" if not mig.get("ok") else "FAIL", mig)

    # T7 runtime no write on permanent
    rt_uri = f"mongodb://omnia_df_runtime:{creds['runtime']}@127.0.0.1:{port}/{perm_db}?authSource=admin"
    tw = _try_write(rt_uri, perm_db)
    add("T7_runtime_write_permanent", "PASS" if tw["result"] == "DENIED" else "FAIL", tw)

    # T8 clone no write on permanent
    cl_uri = f"mongodb://omnia_df_clone:{creds['clone']}@127.0.0.1:{port}/{perm_db}?authSource=admin"
    tw2 = _try_write(cl_uri, perm_db)
    add("T8_clone_write_permanent", "PASS" if tw2["result"] == "DENIED" else "FAIL", tw2)

    # T9 emergency not invocable without unlock
    # clear unlock env
    env_clean = {k: v for k, v in os.environ.items() if not k.startswith("OMNIA_PERMANENT_")}
    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "dogfood_permanent_emergency_restore.py"), "--prove-gates"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env_clean,
    )
    add(
        "T9_emergency_without_unlock",
        "PASS" if p.returncode != 0 else "FAIL",
        {"rc": p.returncode, "out": (p.stdout or "")[-200:]},
    )

    # T10 incomplete unlock DENY
    g = check_emergency_unlock_gates(unlock_token="1", auth_phrase="WRONG", confirm1="", confirm2="")
    add("T10_incomplete_unlock", "PASS" if not g["ok"] else "FAIL", g)

    # T11 double confirm incomplete DENY
    g2 = check_emergency_unlock_gates(
        unlock_token="1",
        auth_phrase="OMNIA FOUNDATION UNLOCK PERMANENT BASE",
        confirm1="CONFIRM-PERMANENT-EMERGENCY",
        confirm2="",
    )
    add("T11_confirm_incomplete", "PASS" if not g2["ok"] else "FAIL", g2)

    # T12 audit append-only verifiable + prove gates PASS
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
        [sys.executable, str(ROOT / "scripts" / "dogfood_permanent_emergency_restore.py"), "--prove-gates"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env_ok,
    )
    after_lines = before.read_text().splitlines() if before.exists() else []
    audit_ok = p2.returncode == 0 and len(after_lines) >= len(before_lines) + 1
    add(
        "T12_emergency_audit_append",
        "PASS" if audit_ok else "FAIL",
        {
            "rc": p2.returncode,
            "before": len(before_lines),
            "after": len(after_lines),
            "stdout": (p2.stdout or "")[-300:],
        },
    )

    # T13 ordinary ops on work copy allowed (gate level)
    ok_clone = ordinary_clone_allowed(
        source_uri=f"mongodb://127.0.0.1:{port}/", target_db="omnia_df_clean_a"
    )
    ok_wipe = ordinary_wipe_allowed(
        uri=f"mongodb://127.0.0.1:{port}/", db_name="omnia_df_clean_a"
    )
    # runtime write on work db
    work_uri = f"mongodb://omnia_df_runtime:{creds['runtime']}@127.0.0.1:{port}/{work_db}?authSource=admin"
    # ensure work db exists via admin
    admin = MongoClient(
        f"mongodb://omnia_df_admin:{creds['admin']}@127.0.0.1:{port}/admin?authSource=admin",
        serverSelectionTimeoutMS=5000,
    )
    admin[work_db]["_c3_init"].insert_one({"ok": 1})
    tw3 = _try_write(work_uri, work_db)
    add(
        "T13_ordinary_work_copy_allowed",
        "PASS"
        if ok_clone.get("ok") and ok_wipe.get("ok") and tw3.get("result") == "PASS_ALLOWED"
        else "FAIL",
        {"clone": ok_clone, "wipe": ok_wipe, "runtime_write_work": tw3},
    )

    # Identity summary
    report = {
        "cycle": "D-175-C3",
        "ok": all(x["result"] == "PASS" for x in results),
        "identity": identity,
        "permanent_db": perm_db,
        "tests": results,
        "git_sha": identity.get("git_sha"),
    }
    art = Path("/opt/cursor/artifacts")
    art.mkdir(parents=True, exist_ok=True)
    (art / "D175-C3-VERIFY-REPORT.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (root / "permanent" / "C3_LAST_VERIFY.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ok": report["ok"], "passed": sum(1 for x in results if x["result"]=="PASS"), "total": len(results)}, indent=2))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
