#!/usr/bin/env python3
"""D-175 C2 — Bootstrap isolated Dogfood Mongo with roles (NOT permanent).

Dedicated mongod on loopback (default 27018) with --auth after user bootstrap.
Users: omnia_df_admin, omnia_df_runtime, omnia_df_clone, omnia_df_backup.
Permanent base security is OUT OF SCOPE (C3).
"""
from __future__ import annotations

import argparse
import json
import os
import secrets
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PORT = 27018
sys.path.insert(0, str(ROOT / "backend"))

from shared.dogfood.backup import assert_dogfood_mongo_port  # noqa: E402


def dogfood_root() -> Path:
    return Path(os.environ.get("DOGFOOD_ROOT") or (ROOT / "dogfood")).resolve()


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, capture_output=True)


def assert_bootstrap_port(port: int) -> int:
    """Refuse shared Cloud port before any stop/start — fail-closed."""
    return assert_dogfood_mongo_port(port)


def pid_on_port(port: int) -> int | None:
    assert_bootstrap_port(port)
    p = run(["bash", "-lc", f"lsof -tiTCP:{port} -sTCP:LISTEN || true"])
    out = (p.stdout or "").strip()
    if not out:
        return None
    try:
        return int(out.splitlines()[0])
    except ValueError:
        return None


def stop_port(port: int) -> None:
    assert_bootstrap_port(port)
    pid = pid_on_port(port)
    if not pid:
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    for _ in range(40):
        if pid_on_port(port) is None:
            return
        time.sleep(0.25)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass


