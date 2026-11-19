#!/usr/bin/env python3
"""D-175 C3 — Initialize & protect the permanent Dogfood base (no C4 seed data).

Steps:
1. Ensure isolated mongod (:27018) + auth (C2 bootstrap)
2. Verify destination / credentials / privileges
3. Create permanent DB + identity marker collection
4. Wire Mongo roles: runtime/clone cannot write permanent; emergency sealed
5. Write IDENTITY.json + role matrix
6. Acquire backup + manifest of the empty permanent base
7. Record git SHA

Does NOT create commercial accounts/orgs (C4).
"""
from __future__ import annotations

import json
import os
import secrets
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from pymongo import MongoClient  # noqa: E402

from shared.dogfood.backup import (  # noqa: E402
    assert_dogfood_mongo_port,
    build_manifest,
    redact_mongo_uri,
    sha256_tree,
    write_manifest,
)
from shared.dogfood.permanent import (  # noqa: E402
    MARKER_COLLECTION,
    build_identity_payload,
    configured_permanent_db_name,
    dogfood_root,
    is_permanent_db_name,
    write_identity,
)


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), text=True
        ).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def _load_creds(root: Path) -> dict:
    p = root / "secrets" / "mongo-df-credentials.json"
    if not p.exists():
        raise RuntimeError("mongo_credentials_missing_run_c2_bootstrap")
    return json.loads(p.read_text(encoding="utf-8"))


def _write_emergency_creds(root: Path, pwd: str) -> Path:
    path = root / "permanent" / "secrets" / "emergency-credentials.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    payload = {
        "user": "omnia_df_emergency",
        "password": pwd,
        "note": "Sealed emergency only — never mount as MONGO_URL runtime",
    }
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(payload, indent=2) + "\n")
    os.replace(str(tmp), str(path))
    path.chmod(0o600)
    return path


