"""Preflight checks for local or (opt-in) staging."""
from __future__ import annotations

import json
from typing import Any, Dict, List

import requests

from .config import EXPECTATIONS, HarnessConfig


def check_health(cfg: HarnessConfig) -> Dict[str, Any]:
    url = f"{cfg.api()}/health"
    try:
        r = requests.get(url, timeout=8)
        body: Any
        try:
            body = r.json()
        except Exception:  # noqa: BLE001
            body = r.text[:200]
        return {
            "check": "health",
            "url": url,
            "status_code": r.status_code,
            "ok": r.status_code == 200,
            "body": body,
        }
    except Exception as e:  # noqa: BLE001
        return {"check": "health", "url": url, "ok": False, "error": str(e)}


def check_mongo(cfg: HarnessConfig) -> Dict[str, Any]:
    try:
        from pymongo import MongoClient

        client = MongoClient(cfg.mongo_url, serverSelectionTimeoutMS=2500)
        client.admin.command("ping")
        db = client[cfg.db_name]
        names = db.list_collection_names()
        return {
            "check": "mongo",
            "ok": True,
            "db_name": cfg.db_name,
            "collections_sample": sorted(names)[:20],
        }
    except Exception as e:  # noqa: BLE001
        return {"check": "mongo", "ok": False, "error": str(e)}


def check_unauth_wall(cfg: HarnessConfig) -> Dict[str, Any]:
    url = f"{cfg.api()}/app/properties"
    try:
        r = requests.get(url, timeout=8)
        ok = r.status_code in (401, 403)
        return {
            "check": "unauth_wall",
            "url": url,
            "status_code": r.status_code,
            "ok": ok,
        }
    except Exception as e:  # noqa: BLE001
        return {"check": "unauth_wall", "ok": False, "error": str(e)}


def check_session_revocation_local(cfg: HarnessConfig) -> Dict[str, Any]:
    """B14 local proof: mint session-bound JWT, revoke in Mongo, access must 401.

    Uses sync PyMongo as SoT (same as API Motor) so the harness does not share a
    Motor client across closed ``asyncio.run`` loops. Does not call remote staging.
    """
    import os
    import sys
    import uuid
    from datetime import datetime, timezone
    from pathlib import Path

    # Ensure backend imports resolve when run from repo root
    root = Path(__file__).resolve().parents[2]
    backend = root / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))
    env_path = backend / ".env"
    if env_path.is_file():
        for line in open(env_path, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() in {"MONGO_URL", "DB_NAME", "JWT_SECRET"}:
                os.environ.setdefault(
                    k.strip(), v.strip().strip('"').strip("'")
                )
    os.environ.setdefault("MONGO_URL", cfg.mongo_url)
    os.environ.setdefault("DB_NAME", cfg.db_name)

    try:
        from pymongo import MongoClient
        from shared.auth.hashing import hash_password
        from shared.auth.jwt_tokens import (
            create_access_token,
            create_refresh_token,
            decode_token,
        )

        client = MongoClient(cfg.mongo_url, serverSelectionTimeoutMS=2500)
        db = client[cfg.db_name]
        run = cfg.run_id or f"w3stg-{uuid.uuid4().hex[:8]}"
        uid = f"{run}-sess-u"
        now = datetime.now(timezone.utc).isoformat()
        sid = str(uuid.uuid4())
        epoch = 0
        db.users.delete_one({"id": uid})
        db.users.insert_one(
            {
                "id": uid,
                "email": f"{uid}@harness.test",
                "password_hash": hash_password("Harness!99"),
                "role": "client",
                "agency_ids": [],
                "is_active": True,
                "active_session_ids": [sid],
                "session_epoch": epoch,
                "created_at": now,
            }
        )
        access = create_access_token(
            uid, f"{uid}@harness.test", "client", session_id=sid, session_epoch=epoch
        )
        refresh = create_refresh_token(uid, session_id=sid)
        payload = decode_token(refresh) or {}
        jti = payload.get("jti")
        if jti:
            db.refresh_tokens.insert_one(
                {
                    "jti": jti,
                    "user_id": uid,
                    "session_id": sid,
                    "expires_at": payload.get("exp"),
                    "created_at": now,
                }
            )

        pre = requests.get(
            f"{cfg.api()}/auth/me",
            headers={"Authorization": f"Bearer {access}"},
            cookies={"access_token": access},
            timeout=10,
        )
        # Immediate Mongo revoke (authoritative SoT shared with every API process)
        db.users.update_one(
            {"id": uid},
            {
                "$set": {
                    "active_session_ids": [],
                    "last_session_revoke_reason": "harness_preflight",
                    "last_session_revoke_at": now,
                    "updated_at": now,
                },
                "$inc": {"session_epoch": 1},
            },
        )
        db.refresh_tokens.delete_many({"user_id": uid})
        post = requests.get(
            f"{cfg.api()}/auth/me",
            headers={"Authorization": f"Bearer {access}"},
            cookies={"access_token": access},
            timeout=10,
        )
        s_ref = requests.Session()
        s_ref.cookies.set("refresh_token", refresh)
        ref = s_ref.post(f"{cfg.api()}/auth/refresh", timeout=10)
        db.users.delete_one({"id": uid})
        db.refresh_tokens.delete_many({"user_id": uid})
        ok = pre.status_code == 200 and post.status_code == 401 and ref.status_code in (
            401,
            403,
        )
        return {
            "check": "session_revocation",
            "ok": ok,
            "pre_me": pre.status_code,
            "post_me": post.status_code,
            "post_refresh": ref.status_code,
            "evidence": (
                "access JWT rejected immediately after sync Mongo "
                "active_session_ids clear + session_epoch bump"
            ),
        }
    except Exception as e:  # noqa: BLE001
        return {"check": "session_revocation", "ok": False, "error": str(e)}


def expectations_report(cfg: HarnessConfig) -> List[Dict[str, Any]]:
    rows = []
    for e in EXPECTATIONS:
        rows.append(
            {
                "key": e.key,
                "expected": e.expected,
                "source_of_truth": e.source_of_truth,
                "verify_how": e.verify_how,
                "acceptance": e.acceptance,
                "local_evidence": e.local_evidence,
                "staging_only": e.staging_only,
                "applies_now": (not e.staging_only) or cfg.mode == "staging",
            }
        )
    return rows


def run_preflight(cfg: HarnessConfig) -> Dict[str, Any]:
    if cfg.mode == "staging" and not cfg.allow_staging:
        return {
            "verdict": "BLOCKED",
            "reason": "staging mode requires OMNIA_STAGING_VERIFY=1",
            "checks": [],
        }
    checks = [
        check_health(cfg),
        check_mongo(cfg),
        check_unauth_wall(cfg),
        check_session_revocation_local(cfg),
    ]
    ok = all(c.get("ok") for c in checks)
    return {
        "verdict": "PASS" if ok else "FAIL",
        "mode": cfg.mode,
        "base_url": cfg.base_url,
        "checks": checks,
        "expectations": expectations_report(cfg),
        "blocked_remote_only": [
            "multi_replica_railway_session_revoke",
            "b8_l5_t22",
        ],
    }


def main():
    import argparse

    p = argparse.ArgumentParser(description="W3 staging harness preflight")
    p.add_argument("--mode", choices=["local", "staging"], default="local")
    p.add_argument("--json-out", default="")
    args = p.parse_args()
    cfg = HarnessConfig(mode=args.mode)
    report = run_preflight(cfg)
    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text)
    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            f.write(text)
    raise SystemExit(0 if report.get("verdict") == "PASS" else 1)


if __name__ == "__main__":
    main()
