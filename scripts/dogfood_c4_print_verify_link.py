#!/usr/bin/env python3
"""D-175 C4 — Print latest email-verification link for a Founder-created user.

Invented email providers never receive mail; Resend is HOLD in dogfood.
This reads the token already stored in the CLEAN work DB (no user invention).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from pymongo import MongoClient  # noqa: E402

from shared.dogfood.c4_structure import assert_c4_workcopy_db_name  # noqa: E402
from shared.dogfood.permanent import dogfood_root  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--email", required=True)
    ap.add_argument("--db", default=os.environ.get("OMNIA_DOGFOOD_RUNTIME_DB") or "omnia_df_clean_c4")
    ap.add_argument("--lang", default="it")
    args = ap.parse_args()

    db_name = assert_c4_workcopy_db_name(args.db, op="verify_link")
    root = dogfood_root()
    creds = json.loads((root / "secrets" / "mongo-df-credentials.json").read_text())
    port = int(os.environ.get("OMNIA_DF_MONGO_PORT") or 27018)
    client = MongoClient(
        f"mongodb://omnia_df_runtime:{creds['runtime']}@127.0.0.1:{port}/?authSource=admin",
        serverSelectionTimeoutMS=8000,
    )
    db = client[db_name]
    email = args.email.strip().lower()
    user = db.users.find_one({"email": email}, {"_id": 0, "id": 1, "email": 1, "email_verified": 1})
    if not user:
        # case-sensitive fallback
        user = db.users.find_one({"email": args.email.strip()}, {"_id": 0, "id": 1, "email": 1, "email_verified": 1})
    if not user:
        print(json.dumps({"ok": False, "error": "user_not_found", "email": email}, indent=2))
        return 2
    if user.get("email_verified") is True:
        print(json.dumps({"ok": True, "already_verified": True, "email": user.get("email")}, indent=2))
        return 0
    tok = db.email_verification_tokens.find_one(
        {"user_id": user["id"], "used": {"$ne": True}},
        sort=[("created_at", -1)],
    ) or db.email_verification_tokens.find_one(
        {"email": user.get("email")},
        sort=[("created_at", -1)],
    )
    if not tok or not tok.get("token"):
        print(json.dumps({"ok": False, "error": "no_token_register_or_resend_first", "user_id": user["id"]}, indent=2))
        return 2
    base = (
        os.environ.get("FRONTEND_URL")
        or Path("/tmp/omnia-stack/SHARE_URL.txt").read_text().strip()
        or "http://127.0.0.1:43123"
    ).rstrip("/")
    link = f"{base}/{args.lang}/verify-email?token={quote(tok['token'])}"
    print(
        json.dumps(
            {
                "ok": True,
                "email": user.get("email"),
                "user_id": user["id"],
                "verify_url": link,
                "note": "Dogfood: open this link yourself — no real email is sent",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