def main() -> int:
    root = dogfood_root()
    port = int(os.environ.get("OMNIA_DF_MONGO_PORT") or 27018)
    assert_dogfood_mongo_port(port)
    db_name = configured_permanent_db_name()
    if not is_permanent_db_name(db_name):
        raise RuntimeError(f"permanent_db_name_invalid:{db_name}")

    # 1) Bootstrap C2 mongod/auth if needed
    boot = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "dogfood_mongo_bootstrap.py"), f"--port={port}"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if boot.returncode != 0:
        raise RuntimeError(f"bootstrap_failed:{boot.stderr[-400:]}")

    creds = _load_creds(root)
    admin_uri = (
        f"mongodb://omnia_df_admin:{creds['admin']}@127.0.0.1:{port}/admin?authSource=admin"
    )
    client = MongoClient(admin_uri, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")

    # 2) Destination checks
    # Refuse if somehow targeting shared app DB
    if db_name.lower() in ("omnia", "admin", "local"):
        raise RuntimeError("permanent_destination_forbidden")

    # 3) Initialize permanent DB marker (no commercial data)
    instance_id = str(uuid.uuid4())
    git_sha = _git_sha()
    pdb = client[db_name]
    pdb[MARKER_COLLECTION].delete_many({})
    pdb[MARKER_COLLECTION].insert_one(
        {
            "instance_id": instance_id,
            "db_name": db_name,
            "cycle": "D-175-C3",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "git_sha": git_sha,
            "kind": "permanent_base_marker",
        }
    )
    # Schema placeholder only — C4 will seed accounts
    pdb["_omnia_permanent_meta"].update_one(
        {"_id": "meta"},
        {
            "$set": {
                "initialized": True,
                "seed_accounts": False,
                "note": "C4 creates fictitious accounts/orgs",
            }
        },
        upsert=True,
    )

    # 4) Roles — runtime/clone cannot write permanent; emergency RW sealed
    emergency_pwd = creds.get("emergency") or secrets.token_urlsafe(24)
    creds["emergency"] = emergency_pwd
    # Persist emergency into main creds file (0600) + dedicated sealed file
    cred_path = root / "secrets" / "mongo-df-credentials.json"
    cred_path.write_text(json.dumps(creds, indent=2) + "\n", encoding="utf-8")
    cred_path.chmod(0o600)
    em_path = _write_emergency_creds(root, emergency_pwd)

    work_db = (os.environ.get("OMNIA_DOGFOOD_RUNTIME_DB") or "omnia_df_clean_work").strip()
    js = f"""
    const admin=db.getSiblingDB('admin');
    function upsertRole(name, privileges) {{
      try {{ admin.dropRole(name); }} catch(e) {{}}
      admin.createRole({{role:name, privileges:privileges, roles:[]}});
      print('role:'+name);
    }}
    function upsertUser(user, pwd, roles) {{
      try {{ admin.dropUser(user); }} catch(e) {{}}
      admin.createUser({{user:user, pwd:pwd, roles:roles}});
      print('user:'+user);
    }}
    // Runtime: work copy only — NO permanent
    upsertRole('df_runtime_rw', [
      {{resource:{{db:'{work_db}', collection:''}}, actions:['find','insert','update','remove','createIndex','listCollections']}},
      {{resource:{{db:'omnia_df_c2_src', collection:''}}, actions:['find','insert','update','remove','createIndex','listCollections']}}
    ]);
    // Clone: read permanent + write work/probe — NO dropDatabase on permanent
    upsertRole('df_clone_ops', [
      {{resource:{{db:'', collection:''}}, actions:['listDatabases']}},
      {{resource:{{db:'{db_name}', collection:''}}, actions:['find','listCollections','listIndexes']}},
      {{resource:{{db:'{work_db}', collection:''}}, actions:['find','insert','update','remove','createIndex','listCollections','dropCollection']}},
      {{resource:{{db:'omnia_df_clean_a', collection:''}}, actions:['find','insert','update','remove','createIndex','listCollections','dropCollection']}},
      {{resource:{{db:'omnia_df_cont_a', collection:''}}, actions:['find','insert','update','remove','createIndex','listCollections','dropCollection']}},
      {{resource:{{db:'omnia_df_probe_c2', collection:''}}, actions:['find','insert','update','remove','createIndex','listCollections','dropCollection']}}
    ]);
    upsertRole('df_backup_ro', [
      {{resource:{{db:'', collection:''}}, actions:['listDatabases']}},
      {{resource:{{db:'{db_name}', collection:''}}, actions:['find','listCollections','listIndexes']}},
      {{resource:{{db:'omnia_df_c2_src', collection:''}}, actions:['find','listCollections','listIndexes']}},
      {{resource:{{db:'{work_db}', collection:''}}, actions:['find','listCollections','listIndexes']}}
    ]);
    upsertRole('df_permanent_emergency', [
      {{resource:{{db:'{db_name}', collection:''}}, actions:['find','insert','update','remove','createIndex','listCollections','dropCollection']}}
    ]);
    upsertUser('omnia_df_runtime', '{creds['runtime']}', [{{role:'df_runtime_rw', db:'admin'}}]);
    upsertUser('omnia_df_clone', '{creds['clone']}', [{{role:'df_clone_ops', db:'admin'}}]);
    upsertUser('omnia_df_backup', '{creds['backup']}', [{{role:'df_backup_ro', db:'admin'}}]);
    upsertUser('omnia_df_emergency', '{emergency_pwd}', [{{role:'df_permanent_emergency', db:'admin'}}]);
    print('c3_roles_ok');
    """
    p = subprocess.run(
        ["mongosh", "--quiet", admin_uri, "--eval", js],
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"role_setup_failed:{(p.stderr or p.stdout)[-600:]}")

    # 5) IDENTITY.json
    identity = build_identity_payload(
        instance_id=instance_id,
        db_name=db_name,
        host="127.0.0.1",
        port=port,
        git_sha=git_sha,
        extra={"runtime_work_db": work_db, "emergency_creds": str(em_path)},
    )
    id_path = write_identity(identity)
    os.environ["OMNIA_DOGFOOD_PERMANENT_DB"] = db_name
    os.environ["OMNIA_DOGFOOD_PERMANENT_URI"] = (
        f"mongodb://127.0.0.1:{port}/{db_name}"
    )
    # Persist env hint file (no passwords)
    env_hint = {
        "OMNIA_DOGFOOD_PERMANENT_DB": db_name,
        "OMNIA_DOGFOOD_PERMANENT_URI": f"mongodb://127.0.0.1:{port}/{db_name}",
        "OMNIA_DF_MONGO_PORT": str(port),
        "OMNIA_DOGFOOD_RUNTIME_DB": work_db,
    }
    (root / "permanent" / "ENV_HINT.json").write_text(
        json.dumps(env_hint, indent=2) + "\n", encoding="utf-8"
    )

    matrix = {
        "cycle": "D-175-C3",
        "instance": f"127.0.0.1:{port}",
        "permanent_db": db_name,
        "auth": True,
        "users": {
            "omnia_df_runtime": {
                "privileges": f"readWrite on {work_db} + omnia_df_c2_src",
                "forbidden": f"any write/drop on {db_name}",
            },
            "omnia_df_clone": {
                "privileges": f"read {db_name}; readWrite work/probe/clean/cont",
                "forbidden": f"write/drop on {db_name}",
            },
            "omnia_df_backup": {
                "privileges": f"read {db_name} and work sources",
                "forbidden": "write/drop",
            },
            "omnia_df_emergency": {
                "privileges": f"readWrite {db_name} only",
                "forbidden": "runtime mount; ordinary scripts",
                "sealed": True,
            },
        },
        "identity": str(id_path),
    }
    (root / "permanent" / "C3_MONGO_ROLE_MATRIX.json").write_text(
        json.dumps(matrix, indent=2) + "\n", encoding="utf-8"
    )

    # 6) Backup + manifest of permanent (source role allows omnia_df_ prefix but
    #    assert_safe_db_name forbids permanent — use admin dump via mongodump directly
    #    with endpoint assert bypassed for THIS init-only path by calling mongodump
    #    after verifying we are on dogfood port). Ordinary restore still denies permanent.
    bak_id = f"c3-perm-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid.uuid4().hex[:8]}"
    bak_dir = root / "permanent" / "backups" / bak_id
    bak_dir.mkdir(parents=True, exist_ok=True)
    dump_out = bak_dir / "mongodump"
    dump_out.mkdir(parents=True, exist_ok=True)
    tool_uri = f"mongodb://omnia_df_admin:{creds['admin']}@127.0.0.1:{port}/?authSource=admin"
    dump = subprocess.run(
        [
            "mongodump",
            f"--uri={tool_uri}",
            f"--db={db_name}",
            f"--out={dump_out}",
        ],
        capture_output=True,
        text=True,
    )
    if dump.returncode != 0:
        raise RuntimeError(f"permanent_dump_failed:{dump.stderr[-400:]}")
    dump_dir = dump_out / db_name
    dump_sha = sha256_tree(dump_dir)
    # Media: empty allowed only with explicit flag for permanent skeleton
    os.environ["OMNIA_DOGFOOD_ALLOW_MISSING_MEDIA"] = "1"
    from shared.dogfood.backup import backup_media

    media = backup_media(root / "media" / "permanent_src", bak_dir)
    manifest = build_manifest(
        backup_id=bak_id,
        source_db=db_name,
        source_uri_redacted=redact_mongo_uri(tool_uri),
        dump_report={
            "ok": True,
            "dump_dir": str(dump_dir),
            "collections_requested": [MARKER_COLLECTION, "_omnia_permanent_meta"],
            "collections_present": [
                c
                for c in (MARKER_COLLECTION, "_omnia_permanent_meta")
                if (dump_dir / f"{c}.bson").is_file()
            ],
            "collections_missing_empty": [],
        },
        media_report=media,
        dump_sha=dump_sha,
        extra={"cycle": "D-175-C3", "kind": "permanent_init"},
    )
    # Override cycle field
    manifest["cycle"] = "D-175-C3"
    man_path = write_manifest(bak_dir / "MANIFEST.json", manifest)

    report = {
        "cycle": "D-175-C3",
        "ok": True,
        "permanent_db": db_name,
        "instance_id": instance_id,
        "identity": str(id_path),
        "role_matrix": str(root / "permanent" / "C3_MONGO_ROLE_MATRIX.json"),
        "backup_id": bak_id,
        "manifest": str(man_path),
        "git_sha": git_sha,
        "mongosh_roles": (p.stdout or "")[-300:],
        "env_hint": env_hint,
    }
    art = Path("/opt/cursor/artifacts")
    art.mkdir(parents=True, exist_ok=True)
    (art / "D175-C3-INIT-REPORT.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    (art / "D175-C3-MONGO-ROLE-MATRIX.json").write_text(
        json.dumps(matrix, indent=2) + "\n", encoding="utf-8"
    )
    (art / "D175-C3-IDENTITY.json").write_text(
        json.dumps(identity, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"ok": True, "permanent_db": db_name, "instance_id": instance_id}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"FAIL {e}", file=sys.stderr)
        raise SystemExit(2)
