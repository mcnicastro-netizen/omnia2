#!/usr/bin/env python3
"""D-175 C4 — Create CLEAN / CONTINUITY work copy from permanent (read-only source).

Never writes to the permanent base. Target must be omnia_df_clean_* or omnia_df_cont_*.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from shared.dogfood.ordinary_ops import ordinary_clone_allowed  # noqa: E402
from shared.dogfood.permanent import (  # noqa: E402
    configured_permanent_db_name,
    dogfood_root,
    load_identity,
    require_identity_or_raise,
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["clean", "continuity"], required=True)
    ap.add_argument("--target", help="Target DB name (default omnia_df_clean_c4 / omnia_df_cont_c4)")
    ap.add_argument("--drop-target", action="store_true", help="Drop target DB before restore")
    args = ap.parse_args()

    root = dogfood_root()
    port = int(os.environ.get("OMNIA_DF_MONGO_PORT") or 27018)
    identity = require_identity_or_raise()
    perm_db = configured_permanent_db_name() or identity["db_name"]
    target = args.target or (
        "omnia_df_clean_c4" if args.kind == "clean" else "omnia_df_cont_c4"
    )

    gate = ordinary_clone_allowed(
        source_uri=f"mongodb://127.0.0.1:{port}/", target_db=target
    )
    if not gate.get("ok"):
        raise RuntimeError(gate.get("error") or "clone_denied")

    creds = json.loads((root / "secrets" / "mongo-df-credentials.json").read_text())
    # Read permanent with backup (or admin); write work-copy with admin only.
    # omnia_df_backup is read-only and cannot mongorestore into clean/cont targets.
    dump_user, dump_pwd = "omnia_df_backup", creds.get("backup")
    if not dump_pwd:
        dump_user, dump_pwd = "omnia_df_admin", creds["admin"]
    restore_user, restore_pwd = "omnia_df_admin", creds["admin"]

    dump_root = root / "c4" / "workcopy_dump" / args.kind
    if dump_root.exists():
        import shutil

        shutil.rmtree(dump_root)
    dump_root.mkdir(parents=True)

    dump_uri = f"mongodb://{dump_user}:{dump_pwd}@127.0.0.1:{port}/?authSource=admin"
    restore_uri = (
        f"mongodb://{restore_user}:{restore_pwd}@127.0.0.1:{port}/?authSource=admin"
    )
    dump = subprocess.run(
        ["mongodump", f"--uri={dump_uri}", f"--db={perm_db}", f"--out={dump_root}"],
        capture_output=True,
        text=True,
    )
    if dump.returncode != 0:
        raise RuntimeError(f"mongodump_failed:{(dump.stderr or '')[-400:]}")

    dump_db_dir = dump_root / perm_db
    if args.drop_target:
        # Full DB drop — mongorestore --drop only drops collections present in the dump
        # (permanent skeleton), which would leave stale C4 commercial collections behind.
        drop = subprocess.run(
            [
                "mongosh",
                "--quiet",
                restore_uri,
                "--eval",
                f"db.getSiblingDB('{target}').dropDatabase()",
            ],
            capture_output=True,
            text=True,
        )
        if drop.returncode != 0:
            raise RuntimeError(f"drop_target_failed:{(drop.stderr or drop.stdout)[-400:]}")
    restore_cmd = [
        "mongorestore",
        f"--uri={restore_uri}",
        f"--db={target}",
        str(dump_db_dir),
    ]
    restore = subprocess.run(restore_cmd, capture_output=True, text=True)
    if restore.returncode != 0:
        raise RuntimeError(f"mongorestore_failed:{(restore.stderr or '')[-400:]}")

    report = {
        "cycle": "D-175-C4",
        "ok": True,
        "kind": args.kind,
        "source_permanent_db": perm_db,
        "target_db": target,
        "identity_instance_id": identity.get("instance_id"),
        "note": "Permanent was read-only source; structure seed via apply_manifest on target",
    }
    out = root / "c4" / f"LAST_WORKCOPY_{args.kind.upper()}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    Path("/opt/cursor/artifacts").mkdir(parents=True, exist_ok=True)
    Path(f"/opt/cursor/artifacts/D175-C4-WORKCOPY-{args.kind.upper()}.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"FAIL {e}", file=sys.stderr)
        raise SystemExit(2)