def wait_ping(uri: str, timeout: float = 40.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        p = run(["mongosh", "--quiet", uri, "--eval", "db.runCommand({ping:1}).ok"])
        if p.returncode == 0 and "1" in (p.stdout or ""):
            return
        time.sleep(0.4)
    raise RuntimeError(f"mongo_not_ready:{uri.split('@')[-1] if '@' in uri else uri}")


def start_mongod(dbpath: Path, port: int, logpath: Path, auth: bool) -> None:
    assert_bootstrap_port(port)
    dbpath.mkdir(parents=True, exist_ok=True)
    logpath.parent.mkdir(parents=True, exist_ok=True)
    if pid_on_port(port):
        # If auth required but process is old unauth, restart
        flag = dbpath / ".auth_enabled"
        if auth and not flag.exists():
            stop_port(port)
        elif not auth and flag.exists():
            # leave as-is; caller decides
            pass
        elif pid_on_port(port):
            return
    cmd = [
        "mongod",
        f"--dbpath={dbpath}",
        "--bind_ip",
        "127.0.0.1",
        f"--port={port}",
        f"--logpath={logpath}",
        "--fork",
    ]
    if auth:
        cmd.append("--auth")
    p = run(cmd)
    if p.returncode != 0:
        raise RuntimeError(f"mongod_start_failed:{(p.stderr or p.stdout)[-400:]}")
    uri = f"mongodb://127.0.0.1:{port}/admin"
    if not auth:
        wait_ping(uri)
    # with auth, caller waits with credentials


def mongosh(uri: str, js: str) -> str:
    p = run(["mongosh", "--quiet", uri, "--eval", js])
    if p.returncode != 0:
        raise RuntimeError(f"mongosh_failed:{(p.stderr or p.stdout)[-600:]}")
    return (p.stdout or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("OMNIA_DF_MONGO_PORT") or DEFAULT_PORT))
    ap.add_argument(
        "--dbpath",
        default=os.environ.get("OMNIA_DF_MONGO_DBPATH") or str(dogfood_root() / "mongo-data"),
    )
    ap.add_argument("--runtime-db", default="omnia_df_c2_src")
    args = ap.parse_args()

    # Fail before any stop_port / mongod — misconfig must not touch shared :27017
    assert_bootstrap_port(args.port)

    root = dogfood_root()
    root.mkdir(parents=True, exist_ok=True)
    dbpath = Path(args.dbpath)
    logpath = root / "logs" / "mongod-df.log"
    cred_path = root / "secrets" / "mongo-df-credentials.json"
    cred_path.parent.mkdir(parents=True, exist_ok=True)

    if cred_path.exists():
        creds = json.loads(cred_path.read_text(encoding="utf-8"))
    else:
        creds = {
            "admin": secrets.token_urlsafe(24),
            "runtime": secrets.token_urlsafe(24),
            "clone": secrets.token_urlsafe(24),
            "backup": secrets.token_urlsafe(24),
        }
        # Atomic 0600 write — avoid world-readable window before chmod
        tmp = cred_path.with_suffix(".tmp")
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(creds, indent=2) + "\n")
        os.replace(str(tmp), str(cred_path))
        cred_path.chmod(0o600)

    flag = dbpath / ".auth_enabled"
    # Phase 1: noauth bootstrap if needed
    if not flag.exists():
        stop_port(args.port)
        start_mongod(dbpath, args.port, logpath, auth=False)
        wait_ping(f"mongodb://127.0.0.1:{args.port}/admin")
        # create admin
        mongosh(
            f"mongodb://127.0.0.1:{args.port}/admin",
            f"""
            const admin=db.getSiblingDB('admin');
            const users=(admin.getUsers().users||[]);
            if (!users.some(u=>u.user==='omnia_df_admin')) {{
              admin.createUser({{user:'omnia_df_admin', pwd:'{creds['admin']}', roles:[{{role:'root', db:'admin'}}]}});
              print('created_admin');
            }} else print('admin_exists');
            """,
        )
        flag.write_text("1\n", encoding="utf-8")
        stop_port(args.port)

    # Phase 2: auth mode
    start_mongod(dbpath, args.port, logpath, auth=True)
    admin_uri = (
        f"mongodb://omnia_df_admin:{creds['admin']}@127.0.0.1:{args.port}/admin?authSource=admin"
    )
    wait_ping(admin_uri)

    rt = args.runtime_db
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
    upsertRole('df_runtime_rw', [
      {{resource:{{db:'{rt}', collection:''}}, actions:['find','insert','update','remove','createIndex','listCollections']}}
    ]);
    upsertRole('df_clone_ops', [
      {{resource:{{db:'', collection:''}}, actions:['listDatabases']}},
      {{resource:{{db:'omnia_df_c2_src', collection:''}}, actions:['find','listCollections','listIndexes']}},
      {{resource:{{db:'omnia_df_probe', collection:''}}, actions:['find','insert','update','remove','createIndex','listCollections','dropCollection']}},
      {{resource:{{db:'omnia_df_probe_c2', collection:''}}, actions:['find','insert','update','remove','createIndex','listCollections','dropCollection']}}
    ]);
    upsertRole('df_backup_ro', [
      {{resource:{{db:'', collection:''}}, actions:['listDatabases']}},
      {{resource:{{db:'omnia_df_c2_src', collection:''}}, actions:['find','listCollections','listIndexes']}},
      {{resource:{{db:'{rt}', collection:''}}, actions:['find','listCollections','listIndexes']}}
    ]);
    upsertUser('omnia_df_runtime', '{creds['runtime']}', [{{role:'df_runtime_rw', db:'admin'}}]);
    upsertUser('omnia_df_clone', '{creds['clone']}', [{{role:'df_clone_ops', db:'admin'}}]);
    upsertUser('omnia_df_backup', '{creds['backup']}', [{{role:'df_backup_ro', db:'admin'}}]);
    print('roles_ok');
    """
    print(mongosh(admin_uri, js))

    matrix = {
        "instance": f"127.0.0.1:{args.port}",
        "auth": True,
        "dbpath": str(dbpath),
        "users": {
            "omnia_df_runtime": {
                "privileges": f"readWrite on {rt} only",
                "forbidden": "write on probe/permanent/shared omnia",
            },
            "omnia_df_clone": {
                "privileges": "read omnia_df_c2_src; readWrite omnia_df_probe + omnia_df_probe_c2 only",
                "forbidden": "permanent / shared omnia / other probe_*",
            },
            "omnia_df_backup": {
                "privileges": "read dogfood source DBs for dump",
                "forbidden": "write / drop",
            },
        },
        "permanent_base": "OUT_OF_SCOPE_C2",
        "credentials": "stored locally under dogfood/secrets (gitignored); never in manifests",
    }
    (root / "C2_MONGO_ROLE_MATRIX.json").write_text(
        json.dumps(matrix, indent=2) + "\n", encoding="utf-8"
    )
    try:
        Path("/opt/cursor/artifacts/D175-C2-MONGO-ROLE-MATRIX.json").write_text(
            json.dumps(matrix, indent=2) + "\n", encoding="utf-8"
        )
    except OSError:
        pass
    print(json.dumps({"ok": True, "port": args.port, "auth": True}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        print(f"FAIL {e}", file=sys.stderr)
        raise SystemExit(2)
